import spacy
import pandas as pd
from nltk.tokenize import sent_tokenize
import re
from sentence_transformers import SentenceTransformer
import pickle
from tqdm import tqdm
from os import listdir
from os.path import isfile, join
from datetime import datetime
from datetime import timezone

from EntityRecognizer import EntityRecognizer
from SpanClusterer import SpanClusterer
from DisinfoFactorScorer import DisinfoFactorScorer
from Config import Config


class DisinfoPipeline:

    def __init__(self):
        print("creating DisinfoPipeline...")
        # self.config = configparser.ConfigParser()
        # self.config.read('config.ini')
        pass

    def load_sentences_from_files(self):
        print("load_sentences_from_files()...")
        # getting sentences from articles
        articles_file_path = "data/documents_for_annotation/"
        onlyfiles = [f for f in listdir(articles_file_path) if isfile(join(articles_file_path, f))]
        
        raw_sentences_objs = []

        for filename in onlyfiles[:1]:
            with open(f"{articles_file_path}/{filename}") as f:
                article_content = f.read()
        #         print(article_content)
                article_sentences = sent_tokenize(article_content)
                
                for i, article_sentence in enumerate(article_sentences):
                    raw_sentence_obj = {
                        "article_filename": filename,
                        "sentence": article_sentence,
                        "sentence_index": i
                    }
                    raw_sentences_objs.append(raw_sentence_obj)

        self.raw_sentences_objs = raw_sentences_objs

    def extract_spans_from_sentences(self):
        print("extract_spans_from_sentences()...")
        self.entityRecognizer = EntityRecognizer()
        self.span_data_objs = self.entityRecognizer.get_spans_from_sentence_objs(self.raw_sentences_objs)

    def predict_disinfo_factor_scores(self):
        print("predict_disinfo_factor_scores()...")
        self.disinfoFactorScorer = DisinfoFactorScorer()
        span_scores_data_objs = self.disinfoFactorScorer.get_all_disinfo_factor_scores(self.span_data_objs)
        self.df_span_scores = pd.DataFrame(span_scores_data_objs)
        current_timestamp = datetime.now(timezone.utc).strftime("%Y_%m_%d-%H_%M_%S")
        self.df_span_scores.to_csv(f"df_span_scores_{current_timestamp}.csv", sep="|", index=False)

    def filter_and_cluster_spans(self):
        print("cluster_spans()...")
        self.spanClusterer = SpanClusterer()
        self.df_clusters_with_labels = self.spanClusterer.filter_and_cluster_spans(self.df_span_scores)

        dict_span2cluster = {}

        list_cluster_labels = self.df_clusters_with_labels["cluster_label"]
        list_of_lists_cluster_spans = [a.tolist() for a in self.df_clusters_with_labels["spans"].tolist()]

        for i, cluster_label in enumerate(list_cluster_labels):
            list_cluster_spans = list_of_lists_cluster_spans[i]
            for span in list_cluster_spans:
                dict_span2cluster[span] = cluster_label

        list_of_all_cluster_spans = [item for sublist in list_of_lists_cluster_spans for item in sublist]
        df_span_scores_filtered = self.df_span_scores[self.df_span_scores["span_text"].isin(list_of_all_cluster_spans)]

        list_span2cluster_labels_mapped = []

        for span in df_span_scores_filtered["span_text"].tolist():
            cluster_label = dict_span2cluster[span]
            list_span2cluster_labels_mapped.append(cluster_label)
            
        df_span_scores_filtered["cluster_label"] = list_span2cluster_labels_mapped
        self.df_span_scores_filtered = df_span_scores_filtered

    def run(self):
        print("run()...")
        self.load_sentences_from_files()
        self.extract_spans_from_sentences()
        self.predict_disinfo_factor_scores()
        if (Config.cfg['default']['filter_and_cluster_spans']):
            self.filter_and_cluster_spans()


def main():
    
    pipeline = DisinfoPipeline()
    pipeline.run()

if __name__ == "__main__":
    main()
