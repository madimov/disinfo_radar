import pandas as pd
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import io
import os
import gspread
from gspread_dataframe import set_with_dataframe
import openpyxl
import atexit

# gc = gspread.service_account("driveproject-392612-86425acec0ff.json")
# dir_path = os.path.dirname(os.path.realpath(__file__))
# json_path = os.path.join(dir_path, "driveproject-392612-86425acec0ff.json")
# gc = gspread.service_account(json_path)

def create_dataframe(file_id):
    # define the scope
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

    # add your service account file
    creds = Credentials.from_service_account_file('driveproject-392612-86425acec0ff.json', scopes=scope)

    # authenticate Google Drive API client
    drive_service = build('drive', 'v3', credentials=creds)

    # create request to get the file
    request = drive_service.files().get_media(fileId=file_id)

    # create an in-memory file
    fh = io.BytesIO()

    # create media downloader
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))

    # create pandas dataframe
    df = pd.read_excel(fh, engine='openpyxl')

    return df



def save_dataframe_to_drive(df, file_name, folder_id):
    # define the scope
    scope = ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive.file',
             'https://www.googleapis.com/auth/drive']

    # add your service account file
    creds = service_account.Credentials.from_service_account_file('driveproject-392612-86425acec0ff.json', scopes=scope)

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



def create_dataframe_from_folder(folder_id):
    # define the scope
    scope = ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive.file',
             'https://www.googleapis.com/auth/drive']

    # add your service account file
    creds = service_account.Credentials.from_service_account_file('driveproject-392612-86425acec0ff.json', scopes=scope)

    # authenticate Google Drive API client
    drive_service = build('drive', 'v3', credentials=creds)

    # query the files in the folder
    query = f"'{folder_id}' in parents and name contains 'data' and mimeType contains 'spreadsheet'"
    results = drive_service.files().list(q=query).execute()
    items = results.get('files', [])

    # empty DataFrame to append each file into
    full_df = pd.DataFrame()

    # download and append each file
    for item in items:
        # create request to get the file
        request = drive_service.files().export_media(fileId=item['id'],
                                                     mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        # create an in-memory file
        fh = io.BytesIO()

        # create media downloader
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))

        # create pandas dataframe and append to full_df
        df = pd.read_excel(fh, engine='openpyxl')
        full_df = pd.concat([full_df, df], ignore_index=True)

    return full_df


import numpy as np

def save_dataframe_in_tab(df, spreadsheet_id, new_tab_name):
    # Define the scope
    scope = ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive.file',
             'https://www.googleapis.com/auth/drive']

    # Add your service account file
    creds = service_account.Credentials.from_service_account_file('driveproject-392612-86425acec0ff.json', scopes=scope)

    # Authenticate Google Sheets API client
    sheets_service = build('sheets', 'v4', credentials=creds)

    # Check if the new_tab_name already exists in the spreadsheet
    spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    tab_exists = False
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == new_tab_name:
            tab_exists = True
            break

    if tab_exists:
        # Clear the existing tab
        clear_request = sheets_service.spreadsheets().values().clear(spreadsheetId=spreadsheet_id, range=new_tab_name)
        clear_request.execute()
    else:
        # Create a new sheet in the spreadsheet
        requests = [
            {
                'addSheet': {
                    'properties': {
                        'title': new_tab_name
                    }
                }
            }
        ]
        batch_update_request = sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': requests})
        batch_update_request.execute()

    # Convert the DataFrame to a 2D list
    df = df.replace(np.nan, '', regex=True)  # Replace 'NaN' values with empty strings
    df_values = df.values.tolist()
    df_headers = [list(df.columns)]
    df_data = df_headers + df_values

    # Write data to the new tab
    data = {
        'values': df_data
    }
    sheets_service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=new_tab_name, body=data, valueInputOption='USER_ENTERED').execute()


from google.oauth2 import service_account
from googleapiclient.discovery import build
import numpy as np

from google.oauth2 import service_account
from googleapiclient.discovery import build
import numpy as np


def save_dataframe_preserve_col_A(df, spreadsheet_id, new_tab_name):
    # Define the scope
    scope = ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive.file',
             'https://www.googleapis.com/auth/drive']

    # Add your service account file
    creds = service_account.Credentials.from_service_account_file('driveproject-392612-86425acec0ff.json', scopes=scope)

    # Authenticate Google Sheets API client
    sheets_service = build('sheets', 'v4', credentials=creds)

    # Check if the new_tab_name already exists in the spreadsheet
    spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    tab_exists = False
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == new_tab_name:
            tab_exists = True
            break

    if not tab_exists:
        # Create a new sheet in the spreadsheet
        requests = [
            {
                'addSheet': {
                    'properties': {
                        'title': new_tab_name
                    }
                }
            }
        ]
        batch_update_request = sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': requests})
        batch_update_request.execute()
    else:
        # Fetch data from column A of the existing tab
        col_A_data = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id,
                                                                range=f"{new_tab_name}!A:A").execute()
        col_A_values = col_A_data.get('values', [])

    # Convert the DataFrame to a 2D list
    df = df.replace(np.nan, '', regex=True)  # Replace 'NaN' values with empty strings
    df_values = df.values.tolist()
    df_headers = [list(df.columns)]
    df_data = df_headers + df_values

    # Define the range starting from B1
    range_name = f"{new_tab_name}!B1"

    # Write data to the tab (excluding Column A)
    data = {
        'values': df_data
    }
    sheets_service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=range_name, body=data, valueInputOption='USER_ENTERED').execute()

    # If there's data in column A, rewrite it back to the sheet to preserve it
    if col_A_values:
        col_A_list = [row[0] if len(row) > 0 else '' for row in col_A_values]
        data_A = {
            'values': [[value] for value in col_A_list]
        }
        sheets_service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=f"{new_tab_name}!A1:A{len(col_A_list)}", body=data_A, valueInputOption='USER_ENTERED').execute()

def main():
    # pipeline = DisinfoPipeline()
    # pipeline.run()

    df_google_output_test = pd.DataFrame({"a": [1, 2], "b": [3,4]}).astype("str")
    save_dataframe_to_drive(df_google_output_test, "df_google_output_test.xlsx", "1XmS1IlBZ4FXHK81cks2L2J8uS884Twwv")

if __name__ == "__main__":
    main()