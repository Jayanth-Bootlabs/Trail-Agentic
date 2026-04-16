from crewai import Task
from agents.validation_agent import validation_agent

def get_validation_task(user_input: str):

    return Task(
        description=f"""
You are a Requirement Gathering Assistant.

USER INPUT:
{user_input}

You must ALWAYS return valid JSON:

{{
  "status": "question" or "final",
  "message": "",
  "project": "",
  "requirements": [],
  "assumptions": []
}}

CRITICAL BEHAVIOR RULE:

You are NOT allowed to keep asking questions repeatedly.

DECISION RULE:

1. Ask a question ONLY if:
   - user input is extremely vague (example: "build app", "make system")

2. Otherwise ALWAYS assume missing details and go FINAL.

3. If user already provided ANY of these:
   - project type (app/system/web)
   - domain (money tracker, CRM, etc.)
   - platform (web/mobile)
   - user context (personal/business)

  THEN you MUST go FINAL immediately

4. Maximum only 1 clarification step in entire conversation.

5. NEVER ask follow-up questions after user gives 2+ meaningful details.

OUTPUT RULE:
- If question → ONLY 1 question in message
- If final → complete structured JSON
        """,
        agent=validation_agent,
        expected_output="Strict JSON with progressive completion logic"
    )