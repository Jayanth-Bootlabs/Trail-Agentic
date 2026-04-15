import json
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv(override=True)

DEPLOYED_ENV = os.getenv("DEPLOYED_ENV", "").lower()

logger = logging.getLogger("data_pipeline_app")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(stream_handler)


def log_event(
    level: str,
    service: str,
    message: str,
    function: str | None = None,
    metadata=None,
    stack_trace=None,
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