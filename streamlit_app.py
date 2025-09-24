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
    prompt_template = """
You are a data extraction assistant specialized in agricultural and environmental government reports.

Your task is to extract structured, insightful data from the input report text and return it as a valid JSON object that strictly follows the defined schema.

---
📄 Input Text:
{text}

---
🧩 JSON Structure (Schema):

Extract the following sections into JSON. Each field is required — include an empty array if no data is found.

- **goals**: Array of goal objects.
  - Each must include:
    - `title`: Short name of the goal.
    - `description`: Explanation of the goal’s purpose or intent.
    - `status`: One of: "Not Started", "In Progress", "Completed".
    - `target`: The quantitative or qualitative target of the goal (string, may include units).
    - `progress`: A number 0–100 representing % completion (estimate if qualitative).

- **bmps**: Array of BMP (Best Management Practices).
  - Each must include:
    - `title`: Short name of the BMP (must be unique).
    - `description`: Explanation of the BMP's content.
    - `category`: Type/classification of the BMP.
    - `quantity`: Numeric quantity (acres, units, etc.).
    - `cost`: Numeric cost in whole dollars (no $ or commas).

- **implementation**: Implementation activities that were performed or executed.
  - Each must include:
    - `activity`: Short title of the implementation step. ⚠️ Must always end with the word "Implementation".
    - `description`: Detailed explanation of what was implemented.
    - `startDate`: In ISO `YYYY-MM-DD` format, or null if not specified.
    - `endDate`: In ISO `YYYY-MM-DD` format, or null if not specified.
    - `status`: One of: "Not Started", "In Progress", "Completed".

- **monitoring**: Activities that track or assess progress by measuring specific indicators.
  - Each must include:
    - `metricName`: Name of the metric being measured (e.g., "Water pH", "Soil Moisture").
    - `value`: The measured value (string or numeric).
    - `units`: Units of the metric if applicable (e.g., "mg/L", "%", "count"); empty string if none.
    - `baseline`: Baseline condition (string).
    - `target`: Target condition (string).
    - `description`: Explanation of what the metric represents and how it was obtained.
  - Avoid duplicates with the same `metricName`.

- **outreach**: Community engagement or communication activities.
  - Each must include:
    - `activity`: Name of the outreach effort.
    - `description`: Who was engaged and what was shared.
    - `count`: Numeric count of times it occurred (default 0 if not given).

- **geographicAreas**: Locations relevant to the report.
  - Each must include:
    - `name`: Name of the geographic area (non-empty string, must be unique).
    - `description`: Details about the area's relevance or role in the report (non-empty string).
    - `acres`: Total size in acres (numeric).
    - `croplandPct`: Percentage of cropland (0–100).
    - `wetlandPct`: Percentage of wetland (0–100).

- **summary**:
  - `totalGoals`: Count of goals extracted.
  - `totalBMPs`: Count of BMPs extracted.
  - `completionRate`: A number between 0–100 representing estimated completion (see rules below).

---
⚠️ COMPLETION RATE RULES:
- Carefully analyze mentions of completed activities, BMPs, milestones, or progress statements.
- Estimate overall completion as a numeric % (0–100).
- Consider both explicit data (e.g., "70% complete") and qualitative cues (e.g., "most activities completed").
- Use reasoning, not a fixed formula. Round to the nearest integer.
- If no progress information, default to 0.

---
✅ OUTPUT RULES:
- If missing, use null (not empty string).
- Numeric fields (progress, completionRate, quantity, cost, acres, counts, percentages) must be plain numbers.
- Dates must be ISO (YYYY-MM-DD) or null.
- Always output all top-level keys, even if arrays are empty.
- Output ONLY a valid JSON object. No explanations or markdown.

Begin extraction now.
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
