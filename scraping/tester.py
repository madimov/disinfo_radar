from utils_conversion import get_pdfs, bulk_pdf_to_text, text_to_csv, pdf_miner_to_text, pdf_miner_bytes_to_text, text_to_csv
from os import listdir, path, remove
import os

dir_path = path.dirname(path.realpath(__file__))
DATA_PATH = dir_path
QUERY = 'test'
DATA_PATH = dir_path + '/data/running/'

#pdf_miner_to_text(DATA_PATH, QUERY)

df = text_to_csv(DATA_PATH, QUERY)

print(df)

#df.to_csv('texttest.csv', index=False)
#pdf_miner_bytes_to_text(DATA_PATH, QUERY)