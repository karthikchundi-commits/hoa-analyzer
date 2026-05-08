import pdfplumber
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def get_client():
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def extract_text(pdf_file) -> str:
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages[:40]:  # cap at 40 pages
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text[:12000]  # cap tokens

def analyze_hoa(text: str, full: bool = False) -> dict:
    preview_prompt = """
You are an expert HOA document analyst. Analyze the following HOA document excerpt.
Return a JSON object with these keys:
- summary: 2-sentence plain English overview
- top_issues: list of 3 most important things a buyer must know (short, plain English)
- rental_restrictions: string — can owner rent the unit? Any restrictions?
- pet_policy: string — pet rules summary
- special_assessments: string — any pending or recent special assessments?
- litigation: string — any active or recent litigation mentioned?
- red_flags: list of up to 3 serious red flags (or empty list if none)
- verdict: one of "Low Risk", "Medium Risk", "High Risk" with one sentence reason

Be direct and specific. Flag anything that could cost the buyer money or restrict their use.
    """

    full_prompt = preview_prompt + """
Also include:
- monthly_fees: HOA fee amount if mentioned
- reserve_fund: reserve fund status (healthy/underfunded/not mentioned)
- insurance: what HOA insurance covers vs owner's responsibility
- prohibited_uses: list of notable prohibited uses (short-term rental, commercial use, etc.)
- maintenance_responsibility: what HOA maintains vs owner
- key_rules: 5 most important rules a new owner must know
    """

    prompt = full_prompt if full else preview_prompt

    response = get_client().chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"HOA DOCUMENT:\n\n{text}"}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )

    import json
    return json.loads(response.choices[0].message.content)
