import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase only once
if "firebase_initialized" not in st.session_state:
    # Load credentials from Streamlit secrets
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)
    st.session_state["firebase_initialized"] = True

# Initialize Firestore client
db = firestore.client()

st.title("📤 Upload DataFrame to Firebase Firestore")

# Example DataFrame
data = {
    "name": ["Alice", "Bob", "Charlie"],
    "age": [25, 30, 35],
    "email": ["alice@example.com", "bob@example.com", "charlie@example.com"]
}
df = pd.DataFrame(data)

st.subheader("🔍 Preview Your Data")
st.dataframe(df)

# Collection name input
collection_name = st.text_input("Enter Firestore collection name", "users")

# Upload button
if st.button("🚀 Upload to Firestore"):
    if not collection_name:
        st.warning("Please enter a collection name.")
    else:
        for i, row in df.iterrows():
            doc_ref = db.collection(collection_name).document()  # auto-generated ID
            doc_ref.set(row.to_dict())
        st.success(f"✅ Uploaded {len(df)} records to '{collection_name}' collection!")

