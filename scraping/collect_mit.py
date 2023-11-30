# Imports
import requests
from bs4 import BeautifulSoup as soup
import lxml

import pandas as pd

from os import listdir, path
from datetime import datetime, timedelta
import json
import re
import time

# Paths
dir_path = path.dirname(path.realpath(__file__))
DATA_PATH = dir_path + '/data/running/'
IN_DATA_PATH = dir_path + '/data/input_data/'

def date_from_url(x):
      # Define regex pattern to get date from url
      pat = r"(20[0-2][0-9]([-_/]?)[0-9]{2}(?:\2[0-9]{2})?)"
      dates = re.compile(pat)

      res = dates.search(x)
      date_parsed = datetime.strptime(res[0], '%Y/%m/%d')

      return date_parsed
      
def get_response(API_Link, pages=1):
      # Get re
      with requests.get(API_Link + '&page=' + str(pages)) as response:
            #page_soup = soup(response.content, 'lxml')
            #return page_soup
            return response

def mit_searcher(API_Link, search_terms, scraped_times):
      # MIT defined topic tags to search
      topic_tags = ['artificial-intelligence', 'humans-and-technology', 'computing'] 

      ## The topic search approach is not used at present, we use the API instead
      # base_url = sources['MIT_Technology_Review']
      # topic_designator = 'topic/'
      # final_url = base_url + topic_designator + topic_tags[0]
      
      # List to save response for each topic tag
      responses = []

      # Getting responses
      for tag in topic_tags:
            url = API_Link + tag
            print(url)
            response = get_response(url, pages=str(1))
            print(response)

            j_response = json.loads(response.text)
            # Just adding response in list, not appending list
            responses = responses + j_response

      # Keys we need to extract from json
      needed_keys = ['title', 'permalink', 'postDate', 'excerpt']

      # Preping a list to save data to
      entries = []
      entries.append(['title', 'url', 'date', 'summary'])

      # Getting data we need
      for item in responses:
            entry = [item['config'][key] for key in needed_keys]
            entries.append(entry)      

      # Putting data in dataframe
      collected_df = pd.DataFrame(entries[1:],columns=entries[0])     
      
      collected_df['date'] = collected_df['url'].apply(lambda x: date_from_url(x))

      # Getting list of texts with keywords therein
      relevant_text = []
      relevant_text.append(['title', 'url', 'date', 'summary', 'text'])
      
      # Getting last collection time, if none, getting oldest date in results
      try:
            last_collected = datetime.strptime(scraped_times[API_Link],'%Y-%m-%dT%H:%M:%SZ')
      except:
            last_collected = min(list(collected_df.date))

      # Gettin text and saving if newer than last collected
      for index, row in collected_df.iterrows():
            if row.date > last_collected:
                  print('Fetching: ' + row.url)
                  response = requests.post(row.url)
                  html = soup(response.text, 'lxml')

                  objects = html.find_all('div', id="content--body")
                  article_text = []
                  for obj in objects:
                        paragraph_text = obj.find_all('p')
                        for p in paragraph_text:
                              article_text.append(p.text)
                  article_text = ' '.join(article_text)
                  
                  save = list(row)
                  save.append(article_text)
                  relevant_text.append(save)  

                  time.sleep(5)
            else:
                  pass

      new_df = pd.DataFrame(relevant_text[1:],columns=relevant_text[0])
      
      # Saving data
      save_path = DATA_PATH + 'mit_data.csv'
      
      if path.isfile(save_path):
            old_df = pd.read_csv(save_path)
            combined_df = pd.concat([new_df, old_df])
            combined_df.drop_duplicates(subset='url', inplace=True)
            combined_df.to_csv(save_path, index=False)
      else:
            new_df.to_csv(save_path, index=False)

      # Saving collection time
      scraped_times[API_Link] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ') 
      with open(IN_DATA_PATH + 'scraped_times.json', 'w', encoding='utf8') as f:
            json.dump(scraped_times, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
      # Paths
      dir_path = path.dirname(path.realpath(__file__))
      DATA_PATH = dir_path + '/data/running/'
      IN_DATA_PATH = dir_path + '/data/input_data/'
      
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
      
      # Getting base url from json
      load_file = IN_DATA_PATH + 'collection_urls_dict.json'
      with open(load_file) as handle:
            sources = json.loads(handle.read())
      
      API_Link = sources['MIT_Technology_Review_API']

      # Getting search terms from json
      load_file = IN_DATA_PATH + 'collection_searchterms.json'
      with open(load_file) as handle:
            search_terms = json.loads(handle.read())

      # Run
      mit_searcher(API_Link, search_terms, scraped_times)