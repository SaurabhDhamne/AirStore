import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_file:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is not set in .env")

    # If it's just the filename, resolve it explicitly to the backend folder
    if not os.path.isabs(creds_file):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        creds_file = os.path.join(base_dir, creds_file)

    if not os.path.exists(creds_file):
        raise ValueError(f"Google Credentials file NOT found at: {creds_file}. Please check the filename in your .env!")

    
    creds = service_account.Credentials.from_service_account_file(
        creds_file, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service

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
