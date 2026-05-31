# -*- coding: utf-8 -*-
"""
Persistence Layer for DataCleanAgent.
Manages session state, audit traces, and DataFrame snapshots using SQLite and Parquet.
Ensures session data is preserved across browser refreshes and application restarts.
"""

import os
import json
import sqlite3
import datetime
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional

class SessionStore:
    """Manages transactional state and audit trail persistence for cleaning sessions."""
    
    def __init__(self, db_dir: str = "data/sessions"):
        self.db_dir = os.path.abspath(db_dir)
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, "sessions_store.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes tables for sessions, actions, and profiles if they do not exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    current_step INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS action_traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    step INTEGER NOT NULL,
                    action_name TEXT NOT NULL,
                    action_args TEXT NOT NULL,
                    justification TEXT NOT NULL,
                    code TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    step INTEGER NOT NULL,
                    profile_json TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            """)
            conn.commit()

    def create_session(self, session_id: str, original_filename: str) -> None:
        """Creates a new session record in the database."""
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions (session_id, created_at, original_filename, current_step) VALUES (?, ?, ?, 0)",
                (session_id, now, original_filename)
            )
            conn.commit()
            
        # Create session snapshot folder
        session_folder = os.path.join(self.db_dir, session_id)
        os.makedirs(session_folder, exist_ok=True)

    def save_action(
        self,
        session_id: str,
        step: int,
        action_name: str,
        action_args: Dict[str, Any],
        justification: str,
        code: str
    ) -> None:
        """Persists a cleaning step action to the audit trail log."""
        now = datetime.datetime.now().isoformat()
        args_str = json.dumps(action_args)
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO action_traces 
                   (session_id, step, action_name, action_args, justification, code, timestamp) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (session_id, step, action_name, args_str, justification, code, now)
            )
            # Update current step on session
            conn.execute(
                "UPDATE sessions SET current_step = ? WHERE session_id = ?",
                (step, session_id)
            )
            conn.commit()

    def save_profile(self, session_id: str, step: int, profile: Dict[str, Any]) -> None:
        """Persists a dataset quality profile snapshot to the database."""
        now = datetime.datetime.now().isoformat()
        profile_str = json.dumps(profile)
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO profiles (session_id, step, profile_json, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, step, profile_str, now)
            )
            conn.commit()

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieves the list of actions recorded for a session, sorted by step ascending."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM action_traces WHERE session_id = ? ORDER BY step ASC",
                (session_id,)
            ).fetchall()
            
        history = []
        for r in rows:
            history.append({
                "step": r["step"],
                "action_name": r["action_name"],
                "action_args": json.loads(r["action_args"]),
                "justification": r["justification"],
                "code": r["code"],
                "timestamp": r["timestamp"]
            })
        return history

    def get_latest_profile(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the most recent statistical profile recorded for a session."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT profile_json FROM profiles WHERE session_id = ? ORDER BY step DESC LIMIT 1",
                (session_id,)
            ).fetchone()
            
        if row:
            return json.loads(row["profile_json"])
        return None

    def save_dataframe_snapshot(self, session_id: str, step: int, df: pd.DataFrame) -> str:
        """
        Saves a DataFrame state snapshot to disk in Parquet format.
        Parquet is fast, compressed, and preserves types natively.
        """
        session_folder = os.path.join(self.db_dir, session_id)
        os.makedirs(session_folder, exist_ok=True)
        file_path = os.path.join(session_folder, f"step_{step}.parquet")
        
        # Save to parquet
        df.to_parquet(file_path, index=False)
        return file_path

    def load_dataframe_snapshot(self, session_id: str, step: int) -> pd.DataFrame:
        """Loads a DataFrame state snapshot from disk parquet file."""
        file_path = os.path.join(self.db_dir, session_id, f"step_{step}.parquet")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"State snapshot not found for session {session_id} at step {step}.")
        return pd.read_parquet(file_path)

    def delete_session(self, session_id: str) -> None:
        """Deletes session database records and associated disk parquet snapshots."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM action_traces WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM profiles WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            
        session_folder = os.path.join(self.db_dir, session_id)
        if os.path.exists(session_folder):
            import shutil
            try:
                shutil.rmtree(session_folder)
            except Exception:
                pass

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Retrieves all sessions registered in the system."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM sessions ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
