import streamlit as st
import pdfplumber

st.set_page_config(page_title="PDF Full Extractor", layout="wide")
st.title("📑 PDF Full Extractor (Text + Tables + Images)")

# Only allow a single PDF file to be uploaded
uploaded_file = st.file_uploader(
    "Drop a PDF file here or click to upload",
    type="pdf",
    accept_multiple_files=False
)

if uploaded_file:
    st.subheader(f"📘 Extracted Content from {uploaded_file.name}")
    full_text = ""

    with pdfplumber.open(uploaded_file) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            st.markdown(f"### 📄 Page {i}")

            # ---- Extract text ----
            text = page.extract_text(x_tolerance=1, y_tolerance=1) or ""
            full_text += text + "\n\n"
            if text.strip():
                st.text_area(f"Text (Page {i})", text, height=200, key=f"text_{i}")

            # ---- Extract tables ----
            tables = page.extract_tables()
            for table in tables:
                st.markdown("**Table found:**")
                for row in table:
                    st.write(" | ".join(cell or "" for cell in row))

            # ---- Extract images ----
            images = page.images
            if images:
                st.markdown("**Images found:**")
                for img_idx, img in enumerate(images, start=1):
                    try:
                        image = page.crop((img["x0"], img["top"], img["x1"], img["bottom"])).to_image()
                        st.image(image.original, caption=f"Page {i} - Image {img_idx}")
                    except Exception as e:
                        st.warning(f"Could not extract image {img_idx} on page {i}: {e}")

    # Optional: show full text combined
    with st.expander("📑 Full Extracted Text (All Pages)"):
        st.text_area("Full Text", full_text, height=400)
