from tika import parser

import io

from io import BytesIO
from pdfminer.high_level import extract_text

from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from pdfminer.pdfparser import PDFSyntaxError, PSSyntaxError, PSEOF

import pandas as pd
import os
from  urllib.request import urlopen
import shutil

from collections import defaultdict
from pathlib import Path
from os import listdir
from os.path import isfile, join
from datetime import datetime, timedelta
import time

def get_pdfs(DATA_PATH, QUERY, df):
      QUERY = QUERY #'CNA'
      pdf_dir = DATA_PATH + QUERY + '_pdfs'

      if not os.path.exists(pdf_dir): 
            os.makedirs(pdf_dir)

      have = set(os.listdir(pdf_dir))

      # Time out for requests
      timeout_secs = 20 

      for index, row in df.iterrows():
            if type(row.url) is list:
                  # this is only for arXiv - edit as new list formats needed
                  for item in row.url:
                        if item['type'] == 'application/pdf':
                              pdf_url = item['href']
                              basename = pdf_url.split('/')[-1]
            else:
                  basename = row.url.split('/')[-1]
                  basename = basename.split('.')[0]
                  pdf_url = row.url
            
            fname = os.path.join(pdf_dir, basename + '.pdf')
            print(fname)

            if not basename in have:
                  print('fetching %s into %s' % (pdf_url, fname))
                  clean_url = pdf_url.replace(" ", "%20")
                  req = urlopen(clean_url, None, timeout_secs)
                  with open(fname, 'wb') as fp:
                        shutil.copyfileobj(req, fp)
            else:
                  print('%s exists, skipping' % (fname, ))

            time.sleep(5)

def pdf_to_text(DATA_PATH, QUERY):
      # Checking for a program and a folder
      if not shutil.which('pdftotext'): # needs Python 3.3+
            print('ERROR: you don\'t have pdftotext installed. Install it first before calling this script')
            sys.exit()

      if not os.path.exists(DATA_PATH + QUERY + '_txt'):
            os.makedirs(DATA_PATH + QUERY + '_txt')
      
      # Specifying paths
      txt_dir = DATA_PATH + QUERY + '_txt'
      pdf_dir = DATA_PATH + QUERY + '_pdfs'

      have = set(os.listdir(txt_dir))
      files = os.listdir(pdf_dir)

      for i,f in enumerate(files):

            txt_basename = f + '.txt'
      
            if txt_basename in have:
                  print('%d/%d skipping %s, already exists.' % (i, len(files), txt_basename, ))
                  continue

            pdf_path = os.path.join(pdf_dir, f)
            txt_path = os.path.join(txt_dir, txt_basename)
            
            cmd = "pdftotext %s %s" % (pdf_path, txt_path)
            os.system(cmd)

            print('%d/%d %s' % (i, len(files), cmd))

            # check output was made
            if not os.path.isfile(txt_path):
                  # there was an error with converting the pdf
                  print('there was a problem with parsing %s to text, creating an empty text file.' % (pdf_path, ))
                  os.system('touch ' + txt_path) # create empty file, but it's a record of having tried to convert

            time.sleep(0.01) #  for ctrl+c termination

def text_to_csv(DATA_PATH, QUERY):

      txt_dir = DATA_PATH + QUERY + '_txt'
      pdf_dir = DATA_PATH + QUERY + '_pdfs'

      #results = defaultdict(list)
      results = []

      for file in Path(txt_dir).iterdir():
            with open(file, "r", encoding="utf-8") as file_open:
                  filename = file.name
                  #results["title"] = filename.split('.txt')[0]
                  #results["text"].append(file_open.read())
                  results.append(file_open.read())

      #df_temp = pd.DataFrame(results)

      # !!! WARNING - DELETE DIR
      shutil.rmtree(txt_dir)
      shutil.rmtree(pdf_dir)

      return results


def bulk_pdf_to_text(DATA_PATH, QUERY):
      done = []
      problem = []

      if not os.path.exists(DATA_PATH + QUERY + '_txt'):
            os.makedirs(DATA_PATH + QUERY + '_txt')
      
      txt_dir = DATA_PATH + QUERY + '_txt'
      pdf_dir = DATA_PATH + QUERY + '_pdfs'
    
      for root, dirs, files in os.walk(DATA_PATH):
            for file in files:
                  path_to_pdf = os.path.join(root, file)
                  [stem, ext] = os.path.splitext(path_to_pdf)

                  #if ext == '.pdf':
                  print("Processing " + path_to_pdf)
                  pdf_contents = parser.from_file(path_to_pdf)
                  
                  txt_basename = file.split('.pdf')[0]
                  print(txt_dir)
                  print(txt_basename)
                  path_to_txt = os.path.join(txt_dir, txt_basename)

                  with open(path_to_txt, 'w', encoding='utf-8') as txt_file:
                        print("Writing contents to " + path_to_txt)
                        if pdf_contents['content'] is None:
                              pass
                        else:
                              #pdf_contents = pdf_contents['content'].replace('\n+', '\n', regex=True)
                              txt_file.write(pdf_contents['content'])

