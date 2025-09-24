import streamlit as st
import google.generativeai as genai
import pdfplumber

# -------- Gemini API Setup --------
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    raise RuntimeError("API key not found in Streamlit secrets under 'GOOGLE_API_KEY'")

# Initialize model
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# -------- PDF Extraction --------
def extract_text_from_pdf(pdf_file):
    text_output = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_output += page_text + "\n"
    except Exception as e:
        raise RuntimeError(f"Failed to read PDF: {e}")
    return text_output

# -------- LLM Extraction --------
def llm_extract(text: str):
    prompt = f"""
    Extract the following fields from this watershed report
    and return in valid JSON only (no extra commentary):

    {{
      "summary": {{ "totalGoals": number, "totalBMPs": number, "completionRate": number }},
      "goals": [{{ "name": string, "status": string, "target": string, "progress": number }}],
      "bmps": [{{ "type": string, "quantity": number, "cost": number }}],
      "implementation": [{{ "name": string, "startDate": string, "endDate": string, "status": string }}],
      "monitoring": [{{ "metricName": string, "baseline": string, "target": string }}],
      "outreach": [{{ "type": string, "count": number }}],
      "geographicAreas": [{{ "name": string, "acres": number, "croplandPct": number, "wetlandPct": number }}]
    }}

    Text: {text}
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise RuntimeError(f"Gemini extraction failed: {e}")
