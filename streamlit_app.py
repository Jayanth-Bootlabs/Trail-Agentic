#poetry run streamlit run streamlit_app.py

import json
from typing import Optional, Dict, Any

import requests
import streamlit as st

BASE_URL = "http://127.0.0.1:8000"

 
# SESSION
 

if "session" not in st.session_state:
    st.session_state.session = requests.Session()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

 
# API CALL
 

def api_call(
    method: str,
    endpoint: str,
    payload: Optional[Dict] = None,
    params: Optional[Dict] = None,
) -> Dict[str, Any]:
    url = f"{BASE_URL}{endpoint}"

    user_email = st.session_state.get("user_email")

    if user_email:
        st.session_state.session.headers["Authorization"] = user_email

    try:
        if method.upper() == "GET":
            resp = st.session_state.session.get(
                url,
                params=params or payload
            )

        elif method.upper() == "DELETE":
            resp = st.session_state.session.delete(url)

        elif method.upper() == "PATCH":
            resp = st.session_state.session.patch(
                url,
                json=payload
            )

        else:
            resp = st.session_state.session.post(
                url,
                json=payload
            )

        resp.raise_for_status()
        return resp.json()

    except Exception as e:
        st.error(f"API call failed: {e}")

        if "resp" in locals():
            st.error(resp.text)

        return {}


def extract_data(response: dict) -> dict:
    if isinstance(response, dict) and "data" in response:
        return response["data"]

    return response


 
# RENDER HELPERS
 

def detect_language(filename: str):
    extension_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".md": "markdown",
        ".sql": "sql",
        ".yaml": "yaml",
        ".yml": "yaml",
    }

    for ext, lang in extension_map.items():
        if filename.endswith(ext):
            return lang

    return "text"


def render_source_code(source_code: dict):
    st.subheader("📁 Generated Files")

    for file_path, code in source_code.items():
        language = detect_language(file_path)

        with st.expander(f"📄 {file_path}", expanded=False):
            st.code(
                code,
                language=language
            )


def render_unit_test(test_code: str):
    st.subheader("🧪 Generated Unit Tests")

    st.code(
        test_code,
        language="python"
    )


def render_documentation(documentation: str):
    st.subheader("📘 Documentation")
    st.markdown(documentation)


def render_generic_json(data):
    st.json(data)


def render_response(data: dict):
    if not isinstance(data, dict):
        st.write(data)
        return

    # =====================================================
    # CODE AGENT RESPONSE
    # =====================================================

    if "source_code" in data:
        st.success("Code generated successfully")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Code ID", data.get("code_id"))

        with col2:
            st.metric(
                "Requirements ID",
                data.get("requirements_id")
            )

        if data.get("project_title"):
            st.subheader("📦 Project")
            st.write(data.get("project_title"))

        if data.get("tech_stack"):
            st.subheader("🛠️ Tech Stack")

            for tech in data.get("tech_stack", []):
                st.badge(tech)

        render_source_code(
            data.get("source_code", {})
        )

        return

    # =====================================================
    # UNIT TEST RESPONSE
    # =====================================================

    if "test_code" in data:
        st.success("Unit tests generated")

        st.write(
            f"Frameworks Used: "
            f"{', '.join(data.get('frameworks_used', []))}"
        )

        render_unit_test(
            data.get("test_code", "")
        )

        return

    # =====================================================
    # DOCUMENTATION RESPONSE
    # =====================================================

    if "documentation" in data:
        render_documentation(
            data.get("documentation")
        )

        return

    # =====================================================
    # DEFAULT
    # =====================================================

    render_generic_json(data)


 
# LOGIN
 

def login(email: str, password: str) -> bool:
    res = api_call(
        "POST",
        "/login",
        {
            "email": email,
            "password": password
        }
    )

    if res and res.get("status"):
        st.session_state.logged_in = True
        st.session_state.user_email = email
        return True

    return False


 
# SIDEBAR
 

with st.sidebar:
    st.header("🔐 Login")

    if not st.session_state.get("logged_in"):
        email = st.text_input("Email")

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button("Login"):
            if login(email, password):
                st.success("Logged in!")
                st.rerun()
            else:
                st.error("Login failed")

    else:
        st.success(
            f"Logged in as "
            f"{st.session_state.user_email}"
        )

        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    st.markdown("---")
    st.markdown(f"**Backend:** `{BASE_URL}`")


if not st.session_state.get("logged_in"):
    st.warning("Please login using sidebar")
    st.stop()


 
# MAIN APP
 

st.title("🧪 Multi-Agent Testing UI")

tab_agents, tab_pipeline, tab_users = st.tabs(
    ["🤖 Agents", "🚀 Pipeline Orchestrator", "👥 User Management"]
)

 
# AGENTS TAB
 

