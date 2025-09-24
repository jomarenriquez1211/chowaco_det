import streamlit as st
import pdfplumber
import google.generativeai as genai
import json
import jsonschema
import pandas as pd
import plotly.express as px

# ---------------------- Setup ----------------------
st.set_page_config(page_title="Watershed Plan Dashboard", layout="wide")

# Configure Gemini API
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("❌ Missing API key in Streamlit secrets under GOOGLE_API_KEY")
    st.stop()

model = genai.GenerativeModel("gemini-1.5-flash")

# ---------------------- Schema Loader ----------------------
def get_json_schema():
    with open("schema.json", "r", encoding="utf-8") as f:
        return json.load(f)

schema = get_json_schema()

# ---------------------- PDF Extractor ----------------------
def extract_text_from_pdf(uploaded_file):
    text_output = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_output += page_text + "\n"
    return text_output

# ---------------------- Prompt Template ----------------------
prompt_template = """
You are a data extraction assistant specialized in agricultural and environmental reports.

Your task is to extract structured data from the input report text and return it as a valid JSON object that strictly follows the defined schema.

---

### 📄 Input Text:
{text}

---

### 🧩 JSON Structure (Schema):

- summary: { totalGoals: number, totalBMPs: number, completionRate: number }
- goals: [{ title: string, description: string, status: string, target: string, progress: number }]
- bmps: [{ title: string, description: string, category: string, quantity: number, cost: number }]
- implementation: [{ activity: string, description: string, startDate: string, endDate: string, status: string }]
- monitoring: [{ metricName: string, value: string, units: string, description: string, baseline: string, target: string }]
- outreach: [{ activity: string, description: string, count: number }]
- geographicAreas: [{ name: string, description: string, acres: number, croplandPct: number, wetlandPct: number }]

⚠️ Rules:
- All fields must be present.
- If no data is found, return empty arrays.
- completionRate must be a number 0–100 (integer).
- Output only valid JSON, no commentary.

Begin extraction now.
"""

# ---------------------- LLM Extractor ----------------------
def llm_extract(text: str):
    prompt = prompt_template.format(text=text[:10000])  # limit input size
    response = model.generate_content(prompt)
    raw_output = response.text.strip()

    try:
        data = json.loads(raw_output)
        jsonschema.validate(instance=data, schema=schema)
        return data
    except json.JSONDecodeError:
        st.error("⚠️ LLM output is not valid JSON")
        st.text(raw_output)
        return None
    except jsonschema.ValidationError as e:
        st.error(f"⚠️ JSON does not match schema\n\n{e.message}")
        st.json(raw_output)
        return None

# ---------------------- Dashboard Renderer ----------------------
def render_dashboard(report):
    st.title("🌊 Watershed Plan Dashboard")

    # --- Summary
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Goals", report["summary"]["totalGoals"])
    col2.metric("Total BMPs", report["summary"]["totalBMPs"])
    col3.metric("Completion Rate", f"{report['summary']['completionRate']}%")

    st.markdown("---")

    # --- Goals
    st.subheader("🎯 Goals")
    if report["goals"]:
        goals_df = pd.DataFrame(report["goals"])
        st.dataframe(goals_df)
        fig_goals = px.bar(goals_df, x="title", y="progress", color="status", title="Goal Progress")
        st.plotly_chart(fig_goals, use_container_width=True)
    else:
        st.info("No goals found.")

    # --- BMPs
    st.subheader("🌱 Best Management Practices (BMPs)")
    if report["bmps"]:
        bmps_df = pd.DataFrame(report["bmps"])
        st.dataframe(bmps_df)
        fig_bmp_qty = px.bar(bmps_df, x="title", y="quantity", color="category", title="BMP Quantities")
        st.plotly_chart(fig_bmp_qty, use_container_width=True)
        fig_bmp_cost = px.bar(bmps_df, x="title", y="cost", color="category", title="BMP Costs")
        st.plotly_chart(fig_bmp_cost, use_container_width=True)

    # --- Implementation
    st.subheader("🛠 Implementation Activities")
    if report["implementation"]:
        impl_df = pd.DataFrame(report["implementation"])
        st.dataframe(impl_df)

    # --- Monitoring
    st.subheader("📊 Monitoring Metrics")
    if report["monitoring"]:
        monitor_df = pd.DataFrame(report["monitoring"])
        st.dataframe(monitor_df)
        fig_monitor = px.bar(monitor_df, x="metricName", y="value", color="units", title="Monitoring Values")
        st.plotly_chart(fig_monitor, use_container_width=True)

    # --- Outreach
    st.subheader("📢 Outreach Activities")
    if report["outreach"]:
        outreach_df = pd.DataFrame(report["outreach"])
        st.dataframe(outreach_df)
        fig_outreach = px.bar(outreach_df, x="activity", y="count", title="Outreach Activity Counts")
        st.plotly_chart(fig_outreach, use_container_width=True)

    # --- Geographic Areas
    st.subheader("🗺 Geographic Areas")
    if report["geographicAreas"]:
        geo_df = pd.DataFrame(report["geographicAreas"])
        st.dataframe(geo_df)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Acres", geo_df["acres"].sum())
        col2.metric("Cropland %", f"{geo_df['croplandPct'].mean():.1f}%")
        col3.metric("Wetland %", f"{geo_df['wetlandPct'].mean():.1f}%")

# ---------------------- Streamlit UI ----------------------
st.header("📤 Upload Watershed Report")
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:
    with st.spinner("Extracting text..."):
        pdf_text = extract_text_from_pdf(uploaded_file)

    with st.spinner("Running LLM extraction..."):
        report = llm_extract(pdf_text)

    if report:
        render_dashboard(report)
