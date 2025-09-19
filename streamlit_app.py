import streamlit as st
from PyPDF2 import PdfReader

st.set_page_config(page_title="PDF Selector", layout="centered")

st.title("📑 Multi-PDF Extractor")

# Upload multiple PDFs
uploaded_files = st.file_uploader(
    "Upload one or more PDF files",
    type="pdf",
    accept_multiple_files=True
)

if uploaded_files:
    file_names = [file.name for file in uploaded_files]

    # "Modal-like" section for multiple file selection
    with st.container():
        st.markdown("### 📌 Select Files")
        st.info("Multiple PDFs were uploaded. Please select one or more to process:")

        selected_files = st.multiselect(
            "Choose PDFs:",
            options=file_names,
            default=file_names  # preselect all
        )

    if st.button("Process Selected PDFs"):
        for file in uploaded_files:
            if file.name in selected_files:
                pdf_reader = PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
                
                st.subheader(f"📘 Extracted Text from {file.name}")
                st.text_area("Extracted text", text[:3000], height=200)  # preview