with tab_agents:
    agent = st.radio(
        "Select Agent",
        [
            "Validation",
            "Requirements",
            "Code",
            "Unit Tests",
            "Insights",
            "Documentation"
        ],
        horizontal=True
    )

    st.markdown("---")

    # =====================================================
    # VALIDATION
    # =====================================================

    if agent == "Validation":
        st.subheader("📝 Validate Request")

        user_input = st.text_area(
            "User Input",
            key="validation_input"
        )

        if st.button("Validate Request"):
            with st.spinner("Validating..."):
                res = api_call(
                    "POST",
                    "/validate_request",
                    {
                        "user_input": user_input
                    }
                )

                if res:
                    data = extract_data(res)
                    st.session_state.validation_response = data

                    if data.get("session_id"):
                        st.session_state.validation_session_id = data.get("session_id")

                    st.rerun()

        validation_data = st.session_state.get("validation_response")

        if validation_data:
            render_response(validation_data)

            status = validation_data.get("status")

            if status == "clarify":
                clarification = st.text_area(
                    "Provide clarification",
                    key="clarification_input"
                )

                if st.button("Continue Request"):
                    continue_payload = {
                        "session_id": validation_data.get("session_id"),
                        "user_reply": clarification
                    }

                    with st.spinner("Continuing validation..."):
                        continue_res = api_call(
                            "POST",
                            "/continue_request",
                            continue_payload
                        )

                        if continue_res:
                            continue_data = extract_data(continue_res)
                            st.session_state.validation_response = continue_data
                            st.rerun()

    # =====================================================
    # REQUIREMENTS
    # =====================================================

    elif agent == "Requirements":
        st.subheader("📝 Generate Requirements")

        validation_session_id = st.number_input(
            "validation_session_id",
            min_value=1,
            step=1,
            value=st.session_state.get(
                "validation_session_id",
                1
            )
        )

        if st.button("Generate Requirements"):
            with st.spinner("Generating requirements..."):
                res = api_call(
                    "POST",
                    "/generate_requirements",
                    {
                        "validation_session_id": validation_session_id
                    }
                )

                if res:
                    data = extract_data(res)
                    render_response(data)

                    requirement_id = data.get("requirement_session_id")

                    if requirement_id:
                        st.session_state.requirement_id = requirement_id

    # =====================================================
    # CODE
    # =====================================================

    elif agent == "Code":
        st.subheader("📝 Generate Code")

        requirement_id = st.number_input(
            "requirements_id",
            min_value=1,
            step=1,
            value=st.session_state.get(
                "requirement_id",
                1
            )
        )

        if st.button("Generate Code"):
            with st.spinner("Generating code..."):
                gen = api_call(
                    "POST",
                    "/generate_code",
                    {
                        "requirements_id": requirement_id
                    }
                )

                if gen:
                    data = extract_data(gen)
                    render_response(data)

                    code_id = data.get("code_id")

                    if code_id:
                        st.session_state.code_id = code_id

        st.markdown("---")
        st.subheader("🔍 Fetch Code")

        fetch_code_id = st.number_input(
            "code_id",
            min_value=1,
            step=1,
            value=st.session_state.get(
                "code_id",
                1
            )
        )

        if st.button("Fetch Code"):
            with st.spinner("Fetching code..."):
                res = api_call(
                    "GET",
                    "/get_code",
                    {
                        "code_id": fetch_code_id
                    }
                )

                if res:
                    data = extract_data(res)
                    render_response(data)

    # =====================================================
    # UNIT TESTS
    # =====================================================

    elif agent == "Unit Tests":
        st.subheader("🧪 Generate Unit Tests")

        code_id = st.number_input(
            "code_id",
            min_value=1,
            step=1,
            value=st.session_state.get(
                "code_id",
                1
            ),
            key="generate_unit_test_code_id"
        )

        if st.button("Generate Unit Tests"):
            with st.spinner("Generating unit tests..."):
                gen = api_call(
                    "POST",
                    "/generate_unit_tests",
                    {
                        "code_id": code_id
                    }
                )

                if gen:
                    data = extract_data(gen)
                    render_response(data)

                    unit_test_id = data.get("unit_test_id")

                    if unit_test_id:
                        st.session_state.unit_test_id = unit_test_id

        st.markdown("---")
        st.subheader("🔍 Fetch Unit Tests")

        fetch_unit_test_id = st.number_input(
            "unit_test_id",
            min_value=1,
            step=1,
            value=st.session_state.get(
                "unit_test_id",
                1
            ),
            key="fetch_unit_test_id"
        )

        if st.button("Fetch Unit Tests"):
            with st.spinner("Fetching unit tests..."):
                res = api_call(
                    "GET",
                    "/get_unit_tests",
                    {
                        "unit_test_id": fetch_unit_test_id
                    }
                )

                if res:
                    data = extract_data(res)
                    render_response(data)

    # =====================================================
    # INSIGHTS AGENT
    # =====================================================

    elif agent == "Insights":
        st.subheader("📝 Generate Insights")

        unit_test_id = st.number_input(
            "unit_test_id",
            min_value=1,
            step=1,
            value=st.session_state.get(
                "unit_test_id",
                1
            ),
            key="insights_unit_test_id"
        )

        if st.button("Generate Insights"):
            with st.spinner("Generating insights..."):
                gen = api_call(
                    "POST",
                    "/generate_insights",
                    {
                        "unit_test_id": unit_test_id
                    }
                )

                if gen:
                    data = extract_data(gen)
                    st.json(data)

                    insight_id = data.get("insight_id")

                    if insight_id:
                        st.session_state.insight_id = insight_id
                        st.success(f"insight_id = {insight_id}")

        st.markdown("---")
        st.subheader("🔍 Fetch Insights")

        fetch_insight_id = st.number_input(
            "insights_id",
            min_value=1,
            step=1,
            value=st.session_state.get(
                "insight_id",
                1
            ),
            key="fetch_insights_id"
        )

        if st.button("Fetch Insights"):
            with st.spinner("Fetching insights..."):
                res = api_call(
                    "GET",
                    "/get_insights",
                    {
                        "insights_id": fetch_insight_id
                    }
                )

                if res:
                    data = extract_data(res)
                    st.json(data)

    # =====================================================
    # DOCUMENTATION AGENT
    # =====================================================

    elif agent == "Documentation":
        st.subheader("📝 Generate Documentation")

        insight_id = st.number_input(
            "insights_id",
            min_value=1,
            step=1,
            value=st.session_state.get(
                "insight_id",
                1
            ),
            key="documentation_insight_id"
        )

        if st.button("Generate Documentation"):
            with st.spinner("Generating documentation..."):
                gen = api_call(
                    "POST",
                    "/generate_documentation",
                    {
                        "insights_id": insight_id
                    }
                )

                if gen:
                    data = extract_data(gen)
                    st.json(data)

                    doc_id = data.get("doc_id")

                    if doc_id:
                        st.session_state.doc_id = doc_id
                        st.success(f"doc_id = {doc_id}")

        st.markdown("---")
        st.subheader("🔍 Fetch Documentation")

        fetch_doc_id = st.number_input(
            "documentation_id",
            min_value=1,
            step=1,
            value=st.session_state.get(
                "doc_id",
                1
            ),
            key="fetch_documentation_id"
        )

        if st.button("Fetch Documentation"):
            with st.spinner("Fetching documentation..."):
                res = api_call(
                    "GET",
                    "/get_documentation",
                    {
                        "documentation_id": fetch_doc_id
                    }
                )

                if res:
                    data = extract_data(res)
                    st.json(data)


 
