import streamlit as st
import pdfplumber
import json
import base64
import io
import google.generativeai as genai
from PIL import Image

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
st.set_page_config(page_title="PDF to ExtractedReport JSON", layout="wide")
st.title("📄 PDF to ExtractedReport JSON (Text + Images)")

uploaded_file = st.file_uploader("Drag and drop a PDF file here", type="pdf")

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
                        # Crop image from page
                        x0, y0, x1, y1 = img["x0"], img["top"], img["x1"], img["bottom"]
                        cropped_image = page.to_image().crop((x0, y0, x1, y1)).original
                        buffered = io.BytesIO()
                        cropped_image.save(buffered, format="PNG")
                        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
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

# JSON schema including images
json_schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "object"},
        "goals": {"type": "array"},
        "bmps": {"type": "array"},
        "implementation": {"type": "array"},
        "monitoring": {"type": "array"},
        "outreach": {"type": "array"},
        "geographicAreas": {"type": "array"},
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
            }
        }
    }
}

if uploaded_file:
    st.subheader("Step 1️⃣ - Extract PDF Content")
    pdf_text, pdf_images = extract_pdf_content(uploaded_file)

    if not pdf_text.strip() and not pdf_images:
        st.warning("No text or images could be extracted from the uploaded PDF.")
    else:
        st.text_area("Raw Extracted Text", pdf_text, height=300)
        if pdf_images:
            st.write(f"Extracted {len(pdf_images)} images from PDF pages")

        st.subheader("Step 2️⃣ - Generate ExtractedReport JSON")

        prompt = f"""
        You are an intelligent data extraction assistant. Extract structured data from the text below.
        Include all goals, BMPs, implementation activities, monitoring metrics, outreach activities,
        and geographic areas. Include images extracted from the PDF in base64.

        Text:
        {pdf_text}

        Images: There are {len(pdf_images)} images extracted from the PDF.

        Output must strictly follow the provided JSON schema including an `images` array.
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
                    # Add extracted images to JSON
                    structured_data["images"] = pdf_images

                    st.subheader("ExtractedReport JSON")
                    st.json(structured_data)

                    st.download_button(
                        "📥 Download JSON",
                        data=json.dumps(structured_data, indent=2),
                        file_name=f"{uploaded_file.name.replace('.pdf','')}_ExtractedReport.json",
                        mime="application/json",
                    )
                except json.JSONDecodeError:
                    st.error("Gemini returned an invalid JSON format.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
