import streamlit as st
import pdfplumber
import json
import google.generativeai as genai
import pandas as pd

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
    "Upload one or more PDF files, and the app will extract structured data according to the `ExtractedReport` interface."
)

uploaded_files = st.file_uploader(
    "Drag and drop PDF files here", type="pdf", accept_multiple_files=True
)

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
        "completionRate": {
          "type": "number",
          "minimum": 0,
          "maximum": 100
        }
      },
      "required": ["totalGoals", "totalBMPs", "completionRate"]
    },
    "goals": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "title": {"type": "string"},
          "description": {"type": "string"}
        },
        "required": ["title", "description"]
      }
    },
    "bmps": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "title": {"type": "string"},
          "description": {"type": "string"},
          "category": {"type": "string"}
        },
        "required": ["title", "description", "category"]
      }
    },
    "implementation": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "activity": {"type": "string"},
          "description": {"type": "string"}
        },
        "required": ["activity", "description"]
      }
    },
    "monitoring": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "metric": {"type": "string"},
          "description": {"type": "string"}
        },
        "required": ["metric", "description"]
      }
    },
    "outreach": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "activity": {"type": "string"},
          "description": {"type": "string"}
        },
        "required": ["activity", "description"]
      }
    },
    "geographicAreas": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "name": {"type": "string"},
          "description": {"type": "string"}
        },
        "required": ["name", "description"]
      }
    }
  },
  "required": ["summary", "goals", "bmps", "implementation", "monitoring", "outreach", "geographicAreas"]
}


if uploaded_files:
    if st.button("Extract Structured Data from All Files"):
        with st.spinner("Processing with Gemini..."):
            for uploaded_file in uploaded_files:
                st.markdown(f"### Processing `{uploaded_file.name}`")
                
                with st.expander("Show/Hide Processing Details"):
                    st.subheader("Step 1️⃣ - Extract PDF Text")
                    pdf_text = extract_text_from_pdf(uploaded_file)
        
                    if not pdf_text.strip():
                        st.warning("No text could be extracted from the uploaded PDF.")
                    else:
                        st.text_area("Raw Extracted Text", pdf_text, height=300)
        
                        st.subheader("Step 2️⃣ - Generate ExtractedReport JSON")
        
                        # The prompt is refined to align with the new, more detailed JSON schema.
                        prompt = f"""
                        You are an intelligent data extraction assistant specialized in agricultural and environmental reports. Analyze the following text extracted from a PDF and extract relevant information according to the ExtractedReport JSON schema described below.

                        Input Text:
                        {pdf_text}
                        
                        Schema Description:
                        You must produce a valid JSON object conforming to this structure:
                        
                        summary: Object with totalGoals, totalBMPs, and completionRate (percentage 0–100).
                        
                        goals: Array of objects with title and description.
                        
                        bmps: Array of objects with title, description, and category.
                        
                        implementation: Array of objects with activity and description.
                        
                        monitoring: Array of objects with metric and description.
                        
                        outreach: Array of objects with activity and description.
                        
                        geographicAreas: Array of objects with name and description.
                        
                        Instructions:
                        
                        Thoroughly understand the entire text, including hierarchical content like main points, sub-bullets, and examples.
                        
                        Extract all relevant information per the schema categories.
                        
                        Accurately capture variations in formatting and structure, ensuring no data is missed.
                        
                        Provide counts and estimates in the summary object based on the extracted data and any progress indicators.
                        
                        Output a single valid JSON object strictly following the described schema, ready for use in dashboards and exports.
        
                        """
        
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
        
                            # ------------------------
                            # Statistical Dashboard
                            # ------------------------
                            if structured_data and "summary" in structured_data:
                                st.subheader("Step 3️⃣ - Statistical Dashboard")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric(label="Total Goals", value=structured_data["summary"]["totalGoals"])
                                with col2:
                                    st.metric(label="Total BMPs", value=structured_data["summary"]["totalBMPs"])
                                with col3:
                                    st.metric(label="Completion Rate", value=f'{structured_data["summary"]["completionRate"]}%')
        
                                # Create a bar chart for categorical data
                                st.markdown("### Report Content Breakdown")
                                data_counts = {
                                    "Goals": structured_data["summary"]["totalGoals"],
                                    "BMPs": structured_data["summary"]["totalBMPs"],
                                    "Implementation Activities": len(structured_data.get("implementation", [])),
                                    "Monitoring Metrics": len(structured_data.get("monitoring", [])),
                                    "Outreach Activities": len(structured_data.get("outreach", [])),
                                    "Geographic Areas": len(structured_data.get("geographicAreas", [])),
                                }
                                
                                df = pd.DataFrame(data_counts.items(), columns=["Category", "Count"])
                                st.bar_chart(df.set_index("Category"))
        
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
