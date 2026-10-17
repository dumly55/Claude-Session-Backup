#!/usr/bin/env python3
"""Restore a backed-up Claude Code session into a (possibly renamed/moved)
project folder so `claude --resume` can find it again.

Usage:
    python restore_session.py <session-id or chat title> [target_dir]

The first argument can be the session id or any part of the chat title
(case-insensitive), matched against the file names in backups/.
If target_dir is omitted, the current working directory is used.
Run this from (or pass) the folder you want the session to resume into,
then cd there and run `claude --resume`.
"""
import re
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKUP_DIR = SCRIPT_DIR / "backups"


def encode_project_path(path: str) -> str:
    # Claude Code keys project folders by lowercasing the drive letter and
    # replacing every non-alphanumeric character in the path with '-'
    # (verified against existing ~/.claude/projects/ directory names, which
    # use a lowercase drive letter while preserving folder name casing).
    path = re.sub(r"^([A-Za-z]):", lambda m: m.group(1).lower() + ":", path)
    return re.sub(r"[^a-zA-Z0-9]", "-", path)


def main():
    if len(sys.argv) < 2:
        print("Usage: python restore_session.py <session-id or chat title> [target_dir]")
        sys.exit(1)

    query = sys.argv[1]
    target_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path.cwd().resolve()

    # Backups are named "<chat title> [<session-id>].jsonl" (or just
    # "<session-id>.jsonl" for untitled chats).
    matches = [p for p in BACKUP_DIR.glob("*.jsonl")
               if p.name != "index.jsonl" and query.lower() in p.stem.lower()]
    if not matches:
        print(f"No backup matching '{query}' in {BACKUP_DIR}")
        print("Look at the file names in backups/ to find the right chat.")
        sys.exit(1)
    if len(matches) > 1:
        print(f"'{query}' matches more than one backup — use the session id:")
        for p in sorted(matches):
            print(f"  {p.name}")
        sys.exit(1)

    backup_file = matches[0]
    session_id = backup_file.stem.rsplit("[", 1)[-1].rstrip("]")

    encoded = encode_project_path(str(target_dir))
    projects_dir = Path.home() / ".claude" / "projects" / encoded
    projects_dir.mkdir(parents=True, exist_ok=True)

    # Claude Code expects the transcript to be named after the session id.
    dest = projects_dir / f"{session_id}.jsonl"
    shutil.copy2(backup_file, dest)

    print(f"Found backup: {backup_file.name}")
    print(f"Restored session {session_id} into: {dest}")
    print(f"Computed project key: {encoded}")
    print(f"Now run: cd \"{target_dir}\" && claude --resume")
    print("(If it doesn't show up, Claude Code's real path-encoding may differ")
    print(" slightly from the rule reproduced here — compare against folder")
    print(f" names already under {projects_dir.parent}.)")


if __name__ == "__main__":
    main()
