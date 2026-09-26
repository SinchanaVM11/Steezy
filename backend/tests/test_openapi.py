from app.main import app
from app.schemas.errors import ErrorResponse


def test_openapi_covers_current_collaboration_contract() -> None:
    document = app.openapi()
    assert set(document["paths"]) == {
        "/health",
        "/wardrobe/items",
        "/feedback",
        "/assets/images",
        "/analysis/garments",
        "/analysis/garments/{job_id}/wardrobe-item",
    }
    assert document["paths"]["/health"]["get"]["responses"]["200"]["content"]
    assert document["paths"]["/wardrobe/items"]["post"]["responses"]["201"]["content"]
    assert document["paths"]["/feedback"]["post"]["responses"]["404"]["content"]


def test_error_schema_has_stable_key_paths() -> None:
    schema = app.openapi()["components"]["schemas"]["ErrorResponse"]
    assert schema["properties"]["error"]["$ref"].endswith("/ErrorBody")
    assert set(app.openapi()["components"]["schemas"]["ErrorBody"]["properties"]) == {
        "code",
        "message",
        "correlation_id",
        "details",
    }
    assert ErrorResponse.model_json_schema()["properties"]["error"]