# PIPELINE ORCHESTRATOR TAB
 

STATUS_ICONS = {
    "pending": "⏳",
    "running": "🔄",
    "completed": "✅",
    "failed": "❌",
    "awaiting_clarification": "❓",
    "rejected": "🚫",
}


def fetch_pipeline_status(run_id: int) -> Optional[dict]:
    res = api_call("GET", f"/pipeline/run/{run_id}")

    if not res:
        return None

    return extract_data(res)


def render_pipeline_status(data: dict):
    if not data or not data.get("run_id"):
        st.info("No pipeline run found. Start a pipeline above.")
        return

    status = data.get("status")
    icon = STATUS_ICONS.get(status, "•")

    col1, col2, col3 = st.columns(3)
    col1.metric("Run ID", data.get("run_id"))
    col2.metric("Status", f"{icon} {status}")
    col3.metric("Updated", data.get("updated_at") or "-")

    if data.get("user_input"):
        st.markdown("**Input**")
        st.write(data.get("user_input"))

    st.markdown("**Stages**")

    for step in data.get("steps", []):
        step_status = step.get("status")
        step_icon = STATUS_ICONS.get(step_status, "•")

        title = (
            f"{step_icon} {step.get('stage')} "
            f"— {step_status}"
        )

        with st.expander(title, expanded=step_status == "failed"):
            st.write(f"Attempt: {step.get('attempt')}")

            if step.get("artifact_id") is not None:
                st.write(
                    f"Artifact ID: {step.get('artifact_id')}"
                )

            if step.get("started_at"):
                st.write(f"Started: {step.get('started_at')}")

            if step.get("finished_at"):
                st.write(
                    f"Finished: {step.get('finished_at')}"
                )

            if step.get("error"):
                st.error(step.get("error"))

    artifacts = data.get("artifacts") or {}
    filled = {
        k: v for k, v in artifacts.items()
        if v is not None
    }

    if filled:
        st.markdown("**Artifacts**")

        cols = st.columns(len(filled))

        for col, (name, value) in zip(cols, filled.items()):
            col.metric(name, value)

    # =====================================================
    # CLARIFICATION
    # =====================================================

    run_id = data.get("run_id")

    if data.get("awaiting_clarification"):
        st.info(
            data.get("clarification_question")
            or "Clarification needed"
        )

        reply = st.text_area(
            "Your reply",
            key=f"pipeline_clarify_input_{run_id}"
        )

        if st.button(
            "Send Clarification",
            key=f"pipeline_clarify_btn_{run_id}"
        ):
            if not reply.strip():
                st.warning("Enter a reply")
            else:
                res = api_call(
                    "POST",
                    f"/pipeline/run/{run_id}/clarify",
                    {"user_reply": reply.strip()}
                )

                if res:
                    st.success("Clarification sent")
                    st.rerun()

    # =====================================================
    # FAILED → RESTART
    # =====================================================

    elif status == "failed":
        st.error("Pipeline failed")

        if st.button(
            "Restart Pipeline",
            key=f"pipeline_restart_btn_{run_id}"
        ):
            res = api_call(
                "POST",
                f"/pipeline/run/{run_id}/restart"
            )

            if res:
                st.success("Pipeline restarted")
                st.rerun()

    elif status == "completed":
        st.success("Pipeline completed")

    elif status == "rejected":
        st.warning("Request was rejected")


