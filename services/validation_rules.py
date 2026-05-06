import re

PROJECT_WORDS = {
    "app", "application", "website", "portal",
    "dashboard", "crm", "erp", "system",
    "platform", "software"
}

PLATFORM_WORDS = {
    "web", "mobile", "android", "ios", "desktop"
}


#Removes left and right space and converts to lower case
def clean_text(text: str) -> str:
    return text.strip().lower()


#Will check for empty input
def is_empty(text: str) -> bool:
    return len(clean_text(text)) == 0


#Will check if input is too short
def too_short(text: str) -> bool:
    return len(clean_text(text).split()) < 2



def looks_like_spam(text: str) -> bool:
    t = clean_text(text)

    #Will check whether input consists only numericals
    if re.fullmatch(r"[0-9]+", t):
        return True

    #Will check whether input consists only of 1 to 4 lowercase letters
    if re.fullmatch(r"[a-z]{1,4}", t):
        return True
    
    #Will check if the input has 2 or fewer unique characters (ignoring spaces)
    if len(set(t.replace(" ", ""))) <= 2:
        return True

    return False


#Will return TRUE, if project keyword is there
def detect_project_keyword(text: str) -> bool:
    words = set(clean_text(text).split())
    return len(words.intersection(PROJECT_WORDS)) > 0


#Will return the platform of what user wants
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