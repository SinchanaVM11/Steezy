from typing import Any

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    correlation_id: str
    details: Any


class ErrorResponse(BaseModel):
    error: ErrorBody
