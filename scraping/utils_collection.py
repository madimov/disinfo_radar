import re
from itertools import combinations, permutations, chain
from datetime import datetime, timedelta
from bs4 import BeautifulSoup as soup

def split_article_on(objects, tag, txt, string_sep=None, parse=True):
      '''
      Splits a full text article on a list of seperators
      objects = the html/soup object
      tag = the seperator tag
      txt= the full text
      parse = set to False to disable this function
      string_sep = a string to split on,
                  this currently looks if string appears 5x or more
                  see line 21 to change
                  "objects" is not needed in this case, but keeping for uniformity
      TO DO: add functionality to do on a String
      '''
      if parse == False:
            header_list_sub = ['(not parsed']
            return txt, header_list_sub
      else:
            header_list_sub = []
            if string_sep is not None:
                  print('String seperator found')
                  header_list_sub = re.findall(string_sep + '{5,}', txt)

            else:
                  header_list_sub = []
                  headers = objects.find_all(tag) 

                  for head in headers:
                        if head.text == '':
                              pass
                        else:
                              header_list_sub.append(head.text)    
            
            default_sep = header_list_sub[0]

            # we skip seps[0] because that's the default separator
            for sep in header_list_sub[1:]:
                  txt = txt.replace(sep, default_sep)
            split_text = [i.strip() for i in txt.split(default_sep)]

            # First section has no "header" so adding one to equalized list lengths            
            while len(header_list_sub) != len(split_text):
                  header_list_sub.insert(0, 'Intro (no tag)')

            split_text = [str(x[0]) + x[1] + x[2] for x in zip(header_list_sub, list(' ' * len(split_text)), split_text)]

            return split_text, header_list_sub

def aggragate(df, group_on, column):
      '''
      Never forget your docstrings!
      Drop duplicate rows based on "group_on"
      Merges data in all "column" rows
      '''
      cmnts = {}
      for i, row in df.iterrows():
            while True:
                  try:
                        if row[column]:
                              cmnts[row[group_on]].append(row[column])
                        else:
                              cmnts[row[group_on]].append('n/a')
                        
                        break

                  except KeyError:
                        cmnts[row[group_on]] = []

      df.drop_duplicates(group_on, inplace=True)

      df[column] = [', '.join(v) for v in cmnts.values()]

      return df

def datetime_parse(x):
      '''
      Parse datetime out of a string
      More functionality should be added as issues encountered 
      Has some serious issues as it stands... not a hard fix, but time consuming 
      '''
      # Remove all non-alpha-numeric
      out = re.sub(r'[^0-9a-zA-Z:]+', ' ', x)

      ## Remove any starting tag with :
      # str.split('Updated: ', expand=True)
      
      # Remove time 
      out.replace(r'\b(([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?\s?([AaPp][Mm])?)', ' ')
      
      month_dict = {
      'January':'1', 'February':'2', 'March':'3', 'April':'4', 'May':'5', 'June':'6',
      'July':'7', 'August':'8', 'September':'9', 'October':'10', 'November':'11', 
      'December':'12', 'Jan':'1', 'Feb':'2', 'Mar':'3', 'Apr':'4', 'May':'5',
      'Jun':'6', 'Jul':'7', 'Aug':'8', 'Sep':'9', 'Oct':'10', 'Nov':'11', 'Dec':'12'
      }

      # Not needed, replaces months with number value, but strtime does that
      #out = [out.replace(key, value) for key, value in month_dict.items() if key in out][0]
      
      # Removing digits longer than 4 long 
      out = re.sub(r'[0-9]\d{4,}', ' ', out)
      #out = re.sub(r'[0-9]+:[0-9]+', ' ', out) # ???

      # Removing all non-digits and words not in months
      out = out.split(' ')
      out = [word for word in out if word.isdigit() or word in list(month_dict.keys())]
      out = ' '.join(out[:3])
      
      # Strip loose whitespace
      out = out.strip()
      
      # Lists for parsing
      month = ['%b', '%m', '%B']
      day = ['%d']
      year = ['%Y', '%y']

      varieties = list(permutations(chain(year, day, month), 3))
      for v in varieties:
            v = ' '.join(v)
            try:
                  date = [datetime.strptime(str(out), v)]# if d != 0 else d for d in out] #old tag used elsewhere, here for ref.
  
                  if date is not None:
                        print('Successfully parsed with format: ' + v)
                        return date
                        break
            except:
                  #print('Failed: ' + v)
                  pass