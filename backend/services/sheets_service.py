import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

import json

def get_sheets_service():
    # 1. First, check if there's a raw JSON string in the environment (Render deployment)
    creds_json_string = os.getenv("GOOGLE_CREDENTIALS_JSON")
    
    if creds_json_string:
        try:
            creds_dict = json.loads(creds_json_string)
            creds = service_account.Credentials.from_service_account_info(
                creds_dict, scopes=SCOPES)
            return build('sheets', 'v4', credentials=creds)
        except Exception as e:
            raise ValueError(f"Failed to parse GOOGLE_CREDENTIALS_JSON: {e}")

    # 2. Fallback to local file-based credentials
    creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_file:
        raise ValueError("Neither GOOGLE_CREDENTIALS_JSON nor GOOGLE_APPLICATION_CREDENTIALS is set in .env")

    # If it's just the filename, resolve it explicitly to the backend folder
    if not os.path.isabs(creds_file):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        creds_file = os.path.join(base_dir, creds_file)

    if not os.path.exists(creds_file):
        raise ValueError(f"Google Credentials file NOT found at: {creds_file}.")
    
    creds = service_account.Credentials.from_service_account_file(
        creds_file, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    
    return service

def get_drive_service():
    """Initializes Google Drive API to download the spreadsheet."""
    creds_json_string = os.getenv("GOOGLE_CREDENTIALS_JSON")
    DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    if creds_json_string:
        creds_dict = json.loads(creds_json_string)
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=DRIVE_SCOPES)
        return build('drive', 'v3', credentials=creds)

    creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not os.path.isabs(creds_file):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        creds_file = os.path.join(base_dir, creds_file)
        
    creds = service_account.Credentials.from_service_account_file(creds_file, scopes=DRIVE_SCOPES)
    return build('drive', 'v3', credentials=creds)
def append_to_sheet(spreadsheet_id: str, range_name: str, values: list[list[str]]):
    """
    Appends rows to the specified Google Sheet.
    values = [['Date', 'Name', 'Amount', 'Status'], ['10/12', 'Coffee', '5', 'Purchased']]
    """
    service = get_sheets_service()
    body = {
        'values': values
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    return result

def create_and_append_sheet(spreadsheet_id: str, new_sheet_name: str, values: list[list[str]]) -> int:
    """
    Dynamically creates a new tab inside the Google Sheets file, adds headers, and appends the data.
    Returns the newly created sheet's gid (sheetId).
    """
    service = get_sheets_service()

    # 1. Create a new sheet
    requests = [{
        "addSheet": {
            "properties": {"title": new_sheet_name}
        }
    }]
    
    body = {"requests": requests}
    try:
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        new_sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
    except Exception as e:
        print(f"Error creating sheet: {e}")
        raise
        
    # 2. Add header row + data rows to the new sheet
    headers = [["Date", "Description/Name", "Amount", "Status"]]
    full_data = headers + values
    
    append_to_sheet(spreadsheet_id, f"{new_sheet_name}!A:D", full_data)
    
    return new_sheet_id

import io
from googleapiclient.http import MediaIoBaseDownload

def export_sheet_to_xlsx(spreadsheet_id: str, output_path: str):
    """
    Downloads the entire Google Spreadsheet (including the newly added tab) as an .xlsx file.
    """
    drive_service = get_drive_service()
    request = drive_service.files().export_media(
        fileId=spreadsheet_id, 
        mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    with io.FileIO(output_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
