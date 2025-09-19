import streamlit as st
import pdfplumber
import pandas as pd
import io

st.set_page_config(page_title="PDF Extractor", layout="wide")
st.title("📄 PDF Upload & Intelligent Text Extraction")

# Sidebar options
st.sidebar.header("Options")
extract_tables = st.sidebar.checkbox("Extract tables", value=True)
use_ocr = st.sidebar.checkbox("Use OCR (for scanned PDFs)", value=False)

# PDF uploader
uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
if uploaded_file:
    st.success(f"Uploaded file: {uploaded_file.name}")
    
    # Extract text and tables
    text_output = ""
    tables_list = []

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                # Extract text
                text = page.extract_text()
                if text:
                    text_output += f"--- Page {page_number} ---\n{text}\n\n"

                # Extract tables
                if extract_tables:
                    tables = page.extract_tables()
                    for table in tables:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        tables_list.append(df)

        # Display text
        st.subheader("Extracted Text")
        st.text_area("Text Content", text_output, height=400)

        # Allow download of text
        st.download_button(
            label="📥 Download Text",
            data=text_output,
            file_name=f"{uploaded_file.name.replace('.pdf','')}_text.txt",
            mime="text/plain"
        )

        # Display tables if any
        if tables_list:
            st.subheader("Extracted Tables")
            for idx, table_df in enumerate(tables_list, start=1):
                st.write(f"Table {idx}")
                st.dataframe(table_df)

            # Download tables as Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for idx, table_df in enumerate(tables_list, start=1):
                    table_df.to_excel(writer, sheet_name=f"Table_{idx}", index=False)
            st.download_button(
                label="📥 Download Tables as Excel",
                data=output.getvalue(),
                file_name=f"{uploaded_file.name.replace('.pdf','')}_tables.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Error processing PDF: {e}")
        if use_ocr:
            st.warning("OCR option is enabled but not implemented in this version.")
