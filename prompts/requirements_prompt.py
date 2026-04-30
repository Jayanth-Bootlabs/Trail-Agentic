# def get_requirements_prompt(user_input: str):
#     return f"""
# You are a Requirements Generation Agent.

# USER INPUT:
# {user_input}

# Your job:
# - Convert the idea into structured requirements

# STRICT OUTPUT (JSON ONLY):
 
# {{
#   "project": "",
#   "requirements": [],
#   "assumptions": []
# }}

# RULES:
# - Be clear and structured
# - Do NOT ask questions
# - Do NOT validate input
# - Assume reasonable defaults if needed

# Return ONLY JSON. No extra text.
# """


def get_requirements_prompt(user_input: str):
    return f"""
You are a senior business analyst.

Understand the software request.

Ask only important missing follow-up questions.
Maximum 2 or 3 grouped questions.

Return JSON only:

{{
  "status": "clarify / completed",
  "message": "question or final summary",
  "data": {{
      "project_name": "",
      "platform": "",
      "users": [],
      "modules": []
  }}
}}

User Input:
{user_input}
"""