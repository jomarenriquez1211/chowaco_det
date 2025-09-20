import streamlit as st
import pdfplumber
import json
import base64
import google.generativeai as genai

# ------------------------
# Gemini API setup
# ------------------------
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("API key not found. Please add `GOOGLE_API_KEY` to your Streamlit secrets.")
    st.stop()

# Use the latest Gemini model
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# ------------------------
# Streamlit UI
# ------------------------
st.set_page_config(page_title="PDF to ExtractedReport JSON", layout="wide")
st.title("📄 PDF to ExtractedReport JSON with Images")

st.markdown(
    "Upload a PDF file, and the app will extract structured data including text and images."
)

uploaded_file = st.file_uploader("Drag and drop a PDF file here", type="pdf")

# ------------------------
# PDF Extraction Function
# ------------------------
def extract_pdf_content(pdf_file):
    """Extract text and images from all pages of a PDF."""
    text_output = ""
    images_output = []

    try:
        with pdfplumber.open(pdf_file) as pdf:
            for i, page in enumerate(pdf.pages):
                # Extract text
                page_text = page.extract_text()
                if page_text:
                    text_output += page_text + "\n"

                # Extract images
                for img_index, img in enumerate(page.images):
                    try:
                        extracted_image = page.extract_image(img)
                        if extracted_image:
                            image_bytes = extracted_image["image"]
                            img_b64 = base64.b64encode(image_bytes).decode("utf-8")
                            images_output.append({
                                "page": i + 1,
                                "image_index": img_index + 1,
                                "data": img_b64
                            })
                    except Exception as e:
                        st.warning(f"Failed to extract image on page {i+1}, index {img_index}: {e}")
    except Exception as e:
        st.error(f"Failed to read PDF: {e}")

    return text_output, images_output

# ------------------------
# JSON Schema
# ------------------------
json_schema = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "object",
            "properties": {
                "totalGoals": {"type": "number"},
                "totalBMPs": {"type": "number"},
                "completionRate": {"type": "number"},
            },
            "required": ["totalGoals", "totalBMPs", "completionRate"],
        },
        "goals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["title", "description"]
            },
        },
        "bmps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "category": {"type": "string"}
                },
                "required": ["title", "description", "category"]
            },
        },
        "implementation": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "activity": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["activity", "description"]
            },
        },
        "monitoring": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "metric": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["metric", "description"]
            },
        },
        "outreach": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "activity": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["activity", "description"]
            },
        },
        "geographicAreas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["name", "description"]
            },
        },
        "images": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "page": {"type": "number"},
                    "image_index": {"type": "number"},
                    "data": {"type": "string"}
                },
                "required": ["page", "image_index", "data"]
            },
        }
    },
    "required": ["summary", "goals", "bmps", "implementation", "monitoring", "outreach", "geographicAreas", "images"],
}

# ------------------------
# Streamlit Processing
# ------------------------
if uploaded_file:
    st.subheader("Step 1️⃣ - Extract PDF Text and Images")
    pdf_text, pdf_images = extract_pdf_content(uploaded_file)

    if not pdf_text.strip():
        st.warning("No text could be extracted from the uploaded PDF.")
    else:
        st.text_area("Raw Extracted Text", pdf_text, height=300)

    if pdf_images:
        st.subheader("Extracted Images")
        for img in pdf_images:
            st.image(base64.b64decode(img["data"]), caption=f"Page {img['page']} - Image {img['image_index']}")

    st.subheader("Step 2️⃣ - Generate ExtractedReport JSON")
    prompt = f"""
    Extract structured data including all goals, BMPs, implementation, monitoring, outreach,
    geographic areas, and images from the following PDF text. Include all images in base64 format.

    Text:
    {pdf_text}

    Images: {len(pdf_images)} extracted
    """

    if st.button("Extract Structured Data"):
        with st.spinner("Processing with Gemini..."):
            try:
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "response_mime_type": "application/json",
                        "response_schema": json_schema,
                    },
                )
                structured_data = json.loads(response.text)
                structured_data["images"] = pdf_images  # Include the images in JSON

                st.subheader("ExtractedReport JSON")
                st.json(structured_data)

                st.download_button(
                    "📥 Download JSON",
                    data=json.dumps(structured_data, indent=2),
                    file_name=f"{uploaded_file.name.replace('.pdf','')}_ExtractedReport.json",
                    mime="application/json",
                )
            except json.JSONDecodeError:
                st.error("The response could not be parsed as JSON.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
