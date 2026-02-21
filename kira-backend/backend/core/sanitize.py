import re

from backend.core.exceptions import ValidationAppError


PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+all\s+previous\s+instructions",
    r"system\s+prompt",
    r"reveal\s+hidden",
    r"developer\s+message",
    r"bypass\s+safety",
]


def validate_prompt_input(text: str) -> None:
    lowered = text.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            raise ValidationAppError("Prompt contains unsafe instruction patterns", "PROMPT_INJECTION_DETECTED")


def sanitize_output_text(text: str) -> str:
    sanitized = text.replace("\x00", "").strip()
    sanitized = re.sub(r"[\x01-\x08\x0B\x0C\x0E-\x1F]", "", sanitized)
    return sanitized
