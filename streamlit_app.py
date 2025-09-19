import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import json

st.title("📑 PDF Uploader to Google Drive (No Duplicates)")

uploaded_files = st.file_uploader(
    "Drag & drop PDF files here",
    type="pdf",
    accept_multiple_files=True
)

# Load service account from secrets
service_account_info = json.loads(st.secrets["gdrive"]["service_account"])
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/drive.file"]
)

drive_service = build('drive', 'v3', credentials=credentials)
FOLDER_ID = st.secrets["gdrive"]["folder_id"]

def file_exists_in_drive(file_name, folder_id):
    query = f"name='{file_name}' and '{folder_id}' in parents"
    results = drive_service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    return results.get('files', [])

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        if file_exists_in_drive(file_name, FOLDER_ID):
            st.warning(f"{file_name} already exists in Google Drive. Skipping upload.")
        else:
            file_bytes = uploaded_file.read()
            file_metadata = {'name': file_name, 'parents': [FOLDER_ID]}
            media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='application/pdf')
            uploaded = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            st.success(f"{file_name} uploaded successfully! File ID: {uploaded.get('id')}")
