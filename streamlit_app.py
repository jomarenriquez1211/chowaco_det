import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

# ----------------------------------------
# 🔐 Check for Firebase secrets
# ----------------------------------------
if "firebase" not in st.secrets:
    st.error("Missing 'firebase' section in secrets.toml.")
    st.stop()

# ----------------------------------------
# 🔌 Initialize Firebase (only once)
# ----------------------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

# ----------------------------------------
# 🗂️ Firestore Client
# ----------------------------------------
db = firestore.client()

# ----------------------------------------
# 🧪 Sample DataFrame
# ----------------------------------------
data = {
    "name": ["Alice", "Bob", "Charlie"],
    "age": [25, 30, 35],
    "email": ["alice@example.com", "bob@example.com", "charlie@example.com"]
}
df = pd.DataFrame(data)

st.title("📤 Streamlit → Firebase Firestore")
st.dataframe(df)

collection_name = st.text_input("Enter collection name", "users")

if st.button("🚀 Upload to Firestore"):
    try:
        for _, row in df.iterrows():
            db.collection(collection_name).add(row.to_dict())
        st.success(f"✅ Uploaded {len(df)} records to '{collection_name}' collection.")
    except Exception as e:
        st.error(f"Error uploading data: {e}")
