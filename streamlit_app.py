import streamlit as st
import pdfplumber
import json
import re
import jsonschema
from jsonschema import validate
import google.generativeai as genai

# -------- Gemini Setup --------
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("❌ API key not found in Streamlit secrets. Please add GOOGLE_API_KEY.")
    st.stop()

model = genai.GenerativeModel("gemini-1.5-flash-latest")

# -------- Helpers --------
def extract_text_from_pdf(pdf_file):
    """Extract raw text from uploaded PDF"""
    text_output = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_output += page_text + "\n"
    return text_output

def get_json_schema():
    """Load dashboard schema definition from schema.json"""
    with open("schema.json", "r", encoding="utf-8") as f:
        return json.load(f)

def validate_json(data, schema):
    """Validate data against schema.json"""
    try:
        validate(instance=data, schema=schema)
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        return False, str(e)

def sanitize_llm_output(text: str) -> str:
    """Clean Gemini output so it can be parsed as JSON."""
    if not text:
        return ""
    # Remove markdown code fences
    text = re.sub(r"```(?:json)?", "", text)
    # Strip whitespace
    text = text.strip()
    # Extract first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end+1]
    return text

# -------- LLM Extraction --------
def llm_extract(text: str):
    prompt = f"""
    You are a data extractor. 
    Analyze the following watershed report and return ONLY one valid JSON object.

    The JSON must strictly follow this structure:

    {{
      "summary": {{
        "totalGoals": number,
        "totalBMPs": number,
        "completionRate": number
      }},
      "goals": [
        {{ "name": string, "status": string, "target": string, "progress": number }}
      ],
      "bmps": [
        {{ "type": string, "quantity": number, "cost": number }}
      ],
      "implementation": [
        {{ "name": string, "startDate": "YYYY-MM-DD", "endDate": "YYYY-MM-DD", "status": string }}
      ],
      "monitoring": [
        {{ "metricName": string, "baseline": string, "target": string }}
      ],
      "outreach": [
        {{ "type": string, "count": number }}
      ],
      "geographicAreas": [
        {{ "name": string, "acres": number, "croplandPct": number, "wetlandPct": number }}
      ]
    }}

    ⚠️ DATA INSTRUCTIONS:
    - Use null (not empty string) if a value is missing or unknown.
    - Dates must be in ISO format (YYYY-MM-DD). If the text says "Month 1–36" or "Year 1", set both startDate and endDate to null.
    - Quantities, costs, counts, and progress must be numbers. Remove symbols like "$" or "%".
    - Keep environmental metric units as part of the string (e.g., "5.0 mg/L").
    - Land areas must be in acres. If only % is given, calculate acres based on watershed size if possible; otherwise use null.
    - If no goals, BMPs, or outreach activities are found, return an empty array [] for that section.
    - Never output commentary, markdown, or extra text — only valid JSON.

    Report Text:
    {text}
    """
    response = model.generate_content(prompt)
    return response.text

# -------- Streamlit App --------
st.title("📑 Watershed Report Extractor with Schema Validation")

uploaded_file = st.file_uploader("Upload a Watershed Report (PDF)", type=["pdf"])

if uploaded_file:
    st.success("✅ File uploaded successfully")

    with st.spinner("Extracting text from PDF..."):
        text = extract_text_from_pdf(uploaded_file)
    st.text_area("Raw PDF Text (preview)", text[:1200] + "...", height=200)

    if st.button("Run LLM Extraction"):
        with st.spinner("Calling Gemini..."):
            raw_output = llm_extract(text)

        sanitized = sanitize_llm_output(raw_output)

        try:
            parsed = json.loads(sanitized)
        except Exception as e:
            st.error(f"⚠️ JSON parsing failed: {e}")
            st.text_area("Raw LLM output", raw_output, height=250)
            st.text_area("Sanitized attempt", sanitized, height=250)
            st.stop()

        schema = get_json_schema()
        is_valid, error_msg = validate_json(parsed, schema)

        if is_valid:
            st.success("✅ JSON is valid against schema!")
            st.json(parsed)
        else:
            st.error("⚠️ JSON does not match schema")
            st.text(error_msg)
            st.text_area("Raw LLM output", raw_output, height=250)
            st.text_area("Sanitized attempt", sanitized, height=250)
