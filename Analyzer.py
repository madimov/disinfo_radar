from sentence_transformers import SentenceTransformer
import pickle
from tqdm import tqdm
import pandas as pd

from Config import Config

class Analyzer:

    def __init__(self):
        print("creating Analyzer...")
        pass

    def get_tech_disinfo_analysis(self, df_span_scores):

    #     column_to_groupby = "span_text"
        column_to_groupby = "cluster_label"
        groupby_spans = df_span_scores.groupby([column_to_groupby])
        
        sr_count = groupby_spans["sentence"].count()
        df_analysis_final = pd.DataFrame({"counts": sr_count})

        for column in ["span_score", "accessibility", "content_gen", "automation"]:
        #     column = "accessibility"
        #     column = "content_gen"


            sr_mean = groupby_spans[[column]].mean()[column]
            sr_min = groupby_spans[[column]].min()[column]
            sr_max = groupby_spans[[column]].max()[column]
            sr_median = groupby_spans[[column]].median()[column]
            sr_std = groupby_spans[[column]].std()[column]

            df_factor_data = pd.DataFrame({
        #         "counts": sr_count,
                f"{column}_mean": sr_mean,
                f"{column}_min": sr_min,
                f"{column}_max": sr_max,
                f"{column}_median": sr_median,
                f"{column}_std": sr_std,
            })
            df_analysis_final = df_analysis_final.join(df_factor_data)
        return df_analysis_final