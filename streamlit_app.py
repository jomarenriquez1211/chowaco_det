from huggingface_hub import InferenceClient
import streamlit as st

hf_key = st.secrets["HF_API_KEY"]
client = InferenceClient(token=hf_key)

prompt = "Translate English to German: How are you?"

response = client.text2text_generation(
    model="google/flan-t5-base",
    input=prompt,
    max_new_tokens=300
)

st.write(response)
