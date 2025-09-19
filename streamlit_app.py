from huggingface_hub import InferenceClient
import streamlit as st

hf_key = st.secrets["HF_API_KEY"]
client = InferenceClient(model="google/flan-t5-base", token=hf_key)

prompt = "Translate English to German: How are you?"

response = client.post(
    json={"inputs": prompt, "parameters": {"max_new_tokens": 300}}
)

st.write(response[0]["generated_text"])
