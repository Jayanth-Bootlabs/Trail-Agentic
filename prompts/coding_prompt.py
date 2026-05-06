def get_coding_prompt(requirements: dict):
    return f"""
You are a senior full-stack software engineer.

Generate production-ready code based on structured requirements.

Rules:
- Return JSON only
- Follow clean architecture
- Separate backend and frontend
- Include folder structure

Output format:

{{
  "status": "completed / partial",
  "message": "summary",
  "code": {{
    "backend": "FastAPI code",
    "frontend": "React code",
    "database": "DB models",
    "structure": "folder structure"
  }}
}}

Requirements JSON:
{requirements}
"""