def pdf_miner_to_text(DATA_PATH, QUERY):
      done = []
      problem = []

      if not os.path.exists(DATA_PATH + QUERY + '_txt'):
            os.makedirs(DATA_PATH + QUERY + '_txt')
      
      txt_dir = DATA_PATH + QUERY + '_txt'
      pdf_dir = DATA_PATH + QUERY + '_pdfs'
    
      for root, dirs, files in os.walk(DATA_PATH):
            for file in files:
                  path_to_pdf = os.path.join(root, file)
                  [stem, ext] = os.path.splitext(path_to_pdf)

                  #if ext == '.pdf':
                  print("Processing " + path_to_pdf)

                  resource_manager = PDFResourceManager()
                  fake_file_handle = io.StringIO() #io.BytesIO()
                  
                  # Perform layout analysis for all text
                  laparams = LAParams()
                  setattr(laparams, 'all_texts', True)

                  converter = TextConverter(resource_manager, fake_file_handle, laparams=laparams)
                  page_interpreter = PDFPageInterpreter(resource_manager, converter)
                  
                  try:
                        with open(path_to_pdf, 'rb') as fh:
                              for page in PDFPage.get_pages(fh, 
                                                            caching=True,
                                                            check_extractable=True):
                                    page_interpreter.process_page(page)
                                    
                              pdf_contents = fake_file_handle.getvalue()

                        # close open handles
                        converter.close()
                        fake_file_handle.close()

                        # creating filename, path and exporting                        
                        txt_basename = file.split('.pdf')[0]

                        path_to_txt = os.path.join(txt_dir, txt_basename)

                        with open(path_to_txt, 'w', encoding='utf-8') as txt_file:
                              print("Writing contents to " + path_to_txt)
                              if pdf_contents is None:
                                    pass
                              else:
                                    #pdf_contents = pdf_contents['content'].replace('\n+', '\n', regex=True)
                                    txt_file.write(pdf_contents)
                  
                  except PDFSyntaxError:
                        print('Verify ' + file + ' is actually PDF')
                        converter.close()
                        fake_file_handle.close()
                        pass 
                  
                  except PSEOF:
                        print(file + ' is corrupted')

                  except PSSyntaxError:   
                        import pikepdf
                        print(file + ' is non-standard (e.g. PDFTex), attempting to convert')
                        with pikepdf.Pdf.open(path_to_pdf) as pdf:
                              pdf.save(path_to_pdf + '.pdf')

                  except ValueError:   
                        print('Error with ' + file)
                        pass

# New but not needed yet

from pdfminer.high_level import extract_text

def pdf_miner_bytes_to_text(DATA_PATH, QUERY):
      done = []
      problem = []

      if not os.path.exists(DATA_PATH + QUERY + '_txt'):
            os.makedirs(DATA_PATH + QUERY + '_txt')
      
      txt_dir = DATA_PATH + QUERY + '_txt'
      pdf_dir = DATA_PATH + QUERY + '_pdfs'
    
      for root, dirs, files in os.walk(DATA_PATH):
            for file in files:
                  path_to_pdf = os.path.join(root, file)
                  [stem, ext] = os.path.splitext(path_to_pdf)

                  #if ext == '.pdf':
                  print("Processing " + path_to_pdf)
                  
                  try:
                        # Perform layout analysis for all text
                        laparams = LAParams()
                        setattr(laparams, 'all_texts', True)

                        resource_manager = PDFResourceManager()
                        fake_file_handle = io.BytesIO()

                        pdf_contents = extract_text(path_to_pdf, fake_file_handle, codec='utf-8', laparams=laparams)

                        fake_file_handle.close()

                        #creating filename, path and exporting                        
                        txt_basename = file.split('.pdf')[0]
                        print(txt_dir)
                        print(txt_basename)

                        path_to_txt = os.path.join(txt_dir, txt_basename)

                        with open(path_to_txt, 'w', encoding='utf-8') as txt_file:
                              print("Writing contents to " + path_to_txt)
                              if pdf_contents is None:
                                    pass
                              else:
                                    txt_file.write(pdf_contents)
                  
                  except PDFSyntaxError:
                        print('Verify ' + file + 'is actually PDF')
                        fake_file_handle.close()
                        pass 
                  
                  except PSEOF:
                        print(file + ' is corrupted')

                  except PSSyntaxError:   
                        import pikepdf
                        print(file + ' is non-standard (e.g. PDFTex), attempting to convert')
                        with pikepdf.Pdf.open(path_to_pdf) as pdf:
                              pdf.save(path_to_pdf + '.pdf')                        