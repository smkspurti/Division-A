import json
import re

def generate_ideas(client, name, skills, domain, tools, duration, github_context: str = ""):
    """
    Prompt chain:
      Step 1 (caller): fetch_github_trending() → github_context  [dataset_fetcher.py]
      Step 2 (here):   inject context into prompt → LLaMA generates ideas
    This constitutes prompt chaining: real-world data → context prompt → LLM generation.
    """
    context_block = f"\n{github_context}\n" if github_context else ""

    prompt = f"""You are an expert hackathon mentor. Generate exactly 5 ranked project ideas for a student.

Student Name: {name}
Skills: {skills}
Domain: {domain}
Available Tools: {tools}
Project Duration: {duration}
{context_block}
Use the trending repository context above (if provided) to suggest realistic, modern project ideas
that align with what the industry is actually building right now.

Return ONLY valid JSON in this exact format, no extra text:
{{
  "ideas": [
    {{
      "rank": 1,
      "title": "Project Title",
      "description": "2-3 sentence description of the project",
      "feasibility_score": 8.5,
      "innovation_score": 7.0,
      "impact_score": 9.0,
      "overall_score": 8.2,
      "tech_stack": ["Python", "Streamlit", "Groq"],
      "dataset": "Dataset name and source",
      "dataset_url": "https://example.com",
      "complexity": "Medium",
      "category": "AI/ML"
    }}
  ]
}}

Make scores realistic and varied. Overall score = average of the three scores.
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )
    text = response.choices[0].message.content.strip()
    text = re.sub(r"```json|```", "", text).strip()
    return json.loads(text)
