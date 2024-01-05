import sys
sys.path.append('./scraping') # needed so this script has access to nested imports in collection.py and processing.py
# sys.path.append('./google_funcs')

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
import pyarrow.parquet as pq
import os
from scipy.stats import zscore

from EntityRecognizer import EntityRecognizer
from SpanFilter import SpanFilter
from SpanClusterer import SpanClusterer
from DisinfoFactorScorer import DisinfoFactorScorer
from Analyzer import Analyzer
from Config import Config

from scraping.collection import run_collection
from scraping.processing import run_processing

import gspread
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
# from google_funcs import drive_functions


class DisinfoPipeline:

    def __init__(self):
        print("creating DisinfoPipeline...")
        pass

    def scrape_articles(self):
        print("scrape_articles()...")
        run_collection()

    def preprocess_scraped_articles(self):
        print("preprocess_scraped_articles()...")
        run_processing()

    def load_sentences_from_compiled_archive(self):
        print("load_sentences_from_compiled_archive()...")
        # getting sentences from articles
        compiled_archive_file_path = "scraping/data/archive/compiled.csv"
        # onlyfiles = [f for f in listdir(articles_file_path) if isfile(join(articles_file_path, f))]
        df_compiled_archive = pd.read_csv(compiled_archive_file_path)
        
        raw_sentences_objs = []

        article_contents = df_compiled_archive['cleaning'].tolist()
        article_urls = df_compiled_archive['url'].tolist()

        if (Config.cfg['default']['test_run_small_sample']): 
            article_contents = article_contents[:5] # can limit selection for quickly testing a small sample. otherwise the whole dataset is re-processed        

        for i, article_content in enumerate(article_contents):
            article_url = article_urls[i]
            article_sentences = sent_tokenize(article_content)
            
            for i, article_sentence in enumerate(article_sentences):
                raw_sentence_obj = {
                    "article_url": article_url, # changing from filename to URL when loading from compiled archive
                    "sentence": article_sentence,
                    "sentence_index": i
                }
                raw_sentences_objs.append(raw_sentence_obj)

        self.raw_sentences_objs = raw_sentences_objs

    def load_sentences_from_files(self): # loads text from individual article files, used during testing
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
        print("extract_spans_from_sentences()... starting")
        self.entityRecognizer = EntityRecognizer()
        self.span_data_objs = self.entityRecognizer.get_spans_from_sentence_objs(self.raw_sentences_objs)
        print("extract_spans_from_sentences()... done")

    def predict_disinfo_factor_scores(self):
        print("predict_disinfo_factor_scores()... starting")
        self.disinfoFactorScorer = DisinfoFactorScorer()
        span_scores_data_objs = self.disinfoFactorScorer.get_all_disinfo_factor_scores(self.span_data_objs)
        self.df_span_scores = pd.DataFrame(span_scores_data_objs)
        # current_timestamp = datetime.now(timezone.utc).strftime("%Y_%m_%d-%H_%M_%S")
        self.df_span_scores.to_csv(f"{self.run_output_directory}/df_span_scores_{self.run_timestamp}.csv", sep="|", index=False)

        if (Config.cfg['default']['filter_and_cluster_spans'] == False):
            self.df_span_scores_final = self.df_span_scores

        print("predict_disinfo_factor_scores()... done")

    def filter_and_cluster_spans(self):
        print("filter_and_cluster_spans()... starting")

        self.spanFilter = SpanFilter()
        self.spans_filtered = self.spanFilter.filter_spans(self.df_span_scores)

        self.spanClusterer = SpanClusterer()
        # self.df_clusters_with_labels = self.spanClusterer.filter_and_cluster_spans(self.df_span_scores)
        self.df_clusters_with_labels = self.spanClusterer.cluster_spans(self.spans_filtered)
        # backup to be able to check mapping of span to cluster
        # self.df_clusters_with_labels.to_parquet(f"{self.run_output_directory}/df_clusters_with_labels_{self.run_timestamp}.parquet") # parquet helps easily load list of spans back into list
        self.df_clusters_with_labels.to_csv(f"{self.run_output_directory}/df_clusters_with_labels_{self.run_timestamp}.csv", sep="|") # csv is fine for manual checking

        dict_span2cluster = {}

        list_cluster_labels = self.df_clusters_with_labels["cluster_label"]
        # list_of_lists_cluster_spans = [a.tolist() for a in self.df_clusters_with_labels["spans"].tolist()]
        list_of_lists_cluster_spans = [a for a in self.df_clusters_with_labels["spans"].tolist()]

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
        self.df_span_scores_final = df_span_scores_filtered

        print("filter_and_cluster_spans()... done")

    def analyze_disinfo_potential(self):
        print("analyze_disinfo_potential()... starting")
        self.analyzer = Analyzer()
        df_tech_disinfo_analysis = self.analyzer.get_tech_disinfo_analysis(self.df_span_scores_final)
        df_tech_disinfo_analysis = df_tech_disinfo_analysis.sort_values("counts", ascending=False)
        # df_tech_disinfo_analysis.to_csv("df_tech_disinfo_analysis_50_articles_WITH_CLUSTERS.csv", sep="|")
        # current_timestamp = datetime.now(timezone.utc).strftime("%Y_%m_%d-%H_%M_%S")
        df_tech_disinfo_analysis.to_csv(f"{self.run_output_directory}/df_tech_disinfo_analysis_{self.run_timestamp}.csv", sep="|")
        self.df_tech_disinfo_analysis = df_tech_disinfo_analysis
        print("analyze_disinfo_potential()... done")

    def save_dataframe_to_drive(self, df, file_name, folder_id):
        # define the scope
        scope = ['https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/drive']

        # add your service account file
        creds = service_account.Credentials.from_service_account_file('google_funcs/driveproject-392612-86425acec0ff.json', scopes=scope)

        # authenticate Google Drive API client
        drive_service = build('drive', 'v3', credentials=creds)

        # check if a file with the same name already exists in the folder
        query = "name='{}' and parents in '{}' and trashed = false".format(file_name, folder_id)
        existing_files = drive_service.files().list(q=query, fields='files(id)').execute().get('files', [])

        if existing_files:
            # get the existing file id
            file_id = existing_files[0]['id']
        else:
            # create a new Google Sheet
            file_metadata = {'name': file_name, 'mimeType': 'application/vnd.google-apps.spreadsheet',
                            'parents': [folder_id]}
            file = drive_service.files().create(body=file_metadata).execute()
            file_id = file.get('id')

        gc = gspread.service_account("google_funcs/driveproject-392612-86425acec0ff.json")
        # authenticate gspread client
        gc = gspread.authorize(creds)

        # open the Google Sheet and get the first worksheet
        sh = gc.open_by_key(file_id)
        worksheet = sh.get_worksheet(0)

        # resize the worksheet to accommodate the dataframe and index
        worksheet.resize(rows=len(df) + 1, cols=len(df.columns))

        # update the worksheet with the dataframe only (no index)
        data = [df.columns.values.tolist()] + df.values.tolist()
        worksheet.update(data)

    def save_output_to_google(self):
        print("save_output_to_google()... starting")

        # df_google_output = self.df_tech_disinfo_analysis.reset_index()
        # df_google_output = df_google_output.astype("str")
        # self.save_dataframe_to_drive(df_google_output, "df_google_output_test_2.xlsx", Config.cfg['default']['google_output_file_location'])

        #filter data
        df_data = self.df_tech_disinfo_analysis
        df_data_filtered = df_data[(df_data["span_score_mean"]>0.96) & (df_data["counts"]>20)]
        df_data_filtered = df_data_filtered.reset_index()
        print(df_data_filtered.columns)

        #dotplot
        df_dotplot = df_data_filtered[['cluster_label', 'accessibility_mean', 'content_gen_mean', 'automation_mean']]
        df_dotplot[['accessibility_mean', 'content_gen_mean', 'automation_mean']] = df_dotplot[['accessibility_mean', 'content_gen_mean', 'automation_mean']].apply(zscore)
        # df_dotplot = df_dotplot.reset_index()
        df_dotplot = df_dotplot.astype("str")
        self.save_dataframe_to_drive(df_dotplot, "disinfo_radar_dotplot.xlsx", Config.cfg['default']['google_output_file_location'])

        # scatter plots
        df_scatter_1 = df_data_filtered[['cluster_label', 'accessibility_mean', 'content_gen_mean']]
        df_scatter_1[['accessibility_mean', 'content_gen_mean']] = df_scatter_1[['accessibility_mean', 'content_gen_mean']].apply(zscore)
        # df_scatter_1 = df_scatter_1.reset_index()
        df_scatter_1 = df_scatter_1.astype("str")
        self.save_dataframe_to_drive(df_scatter_1, "disinfo_radar_scatterplot_accessibility_VS_content.xlsx", Config.cfg['default']['google_output_file_location'])

        df_scatter_2 = df_data_filtered[['cluster_label', 'accessibility_mean', 'automation_mean']]
        df_scatter_2[['accessibility_mean', 'automation_mean']] = df_scatter_2[['accessibility_mean', 'automation_mean']].apply(zscore)
        # df_scatter_2 = df_scatter_2.reset_index()
        df_scatter_2 = df_scatter_2.astype("str")
        self.save_dataframe_to_drive(df_scatter_2, "disinfo_radar_scatterplot_accessibility_VS_automation.xlsx", Config.cfg['default']['google_output_file_location'])

        df_scatter_3 = df_data_filtered[['cluster_label', 'content_gen_mean', 'automation_mean']]
        df_scatter_3[['content_gen_mean', 'automation_mean']] = df_scatter_3[['content_gen_mean', 'automation_mean']].apply(zscore)
        # df_scatter_3 = df_scatter_3.reset_index()
        df_scatter_3 = df_scatter_3.astype("str")
        self.save_dataframe_to_drive(df_scatter_3, "disinfo_radar_scatterplot_content_VS_automation.xlsx", Config.cfg['default']['google_output_file_location'])

        # tornado plot
        def scale_column(column, min_value, max_value):
            min_column = column.min()
            max_column = column.max()
            scaled_column = (column - min_column) / (max_column - min_column) * (max_value - min_value) + min_value
            return scaled_column

        df_tornado = df_data_filtered[['cluster_label', 'counts', 'accessibility_mean', 'content_gen_mean', 'automation_mean']]
        df_tornado[['accessibility_mean', 'content_gen_mean', 'automation_mean']] = df_tornado[['accessibility_mean', 'content_gen_mean', 'automation_mean']].apply(zscore)
        df_tornado['weighted_disinfo_score'] = ((4 * df_tornado["content_gen_mean"]) + df_tornado["automation_mean"] + df_tornado["accessibility_mean"]) / 6
        df_tornado = df_tornado[["cluster_label", "counts", "weighted_disinfo_score"]]
        df_tornado['weighted_disinfo_score'] = scale_column(df_tornado['weighted_disinfo_score'], 10, 210)
        # df_tornado = df_tornado.reset_index()
        df_tornado = df_tornado.astype("str")
        self.save_dataframe_to_drive(df_tornado, "disinfo_radar_tornado.xlsx", Config.cfg['default']['google_output_file_location'])

        print("save_output_to_google()... done")

    def run(self):
        print("PIPELINE run()... starting")
        # current_timestamp = datetime.now(timezone.utc).strftime("%Y_%m_%d-%H_%M_%S")
        current_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.run_timestamp = current_timestamp
        self.run_output_directory = f"output/run_{self.run_timestamp}"
        os.mkdir(self.run_output_directory) 
        self.scrape_articles()
        self.preprocess_scraped_articles()
        # self.load_sentences_from_files()
        self.load_sentences_from_compiled_archive()
        # TODO: only analyze text from new articles to save on performance
        self.extract_spans_from_sentences()
        self.predict_disinfo_factor_scores()
        if (Config.cfg['default']['filter_and_cluster_spans']):
            # TODO: add option to re-train entity normalization / clustering
            self.filter_and_cluster_spans()
        self.analyze_disinfo_potential()

        if (Config.cfg['default']['upload_google_output']):
            self.save_output_to_google()
        
        print("PIPELINE run()... done")


def main():
    pipeline = DisinfoPipeline()
    pipeline.run()

    # if (Config.cfg['default']['upload_google_output']):
    #     df_google_output_test = pd.DataFrame({"X": [10, 20], "Y": [30, 40]}).astype("str")
    #     pipeline.save_dataframe_to_drive(df_google_output_test, "df_google_output_test.xlsx", Config.cfg['default']['google_output_file_location'])

if __name__ == "__main__":
    main()
