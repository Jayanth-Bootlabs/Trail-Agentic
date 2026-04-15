from crewai import Task
from agents.requirement_agent import requirement_agent

def get_requirement_task(validated_data: dict):

    return Task(
        description=f"""
You will receive validated requirement data.

Your job:
1. Clean and normalize it
2. Convert into engineering specification
3. Prepare for code generation

INPUT:
{validated_data}

OUTPUT FORMAT (STRICT JSON):

{{
  "project": "",
  "scope": "",
  "modules": [],
  "features": [],
  "tech_stack_assumptions": [],
  "constraints": []
}}
        """,
        agent=requirement_agent,
        expected_output="Strict JSON engineering specification"
    )