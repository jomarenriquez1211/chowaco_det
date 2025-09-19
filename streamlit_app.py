import streamlit as st
import pdfplumber
import openai
import json

# ------------------------
# OpenAI LLM setup
# ------------------------
OPENAI_API_KEY = "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"  # Replace with your OpenAI API key
openai.api_key = OPENAI_API_KEY
MODEL_NAME = "gpt-4o-mini"  # or "gpt-5-mini"

# ------------------------
# Streamlit UI
# ------------------------
st.title("📄 PDF to Structured Data using OpenAI LLM")

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

    # 2️⃣ Prepare prompt for LLM
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

    # 3️⃣ Use OpenAI API to extract structured data
    if st.button("Extract Structured Data"):
        with st.spinner("Processing with OpenAI LLM..."):
            try:
                completion = openai.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are a precise data extraction assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,
                    max_tokens=1500
                )

                # Extract response content
                llm_output = completion.choices[0].message['content']

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
