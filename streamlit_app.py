import streamlit as st
import pdfplumber
import json
import openai

openai.api_key = st.secrets["OPENAI_API_KEY"]  # Store API key in Streamlit secrets

st.title("📄 Intelligent Report Extraction Tool")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")
if uploaded_file:
    # Extract text from PDF
    text_output = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_output += page_text + "\n"

    st.subheader("Raw Extracted Text")
    st.text_area("PDF Text", text_output, height=300)

    # Prompt LLM for structured extraction
    prompt = f"""
You are an intelligent data extraction assistant. Extract the following fields in valid JSON:

Fields:
- summary: totalGoals (number), totalBMPs (number), completionRate (percentage number)
- goals: list of goals
- bmps: list of Best Management Practices
- implementation: list of activities related to implementation
- monitoring: list of metrics related to monitoring
- outreach: list of outreach activities
- geographicAreas: list of geographic areas mentioned

Return the result in JSON.

Report Text:
{text_output}
"""

    if st.button("Extract Structured Data"):
        with st.spinner("Processing with LLM..."):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            content = response['choices'][0]['message']['content']

            try:
                data = json.loads(content)
                st.subheader("Structured Extracted Data")
                st.json(data)

                # Option to download as JSON
                st.download_button(
                    label="📥 Download JSON",
                    data=json.dumps(data, indent=2),
                    file_name=f"{uploaded_file.name.replace('.pdf','')}_extracted.json",
                    mime="application/json"
                )
            except json.JSONDecodeError:
                st.error("Failed to parse LLM output. Raw output:")
                st.code(content)
