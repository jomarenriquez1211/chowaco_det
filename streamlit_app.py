import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

try:
    # Load credentials from secrets
    service_account_info = dict(st.secrets["gspread"])
    print(service_account_info)
    # Authenticate using the service account
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
