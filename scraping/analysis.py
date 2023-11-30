import pandas as pd
from os import path, listdir
from os.path import isfile, join

# To load models
import joblib

# For new columns
from datetime import datetime

#from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression

from collections import Counter

# Paths
dir_path = path.dirname(path.realpath(__file__))
DATA_PATH = dir_path + '/data/final/'
IN_DATA_PATH = dir_path + '/data/input_data/'
MODEL_PATH = dir_path + '/data/models/'
ARCHIVE_PATH = dir_path + '/data/archive/results/'

def apply_model(df_file, vectorizer, model, sigmoid=False):

      # Load dataframe
      CONVERTERS = {'tokens': eval} 

      df = pd.read_csv(DATA_PATH + df_file, converters=CONVERTERS) #lineterminator='\n')

      ## Load vectorizer and model
      vectorizer = joblib.load(MODEL_PATH + vectorizer)
      model = joblib.load(MODEL_PATH + model)

      # transform data and run data through model
      categories = []
      probabilities = []
      max_probability = []

      for index, row in df.iterrows():
            
            print('Transform-Predict: Index ' + str(index) + ' / ' + row.url + ' @ ' + str(datetime.now()))

            row_data = [' '.join(row.tokens)]
            #row_data = [' '.join(df.hard_tokens[index])]

            # If selector used (and load it of course!)
            #transformed_row = selector.transform(vectorizer.transform(row_data))
            
            if sigmoid == True:
                  transformed_row = vectorizer.transform(row_data).toarray()
            else:
                  transformed_row = vectorizer.transform(row_data)
            
            predicted = model.predict(transformed_row) # 0:feature, 2:feature
            
            print("Predicted Value:", predicted[0])
            categories.append(predicted[0])            
            
            if sigmoid == True:
                  probabilities.append(list(predicted_proba[0]))
                  max_probability.append(max(list(predicted_proba[0])))

            print("---------------------------")

      print(Counter(categories))

      # Save results - new csv, likely persist, include "date_classified" columns = datetime.now

      df['category'] = categories

      if sigmoid == True:
            df['probabilities'] = probabilities
            df['max_probability'] = max_probability

      #To limit data usage, I would drop at least these columns, keep 'clean' for review purposes
      df.drop(columns=['text', 'tokens'], inplace=True)

      # likely should rename, with date and put in new folder with all dated csv files
      df.to_csv(DATA_PATH + 'results.csv', index=False)

      # Archiving results, concated with existing
      results_archive_path = ARCHIVE_PATH + 'results' + '_' + str(datetime.now()) + '.csv'

      df.to_csv(results_archive_path, index=False)

if __name__ == '__main__':

      # Paths, DO - send compiled data to seperate folder
      dir_path = path.dirname(path.realpath(__file__))
      DATA_PATH = dir_path + '/data/final/'
      MODEL_PATH = dir_path + '/data/models/'
      ARCHIVE_PATH = dir_path + '/data/archive/results/'

      ## Check files in model folder - just for info now, but could figure a way to implement, but very unimportant/not helpful now
      models = [f for f in listdir(MODEL_PATH) if isfile(join(MODEL_PATH, f))]
      print('Index, Model Name')
      print(list(zip([index for index, value in enumerate(models)], models)))

      DF_FILE = 'compiled.csv'
      MODEL = 'test_model.pkl'
      VECTORIZER = 'test_vectorizer.pkl'

      apply_model(DF_FILE, VECTORIZER, MODEL, sigmoid=False)
