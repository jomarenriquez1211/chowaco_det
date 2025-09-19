import streamlit as st
import pdfplumber
import json
import openai

# Set your OpenAI API key in Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.title("📄 PDF to Structured Data Extraction")

uploaded_file = st.file_uploader("Drag and drop a PDF", type="pdf")
if uploaded_file:
    # Step 1: Extract raw text from PDF
    text_output = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_output += text + "\n"

    st.subheader("Raw PDF Text")
    st.text_area("Extracted Text", text_output, height=300)

    # Step 2: Use LLM to structure the data
    prompt = f"""
You are an intelligent data extraction assistant. 
Extract data from the text below and structure it in JSON according to this interface:

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

Return valid JSON that fits the above structure.
"""

    if st.button("Extract Structured Data"):
        with st.spinner("Structuring data using LLM..."):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            llm_output = response['choices'][0]['message']['content']

            # Step 3: Parse and display JSON
            try:
                structured_data = json.loads(llm_output)
                st.subheader("Structured Data")
                st.json(structured_data)

                # Allow downloading as JSON
                st.download_button(
                    "📥 Download JSON",
                    data=json.dumps(structured_data, indent=2),
                    file_name=f"{uploaded_file.name.replace('.pdf','')}_structured.json",
                    mime="application/json"
                )
            except json.JSONDecodeError:
                st.error("LLM output could not be parsed as JSON.")
                st.code(llm_output)
