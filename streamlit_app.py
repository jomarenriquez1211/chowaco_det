import streamlit as st
import pdfplumber
import re
import openai
import json
import os

openai.api_key = "YOUR_OPENAI_API_KEY"

st.title("📑 PDF Extractor (LLM + Regex Hybrid)")

uploaded_files = st.file_uploader(
    "Upload one or more PDF files",
    type="pdf",
    accept_multiple_files=True
)

# Output folder
output_dir = "extracted_reports"
os.makedirs(output_dir, exist_ok=True)

# Regex pre-fill function for summary
def regex_extract(text):
    total_goals = len(re.findall(r"Goal\s+\d+", text, re.IGNORECASE))
    total_bmps = len(re.findall(r"BMP\s+\d+", text, re.IGNORECASE))
    completion_matches = re.findall(r"Completion Rate:\s*(\d+)%", text)
    completion_rate = int(completion_matches[0]) if completion_matches else 0
    return {
        "totalGoals": total_goals,
        "totalBMPs": total_bmps,
        "completionRate": completion_rate
    }

# Extract PDF text
def extract_pdf_text(file):
    full_text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            full_text += text + "\n"
    return full_text

# LLM extraction function
def llm_extract(text):
    prompt = f"""
    Extract a structured report from the following text and format it as JSON
    that matches the TypeScript interface 'ExtractedReport':

    {text}

    JSON structure:
    {{
      "summary": {{ "totalGoals": number, "totalBMPs": number, "completionRate": number }},
      "goals": [],
      "bmps": [],
      "implementation": [],
      "monitoring": [],
      "outreach": [],
      "geographicAreas": []
    }}

    Make sure all fields are present, even if empty.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts structured JSON from reports."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    output_text = response.choices[0].message['content']

    try:
        return json.loads(output_text)
    except json.JSONDecodeError:
        # fallback to regex summary and empty arrays
        return {
            "summary": regex_extract(text),
            "goals": [],
            "bmps": [],
            "implementation": [],
            "monitoring": [],
            "outreach": [],
            "geographicAreas": []
        }

# Process uploaded PDFs
if uploaded_files:
    for file in uploaded_files:
        st.write(f"Processing: {file.name}")
        text = extract_pdf_text(file)
        report = llm_extract(text)

        # Save JSON
        output_path = os.path.join(output_dir, f"{file.name}_report.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    st.success(f"Extraction complete! JSON reports saved in `{output_dir}`")
