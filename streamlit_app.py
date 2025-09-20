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
          "type": "number"
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
          "activity": {"type": "string"},
          "description": {"type": "string"}
        },
        "required": ["activity", "description"]
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
                        
                        goals: Array of goal activity objects, each with title and description.
                        
                        bmps: Array of Best Management Practices(BMP) activity objects, each with title, description, and category.
                        
                        implementation: Array of implementation activity objects, each with activity and description.
                        
                        monitoring: Array of monitoring activity objects, each with activity and description.
                        
                        outreach: Array of outreach activity objects, each with activity and description.
                        
                        geographicAreas: Array of geographic area objects, each with name and description.
                        
                        Instructions:
                        
                        Thoroughly understand the entire text, including hierarchical content like main points, sub-bullets, and examples.
                        
                        Extract all relevant information according to the schema categories above.
                        
                        Accurately capture variations in formatting and document structure, ensuring no data is missed.
                        
                        Provide counts and estimates in the summary object based on the extracted data and any reported progress indicators.
                        
                        Output a single valid JSON object strictly following the described schema, ready for use in dashboards and exports.

                        For the calculation of Completion Rate use the criteria below:
                        1. Identify any explicit progress or completion information in the text, such as percentages, ratios, or statements indicating how much of the project, goals, BMPs, or activities have been completed.
                        2. If explicit completion percentages are provided (e.g., "75% complete," "3 of 4 activities finished"), use those values directly.
                        3. If not explicitly stated, estimate the overall completion rate by comparing the number of completed items to the total planned items across goals, BMPs, implementation activities, monitoring activities, and outreach activities.
                        4. The completionRate should be a single numeric value between 0 and 100, representing the overall percentage of project completion.
        
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
