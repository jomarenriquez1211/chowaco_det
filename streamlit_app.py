import streamlit as st
from google.oauth2.service_account import Credentials
import streamlit as st
import pdfplumber
import json
import google.generativeai as genai
import pandas as pd

# ------------------------
# Gemini API setup
# ------------------------
try:
    genai.configure(api_key=st.secrets["gspread"])
except KeyError:
    st.error("API key not found. Please add `GOOGLE_API_KEY` to your Streamlit secrets.")
    st.stop()

