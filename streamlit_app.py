import streamlit as st
from PyPDF2 import PdfReader
from transformers import pipeline

# Load a free Hugging Face LLM (distilbert, flan-t5, etc.)
nlp = pipeline("text2text-generation", model="google/flan-t5-base")

st.title("📄 Free PDF Extractor with Hugging Face")

uploaded_files = st.file_uploader(
    "Upload PDFs", type=["pdf"], accept_multiple_files=True
)

if uploaded_files:
    pdf_texts = {}

    for uploaded_file in uploaded_files:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        pdf_texts[uploaded_file.name] = text

    selected_files = st.multiselect(
        "Select PDF(s) for processing:", list(pdf_texts.keys())
    )

    if st.button("🔍 Extract with Hugging Face"):
        for file_name in selected_files:
            with st.spinner(f"Processing {file_name}..."):
                prompt = f"""
                Extract and categorize this PDF content into JSON with fields:
                summary, goals, bmps, implementation, monitoring, outreach, geographicAreas.
                
                Content:
                {pdf_texts[file_name]}
                """

                result = nlp(prompt, max_length=512, truncation=True)[0]['generated_text']
                st.subheader(f"Results for {file_name}")
                st.json(result)
