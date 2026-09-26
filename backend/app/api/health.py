from fastapi import APIRouter
from app.schemas.errors import ErrorResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Check API liveness",
    response_model=dict[str, str],
    responses={500: {"model": ErrorResponse, "description": "Unexpected API error"}},
)
def health() -> dict[str, str]:
    """Report that the API process is accepting requests."""
    return {"status": "ok"}
