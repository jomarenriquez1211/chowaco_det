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
