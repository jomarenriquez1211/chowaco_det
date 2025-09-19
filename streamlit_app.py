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

    # Show "modal-like" box for selection (using Streamlit container + markdown)
    with st.container():
        st.markdown("### 📌 Select File")
        st.info("Multiple PDFs were uploaded. Please select the file to process:")

        selected_file = st.radio(
            "Choose one PDF:", 
            options=file_names,
            index=0
        )

    if st.button("Process Selected PDF"):
        for file in uploaded_files:
            if file.name == selected_file:
                pdf_reader = PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
                
                st.subheader(f"📘 Extracted Text from {selected_file}")
                st.text_area("Extracted text", text[:3000], height=200)  # preview
