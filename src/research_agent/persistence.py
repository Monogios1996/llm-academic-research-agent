"""SQLite-backed LangGraph checkpoint persistence.

The Unit 6 design calls for inspectable persistent workflow state. This module
keeps the storage concern separate from orchestration and uses LangGraph's
official SQLite checkpointer for lightweight local persistence.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


class SQLiteCheckpointStore:
    """Own a SQLite connection and expose a LangGraph checkpoint saver."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(
            self.path,
            check_same_thread=False,
        )
        self.saver = SqliteSaver(self.connection)

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self.connection.close()
