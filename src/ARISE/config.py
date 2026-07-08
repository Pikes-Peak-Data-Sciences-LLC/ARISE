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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_env_file(PROJECT_ROOT / ".env")

MCP_SERVERS_PATH = PROJECT_ROOT / "mcp_server.yaml"

DEFAULT_AGENTS = 3
MAX_STEPS = 1000
MAX_TOKENS = 4096
TEMPERATURE = 0.2
MAX_AGENTS = 10
REWORK_PASSES = 1
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
BEDROCK_MODEL = os.getenv("BEDROCK_MODEL", "anthropic.claude-haiku-4-5-20251001-v1:0")


def resolve_bedrock_model_id(model: str, region: str) -> str:
    """Map bare foundation model IDs to Bedrock inference profile IDs."""
    if model.startswith(("arn:", "us.", "eu.", "ap.", "global.")):
        return model
    if model.startswith(("amazon.", "anthropic.")):
        geo = region.split("-")[0]
        return f"{geo}.{model}"
    return model
