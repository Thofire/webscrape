# -------------------------------
# Google Sheets Setup
# -------------------------------
import gspread
from google.oauth2.service_account import Credentials
def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open("Prices").sheet1
    sheet.clear()
    sheet.append_row(['Site', 'URL', 'Item', 'Price'])
    return sheet

# -------------------------------
# Upload to Google Sheets
# -------------------------------
def upload_to_sheets(sheet, all_data):
    for row in all_data:
        sheet.append_row(list(row))     
    print("\n✅ Done! Data uploaded to Google Sheets.")
    