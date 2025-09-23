import os
import io
import json
import uuid
import firebase_admin
import google.generativeai as genai
from firebase_admin import credentials, firestore
from datetime import datetime
import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import streamlit as st  # For st.secrets usage

# -------- Firestore Initialization --------
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Configure Gemini API
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY in environment variables.")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# Load JSON schema from file
def get_json_schema():
    with open("schema.json", "r", encoding="utf-8") as f:
        return json.load(f)

# Load prompt template from file
def get_prompt_template():
    with open("prompt.txt", "r", encoding="utf-8") as f:
        return f.read()

# Upload structured data to Firestore
def upload_data_normalized(file_name, summary, structured_data):
    collection_name = "extracted_reports"
    base_doc_ref = db.collection(collection_name).document(file_name)

    # Set base document with summary
    base_doc_ref.set({
        "sourceFileName": file_name,
        "createdAt": datetime.utcnow(),
        "summary": summary
    })

    section_keys = ["goals", "bmps", "implementation", "monitoring", "outreach", "geographicAreas"]

    # Delete old subcollections if any
    for section in section_keys:
        docs = base_doc_ref.collection(section).stream()
        for doc in docs:
            doc.reference.delete()

    # Upload new data
    for section in section_keys:
        items = structured_data.get(section, [])
        for item in items:
            doc_id = item.get("id") or str(uuid.uuid4())
            item["id"] = doc_id
            item["createdAt"] = datetime.utcnow()
            base_doc_ref.collection(section).document(doc_id).set(item)

# Generate structured data from PDF text
def generate_structured_data(pdf_text, schema, prompt_template):
    prompt = prompt_template.replace("{pdf_text}", pdf_text)
    response = model.generate_content(
        prompt,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": schema,
        },
    )
    return json.loads(response.text)

# Extract text from PDF (try text extraction, fallback to OCR using PyMuPDF + pytesseract)
def extract_text_from_pdf(uploaded_file):
    text_output = ""
    try:
        # Try pdfplumber text extraction first
        uploaded_file.seek(0)
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_output += page_text + "\n"
        if text_output.strip():
            return text_output

        # OCR fallback - use PyMuPDF to render pages and pytesseract to OCR
        uploaded_file.seek(0)
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        zoom = 2  # 2x zoom for better OCR accuracy (~150-200 DPI)
        mat = fitz.Matrix(zoom, zoom)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # Convert pixmap to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Run OCR on image
            page_text = pytesseract.image_to_string(img)
            text_output += page_text + "\n\n"

        return text_output

    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF: {e}")
