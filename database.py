import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)
DB_FILE = Path("screener_cache.db")


def get_connection() -> sqlite3.Connection:
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_initialized() -> None:
    """Internal function to initialize database tables and indices."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Create stock cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_cache (
                ticker TEXT PRIMARY KEY,
                company_name TEXT,
                sector TEXT,
                industry TEXT,
                market_cap REAL,
                pe_ratio REAL,
                pb_ratio REAL,
                ps_ratio REAL,
                ev_ebitda REAL,
                roe REAL,
                roa REAL,
                gross_margin REAL,
                operating_margin REAL,
                net_margin REAL,
                revenue_growth REAL,
                earnings_growth REAL,
                free_cashflow_yield REAL,
                debt_to_equity REAL,
                current_ratio REAL,
                quick_ratio REAL,
                dividend_yield REAL,
                payout_ratio REAL,
                beta REAL,
                fifty_two_week_high REAL,
                fifty_two_week_low REAL,
                current_price REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create historical snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS score_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date DATE DEFAULT CURRENT_DATE,
                ticker TEXT,
                overall_score REAL,
                value_score REAL,
                quality_score REAL,
                growth_score REAL,
                rank INTEGER,
                FOREIGN KEY (ticker) REFERENCES stock_cache (ticker)
            )
        """)

        conn.commit()


def init_db() -> bool:
    """Public wrapper to initialize database tables and schema."""
    try:
        _ensure_initialized()
        logger.info("Database initialized successfully.")
        return True
    except Exception as err:
        logger.error("Failed to initialize database: %s", err)
        return False


def save_stock_cache(df: pd.DataFrame) -> bool:
    """Saves or updates fetched stock records in SQLite."""
    if df.empty:
        return False
    try:
        init_db()
        with get_connection() as conn:
            df.to_sql("stock_cache", conn, if_exists="replace", index=False)
            conn.commit()
        return True
    except Exception as err:
        logger.error("Error saving stock cache: %s", err)
        return False


def load_stock_cache() -> pd.DataFrame:
    """Loads cached stock metrics from SQLite."""
    try:
        init_db()
        with get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM stock_cache", conn)
    except Exception as err:
        logger.error("Error reading stock cache: %s", err)
        return pd.DataFrame()


def save_score_snapshot(scores_df: pd.DataFrame) -> bool:
    """Records a scoring snapshot for historical trend analysis."""
    if scores_df.empty:
        return False
    try:
        init_db()
        with get_connection() as conn:
            scores_df.to_sql("score_snapshots", conn, if_exists="append", index=False)
            conn.commit()
        return True
    except Exception as err:
        logger.error("Error saving score snapshot: %s", err)
        return False