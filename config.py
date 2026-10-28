from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent
AGENTS_DIR = ROOT / "agents"
SHARED_DIR = ROOT / "shared"
DATA_DIR = ROOT / "data"
WORKSPACE_DIR = ROOT / "workspace"
CHECKPOINT_DB = DATA_DIR / "checkpoints.sqlite"

OLLAMA_MODEL = os.environ.get("AGENT_OFFICE_MODEL", "qwen3.5:9b")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
MAX_QA_RETRIES = int(os.environ.get("AGENT_OFFICE_MAX_RETRIES", "2"))
MAX_SCOPE_ESCALATIONS = int(os.environ.get("AGENT_OFFICE_MAX_SCOPE_ESCALATIONS", "3"))
MAX_SCOPE_DIALOGUE_TURNS = int(os.environ.get("AGENT_OFFICE_MAX_SCOPE_DIALOGUE", "4"))
LLM_TEMPERATURE = float(os.environ.get("AGENT_OFFICE_TEMPERATURE", "0.2"))
OLLAMA_NUM_PREDICT = int(os.environ.get("AGENT_OFFICE_NUM_PREDICT", "12288"))
JSON_PARSE_ATTEMPTS = int(os.environ.get("AGENT_OFFICE_JSON_ATTEMPTS", "4"))
MODELS_CONFIG_PATH = os.environ.get("AGENT_OFFICE_MODELS", str(ROOT / "models.yaml"))
SKILLS_CONFIG_PATH = os.environ.get("AGENT_OFFICE_SKILLS", str(ROOT / "skills.yaml"))
OFFICE_CONFIG_PATH = os.environ.get("AGENT_OFFICE_CONFIG", str(ROOT / "office.yaml"))
