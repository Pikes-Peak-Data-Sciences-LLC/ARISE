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

DEFAULT_AGENTS = 3 # the number of agents to start with
MAX_AGENTS = 10 # the maximum number of agents allowed
MEMORY_WINDOW = 30 # the number of previous turns to keep in memory
OUTPUT_CHARACTER_LIMIT = 10000 # the maximum number of characters allowed in an output. This should be < MAX_TOKENS * 4.
MAX_STEPS = 1000 # the maximum number of steps allowed overall
REWORK_PASSES = 0 # the number of rework cycles

# LLM parameters
MAX_TOKENS = 8192
MAX_RETRIES = 1
TEMPERATURE = 0.2 
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
