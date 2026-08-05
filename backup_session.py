#!/usr/bin/env python3
"""Claude Code SessionEnd hook: copies the transcript to a path-independent
backup folder so renaming/moving a project directory can never lose history.

Registered globally in ~/.claude/settings.json under hooks.SessionEnd.
"""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKUP_DIR = SCRIPT_DIR / "backups"
INDEX_FILE = BACKUP_DIR / "index.jsonl"
ERROR_LOG = BACKUP_DIR / "errors.log"


def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        payload = json.load(sys.stdin)
        session_id = payload.get("session_id", "unknown")
        transcript_path = payload.get("transcript_path")
        cwd = payload.get("cwd")
        exit_reason = payload.get("exit_reason")

        if transcript_path and Path(transcript_path).exists():
            shutil.copy2(transcript_path, BACKUP_DIR / f"{session_id}.jsonl")

        with open(INDEX_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "session_id": session_id,
                "cwd": cwd,
                "transcript_path": transcript_path,
                "exit_reason": exit_reason,
                "backed_up_at": datetime.now(timezone.utc).isoformat(),
            }) + "\n")
    except Exception as e:
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()} {e}\n")


if __name__ == "__main__":
    main()
