import hashlib
from passlib.context import CryptContext
import json

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

    cleaned = raw.replace("```json", "").replace("```", "").strip()

    try:
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1

        if start == -1 or end == -1:
            return None

        json_str = cleaned[start:end]

        return json.loads(json_str)

    except Exception:
        return None