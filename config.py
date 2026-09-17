"""
Configuration management for the research pipeline.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
RESULTS_DIR = DATA_DIR / "results"
CACHE_DIR = DATA_DIR / "cache"
OUTPUT_DIR = ROOT_DIR / "output"

# Create directories
for d in [DATA_DIR, RESULTS_DIR, CACHE_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# --- API Keys ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY", "")

# --- Composio ---
USE_COMPOSIO = bool(COMPOSIO_API_KEY)  # Auto-enable if key is present

# --- LLM Settings ---
GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_RPM = 15          # Free tier: 15 requests per minute
GEMINI_RPD = 1500         # Free tier: 1500 requests per day
LLM_TEMPERATURE = 0.1     # Low temperature for factual extraction
LLM_MAX_OUTPUT_TOKENS = 4096

# --- Search Settings ---
SEARCH_RESULTS_PER_QUERY = 5
MAX_URLS_PER_APP = 6
URL_FETCH_TIMEOUT = 15     # seconds
MAX_DOC_CHARS = 8000       # Max chars to feed to LLM per document

# --- Pipeline Settings ---
CONCURRENCY = 3            # Parallel URL fetches
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2            # seconds

# --- Verification ---
VERIFICATION_SAMPLE_SIZE = 20  # Apps to manually verify
