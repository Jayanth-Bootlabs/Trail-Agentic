import asyncio
import json
import os
import re
import time
import traceback
import uuid

from dotenv import load_dotenv
from langchain_ollama import ChatOllama

from utils.logger import get_pipeline_context, log_event
from utils.metrics import LLM_LATENCY, LLM_REQUESTS, LLM_RESPONSE_CHARS

load_dotenv(override=True)

SERVICE_NAME = "model_router"



# CONFIG

def _env_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        log_event(
            level="WARNING",
            service=SERVICE_NAME,
            function="_env_int",
            message=f"Invalid integer for {key}, falling back to default",
            metadata={"value": raw, "default": default},
        )
        return default


def _env_float(key: str, default: float) -> float:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        log_event(
            level="WARNING",
            service=SERVICE_NAME,
            function="_env_float",
            message=f"Invalid float for {key}, falling back to default",
            metadata={"value": raw, "default": default},
        )
        return default


BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

SIMPLE_MODEL = os.getenv("OLLAMA_SIMPLE_MODEL", "llama3.1:latest")

COMPLEX_MODEL = os.getenv("OLLAMA_COMPLEX_MODEL", "gpt-oss:120b-cloud")

TEMPERATURE = _env_float("LLM_ROUTER_TEMPERATURE", 0.1)

NUM_PREDICT = _env_int("LLM_ROUTER_NUM_PREDICT", 0)

KEEP_ALIVE = os.getenv("LLM_ROUTER_KEEP_ALIVE", "30m")

TIMEOUT = _env_float("LLM_ROUTER_TIMEOUT", 600)

JSON_MODE = _env_bool("LLM_ROUTER_JSON_MODE", True)

FALLBACK_TO_COMPLEX = _env_bool("LLM_ROUTER_FALLBACK_TO_COMPLEX", True)

ENABLED = _env_bool("LLM_ROUTER_ENABLED", True)

TRACE_INCLUDE_QUERY = _env_bool("LLM_TRACE_INCLUDE_QUERY", True)



# TIERS


SIMPLE = "simple"

COMPLEX = "complex"

TIER_MODELS = {
    SIMPLE: SIMPLE_MODEL,
    COMPLEX: COMPLEX_MODEL,
}

TIER_NUM_CTX = {
    SIMPLE: _env_int("LLM_ROUTER_NUM_CTX_SIMPLE", 16384),
    COMPLEX: _env_int("LLM_ROUTER_NUM_CTX_COMPLEX", 32768),
}

TIER_NUM_PREDICT = {
    SIMPLE: _env_int("LLM_ROUTER_NUM_PREDICT_SIMPLE", 8192),
    COMPLEX: _env_int("LLM_ROUTER_NUM_PREDICT_COMPLEX", 24576),
}



# NODE ROUTING TABLE


NODE_TIER_MAP = {
    "validation_node": COMPLEX,
    "requirements_node": COMPLEX,
    "code_node": COMPLEX,
    "unit_test_node": COMPLEX,
    "insights_node": SIMPLE,
    "documentation_node": SIMPLE,
}


def resolve_tier(node_name: str) -> str:
    tier = NODE_TIER_MAP.get(node_name)

    if tier is None:
        tier = COMPLEX if FALLBACK_TO_COMPLEX else SIMPLE

        log_event(
            level="WARNING",
            service=SERVICE_NAME,
            function="resolve_tier",
            message="Unknown node, using fallback tier",
            metadata={
                "node": node_name,
                "resolved_tier": tier,
            },
        )

    return tier



# HARMONY RESPONSE CLEANING


_HARMONY_END = re.compile(r"<\|end\|>")

_HARMONY_CHANNEL = re.compile(r"<\|channel\|>[^<]*<\|message\|>")

_HARMONY_ANY = re.compile(r"<\|[^|>]*\|>")

_HARMONY_FINAL = re.compile(
    r"<\|channel\|>final<\|message\|>(.*?)(?:<\|end\|>|<\|start\|>|\Z)",
    re.DOTALL,
)


def strip_reasoning(raw: str) -> str:
    if not raw:
        return raw

    if not _HARMONY_CHANNEL.search(raw):
        return raw.strip()

    final_match = _HARMONY_FINAL.search(raw)

    if final_match:
        return final_match.group(1).strip()

    text = _HARMONY_CHANNEL.sub("", raw)
    text = _HARMONY_END.sub("", text)

    return _HARMONY_ANY.sub("", text).strip()


 
# ROUTED LLM
 

