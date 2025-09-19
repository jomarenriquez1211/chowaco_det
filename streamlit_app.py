from openai import OpenAI
from PyPDF2 import PdfReader
import streamlit as st

# ✅ Load API key from Streamlit secrets
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# Streamlit UI
st.title("📄 PDF Intelligent Extractor")

uploaded_files = st.file_uploader(
    "Upload one or more PDF reports",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    pdf_texts = {}

    for uploaded_file in uploaded_files:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        pdf_texts[uploaded_file.name] = text

    # Let user select which PDFs to analyze
    selected_files = st.multiselect(
        "Select PDF(s) for GPT processing:",
        options=list(pdf_texts.keys())
    )

    if st.button("🔍 Extract with GPT"):
        for file_name in selected_files:
            with st.spinner(f"Processing {file_name} with GPT..."):
                prompt = f"""
                You are a helpful assistant. Extract and categorize the following PDF content
                into the structure below. If something doesn’t exist, leave it empty.

                Expected JSON structure:
                {{
                  "summary": {{
                    "totalGoals": number,
                    "totalBMPs": number,
                    "completionRate": number
                  }},
                  "goals": [],
                  "bmps": [],
                  "implementation": [],
                  "monitoring": [],
                  "outreach": [],
                  "geographicAreas": []
                }}

                PDF content:
                {pdf_texts[file_name]}
                """

                response = client.chat.completions.create(
                    model="gpt-4o-mini",  # or "gpt-4" if you have access
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )

                extracted = response.choices[0].message.content
                st.subheader(f"Results for {file_name}")
                st.json(extracted)
