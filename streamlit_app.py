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

    for file in uploaded_files:
        if file.name in selected_files:
            with pdfplumber.open(file) as pdf:
                num_pages = len(pdf.pages)
                
                # Page selector
                st.subheader(f"📘 {file.name}")
                selected_page = st.number_input(
                    f"Select page (1-{num_pages}) for {file.name}", 
                    min_value=1, 
                    max_value=num_pages, 
                    value=1, 
                    key=file.name  # unique key per file
                )
                
                # Extract text from selected page
                page = pdf.pages[selected_page - 1]
                page_text = page.extract_text(x_tolerance=1, y_tolerance=1) or ""
                
                # Extract tables (if any)
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        page_text += "\n\n[TABLE]\n"
                        for row in table:
                            page_text += " | ".join(cell or "" for cell in row) + "\n"

                st.text_area(
                    f"📄 Page {selected_page} content",
                    page_text,
                    height=300
                )
