import streamlit as st
import pdfplumber
import json
import re
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import jsonschema
from jsonschema import validate

# ---------- Gemini Setup ----------
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("❌ API key not found in Streamlit secrets. Please add GOOGLE_API_KEY.")
    st.stop()

model = genai.GenerativeModel("gemini-1.5-flash-latest")

# ---------- Schema Loader ----------
def get_json_schema():
    with open("schema.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- PDF Extraction ----------
def extract_text_from_pdf(pdf_file):
    text_output = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_output += page_text + "\n"
    return text_output

# ---------- LLM Extraction ----------
def llm_extract(text: str):
    prompt = f"""
    You are a domain expert in agriculture, watershed management, and government reporting. 
    Extract structured, insightful data from the following report and return ONLY one valid JSON object.

    The JSON must strictly follow this structure:

    {{
      "summary": {{
        "totalGoals": number,
        "totalBMPs": number,
        "completionRate": number
      }},
      "goals": [
        {{ "name": string, "status": string, "target": string, "progress": number }}
      ],
      "bmps": [
        {{ "type": string, "quantity": number, "cost": number }}
      ],
      "implementation": [
        {{ "name": string, "startDate": "YYYY-MM-DD", "endDate": "YYYY-MM-DD", "status": string }}
      ],
      "monitoring": [
        {{ "metricName": string, "baseline": string, "target": string }}
      ],
      "outreach": [
        {{ "type": string, "count": number }}
      ],
      "geographicAreas": [
        {{ "name": string, "acres": number, "croplandPct": number, "wetlandPct": number }}
      ]
    }}

    ⚠️ RULES FOR DATA:
    - If a value is missing, use null (never empty string).
    - Dates must be ISO (YYYY-MM-DD). If vague like "Month 1–36", set to null.
    - Numeric fields (quantities, costs, progress, completionRate, counts, percentages, acres) must be plain numbers only.
    - Progress must be a percentage (0–100). If qualitative, estimate based on report (e.g., "partially complete" ≈ 50).
    - For environmental metrics (baseline, target), preserve units (e.g., "5.0 mg/L").
    - For costs, remove currency symbols and round to nearest whole number.
    - For goals, status must be one of: "Not Started", "In Progress", "Completed".
    - If a section has no data, return [].
    - Always output ALL top-level keys, even if empty.
    - Return ONLY valid JSON. Do not add commentary or markdown.

    ✅ Examples of good output:
    - "status": "In Progress"
    - "completionRate": 72
    - "progress": 45
    - "startDate": "2021-01-01"
    - "baseline": "7.5 pH"
    - "croplandPct": 77

    Report Text:
    {text}
    """
    response = model.generate_content(prompt)
    return response.text


# ---------- Sanitizer ----------
def sanitize_llm_output(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"```(?:json)?", "", text)  # remove code fences
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end+1]
    return text

# ---------- Schema Validator ----------
def validate_json(data, schema):
    try:
        validate(instance=data, schema=schema)
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        return False, str(e)

# ---------- Streamlit App ----------
st.set_page_config(page_title="Watershed Plan Dashboard", layout="wide")
st.title("📑 Watershed Report → Dashboard")

uploaded_file = st.file_uploader("Upload a Watershed Report (PDF)", type=["pdf"])

if uploaded_file:
    with st.spinner("📖 Extracting text from PDF..."):
        text = extract_text_from_pdf(uploaded_file)
    st.success("✅ PDF text extracted")

    if st.button("Run Extraction and Build Dashboard"):
        with st.spinner("🤖 Extracting structured data using Gemini..."):
            raw_output = llm_extract(text)
            sanitized = sanitize_llm_output(raw_output)

        try:
            report = json.loads(sanitized)
        except Exception as e:
            st.error(f"⚠️ JSON parsing failed: {e}")
            st.text_area("Raw LLM output", raw_output, height=250)
            st.text_area("Sanitized attempt", sanitized, height=250)
            st.stop()

        schema = get_json_schema()
        is_valid, error_msg = validate_json(report, schema)

        if not is_valid:
            st.error("⚠️ JSON does not match schema")
            st.text(error_msg)
            st.json(report)
            st.stop()

        # ----------- Dashboard Rendering -----------
        st.success("✅ Data extraction complete! Rendering dashboard...")

        # --- Summary KPIs
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Goals", report["summary"]["totalGoals"])
        col2.metric("Total BMPs", report["summary"]["totalBMPs"])
        col3.metric("Completion Rate", f"{report['summary']['completionRate']}%")

        st.markdown("---")

        # --- Goals Section
        st.subheader("🎯 Goals")
        if report["goals"]:
            goals_df = pd.DataFrame(report["goals"])
            st.dataframe(goals_df)

            fig_goals = px.bar(goals_df, x="name", y="progress", color="status", title="Goal Progress")
            st.plotly_chart(fig_goals, use_container_width=True)
        else:
            st.info("No goals found in this report.")

        # --- BMPs Section
        st.subheader("🌱 Best Management Practices (BMPs)")
        bmps_df = pd.DataFrame(report["bmps"])
        col1, col2 = st.columns(2)
        with col1:
            fig_bmp_qty = px.bar(bmps_df, x="type", y="quantity", title="BMP Quantities")
            st.plotly_chart(fig_bmp_qty, use_container_width=True)
        with col2:
            fig_bmp_pie = px.pie(bmps_df, names="type", values="quantity", title="BMP Distribution")
            st.plotly_chart(fig_bmp_pie, use_container_width=True)
        st.dataframe(bmps_df)

        # --- Implementation
        st.subheader("🛠 Implementation Activities")
        impl_df = pd.DataFrame(report["implementation"])
        st.dataframe(impl_df)

        # --- Monitoring
        st.subheader("📊 Monitoring Metrics")
        monitor_df = pd.DataFrame(report["monitoring"])
        st.dataframe(monitor_df)

        # --- Outreach
        st.subheader("📢 Outreach Activities")
        outreach_df = pd.DataFrame(report["outreach"])
        fig_outreach = px.bar(outreach_df, x="type", y="count", title="Outreach Activities")
        st.plotly_chart(fig_outreach, use_container_width=True)

        # --- Geographic Areas
        st.subheader("🗺️ Geographic Areas")
        geo_df = pd.DataFrame(report["geographicAreas"])
        st.dataframe(geo_df)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Acres", geo_df["acres"].iloc[0])
        with col2:
            st.metric("Cropland %", f"{geo_df['croplandPct'].iloc[0]}%")
