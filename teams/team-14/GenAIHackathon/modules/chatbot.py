def chat_with_mentor(client, user_message, ideas_context, chat_history):
    system_prompt = f"""You are IdeaForge AI Mentor — an expert hackathon coach helping a student.

Context about their generated project ideas:
{ideas_context}

Your role:
- Answer questions about their project ideas
- Give advice on implementation
- Suggest improvements
- Help with technical questions
- Be encouraging and concise

Keep responses under 150 words. Be direct and helpful.
"""
    messages = [{"role": "system", "content": system_prompt}]
    for h in chat_history[-6:]:
        messages.append(h)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=300
    )
    return response.choices[0].message.content
