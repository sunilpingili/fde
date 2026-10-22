import os
import psycopg
from pathlib import Path
from dotenv import load_dotenv

# Load .env from this project's own directory (not the root .env used by other projects)
load_dotenv(Path(__file__).parent / ".env")

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "healthcare_readmission_db"),
    "user":     os.getenv("DB_USER", "fde_user"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_connection() -> psycopg.Connection:
    return psycopg.connect(**DB_CONFIG)


def init_db():
    schema_path = Path(__file__).parent / "schema.sql"
    sql = schema_path.read_text()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
