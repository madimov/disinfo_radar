from sklearn.cluster import DBSCAN
from sklearn.cluster import MeanShift
from sklearn.cluster import AffinityPropagation
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sentence_transformers import SentenceTransformer
import regex as re

import spacy
from tqdm import tqdm

from Config import Config

class SpanClusterer:

    def __init__(self):
        print("creating SpanClusterer...")
        # self.nlp_spancat = spacy.load(Config.cfg['default']['location_model_spacy_spancat'])
        self.model_sentence_transformer = SentenceTransformer(Config.cfg['default']['model_name_sentence_transformer'])
        # loading it here as well as each component of the pipeline might need a different vectorizer
        # TODO: rename to model_span_vectorizer
        pass

    def validate_spans(self, spans_to_validate): # TODO: rename to get_valid_spans
        validated_spans = []
        
        for span in spans_to_validate:
            valid_span = True
            if len(span) >= 30 and " " not in span:
                valid_span = False
    #         elif span[0] in string.punctuation:
    #             valid_span = False
            elif re.search(r"^[^a-zA-Z]", span):
                valid_span = False
            
            
            if valid_span:
                validated_spans.append(span)
        
        return validated_spans

    def filter_and_cluster_spans(self, df_span_scores):

        # df_span_scores = pd.read_csv("df_span_scores_50_articles.csv", sep="|")
        spans_filtered = df_span_scores[df_span_scores["span_score"] >= 0.999]["span_text"].unique().tolist()
        self.valid_spans = self.validate_spans(spans_filtered)

        self.valid_spans_embeddings = self.model_sentence_transformer.encode(self.valid_spans)

        X = np.array(self.valid_spans_embeddings)

        clustering = AffinityPropagation(random_state=5).fit(X)

        span_cluster_pairs = list(zip(self.valid_spans, clustering.labels_))

        dict_clusters = {}
        for pair in span_cluster_pairs:
            span_cluster_index = pair[1]
            cluster_center_span_index = clustering.cluster_centers_indices_[span_cluster_index]
            cluster_center_span = self.valid_spans[cluster_center_span_index]
            span_text = pair[0]
            if span_cluster_index in dict_clusters:
                dict_clusters[span_cluster_index].append(span_text)
            else:
                dict_clusters[span_cluster_index] = [span_text]
                
        dict_clusters_with_labels = []
        for cluster_index in dict_clusters:
            cluster_center_span_index = clustering.cluster_centers_indices_[cluster_index]
            cluster_center_span = self.valid_spans[cluster_center_span_index]
            spans_in_cluster = dict_clusters[cluster_index]
            print(cluster_center_span)
            for span in spans_in_cluster:
                print("\t", span)
            print()
            obj = {
                "cluster_label": cluster_center_span,
                "spans": spans_in_cluster
            }
            dict_clusters_with_labels.append(obj)
            

        df_clusters_with_labels = pd.DataFrame(dict_clusters_with_labels)

        df_clusters_with_labels.to_parquet("df_clusters_AP_with_labels_50_articles.parquet") # backup to be able to check mapping

        return df_clusters_with_labels