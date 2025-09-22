import streamlit as st

st.title("🔍 Secrets Debugger")

# Check what's available in st.secrets
st.write("Secrets available:", list(st.secrets.keys()))

# Try printing the Firebase config if it exists
if "firebase" in st.secrets:
    st.success("✅ Firebase config found in secrets.")
    st.json(st.secrets["firebase"])
else:
    st.error("❌ 'firebase' section not found in secrets!")
