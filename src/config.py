from pathlib import Path
from dotenv import load_dotenv
import os

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(ENV_PATH)

TWITTERAPI_KEY = os.getenv("TWITTERAPI_KEY")
BRIGHT_DATA_AUTH = os.getenv("BRIGHT_DATA_AUTH")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TWITTERAPI_KEY:
    raise RuntimeError("TWITTERAPI_KEY is not set in .env")
if not BRIGHT_DATA_AUTH:
    raise RuntimeError("BRIGHT_DATA_AUTH is not set in .env")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set in .env")

COOKIES_FILE = ROOT_DIR / "cookies.txt"
