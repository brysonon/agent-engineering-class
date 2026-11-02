from pathlib import Path

from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parent
COURSE_DIR = PROJECT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
MODEL = "text-embedding-3-small"

load_dotenv(COURSE_DIR / ".env")
