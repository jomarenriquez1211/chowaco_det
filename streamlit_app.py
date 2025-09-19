import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

st.title("Upload PDFs to Google Drive (No Duplicates)")

uploaded_files = st.file_uploader(
    "Drag and drop PDF files here",
    type="pdf",
    accept_multiple_files=True
)

# --- Google Drive setup ---
SERVICE_ACCOUNT_FILE = "service_account.json"  # Your key
SCOPES = ['https://www.googleapis.com/auth/drive.file']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=credentials)

# Optional: specify a folder ID in Drive
FOLDER_ID = "your_folder_id_here"  # leave as None to use root

def file_exists_in_drive(file_name, folder_id=None):
    query = f"name='{file_name}'"
    if folder_id:
        query += f" and '{folder_id}' in parents"
    results = drive_service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    return results.get('files', [])

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        existing_files = file_exists_in_drive(file_name, FOLDER_ID)
        
        if existing_files:
            st.warning(f"{file_name} already exists in Google Drive. Skipping upload.")
        else:
            file_bytes = uploaded_file.read()
            file_metadata = {'name': file_name}
            if FOLDER_ID:
                file_metadata['parents'] = [FOLDER_ID]

            media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='application/pdf')
            uploaded = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            st.success(f"{file_name} uploaded successfully! File ID: {uploaded.get('id')}")
