import openai
import pdfplumber

def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def llm_extract(text):
    prompt = f"""
    Extract the following fields from this watershed report:
    {{
      summary: {{ totalGoals: number; totalBMPs: number; completionRate: number }},
      goals: Goal[],
      bmps: BMP[],
      implementation: ImplementationActivity[],
      monitoring: MonitoringMetric[],
      outreach: OutreachActivity[],
      geographicAreas: GeographicArea[]
    }}
    
    Text: {text}
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a data extractor."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]
