import json
import logging
import os
import traceback
from collections.abc import Callable
from contextvars import ContextVar, Token
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv(override=True)

DEPLOYED_ENV = os.getenv("DEPLOYED_ENV", "").lower()

logger = logging.getLogger("data_pipeline_app")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    formatter = logging.Formatter("%(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    project_root = Path(__file__).resolve().parents[1]
    log_path = Path(os.getenv("APP_LOG_FILE", str(project_root / "logs/backend.jsonl")))
    if not log_path.is_absolute():
        log_path = project_root / log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=20 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


_PIPELINE_CONTEXT: ContextVar[dict] = ContextVar("pipeline_context", default={})


def set_pipeline_context(run_id: int, user_input: str) -> Token:
    return _PIPELINE_CONTEXT.set({"pipeline_run_id": run_id, "pipeline_query": user_input})


def reset_pipeline_context(token: Token) -> None:
    _PIPELINE_CONTEXT.reset(token)


def get_pipeline_context() -> dict:
    return _PIPELINE_CONTEXT.get()


def log_event(
    level: str,
    service: str,
    message: str,
    function: str | None = None,
    metadata=None,
    stack_trace=None,
    fields=None,
):
    log_entry = {
        "timestamp": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
        "level": level.upper(),
        "service": service,
        "message": message,
        "function": function,
        "metadata": metadata or {},
        "env": DEPLOYED_ENV,
    }

    if stack_trace:
        log_entry["stack_trace"] = stack_trace

    if fields:
        log_entry.update(fields)

    level = level.upper()

    if level == "DEBUG":
        logger.debug(json.dumps(log_entry, default=str))
    elif level == "INFO":
        logger.info(json.dumps(log_entry, default=str))
    elif level == "WARNING":
        logger.warning(json.dumps(log_entry, default=str))
    elif level == "ERROR":
        logger.error(json.dumps(log_entry, default=str))
    elif level == "CRITICAL":
        logger.critical(json.dumps(log_entry, default=str))
    else:
        logger.info(json.dumps(log_entry, default=str))


def trace_graph_node(node_name: str, node: Callable):
    """Wrap a LangGraph node and log the selected state fields around it."""
    async def logged_node(state):
        state_fields = ("user_input", "messages", "status", "error", "retry_count")

        def snapshot(current_state):
            return {key: current_state.get(key) for key in state_fields}

        log_event(
            level="INFO",
            service="langgraph",
            function=node_name,
            message="Graph state before node",
            metadata={"graph_state": snapshot(state)},
        )

        try:
            updated_state = await node(state)
        except Exception as exc:
            error_state = snapshot(state)
            error_state["error"] = str(exc)
            log_event(
                level="ERROR",
                service="langgraph",
                function=node_name,
                message="Graph node raised an exception",
                metadata={"graph_state": error_state},
                stack_trace=traceback.format_exc(),
            )
            raise

        log_event(
            level="INFO",
            service="langgraph",
            function=node_name,
            message="Graph state after node",
            metadata={"graph_state": snapshot(updated_state)},
        )
        return updated_state

    return logged_node
