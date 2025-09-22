import os
import io
import json
import uuid
import firebase_admin
import google.generativeai as genai
from firebase_admin import credentials, firestore
from datetime import datetime
from pathlib import Path
import streamlit as st
import pandas as pd
import pdfplumber
from PIL import Image
import pytesseract
from PyPDF2 import PdfReader

# -------- Firestore Initialization --------
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)
db = firestore.client()


# ---------- 🤖 Gemini API Setup ----------
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY in environment variables.")
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash-latest")

# ---------- Helper: Load JSON schema ----------
def get_json_schema():
    with open("schema.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- Helper: Load Prompt Template ----------
def get_prompt_template():
    with open("prompt.txt", "r", encoding="utf-8") as f:
        return f.read()

# ---------- 📤 Upload to Firestore ----------
def upload_data_normalized(file_name, summary, structured_data):
    collection_name = "extracted_reports"
    base_doc_ref = db.collection(collection_name).document(file_name)

    # Overwrite base document
    base_doc_ref.set({
        "sourceFileName": file_name,
        "createdAt": datetime.utcnow(),
        "summary": summary
    })

    section_keys = ["goals", "bmps", "implementation", "monitoring", "outreach", "geographicAreas"]

    # Delete old subcollections
    for section in section_keys:
        docs = base_doc_ref.collection(section).stream()
        for doc in docs:
            doc.reference.delete()

    # Upload new items
    for section in section_keys:
        items = structured_data.get(section, [])
        for item in items:
            doc_id = item.get("id") or str(uuid.uuid4())
            item["id"] = doc_id
            item["createdAt"] = datetime.utcnow()
            base_doc_ref.collection(section).document(doc_id).set(item)

# ---------- 🤖 Generate structured data ----------
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

# ---------- 📚 PDF Text Extraction (Text + OCR) ----------
def extract_text_from_pdf(uploaded_file):
    text_output = ""
    try:
        # Try extracting text with pdfplumber
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_output += page_text + "\n"
        if text_output.strip():
            return text_output

        # OCR fallback
        pdf_reader = PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            x_object = page.get("/Resources", {}).get("/XObject")
            if not x_object:
                continue
            for obj in x_object:
                if x_object[obj]["/Subtype"] == "/Image":
                    size = (x_object[obj]["/Width"], x_object[obj]["/Height"])
                    data = x_object[obj].get_data()
                    img = Image.open(io.BytesIO(data))
                    text_output += pytesseract.image_to_string(img)
        return text_output

    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF: {e}")
