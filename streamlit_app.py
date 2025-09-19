import streamlit as st
import pdfplumber
import requests
import json

# ------------------------
# Gemini API setup
# ------------------------
GEMINI_API_KEY = "AIzaSyBg8kL0hF3fU78WqjTkgiap800F8kf_Meg"
GEMINI_API_URL = "https://api.generativeai.googleapis.com/v1beta2/models/gemini-1.5:predict"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {GEMINI_API_KEY}"
}

# ------------------------
# Streamlit UI
# ------------------------
st.title("📄 PDF to Structured Data using Gemini API")

uploaded_file = st.file_uploader("Drag and drop a PDF", type="pdf")

if uploaded_file:
    # 1️⃣ Extract text from PDF
    text_output = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_output += page_text + "\n"

    st.subheader("Raw PDF Text")
    st.text_area("Extracted Text", text_output, height=300)

    # 2️⃣ Prepare prompt for Gemini
    prompt = f"""
You are an intelligent data extraction assistant. Extract the following structured report from the text below.

interface ExtractedReport {{
  summary: {{
    totalGoals: number;
    totalBMPs: number;
    completionRate: number;
  }};
  goals: Goal[];
  bmps: BMP[];
  implementation: ImplementationActivity[];
  monitoring: MonitoringMetric[];
  outreach: OutreachActivity[];
  geographicAreas: GeographicArea[];
}}

Text:
{text_output}

Return valid JSON matching this interface.
"""

    # 3️⃣ Use Gemini API
    if st.button("Extract Structured Data"):
        with st.spinner("Processing with Gemini API..."):
            try:
                payload = {
                    "instances": [{"content": prompt}],
                    "parameters": {"max_output_tokens": 1500}
                }

                response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
                response.raise_for_status()

                llm_output = response.json()["predictions"][0]["content"]

                # Try parsing JSON
                structured_data = json.loads(llm_output)
                
                st.subheader("Structured Data")
                st.json(structured_data)

                st.download_button(
                    "📥 Download JSON",
                    data=json.dumps(structured_data, indent=2),
                    file_name=f"{uploaded_file.name.replace('.pdf','')}_structured.json",
                    mime="application/json"
                )

            except json.JSONDecodeError:
                st.error("Failed to parse LLM output as JSON. Here is raw output:")
                st.code(llm_output)

            except Exception as e:
                st.error(f"An error occurred: {e}")
