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

interface ExtractedReport {
  summary: {
    totalGoals: number;
    totalBMPs: number;
    completionRate: number;
  };
  goals: Goal[];
  bmps: BMP[];
  implementation: ImplementationActivity[];
  monitoring: MonitoringMetric[];
  outreach: OutreachActivity[];
  geographicAreas: GeographicArea[];
}

Instructions:

1. Identify and count all distinct goals mentioned in the report and populate the `goals` array. Each goal should have a title and description.
2. Identify all Best Management Practices (BMPs) described, including associated details such as category, description, or implementation status, and populate the `bmps` array.
3. Extract implementation activities and assign them to the `implementation` array, capturing details such as responsible parties, timeline, and related goals/BMPs.
4. Extract monitoring metrics, such as measurements, indicators, or targets, and populate the `monitoring` array.
5. Extract outreach activities such as workshops, training, or community engagement efforts and populate the `outreach` array.
6. Identify geographic areas, such as watersheds, counties, or regions, and populate the `geographicAreas` array.
7. Generate a `summary` object with:
   - `totalGoals`: the number of distinct goals
   - `totalBMPs`: the total number of BMPs
   - `completionRate`: a percentage estimate based on reported progress
8. Ignore irrelevant content and focus only on actionable, report-specific data.
9. Output your result as a valid JSON object that strictly follows the `ExtractedReport` interface.

Example output:

{
  "summary": {
    "totalGoals": 3,
    "totalBMPs": 12,
    "completionRate": 75
  },
  "goals": [
    { "title": "Goal 1", "description": "Reduce soil erosion in watershed X" },
    { "title": "Goal 2", "description": "Improve water quality in river Y" }
  ],
  "bmps": [
    { "title": "Cover Crops", "description": "Plant cover crops in fallow fields", "category": "Soil" }
  ],
  ...
}


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
