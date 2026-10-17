#!/usr/bin/env python3
"""Claude Code SessionEnd hook: copies the transcript to a path-independent
backup folder so renaming/moving a project directory can never lose history.

Backups are named after the chat title, e.g.
    backups/Add login page and README [3c9e1a42-7b5d-4f08-9e61-2d4a8c0b7f13].jsonl

Registered globally in ~/.claude/settings.json under hooks.SessionEnd.
"""
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKUP_DIR = SCRIPT_DIR / "backups"
INDEX_FILE = BACKUP_DIR / "index.jsonl"
ERROR_LOG = BACKUP_DIR / "errors.log"


def chat_title(transcript_path):
    # Claude Code stores the chat title in the transcript as "ai-title"
    # records, plus "custom-title" if you renamed the chat yourself. The
    # title can change mid-session, so the last one wins.
    ai = custom = None
    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            if '"ai-title"' not in line and '"custom-title"' not in line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") == "ai-title":
                ai = d.get("aiTitle") or ai
            elif d.get("type") == "custom-title":
                custom = d.get("customTitle") or custom
    return custom or ai


def backup_name(title, session_id):
    # Strip characters Windows won't allow in file names (and brackets,
    # which restore_session.py uses to find the session id).
    safe = re.sub(r"[/\\]", "-", title or "")
    safe = re.sub(r'[<>:"|?*\[\]\x00-\x1f]', "", safe).strip(" .")[:80]
    return f"{safe} [{session_id}].jsonl" if safe else f"{session_id}.jsonl"


def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        payload = json.load(sys.stdin)
        session_id = payload.get("session_id", "unknown")
        transcript_path = payload.get("transcript_path")
        cwd = payload.get("cwd")
        exit_reason = payload.get("exit_reason")
        title = None

        if transcript_path and Path(transcript_path).exists():
            title = chat_title(transcript_path)
            dest = BACKUP_DIR / backup_name(title, session_id)
            shutil.copy2(transcript_path, dest)
            # Remove copies saved under an older title for this session.
            for old in BACKUP_DIR.glob(f"*{session_id}*.jsonl"):
                if old != dest:
                    old.unlink()

        with open(INDEX_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "session_id": session_id,
                "title": title,
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
