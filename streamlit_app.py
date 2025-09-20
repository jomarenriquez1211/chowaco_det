import streamlit as st
import pdfplumber

st.set_page_config(page_title="PDF Full Extractor", layout="wide")
st.title("📑 PDF Full Extractor (Text + Tables + Images)")

uploaded_files = st.file_uploader(
    "Upload one or more PDF files",
    type="pdf",
    accept_multiple_files=True
)

if uploaded_files:
    file_names = [file.name for file in uploaded_files]

    selected_files = st.multiselect(
        "Choose PDFs to process:",
        options=file_names,
        default=file_names
    )

    for file in uploaded_files:
        if file.name in selected_files:
            st.subheader(f"📘 Extracted Content from {file.name}")
            
            with pdfplumber.open(file) as pdf:
                full_text = ""

                for i, page in enumerate(pdf.pages, start=1):
                    st.markdown(f"### 📄 Page {i}")

                    # ---- Extract text ----
                    text = page.extract_text(x_tolerance=1, y_tolerance=1) or ""
                    full_text += text + "\n\n"
                    if text.strip():
                        st.text_area(f"Text (Page {i})", text, height=200, key=f"{file.name}_text_{i}")

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
                                # Crop image from PDF
                                image = page.crop((img["x0"], img["top"], img["x1"], img["bottom"])).to_image()
                                st.image(image.original, caption=f"Page {i} - Image {img_idx}")
                            except Exception as e:
                                st.warning(f"Could not extract image {img_idx} on page {i}: {e}")

            # Optional: show full text combined
            with st.expander("📑 Full Extracted Text (All Pages)"):
                st.text_area("Full Text", full_text, height=400)
