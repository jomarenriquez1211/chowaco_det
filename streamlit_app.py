import streamlit as st
from google.oauth2.service_account import Credentials

try:
    # Convert Streamlit secrets into a credentials dict
    service_account_info = dict(st.secrets["gspread"])

    # Load credentials from dict
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    st.success("✅ Service account credentials loaded successfully!")

except Exception as e:
    st.error(f"❌ Failed to load credentials: {e}")
