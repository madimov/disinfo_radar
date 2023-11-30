from sklearn.cluster import DBSCAN
from sklearn.cluster import MeanShift
from sklearn.cluster import AffinityPropagation
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import regex as re

import spacy
from tqdm import tqdm

from Config import Config

class SpanFilter:

    def __init__(self):
        print("creating SpanFilter...")
        pass

    def get_valid_spans(self, spans_to_validate):
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
    
    def filter_spans(self, df_span_scores):

        # df_span_scores = pd.read_csv("df_span_scores_50_articles.csv", sep="|")
        spans_confident = df_span_scores[df_span_scores["span_score"] >= 0.999]["span_text"].unique().tolist()
        spans_filtered = self.get_valid_spans(spans_confident)

        return spans_filtered