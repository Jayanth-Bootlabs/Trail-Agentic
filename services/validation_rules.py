import re

PROJECT_WORDS = {
    "app", "application", "website", "portal",
    "dashboard", "crm", "erp", "system",
    "platform", "software"
}

PLATFORM_WORDS = {
    "web", "mobile", "android", "ios", "desktop"
}


def clean_text(text: str) -> str:
    return text.strip().lower()


def is_empty(text: str) -> bool:
    return len(clean_text(text)) == 0


def too_short(text: str) -> bool:
    return len(clean_text(text).split()) < 2


def looks_like_spam(text: str) -> bool:
    t = clean_text(text)

    if re.fullmatch(r"[0-9]+", t):
        return True

    if re.fullmatch(r"[a-z]{1,4}", t):
        return True

    if len(set(t.replace(" ", ""))) <= 2:
        return True

    return False


def detect_project_keyword(text: str) -> bool:
    words = set(clean_text(text).split())
    return len(words.intersection(PROJECT_WORDS)) > 0


def detect_platform(text: str):
    words = set(clean_text(text).split())
    return list(words.intersection(PLATFORM_WORDS))


def run_rule_validation(user_input: str):
    text = clean_text(user_input)

    if is_empty(text):
        return {
            "status": "invalid",
            "message": "Please enter your project idea.",
            "source": "rule_engine"
        }

    if too_short(text):
        return {
            "status": "invalid",
            "message": "Please describe your request in more detail.",
            "source": "rule_engine"
        }

    if looks_like_spam(text):
        return {
            "status": "invalid",
            "message": "Input looks invalid. Please enter a real project request.",
            "source": "rule_engine"
        }

    has_project = detect_project_keyword(text)
    platforms = detect_platform(text)

    if has_project and platforms:
        return {
            "status": "valid",
            "message": "Project request accepted.",
            "platforms": platforms,
            "source": "rule_engine"
        }

    return None