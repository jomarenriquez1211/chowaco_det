import json
import streamlit as st
from google.oauth2.service_account import Credentials

try:
    # Load JSON string from Streamlit secrets
    json_str = st.secrets["gspreads"]

    # Parse JSON string to dictionary
    service_account_info = json.loads(json_str)

    # Create Credentials object
    credentials = Credentials.from_service_account_info(
        service_account_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    
    # If no exception so far, it means credentials loaded successfully
    st.success("✅ Service account credentials loaded successfully!")

except Exception as e:
    st.error(f"❌ Failed to load credentials: {e}")
