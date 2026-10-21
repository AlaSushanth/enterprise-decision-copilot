import os
from pathlib import Path
from dotenv import load_dotenv

# Base Project Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "documents"
DB_PATH = DATA_DIR / "database" / "enterprise_analytics.duckdb"
CHROMA_PERSIST_DIR = BASE_DIR / "chroma_db"

load_dotenv(BASE_DIR / ".env")

# LLM & Embedding Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Default Model Selection
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini") # 'gemini', 'openai', or 'rule-fallback'
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
