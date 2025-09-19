import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import json
from googleapiclient.errors import HttpError

st.title("📑 PDF Uploader to Google Shared Drive (No Duplicates)")

uploaded_files = st.file_uploader(
    "Drag & drop PDF files here",
    type="pdf",
    accept_multiple_files=True
)

# Load service account from secrets
service_account_info = json.loads(st.secrets["gdrive"]["service_account"])
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/drive"]
)

drive_service = build('drive', 'v3', credentials=credentials)
SHARED_DRIVE_ID = st.secrets["gdrive"]["shared_drive_id"]
FOLDER_ID = st.secrets["gdrive"]["folder_id"]  # optional, can be None

# Check if file exists in the folder
def file_exists_in_drive(file_name, folder_id=None):
    if folder_id:
        query = f'name="{file_name}" and "{folder_id}" in parents'
    else:
        query = f'name="{file_name}"'

    try:
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            corpora='drive',
            driveId=SHARED_DRIVE_ID,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields='files(id, name)'
        ).execute()
        return results.get('files', [])
    except HttpError as e:
        st.error(f"Google Drive query failed for {file_name}: {e}")
        return []

# Upload files to Shared Drive
if uploaded_files:
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        existing_files = file_exists_in_drive(file_name, FOLDER_ID)

        if existing_files:
            st.warning(f"{file_name} already exists in Google Drive. Skipping upload.")
        else:
            try:
                file_bytes = uploaded_file.read()
                file_metadata = {'name': file_name}
                if FOLDER_ID:
                    file_metadata['parents'] = [FOLDER_ID]

                media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='application/pdf')
                uploaded = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id',
                    supportsAllDrives=True
                ).execute()
                st.success(f"{file_name} uploaded successfully! File ID: {uploaded.get('id')}")
            except HttpError as e:
                st.error(f"Failed to upload {file_name}: {e}")
