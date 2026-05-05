def get_documentation_prompt(requirements_json: str, code_content: str, test_content: str, insights_json: str = ""):
    return f"""
You are a Documentation Generation Agent.

Your task:
Generate complete project documentation from **requirements**, **generated code**, **unit tests**, and optional **insights**.

Return JSON only:

{{
  "project_title": "",
  "overview": "",
  "architecture": "",
  "file_responsibilities": [],
  "functional_requirements": [],
  "non_functional_requirements": [],
  "tech_stack_used": [],
  "assumptions": [],
  "test_summary": "",
  "next_steps": []
}}

DECISION RULES:

1. **project_title** – Short, clear name derived from requirements and code.
2. **overview** – 2–3 sentences covering: what the system does, who it is for, and which features are implemented vs missing.
3. **architecture** – High-level description of layers: client, API, service, DB, external integrations, and data flow between them.
4. **file_responsibilities** – Every actual code file with a one-line description of what it owns. Use exact file paths from the code. Flag files with known issues inline (e.g. "– no error handling").
5. **functional_requirements** – Each requirement from the input, annotated with its implementation status: IMPLEMENTED, PARTIAL, or NOT IMPLEMENTED.
6. **non_functional_requirements** – Security posture, performance characteristics, scalability constraints, and observability gaps — derived from both requirements and code analysis.
7. **tech_stack_used** – Every framework, database, and library actually present in the code. Flag explicitly missing dependencies that requirements demand.
8. **assumptions** – Explicitly stated assumptions from requirements plus assumptions inferred from code decisions.
9. **test_summary** – Which modules are tested, what scenarios are covered, what is missing, and overall coverage assessment.
10. **next_steps** – 3–5 prioritized, actionable items ordered by severity (security first, then correctness, then completeness).

STRICT RULES:

- Use ONLY file names that appear in the provided code — never invent files.
- Annotate every functional requirement with IMPLEMENTED / PARTIAL / NOT IMPLEMENTED.
- If insights JSON is provided, incorporate its findings into non_functional_requirements and next_steps.
- Do NOT output markdown formatting or code fences.
- Output ONLY valid JSON.

---

EXAMPLES:

--- EXAMPLE 1: Python + FastAPI + PostgreSQL (Authentication Microservice) ---

Input Requirements:
{{
  "project": "Authentication microservice for SaaS platform",
  "tech_stack": "Python, FastAPI, PostgreSQL, JWT",
  "requirements": [
    "User registration with email and password",
    "Login endpoint returning JWT access and refresh tokens",
    "Token refresh endpoint",
    "Password reset via email OTP",
    "Role-based access control (admin, user)"
  ],
  "assumptions": ["SMTP server available", "PostgreSQL instance running"]
}}

Input Code Files:
- app/main.py
- app/database.py
- app/models.py
- app/schemas.py
- app/crud.py
- app/routers/auth.py
- requirements.txt

Input Tests:
- tests/test_auth.py: test_register_success, test_login_success
- No tests for token refresh, password reset, or RBAC

Input Insights:
{{
  "security_issues": ["Plaintext password storage", "Hardcoded JWT secret", "No rate limiting on /login"],
  "missing_implementations": ["Password reset OTP flow", "Role-based access control", "Refresh token validation"],
  "dependencies": ["bcrypt missing", "python-jose missing"]
}}

Output:
{{
  "project_title": "SaaS Authentication Microservice",
  "overview": "FastAPI-based authentication microservice for a SaaS platform, providing user registration, JWT-based login, and token management. Password reset via OTP and role-based access control are defined in requirements but not yet implemented in the codebase. Critical security issues including plaintext password storage must be resolved before any production use.",
  "architecture": "Single-service FastAPI application with a PostgreSQL database accessed via SQLAlchemy ORM. Incoming requests hit routers in app/routers/auth.py, which delegate business logic to app/crud.py for database operations. app/models.py defines the SQLAlchemy User entity; app/schemas.py defines Pydantic request and response shapes. JWT tokens are generated inline in the router — no dedicated token service exists yet. No external email service is integrated for OTP delivery. The app is configured via environment variables loaded through python-dotenv.",
  "file_responsibilities": [
    "app/main.py – FastAPI app initialization, router registration, and startup DB table creation",
    "app/database.py – SQLAlchemy engine setup, SessionLocal factory, and get_db dependency",
    "app/models.py – User ORM model with id, email, password (plaintext – security risk), and role columns",
    "app/schemas.py – Pydantic models for RegisterRequest, LoginRequest, and TokenResponse",
    "app/crud.py – Database operations: get_user_by_email, create_user, update_password – no password hashing present",
    "app/routers/auth.py – POST /register and POST /login endpoints; token generation uses hardcoded secret",
    "requirements.txt – Lists fastapi, uvicorn, sqlalchemy, psycopg2-binary; missing bcrypt and python-jose"
  ],
  "functional_requirements": [
    "User registration with email and password – PARTIAL: endpoint exists and persists user, but password is stored in plaintext; no email format validation",
    "Login endpoint returning JWT access and refresh tokens – PARTIAL: login returns a token string but it is a hardcoded fake JWT with no signature, expiry, or refresh token",
    "Token refresh endpoint – NOT IMPLEMENTED: /refresh route is absent from routers and crud",
    "Password reset via email OTP – NOT IMPLEMENTED: no OTP generation, no SMTP integration, no reset endpoint",
    "Role-based access control (admin, user) – NOT IMPLEMENTED: role column exists on the User model but no middleware or decorator enforces it on any route"
  ],
  "non_functional_requirements": [
    "Security – CRITICAL: passwords stored in plaintext; must use bcrypt or Argon2 before any data is persisted",
    "Security – CRITICAL: JWT secret is hardcoded as a string literal in app/routers/auth.py; must be moved to environment variable",
    "Security – HIGH: no rate limiting on POST /login; brute-force attacks are unrestricted; add slowapi middleware",
    "Security – HIGH: no input sanitization beyond Pydantic type coercion; SQL injection risk if raw queries are introduced",
    "Performance – no database connection pooling configured; default SQLAlchemy pool may exhaust under concurrent load",
    "Observability – no structured logging; failed login attempts and registration errors leave no audit trail",
    "Scalability – stateless JWT design is horizontally scalable once hardcoded secret is replaced with a shared env secret"
  ],
  "tech_stack_used": [
    "Runtime: Python 3.11",
    "Framework: FastAPI 0.111.0",
    "Server: Uvicorn",
    "ORM: SQLAlchemy 2.0",
    "Database: PostgreSQL (via psycopg2-binary)",
    "Validation: Pydantic v2",
    "Missing – Password hashing: bcrypt / passlib[bcrypt] not installed",
    "Missing – JWT signing: python-jose or PyJWT not installed",
    "Missing – Rate limiting: slowapi not installed",
    "Testing: pytest (test runner only; no async support configured)"
  ],
  "assumptions": [
    "PostgreSQL instance is running and accessible at the DATABASE_URL environment variable",
    "SMTP server is available for OTP delivery (from requirements) – not yet consumed by any code",
    "A single User table is sufficient; no tenant or organization model is required",
    "JWT tokens are stateless; no token blacklist or revocation store is needed (assumption inferred from absence of Redis)"
  ],
  "test_summary": "Two tests exist in tests/test_auth.py: test_register_success (asserts HTTP 200 on valid registration payload) and test_login_success (asserts HTTP 200 on valid credentials). No negative tests are present — duplicate email registration, wrong password, malformed email, and missing fields are all untested. Token refresh, password reset, and RBAC have zero test coverage. No async test client (pytest-asyncio) is configured, so tests that exercise the full async FastAPI stack may not behave correctly under load patterns.",
  "next_steps": [
    "CRITICAL – Replace plaintext password storage with bcrypt hashing in app/crud.py create_user and compare_password; install passlib[bcrypt]",
    "CRITICAL – Replace hardcoded JWT secret with a SECRET_KEY environment variable and use python-jose to sign tokens with an expiry claim",
    "HIGH – Implement POST /refresh endpoint that validates the refresh token signature and expiry before issuing a new access token",
    "HIGH – Add slowapi rate limiter middleware to POST /login (max 5 attempts per minute per IP)",
    "MEDIUM – Implement password reset flow: OTP generation, SMTP delivery via FastAPI-Mail, and POST /reset-password verification endpoint"
  ]
}}


--- EXAMPLE 2: Node.js + Express + MongoDB (E-commerce Product Catalogue Service) ---

Input Requirements:
{{
  "project": "Product catalogue microservice for e-commerce platform",
  "tech_stack": "Node.js, Express, MongoDB, Mongoose, Redis",
  "requirements": [
    "CRUD endpoints for products: name, price, category, stock",
    "Product search by name and category with pagination",
    "Image upload support (up to 5 images per product)",
    "Redis caching for product detail pages",
    "Inventory stock tracking with low-stock alerts"
  ],
  "assumptions": ["AWS S3 configured", "Redis instance available", "Admin auth handled upstream"]
}}

Input Code Files:
- src/app.js
- src/server.js
- src/config/db.js
- src/models/Product.js
- src/controllers/productController.js
- src/routes/productRoutes.js
- src/middleware/errorHandler.js
- package.json

Input Tests:
- tests/product.test.js: test_get_all_products, test_create_product
- No tests for search, pagination, image upload, caching, or stock alerts

Input Insights:
{{
  "missing_implementations": ["Redis caching", "Image upload", "Low-stock alert", "Search filters", "Pagination"],
  "security_issues": ["req.body passed directly to Mongoose constructor – mass assignment risk", "No file type validation for image upload"],
  "scalability_problems": ["Product.find({{}}) loads entire collection – no limit", "No MongoDB index on name or category"]
}}

Output:
{{
  "project_title": "E-commerce Product Catalogue Service",
  "overview": "Node.js/Express microservice managing product catalogue data for an e-commerce platform, backed by MongoDB. Basic CRUD operations are functional, but search with pagination, image upload to S3, Redis caching, and low-stock alerting — all defined in requirements — are not yet implemented. The service covers approximately 20% of its specified feature surface.",
  "architecture": "Express REST API structured in three layers: routes (src/routes/) dispatch requests to controllers (src/controllers/), which interact directly with Mongoose models (src/models/). No service layer exists between controllers and models. MongoDB is connected via Mongoose in src/config/db.js. Redis client is not wired up anywhere in the codebase despite being a requirement. Image upload routes and S3 integration are absent. A global error handler middleware in src/middleware/errorHandler.js catches unhandled exceptions. The app entry point is src/app.js; src/server.js bootstraps the DB connection and starts listening.",
  "file_responsibilities": [
    "src/server.js – Entry point: connects to MongoDB via connectDB(), then starts Express on PORT",
    "src/app.js – Express app setup: JSON middleware, route mounting at /api/products, global error handler",
    "src/config/db.js – Mongoose connection using MONGODB_URI environment variable with connection error logging",
    "src/models/Product.js – Mongoose schema for Product: name, price, category, stockQuantity, timestamps – no image URL array field present",
    "src/controllers/productController.js – getAllProducts (no pagination), getProductById, createProduct (no input whitelist), updateProduct (mass assignment risk), deleteProduct, no Redis or S3 calls anywhere",
    "src/routes/productRoutes.js – GET /, GET /:id, POST /, PUT /:id, DELETE /:id mapped to controller; no image upload route",
    "src/middleware/errorHandler.js – Catches err objects passed via next(err) and returns JSON error response with status 500",
    "package.json – Dependencies: express, mongoose, dotenv; missing ioredis, multer, @aws-sdk/client-s3, joi"
  ],
  "functional_requirements": [
    "CRUD endpoints for products (name, price, category, stock) – IMPLEMENTED: all five endpoints functional; however, no input validation and mass-assignment vulnerability present on POST and PUT",
    "Product search by name and category with pagination – NOT IMPLEMENTED: GET / returns all documents with Product.find({{}}) and no query params are read or applied",
    "Image upload support (up to 5 images per product) – NOT IMPLEMENTED: no multer middleware, no S3 client, no images field on the Product schema",
    "Redis caching for product detail pages – NOT IMPLEMENTED: no Redis client initialized anywhere; GET /:id hits MongoDB on every request",
    "Inventory stock tracking with low-stock alerts – NOT IMPLEMENTED: stockQuantity field exists on the schema but no threshold check, no alert trigger, and no stock-reduction endpoint"
  ],
  "non_functional_requirements": [
    "Security – HIGH: req.body passed directly into new Product() and findByIdAndUpdate() allows callers to overwrite any schema field including internal ones",
    "Security – HIGH: no ObjectId validation on :id path params; invalid IDs cause a Mongoose CastError that leaks a stack trace",
    "Security – MEDIUM: no authorization middleware; any client can create, update, or delete products without credentials",
    "Performance – CRITICAL: Product.find({{}}) with no .limit() loads the entire collection into memory on every GET / request",
    "Performance – no MongoDB index on name or category; search queries (once implemented) will perform full collection scans",
    "Scalability – Redis caching not implemented; product detail page load will scale linearly with MongoDB read latency",
    "Observability – no request logging middleware (morgan or equivalent); no structured application logs"
  ],
  "tech_stack_used": [
    "Runtime: Node.js 20",
    "Framework: Express 4.19",
    "ODM: Mongoose 8",
    "Database: MongoDB",
    "Config: dotenv",
    "Missing – Caching: ioredis not installed",
    "Missing – File upload: multer not installed",
    "Missing – Cloud storage: @aws-sdk/client-s3 not installed",
    "Missing – Validation: joi or zod not installed",
    "Testing: Jest + Supertest"
  ],
  "assumptions": [
    "AWS S3 bucket is provisioned and credentials are available via environment variables (from requirements) – not consumed by any code yet",
    "Redis instance is available at a REDIS_URL environment variable (from requirements) – not consumed by any code yet",
    "Admin authentication and authorization is enforced by an upstream API gateway – no auth code is expected in this service",
    "Product catalogue size may grow large enough to require pagination (inferred from pagination requirement)",
    "Low-stock threshold is a fixed business rule, not a per-product configurable value (inferred from absence of threshold field on schema)"
  ],
  "test_summary": "Two tests exist in tests/product.test.js: test_get_all_products (asserts HTTP 200 and array response) and test_create_product (asserts HTTP 200 on valid body). Search, pagination, image upload, Redis caching, stock tracking, and low-stock alerts have zero test coverage. No negative-path tests exist — invalid ObjectId, missing required fields, oversized image count, and insufficient stock are all untested. No test database setup or teardown is configured, meaning tests run against whatever MONGODB_URI is set in the environment.",
  "next_steps": [
    "CRITICAL – Add .limit() and .skip() to Product.find() immediately and expose page and limit as query params to prevent full-collection memory loads in production",
    "HIGH – Introduce a Joi or Zod validation schema and a validate middleware; whitelist allowed fields on create and update to eliminate mass-assignment risk",
    "HIGH – Implement search: read name and category query params and build a Mongoose filter with a text index on name and an exact match on category",
    "MEDIUM – Wire up ioredis client and add a cache-aside layer in getProductById: check Redis first, fall back to MongoDB, write result to Redis with a 5-minute TTL",
    "MEDIUM – Add multer middleware for image uploads, validate file type (JPEG/PNG only) and count (max 5), upload to S3 via @aws-sdk/client-s3, and store returned URLs in a Product.images array"
  ]
}}


--- EXAMPLE 3: Java + Spring Boot + MySQL (HR Leave Management Service) ---

Input Requirements:
{{
  "project": "HR Leave Management module for enterprise HRMS",
  "tech_stack": "Java 17, Spring Boot 3, Spring Security, MySQL, Hibernate/JPA",
  "requirements": [
    "Employees can apply for leave with type (sick, casual, earned), start date, end date, reason",
    "Managers can approve or reject leave applications",
    "Leave balance tracking per employee per year",
    "Email notifications on application, approval, and rejection",
    "Audit log of all leave status changes"
  ],
  "assumptions": ["SMTP configured via Spring Mail", "Employee and Manager entities exist", "JWT auth provided by upstream gateway"]
}}

Input Code Files:
- src/main/java/com/hr/Application.java
- src/main/java/com/hr/controller/LeaveController.java
- src/main/java/com/hr/model/Leave.java
- src/main/java/com/hr/repository/LeaveRepository.java
- src/main/java/com/hr/exception/GlobalExceptionHandler.java
- src/main/resources/application.properties

Input Tests:
- src/test/java/com/hr/LeaveControllerTest.java: testApplyLeave, testApproveLeave
- No tests for rejection, balance enforcement, email delivery, audit log, or authorization

Input Insights:
{{
  "security_issues": ["No @PreAuthorize on approve/reject – any caller can approve leaves", "employeeId is caller-supplied – an employee can apply on behalf of others"],
  "missing_implementations": ["Email notifications", "Audit log entity", "Balance deduction on approval", "Date overlap validation", "Manager authorization check"],
  "code_quality_issues": ["Business logic in controller – no service layer", ".get() on Optional without orElseThrow", "No @Transactional on approve/reject"]
}}

Output:
{{
  "project_title": "HR Leave Management Service",
  "overview": "Spring Boot microservice for managing employee leave applications within an enterprise HRMS. Employees can submit leave requests and managers can approve or reject them via REST endpoints. Email notifications and audit logging are specified in requirements but not implemented; leave balance deduction and manager authorization are also absent, making the service incomplete and insecure for production use.",
  "architecture": "Single Spring Boot application exposing a REST API via LeaveController. Requests are handled directly in the controller with no intermediate service layer — all business logic (status mutation, balance lookup) lives in controller methods. The Leave JPA entity is persisted to MySQL via LeaveRepository (Spring Data JPA). No Spring Security configuration is present despite the security requirement; authorization is expected from an upstream JWT gateway but no principal extraction occurs in the code. JavaMailSender is listed as a requirement dependency but is not autowired anywhere. No audit log entity or event listener exists.",
  "file_responsibilities": [
    "src/main/java/com/hr/Application.java – Spring Boot entry point with @SpringBootApplication; no custom beans or configuration",
    "src/main/java/com/hr/controller/LeaveController.java – All five endpoints (apply, approve, reject, getBalance, getById); contains business logic directly – no service layer; uses Optional.get() without orElseThrow on approve and reject",
    "src/main/java/com/hr/model/Leave.java – JPA entity with fields: id, employeeId, type, startDate, endDate, reason, status, createdAt; no audit log relationship; no constraint annotations on fields",
    "src/main/java/com/hr/repository/LeaveRepository.java – Extends JpaRepository; custom method countByEmployeeIdAndStatus used for balance calculation; no index hints or pagination support",
    "src/main/java/com/hr/exception/GlobalExceptionHandler.java – @RestControllerAdvice handling ResourceNotFoundException (404) and generic Exception (500); does not handle MethodArgumentNotValidException or custom business exceptions",
    "src/main/resources/application.properties – Datasource URL uses hardcoded credentials; spring.jpa.hibernate.ddl-auto=update; no mail server properties configured"
  ],
  "functional_requirements": [
    "Employees can apply for leave (type, start date, end date, reason) – PARTIAL: POST /leaves/apply persists a Leave entity, but type is not validated against the allowed enum (sick, casual, earned), date range is not validated, and employeeId is taken from the request body instead of the authenticated principal",
    "Managers can approve or reject leave applications – PARTIAL: PUT /leaves/approve/{{id}} and PUT /leaves/reject/{{id}} endpoints exist and update status, but no authorization check verifies the caller is a manager, and no check verifies the manager manages the applying employee",
    "Leave balance tracking per employee per year – PARTIAL: GET /leaves/balance/{{employeeId}} returns a count of APPROVED leaves, but does not differentiate by leave type (sick/casual/earned have separate quotas) and does not enforce balance limits before applying",
    "Email notifications on application, approval, and rejection – NOT IMPLEMENTED: JavaMailSender is not autowired anywhere; no email templates or notification trigger exist in the codebase",
    "Audit log of all leave status changes – NOT IMPLEMENTED: no LeaveAuditLog entity, no repository, no @EntityListeners or ApplicationEvent listener to capture status transitions"
  ],
  "non_functional_requirements": [
    "Security – CRITICAL: PUT /leaves/approve/{{id}} and /reject/{{id}} have no @PreAuthorize or role check; any authenticated or unauthenticated caller can approve any leave",
    "Security – CRITICAL: employeeId is accepted from the request body in POST /leaves/apply; an employee can submit leave on behalf of any other employee ID",
    "Security – HIGH: database credentials are hardcoded in application.properties instead of being externalized to environment variables or a secrets manager",
    "Correctness – HIGH: Optional.get() without orElseThrow in approve and reject will throw NoSuchElementException (HTTP 500) for non-existent leave IDs instead of a proper 404",
    "Correctness – HIGH: no @Transactional on approve/reject; if an exception occurs after the status is saved, the DB state is updated but the caller receives an error — no rollback occurs",
    "Observability – no SLF4J logging statements in controller or exception handler; failed approvals and rejections leave no trace",
    "Scalability – countByEmployeeIdAndStatus performs a table scan without a composite index on (employee_id, status); will degrade as leave history grows"
  ],
  "tech_stack_used": [
    "Runtime: Java 17",
    "Framework: Spring Boot 3.2",
    "Web: Spring MVC (spring-boot-starter-web)",
    "Persistence: Spring Data JPA + Hibernate",
    "Database: MySQL 8",
    "Build: Maven (pom.xml present)",
    "Missing – Validation: spring-boot-starter-validation not in pom.xml; @Valid annotations cannot be processed",
    "Missing – Mail: spring-boot-starter-mail not in pom.xml; JavaMailSender is unavailable",
    "Missing – Security enforcement: spring-boot-starter-security present in pom but no SecurityConfig class or @PreAuthorize usage found",
    "Testing: Spring Boot Test + JUnit 5 + MockMvc"
  ],
  "assumptions": [
    "JWT authentication is enforced by an upstream API gateway — the service does not validate tokens (from requirements); however, the service currently does not extract any principal from the SecurityContext either",
    "SMTP server is available and configured (from requirements) — Spring Mail dependency and properties are missing from the actual code",
    "Employee and Manager JPA entities exist in a separate module or service (from requirements) — only an employeeId Long field is used; no foreign key relationship to an Employee table is present",
    "Leave types (sick, casual, earned) have separate annual quotas — inferred from multi-type requirement; quota values are not defined anywhere in the code",
    "Leave balance resets annually — inferred from 'per year' language in requirements; no year filter is applied in the balance query"
  ],
  "test_summary": "Two tests exist in LeaveControllerTest.java: testApplyLeave (POST /leaves/apply with a valid body, asserts HTTP 200) and testApproveLeave (PUT /leaves/approve/1, asserts HTTP 200). No tests cover: leave rejection, invalid leave type, overlapping date ranges, balance enforcement, applying on behalf of another employee, approving as a non-manager, email notification triggering, audit log creation, or non-existent leave ID handling. The test class uses @SpringBootTest with a real application context but no test database configuration — tests will attempt to connect to the MySQL instance defined in application.properties.",
  "next_steps": [
    "CRITICAL – Add @PreAuthorize('hasRole(MANAGER)') to approve and reject endpoints and derive employeeId in apply from SecurityContextHolder.getContext().getAuthentication().getName() instead of the request body",
    "CRITICAL – Externalize database credentials from application.properties to environment variables (${{DB_USERNAME}}, ${{DB_PASSWORD}}) and add spring-boot-starter-validation to pom.xml",
    "HIGH – Extract all business logic into a LeaveService class annotated with @Transactional; replace Optional.get() with orElseThrow(ResourceNotFoundException) throughout",
    "HIGH – Add spring-boot-starter-mail to pom.xml, configure application.properties mail properties, and implement a NotificationService that sends emails on PENDING, APPROVED, and REJECTED status transitions",
    "MEDIUM – Create a LeaveAuditLog JPA entity and an ApplicationEvent listener that records leaveId, oldStatus, newStatus, changedBy, and changedAt on every status change"
  ]
}}

---

REQUIREMENTS:
{requirements_json}

GENERATED CODE:
{code_content}

UNIT TESTS:
{test_content}

INSIGHTS (optional, may be empty string):
{insights_json}
"""