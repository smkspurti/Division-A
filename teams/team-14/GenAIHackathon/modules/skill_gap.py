import json
import re

def analyze_skill_gap(client, skills, top_idea_title, top_idea_tech_stack):
    prompt = f"""You are a career mentor. Analyze skill gaps for a student.

Student's current skills: {skills}
Project they want to build: {top_idea_title}
Required tech stack: {', '.join(top_idea_tech_stack)}

Return ONLY valid JSON, no extra text:
{{
  "has_skills": ["skill1", "skill2"],
  "missing_skills": [
    {{
      "skill": "Skill Name",
      "importance": "High",
      "learn_in": "3 days",
      "resource": "Resource name",
      "resource_url": "https://example.com"
    }}
  ],
  "readiness_score": 75,
  "summary": "One sentence summary of readiness"
}}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    text = response.choices[0].message.content.strip()
    text = re.sub(r"```json|```", "", text).strip()
    return json.loads(text)
