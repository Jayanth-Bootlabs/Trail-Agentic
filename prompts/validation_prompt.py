VALIDATION_RULES = {
    "min_required": 2,
    "dimensions": """
1. Platform (web, mobile, backend)
2. Domain (finance, CRM, chatbot, e-commerce)
3. Functionality (track expenses, manage users, reports)
4. Technology (python, AI, react)
""",
    "invalid_examples": """
- build app
- create system
- create web app
""",
    "valid_examples": """
- create web app for expense tracking
- build AI chatbot using python
- create CRM system for sales team
"""
}


def get_validation_prompt(user_input: str):
    return f"""
You are a Requirement Validation Agent.

Your job is ONLY to decide:
- Is the input clear enough to proceed?
- OR do we need ONE clarification?

USER INPUT:
{user_input}

STRICT OUTPUT (JSON ONLY):

{{
  "status": "question" or "valid",
  "message": ""
}}

CRITICAL RULES:
- Do NOT generate requirements
- Do NOT assume missing details
- Do NOT expand the idea

DECISION LOGIC:

Input is VALID only if it contains at least {VALIDATION_RULES["min_required"]} of the following:

{VALIDATION_RULES["dimensions"]}

Examples:

INVALID:
{VALIDATION_RULES["invalid_examples"]}

VALID:
{VALIDATION_RULES["valid_examples"]}

OUTPUT RULES:

- If INVALID → ask ONLY 1 clear question
- If VALID → message must be empty
- Return ONLY JSON
"""