from crewai import Task
from agents.code_agent import code_agent


def get_code_task(requirement_spec: dict):

    return Task(
        description=f"""
You are a senior software architect and engineer.

You are responsible for building a COMPLETE, production-grade application from the given requirement.

REQUIREMENT: {requirement_spec}

STEP 1: UNDERSTAND
- Deeply analyze the requirement
- Identify the nature of the system (API, UI, data pipeline, CLI tool, distributed system, etc.)
- Identify scale and complexity

STEP 2: DECIDE ARCHITECTURE
You must intelligently decide:
- programming language(s)
- framework(s)
- system design
- data storage approach
- deployment approach

DO NOT assume any fixed language or framework.
Choose the most suitable technologies based on the requirement.

STEP 3: DESIGN COMPLETE SYSTEM

You MUST include:
- application entry point
- configuration management
- environment setup
- dependency management
- core logic layers
- data layer (if needed)
- communication layer (API/UI/etc)
- logging and error handling
- modular structure
- deployment setup (containerization if relevant)
- testing setup

STEP 4: GENERATE FULL PROJECT

- Generate a REALISTIC and COMPLETE project
- Include ALL necessary files across the system
- Maintain consistency across files
- Ensure code is executable and logically connected

STRICT RULES:

- DO NOT default to any specific language
- DO NOT assume backend-only
- DO NOT generate minimal examples
- DO NOT skip important layers
- DO NOT explain anything outside JSON

If requirement is ambiguous:
- Choose the most industry-standard approach
- Be consistent in your decision

OUTPUT FORMAT (STRICT JSON ONLY):

{{
  "project_name": "",
  "architecture_summary": "",
  "chosen_technologies": {{
    "languages": [],
    "frameworks": [],
    "tools": []
  }},
  "files": {{
    "file_path_with_structure": "complete code content"
  }}
}}

VERY IMPORTANT:

- "files" must contain a COMPLETE project (many files)
- File structure must match chosen technologies
- Code must be real, not placeholders
- Entire system must be cohesive

DO NOT OUTPUT ANY TEXT OUTSIDE JSON
        """,
        agent=code_agent,
        expected_output="Full multi-language production project JSON"
    )