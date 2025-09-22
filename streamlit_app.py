import streamlit as st
import json
import pandas as pd
from pathlib import Path
import firebase_database  # assumes backend.py is in same folder

st.set_page_config(page_title="PDF to ExtractedReport JSON", layout="wide")
st.title("📄 PDF to ExtractedReport JSON using Gemini")


st.markdown("Upload one or more PDF files, and the app will extract structured data according to the `ExtractedReport` interface and upload to Firestore.")

uploaded_files = st.file_uploader(
    "Drag and drop PDF files here", type="pdf", accept_multiple_files=True
)


def get_json_schema():
    schema_path = Path(__file__).parent / "schema.json"
    with open(schema_path, "r") as f:
        return json.load(f)

def get_prompt_template():
    prompt_path = Path(__file__).parent / "prompt.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

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
                pdf_text = firebase_database.extract_text_from_pdf(uploaded_file)
                if not pdf_text.strip():
                    st.warning("No text could be extracted from the uploaded PDF.")
                    continue

                structured_data = firebase_database.generate_structured_data(pdf_text, json_schema, prompt_template)
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
                firebase_database.upload_data_normalized(uploaded_file.name, summary, structured_data)

                st.success(f"✅ Data from `{uploaded_file.name}` uploaded successfully to Firestore.")

            except json.JSONDecodeError:
                st.error("❌ The response could not be parsed as JSON. Gemini may have returned an invalid format.")
            except Exception as e:
                st.error(f"⚠️ An error occurred: {e}")
