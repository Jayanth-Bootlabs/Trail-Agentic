def get_code_prompt(requirements_json: str):
    return f"""
You are a Code Generation Agent.

Your task:
Generate complete, runnable project source code from the given **requirements**.

Return JSON only:

{{
  "project_title": "",
  "tech_stack": [],
  "file_structure": [],
  "source_code": {{
    "file_path": "code here"
  }}
}}

DECISION RULES:

1. **project_title** – Short, meaningful name derived from the requirements.
2. **tech_stack** – All languages, frameworks, databases, and key libraries used.
3. **file_structure** – Complete list of every file path in the project.
4. **source_code** – Dictionary of file_path → full working code. Every file in file_structure must have a corresponding entry here.

STRICT RULES:

- Produce a realistic multi-file project structure matching the tech stack.
- Every file must contain complete, working code — no placeholders, no TODO comments, no stub functions.
- Follow language-specific best practices: PEP8 for Python, Airbnb style for JS, Google style for Java.
- Use environment variables for secrets (DB URLs, API keys) — never hardcode credentials.
- Include a requirements.txt / package.json / pom.xml / go.mod with all dependencies pinned.
- Include a README.md with setup and run instructions.
- Do NOT invent files that are not needed by the requirements.
- Do NOT output markdown formatting or code fences.
- Output ONLY valid JSON.

---

EXAMPLES:

--- EXAMPLE 1: Python + FastAPI + PostgreSQL (URL Shortener API) ---

Input:
{{
  "project": "URL shortener service",
  "tech_stack": "Python, FastAPI, PostgreSQL",
  "requirements": [
    "POST /shorten to accept a long URL and return a short code",
    "GET /{{code}} to redirect to the original URL",
    "Track visit count per short URL",
    "Return 404 if short code does not exist"
  ],
  "assumptions": ["PostgreSQL running locally", "No auth required"]
}}

Output:
{{
  "project_title": "URL Shortener API",
  "tech_stack": ["Python 3.11", "FastAPI", "PostgreSQL", "SQLAlchemy", "Alembic", "Uvicorn"],
  "file_structure": [
    "app/__init__.py",
    "app/main.py",
    "app/database.py",
    "app/models.py",
    "app/schemas.py",
    "app/crud.py",
    "app/routers/urls.py",
    "alembic/env.py",
    "alembic/versions/.gitkeep",
    "alembic.ini",
    ".env.example",
    "requirements.txt",
    "README.md"
  ],
  "source_code": {{
    "app/__init__.py": "",

    "app/main.py": "from fastapi import FastAPI\nfrom fastapi.responses import RedirectResponse\nfrom app.database import engine, Base\nfrom app.routers import urls\n\nBase.metadata.create_all(bind=engine)\n\napp = FastAPI(title=\"URL Shortener\")\napp.include_router(urls.router)\n\n@app.get(\"/health\")\ndef health():\n    return {{\"status\": \"ok\"}}",

    "app/database.py": "import os\nfrom sqlalchemy import create_engine\nfrom sqlalchemy.ext.declarative import declarative_base\nfrom sqlalchemy.orm import sessionmaker\nfrom dotenv import load_dotenv\n\nload_dotenv()\n\nDATABASE_URL = os.getenv(\"DATABASE_URL\", \"postgresql://user:password@localhost/urlshortener\")\n\nengine = create_engine(DATABASE_URL)\nSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)\nBase = declarative_base()\n\ndef get_db():\n    db = SessionLocal()\n    try:\n        yield db\n    finally:\n        db.close()",

    "app/models.py": "from sqlalchemy import Column, Integer, String, DateTime, func\nfrom app.database import Base\n\nclass ShortURL(Base):\n    __tablename__ = \"short_urls\"\n\n    id = Column(Integer, primary_key=True, index=True)\n    original_url = Column(String, nullable=False)\n    short_code = Column(String(10), unique=True, index=True, nullable=False)\n    visit_count = Column(Integer, default=0, nullable=False)\n    created_at = Column(DateTime(timezone=True), server_default=func.now())",

    "app/schemas.py": "from pydantic import BaseModel, HttpUrl\nfrom datetime import datetime\n\nclass ShortenRequest(BaseModel):\n    url: HttpUrl\n\nclass ShortenResponse(BaseModel):\n    short_code: str\n    short_url: str\n    original_url: str\n\n    class Config:\n        from_attributes = True\n\nclass URLStatsResponse(BaseModel):\n    short_code: str\n    original_url: str\n    visit_count: int\n    created_at: datetime\n\n    class Config:\n        from_attributes = True",

    "app/crud.py": "import random\nimport string\nfrom sqlalchemy.orm import Session\nfrom app import models, schemas\n\ndef generate_short_code(length: int = 6) -> str:\n    chars = string.ascii_letters + string.digits\n    return \"\".join(random.choices(chars, k=length))\n\ndef get_url_by_code(db: Session, short_code: str) -> models.ShortURL | None:\n    return db.query(models.ShortURL).filter(models.ShortURL.short_code == short_code).first()\n\ndef create_short_url(db: Session, request: schemas.ShortenRequest) -> models.ShortURL:\n    short_code = generate_short_code()\n    while get_url_by_code(db, short_code):\n        short_code = generate_short_code()\n    db_url = models.ShortURL(original_url=str(request.url), short_code=short_code)\n    db.add(db_url)\n    db.commit()\n    db.refresh(db_url)\n    return db_url\n\ndef increment_visit_count(db: Session, url: models.ShortURL) -> models.ShortURL:\n    url.visit_count += 1\n    db.commit()\n    db.refresh(url)\n    return url",

    "app/routers/urls.py": "from fastapi import APIRouter, Depends, HTTPException\nfrom fastapi.responses import RedirectResponse\nfrom sqlalchemy.orm import Session\nfrom app import crud, schemas\nfrom app.database import get_db\n\nrouter = APIRouter()\n\n@router.post(\"/shorten\", response_model=schemas.ShortenResponse, status_code=201)\ndef shorten_url(request: schemas.ShortenRequest, db: Session = Depends(get_db)):\n    db_url = crud.create_short_url(db, request)\n    return schemas.ShortenResponse(\n        short_code=db_url.short_code,\n        short_url=f\"http://localhost:8000/{{db_url.short_code}}\",\n        original_url=db_url.original_url\n    )\n\n@router.get(\"/{{short_code}}/stats\", response_model=schemas.URLStatsResponse)\ndef get_stats(short_code: str, db: Session = Depends(get_db)):\n    db_url = crud.get_url_by_code(db, short_code)\n    if not db_url:\n        raise HTTPException(status_code=404, detail=f\"Short code '{{short_code}}' not found\")\n    return db_url\n\n@router.get(\"/{{short_code}}\")\ndef redirect_to_url(short_code: str, db: Session = Depends(get_db)):\n    db_url = crud.get_url_by_code(db, short_code)\n    if not db_url:\n        raise HTTPException(status_code=404, detail=f\"Short code '{{short_code}}' not found\")\n    crud.increment_visit_count(db, db_url)\n    return RedirectResponse(url=db_url.original_url, status_code=302)",

    ".env.example": "DATABASE_URL=postgresql://user:password@localhost/urlshortener",

    "requirements.txt": "fastapi==0.111.0\nuvicorn[standard]==0.29.0\nsqlalchemy==2.0.30\nalembic==1.13.1\npsycopg2-binary==2.9.9\npython-dotenv==1.0.1\npydantic[email]==2.7.1",

    "README.md": "# URL Shortener API\n\n## Setup\n```bash\npip install -r requirements.txt\ncp .env.example .env\n# Edit .env with your PostgreSQL credentials\nalembic upgrade head\nuvicorn app.main:app --reload\n```\n\n## Endpoints\n- POST /shorten — body: {{\"url\": \"https://example.com\"}} — returns short_code\n- GET /{{code}} — redirects to original URL\n- GET /{{code}}/stats — returns visit count and metadata\n- GET /health — health check"
  }}
}}


--- EXAMPLE 2: Node.js + Express + MongoDB (Task Management API) ---

Input:
{{
  "project": "Task management REST API",
  "tech_stack": "Node.js, Express, MongoDB, Mongoose",
  "requirements": [
    "CRUD for tasks: title, description, status (todo/in-progress/done), due date",
    "Filter tasks by status",
    "Mark task as complete",
    "Input validation on create and update",
    "Centralized error handling"
  ],
  "assumptions": ["MongoDB Atlas connection string provided via env", "No auth required"]
}}

Output:
{{
  "project_title": "Task Manager API",
  "tech_stack": ["Node.js 20", "Express 4", "MongoDB", "Mongoose 8", "Joi"],
  "file_structure": [
    "src/app.js",
    "src/server.js",
    "src/config/db.js",
    "src/models/Task.js",
    "src/schemas/taskSchema.js",
    "src/controllers/taskController.js",
    "src/routes/taskRoutes.js",
    "src/middleware/errorHandler.js",
    "src/middleware/validate.js",
    ".env.example",
    "package.json",
    "README.md"
  ],
  "source_code": {{
    "src/server.js": "const app = require('./app');\nconst connectDB = require('./config/db');\n\nconst PORT = process.env.PORT || 3000;\n\nconnectDB().then(() => {{\n  app.listen(PORT, () => console.log(`Server running on port ${{PORT}}`));\n}}).catch(err => {{\n  console.error('DB connection failed:', err);\n  process.exit(1);\n}});",

    "src/app.js": "const express = require('express');\nrequire('dotenv').config();\nconst taskRoutes = require('./routes/taskRoutes');\nconst errorHandler = require('./middleware/errorHandler');\n\nconst app = express();\napp.use(express.json());\n\napp.get('/health', (req, res) => res.json({{ status: 'ok' }}));\napp.use('/api/tasks', taskRoutes);\napp.use(errorHandler);\n\nmodule.exports = app;",

    "src/config/db.js": "const mongoose = require('mongoose');\n\nasync function connectDB() {{\n  const uri = process.env.MONGODB_URI;\n  if (!uri) throw new Error('MONGODB_URI is not set in environment');\n  await mongoose.connect(uri);\n  console.log('MongoDB connected');\n}}\n\nmodule.exports = connectDB;",

    "src/models/Task.js": "const mongoose = require('mongoose');\n\nconst taskSchema = new mongoose.Schema({{\n  title: {{ type: String, required: true, trim: true, maxlength: 200 }},\n  description: {{ type: String, trim: true, maxlength: 2000 }},\n  status: {{ type: String, enum: ['todo', 'in-progress', 'done'], default: 'todo' }},\n  dueDate: {{ type: Date }},\n  completedAt: {{ type: Date }}\n}}, {{ timestamps: true }});\n\nmodule.exports = mongoose.model('Task', taskSchema);",

    "src/schemas/taskSchema.js": "const Joi = require('joi');\n\nconst createTaskSchema = Joi.object({{\n  title: Joi.string().trim().max(200).required(),\n  description: Joi.string().trim().max(2000).optional(),\n  status: Joi.string().valid('todo', 'in-progress', 'done').optional(),\n  dueDate: Joi.date().iso().optional()\n}});\n\nconst updateTaskSchema = Joi.object({{\n  title: Joi.string().trim().max(200).optional(),\n  description: Joi.string().trim().max(2000).optional(),\n  status: Joi.string().valid('todo', 'in-progress', 'done').optional(),\n  dueDate: Joi.date().iso().optional()\n}}).min(1);\n\nmodule.exports = {{ createTaskSchema, updateTaskSchema }};",

    "src/middleware/validate.js": "function validate(schema) {{\n  return (req, res, next) => {{\n    const {{ error }} = schema.validate(req.body, {{ abortEarly: false }});\n    if (error) {{\n      const messages = error.details.map(d => d.message);\n      return res.status(400).json({{ success: false, errors: messages }});\n    }}\n    next();\n  }};\n}}\n\nmodule.exports = validate;",

    "src/middleware/errorHandler.js": "function errorHandler(err, req, res, next) {{\n  console.error(err.stack);\n  const status = err.status || 500;\n  res.status(status).json({{\n    success: false,\n    message: err.message || 'Internal server error'\n  }});\n}}\n\nmodule.exports = errorHandler;",

    "src/controllers/taskController.js": "const Task = require('../models/Task');\n\nexports.getAllTasks = async (req, res, next) => {{\n  try {{\n    const filter = {{}};\n    if (req.query.status) filter.status = req.query.status;\n    const tasks = await Task.find(filter).sort({{ createdAt: -1 }});\n    res.json({{ success: true, count: tasks.length, data: tasks }});\n  }} catch (err) {{ next(err); }}\n}};\n\nexports.getTaskById = async (req, res, next) => {{\n  try {{\n    const task = await Task.findById(req.params.id);\n    if (!task) return res.status(404).json({{ success: false, message: 'Task not found' }});\n    res.json({{ success: true, data: task }});\n  }} catch (err) {{ next(err); }}\n}};\n\nexports.createTask = async (req, res, next) => {{\n  try {{\n    const task = await Task.create(req.body);\n    res.status(201).json({{ success: true, data: task }});\n  }} catch (err) {{ next(err); }}\n}};\n\nexports.updateTask = async (req, res, next) => {{\n  try {{\n    const task = await Task.findByIdAndUpdate(req.params.id, req.body, {{ new: true, runValidators: true }});\n    if (!task) return res.status(404).json({{ success: false, message: 'Task not found' }});\n    res.json({{ success: true, data: task }});\n  }} catch (err) {{ next(err); }}\n}};\n\nexports.completeTask = async (req, res, next) => {{\n  try {{\n    const task = await Task.findByIdAndUpdate(\n      req.params.id,\n      {{ status: 'done', completedAt: new Date() }},\n      {{ new: true }}\n    );\n    if (!task) return res.status(404).json({{ success: false, message: 'Task not found' }});\n    res.json({{ success: true, data: task }});\n  }} catch (err) {{ next(err); }}\n}};\n\nexports.deleteTask = async (req, res, next) => {{\n  try {{\n    const task = await Task.findByIdAndDelete(req.params.id);\n    if (!task) return res.status(404).json({{ success: false, message: 'Task not found' }});\n    res.status(204).send();\n  }} catch (err) {{ next(err); }}\n}};",

    "src/routes/taskRoutes.js": "const express = require('express');\nconst router = express.Router();\nconst taskController = require('../controllers/taskController');\nconst validate = require('../middleware/validate');\nconst {{ createTaskSchema, updateTaskSchema }} = require('../schemas/taskSchema');\n\nrouter.get('/', taskController.getAllTasks);\nrouter.get('/:id', taskController.getTaskById);\nrouter.post('/', validate(createTaskSchema), taskController.createTask);\nrouter.put('/:id', validate(updateTaskSchema), taskController.updateTask);\nrouter.patch('/:id/complete', taskController.completeTask);\nrouter.delete('/:id', taskController.deleteTask);\n\nmodule.exports = router;",

    ".env.example": "MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/taskdb\nPORT=3000",

    "package.json": "{{\n  \"name\": \"task-manager-api\",\n  \"version\": \"1.0.0\",\n  \"main\": \"src/server.js\",\n  \"scripts\": {{\n    \"start\": \"node src/server.js\",\n    \"dev\": \"nodemon src/server.js\"\n  }},\n  \"dependencies\": {{\n    \"dotenv\": \"^16.4.5\",\n    \"express\": \"^4.19.2\",\n    \"joi\": \"^17.13.1\",\n    \"mongoose\": \"^8.4.0\"\n  }},\n  \"devDependencies\": {{\n    \"nodemon\": \"^3.1.3\"\n  }}\n}}",

    "README.md": "# Task Manager API\n\n## Setup\n```bash\nnpm install\ncp .env.example .env\n# Add your MongoDB URI to .env\nnpm run dev\n```\n\n## Endpoints\n- GET /api/tasks?status=todo — list tasks, filter by status\n- GET /api/tasks/:id — get task by ID\n- POST /api/tasks — create task (body: title, description, dueDate, status)\n- PUT /api/tasks/:id — update task fields\n- PATCH /api/tasks/:id/complete — mark task as done\n- DELETE /api/tasks/:id — delete task"
  }}
}}


--- EXAMPLE 3: Java + Spring Boot + MySQL (Product Inventory API) ---

Input:
{{
  "project": "Product inventory management system",
  "tech_stack": "Java 17, Spring Boot 3, MySQL, Spring Data JPA",
  "requirements": [
    "CRUD for products: name, SKU, price, stock quantity, category",
    "Search products by name or category",
    "Reduce stock on order (prevent negative stock)",
    "Global exception handling with proper HTTP status codes",
    "DTO pattern to avoid exposing JPA entities directly"
  ],
  "assumptions": ["MySQL running locally", "No auth required for now"]
}}

Output:
{{
  "project_title": "Product Inventory API",
  "tech_stack": ["Java 17", "Spring Boot 3.2", "MySQL 8", "Spring Data JPA", "Hibernate", "Maven"],
  "file_structure": [
    "src/main/java/com/inventory/Application.java",
    "src/main/java/com/inventory/controller/ProductController.java",
    "src/main/java/com/inventory/service/ProductService.java",
    "src/main/java/com/inventory/repository/ProductRepository.java",
    "src/main/java/com/inventory/model/Product.java",
    "src/main/java/com/inventory/dto/ProductRequestDTO.java",
    "src/main/java/com/inventory/dto/ProductResponseDTO.java",
    "src/main/java/com/inventory/dto/StockReduceRequest.java",
    "src/main/java/com/inventory/exception/GlobalExceptionHandler.java",
    "src/main/java/com/inventory/exception/ResourceNotFoundException.java",
    "src/main/java/com/inventory/exception/InsufficientStockException.java",
    "src/main/resources/application.properties",
    "pom.xml",
    "README.md"
  ],
  "source_code": {{
    "src/main/java/com/inventory/Application.java": "package com.inventory;\n\nimport org.springframework.boot.SpringApplication;\nimport org.springframework.boot.autoconfigure.SpringBootApplication;\n\n@SpringBootApplication\npublic class Application {{\n    public static void main(String[] args) {{\n        SpringApplication.run(Application.class, args);\n    }}\n}}",

    "src/main/java/com/inventory/model/Product.java": "package com.inventory.model;\n\nimport jakarta.persistence.*;\nimport java.math.BigDecimal;\nimport java.time.LocalDateTime;\n\n@Entity\n@Table(name = \"products\")\npublic class Product {{\n    @Id\n    @GeneratedValue(strategy = GenerationType.IDENTITY)\n    private Long id;\n\n    @Column(nullable = false)\n    private String name;\n\n    @Column(unique = true, nullable = false)\n    private String sku;\n\n    @Column(nullable = false)\n    private BigDecimal price;\n\n    @Column(nullable = false)\n    private Integer stockQuantity;\n\n    private String category;\n\n    @Column(updatable = false)\n    private LocalDateTime createdAt;\n\n    @PrePersist\n    protected void onCreate() {{ this.createdAt = LocalDateTime.now(); }}\n\n    public Long getId() {{ return id; }}\n    public String getName() {{ return name; }}\n    public void setName(String name) {{ this.name = name; }}\n    public String getSku() {{ return sku; }}\n    public void setSku(String sku) {{ this.sku = sku; }}\n    public BigDecimal getPrice() {{ return price; }}\n    public void setPrice(BigDecimal price) {{ this.price = price; }}\n    public Integer getStockQuantity() {{ return stockQuantity; }}\n    public void setStockQuantity(Integer stockQuantity) {{ this.stockQuantity = stockQuantity; }}\n    public String getCategory() {{ return category; }}\n    public void setCategory(String category) {{ this.category = category; }}\n    public LocalDateTime getCreatedAt() {{ return createdAt; }}\n}}",

    "src/main/java/com/inventory/dto/ProductRequestDTO.java": "package com.inventory.dto;\n\nimport jakarta.validation.constraints.*;\nimport java.math.BigDecimal;\n\npublic class ProductRequestDTO {{\n    @NotBlank(message = \"Name is required\")\n    private String name;\n\n    @NotBlank(message = \"SKU is required\")\n    private String sku;\n\n    @NotNull(message = \"Price is required\")\n    @DecimalMin(value = \"0.01\", message = \"Price must be greater than 0\")\n    private BigDecimal price;\n\n    @NotNull(message = \"Stock quantity is required\")\n    @Min(value = 0, message = \"Stock quantity cannot be negative\")\n    private Integer stockQuantity;\n\n    private String category;\n\n    public String getName() {{ return name; }}\n    public void setName(String name) {{ this.name = name; }}\n    public String getSku() {{ return sku; }}\n    public void setSku(String sku) {{ this.sku = sku; }}\n    public BigDecimal getPrice() {{ return price; }}\n    public void setPrice(BigDecimal price) {{ this.price = price; }}\n    public Integer getStockQuantity() {{ return stockQuantity; }}\n    public void setStockQuantity(Integer qty) {{ this.stockQuantity = qty; }}\n    public String getCategory() {{ return category; }}\n    public void setCategory(String category) {{ this.category = category; }}\n}}",

    "src/main/java/com/inventory/dto/ProductResponseDTO.java": "package com.inventory.dto;\n\nimport java.math.BigDecimal;\nimport java.time.LocalDateTime;\n\npublic class ProductResponseDTO {{\n    private Long id;\n    private String name;\n    private String sku;\n    private BigDecimal price;\n    private Integer stockQuantity;\n    private String category;\n    private LocalDateTime createdAt;\n\n    public ProductResponseDTO(Long id, String name, String sku, BigDecimal price,\n                              Integer stockQuantity, String category, LocalDateTime createdAt) {{\n        this.id = id; this.name = name; this.sku = sku; this.price = price;\n        this.stockQuantity = stockQuantity; this.category = category; this.createdAt = createdAt;\n    }}\n\n    public Long getId() {{ return id; }}\n    public String getName() {{ return name; }}\n    public String getSku() {{ return sku; }}\n    public BigDecimal getPrice() {{ return price; }}\n    public Integer getStockQuantity() {{ return stockQuantity; }}\n    public String getCategory() {{ return category; }}\n    public LocalDateTime getCreatedAt() {{ return createdAt; }}\n}}",

    "src/main/java/com/inventory/dto/StockReduceRequest.java": "package com.inventory.dto;\n\nimport jakarta.validation.constraints.Min;\nimport jakarta.validation.constraints.NotNull;\n\npublic class StockReduceRequest {{\n    @NotNull(message = \"Quantity is required\")\n    @Min(value = 1, message = \"Quantity must be at least 1\")\n    private Integer quantity;\n\n    public Integer getQuantity() {{ return quantity; }}\n    public void setQuantity(Integer quantity) {{ this.quantity = quantity; }}\n}}",

    "src/main/java/com/inventory/repository/ProductRepository.java": "package com.inventory.repository;\n\nimport com.inventory.model.Product;\nimport org.springframework.data.jpa.repository.JpaRepository;\nimport org.springframework.data.jpa.repository.Query;\nimport org.springframework.data.repository.query.Param;\nimport java.util.List;\nimport java.util.Optional;\n\npublic interface ProductRepository extends JpaRepository<Product, Long> {{\n    Optional<Product> findBySku(String sku);\n\n    @Query(\"SELECT p FROM Product p WHERE \" +\n           \"(:name IS NULL OR LOWER(p.name) LIKE LOWER(CONCAT('%', :name, '%'))) AND \" +\n           \"(:category IS NULL OR LOWER(p.category) = LOWER(:category))\")\n    List<Product> searchProducts(@Param(\"name\") String name, @Param(\"category\") String category);\n}}",

    "src/main/java/com/inventory/exception/ResourceNotFoundException.java": "package com.inventory.exception;\n\npublic class ResourceNotFoundException extends RuntimeException {{\n    public ResourceNotFoundException(String message) {{ super(message); }}\n}}",

    "src/main/java/com/inventory/exception/InsufficientStockException.java": "package com.inventory.exception;\n\npublic class InsufficientStockException extends RuntimeException {{\n    public InsufficientStockException(String message) {{ super(message); }}\n}}",

    "src/main/java/com/inventory/exception/GlobalExceptionHandler.java": "package com.inventory.exception;\n\nimport org.springframework.http.HttpStatus;\nimport org.springframework.http.ResponseEntity;\nimport org.springframework.web.bind.MethodArgumentNotValidException;\nimport org.springframework.web.bind.annotation.ExceptionHandler;\nimport org.springframework.web.bind.annotation.RestControllerAdvice;\nimport java.util.HashMap;\nimport java.util.Map;\n\n@RestControllerAdvice\npublic class GlobalExceptionHandler {{\n\n    @ExceptionHandler(ResourceNotFoundException.class)\n    public ResponseEntity<Map<String, String>> handleNotFound(ResourceNotFoundException ex) {{\n        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of(\"error\", ex.getMessage()));\n    }}\n\n    @ExceptionHandler(InsufficientStockException.class)\n    public ResponseEntity<Map<String, String>> handleStock(InsufficientStockException ex) {{\n        return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY).body(Map.of(\"error\", ex.getMessage()));\n    }}\n\n    @ExceptionHandler(MethodArgumentNotValidException.class)\n    public ResponseEntity<Map<String, Object>> handleValidation(MethodArgumentNotValidException ex) {{\n        Map<String, String> fieldErrors = new HashMap<>();\n        ex.getBindingResult().getFieldErrors().forEach(e -> fieldErrors.put(e.getField(), e.getDefaultMessage()));\n        return ResponseEntity.badRequest().body(Map.of(\"errors\", fieldErrors));\n    }}\n\n    @ExceptionHandler(Exception.class)\n    public ResponseEntity<Map<String, String>> handleGeneral(Exception ex) {{\n        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(\"error\", \"Unexpected error occurred\"));\n    }}\n}}",

    "src/main/java/com/inventory/service/ProductService.java": "package com.inventory.service;\n\nimport com.inventory.dto.*;\nimport com.inventory.exception.InsufficientStockException;\nimport com.inventory.exception.ResourceNotFoundException;\nimport com.inventory.model.Product;\nimport com.inventory.repository.ProductRepository;\nimport org.springframework.stereotype.Service;\nimport org.springframework.transaction.annotation.Transactional;\nimport java.util.List;\nimport java.util.stream.Collectors;\n\n@Service\npublic class ProductService {{\n    private final ProductRepository productRepository;\n\n    public ProductService(ProductRepository productRepository) {{\n        this.productRepository = productRepository;\n    }}\n\n    private ProductResponseDTO toDTO(Product p) {{\n        return new ProductResponseDTO(p.getId(), p.getName(), p.getSku(), p.getPrice(),\n                                     p.getStockQuantity(), p.getCategory(), p.getCreatedAt());\n    }}\n\n    public List<ProductResponseDTO> searchProducts(String name, String category) {{\n        return productRepository.searchProducts(name, category).stream().map(this::toDTO).collect(Collectors.toList());\n    }}\n\n    public ProductResponseDTO getById(Long id) {{\n        return toDTO(productRepository.findById(id)\n            .orElseThrow(() -> new ResourceNotFoundException(\"Product not found with id: \" + id)));\n    }}\n\n    @Transactional\n    public ProductResponseDTO createProduct(ProductRequestDTO dto) {{\n        Product p = new Product();\n        p.setName(dto.getName()); p.setSku(dto.getSku()); p.setPrice(dto.getPrice());\n        p.setStockQuantity(dto.getStockQuantity()); p.setCategory(dto.getCategory());\n        return toDTO(productRepository.save(p));\n    }}\n\n    @Transactional\n    public ProductResponseDTO updateProduct(Long id, ProductRequestDTO dto) {{\n        Product p = productRepository.findById(id)\n            .orElseThrow(() -> new ResourceNotFoundException(\"Product not found with id: \" + id));\n        p.setName(dto.getName()); p.setPrice(dto.getPrice());\n        p.setStockQuantity(dto.getStockQuantity()); p.setCategory(dto.getCategory());\n        return toDTO(productRepository.save(p));\n    }}\n\n    @Transactional\n    public ProductResponseDTO reduceStock(Long id, int quantity) {{\n        Product p = productRepository.findById(id)\n            .orElseThrow(() -> new ResourceNotFoundException(\"Product not found with id: \" + id));\n        if (p.getStockQuantity() < quantity) {{\n            throw new InsufficientStockException(\n                String.format(\"Insufficient stock for SKU %s. Requested: %d, Available: %d\",\n                              p.getSku(), quantity, p.getStockQuantity()));\n        }}\n        p.setStockQuantity(p.getStockQuantity() - quantity);\n        return toDTO(productRepository.save(p));\n    }}\n\n    @Transactional\n    public void deleteProduct(Long id) {{\n        if (!productRepository.existsById(id))\n            throw new ResourceNotFoundException(\"Product not found with id: \" + id);\n        productRepository.deleteById(id);\n    }}\n}}",

    "src/main/java/com/inventory/controller/ProductController.java": "package com.inventory.controller;\n\nimport com.inventory.dto.*;\nimport com.inventory.service.ProductService;\nimport jakarta.validation.Valid;\nimport org.springframework.http.HttpStatus;\nimport org.springframework.http.ResponseEntity;\nimport org.springframework.web.bind.annotation.*;\nimport java.util.List;\n\n@RestController\n@RequestMapping(\"/api/products\")\npublic class ProductController {{\n    private final ProductService productService;\n\n    public ProductController(ProductService productService) {{\n        this.productService = productService;\n    }}\n\n    @GetMapping\n    public ResponseEntity<List<ProductResponseDTO>> search(\n            @RequestParam(required = false) String name,\n            @RequestParam(required = false) String category) {{\n        return ResponseEntity.ok(productService.searchProducts(name, category));\n    }}\n\n    @GetMapping(\"/{{id}}\")\n    public ResponseEntity<ProductResponseDTO> getById(@PathVariable Long id) {{\n        return ResponseEntity.ok(productService.getById(id));\n    }}\n\n    @PostMapping\n    public ResponseEntity<ProductResponseDTO> create(@Valid @RequestBody ProductRequestDTO dto) {{\n        return ResponseEntity.status(HttpStatus.CREATED).body(productService.createProduct(dto));\n    }}\n\n    @PutMapping(\"/{{id}}\")\n    public ResponseEntity<ProductResponseDTO> update(@PathVariable Long id, @Valid @RequestBody ProductRequestDTO dto) {{\n        return ResponseEntity.ok(productService.updateProduct(id, dto));\n    }}\n\n    @PatchMapping(\"/{{id}}/reduce-stock\")\n    public ResponseEntity<ProductResponseDTO> reduceStock(@PathVariable Long id, @Valid @RequestBody StockReduceRequest req) {{\n        return ResponseEntity.ok(productService.reduceStock(id, req.getQuantity()));\n    }}\n\n    @DeleteMapping(\"/{{id}}\")\n    public ResponseEntity<Void> delete(@PathVariable Long id) {{\n        productService.deleteProduct(id);\n        return ResponseEntity.noContent().build();\n    }}\n}}",

    "src/main/resources/application.properties": "spring.datasource.url=jdbc:mysql://localhost:3306/inventorydb?createDatabaseIfNotExist=true\nspring.datasource.username=${{DB_USERNAME:root}}\nspring.datasource.password=${{DB_PASSWORD:}}\nspring.datasource.driver-class-name=com.mysql.cj.jdbc.Driver\nspring.jpa.hibernate.ddl-auto=update\nspring.jpa.show-sql=false\nspring.jpa.properties.hibernate.dialect=org.hibernate.dialect.MySQLDialect\nserver.port=8080",

    "pom.xml": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<project xmlns=\"http://maven.apache.org/POM/4.0.0\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n  xsi:schemaLocation=\"http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd\">\n  <modelVersion>4.0.0</modelVersion>\n  <parent>\n    <groupId>org.springframework.boot</groupId>\n    <artifactId>spring-boot-starter-parent</artifactId>\n    <version>3.2.5</version>\n  </parent>\n  <groupId>com.inventory</groupId>\n  <artifactId>product-inventory</artifactId>\n  <version>1.0.0</version>\n  <properties>\n    <java.version>17</java.version>\n  </properties>\n  <dependencies>\n    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency>\n    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-data-jpa</artifactId></dependency>\n    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-validation</artifactId></dependency>\n    <dependency><groupId>com.mysql</groupId><artifactId>mysql-connector-j</artifactId><scope>runtime</scope></dependency>\n    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-test</artifactId><scope>test</scope></dependency>\n  </dependencies>\n  <build>\n    <plugins>\n      <plugin><groupId>org.springframework.boot</groupId><artifactId>spring-boot-maven-plugin</artifactId></plugin>\n    </plugins>\n  </build>\n</project>",

    "README.md": "# Product Inventory API\n\n## Setup\n```bash\n# Set environment variables or edit application.properties\nexport DB_USERNAME=root\nexport DB_PASSWORD=yourpassword\nmvn spring-boot:run\n```\n\n## Endpoints\n- GET /api/products?name=widget&category=electronics — search products\n- GET /api/products/:id — get product\n- POST /api/products — create product\n- PUT /api/products/:id — update product\n- PATCH /api/products/:id/reduce-stock — reduce stock (body: {{\"quantity\": 5}})\n- DELETE /api/products/:id — delete product"
  }}
}}

---

REQUIREMENTS:
{requirements_json}
"""