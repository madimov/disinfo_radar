import pandas as pd

import os
from os.path import isfile, join
from os import listdir, path
from datetime import datetime

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import string
import spacy
import re

import shutil

# INSTALL FIRST:
# nltk.download('stopwords')
# python -m spacy download en_core_web_sm

def cleaning(text):
      cleaned_text = text.replace("\n", " ")
      cleaned_text = cleaned_text.replace("\t", " ")
      cleaned_text = cleaned_text.replace('\r', '')

      cleaned_text = re.sub('[^\S\r\n]{2,}', ' ', cleaned_text) # extra spaces
      cleaned_text = cleaned_text.rstrip()

      ###exessive length remove_numbers
      tokens=word_tokenize(cleaned_text)
      cleaned_tokens=[x for x in tokens if len(x) <35]
      final_text=" ".join(cleaned_tokens)

      return final_text

def lower_case(text):
      cleaned_text = text.lower() # lower case
      return cleaned_text

def delete_hyperlinks(text):
      '''
      Only with http (so not e.g www.cna.org), but could add easily
      Note if hyperlink breaks accross a page, it misses it and leaves long messy tokens
      These should somehow be dealt with
      '''
      #cleaned_text = re.sub(r"http\S+", "", text)
      cleaned_text = re.sub("(?P<url>https?://[^\s]+)", "", text)
      return cleaned_text

def remove_punctuation(txt):
      special_punctuation = '：，,《。》“„:一・«»”“]'
      final_punctuation = string.punctuation + special_punctuation
      txt_nopunct = ''.join([c for c in txt if c not in final_punctuation])

      return txt_nopunct

def lemmatization(texts, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV']):
      '''For all possible tags see https://github.com/explosion/spaCy/blob/master/spacy/glossary.py
      which is based on https://universaldependencies.org/u/pos/
      '''

      nlp = spacy.load("en_core_web_sm") # disable=['parser', 'ner']) ## if you need efficiency

      # TO-DO: Move to json and load
      # But first ? Do we need it? I recommend this be our search_terms...maybe, thus load here
      to_keep = []
      
      doc = nlp("".join(texts)) #nlp(sent) #" ".join(sent))
      texts_out = [token.lemma_ for token in doc if token.pos_ in allowed_postags or token.text in to_keep]
      return texts_out

def remove_stopwords(txt):
      # add in anything else we need to remove, eg. for some analysis, any search tags would be dropped from text
      new_stop_words = []

      lang = 'english'
      stop_words = list(stopwords.words(lang))
      final_stop_words = stop_words + new_stop_words

      txt_nostops = [w for w in txt if not w in final_stop_words]
      #txt_nostops = ' '.join([w for w in txt if not w in stop_words]) # Alternate
      return txt_nostops

def remove_numbers(txt):
      '''
      TODO: Not checked as likely dropped for lemmatization, POS tagging
      '''
      result = ''.join([i for i in txt if not i.isdigit()])
      return result

def get_tag(x):
      '''
      For ArXiv only, no implemented
      '''
      tag = x[0]['term']
      # TODO: scrape https://arxiv.org/category_taxonomy to translate codes to plain english
      return tag

def pre_process(df, key, action_col = 'text', filetype = 'csv', load = False):

      dir_path = path.dirname(path.realpath(__file__))
      DATA_PATH = dir_path + '/data/running/' #running
      IN_DATA_PATH = dir_path + '/data/input_data/'
      OUTPUT_PATH = dir_path + '/data/final/'
      ARCHIVE_PATH = dir_path + '/data/archive/'
      
      # if load == True: # TODO: load_file was not defined here, so deactivating this for now. Re-implement if needed
      #       if filetype == 'json':
      #             df = pd.read_json(DATA_PATH + load_file, convert_dates=True, lines=True, orient='records')
      #       else:
      #             CONVERTERS = {'tags': eval, 'arxiv_primary_category': eval,"published_parsed": eval}
      #             df = pd.read_csv(OUTPUT_PATH + load_file, converters=CONVERTERS)

      df['cleaning'] = df[action_col].dropna().apply(lambda x: cleaning(x))

      df['processing'] = df['cleaning'].dropna().apply(lambda x: lower_case(x))

      df['processing'] = df['processing'].dropna().apply(lambda x: delete_hyperlinks(x))

      df['processing'] = df['processing'].dropna().apply(lambda x: remove_punctuation(x))

      df['processing'] = df['processing'].dropna().apply(lambda x:  lemmatization(x, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV']))

      # move before lemmatization?
      df['tokens'] = df['processing'].dropna().apply(lambda x:  remove_stopwords(x))

      df.drop(columns=['processing'], inplace=True)
      df.dropna(subset='tokens', inplace=True)

      # Not needed, if used make a try-except clause
      #df['category'] = df['tags'].dropna().apply(lambda x:  get_tag(x))

      # Saving, overwriting existing, and archiving
      save_path = OUTPUT_PATH + key + '.csv'
      archive_path = ARCHIVE_PATH + key + '_' + str(datetime.now()) + '.csv'

      df.to_csv(save_path, index=False)
      df.to_csv(archive_path, index=False)

      return df

def run_processing():
      # Paths
      dir_path = path.dirname(path.realpath(__file__))
      DATA_PATH = dir_path + '/data/running/' #running
      IN_DATA_PATH = dir_path + '/data/input_data/'
      OUTPUT_PATH = dir_path + '/data/final/'
      ARCHIVE_PATH = dir_path + '/data/archive/'

      onlyfiles = [f for f in listdir(DATA_PATH) if isfile(join(DATA_PATH, f))]

      # Loads all files in folder into dataframes

      files = [f.split('.')[0] for f in listdir(DATA_PATH) if isfile(join(DATA_PATH, f))]
      files = [f for f in files if len(f) > 0] # Miko note: was otherwise getting empty file name in list
      print(files)

      dataframe = {}

      for file in files:
            #try:
            dataframe[file] = pd.read_csv(DATA_PATH + file + '.csv', lineterminator='\n')
            #except:
            #      pass

      dataframe_final= {}
      for key, value in dataframe.items():
            dataframe[key] = pre_process(dataframe[key], key, action_col = 'text', filetype = 'csv', load = False)

      # Get new dfs in new dictionary, merge and export
      df_compiled = pd.concat([v for k,v in dataframe.items()])
      # May prefer to send to a seperate analysis folder
      df_compiled.to_csv(OUTPUT_PATH + 'compiled.csv', index=False)

      # Archiving full collection, concated with existing
      full_archive_path = ARCHIVE_PATH + 'compiled.csv'

      if path.isfile(full_archive_path):
            old_df = pd.read_csv(full_archive_path)
            combined_df = pd.concat([df_compiled, old_df])
            combined_df.to_csv(full_archive_path, index=False)
      else:
            df_compiled.to_csv(full_archive_path, index=False)

      # Deleting running data and making fresh folder for next iteration
      shutil.rmtree(DATA_PATH)
      os.makedirs(DATA_PATH)


if __name__ == '__main__':
      run_processing()