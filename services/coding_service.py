# import traceback
# import json
# from fastapi import HTTPException
# from models.requirements_model import RequirementSession
# from models.code_model import GeneratedCode
# from prompts.code_prompt import get_code_prompt
# from utils.gemini_llm import llm
# from utils.logger import log_event

# SERVICE_NAME = "code_generation_service"


# async def generate_code_service(payload):
#     try:
#         requirements_id = payload.requirements_id

#         log_event(
#             level="INFO",
#             service=SERVICE_NAME,
#             function="generate_code_service",
#             message="Code generation started",
#             metadata={"requirements_id": requirements_id},
#         )

#         requirement = await RequirementSession.get_or_none(
#             id=requirements_id,
#             is_completed=True
#         )

#         if not requirement:
#             raise HTTPException(
#                 status_code=404,
#                 detail="Requirement not found or not completed yet"
#             )

#         prompt = get_code_prompt(requirement.combined_input)
#         response = await llm.generate(prompt)

#         response = response.strip()
#         if response.startswith("```json"):
#             response = response[7:]
#         if response.endswith("```"):
#             response = response[:-3]

#         code_data = json.loads(response)

#         code_obj = await GeneratedCode.create(
#             requirement_id=requirements_id,
#             code_json=code_data,
#             is_completed=True
#         )

#         log_event(
#             level="INFO",
#             service=SERVICE_NAME,
#             function="generate_code_service",
#             message="Code stored successfully",
#             metadata={"code_id": code_obj.id},
#         )

#         return {
#             "code_id": code_obj.id,
#             "requirements_id": requirements_id,
#             "source_code": code_data.get("source_code", {}),
#         }

#     except HTTPException:
#         raise

#     except Exception:
#         log_event(
#             level="ERROR",
#             service=SERVICE_NAME,
#             function="generate_code_service",
#             message="Code generation failed",
#             stack_trace=traceback.format_exc(),
#         )
#         raise HTTPException(status_code=500, detail="Internal server error")


# async def get_generated_code_service(payload):
#     try:
#         code_id = payload.code_id

#         log_event(
#             level="INFO",
#             service=SERVICE_NAME,
#             function="get_generated_code_service",
#             message="Fetching generated code",
#             metadata={"code_id": code_id},
#         )

#         code_record = await GeneratedCode.get_or_none(id=code_id)

#         if not code_record:
#             raise HTTPException(status_code=404, detail="Generated code not found")

#         code_data = code_record.code_json or {}

#         return {
#             "code_id": code_record.id,
#             "requirements_id": code_record.requirement_id,
#             "project_title": code_data.get("project_title", ""),
#             "tech_stack": code_data.get("tech_stack", []),
#             "file_structure": code_data.get("file_structure", []),
#             "source_code": code_data.get("source_code", {}),
#             "created_at": str(code_record.created_at) if code_record.created_at else None,
#         }

#     except HTTPException:
#         raise

#     except Exception:
#         log_event(
#             level="ERROR",
#             service=SERVICE_NAME,
#             function="get_generated_code_service",
#             message="Fetching code failed",
#             stack_trace=traceback.format_exc(),
#         )
#         raise HTTPException(status_code=500, detail="Internal server error")