import streamlit as st
import pandas as pd
import backend  # assumes backend.py is in same folder

st.set_page_config(page_title="PDF to ExtractedReport JSON", layout="wide")
st.title("📄 PDF to ExtractedReport JSON using Gemini")
st.markdown("Upload one or more PDF files, and the app will extract structured data according to the `ExtractedReport` interface and upload to Firestore.")

uploaded_files = st.file_uploader(
    "Drag and drop PDF files here", type="pdf", accept_multiple_files=True
)

# Paste your full JSON schema here:
json_schema = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "object",
            "properties": {
                "totalGoals": {"type": "number"},
                "totalBMPs": {"type": "number"},
                "completionRate": {"type": "number"}
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

# Prompt template (same as before, just insert {pdf_text})
prompt_template = """
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

**monitoring**: Activities that track or assess progress by measuring specific indicators.
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

def display_section_df(name, data, columns):
    st.markdown(f"### {name}")
    if data:
        df = pd.DataFrame(data)
        if columns:
            available_cols = [col for col in columns if col in df.columns]
            df = df[available_cols]
        st.dataframe(df)
    else:
        st.write("No data available.")

if uploaded_files:
    if st.button("Extract Structured Data from All Files and Upload to Firestore"):
        for uploaded_file in uploaded_files:
            st.markdown(f"### Processing `{uploaded_file.name}`")
            st.markdown(f"**Source File:** `{uploaded_file.name}`")

            try:
                pdf_text = backend.extract_text_from_pdf(uploaded_file)
                if not pdf_text.strip():
                    st.warning("No text could be extracted from the uploaded PDF.")
                    continue

                structured_data = backend.generate_structured_data(pdf_text, json_schema, prompt_template)
                summary = structured_data.get("summary", {})

                # Show summary as metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Goals", summary.get("totalGoals", 0))
                col2.metric("Total BMPs", summary.get("totalBMPs", 0))
                col3.metric("Completion Rate", f"{summary.get('completionRate', 0)}%")

                # Display each section as DataFrame
                display_section_df("Goals", structured_data.get("goals", []), ["id", "title", "description"])
                display_section_df("BMPs", structured_data.get("bmps", []), ["id", "title", "description", "category"])
                display_section_df("Implementation Activities", structured_data.get("implementation", []), ["id", "activity", "description"])
                display_section_df("Monitoring Activities", structured_data.get("monitoring", []), ["id", "metricName", "value", "units", "description"])
                display_section_df("Outreach Activities", structured_data.get("outreach", []), ["id", "activity", "description"])
                display_section_df("Geographic Areas", structured_data.get("geographicAreas", []), ["id", "name", "description"])

                # Upload fresh data to Firestore with overwrite
                backend.upload_data_normalized(uploaded_file.name, summary, structured_data)

                st.success(f"✅ Data from `{uploaded_file.name}` uploaded successfully to Firestore.")

            except json.JSONDecodeError:
                st.error("❌ The response could not be parsed as JSON. Gemini may have returned an invalid format.")
            except Exception as e:
                st.error(f"⚠️ An error occurred: {e}")
