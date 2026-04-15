from crewai import Task
from agents.validation_agent import validation_agent

def get_validation_task(user_input: str):

    return Task(
        description=f"""
You are a Requirement Gathering Assistant.

USER INPUT:
{user_input}

RULES:

You are in FAST MODE.

- Do NOT over-ask questions.
- Do NOT do deep clarification loops.
- Prefer assumptions over follow-up questions.

STEP 1:
If input is extremely vague (e.g., "make app"):
→ ask ONE short clarification question
→ stop

STEP 2:
Otherwise (default case):
→ assume missing details
→ generate FINAL JSON immediately

FINAL JSON FORMAT:
{{
  "type": "final",
  "project": "",
  "requirements": [],
  "assumptions": [],
  "clarifications": []
}}

IMPORTANT:
- Only ask ONE question maximum
- Otherwise always return JSON
        """,
        agent=validation_agent,
        expected_output="Either one short question OR final structured JSON"
    )