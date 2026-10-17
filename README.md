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

I also wanted to be able to move a chat from one project folder into the
one I'm currently working in. Without this, the only way to bring an old
chat along as context was to convert it to a Markdown file and feed that
in. Now I can drop the whole session into the current folder and resume
it with its full history.

These two scripts back up every session transcript to a path-independent
location as it ends, and let you restore a transcript back into a
(possibly renamed) folder so it shows up again for `--resume`.

## How it works

- **`backup_session.py`** — registered as a global `SessionEnd` hook. On
  every session end, Claude Code passes it a JSON payload on stdin
  (`session_id`, `transcript_path`, `cwd`, `exit_reason`). The script reads
  the chat title out of the transcript and saves the copy as
  `backups/<chat title> [<session_id>].jsonl`, so you can tell which chat
  is which just from the file name. If the title changes later, the next
  backup replaces the old file. It also appends a record (including the
  title and the folder the session ran in) to `backups/index.jsonl`.
- **`restore_session.py`** — given a session id (or part of the chat title)
  and a target folder, reproduces Claude Code's path-encoding scheme, copies
  the backed-up transcript into the matching
  `~/.claude/projects/<encoded-path>/` directory, and prints the `cd` +
  `claude --resume` command to run.

Example of what `backups/` looks like:

```
backups/
  Add login page and README [3c9e1a42-7b5d-4f08-9e61-2d4a8c0b7f13].jsonl
  Fix chart colors [8f2b6d10-4c3e-4a97-b1d5-6e0f9a3c2b84].jsonl
  index.jsonl
```

## Privacy

The `backups/` folder is gitignored (along with any stray `*.jsonl` file) —
it contains full conversation history and local file paths, so it stays on
your machine and is never committed or pushed. Only the scripts and this
README are in the repository.

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

Run this from the `Claude Session Backup` folder:

```
python restore_session.py <session-id> "<target folder>"
```

- `<session-id>` is the id in square brackets at the end of the backup's
  file name. Part of the chat title works too (e.g. `"login page"`) as
  long as it only matches one backup.
- `"<target folder>"` is the project folder you want the chat to show up
  in. Keep the quotes. If you leave it out, the current directory is used.

### Example

Say you had a chat called **Add login page and README** that started in a
`recipe-app` project. You're now working in a `weather-dashboard` project
and want that chat there. Its backup is:

```
backups/Add login page and README [3c9e1a42-7b5d-4f08-9e61-2d4a8c0b7f13].jsonl
```

So you run:

```
python restore_session.py 3c9e1a42-7b5d-4f08-9e61-2d4a8c0b7f13 "C:\Users\alex\weather-dashboard"
```

Output:

```
Found backup: Add login page and README [3c9e1a42-7b5d-4f08-9e61-2d4a8c0b7f13].jsonl
Restored session 3c9e1a42-7b5d-4f08-9e61-2d4a8c0b7f13 into: C:\Users\alex\.claude\projects\c--Users-alex-weather-dashboard\3c9e1a42-7b5d-4f08-9e61-2d4a8c0b7f13.jsonl
Computed project key: c--Users-alex-weather-dashboard
Now run: cd "C:\Users\alex\weather-dashboard" && claude --resume
```

After that, the chat shows up in the session list for `weather-dashboard`
and you can pick up where you left off.

## Caveats

- The path-encoding rule in `restore_session.py` was reverse-engineered by
  inspecting existing `~/.claude/projects/` folder names, not from official
  documentation — if Claude Code changes its encoding scheme, the computed
  key may need adjustment. Compare against real folder names under
  `~/.claude/projects/` if a restored session doesn't show up.
