import streamlit as st
from PyPDF2 import PdfReader

st.set_page_config(page_title="Multi-PDF Extractor", layout="wide")

st.title("📑 Multi-PDF Extractor")

# Upload multiple PDFs
uploaded_files = st.file_uploader(
    "Upload one or more PDF files",
    type="pdf",
    accept_multiple_files=True
)

if uploaded_files:
    # Show list of uploaded files
    file_names = [file.name for file in uploaded_files]
    
    # Let user select one or more PDFs to process
    selected_files = st.multiselect(
        "Select PDF(s) to extract text from:",
        options=file_names,
        default=file_names  # preselect all
    )

    if st.button("Process Selected PDFs"):
        all_texts = {}
        for file in uploaded_files:
            if file.name in selected_files:
                pdf_reader = PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
                all_texts[file.name] = text

        # Display results
        for name, text in all_texts.items():
            st.subheader(f"📘 Extracted Text from {name}")
            st.text_area("Extracted text", text[:3000], height=200)  # show preview
