import streamlit as st
import pdfplumber
import json
import google.generativeai as genai

# ------------------------
# Gemini API setup
# ------------------------

# IMPORTANT: Get your API key from https://aistudio.google.com/app/apikey
# and set it as a Streamlit secret.
# In your Streamlit app, create a .streamlit/secrets.toml file and add:
# GOOGLE_API_KEY="AIzaSy...your-key..._Meg"

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("API key not found. Please add `GOOGLE_API_KEY` to your Streamlit secrets.")
    st.stop()

# Using the recommended gemini-1.5-flash model for its generous free tier limits.
# We're now using the explicit "latest" alias to ensure compatibility with structured output.
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# ------------------------
# Streamlit UI
# ------------------------
st.title("📄 PDF to Structured Data using Gemini")
st.markdown("Upload a PDF file to extract structured data based on a predefined interface.")

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
    st.text_area("Extracted Text", text_output, height=300, key="raw_text")

    # 2️⃣ Prepare the prompt and the structured schema
    prompt = f"""
    You are an intelligent data extraction assistant. Extract the following structured report from the text below.

    Text:
    {text_output}

    Return only valid JSON that matches the provided schema. Do not include any additional text or formatting.
    """

    # Define the JSON schema for the desired output
    # The API requires a non-empty 'properties' field for any object types.
    json_schema = {
        "type": "object",
        "properties": {
            "summary": {
                "type": "object",
                "properties": {
                    "totalGoals": {"type": "number"},
                    "totalBMPs": {"type": "number"},
                    "completionRate": {"type": "number"},
                },
            },
            "goals": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                    }
                },
            },
            "bmps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                    }
                },
            },
            "implementation": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "activity": {"type": "string"},
                    }
                },
            },
            "monitoring": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "metric": {"type": "string"},
                    }
                },
            },
            "outreach": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "activity": {"type": "string"},
                    }
                },
            },
            "geographicAreas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                    }
                },
            },
        },
    }

    # 3️⃣ Call Gemini API with structured output configuration
    if st.button("Extract Structured Data", key="extract_button"):
        with st.spinner("Processing with Gemini..."):
            try:
                # Use a generation_config to ensure the model returns a structured JSON object
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "response_mime_type": "application/json",
                        "response_schema": json_schema,
                    }
                )

                # The response.text will now contain the valid JSON string
                structured_data = json.loads(response.text)

                st.subheader("Structured Data")
                st.json(structured_data)

                st.download_button(
                    "📥 Download JSON",
                    data=json.dumps(structured_data, indent=2),
                    file_name=f"{uploaded_file.name.replace('.pdf','')}_structured.json",
                    mime="application/json"
                )

            except Exception as e:
                st.error(f"An error occurred: {e}")
