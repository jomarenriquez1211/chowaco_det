import os
import json

# If using GitHub secrets or Streamlit secrets:
service_account_info = st.secrets["GCP_SA_CREDENTIALS"]  # This is the JSON string

# Write to a temp file
service_account_path = "temp_service_account.json"
with open(service_account_path, "w") as f:
    f.write(service_account_info)

# Use this path for Google credentials
from google.oauth2.service_account import Credentials

credentials = Credentials.from_service_account_file(
    service_account_path,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
