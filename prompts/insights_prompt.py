def get_insights_prompt(requirements_json: str, code_content: str, test_content: str):
    return f"""
You are an Insights Generation Agent.

Your task:
Analyze the project's **requirements**, **generated code**, and **unit tests** together.
Produce structured insights.

Return JSON only:

{{
  "status": "completed",
  "insights_summary": "",
  "key_insights": [],
  "missing_implementations": [],
  "code_quality_issues": [],
  "security_issues": [],
  "scalability_problems": [],
  "refactoring_suggestions": [],
  "dependencies": [],
  "recommendations": []
}}

DECISION RULES:

1. **insights_summary** – One sentence describing overall system health.
2. **key_insights** – 3–5 important observations about code correctness, coverage, and design.
3. **missing_implementations** – Features in requirements but absent from code or tests.
4. **code_quality_issues** – Duplication, poor naming, magic numbers, missing error handling, no logging.
5. **security_issues** – Hardcoded secrets, no input validation, weak auth, SQL injection risk, no rate limiting.
6. **scalability_problems** – N+1 queries, no caching, blocking I/O, stateful bottlenecks, no pagination.
7. **refactoring_suggestions** – Structural improvements: patterns, abstractions, separation of concerns.
8. **dependencies** – External libraries/APIs used or missing from the codebase.
9. **recommendations** – 2–3 actionable next steps prioritized by severity.

STRICT RULES:

- Compare requirements against code and tests line by line.
- Flag every requirement that has no corresponding test.
- Flag every test that only covers the happy path.
- Do NOT ask questions.
- Do NOT assume missing details.
- Output ONLY valid JSON.

---

EXAMPLES:

--- EXAMPLE 1: Python + FastAPI + PostgreSQL (Auth Service) ---

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

Input Code:
from fastapi import FastAPI
from database import db

app = FastAPI()

@app.post("/register")
def register(email: str, password: str):
    existing = db.query("SELECT * FROM users WHERE email = '" + email + "'")
    if existing:
        return {{"error": "exists"}}
    db.execute("INSERT INTO users (email, password) VALUES ('" + email + "', '" + password + "')")
    return {{"message": "registered"}}

@app.post("/login")
def login(email: str, password: str):
    user = db.query("SELECT * FROM users WHERE email='" + email + "' AND password='" + password + "'")
    if user:
        token = "fake-jwt-" + email
        return {{"token": token}}
    return {{"error": "invalid"}}

@app.post("/refresh")
def refresh(token: str):
    return {{"token": "new-fake-jwt"}}

Input Tests:
def test_register():
    response = client.post("/register", json={{"email": "a@b.com", "password": "pass"}})
    assert response.status_code == 200

def test_login():
    response = client.post("/login", json={{"email": "a@b.com", "password": "pass"}})
    assert response.status_code == 200

Output:
{{
  "insights_summary": "Critical security flaws dominate — raw SQL with plaintext passwords and a hardcoded fake JWT make this auth service unsafe for any environment.",
  "key_insights": [
    "SQL queries are built by string concatenation, creating textbook SQL injection vulnerabilities in both /register and /login.",
    "Passwords are stored and compared in plaintext — any database breach exposes all credentials immediately.",
    "JWT tokens are hardcoded strings ('fake-jwt-' + email) with no signature, expiry, or secret key.",
    "Password reset via email OTP and role-based access control are entirely absent from both code and tests.",
    "Tests cover only happy-path HTTP 200 responses and make no assertions on token format, error codes, or duplicate email handling."
  ],
  "missing_implementations": [
    "Password reset flow: OTP generation, SMTP delivery, OTP verification endpoint.",
    "Token refresh logic: validate refresh token signature and expiry before issuing new access token.",
    "Role-based access control: roles column in users table, role assignment on registration, and a dependency/middleware to enforce roles on protected routes.",
    "Logout/token revocation: blacklist or refresh token invalidation.",
    "Input validation: email format check, minimum password length enforcement using Pydantic models."
  ],
  "code_quality_issues": [
    "Raw SQL string concatenation instead of parameterized queries or an ORM like SQLAlchemy.",
    "No Pydantic request models — email and password arrive as bare query params, bypassing FastAPI's validation layer.",
    "Generic error returns ({{'error': 'exists'}}) instead of HTTPException with proper status codes (409, 401).",
    "No logging — failed login attempts and registration errors produce no audit trail.",
    "Token generation logic mixed directly into route handlers; should be isolated in an auth service or utility module."
  ],
  "security_issues": [
    "SQL injection: all four queries use f-string/concatenation interpolation — an attacker can bypass auth with ' OR '1'='1.",
    "Plaintext password storage: passwords must be hashed with bcrypt or Argon2 before INSERT.",
    "Fake JWT: tokens carry no cryptographic signature — any string prefixed 'fake-jwt-' grants access.",
    "No rate limiting on /login — brute-force attacks are unrestricted.",
    "No HTTPS enforcement or CORS configuration visible in app setup."
  ],
  "scalability_problems": [
    "SELECT * FROM users on every login and register — no index on the email column, causing full table scans as user count grows.",
    "Synchronous db.query calls inside async FastAPI routes will block the event loop under load — use async SQLAlchemy or databases library.",
    "No connection pooling configured — each request may open a new DB connection."
  ],
  "refactoring_suggestions": [
    "Replace raw SQL with SQLAlchemy ORM models and use parameterized queries or the ORM's built-in escaping.",
    "Extract auth logic (token creation, password hashing, OTP generation) into a dedicated AuthService class to keep routes thin.",
    "Define Pydantic schemas (RegisterRequest, LoginRequest) and use FastAPI's dependency injection for input validation.",
    "Add a middleware layer for rate limiting (slowapi) and structured logging (structlog or loguru)."
  ],
  "dependencies": [
    "bcrypt or passlib[bcrypt] — missing, required for password hashing.",
    "python-jose or PyJWT — missing, required for real JWT signing and verification.",
    "SQLAlchemy with asyncpg — missing, required for async ORM and connection pooling.",
    "slowapi — missing, required for rate limiting on auth endpoints.",
    "pytest-asyncio — missing, required to properly test async FastAPI routes."
  ],
  "recommendations": [
    "Immediately replace plaintext password storage with bcrypt hashing and switch to parameterized SQLAlchemy queries — these two issues make the service exploitable right now.",
    "Implement real JWT signing using python-jose with a SECRET_KEY from environment variables, including access token expiry (15 min) and refresh token expiry (7 days).",
    "Write negative test cases: duplicate email registration (expect 409), wrong password login (expect 401), expired token refresh (expect 403), and invalid email format (expect 422)."
  ]
}}


--- EXAMPLE 2: Node.js + Express + MongoDB (E-commerce Product Service) ---

Input Requirements:
{{
  "project": "Product catalogue microservice for e-commerce platform",
  "tech_stack": "Node.js, Express, MongoDB, Mongoose, Redis",
  "requirements": [
    "CRUD endpoints for products (create, read, update, delete)",
    "Product search by name and category with pagination",
    "Image upload support (up to 5 images per product)",
    "Redis caching for product detail pages",
    "Inventory stock tracking with low-stock alerts"
  ],
  "assumptions": ["AWS S3 bucket configured", "Redis instance available", "Admin auth handled upstream"]
}}

Input Code:
const express = require('express');
const Product = require('./models/Product');
const app = express();
app.use(express.json());

app.get('/products', async (req, res) => {{
  const products = await Product.find({{}});
  res.json(products);
}});

app.get('/products/:id', async (req, res) => {{
  const product = await Product.findById(req.params.id);
  res.json(product);
}});

app.post('/products', async (req, res) => {{
  const product = new Product(req.body);
  await product.save();
  res.json(product);
}});

app.put('/products/:id', async (req, res) => {{
  const product = await Product.findByIdAndUpdate(req.params.id, req.body, {{new: true}});
  res.json(product);
}});

app.delete('/products/:id', async (req, res) => {{
  await Product.findByIdAndDelete(req.params.id);
  res.json({{message: 'deleted'}});
}});

Input Tests:
describe('Product API', () => {{
  it('should return all products', async () => {{
    const res = await request(app).get('/products');
    expect(res.statusCode).toBe(200);
  }});

  it('should create a product', async () => {{
    const res = await request(app).post('/products').send({{name: 'Widget', price: 9.99}});
    expect(res.statusCode).toBe(200);
  }});
}});

Output:
{{
  "insights_summary": "Basic CRUD scaffolding works but search, caching, image upload, and inventory tracking are all missing — the service covers roughly 20% of its requirements.",
  "key_insights": [
    "GET /products fetches the entire collection with Product.find({{}}) — no pagination, no filtering, no field projection — this will time out as inventory grows.",
    "Redis caching is required but zero Redis client code exists anywhere in the codebase.",
    "Image upload is mentioned in requirements but there is no multer middleware, no S3 integration, and no image URL field visible in the route handlers.",
    "Inventory and low-stock alert logic are completely absent — no stock field updates, no threshold checks, no notification trigger.",
    "No try/catch blocks exist in any route — a single Mongoose error or invalid ObjectId crashes the process with an unhandled promise rejection."
  ],
  "missing_implementations": [
    "Product search: query params for name (regex or text index) and category filter, combined with Mongoose .skip()/.limit() for pagination.",
    "Image upload: multer middleware for multipart/form-data, S3 upload via aws-sdk, storing returned URLs in the product document (max 5 images validation).",
    "Redis caching: cache GET /products/:id responses with a TTL (e.g. 300s), invalidate on PUT/DELETE for the same id.",
    "Inventory tracking: stock field on Product model, decrement on order events, alert mechanism (webhook, email, or queue message) when stock falls below threshold.",
    "Input validation: required fields (name, price, category, stock), price must be positive, stock must be a non-negative integer."
  ],
  "code_quality_issues": [
    "No error handling in any async route — all five handlers will propagate Mongoose exceptions as unhandled rejections.",
    "PUT /products/:id passes req.body directly to findByIdAndUpdate without a whitelist — callers can overwrite any field including internal fields like _id and __v.",
    "GET /products returns entire documents including all fields — should project only fields needed by the client.",
    "No HTTP status code discipline: successful POST should return 201, not 200; successful DELETE should return 204 with no body.",
    "No request logging middleware (morgan or winston) — impossible to audit API traffic or debug latency issues."
  ],
  "security_issues": [
    "req.body passed directly into Product constructor and findByIdAndUpdate allows mass-assignment of any field — use a DTO whitelist or Joi/Zod schema.",
    "No ObjectId validation on :id params — an invalid id string causes an ugly Mongoose CastError rather than a 400 response, and could expose stack traces.",
    "No file type or file size validation for the (unimplemented) image upload — required before S3 integration to prevent uploading executables.",
    "No authorization check on POST/PUT/DELETE routes — any unauthenticated client can modify the catalogue."
  ],
  "scalability_problems": [
    "Product.find({{}}) with no limit loads the entire collection into memory — must add .limit() with a maximum page size (e.g. 100).",
    "No MongoDB index on name or category fields — text search will perform a full collection scan.",
    "Redis cache not implemented — repeated GET /products/:id hits MongoDB on every request.",
    "No connection pool configuration for Mongoose — default pool size of 5 will bottleneck under concurrent load.",
    "Synchronous image processing in request handlers (when implemented) will block the event loop — use streams or offload to a background worker queue."
  ],
  "refactoring_suggestions": [
    "Introduce a repository layer (ProductRepository) to encapsulate all Mongoose queries, making routes thin and the data layer independently testable.",
    "Use express-async-errors or a global asyncHandler wrapper to centralize error handling instead of duplicating try/catch in every route.",
    "Separate image upload into its own Express router and service class (ImageService) to isolate S3 logic from product business logic.",
    "Create a CacheService abstraction over the Redis client so caching strategy can be changed (or mocked in tests) without touching route code."
  ],
  "dependencies": [
    "redis (ioredis) — missing, required for caching layer.",
    "multer — missing, required for multipart image upload handling.",
    "aws-sdk or @aws-sdk/client-s3 — missing, required for S3 image storage.",
    "joi or zod — missing, required for request body validation.",
    "express-async-errors — missing, required for clean async error propagation.",
    "mongoose-paginate-v2 — missing or equivalent pagination plugin needed."
  ],
  "recommendations": [
    "Add try/catch with a centralized error handler as the first fix — currently any DB error crashes all in-flight requests silently.",
    "Implement pagination on GET /products immediately using .skip()/.limit() and expose page and limit as query params — this is a correctness issue in production.",
    "Wire up the Redis client and add caching to GET /products/:id before deploying — MongoDB will be overwhelmed by product detail page traffic without it."
  ]
}}


--- EXAMPLE 3: Java + Spring Boot + MySQL (HR Leave Management Service) ---

Input Requirements:
{{
  "project": "HR Leave Management module for enterprise HRMS",
  "tech_stack": "Java 17, Spring Boot 3, Spring Security, MySQL, Hibernate/JPA",
  "requirements": [
    "Employees can apply for leave with type (sick, casual, earned), start date, end date, and reason",
    "Managers can approve or reject leave applications",
    "Leave balance tracking per employee per year",
    "Email notifications on application, approval, and rejection",
    "Audit log of all leave status changes"
  ],
  "assumptions": ["SMTP configured via Spring Mail", "Employee and Manager entities exist", "JWT auth provided by upstream gateway"]
}}

Input Code:
@RestController
@RequestMapping("/leaves")
public class LeaveController {{

    @Autowired
    LeaveRepository leaveRepo;

    @PostMapping("/apply")
    public Leave applyLeave(@RequestBody Leave leave) {{
        leave.setStatus("PENDING");
        return leaveRepo.save(leave);
    }}

    @PutMapping("/approve/{{id}}")
    public Leave approveLeave(@PathVariable Long id) {{
        Leave leave = leaveRepo.findById(id).get();
        leave.setStatus("APPROVED");
        return leaveRepo.save(leave);
    }}

    @PutMapping("/reject/{{id}}")
    public Leave rejectLeave(@PathVariable Long id) {{
        Leave leave = leaveRepo.findById(id).get();
        leave.setStatus("REJECTED");
        return leaveRepo.save(leave);
    }}

    @GetMapping("/balance/{{employeeId}}")
    public int getBalance(@PathVariable Long employeeId) {{
        return leaveRepo.countByEmployeeIdAndStatus(employeeId, "APPROVED");
    }}
}}

Input Tests:
@SpringBootTest
class LeaveControllerTest {{
    @Test
    void testApplyLeave() {{
        Leave leave = new Leave();
        leave.setEmployeeId(1L);
        leave.setType("SICK");
        ResponseEntity<Leave> response = restTemplate.postForEntity("/leaves/apply", leave, Leave.class);
        assertEquals(200, response.getStatusCodeValue());
    }}

    @Test
    void testApproveLeave() {{
        ResponseEntity<Leave> response = restTemplate.exchange("/leaves/approve/1", HttpMethod.PUT, null, Leave.class);
        assertEquals(200, response.getStatusCodeValue());
    }}
}}

Output:
{{
  "insights_summary": "The leave service has basic CRUD but is missing email notifications, audit logging, balance deduction logic, and any security enforcement — manager approval is callable by anyone.",
  "key_insights": [
    "leaveRepo.findById(id).get() is used in both approve and reject without .orElseThrow() — if the leave ID does not exist, it throws a NoSuchElementException that becomes an unhandled 500.",
    "Leave balance is calculated by counting APPROVED leaves — this ignores leave type (sick vs casual vs earned have separate quotas) and does not deduct balance on approval or enforce limits before apply.",
    "Email notifications (on apply, approve, reject) are required but JavaMailSender is not injected anywhere in the controller or a service layer.",
    "Audit log of status changes is entirely absent — no entity, no repository, no event listener.",
    "No Spring Security configuration guards the /approve and /reject endpoints — any authenticated or unauthenticated user can approve leaves."
  ],
  "missing_implementations": [
    "Leave type validation on apply: enforce that leave.getType() is one of SICK, CASUAL, EARNED; reject with 400 otherwise.",
    "Balance enforcement: before saving a PENDING leave, check remaining quota for that leave type and year; reject with 422 if insufficient balance.",
    "Balance deduction on approval: when status moves to APPROVED, decrement the employee's balance for that leave type.",
    "Email notifications: send email via JavaMailSender to the employee on PENDING, and to both employee and manager on APPROVED/REJECTED.",
    "Audit log entity (LeaveAuditLog) capturing: leaveId, changedBy, oldStatus, newStatus, changedAt — populated via a @EntityListeners or Spring ApplicationEvent.",
    "Manager authorization check: verify the principal making PUT /approve or /reject actually manages the employee who applied.",
    "Date validation: endDate must not be before startDate; leave duration must not overlap with existing approved leaves."
  ],
  "code_quality_issues": [
    "Field injection via @Autowired on leaveRepo — use constructor injection for testability and to make dependencies explicit.",
    "Business logic (status mutation, balance check) lives directly in the controller — extract to a LeaveService class following single responsibility principle.",
    ".get() on Optional without .orElseThrow() produces an unhelpful stack trace; replace with leaveRepo.findById(id).orElseThrow(() -> new LeaveNotFoundException(id)).",
    "Leave entity returned directly from controller exposes all database columns including internal fields — use a LeaveResponseDTO to control API shape.",
    "No @Transactional annotation on approve/reject — if the email send fails after save(), the DB is updated but the notification is lost with no rollback."
  ],
  "security_issues": [
    "No @PreAuthorize or Spring Security method-level security on /approve and /reject — any caller can approve any leave application.",
    "Employee can set leave.setStatus() directly via @RequestBody — status field should be server-controlled and stripped from the incoming payload.",
    "No validation annotations (@NotNull, @NotBlank, @Future) on the Leave entity — null startDate or negative duration will persist to the database.",
    "employeeId in the apply request is caller-supplied — an employee could apply leave on behalf of another employee; derive employeeId from the JWT principal instead."
  ],
  "scalability_problems": [
    "countByEmployeeIdAndStatus scans all leave records for that employee — add a composite index on (employee_id, status, year) to keep balance queries fast.",
    "No pagination on any list endpoint (e.g. GET /leaves by manager or team) — fetching all leaves for a department in a single query will degrade as history grows.",
    "Sending email synchronously inside the approve/reject transaction blocks the HTTP thread for the duration of the SMTP round-trip — offload to @Async or a message queue (RabbitMQ/Kafka).",
    "Balance calculation re-queries the database on every request — cache per-employee balances in Redis with invalidation on approval/rejection."
  ],
  "refactoring_suggestions": [
    "Introduce a LeaveService with applyLeave(), approveLeave(), rejectLeave() methods annotated with @Transactional — the controller becomes a thin HTTP adapter.",
    "Create a LeaveBalanceService that owns quota rules per leave type; this isolates policy changes (e.g. new leave types) from persistence logic.",
    "Use Spring ApplicationEvents (LeaveAppliedEvent, LeaveApprovedEvent, LeaveRejectedEvent) so the NotificationService and AuditService react to state changes without coupling to LeaveService.",
    "Replace entity return types with DTOs (LeaveRequestDTO, LeaveResponseDTO) using MapStruct for mapping — keeps API contract stable as the entity evolves."
  ],
  "dependencies": [
    "spring-boot-starter-mail — present in requirements but not imported; required for JavaMailSender.",
    "spring-boot-starter-validation — missing; required for @Valid and Bean Validation annotations on request bodies.",
    "spring-boot-starter-security — missing or not configured; required to enforce MANAGER role on approve/reject endpoints.",
    "spring-boot-starter-data-redis — missing; required if balance caching is added.",
    "mapstruct — missing; recommended for DTO mapping to replace manual converters."
  ],
  "recommendations": [
    "Add @PreAuthorize('hasRole(MANAGER)') to approve and reject endpoints and derive employeeId from the JWT SecurityContext instead of the request body — these are exploitable gaps in the current state.",
    "Extract all business logic into LeaveService with @Transactional and wire in JavaMailSender — this also unlocks the ability to roll back DB changes if email delivery fails.",
    "Add @Valid with constraint annotations (@NotNull on employeeId, type, startDate, endDate; custom @ValidDateRange) on the apply endpoint and write negative test cases for each constraint."
  ]
}}

---

REQUIREMENTS:
{requirements_json}

GENERATED CODE:
{code_content}

UNIT TESTS:
{test_content}
"""