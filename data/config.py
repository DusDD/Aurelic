import os
from dotenv import load_dotenv

load_dotenv()

# Database
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", 5432))
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# --------------------------
# API Keys
# --------------------------
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

if not POLYGON_API_KEY:
    raise RuntimeError(
        "POLYGON_API_KEY not set. "
        "Please export POLYGON_API_KEY before running the app."
    )

# --------------------------
# Symbols
# --------------------------
SYMBOLS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
]