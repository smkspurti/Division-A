import json
import re

def generate_roadmap(client, top_idea_title, top_idea_description, skills, duration):
    weeks = int(duration.split()[0])
    prompt = f"""You are a project manager. Create a detailed milestone roadmap.

Project: {top_idea_title}
Description: {top_idea_description}
Student Skills: {skills}
Duration: {duration}

Return ONLY valid JSON, no extra text:
{{
  "project": "{top_idea_title}",
  "total_weeks": {weeks},
  "weeks": [
    {{
      "week": 1,
      "title": "Week title",
      "goal": "Main goal of the week",
      "tasks": ["Task 1", "Task 2", "Task 3"],
      "deliverable": "What is ready at end of week",
      "milestone": "Key milestone name"
    }}
  ]
}}

Create exactly {weeks} week entries.
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500
    )
    text = response.choices[0].message.content.strip()
    text = re.sub(r"```json|```", "", text).strip()
    return json.loads(text)
