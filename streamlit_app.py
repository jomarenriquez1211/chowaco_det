from openai import OpenAI
import streamlit as st

api_key = st.secrets["OPENAI_API_KEY"]  # must match the TOML name
client = OpenAI(api_key=api_key)
st.write("Loaded key prefix:", api_key[:10] + "...")
