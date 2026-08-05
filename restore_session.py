#!/usr/bin/env python3
"""Restore a backed-up Claude Code session into a (possibly renamed/moved)
project folder so `claude --resume` can find it again.

Usage:
    python restore_session.py <session-id> [target_dir]

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
        print("Usage: python restore_session.py <session-id> [target_dir]")
        sys.exit(1)

    session_id = sys.argv[1]
    target_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path.cwd().resolve()

    backup_file = BACKUP_DIR / f"{session_id}.jsonl"
    if not backup_file.exists():
        print(f"No backup found for session {session_id} in {BACKUP_DIR}")
        print("Check backups/index.jsonl to find the right session-id.")
        sys.exit(1)

    encoded = encode_project_path(str(target_dir))
    projects_dir = Path.home() / ".claude" / "projects" / encoded
    projects_dir.mkdir(parents=True, exist_ok=True)

    dest = projects_dir / f"{session_id}.jsonl"
    shutil.copy2(backup_file, dest)

    print(f"Restored session {session_id} into: {dest}")
    print(f"Computed project key: {encoded}")
    print(f"Now run: cd \"{target_dir}\" && claude --resume")
    print("(If it doesn't show up, Claude Code's real path-encoding may differ")
    print(" slightly from the rule reproduced here — compare against folder")
    print(f" names already under {projects_dir.parent}.)")


if __name__ == "__main__":
    main()
