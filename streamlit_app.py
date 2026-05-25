# poetry run streamlit run streamlit_app.py

import streamlit as st
import requests
from typing import Optional, Dict, Any

BASE_URL = "http://localhost:8000"

# =========================================================
# SESSION
# =========================================================

if "session" not in st.session_state:
    st.session_state.session = requests.Session()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# =========================================================
# API CALL
# =========================================================

def api_call(
    method: str,
    endpoint: str,
    payload: Optional[Dict] = None,
    params: Optional[Dict] = None,
) -> Dict[str, Any]:

    url = f"{BASE_URL}{endpoint}"

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


# =========================================================
# LOGIN
# =========================================================

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


# =========================================================
# SIDEBAR
# =========================================================

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


# =========================================================
# MAIN APP
# =========================================================

st.title("🧪 Multi-Agent Testing UI")

tab_agents, tab_users = st.tabs(
    ["🤖 Agents", "👥 User Management"]
)


# =========================================================
# AGENTS TAB
# =========================================================

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
    # VALIDATION AGENT
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
                        st.session_state.validation_session_id = data.get(
                            "session_id"
                        )

                    st.rerun()

        validation_data = st.session_state.get(
            "validation_response"
        )

        if validation_data:

            st.json(validation_data)

            status = validation_data.get("status")

            # ---------------- CLARIFY ----------------

            if status == "clarify":

                st.warning(
                    validation_data.get("message")
                )

                clarification = st.text_area(
                    "Provide clarification",
                    key="clarification_input"
                )

                if st.button("Continue Request"):

                    continue_payload = {
                        "session_id": validation_data.get(
                            "session_id"
                        ),
                        "user_reply": clarification
                    }

                    with st.spinner(
                        "Continuing validation..."
                    ):

                        continue_res = api_call(
                            "POST",
                            "/continue_request",
                            continue_payload
                        )

                        if continue_res:

                            continue_data = extract_data(
                                continue_res
                            )

                            st.session_state.validation_response = (
                                continue_data
                            )

                            if continue_data.get(
                                "session_id"
                            ):
                                st.session_state.validation_session_id = (
                                    continue_data.get(
                                        "session_id"
                                    )
                                )

                            st.rerun()

            # ---------------- VALID ----------------

            elif status == "valid":

                st.success("Validation successful")

                st.info(
                    f"Use validation_session_id = "
                    f"{validation_data.get('session_id')} "
                    f"in Requirements Agent"
                )

            # ---------------- INVALID ----------------

            elif status == "invalid":

                st.error(
                    validation_data.get("message")
                )

    # =====================================================
    # REQUIREMENTS AGENT
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
            ),
            key="requirements_validation_id"
        )

        if st.button("Generate Requirements"):

            with st.spinner(
                "Generating requirements..."
            ):

                res = api_call(
                    "POST",
                    "/generate_requirements",
                    {
                        "validation_session_id":
                        validation_session_id
                    }
                )

                if res:

                    data = extract_data(res)

                    st.json(data)

                    requirement_id = data.get(
                        "requirement_session_id"
                    )

                    if requirement_id:

                        st.session_state.requirement_id = (
                            requirement_id
                        )

                        st.success(
                            f"requirement_session_id = "
                            f"{requirement_id}"
                        )

        st.markdown("---")

        st.info(
            "Requirements GET endpoint not available"
        )

    # =====================================================
    # CODE AGENT
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
            ),
            key="code_requirement_id"
        )

        if st.button("Generate Code"):

            with st.spinner("Generating code..."):

                gen = api_call(
                    "POST",
                    "/generate_code",
                    {
                        "requirements_id":
                        requirement_id
                    }
                )

                if gen:

                    data = extract_data(gen)

                    st.json(data)

                    code_id = data.get("code_id")

                    if code_id:

                        st.session_state.code_id = code_id

                        st.success(
                            f"code_id = {code_id}"
                        )

        st.markdown("---")

        st.subheader("🔍 Fetch Code")

        fetch_code_id = st.number_input(
            "code_id",
            min_value=1,
            step=1,
            value=st.session_state.get(
                "code_id",
                1
            ),
            key="fetch_code_id"
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

                    st.json(data)

    # =====================================================
    # UNIT TESTS AGENT
    # =====================================================

    elif agent == "Unit Tests":

        st.subheader("📝 Generate Unit Tests")

        code_id = st.number_input(
            "code_id",
            min_value=1,
            step=1,
            value=st.session_state.get(
                "code_id",
                1
            ),
            key="unit_test_code_id"
        )

        if st.button("Generate Unit Tests"):

            with st.spinner(
                "Generating unit tests..."
            ):

                gen = api_call(
                    "POST",
                    "/generate_unit_tests",
                    {
                        "code_id": code_id
                    }
                )

                if gen:

                    data = extract_data(gen)

                    st.json(data)

                    unit_test_id = data.get(
                        "unit_test_id"
                    )

                    if unit_test_id:

                        st.session_state.unit_test_id = (
                            unit_test_id
                        )

                        st.success(
                            f"unit_test_id = "
                            f"{unit_test_id}"
                        )

        st.markdown("---")

        st.subheader("🔍 Fetch Unit Tests")

        fetch_ut_id = st.number_input(
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

            with st.spinner(
                "Fetching unit tests..."
            ):

                res = api_call(
                    "GET",
                    "/get_unit_tests",
                    {
                        "unit_test_id":
                        fetch_ut_id
                    }
                )

                if res:

                    data = extract_data(res)

                    st.json(data)

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

            with st.spinner(
                "Generating insights..."
            ):

                gen = api_call(
                    "POST",
                    "/generate_insights",
                    {
                        "unit_test_id":
                        unit_test_id
                    }
                )

                if gen:

                    data = extract_data(gen)

                    st.json(data)

                    insight_id = data.get(
                        "insight_id"
                    )

                    if insight_id:

                        st.session_state.insight_id = (
                            insight_id
                        )

                        st.success(
                            f"insight_id = "
                            f"{insight_id}"
                        )

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

            with st.spinner(
                "Fetching insights..."
            ):

                res = api_call(
                    "GET",
                    "/get_insights",
                    {
                        "insights_id":
                        fetch_insight_id
                    }
                )

                if res:

                    data = extract_data(res)

                    st.json(data)

    # =====================================================
    # DOCUMENTATION AGENT
    # =====================================================

    elif agent == "Documentation":

        st.subheader(
            "📝 Generate Documentation"
        )

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

            with st.spinner(
                "Generating documentation..."
            ):

                gen = api_call(
                    "POST",
                    "/generate_documentation",
                    {
                        "insights_id":
                        insight_id
                    }
                )

                if gen:

                    data = extract_data(gen)

                    st.json(data)

                    doc_id = data.get("doc_id")

                    if doc_id:

                        st.session_state.doc_id = (
                            doc_id
                        )

                        st.success(
                            f"doc_id = {doc_id}"
                        )

        st.markdown("---")

        st.subheader(
            "🔍 Fetch Documentation"
        )

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

            with st.spinner(
                "Fetching documentation..."
            ):

                res = api_call(
                    "GET",
                    "/get_documentation",
                    {
                        "documentation_id":
                        fetch_doc_id
                    }
                )

                if res:

                    data = extract_data(res)

                    st.json(data)


# =========================================================
# USER MANAGEMENT TAB
# =========================================================

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

        name = st.text_input(
            "New Name"
        )

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

                st.warning(
                    "At least one field required"
                )

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