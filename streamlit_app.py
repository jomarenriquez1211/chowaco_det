import streamlit as st
import pdfplumber
from huggingface_hub import InferenceClient
import json

# ------------------------
# Hugging Face LLM setup (public model)
# ------------------------
HF_TOKEN = "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"  # Replace with your token

# Use a public instruction-tuned model
MODEL_NAME = "google/flan-t5-small"

# Use a supported provider: "hf-inference" or "auto"
client = InferenceClient(provider="hf-inference", api_key=HF_TOKEN)

# ------------------------
# Streamlit UI
# ------------------------
st.title("📄 PDF to Structured Data using Hugging Face LLM")

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

    # 3️⃣ Send to LLM when button is clicked
    if st.button("Extract Structured Data"):
        with st.spinner("Processing with Hugging Face LLM..."):
            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}]
                )

                llm_output = completion.choices[0].message
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
