import pdfplumber
import json
import uuid
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai
import streamlit as st  # Needed for secrets

# -------- Firestore Initialization --------
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)
db = firestore.client()

# -------- Gemini API Setup --------
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    raise RuntimeError("API key not found in Streamlit secrets under 'GOOGLE_API_KEY'")

model = genai.GenerativeModel("gemini-1.5-flash-latest")

# ---------- 📄 Load schema & prompt from file ----------
def get_json_schema():
    schema_path = Path(__file__).parent / "schema.json"
    with open(schema_path, "r") as f:
        return json.load(f)

def get_prompt_template():
    prompt_path = Path(__file__).parent / "prompt.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()
        
def extract_text_from_pdf(pdf_file):
    text_output = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_output += page_text + "\n"
    except Exception as e:
        raise RuntimeError(f"Failed to read PDF: {e}")
    return text_output


def generate_structured_data(pdf_text, json_schema, prompt_template):
    prompt = prompt_template.format(pdf_text=pdf_text)
    response = model.generate_content(
        prompt,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": json_schema,
        },
    )
    return json.loads(response.text)


def delete_existing_docs(collection_name, file_name):
    coll_ref = db.collection(collection_name)
    docs = coll_ref.where("sourceFileName", "==", file_name).stream()
    batch = db.batch()
    count = 0
    for doc in docs:
        batch.delete(doc.reference)
        count += 1
        if count % 500 == 0:
            batch.commit()
            batch = db.batch()
    batch.commit()


def upload_data_normalized(file_name, summary, structured_data):
    # Delete previous summary doc for this file
    db.collection("summaries").document(file_name).delete()

    # Delete previous docs in all sections for this file
    sections = ["goals", "bmps", "implementation", "monitoring", "outreach", "geographicAreas"]
    for section in sections:
        delete_existing_docs(section, file_name)

    # Upload summary doc
    db.collection("summaries").document(file_name).set({
        "sourceFileName": file_name,
        "createdAt": datetime.utcnow(),
        **summary
    })

    # Upload section documents
    for section in sections:
        coll_ref = db.collection(section)
        batch = db.batch()
        for item in structured_data.get(section, []):
            doc_id = item.get("id") or str(uuid.uuid4())
            doc_ref = coll_ref.document(doc_id)
            batch.set(doc_ref, {
                **item,
                "sourceFileName": file_name,
                "createdAt": datetime.utcnow()
            })
        batch.commit()
