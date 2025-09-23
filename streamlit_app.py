import streamlit as st
import json
import pandas as pd
import pdfplumber
import fitz  # PyMuPDF
import easyocr
import io
import numpy as np
from PIL import Image
import firebase_database  # Your backend module

st.set_page_config(page_title="📄 PDF to ExtractedReport JSON", layout="wide")
st.title("📄 PDF to ExtractedReport JSON using Gemini")
st.markdown("Upload one or more PDF files. The app will extract structured data and upload it to Firestore.")

# Load schema & prompt from backend
json_schema = firebase_database.get_json_schema()
prompt_template = firebase_database.get_prompt_template()

uploaded_files = st.file_uploader(
    "Drag and drop PDF files here", type="pdf", accept_multiple_files=True
)

# Initialize EasyOCR reader once
reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if you have CUDA-enabled GPU

def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_images_from_pdf(file):
    images = []
    doc = fitz.open(stream=file.read(), filetype="pdf")
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img_bytes = pix.tobytes("png")
        images.append(img_bytes)
    return images

def ocr_image_with_easyocr(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    # EasyOCR accepts numpy array
    img_array = np.array(image)
    result = reader.readtext(img_array)
    text = " ".join([res[1] for res in result])
    return text

def display_section_df(name, data, columns):
    st.markdown(f"### {name}")
    if data:
        df = pd.DataFrame(data)
        if columns:
            available_cols = [col for col in columns if col in df.columns]
            df = df[available_cols]
        st.dataframe(df)
    else:
        st.info("No data available.")

if uploaded_files:
    if st.button("Extract & Upload to Firestore"):
        for uploaded_file in uploaded_files:
            st.markdown(f"---\n### Processing `{uploaded_file.name}`")
            try:
                # Reset file pointer before reading
                uploaded_file.seek(0)
                pdf_text = extract_text_from_pdf(uploaded_file)

                # If no embedded text found, use OCR on images
                if not pdf_text.strip():
                    st.info("No embedded text found, running OCR on images...")
                    uploaded_file.seek(0)  # Reset again before extracting images
                    images = extract_images_from_pdf(uploaded_file)
                    ocr_text = ""
                    for img_bytes in images:
                        ocr_text += ocr_image_with_easyocr(img_bytes) + "\n"
                    pdf_text = ocr_text

                if not pdf_text.strip():
                    st.warning("No text could be extracted even after OCR.")
                    continue

                structured_data = firebase_database.generate_structured_data(
                    pdf_text, json_schema, prompt_template
                )
                summary = structured_data.get("summary", {})

                # Display summary metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Goals", summary.get("totalGoals", 0))
                col2.metric("Total BMPs", summary.get("totalBMPs", 0))
                col3.metric("Completion Rate", f"{summary.get('completionRate', 0)}%")

                # Display extracted tables
                display_section_df("Goals", structured_data.get("goals", []), ["id", "title", "description"])
                display_section_df("BMPs", structured_data.get("bmps", []), ["id", "title", "description", "category"])
                display_section_df("Implementation Activities", structured_data.get("implementation", []), ["id", "activity", "description"])
                display_section_df("Monitoring Activities", structured_data.get("monitoring", []), ["id", "metricName", "value", "units", "description"])
                display_section_df("Outreach Activities", structured_data.get("outreach", []), ["id", "activity", "description"])
                display_section_df("Geographic Areas", structured_data.get("geographicAreas", []), ["id", "name", "description"])

                # Upload to Firestore
                firebase_database.upload_data_normalized(uploaded_file.name, summary, structured_data)
                st.success(f"✅ Uploaded `{uploaded_file.name}` to Firestore!")

            except json.JSONDecodeError:
                st.error("❌ Failed to parse JSON from Gemini.")
            except Exception as e:
                st.error(f"⚠️ Error: {e}")
