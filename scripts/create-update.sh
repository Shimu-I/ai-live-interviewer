#!/bin/bash
#
# create-update.sh
#
# Packages a set of changed files (relative to the project root) into
# updates/update-XXX.zip, along with a manifest.json and a copy of
# install-update.sh. This is the script used when producing a new update
# for the user to download and apply.
#
# Usage:
#   ./scripts/create-update.sh "Description of this update" \
#       frontend/src/components/VoiceOrb.tsx:modify \
#       backend/src/modules/interviews/interview.service.ts:add \
#       backend/src/modules/export/transcript.service.ts:add
#
# Each file argument is "relative/path:action" where action is add|modify|remove.
# Run from the project root (ai-live-interviewer/).
#
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPDATES_DIR="$PROJECT_DIR/updates"
mkdir -p "$UPDATES_DIR"

if [ $# -lt 2 ]; then
  echo "Usage: $0 \"description\" path:action [path:action ...]" >&2
  exit 1
fi

DESCRIPTION="$1"
shift

# Determine next update number
LAST_NUM=0
for d in "$UPDATES_DIR"/update-*; do
  [ -d "$d" ] || continue
  n=$(basename "$d" | sed -E 's/update-0*([0-9]+).*/\1/')
  if [ "$n" -gt "$LAST_NUM" ] 2>/dev/null; then LAST_NUM=$n; fi
done
NEXT_NUM=$((LAST_NUM + 1))
UPDATE_ID=$(printf "%03d" "$NEXT_NUM")

STAGE_DIR="$UPDATES_DIR/update-$UPDATE_ID"
FILES_DIR="$STAGE_DIR/files"
rm -rf "$STAGE_DIR"
mkdir -p "$FILES_DIR"

MANIFEST="$STAGE_DIR/manifest.json"
{
  echo "{"
  echo "  \"update\": \"$UPDATE_ID\","
  echo "  \"description\": \"$DESCRIPTION\","
  echo "  \"files\": ["
} > "$MANIFEST"

FIRST=1
for entry in "$@"; do
  rel_path="${entry%%:*}"
  action="${entry##*:}"

  if [ "$FIRST" -eq 0 ]; then echo "," >> "$MANIFEST"; fi
  FIRST=0
  printf '    { "path": "%s", "action": "%s" }' "$rel_path" "$action" >> "$MANIFEST"

  if [ "$action" != "remove" ]; then
    SRC="$PROJECT_DIR/$rel_path"
    DEST="$FILES_DIR/$rel_path"
    mkdir -p "$(dirname "$DEST")"
    cp "$SRC" "$DEST"
  fi
done

{
  echo ""
  echo "  ]"
  echo "}"
} >> "$MANIFEST"

cp "$PROJECT_DIR/scripts/install-update.sh" "$STAGE_DIR/install-update.sh"
chmod +x "$STAGE_DIR/install-update.sh"

cd "$UPDATES_DIR"
zip -r "update-$UPDATE_ID.zip" "update-$UPDATE_ID" > /dev/null

echo "Created $UPDATES_DIR/update-$UPDATE_ID.zip"
