import streamlit as st
import pdfplumber
import json
import google.generativeai as genai
import pandas as pd

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
st.set_page_config(page_title="PDF to ExtractedReport Table Output", layout="wide")
st.title("📄 PDF Extraction with Paragraph Classification & Tables")

st.markdown(
    "Upload one or more PDF files. The app will classify paragraphs and extract structured data into tables."
)

uploaded_files = st.file_uploader(
    "Drag and drop PDF files here", type="pdf", accept_multiple_files=True
)

def extract_paragraphs_from_pdf(pdf_file):
    paragraphs = []
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Split on newlines, filter empty lines
                    lines = text.split("\n")
                    paragraphs.extend([line.strip() for line in lines if line.strip()])
    except Exception as e:
        st.error(f"Failed to read PDF: {e}")
    return paragraphs


def classify_paragraphs_with_llm(paragraphs):
    # Build prompt with JSON array of paragraphs
    prompt = f"""
You are a document classification assistant.

Given a list of paragraphs from a government/environmental report, classify each into one of these categories:

- main_content: Main points or summaries
- sub_bullet: Supporting sub-points or bullets
- example: Specific examples, case studies, or illustrative content
- administrative_text: Headers, footers, contact info, metadata, etc.

Respond as a JSON array with objects:
{{"type": "...", "text": "..."}}

Paragraphs:
{json.dumps(paragraphs, indent=2)}
    """

    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )

    try:
        classified = json.loads(response.text)
        return classified
    except Exception:
        st.error("Failed to classify paragraphs - invalid JSON from model.")
        return []

# JSON schema (same as your original)
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
        for uploaded_file in uploaded_files:
            st.markdown(f"### Processing `{uploaded_file.name}`")
            with st.spinner("Extracting paragraphs from PDF..."):
                paragraphs = extract_paragraphs_from_pdf(uploaded_file)

            if not paragraphs:
                st.warning("No text could be extracted from the PDF.")
                continue

            with st.expander("Classify Paragraphs"):
                classified_paragraphs = classify_paragraphs_with_llm(paragraphs)
                if classified_paragraphs:
                    df_classified = pd.DataFrame(classified_paragraphs)
                    st.dataframe(df_classified)
                else:
                    st.warning("Paragraph classification failed.")

            # Filter out administrative text paragraphs
            filtered_text = "\n".join(
                p["text"] for p in classified_paragraphs
                if p.get("type") in ("main_content", "sub_bullet", "example")
            )

            st.subheader("Filtered Text for Structured Extraction")
            st.text_area("Filtered text sent to Gemini for JSON extraction", filtered_text, height=300)

            # Prepare prompt for structured extraction
            prompt = f"""
You are a data extraction assistant specialized in agricultural and environmental reports.

Your task is to extract structured data from the input report text and return it as a valid JSON object that strictly follows the defined schema.

---

### 📄 Input Text:
{filtered_text}

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

            with st.spinner("Extracting structured data with Gemini..."):
                try:
                    response = model.generate_content(
                        prompt,
                        generation_config={
                            "response_mime_type": "application/json",
                            "response_schema": json_schema,
                        },
                    )
                    structured_data = json.loads(response.text)

                    # Display tables for each category except summary which uses metrics
                    st.subheader("Summary Metrics")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Goals", structured_data["summary"]["totalGoals"])
                    col2.metric("Total BMPs", structured_data["summary"]["totalBMPs"])
                    col3.metric("Completion Rate", f'{structured_data["summary"]["completionRate"]}%')

                    def df_from_list_of_dicts(lst, columns):
                        if lst:
                            df = pd.DataFrame(lst)
                            # Remove id column for clarity if present
                            if "id" in df.columns:
                                df = df.drop(columns=["id"])
                            return df[columns] if all(c in df.columns for c in columns) else df
                        return pd.DataFrame()

                    st.subheader("Goals")
                    df_goals = df_from_list_of_dicts(structured_data.get("goals", []), ["title", "description"])
                    st.dataframe(df_goals if not df_goals.empty else "No goals found")

                    st.subheader("BMPs")
                    df_bmps = df_from_list_of_dicts(structured_data.get("bmps", []), ["title", "description", "category"])
                    st.dataframe(df_bmps if not df_bmps.empty else "No BMPs found")

                    st.subheader("Implementation Activities")
                    df_impl = df_from_list_of_dicts(structured_data.get("implementation", []), ["activity", "description"])
                    st.dataframe(df_impl if not df_impl.empty else "No implementation activities found")

                    st.subheader("Monitoring Activities")
                    df_monitor = df_from_list_of_dicts(structured_data.get("monitoring", []), ["activity", "description"])
                    st.dataframe(df_monitor if not df_monitor.empty else "No monitoring activities found")

                    st.subheader("Outreach Activities")
                    df_outreach = df_from_list_of_dicts(structured_data.get("outreach", []), ["activity", "description"])
                    st.dataframe(df_outreach if not df_outreach.empty else "No outreach activities found")

                    st.subheader("Geographic Areas")
                    df_geo = df_from_list_of_dicts(structured_data.get("geographicAreas", []), ["name", "description"])
                    st.dataframe(df_geo if not df_geo.empty else "No geographic areas found")

                except json.JSONDecodeError:
                    st.error("The response could not be parsed as JSON. The Gemini model may have returned an invalid format.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
