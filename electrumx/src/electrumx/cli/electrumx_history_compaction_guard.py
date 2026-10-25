#!/usr/bin/env python3

"""Check whether the legacy ElectrumX history DB needs compaction.

History DB versions 0 and 1 use an unsigned two-byte flush ID.  This guard
keeps the server away from that on-disk limit and also detects an interrupted
compaction before ElectrumX opens the database normally.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Any

from electrumx.server.storage import db_class


COMPACTION_REQUIRED = 75
DEFAULT_THRESHOLD = 50_000
MAX_FLUSH_ID = 65_535
STATE_KEY = b"state\0\0"


def parse_threshold(raw_value: str | None) -> int:
    """Return a safe pre-overflow threshold from the environment value."""
    if raw_value is None or not raw_value.strip():
        return DEFAULT_THRESHOLD
    try:
        threshold = int(raw_value)
    except ValueError as exc:
        raise ValueError("HISTORY_COMPACTION_THRESHOLD must be an integer") from exc
    if not 1 <= threshold < MAX_FLUSH_ID:
        raise ValueError(
            f"HISTORY_COMPACTION_THRESHOLD must be between 1 and {MAX_FLUSH_ID - 1}"
        )
    return threshold


def parse_history_state(raw_state: bytes | None) -> dict[str, Any] | None:
    """Parse and minimally validate the state stored in the history DB."""
    if raw_state is None:
        return None
    try:
        state = ast.literal_eval(raw_state.decode("utf-8"))
    except (SyntaxError, UnicodeDecodeError, ValueError) as exc:
        raise ValueError("history DB state is not valid") from exc
    if not isinstance(state, dict):
        raise ValueError("history DB state is not a dictionary")
    flush_count = state.get("flush_count")
    if not isinstance(flush_count, int) or isinstance(flush_count, bool) or flush_count < 0:
        raise ValueError("history DB flush_count is missing or invalid")
    comp_cursor = state.get("comp_cursor", -1)
    if not isinstance(comp_cursor, int) or isinstance(comp_cursor, bool):
        raise ValueError("history DB comp_cursor is invalid")
    return state


def compaction_reason(state: dict[str, Any] | None, threshold: int) -> str | None:
    """Describe why compaction is required, or return None when it is safe."""
    if state is None:
        return None
    comp_cursor = int(state.get("comp_cursor", -1))
    if comp_cursor != -1:
        return f"an interrupted compaction is recorded at cursor {comp_cursor:,}"
    flush_count = int(state["flush_count"])
    if flush_count >= threshold:
        return f"flush count {flush_count:,} reached threshold {threshold:,}"
    return None


def read_history_state(db_directory: Path, engine_name: str) -> dict[str, Any] | None:
    """Read history state without creating a database that does not exist."""
    history_directory = db_directory / "hist"
    if not history_directory.exists():
        return None
    if not db_directory.is_dir():
        raise ValueError(f"DB_DIRECTORY is not a directory: {db_directory}")

    original_directory = Path.cwd()
    database = None
    try:
        os.chdir(db_directory)
        storage_class = db_class(engine_name)
        database = storage_class("hist", False)
        return parse_history_state(database.get(STATE_KEY))
    finally:
        try:
            if database is not None:
                database.close()
        finally:
            os.chdir(original_directory)


def main() -> int:
    try:
        db_directory_raw = os.environ.get("DB_DIRECTORY")
        if not db_directory_raw:
            raise ValueError("DB_DIRECTORY is not set")
        threshold = parse_threshold(os.environ.get("HISTORY_COMPACTION_THRESHOLD"))
        state = read_history_state(
            Path(db_directory_raw), os.environ.get("DB_ENGINE", "leveldb")
        )
        reason = compaction_reason(state, threshold)
    except Exception as exc:
        print(f"History compaction guard failed: {exc}", file=sys.stderr)
        return 1

    if state is None:
        print("History compaction guard: no existing history state; startup is safe")
        return 0

    flush_count = int(state["flush_count"])
    if reason:
        print(f"History compaction required: {reason}")
        return COMPACTION_REQUIRED

    print(
        f"History compaction guard: flush count {flush_count:,} is below "
        f"threshold {threshold:,}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
