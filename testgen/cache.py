# testgen/cache.py
import sqlite3
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def init_cache(db_path: str, allow_threads: bool = True) -> sqlite3.Connection:
    """
    Initialize or open an SQLite cache. 
    If allow_threads, we disable same-thread check for ThreadPoolExecutor.
    """
    conn = sqlite3.connect(db_path, check_same_thread=not allow_threads)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS test_cache (
            key TEXT PRIMARY KEY,
            source_hash TEXT,
            model_name TEXT,
            generated_code TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def compute_sha256_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def get_cached_test(conn: sqlite3.Connection, key: str, source_hash: str, model_name: str) -> Optional[str]:
    row = conn.execute(
        "SELECT generated_code FROM test_cache WHERE key=? AND source_hash=? AND model_name=?",
        (key, source_hash, model_name)
    ).fetchone()
    if row:
        logger.info(f"Cache HIT for key={key}")
        return row[0]
    logger.debug(f"Cache MISS for key={key}")
    return None

def cache_test(conn: sqlite3.Connection, key: str, source_hash: str, model_name: str, generated_code: str) -> None:
    try:
        conn.execute("""
            INSERT OR REPLACE INTO test_cache (key, source_hash, model_name, generated_code)
            VALUES (?, ?, ?, ?)
        """, (key, source_hash, model_name, generated_code))
        conn.commit()
        logger.info(f"Cached test for key={key}")
    except sqlite3.Error as e:
        logger.error(f"Failed to write cache: {e}")
