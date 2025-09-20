import streamlit as st
import pdfplumber
import pandas as pd
import os
from PIL import Image

st.title("📑 PDF Extractor (Save Text, Tables, Images)")

uploaded_files = st.file_uploader(
    "Upload one or more PDF files",
    type="pdf",
    accept_multiple_files=True
)

# Output folder
output_dir = "extracted_files"
os.makedirs(output_dir, exist_ok=True)

if uploaded_files:
    for file in uploaded_files:
        st.write(f"Processing: {file.name}")
        with pdfplumber.open(file) as pdf:
            full_text = ""

            for i, page in enumerate(pdf.pages, start=1):
                # ---- Extract text ----
                text = page.extract_text() or ""
                full_text += f"--- Page {i} ---\n{text}\n\n"

                # Save text per page
                with open(os.path.join(output_dir, f"{file.name}_page{i}.txt"), "w", encoding="utf-8") as f:
                    f.write(text)

                # ---- Extract tables ----
                tables = page.extract_tables()
                for tbl_idx, table in enumerate(tables, start=1):
                    df = pd.DataFrame(table[1:], columns=table[0])
                    csv_path = os.path.join(output_dir, f"{file.name}_page{i}_table{tbl_idx}.csv")
                    df.to_csv(csv_path, index=False, encoding="utf-8")

                # ---- Extract images ----
                images = page.images
                if images:
                    zoom = 2  # scale factor for proper resolution
                    page_img_obj = page.to_image(resolution=72*zoom)
                    page_img = page_img_obj.original

                    for img_idx, img in enumerate(images, start=1):
                        # scale PDF coordinates to image pixels
                        x0 = int(img["x0"] * zoom)
                        top = int(img["top"] * zoom)
                        x1 = int(img["x1"] * zoom)
                        bottom = int(img["bottom"] * zoom)
                        cropped_img = page_img.crop((x0, top, x1, bottom))

                        img_path = os.path.join(output_dir, f"{file.name}_page{i}_img{img_idx}.png")
                        cropped_img.save(img_path)

            # Save full text of the PDF
            with open(os.path.join(output_dir, f"{file.name}_full_text.txt"), "w", encoding="utf-8") as f:
                f.write(full_text)

    st.success(f"Extraction complete! Files saved in `{output_dir}`")
