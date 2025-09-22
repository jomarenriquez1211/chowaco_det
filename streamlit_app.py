import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

try:
    # Load credentials from secrets
    service_account_info = dict(st.secrets["gspread"])

    # Authenticate using the service account
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    # Connect to Google Sheets
    gc = gspread.authorize(credentials)

    # Test: Open a Google Sheet by name
    SHEET_NAME = "Test Sheet"  # Replace with your actual sheet name
    sh = gc.open(SHEET_NAME)

    # Optionally, read from the first worksheet
    worksheet = sh.get_worksheet(0)
    values = worksheet.get_all_values()

    st.success(f"✅ Successfully connected to Google Sheet: '{SHEET_NAME}'")
    st.write("📄 First few rows:")
    st.dataframe(values[:5])  # show first 5 rows

except Exception as e:
    st.error(f"❌ Failed to connect to Google Sheets: {e}")
