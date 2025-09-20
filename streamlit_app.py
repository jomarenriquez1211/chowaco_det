import streamlit as st
import pdfplumber
import json
import google.generativeai as genai

# ------------------------
# Gemini API setup
# ------------------------
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("API key not found. Please add `GOOGLE_API_KEY` to your Streamlit secrets.")
    st.stop()

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

# JSON schema matching the ExtractedReport interface
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
            "items": {"type": "object", "properties": {"name": {"type": "string"}}},
        },
        "bmps": {
            "type": "array",
            "items": {"type": "object", "properties": {"name": {"type": "string"}}},
        },
        "implementation": {
            "type": "array",
            "items": {"type": "object", "properties": {"activity": {"type": "string"}}},
        },
        "monitoring": {
            "type": "array",
            "items": {"type": "object", "properties": {"metric": {"type": "string"}}},
        },
        "outreach": {
            "type": "array",
            "items": {"type": "object", "properties": {"activity": {"type": "string"}}},
        },
        "geographicAreas": {
            "type": "array",
            "items": {"type": "object", "properties": {"name": {"type": "string"}}},
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

        prompt = f"""
        You are an intelligent data extraction assistant. Extract the following structured report from the text below.

        Text:
        {pdf_text}

        Return only valid JSON matching the ExtractedReport interface:
        ExtractedReport {{
            summary: {{ totalGoals: number; totalBMPs: number; completionRate: number; }};
            goals: Goal[];
            bmps: BMP[];
            implementation: ImplementationActivity[];
            monitoring: MonitoringMetric[];
            outreach: OutreachActivity[];
            geographicAreas: GeographicArea[];
        }}

        """

        if st.button("Extract Structured Data"):
            with st.spinner("Processing with Gemini..."):
                try:
                    response = model.generate_content(
                        prompt,
                        generation_config={
                            "response_mime_type": "application/json",
                            "response_schema": json_schema,
                        },
                    )
                    structured_data = json.loads(response.text)

                    st.subheader("ExtractedReport JSON")
                    st.json(structured_data)

                    st.download_button(
                        "📥 Download JSON",
                        data=json.dumps(structured_data, indent=2),
                        file_name=f"{uploaded_file.name.replace('.pdf','')}_ExtractedReport.json",
                        mime="application/json",
                    )
                except json.JSONDecodeError:
                    st.error("The response could not be parsed as JSON. Check the PDF content.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
