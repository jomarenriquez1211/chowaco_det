import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["openai"]["api_key"])

prompt = st.text_input("Enter your prompt:")
if st.button("Generate"):
    if prompt:
        completion = client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": prompt}]
        )
        st.write(completion.choices[0].message.content)
