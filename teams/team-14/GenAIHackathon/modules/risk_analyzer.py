import json
import re

def analyze_risks(client, top_idea_title, skills, tools, duration):
    prompt = f"""You are a risk analyst. Analyze project risks for a student hackathon project.

Project: {top_idea_title}
Skills: {skills}
Tools: {tools}
Duration: {duration}

Return ONLY valid JSON, no extra text:
{{
  "overall_risk": "Medium",
  "risk_score": 45,
  "risks": [
    {{
      "category": "Technical",
      "risk": "Risk description",
      "probability": "High",
      "impact": "Medium",
      "mitigation": "How to handle it"
    }}
  ],
  "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
}}

Include 4-5 risks across different categories: Technical, Time, Data, Team, Scope.
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    text = response.choices[0].message.content.strip()
    text = re.sub(r"```json|```", "", text).strip()
    return json.loads(text)
