import streamlit as st
import pdfplumber
import json
import google.generativeai as genai
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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
# Streamlit UI setup
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

# Your existing detailed JSON schema here (same as your provided schema) ...
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
          "metricName": {"type": "string"},
          "value": {},
          "units": {"type": "string"},
          "description": {"type": "string"}
        },
        "required": ["metricName", "value", "description"]
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

def save_to_google_sheet(structured_data, filename_prefix):
    try:
        # Setup Google Sheets API
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
        client = gspread.authorize(creds)

        # Create new Google Sheet
        spreadsheet = client.create(f"{filename_prefix}_ExtractedReport")

        # Share the sheet with yourself (optional)
        # spreadsheet.share("your.email@example.com", perm_type="user", role="writer")

        # Write Summary to default sheet
        summary_data = structured_data.get("summary", {})
        summary_df = pd.DataFrame([summary_data])
        worksheet = spreadsheet.sheet1
        worksheet.update_title("Summary")
        worksheet.update([summary_df.columns.tolist()] + summary_df.values.tolist())

        # Write other sections to separate sheets
        sections = ["goals", "bmps", "implementation", "monitoring", "outreach", "geographicAreas"]

        for section in sections:
            items = structured_data.get(section, [])
            if not items:
                continue  # Skip empty

            df = pd.DataFrame(items)
            new_sheet = spreadsheet.add_worksheet(
                title=section.capitalize(),
                rows=str(len(df) + 1),
                cols=str(len(df.columns))
            )
            new_sheet.update([df.columns.tolist()] + df.values.tolist())

        st.success(f"✅ Google Sheet created: {filename_prefix}_ExtractedReport")
        st.markdown(f"[📄 Open in Google Sheets](https://docs.google.com/spreadsheets/d/{spreadsheet.id})")

    except Exception as e:
        st.error(f"❌ Failed to save to Google Sheet: {e}")

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
                        continue  # Skip to next file

                    st.text_area("Raw Extracted Text", pdf_text, height=300)

                    st.subheader("Step 2️⃣ - Generate ExtractedReport JSON")

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
                      - Each item must include:
                        - `activity`: Short name of the implementation step.
                        - `description`: Detailed explanation of what was implemented.

                    - **monitoring**: Activities that track or assess progress by measuring specific indicators.
                      - Each item must include:
                        - `metricName`: Name of the metric being measured (e.g., "Water pH", "Soil Moisture").
                        - `value`: The measured value or status of the metric (can be numeric or descriptive).
                        - `units`: Units of the metric if applicable (e.g., "mg/L", "%", "count").
                        - `description`: Explanation of what the metric represents and how it was obtained.

                    - **outreach**: Community engagement or communication activities.
                      - Each must include:
                        - `activity`: Name of the outreach effort.
                        - `description`: Who was engaged and what was shared.

                    - **geographicAreas**: Locations relevant to the report.
                      - Each must include:
                        - `name`: Name of the area.
                        - `description`: Details about its relevance.

                    ---

                   For the `completionRate`, carefully analyze the entire input text for mentions of completed goal activities, BMP implementations, milestones, or progress statements.

                    - Estimate the overall completion as a numeric percentage (0–100) reflecting the progress toward fulfilling all stated goals and BMPs.
                    - Consider both explicit quantitative data (e.g., "70% complete") and qualitative descriptions indicating progress (e.g., "most activities have been finished", "implementation ongoing").
                    - Use your best judgment to infer the level of completion even if exact figures are not provided.
                    - Return **only** a single numeric value between 0 and 100, rounded to the nearest integer. No text, ranges, or explanations.
                    - If no progress information is found, default to 0.

                    ⚠️ Do **not** calculate the completion rate by a fixed formula or ratio of counts but use your LLM reasoning to estimate overall progress based on the report content.

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
                                "response_schema": json_schema,
                            },
                        )
                        structured_data = json.loads(response.text)

                        st.subheader("ExtractedReport JSON")
                        st.json(structured_data)

                        # Step 3: Statistical Dashboard
                        if structured_data and "summary" in structured_data:
                            st.subheader("Step 3️⃣ - Statistical Dashboard")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric(label="Total Goals", value=structured_data["summary"]["totalGoals"])
                            with col2:
                                st.metric(label="Total BMPs", value=structured_data["summary"]["totalBMPs"])
                            with col3:
                                st.metric(label="Completion Rate", value=f'{structured_data["summary"]["completionRate"]}%')

                            # Bar chart for category counts
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

                        # Download JSON button
                        st.download_button(
                            "📥 Download JSON",
                            data=json.dumps(structured_data, indent=2),
                            file_name=f"{uploaded_file.name.replace('.pdf','')}_ExtractedReport.json",
                            mime="application/json",
                        )

                        # Save to Google Sheets
                        filename_prefix = uploaded_file.name.replace(".pdf", "")
                        save_to_google_sheet(structured_data, filename_prefix)

                    except json.JSONDecodeError:
                        st.error("The response could not be parsed as JSON. The Gemini model may have returned an invalid format.")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
