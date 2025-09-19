import streamlit as st
import pdfplumber
import json
from openai import OpenAI

# Load API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
st.write("✅ API key loaded?", bool(st.secrets.get("OPENAI_API_KEY")))


# Function to extract text from multiple PDFs
def extract_text_from_pdfs(uploaded_files):
    all_text = ""
    for uploaded_file in uploaded_files:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"
    return all_text

# Function to call GPT-4 for structured extraction
def extract_with_gpt4(pdf_text: str):
    prompt = f"""
    You are an expert at extracting structured data from unstructured reports.
    Given the following text, extract the information into this JSON structure:

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

    IMPORTANT:
    - Only return valid JSON
    - If information is missing, use null or empty arrays
    - Infer counts if explicitly written

    Report text:
    {pdf_text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # can change to "gpt-4" if available
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    try:
        data = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        st.error("⚠️ GPT-4 response was not valid JSON.")
        return None

    return data


# ---------------- STREAMLIT APP ---------------- #

st.set_page_config(page_title="🌱 PDF Report Extractor", layout="wide")
st.title("🌱 PDF Report Extractor with GPT-4")

uploaded_files = st.file_uploader(
    "Upload one or more PDF reports", type=["pdf"], accept_multiple_files=True
)

if uploaded_files:
    st.success(f"{len(uploaded_files)} file(s) uploaded successfully.")

    if st.button("🚀 Extract Data with GPT-4"):
        with st.spinner("Extracting text from PDFs..."):
            pdf_text = extract_text_from_pdfs(uploaded_files)

        with st.spinner("Sending to GPT-4 for analysis..."):
            result = extract_with_gpt4(pdf_text)

        if result:
            st.subheader("📊 Extracted Data (JSON)")
            st.json(result)