class RoutedLLM:
    def __init__(self):
        self._clients = {}

    def _build_client(self, tier: str) -> ChatOllama:
        model = TIER_MODELS[tier]

        num_predict = NUM_PREDICT or TIER_NUM_PREDICT[tier]

        params = {
            "model": model,
            "base_url": BASE_URL,
            "num_ctx": TIER_NUM_CTX[tier],
            "num_predict": num_predict,
            "temperature": TEMPERATURE,
            "keep_alive": KEEP_ALIVE,
            "async_client_kwargs": {"timeout": TIMEOUT},
        }

        if JSON_MODE:
            params["format"] = "json"

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="_build_client",
            message="Ollama client initialized",
            metadata={
                "tier": tier,
                "model": model,
                "base_url": BASE_URL,
                "num_ctx": params["num_ctx"],
                "num_predict": num_predict,
                "json_mode": JSON_MODE,
            },
        )

        return ChatOllama(**params)

    def get_client(self, tier: str) -> ChatOllama:
        client = self._clients.get(tier)

        if client is None:
            client = self._build_client(tier)
            self._clients[tier] = client

        return client

    def _model_for(self, tier: str) -> str:
        return TIER_MODELS[tier]

    async def generate_for_node(
        self,
        prompt: str,
        node_name: str,
        request_context=None,
    ) -> str:
        tier = resolve_tier(node_name)

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate_for_node",
            message="Routing LLM request",
            metadata={
                "node": node_name,
                "tier": tier,
                "model": self._model_for(tier),
            },
        )

        return await self.generate(
            prompt,
            tier,
            node=node_name,
            request_context=request_context,
        )

    async def generate(
        self,
        prompt: str,
        tier: str = COMPLEX,
        node: str | None = None,
        request_context=None,
    ) -> str:
        if not ENABLED:
            log_event(
                level="WARNING",
                service=SERVICE_NAME,
                function="generate",
                message="Router disabled, defaulting to complex tier",
                metadata={"tier": tier},
            )
            tier = COMPLEX

        client = self.get_client(tier)

        node_label = node or "direct"
        model = self._model_for(tier)
        started_at = time.perf_counter()
        trace_id = uuid.uuid4().hex
        pipeline_context = get_pipeline_context()
        pipeline_query = pipeline_context.get("pipeline_query", "") if TRACE_INCLUDE_QUERY else ""
        pipeline_query = pipeline_query[:2000]
        if not TRACE_INCLUDE_QUERY:
            query = ""
        elif isinstance(request_context, str):
            query = request_context
        else:
            query = json.dumps(request_context, ensure_ascii=False, default=str) if request_context is not None else ""
        query_truncated = TRACE_INCLUDE_QUERY and len(query) > 2000
        query = query[:2000]

        try:
            response = await client.ainvoke(prompt)
        except Exception:
            duration = time.perf_counter() - started_at
            LLM_LATENCY.labels(
                node=node_label, tier=tier, model=model
            ).observe(duration)

            LLM_REQUESTS.labels(
                node=node_label, tier=tier, model=model, status="error"
            ).inc()

            log_event(
                level="ERROR",
                service=SERVICE_NAME,
                function="generate",
                message="LLM request trace",
                fields={
                    "event": "llm_request",
                    "trace_id": trace_id,
                    "pipeline_run_id": pipeline_context.get("pipeline_run_id"),
                    "pipeline_query": pipeline_query,
                    "node": node_label,
                    "tier": tier,
                    "model": model,
                    "status": "error",
                    "duration_seconds": duration,
                    "query": query,
                    "query_truncated": query_truncated,
                },
            )

            log_event(
                level="ERROR",
                service=SERVICE_NAME,
                function="generate",
                message="Ollama call failed",
                stack_trace=traceback.format_exc(),
                metadata={
                    "node": node_label,
                    "tier": tier,
                    "model": model,
                    "base_url": BASE_URL,
                },
            )
            raise

        content = getattr(response, "content", response)

        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )

        cleaned = strip_reasoning(str(content))
        duration = time.perf_counter() - started_at

        LLM_LATENCY.labels(
            node=node_label, tier=tier, model=model
        ).observe(duration)

        LLM_REQUESTS.labels(
            node=node_label, tier=tier, model=model, status="success"
        ).inc()

        LLM_RESPONSE_CHARS.labels(
            node=node_label, tier=tier, model=model
        ).observe(len(cleaned))

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate",
            message="LLM request trace",
            fields={
                "event": "llm_request",
                "trace_id": trace_id,
                "pipeline_run_id": pipeline_context.get("pipeline_run_id"),
                "pipeline_query": pipeline_query,
                "node": node_label,
                "tier": tier,
                "model": model,
                "status": "success",
                "duration_seconds": duration,
                "query": query,
                "query_truncated": query_truncated,
            },
        )

        log_event(
            level="INFO",
            service=SERVICE_NAME,
            function="generate",
            message="Ollama response received",
            metadata={
                "node": node_label,
                "tier": tier,
                "model": model,
                "response_length": len(cleaned),
            },
        )

        return cleaned

    def invoke(self, prompt: str, tier: str = COMPLEX) -> str:
        return asyncio.run(self.generate(prompt, tier))

    def call(self, messages=None, **kwargs):
        if messages:
            prompt = "\n".join(
                m.get("content", "") for m in messages if isinstance(m, dict)
            )
        else:
            prompt = str(kwargs.get("prompt", ""))

        return asyncio.run(self.generate(prompt, kwargs.get("tier", COMPLEX)))

    def __call__(self, prompt: str, tier: str = COMPLEX) -> str:
        return self.invoke(prompt, tier)


llm = RoutedLLM()
