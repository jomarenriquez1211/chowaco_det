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
st.set_page_config(page_title="PDF to ExtractedReport Tables", layout="wide")
st.title("📄 PDF to ExtractedReport (Table Format Only)")

uploaded_files = st.file_uploader(
    "Upload one or more PDF files", type="pdf", accept_multiple_files=True
)

def extract_text_from_pdf(pdf_file):
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
        with st.spinner("Processing with Gemini..."):
            for uploaded_file in uploaded_files:
                st.markdown(f"### 📄 `{uploaded_file.name}`")

                pdf_text = extract_text_from_pdf(uploaded_file)

                if not pdf_text.strip():
                    st.warning("No text could be extracted from this PDF.")
                    continue

                prompt = f"""
                You are a data extraction assistant for environmental reports.

                Extract the following structured data from the input text and return as valid JSON:

                - summary: totalGoals, totalBMPs, completionRate (0–100%)
                - goals: id, title, description
                - bmps: id, title, description, category
                - implementation: id, activity, description
                - monitoring: id, activity, description
                - outreach: id, activity, description
                - geographicAreas: id, name, description

                If no data is found for a category, return an empty array.

                Estimate completionRate based on qualitative or quantitative statements (not from raw counts). Default to 0 if unclear.

                --- INPUT TEXT ---
                {pdf_text}
                --- END INPUT TEXT ---

                Respond only with a valid JSON object that strictly follows the schema.
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

                    # ------------------------
                    # Summary Statistics
                    # ------------------------
                    if "summary" in structured_data:
                        st.subheader("📊 Summary Metrics")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Total Goals", structured_data["summary"]["totalGoals"])
                        col2.metric("Total BMPs", structured_data["summary"]["totalBMPs"])
                        col3.metric("Completion Rate", f"{structured_data['summary']['completionRate']}%")

                        # Bar chart breakdown
                        st.markdown("### 📊 Report Breakdown")
                        data_counts = {
                            "Goals": structured_data["summary"]["totalGoals"],
                            "BMPs": structured_data["summary"]["totalBMPs"],
                            "Implementation": len(structured_data.get("implementation", [])),
                            "Monitoring": len(structured_data.get("monitoring", [])),
                            "Outreach": len(structured_data.get("outreach", [])),
                            "Geographic Areas": len(structured_data.get("geographicAreas", [])),
                        }
                        df = pd.DataFrame(data_counts.items(), columns=["Category", "Count"])
                        st.bar_chart(df.set_index("Category"))

                    # ------------------------
                    # Tabulated Outputs
                    # ------------------------
                    st.subheader("📋 Extracted Tables")

                    if structured_data.get("goals"):
                        st.markdown("#### 🎯 Goals")
                        st.dataframe(pd.DataFrame(structured_data["goals"]))

                    if structured_data.get("bmps"):
                        st.markdown("#### 🛠️ BMPs")
                        st.dataframe(pd.DataFrame(structured_data["bmps"]))

                    if structured_data.get("implementation"):
                        st.markdown("#### 🏗️ Implementation Activities")
                        st.dataframe(pd.DataFrame(structured_data["implementation"]))

                    if structured_data.get("monitoring"):
                        st.markdown("#### 📈 Monitoring Activities")
                        st.dataframe(pd.DataFrame(structured_data["monitoring"]))

                    if structured_data.get("outreach"):
                        st.markdown("#### 📣 Outreach Activities")
                        st.dataframe(pd.DataFrame(structured_data["outreach"]))

                    if structured_data.get("geographicAreas"):
                        st.markdown("#### 🗺️ Geographic Areas")
                        st.dataframe(pd.DataFrame(structured_data["geographicAreas"]))

                    # ------------------------
                    # Download Button
                    # ------------------------
                    st.download_button(
                        "📥 Download JSON",
                        data=json.dumps(structured_data, indent=2),
                        file_name=f"{uploaded_file.name.replace('.pdf','')}_ExtractedReport.json",
                        mime="application/json",
                    )

                except json.JSONDecodeError:
                    st.error("❌ Failed to parse Gemini's response as JSON.")
                except Exception as e:
                    st.error(f"❌ An unexpected error occurred: {e}")
