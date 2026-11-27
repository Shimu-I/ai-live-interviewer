#!/bin/bash
#
# install-update.sh
#
# Applies an update-XXX package to your master ai-live-interviewer project folder.
# Run this from inside the extracted update-XXX/ directory (it expects a sibling
# "files/" folder and a "manifest.json" in the same directory as this script).
#
# Usage:
#   ./install-update.sh
#   PROJECT_DIR=/custom/path ./install-update.sh
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$SCRIPT_DIR/manifest.json"
FILES_DIR="$SCRIPT_DIR/files"
PROJECT_DIR="${PROJECT_DIR:-$HOME/ai-live-interviewer}"

if [ ! -f "$MANIFEST" ]; then
  echo "ERROR: manifest.json not found next to this script." >&2
  exit 1
fi

if [ ! -d "$PROJECT_DIR" ]; then
  echo "ERROR: Master project folder not found at $PROJECT_DIR" >&2
  echo "Set PROJECT_DIR=/path/to/ai-live-interviewer and re-run." >&2
  exit 1
fi

UPDATE_ID=$(grep -o '"update"[[:space:]]*:[[:space:]]*"[^"]*"' "$MANIFEST" | sed -E 's/.*"([^"]+)"$/\1/')
UPDATE_ID="${UPDATE_ID:-unknown}"
DESCRIPTION=$(grep -o '"description"[[:space:]]*:[[:space:]]*"[^"]*"' "$MANIFEST" | sed -E 's/.*"([^"]+)"$/\1/')

BACKUP_DIR="$PROJECT_DIR/backups/update-$UPDATE_ID"
mkdir -p "$BACKUP_DIR"

echo "======================================================"
echo " Applying update-$UPDATE_ID"
echo " $DESCRIPTION"
echo " Target project: $PROJECT_DIR"
echo "======================================================"

# Extract each "path" entry from manifest.json (simple line-based parse; manifest
# is intentionally kept flat/simple so this works without a JSON tool dependency).
PATHS=$(grep -o '"path"[[:space:]]*:[[:space:]]*"[^"]*"' "$MANIFEST" | sed -E 's/.*"([^"]+)"$/\1/')

ADDED=0
MODIFIED=0

while IFS= read -r rel_path; do
  [ -z "$rel_path" ] && continue

  SRC="$FILES_DIR/$rel_path"
  DEST="$PROJECT_DIR/$rel_path"

  if [ ! -f "$SRC" ]; then
    echo "  ! Skipping $rel_path (not found in files/)"
    continue
  fi

  if [ -f "$DEST" ]; then
    BACKUP_TARGET="$BACKUP_DIR/$rel_path"
    mkdir -p "$(dirname "$BACKUP_TARGET")"
    cp "$DEST" "$BACKUP_TARGET"
    echo "  ~ modified: $rel_path (backed up)"
    MODIFIED=$((MODIFIED + 1))
  else
    echo "  + added:    $rel_path"
    ADDED=$((ADDED + 1))
  fi

  mkdir -p "$(dirname "$DEST")"
  cp "$SRC" "$DEST"
done <<< "$PATHS"

echo "------------------------------------------------------"
echo "Update $UPDATE_ID applied: $ADDED added, $MODIFIED modified."
echo "Backups (if any) saved under: $BACKUP_DIR"
echo "------------------------------------------------------"
