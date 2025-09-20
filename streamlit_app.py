import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

prompt = st.text_input("Enter your prompt:")
if st.button("Generate"):
    if prompt:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",  # <-- free-tier model
            messages=[{"role": "user", "content": prompt}]
        )
        st.write(completion.choices[0].message.content)
