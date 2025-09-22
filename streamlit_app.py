from google.oauth2.service_account import Credentials
import streamlit as st

try:
    # Convert Streamlit secrets dict to service account dict
    service_account_info = dict(st.secrets["gspread"])
    
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    st.success("✅ Service account loaded successfully (via split secrets)")
except Exception as e:
    st.error(f"❌ Failed to load credentials: {e}")
