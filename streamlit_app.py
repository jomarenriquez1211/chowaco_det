import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Attempt to load and authenticate with Google Sheets
try:
    # Load credentials from Streamlit secrets
    service_account_info = dict(st.secrets["gspread"])

    # Authenticate using the service account
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    # Authorize gspread client
    client = gspread.authorize(credentials)

    # OPTIONAL: Try opening a spreadsheet to verify access (replace with your actual Sheet name)
    TEST_SHEET_NAME = "Your Google Sheet Name Here"
    spreadsheet = client.open(TEST_SHEET_NAME)
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_values()

    st.success("✅ Successfully connected to Google Sheets!")
    st.write("First 5 rows from the sheet:")
    st.dataframe(data[:5])

except KeyError as ke:
    st.error(f"❌ Missing key in secrets: {ke}")
except gspread.exceptions.SpreadsheetNotFound:
    st.warning(f"⚠️ Connected to Google Sheets, but spreadsheet '{TEST_SHEET_NAME}' not found.")
except Exception as e:
    st.error(f"❌ Failed to connect to Google Sheets: {e}")
