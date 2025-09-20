
from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
  model="gpt-5",
  messages=[
      {
          "role": "user",
          "content": "Write a one-sentence bedtime story about a unicorn."
      }
  ]
)

print(completion.choices[0].message.content)

# import streamlit as st
# import pdfplumber
# import re
# import openai
# import json
# import os

# # ---------------------------
# # Configure OpenAI API key
# # ---------------------------
# openai.api_key = "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"

# st.title("📑 PDF Extractor (LLM + Regex Hybrid)")

# # ---------------------------
# # File uploader
# # ---------------------------
# uploaded_files = st.file_uploader(
#     "Upload one or more PDF files",
#     type="pdf",
#     accept_multiple_files=True
# )

# # ---------------------------
# # Output folder
# # ---------------------------
# output_dir = "extracted_reports"
# os.makedirs(output_dir, exist_ok=True)

# # ---------------------------
# # Helper: Regex extraction for summary
# # ---------------------------
# def regex_extract(text):
#     total_goals = len(re.findall(r"Goal\s+\d+", text, re.IGNORECASE))
#     total_bmps = len(re.findall(r"BMP\s+\d+", text, re.IGNORECASE))
#     completion_matches = re.findall(r"Completion Rate:\s*(\d+)%", text)
#     completion_rate = int(completion_matches[0]) if completion_matches else 0
#     return {
#         "totalGoals": total_goals,
#         "totalBMPs": total_bmps,
#         "completionRate": completion_rate
#     }

# # ---------------------------
# # Helper: Extract PDF text
# # ---------------------------
# def extract_pdf_text(file):
#     full_text = ""
#     with pdfplumber.open(file) as pdf:
#         for page in pdf.pages:
#             text = page.extract_text() or ""
#             full_text += text + "\n"
#     return full_text

# # ---------------------------
# # Helper: LLM extraction using ChatGPT (new SDK)
# # ---------------------------
# def llm_extract(text):
#     prompt = f"""
#     Extract a structured report from the following text and format it as JSON
#     that matches the TypeScript interface 'ExtractedReport':

#     {text}

#     JSON structure:
#     {{
#       "summary": {{ "totalGoals": number, "totalBMPs": number, "completionRate": number }},
#       "goals": [],
#       "bmps": [],
#       "implementation": [],
#       "monitoring": [],
#       "outreach": [],
#       "geographicAreas": []
#     }}

#     Ensure all fields are present even if empty arrays.
#     """

#     try:
#         response = openai.chat.completions.create(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant that extracts structured JSON from reports."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0
#         )

#         output_text = response.choices[0].message["content"]

#         return json.loads(output_text)
#     except json.JSONDecodeError:
#         # fallback to regex summary and empty arrays
#         return {
#             "summary": regex_extract(text),
#             "goals": [],
#             "bmps": [],
#             "implementation": [],
#             "monitoring": [],
#             "outreach": [],
#             "geographicAreas": []
#         }
#     except Exception as e:
#         st.error(f"LLM extraction failed: {e}")
#         return {
#             "summary": regex_extract(text),
#             "goals": [],
#             "bmps": [],
#             "implementation": [],
#             "monitoring": [],
#             "outreach": [],
#             "geographicAreas": []
#         }

# # ---------------------------
# # Main processing
# # ---------------------------
# if uploaded_files:
#     for file in uploaded_files:
#         st.write(f"Processing: {file.name}")
#         text = extract_pdf_text(file)
#         report = llm_extract(text)

#         # Save JSON
#         output_path = os.path.join(output_dir, f"{file.name}_report.json")
#         with open(output_path, "w", encoding="utf-8") as f:
#             json.dump(report, f, indent=2)

#     st.success(f"Extraction complete! JSON reports saved in `{output_dir}`")
