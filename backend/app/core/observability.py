from uuid import UUID, uuid4

from fastapi import Request


def correlation_id(request: Request) -> str:
    value = getattr(request.state, "correlation_id", None)
    return value or str(uuid4())


def valid_correlation_id(value: str | None) -> str:
    try:
        return str(UUID(value)) if value else str(uuid4())
    except (ValueError, AttributeError):
        return str(uuid4())
