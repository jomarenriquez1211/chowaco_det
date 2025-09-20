import streamlit as st
import pdfplumber
import json
import google.generativeai as genai

# ------------------------
# Gemini API setup
# ------------------------
try:
    # This assumes the API key is set in Streamlit's secrets.toml file.
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("API key not found. Please add `GOOGLE_API_KEY` to your Streamlit secrets.")
    st.stop()

# Use the latest available Gemini model for text generation.
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# ------------------------
# Streamlit UI
# ------------------------
st.set_page_config(page_title="PDF to ExtractedReport JSON", layout="wide")
st.title("📄 PDF to ExtractedReport JSON using Gemini")
st.markdown(
    "Upload a PDF file, and the app will extract structured data according to the `ExtractedReport` interface."
)

uploaded_file = st.file_uploader("Drag and drop a PDF file here", type="pdf")

def extract_text_from_pdf(pdf_file):
    """Extract text from all pages of a PDF."""
    text_output = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_output += page_text + "\n"
    except Exception as e:
        st.error(f"Failed to read PDF: {e}")
    return text_output

# Corrected JSON schema to match the detailed interface described in the prompt.
# This schema is crucial for instructing the Gemini model on the exact output format.
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
            "required": ["totalGoals", "totalBMPs", "completionRate"],
        },
        "goals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["title", "description"]
            },
        },
        "bmps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "category": {"type": "string"}
                },
                "required": ["title", "description", "category"]
            },
        },
        "implementation": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "activity": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["activity", "description"]
            },
        },
        "monitoring": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "metric": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["metric", "description"]
            },
        },
        "outreach": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "activity": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["activity", "description"]
            },
        },
        "geographicAreas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["name", "description"]
            },
        },
    },
    "required": ["summary", "goals", "bmps", "implementation", "monitoring", "outreach", "geographicAreas"],
}

if uploaded_file:
    st.subheader("Step 1️⃣ - Extract PDF Text")
    pdf_text = extract_text_from_pdf(uploaded_file)

    if not pdf_text.strip():
        st.warning("No text could be extracted from the uploaded PDF.")
    else:
        st.text_area("Raw Extracted Text", pdf_text, height=300)

        st.subheader("Step 2️⃣ - Generate ExtractedReport JSON")

        # The prompt is refined to align with the new, more detailed JSON schema.
        prompt = f"""
        You are an intelligent data extraction assistant. Extract the following structured report from the text below, strictly following the provided JSON schema.

        Text:
        {pdf_text}

        Instructions:
        1.  Extract all goals mentioned in the report. For each goal, provide a `title` and a brief `description`.
        2.  Extract all Best Management Practices (BMPs). For each, provide a `title`, a brief `description`, and a `category` (e.g., "Soil", "Water Quality", "Vegetation").
        3.  Extract and list all implementation activities. For each, provide the `activity` name and a brief `description`.
        4.  Extract and list all monitoring metrics. For each, provide the `metric` name and a brief `description` of what is being measured.
        5.  Extract and list all outreach activities. For each, provide the `activity` name and a brief `description` of the effort.
        6.  Extract all geographic areas mentioned, such as watersheds, counties, or regions. For each, provide the `name` and a brief `description`.
        7.  Generate a `summary` object with:
            -   `totalGoals`: the number of distinct goals found.
            -   `totalBMPs`: the total number of BMPs found.
            -   `completionRate`: a percentage estimate based on reported progress.
        8.  Output your result as a valid JSON object that strictly follows the provided schema.

        """

        if st.button("Extract Structured Data"):
            with st.spinner("Processing with Gemini..."):
                try:
                    response = model.generate_content(
                        prompt,
                        generation_config={
                            "response_mime_type": "application/json",
                            # Use the updated and correct schema.
                            "response_schema": json_schema,
                        },
                    )
                    # The response.text property contains the generated JSON string.
                    structured_data = json.loads(response.text)

                    st.subheader("ExtractedReport JSON")
                    st.json(structured_data)

                    # Download button for the generated JSON file.
                    st.download_button(
                        "📥 Download JSON",
                        data=json.dumps(structured_data, indent=2),
                        file_name=f"{uploaded_file.name.replace('.pdf','')}_ExtractedReport.json",
                        mime="application/json",
                    )
                except json.JSONDecodeError:
                    st.error("The response could not be parsed as JSON. The Gemini model may have returned an invalid format.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
