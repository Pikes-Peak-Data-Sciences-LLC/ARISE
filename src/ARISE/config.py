"""Configuration defaults for ARISE."""

import os
from pathlib import Path


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_env_file(Path(__file__).resolve().parents[2] / ".env")

DEFAULT_AGENTS = 5
MAX_AGENTS = 10
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
BEDROCK_MODEL = os.getenv("BEDROCK_MODEL", "us.amazon.nova-micro-v1:0")


def resolve_bedrock_model_id(model: str, region: str) -> str:
    """Map bare Nova model IDs to Bedrock inference profile IDs."""
    if model.startswith(("arn:", "us.", "eu.", "ap.")):
        return model
    if model.startswith("amazon."):
        geo = region.split("-")[0]
        return f"{geo}.{model}"
    return model
