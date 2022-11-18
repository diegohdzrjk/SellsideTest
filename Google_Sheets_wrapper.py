######################################
# Code Author: Diego Hernandez Rajkov
# Date: Aug - 2021
# Python version: Python 3
######################################

# Libraries
import socket
import os.path
import pickle
import json
import traceback
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from oauth2client.client import AccessTokenCredentials
import urllib
import streamlit as st
from httplib2 import Http
from apiclient import discovery
import numpy as np

######################################################################
##                       Google Sheets service                      ##
######################################################################

import os 
dir_path = os.path.dirname(os.path.realpath(__file__))
dir_path = "/".join(dir_path.split("/")[:-1])
GOOGLE_SHEETS_CREDENTIALS_FOLDER = ""#dir_path+"/Credentials/GoogleSheets/"

# Refresh token
client_id     = st.secrets["GoogleSheets_client_id"]
client_secret = st.secrets["GoogleSheets_client_secret"]
refresh_token = st.secrets["GoogleSheets_refresh_token"]


def get_GS_service(use_refreshed_token=True, servicetype='sheets', version='v4'):
    if use_refreshed_token:
        print("Trying: Using a refreshed token")
        return get_service_refreshed_token(servicetype, version)
    else:
        print("Trying: Using credentials")
        return get_GS_service_CREDS(servicetype, version)
    
def refresh_access_token():
    data = urllib.parse.urlencode({'grant_type':    'refresh_token',
                                   'client_id':     client_id,
                                   'client_secret': client_secret,
                                   'refresh_token': refresh_token,
                                   'include_granted_scopes' :'true'
                                  }).encode("utf-8")
    
    req = urllib.request.Request('https://oauth2.googleapis.com/token', 
                                 headers={'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'})
    
    with urllib.request.urlopen(req, data=data) as f:
        resp = f.read()
        my_json = resp.decode('utf8').replace("'", '"')
        # Load the JSON to a Python list & dump it back out as formatted JSON
        data = json.loads(my_json)
        return data

def get_service_refreshed_token(servicetype='sheets', version='v4'):
    """Get a service that communicates to a Google API.
      Args:
        api_name: string The name of the api to connect to.
        api_version: string The api version to connect to.
        access_token: string with the Access Token

      Returns:
        A service that is connected to the specified API.
   """
    try:
        # Prepare the token
        access_token = refresh_access_token()

        # Prepare credentials, and authorize HTTP object with them.
        credentials = AccessTokenCredentials(access_token['access_token'], 'my-user-agent/1.0')
        http = credentials.authorize(Http())

        # Build the service object.
        service = build(servicetype, version, http=http)

        return service
    except:
        return traceback.format_exc()
    
def get_GS_service_CREDS(servicetype='sheets', version='v4'):
    """
        ---------------------------------
        Get the Google Sheets service
        ---------------------------------
        Return: 
            - the Google Sheets service
            - error flag
        ---------------------------------
    """
    socket.setdefaulttimeout(600)
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    
    try:
        if os.path.exists(GOOGLE_SHEETS_CREDENTIALS_FOLDER+'token.pickle'):
            with open(GOOGLE_SHEETS_CREDENTIALS_FOLDER+'token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_SHEETS_CREDENTIALS_FOLDER+'credentials.json', 
                                                                 SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(GOOGLE_SHEETS_CREDENTIALS_FOLDER+'token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build(servicetype, version, credentials=creds)
        return service
    except:
        return traceback.format_exc()

def get_spreadsheet_data(service, spreadsheet_id, data_to_pull):
    """
        --------------------------------------------------------
        Get the data from a Google Sheets spreadsheet
        --------------------------------------------------------
        service: Google Sheet service
        spreadsheet_id : spreadsheet id
        data_to_pull: Range to get the data from the spreadsheet
        --------------------------------------------------------
        Return:
            - data
            - status
            - error flag
        --------------------------------------------------------
    """
    socket.setdefaulttimeout(600)
    sheet = service.spreadsheets()
 
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=data_to_pull).execute()
    values = result.get('values', [])
    if not values:
        return None
    else:
        return values
   
    
    
def create_spreadsheet(service, title, pages=[]):
    """
        --------------------------------------------------------
        Create a Google Sheets spreadsheet 
        --------------------------------------------------------
        service: Google Sheet service
        title: Title of the spreadsheet
        --------------------------------------------------------
        Return:
            - spreadsheet id
            - title of the spreadsheet
            - error flag
        --------------------------------------------------------
    """
    sheets = []
    if len(pages)==0:
        sheets.append({'properties': {'title': 'Log'}})
    else:
        for pagename in pages:
            sheets.append({'properties': {'title': pagename}})
        
    spreadsheet = {'properties': {'title': title}, 'sheets': sheets}
    
    try:
        spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
        return spreadsheet.get('spreadsheetId')
    except:
        return traceback.format_exc()
    
def add_writer_perm(service, spreadsheet_id, emails):
    """
        --------------------------------------------------------
        Update permissions Google Sheets spreadsheet 
        --------------------------------------------------------
        service: Google Sheet service
        spreadsheet_id : spreadsheet id
        data_to_pull: Range to get the data from the spreadsheet
        df: Data to insert in as pandas Dataframe
        --------------------------------------------------------
        Return:
            - exe_update/error
            - error flag
        --------------------------------------------------------
    """
    try:
        for email in emails:
            user_permission = ({'type': 'user', 'role': 'writer','emailAddress': email})
            res = service.permissions().create(fileId=spreadsheet_id, body=user_permission).execute()
        return emails
    except:
        return traceback.format_exc()
    
def update_spreadsheet(service, spreadsheet_id, spreadsheet_range, df):
    """
        --------------------------------------------------------
        Update the values Google Sheets spreadsheet 
        --------------------------------------------------------
        service: Google Sheet service
        spreadsheet_id : spreadsheet id
        data_to_pull: Range to get the data from the spreadsheet
        df: Data to insert in as pandas Dataframe
        --------------------------------------------------------
        Return:
            - exe_update/error
            - status
            - error flag
        --------------------------------------------------------
    """
    socket.setdefaulttimeout(600)
    values = np.transpose([list(df.columns), *df.to_numpy().tolist()]).tolist()
    try:
        exe_update = service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=spreadsheet_range,
                                                            valueInputOption='USER_ENTERED', 
                                                            body={'majorDimension': 'COLUMNS', 'values': values}).execute()
        return exe_update
    except ValueError:
        print(ValueError)
        return None
    except:
        return traceback.format_exc()

