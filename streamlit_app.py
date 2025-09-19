import streamlit as st
from openai import OpenAI

# Get the key from Streamlit secrets
api_key = st.secrets["OPENAI_API_KEY"]

# Initialize client
client = OpenAI(api_key=api_key)

# Test call
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Say hello"}]
)

st.write(response.choices[0].message["content"])
