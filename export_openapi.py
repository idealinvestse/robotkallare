"""Utility script to export the FastAPI OpenAPI schema to docs/openapi.json.

Run from project root:
    python export_openapi.py
This will import the FastAPI app from app.api, generate the OpenAPI schema,
write it to docs/openapi.json (creating the directory if needed), and print a
confirmation message. The script avoids starting the HTTP server, so it is
safe to run in any environment as long as the required environment variables
are present or have sensible defaults in `app.config.Settings`.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from importlib import import_module

# Ensure execution from project root
def _project_root() -> Path:
    return Path(__file__).resolve().parent


def main() -> None:
    os.environ.setdefault("SKIP_TWILIO_VALIDATION", "True")

    # Import the FastAPI application without standing up the server
    api_module = import_module("app.api")
    app = getattr(api_module, "app")

    # Generate the OpenAPI schema in memory
    openapi_schema = app.openapi()

    # Output path
    docs_dir = _project_root() / "docs"
    docs_dir.mkdir(exist_ok=True)
    out_file = docs_dir / "openapi.json"

    # Write schema prettified
    out_file.write_text(json.dumps(openapi_schema, indent=2))
    print(f"OpenAPI schema exported to {out_file.relative_to(_project_root())}")


if __name__ == "__main__":
    main()
