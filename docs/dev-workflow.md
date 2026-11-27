# Dev Workflow: Ubuntu Setup & Update System

This describes how you work with Claude on this project across sessions without
ever having to recreate the folder structure or lose existing files.

## 1. One Master Project Folder

Everything lives in one place on your machine, e.g. `~/ai-live-interviewer/`. Claude
never regenerates this whole folder — it only ever ships **incremental updates**.

## 2. Python, Isolated

The primary stack (Next.js + NestJS + PostgreSQL) does not need Python. If/when
Python tooling is needed (data analysis, ML experiments, file processing scripts),
it lives isolated under `python/`, with its own virtual environment:

```bash
cd ai-live-interviewer/python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

This keeps the Node.js project and any Python tooling from ever colliding.

## 3. The Update System: ZIP + Manifest + Install Script

Every time Claude adds or changes files, it packages **only those files** as
`update-XXX.zip` (numbered sequentially) instead of resending the whole project.

### Contents of an update ZIP
```
update-XXX/
├── manifest.json          # what changed and why
├── files/                 # only new/modified files, in their real relative paths
│   ├── frontend/src/...
│   └── backend/src/...
└── install-update.sh      # applies this specific update
```

### manifest.json example
```json
{
  "update": "001",
  "description": "Phase 1: frontend/backend scaffolding + Prisma schema",
  "files": [
    { "path": "frontend/package.json", "action": "add" },
    { "path": "backend/prisma/schema.prisma", "action": "add" },
    { "path": "backend/src/modules/interviews/interview.service.ts", "action": "modify" }
  ]
}
```
`action` is one of `add`, `modify`, `remove`.

### How you apply an update
```bash
cd ~/Downloads            # wherever update-XXX.zip landed
unzip update-XXX.zip
cd update-XXX
./install-update.sh       # reads manifest, backs up, then copies files in
```

### What install-update.sh guarantees
1. Locates your master project folder (`$HOME/ai-live-interviewer` by default,
   overridable with `PROJECT_DIR=/path ./install-update.sh`).
2. Creates a timestamped backup of every file about to be touched, under
   `backups/update-XXX/`.
3. Copies only the files listed in the manifest — never wipes or recreates
   directories wholesale.
4. Prints a summary of what was added/modified/removed.
5. Never deletes files outside the manifest.

The reusable generic version of this script is at
`scripts/install-update.sh` and gets copied into every `update-XXX.zip` Claude
produces (with the manifest's file list baked in via the accompanying
`manifest.json` in the same ZIP).

### How Claude generates an update (for reference)
`scripts/create-update.sh` takes a list of changed file paths (relative to the
project root) plus a description, and produces `updates/update-XXX.zip` containing
the manifest, the files, and a copy of `install-update.sh`. See that script's
header comment for usage.

## 4. Never Destroy Existing Files

Rules Claude follows for every update:
- Only touch files explicitly listed in the manifest.
- Back up before overwrite.
- Additive by default — removals must be explicit `action: remove` entries, never
  implicit.
- Update `README.md`'s Progress Log and roadmap status table at the end of every
  step, in every update.
