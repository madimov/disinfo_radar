import arxiv
import json
import pandas as pd
from os import listdir, path, remove
from os.path import isfile, join
from pandas import json_normalize
from datetime import datetime

from utils_collection import aggragate
from utils_conversion import get_pdfs, bulk_pdf_to_text, text_to_csv, pdf_miner_to_text

# Paths
dir_path = path.dirname(path.realpath(__file__))
DATA_PATH = dir_path + '/data/running/'
IN_DATA_PATH = dir_path + '/data/input_data/'
OUTPUT_PATH = dir_path + '/data/raw/'

def str_to_datetime(x):
      y = datetime.strptime(x,'%Y-%m-%dT%H:%M:%SZ')
      return y

def arxiv_searcher(results, search_terms, scraped_times):
      '''
      Function that turns an arxiv query into a df
      Parameters:
        QUERY = term to search for
        results = max results to return
        scraped_times = json of last scrape, TO-DO: load this in main as string time
                    so string time can be entered here for special search
      '''

      for QUERY in search_terms['search_term']:
          search = arxiv.Search(
            query = QUERY,
            max_results = results,
            sort_by = arxiv.SortCriterion.SubmittedDate,
            #sort_order = arxiv.SortOrder.descending
          )

          # Save as, NOTE: I would save them all together 
          #save_as = 'arxiv_' + QUERY
          save_as = 'arxiv_data'

          file = OUTPUT_PATH + save_as + '.jsonl'

          for result in search.results():
                with open (file, 'a') as f:
                      json.dump(result._raw, f, default=str) # use raw as __dict__ has raw in it, thus more data
                      f.write('\n')
      
      # Moving json to df
      df = pd.read_json(file, convert_dates=True, lines=True, orient='records')
      
      # Add column with search term used to locate article
      #df['search_term'] = QUERY
      
      # Reducing data to only what we need, matching format to other csv files
      df['published'] = df['published'].apply(lambda x: str_to_datetime(x))
      df = df[['title', 'links', 'published']] # 'summary' 'search_term'
      df = df.rename(columns={'links': 'url', 'published': 'date'})
      
      # Getting last collection time, if none, getting oldest date in results
      base_url = 'arxiv'
      try:
            last_collected = datetime.strptime(scraped_times[base_url],'%Y-%m-%dT%H:%M:%SZ')
      except:
            last_collected = min(list(df.date))

      # Filter to just since last search
      new_df = df[df.date >= last_collected]
      
      #PDF work
      if len(new_df) == 0:
            print('No new data')
            pass      
      
      else:
            QUERY = 'arXiv'

            get_pdfs(DATA_PATH, QUERY, new_df)
            
            pdf_miner_to_text(DATA_PATH, QUERY)
            # bulk_pdf_to_text(DATA_PATH, QUERY)
            # pdf_to_text(DATA_PATH, QUERY)
            
            df_temp = text_to_csv(DATA_PATH, QUERY)

            #try:
            new_df['text'] = df_temp
            
            #except:
            #    print('No new documents')
            
            # Saving, as new if not exists, concating if file exists already
            save_path = DATA_PATH + 'arxiv_data.csv'
            
            if path.isfile(save_path):
                  old_df = pd.read_csv(save_path)
                  combined_df = pd.concat([new_df, old_df])
                  combined_df.drop_duplicates(subset='title', inplace=True)
                  combined_df.to_csv(save_path, index=False)
            else:
                  new_df.to_csv(save_path, index=False)
      
      # Saving collection time
      scraped_times[base_url] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ') 
      with open(IN_DATA_PATH + 'scraped_times.json', 'w', encoding='utf8') as f:
            json.dump(scraped_times, f, indent=2, ensure_ascii=False)
      
      # Delete jsonl - IMO this is best, if you need to save it, save it elsewhere
      remove(file)

      return new_df

if __name__ == '__main__':
      # Paths
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

      arxiv_searcher(10, search_terms, scraped_times)



