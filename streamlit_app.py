import streamlit as st
import pdfplumber
import json
import google.generativeai as genai

# ------------------------
# Gemini API setup
# ------------------------

# IMPORTANT: Get your API key from https://aistudio.google.com/app/apikey
# and set it as an environment variable or in Streamlit secrets.
# For this example, we'll use Streamlit secrets.
# Create a .streamlit/secrets.toml file and add:
# GOOGLE_API_KEY="AIzaSyBg8kL0hF3fU78WqjTkgiap800F8kf_Meg"

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("API key not found. Please add `GOOGLE_API_KEY` to your Streamlit secrets.")
    st.stop()

# Choose your model. Use "gemini-1.5-pro" or "gemini-1.0-pro"
model = genai.GenerativeModel("gemini-1.5-flash")

# ------------------------
# Streamlit UI
# ------------------------
st.title("📄 PDF to Structured Data using Gemini (Google Generative AI SDK)")

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

    # 2️⃣ Prepare prompt
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

    Return only valid JSON that matches this interface. Do not include any additional text or formatting.
    """

    # 3️⃣ Call Gemini API
    if st.button("Extract Structured Data"):
        with st.spinner("Processing with Gemini..."):
            try:
                response = model.generate_content(prompt)
                
                # Access the text from the response object
                llm_output = response.text
                
                # Clean up any potential markdown or extra characters
                llm_output = llm_output.strip().replace("```json", "").replace("```", "")
                
                # Parse JSON
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
                st.error("Failed to parse LLM output as JSON. Here is the raw output:")
                st.code(llm_output)
            except Exception as e:
                st.error(f"An error occurred: {e}")
