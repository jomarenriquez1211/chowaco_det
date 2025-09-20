import streamlit as st
from openai import OpenAI

# Temporary direct API key (only for testing locally!)
client = OpenAI(api_key="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")

prompt = st.text_input("Enter your prompt:")
if prompt:
    completion = client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": prompt}]
    )
    st.write(completion.choices[0].message.content)
