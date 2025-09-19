import streamlit as st
import pdfplumber

st.set_page_config(page_title="PDF Structured Extractor", layout="centered")
st.title("📑 PDF Structured Extractor")

uploaded_files = st.file_uploader(
    "Upload one or more PDF files",
    type="pdf",
    accept_multiple_files=True
)

if uploaded_files:
    file_names = [file.name for file in uploaded_files]

    selected_files = st.multiselect(
        "Choose PDFs to process:",
        options=file_names,
        default=file_names
    )

    if st.button("Process Selected PDFs"):
        for file in uploaded_files:
            if file.name in selected_files:
                structured_text = ""
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages:
                        # Extract text with formatting
                        text = page.extract_text(x_tolerance=1, y_tolerance=1) or ""
                        structured_text += text + "\n\n"
                        
                        # Extract tables (if any)
                        tables = page.extract_tables()
                        for table in tables:
                            structured_text += "\n[TABLE]\n"
                            for row in table:
                                structured_text += " | ".join(cell or "" for cell in row) + "\n"

                st.subheader(f"📘 Extracted Text from {file.name}")
                st.text_area("Extracted text with structure", structured_text[:3000], height=200)
