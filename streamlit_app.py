import streamlit as st
import pdfplumber
from gpt4all import GPT4All

# --- Load GPT4All model ---
st.sidebar.title("LLM Settings")
model_path = st.sidebar.text_input("Enter GPT4All model path:", "ggml-gpt4all-l13b-snoozy.bin")

@st.cache_resource
def load_model(path):
    return GPT4All(path)

model = load_model(model_path)

# --- Streamlit Page ---
st.set_page_config(page_title="PDF Full Extractor + LLM", layout="wide")
st.title("📑 PDF Full Extractor (Text + Tables + Images) + GPT4All")

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

    user_prompt = st.text_input("Ask a question about the PDF(s):", placeholder="e.g., Summarize this document")

    for file in uploaded_files:
        if file.name in selected_files:
            st.subheader(f"📘 Extracted Content from {file.name}")
            full_text = ""

            with pdfplumber.open(file) as pdf:
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
                                image = page.crop((img["x0"], img["top"], img["x1"], img["bottom"])).to_image()
                                st.image(image.original, caption=f"Page {i} - Image {img_idx}")
                            except Exception as e:
                                st.warning(f"Could not extract image {img_idx} on page {i}: {e}")

            # Optional: show full text combined
            with st.expander("📑 Full Extracted Text (All Pages)"):
                st.text_area("Full Text", full_text, height=400)

            # ---- GPT4All processing ----
            if user_prompt.strip():
                st.subheader("🤖 GPT4All Response")
                full_prompt = f"PDF Content:\n{full_text}\n\nQuestion: {user_prompt}"
                try:
                    response = model.generate(full_prompt)
                    st.write(response)
                except Exception as e:
                    st.error(f"Error generating LLM response: {e}")
