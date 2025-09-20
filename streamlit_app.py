import streamlit as st
from gpt4all import GPT4All

st.set_page_config(page_title="Local Chatbot")

# Load the model (first run will download it)
model = GPT4All("mistral-7b-openorca.gguf2.Q4_0.gguf")

st.title("💬 Local Chatbot (GPT4All)")

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.text_input("You:", "")

if st.button("Send") and user_input:
    st.session_state.history.append(("You", user_input))
    output = model.generate(user_input, max_tokens=200)
    st.session_state.history.append(("Bot", output))

for role, text in st.session_state.history:
    st.markdown(f"**{role}:** {text}")
