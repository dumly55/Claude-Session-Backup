# Claude Session Backup

## Why this exists

I renamed and moved around some project folders and found that a Claude
Code chat session I'd had in one of them had vanished — it no longer showed
up in `claude --resume`, and there was no way to get back to that history.

This happens because Claude Code doesn't store sessions by name or content —
it keys each session's transcript to an encoded copy of the project folder's
*path* (under `~/.claude/projects/<encoded-path>/`). The encoding is derived
from the exact folder path at the time the session ran. Rename or move that
folder afterward and the path no longer matches anything, so the session
becomes orphaned: the transcript file still exists on disk, but Claude Code
has no way to associate it with the folder anymore.

I built this project to find a way around that: back up every transcript to
a location that isn't tied to any project path, and provide a way to
re-associate a backed-up transcript with a folder (including a renamed or
moved one) so it becomes resumable again.

These two scripts back up every session transcript to a path-independent
location as it ends, and let you restore a transcript back into a
(possibly renamed) folder so it shows up again for `--resume`.

## How it works

- **`backup_session.py`** — registered as a global `SessionEnd` hook. On
  every session end, Claude Code passes it a JSON payload on stdin
  (`session_id`, `transcript_path`, `cwd`, `exit_reason`). The script copies
  the transcript into `backups/<session_id>.jsonl` and appends a record to
  `backups/index.jsonl` so you can look up which session belongs to which
  project.
- **`restore_session.py`** — given a `session_id` and a target folder,
  reproduces Claude Code's path-encoding scheme, copies the backed-up
  transcript into the matching `~/.claude/projects/<encoded-path>/`
  directory, and prints the `cd` + `claude --resume` command to run.

The `backups/` folder (real transcripts and `index.jsonl`) is gitignored —
it contains conversation history and local file paths, so it never leaves
your machine.

## Setup

Add the hook to your global `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python \"/path/to/Claude Session Backup/backup_session.py\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

From then on, every session gets backed up automatically when it ends.

## Restoring a session

```
python restore_session.py <session-id> [target_dir]
```

If `target_dir` is omitted, the current directory is used.

### Example (synthetic data)

Say `backups/index.jsonl` contains:

```json
{"session_id": "demo-1234", "cwd": "C:\\Users\\alice\\projects\\myapp", "transcript_path": "C:\\Users\\alice\\.claude\\projects\\c--Users-alice-projects-myapp\\demo-1234.jsonl", "exit_reason": "clear", "backed_up_at": "2026-01-15T10:32:00+00:00"}
```

The project folder `myapp` later gets renamed to `myapp-v2`. To bring the
session back:

```
$ python restore_session.py demo-1234 "C:\Users\alice\projects\myapp-v2"
Restored session demo-1234 into: C:\Users\alice\.claude\projects\c--Users-alice-projects-myapp-v2\demo-1234.jsonl
Computed project key: c--Users-alice-projects-myapp-v2
Now run: cd "C:\Users\alice\projects\myapp-v2" && claude --resume
```

`myapp-v2` now shows the session in `claude --resume` even though it was
originally recorded under the old folder name.

## Caveats

- The path-encoding rule in `restore_session.py` was reverse-engineered by
  inspecting existing `~/.claude/projects/` folder names, not from official
  documentation — if Claude Code changes its encoding scheme, the computed
  key may need adjustment. Compare against real folder names under
  `~/.claude/projects/` if a restored session doesn't show up.
