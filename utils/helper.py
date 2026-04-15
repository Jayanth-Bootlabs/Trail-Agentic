import hashlib
from passlib.context import CryptContext
import json
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    sha_password = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(sha_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    sha_password = hashlib.sha256(plain_password.encode()).hexdigest()
    return pwd_context.verify(sha_password, hashed_password)


def clean_ai_response(raw: str):
    if not raw:
        return None

    cleaned = re.sub(r"```(?:json)?", "", raw)
    cleaned = cleaned.replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    return cleaned