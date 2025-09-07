import re
from typing import Any


def to_camel_case(s: str) -> str:
    """Convert snake_case, kebab-case, or spaced string to camelCase."""
    parts = re.split(r"[_\-\s]+", s)
    return parts[0].lower() + "".join(word.capitalize() for word in parts[1:])


def keys_to_camel_case(
    obj: dict[str, Any] | list[Any] | Any,
) -> dict[str, Any] | list[Any] | Any:
    """Recursively convert all dict keys to camelCase."""
    if isinstance(obj, dict):
        return {
            to_camel_case(k) if isinstance(k, str) else k: keys_to_camel_case(v)
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [keys_to_camel_case(item) for item in obj]
    else:
        return obj