def batch_update_spreadsheet(service, spreadsheet_id, spreadsheet_range, df):
    """
        --------------------------------------------------------
        Update the values Google Sheets spreadsheet 
        --------------------------------------------------------
        service: Google Sheet service
        spreadsheet_id : spreadsheet id
        data_to_pull: Range to get the data from the spreadsheet
        df: Data to insert in as pandas Dataframe
        --------------------------------------------------------
        Return:
            - exe_update/error
            - status
            - error flag
        --------------------------------------------------------
    """
    socket.setdefaulttimeout(600)
    response = service.spreadsheets().get(spreadsheetId=spreadsheet_id, 
                                         ranges=spreadsheet_range, 
                                         includeGridData=False).execute()
    
    sheetId = response['sheets'][0]['properties']['sheetId']
    batch_update_spreadsheet_request_body = {'requests': [{"updateCells": {"range": {"sheetId": sheetId}, 
                                                                           "fields": "userEnteredValue"}
                                                          }]
                                            }
    request = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, 
                                                 body=batch_update_spreadsheet_request_body).execute()

    values = np.transpose([list(df.columns), *df.to_numpy().tolist()]).tolist()
    try:
        exe_update = service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=spreadsheet_range,
                                                            valueInputOption='USER_ENTERED', 
                                                            body={'majorDimension': 'COLUMNS', 'values': values}).execute()
        return exe_update
    except ValueError:
        print(ValueError)
        return None
    except:
        return traceback.format_exc()
    
    
def append_to_spreadsheet(service, spreadsheet_id, spreadsheet_range, df):
    """
        --------------------------------------------------------
        Update the values Google Sheets spreadsheet 
        --------------------------------------------------------
        service: Google Sheet service
        spreadsheet_id : spreadsheet id
        data_to_pull: Range to get the data from the spreadsheet
        df: Data to insert in as pandas Dataframe
        --------------------------------------------------------
        Return:
            - exe_append/error
            - status
            - error flag
        --------------------------------------------------------
    """
    socket.setdefaulttimeout(600)
    values = np.transpose([*df.to_numpy().tolist()]).tolist()
    try:
        exe_append = service.spreadsheets().values().append(spreadsheetId=spreadsheet_id, range=spreadsheet_range, 
                                                            valueInputOption='USER_ENTERED', 
                                                            body={'majorDimension': 'COLUMNS', 'values': values}).execute()
        return exe_append
    except:
        return traceback.format_exc()
    
    
def create_log_Google_Sheet(service, title, df):
    """
        --------------------------------------------------------
        Create a log Google Sheets spreadsheet 
        --------------------------------------------------------
        service: Google Sheet service
        title: Title of the spreadsheet
        df: Log data as pandas Dataframe
        --------------------------------------------------------
        Return:
            - spreadsheet_id
            - status
            - error flag
        --------------------------------------------------------
    """
    try:
        spreadsheet_id, title, err = create_spreadsheet(service, title)
        update, status, err = update_spreadsheet(service, spreadsheet_id, 'Log', df)
        return spreadsheet_id
    except:
        return traceback.format_exc()

    
def sheetProperties(title, extrasheetProperties={}):
    default_Properties = {'properties':{'title': title,
                                        'sheetType': 'GRID',
                                        'hidden': False,
                                       }
                         }

    default_Properties['properties'].update(extrasheetProperties)
    return default_Properties

def add_sheets(service, spreadsheetId, pages, pages_data=[], extrasheetProperties={}):
    try:
        request_body = {'requests': [{'addSheet': sheetProperties(pagename, extrasheetProperties)} 
                                     for pagename in pages]}
        
        request = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=request_body).execute()
        if len(pages_data)>0:
            for pagename, df in zip(pages,pages_data):
                values = np.transpose([list(df.columns), *df.to_numpy().tolist()]).tolist()
                exe_update = service.spreadsheets().values().update(spreadsheetId=spreadsheetId, range=pagename,
                                                                    valueInputOption='USER_ENTERED', 
                                                                    body={'majorDimension': 'COLUMNS', 'values': values}
                                                                   ).execute()

        return spreadsheetId
    except:
        return traceback.format_exc()