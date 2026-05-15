#poetry run streamlit run streamlit_app.py

import streamlit as st
import requests
from typing import Optional, Dict, Any

BASE_URL = "http://localhost:8000"

# ---------- Session ----------
if "session" not in st.session_state:
    st.session_state.session = requests.Session()

def api_call(method: str, endpoint: str, payload: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
    url = f"{BASE_URL}{endpoint}"
    try:
        if method.upper() == "GET":
            resp = st.session_state.session.get(url, params=params or payload)
        else:
            resp = st.session_state.session.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API call failed: {e}")
        if 'resp' in locals():
            st.error(f"Response: {resp.text}")
        return {}

def extract_data(response: dict) -> dict:
    if isinstance(response, dict) and "data" in response:
        return response["data"]
    return response

def login(email: str, password: str) -> bool:
    res = api_call("POST", "/login", {"email": email, "password": password})
    if res and res.get("status"):
        st.session_state.logged_in = True
        st.session_state.user_email = email
        return True
    return False

# ---------- Sidebar Login ----------
with st.sidebar:
    st.header("🔐 Login")
    if not st.session_state.get("logged_in"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login(email, password):
                st.success("Logged in!")
                st.rerun()
            else:
                st.error("Login failed")
    else:
        st.success(f"Logged in as {st.session_state.user_email}")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()
    st.markdown("---")
    st.markdown(f"**Backend:** `{BASE_URL}`")

if not st.session_state.get("logged_in"):
    st.warning("Please login using the sidebar.")
    st.stop()

# ---------- Main App ----------
st.title("🧪 Multi-Agent System – Testing UI")
tab_agents, tab_users = st.tabs(["🤖 Agents", "👥 User Management"])

# ==================== AGENTS TAB (VERTICAL LAYOUT) ====================
# ==================== AGENTS TAB (VERTICAL LAYOUT WITH DEBUG) ====================
with tab_agents:
    agent = st.radio(
        "Select agent",
        ["Validation", "Requirements", "Code", "Unit Tests", "Insights", "Documentation"],
        horizontal=True
    )
    
    st.markdown("---")
    
    # ----- Validation Agent -----
    if agent == "Validation":
        st.subheader("📝 Generate (POST)")
        user_input = st.text_area("User Input", key="val_input")
        if st.button("Validate Request", key="val_gen"):
            with st.spinner("Validating..."):
                res = api_call("POST", "/validate_request", {"user_input": user_input})
                if res:
                    st.json(extract_data(res))
        st.markdown("---")
        st.subheader("🔍 Fetch (GET)")
        st.info("Validation has no GET endpoint – use generate to get session ID.")
    
        # ----- Requirements Agent -----
    elif agent == "Requirements":
        st.subheader("📝 Generate (POST)")
        val_sess_id = st.number_input("validation_session_id", min_value=1, step=1, key="req_gen_id")
        if st.button("Generate Requirements", key="req_gen"):
            with st.spinner("Generating requirements..."):
                res = api_call("POST", "/generate_requirements", {"validation_session_id": val_sess_id})
                if res:
                    data = extract_data(res)  # data = {"requirement_session_id": ..., "status": ..., "message": ..., "data": {...}}
                    req_id = data.get("requirement_session_id")
                    if req_id:
                        st.success(f"requirement_session_id = {req_id}")
                        st.write("**Status:**", data.get("status", "N/A"))
                        st.write("**Message:**", data.get("message", "N/A"))
                        # Display the nested requirement content
                        req_data = data.get("data", {})
                        if req_data:
                            st.subheader("Requirements Details")
                            st.json(req_data)
                        else:
                            st.info("No detailed requirement data returned.")
                    else:
                        st.error("No 'requirement_session_id' in response. Raw data:")
                        st.json(data)
        st.markdown("---")
        st.subheader("🔍 Fetch (GET)")
        st.info("No GET endpoint for requirements. Use the requirement_session_id in the Code agent to generate code.")
    
        # ----- Code Agent -----
    elif agent == "Code":
        st.subheader("📝 Generate (POST)")
        req_id = st.number_input("requirements_id", min_value=1, step=1, key="code_gen_id")
        if st.button("Generate Code", key="code_gen"):
            with st.spinner("Generating code..."):
                gen = api_call("POST", "/generate_code", {"requirements_id": req_id})
                if gen:
                    data = extract_data(gen)
                    code_id = data.get("code_id")
                    if code_id:
                        st.success(f"code_id = {code_id}")
                        # Display generated metadata
                        st.write("**Project Title:**", data.get("project_title", "N/A"))
                        st.write("**Tech Stack:**", ", ".join(data.get("tech_stack", [])) if data.get("tech_stack") else "N/A")
                        st.write("**File Structure:**")
                        for file_path in data.get("file_structure", []):
                            st.write(f"- {file_path}")
                        # Show source code
                        source_code = data.get("source_code", {})
                        if source_code:
                            st.subheader("Generated Source Code")
                            for filename, code in source_code.items():
                                with st.expander(f"📄 {filename}"):
                                    st.code(code, language="python" if filename.endswith(".py") else "javascript")
                        else:
                            st.warning("No source code returned.")
                    else:
                        st.error("No 'code_id' in response. Raw data:")
                        st.json(data)
        st.markdown("---")
        st.subheader("🔍 Fetch (GET) by ID")
        fetch_id = st.number_input("code_id", min_value=1, step=1, key="code_fetch_id")
        if st.button("Fetch Code", key="code_fetch"):
            with st.spinner("Fetching code..."):
                res = api_call("GET", "/get_code", {"code_id": fetch_id})
                if res:
                    data = extract_data(res)
                    st.write("**Project Title:**", data.get("project_title", "N/A"))
                    st.write("**Tech Stack:**", ", ".join(data.get("tech_stack", [])) if data.get("tech_stack") else "N/A")
                    st.write("**File Structure:**")
                    for file_path in data.get("file_structure", []):
                        st.write(f"- {file_path}")
                    source_code = data.get("source_code", {})
                    if source_code:
                        st.subheader("Source Code")
                        for filename, code in source_code.items():
                            with st.expander(f"📄 {filename}"):
                                st.code(code, language="python" if filename.endswith(".py") else "javascript")
                    else:
                        st.warning("No source code found.")
                else:
                    st.error("No response received.")
    
    # ----- Unit Tests Agent -----
       
    elif agent == "Unit Tests":
        st.subheader("📝 Generate (POST)")
        code_id = st.number_input("code_id", min_value=1, step=1, key="ut_gen_id")
        if st.button("Generate Unit Tests", key="ut_gen"):
            with st.spinner("Generating unit tests..."):
                gen = api_call("POST", "/generate_unit_tests", {"code_id": code_id})
                if gen:
                    data = extract_data(gen)
                    ut_id = data.get("unit_test_id")
                    st.success(f"unit_test_id = {ut_id}")
                    # Auto-fetch
                    fetch = api_call("GET", "/get_unit_tests", {"unit_test_id": ut_id})
                    if fetch:
                        test_data = extract_data(fetch)
                        st.subheader("Test Code")
                        st.code(test_data.get("test_code", ""), language="python")
                        st.write("**Test Summary:**", test_data.get("test_summary", "N/A"))
                        st.write("**Frameworks Used:**", test_data.get("frameworks_used", []))
        st.markdown("---")
        st.subheader("🔍 Fetch (GET) by ID")
        fetch_ut_id = st.number_input("unit_test_id", min_value=1, step=1, key="ut_fetch_id")
        if st.button("Fetch Unit Tests", key="ut_fetch"):
            with st.spinner("Fetching unit tests..."):
                res = api_call("GET", "/get_unit_tests", {"unit_test_id": fetch_ut_id})
                if res:
                    st.subheader("Raw Response")
                    st.json(res)
                    test_data = extract_data(res)
                    test_code = test_data.get("test_code", "")
                    if test_code:
                        st.subheader("Test Code")
                        st.code(test_code, language="python")
                    else:
                        st.warning("No test_code found.")
                    st.write("**Test Summary:**", test_data.get("test_summary", "N/A"))
                    st.write("**Frameworks Used:**", test_data.get("frameworks_used", []))
                else:
                    st.error("No response received.")
    
       # ----- Insights Agent -----
    elif agent == "Insights":
        st.subheader("📝 Generate (POST)")
        ut_id = st.number_input("unit_test_id", min_value=1, step=1, key="ins_gen_id")
        if st.button("Generate Insights", key="ins_gen"):
            with st.spinner("Generating insights..."):
                gen = api_call("POST", "/generate_insights", {"unit_test_id": ut_id})
                if gen:
                    data = extract_data(gen)
                    ins_id = data.get("insight_id")
                    if ins_id:
                        st.success(f"insight_id = {ins_id}")
                        fetch = api_call("GET", "/get_insights", {"insights_id": ins_id})
                        if fetch:
                            ins_data = extract_data(fetch)
                            # Display all fields from the model
                            st.write("### Insights Summary")
                            st.write(ins_data.get("insights_summary", "N/A"))
                            
                            fields_to_display = [
                                ("Key Insights", "key_insights"),
                                ("Missing Implementations", "missing_implementations"),
                                ("Code Quality Issues", "code_quality_issues"),
                                ("Security Issues", "security_issues"),
                                ("Scalability Problems", "scalability_problems"),
                                ("Refactoring Suggestions", "refactoring_suggestions"),
                                ("Dependencies", "dependencies"),
                                ("Recommendations", "recommendations")
                            ]
                            for title, field in fields_to_display:
                                values = ins_data.get(field, [])
                                if values:
                                    st.write(f"### {title}")
                                    for item in values:
                                        st.write(f"- {item}")
                    else:
                        st.error("No 'insight_id' in response. Raw data:")
                        st.json(data)
        st.markdown("---")
        st.subheader("🔍 Fetch (GET) by ID")
        fetch_ins_id = st.number_input("insights_id", min_value=1, step=1, key="ins_fetch_id")
        if st.button("Fetch Insights", key="ins_fetch"):
            with st.spinner("Fetching insights..."):
                res = api_call("GET", "/get_insights", {"insights_id": fetch_ins_id})
                if res:
                    st.subheader("Raw Response")
                    st.json(res)
                    ins_data = extract_data(res)
                    st.write("### Insights Summary")
                    st.write(ins_data.get("insights_summary", "N/A"))
                    
                    fields_to_display = [
                        ("Key Insights", "key_insights"),
                        ("Missing Implementations", "missing_implementations"),
                        ("Code Quality Issues", "code_quality_issues"),
                        ("Security Issues", "security_issues"),
                        ("Scalability Problems", "scalability_problems"),
                        ("Refactoring Suggestions", "refactoring_suggestions"),
                        ("Dependencies", "dependencies"),
                        ("Recommendations", "recommendations")
                    ]
                    for title, field in fields_to_display:
                        values = ins_data.get(field, [])
                        if values:
                            st.write(f"### {title}")
                            for item in values:
                                st.write(f"- {item}")
                    if not ins_data.get("insights_summary") and not any(ins_data.get(f) for _, f in fields_to_display):
                        st.warning("No insights found.")
                else:
                    st.error("No response received.")
    
           # ----- Documentation Agent -----
    elif agent == "Documentation":
        st.subheader("📝 Generate (POST)")
        ins_id = st.number_input("insights_id", min_value=1, step=1, key="doc_gen_id")
        if st.button("Generate Documentation", key="doc_gen"):
            with st.spinner("Generating documentation..."):
                gen = api_call("POST", "/generate_documentation", {"insights_id": ins_id})
                if gen:
                    data = extract_data(gen)
                    # Note: response contains "doc_id" (not "documentation_id")
                    doc_id = data.get("doc_id")
                    if doc_id:
                        st.success(f"doc_id = {doc_id}")
                        # Auto-fetch after generation
                        fetch = api_call("GET", "/get_documentation", {"documentation_id": doc_id})
                        if fetch:
                            doc_data = extract_data(fetch)
                            # Display all fields from Documentation model
                            st.write("### Overview")
                            st.write(doc_data.get("overview", "N/A"))
                            st.write("### Architecture")
                            st.write(doc_data.get("architecture", "N/A"))
                            st.write("### Test Summary")
                            st.write(doc_data.get("test_summary", "N/A"))
                            
                            fields_to_display = [
                                ("File Responsibilities", "file_responsibilities"),
                                ("Functional Requirements", "functional_requirements"),
                                ("Non-Functional Requirements", "non_functional_requirements"),
                                ("Tech Stack Used", "tech_stack_used"),
                                ("Assumptions", "assumptions"),
                                ("Next Steps", "next_steps")
                            ]
                            for title, field in fields_to_display:
                                values = doc_data.get(field, [])
                                if values:
                                    st.write(f"### {title}")
                                    if isinstance(values, list):
                                        for item in values:
                                            st.write(f"- {item}")
                                    else:
                                        st.write(values)
                    else:
                        st.error("No 'doc_id' in response. Raw data:")
                        st.json(data)
        st.markdown("---")
        st.subheader("🔍 Fetch (GET) by ID")
        fetch_doc_id = st.number_input("documentation_id", min_value=1, step=1, key="doc_fetch_id")
        if st.button("Fetch Documentation", key="doc_fetch"):
            with st.spinner("Fetching documentation..."):
                res = api_call("GET", "/get_documentation", {"documentation_id": fetch_doc_id})
                if res:
                    st.subheader("Raw Response")
                    st.json(res)
                    doc_data = extract_data(res)
                    st.write("### Overview")
                    st.write(doc_data.get("overview", "N/A"))
                    st.write("### Architecture")
                    st.write(doc_data.get("architecture", "N/A"))
                    st.write("### Test Summary")
                    st.write(doc_data.get("test_summary", "N/A"))
                    
                    fields_to_display = [
                        ("File Responsibilities", "file_responsibilities"),
                        ("Functional Requirements", "functional_requirements"),
                        ("Non-Functional Requirements", "non_functional_requirements"),
                        ("Tech Stack Used", "tech_stack_used"),
                        ("Assumptions", "assumptions"),
                        ("Next Steps", "next_steps")
                    ]
                    for title, field in fields_to_display:
                        values = doc_data.get(field, [])
                        if values:
                            st.write(f"### {title}")
                            if isinstance(values, list):
                                for item in values:
                                    st.write(f"- {item}")
                            else:
                                st.write(values)
                    if not doc_data.get("overview") and not any(doc_data.get(f) for _, f in fields_to_display):
                        st.warning("No documentation found.")
                else:
                    st.error("No response received.")
# ==================== USER MANAGEMENT TAB ====================
with tab_users:
    st.header("👥 User Management")
    action = st.selectbox("Action", ["Create User", "Get All Users", "Get Single User", "Update User", "Delete User"])
    
    if action == "Create User":
        email = st.text_input("Email", key="create_email")
        name = st.text_input("Name", key="create_name")
        password = st.text_input("Password", type="password", key="create_pw")
        if st.button("Create User"):
            res = api_call("POST", "/creat_users", {"email": email, "name": name, "password": password})
            if res:
                st.success("User created")
                st.json(res)
    
    elif action == "Get All Users":
        if st.button("Fetch All Users"):
            res = api_call("GET", "/get_all_users")
            if res:
                st.json(res)
    
    elif action == "Get Single User":
        uid = st.number_input("User ID", min_value=1, step=1)
        if st.button("Get User"):
            res = api_call("GET", f"/get_single_user/{uid}")
            if res:
                st.json(res)
    
    elif action == "Update User":
        uid = st.number_input("User ID", min_value=1, step=1, key="update_uid")
        email = st.text_input("New Email", key="update_email")
        name = st.text_input("New Name", key="update_name")
        password = st.text_input("New Password", type="password", key="update_pw")
        if st.button("Update User"):
            payload = {}
            if email: payload["email"] = email
            if name: payload["name"] = name
            if password: payload["password"] = password
            if payload:
                res = api_call("PATCH", f"/update_user/{uid}", payload)
                if res:
                    st.success("User updated")
                    st.json(res)
            else:
                st.warning("At least one field required")
    
    elif action == "Delete User":
        uid = st.number_input("User ID", min_value=1, step=1, key="del_uid")
        if st.button("Delete User"):
            res = api_call("DELETE", f"/delete_single_user/{uid}")
            if res:
                st.success("User deleted")
                st.json(res)