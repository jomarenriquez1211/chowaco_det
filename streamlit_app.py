import streamlit as st
from PyPDF2 import PdfReader

st.title("📑 PDF Drag & Drop Processor")

# Drag and drop file uploader
uploaded_file = st.file_uploader("Drag and drop your PDF here", type="pdf")

if uploaded_file is not None:
    st.success("✅ File uploaded successfully!")

    # Read PDF content
    pdf_reader = PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"

    st.subheader("📄 Extracted Text")
    st.write(text[:2000])  # show first 2000 chars for preview

    # Save the PDF if needed
    with open("uploaded.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.info("PDF saved locally as `uploaded.pdf`.")