@st.fragment(run_every=30)
def live_pipeline_status(run_id: int):
    data = fetch_pipeline_status(run_id)

    if data:
        render_pipeline_status(data)
    else:
        st.warning("Unable to fetch pipeline status")


with tab_pipeline:
    st.header("🚀 Pipeline Orchestrator")

    pipeline_input = st.text_area(
        "Describe the pipeline you want to generate",
        key="pipeline_input"
    )

    col_start, col_run = st.columns([1, 1])

    with col_start:
        if st.button("Start Pipeline", type="primary"):
            if not pipeline_input.strip():
                st.warning("Enter a pipeline description")
            else:
                with st.spinner("Starting pipeline..."):
                    res = api_call(
                        "POST",
                        "/pipeline/run",
                        {"user_input": pipeline_input.strip()}
                    )

                if res:
                    data = extract_data(res)
                    run_id = data.get("run_id")

                    if run_id:
                        st.session_state.pipeline_run_id_input = run_id
                        st.success(f"Pipeline started (run_id={run_id})")
                        st.rerun()

    with col_run:
        if "pipeline_run_id_input" not in st.session_state:
            st.session_state.pipeline_run_id_input = 1

        run_id = st.number_input(
            "Run ID",
            min_value=1,
            step=1,
            key="pipeline_run_id_input"
        )

    st.markdown("---")

    live_pipeline_status(run_id)


 
# USER MANAGEMENT TAB
 

with tab_users:
    st.header("👥 User Management")

    action = st.selectbox(
        "Action",
        [
            "Create User",
            "Get All Users",
            "Get Single User",
            "Update User",
            "Delete User"
        ]
    )

    # =====================================================
    # CREATE USER
    # =====================================================

    if action == "Create User":
        email = st.text_input("Email")
        name = st.text_input("Name")
        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button("Create User"):
            res = api_call(
                "POST",
                "/create_users",
                {
                    "email": email,
                    "name": name,
                    "password": password
                }
            )

            if res:
                st.success("User created")
                st.json(res)

    # =====================================================
    # GET ALL USERS
    # =====================================================

    elif action == "Get All Users":
        if st.button("Fetch All Users"):
            res = api_call(
                "GET",
                "/get_all_users"
            )

            if res:
                st.json(res)

    # =====================================================
    # GET SINGLE USER
    # =====================================================

    elif action == "Get Single User":
        user_id = st.number_input(
            "User ID",
            min_value=1,
            step=1
        )

        if st.button("Get User"):
            res = api_call(
                "GET",
                f"/get_single_user/{user_id}"
            )

            if res:
                st.json(res)

    # =====================================================
    # UPDATE USER
    # =====================================================

    elif action == "Update User":
        user_id = st.number_input(
            "User ID",
            min_value=1,
            step=1,
            key="update_user_id"
        )

        name = st.text_input("New Name")

        if st.button("Update User"):
            payload = {}

            if name:
                payload["name"] = name

            if payload:
                res = api_call(
                    "PATCH",
                    f"/update_user/{user_id}",
                    payload
                )

                if res:
                    st.success("User updated")
                    st.json(res)

            else:
                st.warning("At least one field required")

    # =====================================================
    # DELETE USER
    # =====================================================

    elif action == "Delete User":
        user_id = st.number_input(
            "User ID",
            min_value=1,
            step=1,
            key="delete_user_id"
        )

        if st.button("Delete User"):
            res = api_call(
                "DELETE",
                f"/delete_single_user/{user_id}"
            )

            if res:
                st.success("User deleted")
                st.json(res)
