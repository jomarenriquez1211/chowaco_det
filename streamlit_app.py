import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

# 🔐 Validate secrets
if "firebase" not in st.secrets:
    st.error("Missing 'firebase' section in secrets.toml.")
    st.stop()

# 🔌 Initialize Firebase only once
if "firebase_initialized" not in st.session_state:
    try:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
        st.session_state["firebase_initialized"] = True
    except Exception as e:
        st.error(f"Firebase initialization failed: {e}")
        st.stop()

# Firestore client
db = firestore.client()

# Sample data
data = {
    "name": ["Alice", "Bob", "Charlie"],
    "age": [25, 30, 35],
    "email": ["alice@example.com", "bob@example.com", "charlie@example.com"]
}
df = pd.DataFrame(data)

st.title("📤 Streamlit → Firebase Firestore")
st.dataframe(df)

collection_name = st.text_input("Enter Firestore collection name", "users")

if st.button("🚀 Upload to Firestore"):
    for _, row in df.iterrows():
        db.collection(collection_name).add(row.to_dict())
    st.success(f"✅ Uploaded {len(df)} records to '{collection_name}' collection.")
