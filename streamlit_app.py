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
                        You are a data extraction assistant specialized in agricultural and environmental reports.
                        
                        Your task is to extract structured data from the input report text and return it as a valid JSON object that strictly follows the defined schema.
                        
                        ---
                        
                        ### 📄 Input Text:
                        {pdf_text}
                        
                        ---
                        
                        ### 🧩 JSON Structure (Schema):
                        
                        Extract the following sections into JSON. Each field is required — include an empty array if no data is found.
                        
                        - **summary**:
                          - `totalGoals`: Total number of goal activities.
                          - `totalBMPs`: Total number of BMP activities.
                          - `completionRate`: A number between 0–100 representing estimated completion (see calculation rules below).
                        
                        - **goals**: Array of goal objects.
                          - Each must include:
                            - `title`: Short name of the goal.
                            - `description`: Explanation of the goal’s purpose or intent.
                        
                        - **bmps**: Array of BMP (Best Management Practice) objects.
                          - Each must include:
                            - `title`: Name of the BMP.
                            - `description`: Description of what it involves.
                            - `category`: Type/classification of the BMP.
                        
                        - **implementation**: On-the-ground activities that were performed or executed.
                          - Each must include:
                            - `activity`: Short name of the implementation step.
                            - `description`: Details of what was implemented.
                        
                        - **monitoring**: Activities that track or assess progress.
                          - Each must include:
                            - `activity`: Name of the monitoring action.
                            - `description`: What was monitored and how.
                        
                        - **outreach**: Community engagement or communication activities.
                          - Each must include:
                            - `activity`: Name of the outreach effort.
                            - `description`: Who was engaged and what was shared.
                        
                        - **geographicAreas**: Locations relevant to the report.
                          - Each must include:
                            - `name`: Name of the area.
                            - `description`: Details about its relevance.
                        
                        ---
                        
                        ### 📊 Completion Rate Rules
                        
                        Your goal is to extract or estimate the `completionRate` in the `summary` section based on the report.
                        
                        1. **If the report includes an explicit percentage**, such as:
                           - "75% complete"
                           - "80 percent of activities done"
                           → Use that value directly.
                        
                        2. **If the report provides numerical progress**, such as:
                           - "3 out of 4 activities completed"
                           → Calculate: `(3 / 4) * 100 = 75`
                        
                        3. **If only vague indicators are given**, interpret as follows:
                           - "fully completed", "entirely finished" → `100`
                           - "mostly complete", "nearly done" → `80–90`
                           - "partially complete", "in progress" → `40–60`
                           - "ongoing", "just started" → `10–30`
                           - "not started", "pending" → `0`
                        
                        4. If no completion info is available:
                           - Estimate completionRate as:
                             ```
                             totalCompletedActivities = number of activities with indications of completion
                             totalActivities = total number of goals, BMPs, implementation, monitoring, and outreach items
                             completionRate = (totalCompletedActivities / totalActivities) * 100
                             ```
                        
                        ⚠️ Return a single numeric value between `0` and `100` as `completionRate`. Do not return ranges or text.
                        
                        ---
                        
                        ### ✅ Output Instructions
                        
                        - Output **only** a valid JSON object.
                        - All required fields must be included.
                        - If no entries exist in a category, use an empty array.
                        - Follow the schema strictly.
                        
                        Begin extraction now.
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
