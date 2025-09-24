import streamlit as st
import pdfplumber
import google.generativeai as genai
import json

# ----------------- Gemini Setup -----------------
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("❌ API key not found in Streamlit secrets. Please add GOOGLE_API_KEY.")
    st.stop()

model = genai.GenerativeModel("gemini-1.5-flash-latest")

# ----------------- PDF Extraction -----------------
def extract_text_from_pdf(pdf_file):
    text_output = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_output += page_text + "\n"
    except Exception as e:
        st.error(f"❌ Failed to read PDF: {e}")
    return text_output

# ----------------- LLM Extraction -----------------
def llm_extract(text: str):
    prompt = f"""
    Extract the following fields from this watershed report
    and return in valid JSON only (no commentary):

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
        st.error(f"❌ Gemini extraction failed: {e}")
        return "{}"

# ----------------- Streamlit UI -----------------
st.title("📑 Bear Lake Watershed Report Extractor")

uploaded_file = st.file_uploader("Upload your watershed PDF", type=["pdf"])

if uploaded_file:
    st.success("✅ File uploaded successfully")
    with st.spinner("Extracting text..."):
        text = extract_text_from_pdf(uploaded_file)

    if text:
        st.text_area("Extracted Raw Text (preview)", text[:1000] + "...", height=200)

        if st.button("Run LLM Extraction"):
            with st.spinner("Sending to Gemini..."):
                extracted_json = llm_extract(text)

            try:
                structured_data = json.loads(extracted_json)
                st.json(structured_data)  # pretty display
            except json.JSONDecodeError:
                st.error("⚠️ LLM output is not valid JSON. Check raw output below:")
                st.text(extracted_json)
