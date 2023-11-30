from collect_arxiv import str_to_datetime, arxiv_searcher
from collect_cna import cna_searcher, cna_searcher_two
from collect_ieee import ieee_searcher
from collect_importai import importai_searcher
from collect_synced import synced_searcher
from collect_mit import date_from_url, get_response, mit_searcher

from utils_notifications import send_notification

from os import listdir, path
import json
import traceback

def run_collection():
      dir_path = path.dirname(path.realpath(__file__))
      DATA_PATH = dir_path + '/data/running/'
      IN_DATA_PATH = dir_path + '/data/input_data/'
      OUTPUT_PATH = dir_path + '/data/raw/'

      # Getting last collection date, if none initializing dictionary
      try:
            with open(IN_DATA_PATH + 'scraped_times.json') as f:
                  scraped_times = json.load(f)     
      except:
            with open(IN_DATA_PATH + 'scraped_times.json', 'w', encoding='utf8') as f:
                  init_dict = {}
                  json.dump(init_dict, f)
            with open(IN_DATA_PATH + 'scraped_times.json') as f:
                  scraped_times = json.load(f)  
      
      # Getting search terms from json
      load_file = IN_DATA_PATH + 'collection_searchterms.json'
      with open(load_file) as handle:
            search_terms = json.loads(handle.read())
      
      # Getting base urls from json
      load_file = IN_DATA_PATH + 'collection_urls_dict_v2.json' 
      with open(load_file) as handle:
            sources = json.loads(handle.read())

      # arXiv
      try:
            arxiv_searcher(3, search_terms, scraped_times)
      except Exception as e:
            print("Scraping failed for ", 'arXiv')
            print(e)
            send_notification("Scraping failed for " + 'arXiv' + '\n' + str(e) + '\n' + traceback.format_exc())

      # Getting all sources by calling dictionary
      retry_list = []

      for key, value in sources.items():
            try:
                  key2 = eval(key)
                  key2(sources[key], search_terms, scraped_times)
                  print('Successfully scraped: ' + sources[key])
            except Exception as e:
                  print("First scraping failed for ", sources[key])
                  print(e)
                  retry_list.append(key)
                  #send_notification("Scraping failed for " + sources[key] + '\n' + str(e) + '\n' + traceback.format_exc())

      for key in retry_list:
            try:
                  key2 = eval(key)
                  key2(sources[key], search_terms, scraped_times)
                  print('Second attempt successful for: ' + sources[key])
            except Exception as e:
                  print("Scraping failed for ", sources[key])
                  print(e)
                  send_notification("Scraping failed for " + sources[key] + '\n' + str(e) + '\n' + traceback.format_exc())            



if __name__ == '__main__':
      run_collection()