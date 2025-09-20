import streamlit as st
import pdfplumber
import pandas as pd
from PIL import Image
import io

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
        if file.name not in selected_files:
            continue

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
                if tables:
                    st.markdown("**Tables found:**")
                    for tbl_idx, table in enumerate(tables, start=1):
                        df = pd.DataFrame(table[1:], columns=table[0])
                        st.dataframe(df)
                        # Optional: download table as CSV
                        csv = df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label=f"Download Table {tbl_idx} (Page {i}) as CSV",
                            data=csv,
                            file_name=f"{file.name}_page{i}_table{tbl_idx}.csv",
                            mime="text/csv"
                        )

                # ---- Extract images ----
                images = page.images
                if images:
                    st.markdown("**Images found:**")
                    page_img = page.to_image()
                    for img_idx, img in enumerate(images, start=1):
                        try:
                            bbox = (img["x0"], img["top"], img["x1"], img["bottom"])
                            cropped_img = page_img.within_bbox(bbox).original
                            st.image(cropped_img, caption=f"Page {i} - Image {img_idx}")
                        except Exception as e:
                            st.warning(f"Could not extract image {img_idx} on page {i}: {e}")

        # Optional: show full text combined
        with st.expander("📑 Full Extracted Text (All Pages)"):
            st.text_area("Full Text", full_text, height=400)

        # Optional: download full text
        st.download_button(
            label="Download Full Text",
            data=full_text,
            file_name=f"{file.name}_full_text.txt",
            mime="text/plain"
        )
