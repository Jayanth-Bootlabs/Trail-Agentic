from prometheus_client import Counter, Gauge, Histogram



# LLM / MODEL ROUTING


LLM_REQUESTS = Counter(
    "llm_requests_total",
    "LLM requests routed by node, tier, model and status",
    ["node", "tier", "model", "status"],
)

LLM_LATENCY = Histogram(
    "llm_latency_seconds",
    "LLM request latency by node, tier and model",
    ["node", "tier", "model"],
    buckets=(0.25, 0.5, 1, 2.5, 5, 10, 20, 30, 60, 120, 300, 600),
)

LLM_RESPONSE_CHARS = Histogram(
    "llm_response_chars",
    "LLM response size in characters",
    ["node", "tier", "model"],
    buckets=(100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000),
)



# PIPELINE ORCHESTRATION


PIPELINE_RUNS = Counter(
    "pipeline_runs_total",
    "Pipeline runs by final status",
    ["status"],
)

PIPELINE_ACTIVE_RUNS = Gauge(
    "pipeline_active_runs",
    "Pipeline runs currently executing",
)

PIPELINE_STAGE_DURATION = Histogram(
    "pipeline_stage_duration_seconds",
    "Pipeline stage execution duration by stage",
    ["stage"],
    buckets=(1, 2.5, 5, 10, 20, 30, 60, 120, 300, 600),
)

PIPELINE_STAGE_FAILURES = Counter(
    "pipeline_stage_failures_total",
    "Pipeline stage failures by stage",
    ["stage"],
)

PIPELINE_CLARIFICATIONS = Counter(
    "pipeline_clarifications_total",
    "Clarification replies sent by users",
)



# REDIS CACHE


CACHE_LOOKUPS = Counter(
    "cache_lookups_total",
    "Redis cache lookups by service and result",
    ["service", "result"],
)
