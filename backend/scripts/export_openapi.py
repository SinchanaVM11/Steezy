import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


REQUIRED_OPERATIONS = {
    ("/health", "get"),
    ("/wardrobe/items", "get"),
    ("/wardrobe/items", "post"),
    ("/feedback", "get"),
    ("/feedback", "post"),
    ("/assets/images", "post"),
    ("/analysis/garments", "post"),
    ("/analysis/garments/{job_id}/wardrobe-item", "post"),
}


def schema() -> dict:
    return app.openapi()


def validate(document: dict) -> None:
    paths = document.get("paths", {})
    missing = sorted(
        f"{method.upper()} {path}"
        for path, method in REQUIRED_OPERATIONS
        if method not in paths.get(path, {})
    )
    if missing:
        raise ValueError(f"OpenAPI schema is missing operations: {', '.join(missing)}")

    for path, method in REQUIRED_OPERATIONS:
        operation = paths[path][method]
        if "responses" not in operation:
            raise ValueError(f"{method.upper()} {path} has no response metadata")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export and validate Steezy OpenAPI schema.")
    parser.add_argument("--output", type=Path, help="Write JSON to this path instead of stdout.")
    args = parser.parse_args()
    document = schema()
    validate(document)
    serialized = json.dumps(document, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    else:
        sys.stdout.write(serialized)


if __name__ == "__main__":
    main()
