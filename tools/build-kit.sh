#!/usr/bin/env bash
# Package a kit folder's shippable artifacts into its public/ directory.
# Usage: build-kit.sh <kit-folder-name>   e.g. build-kit.sh fable-5-transcription-kit
set -euo pipefail

KIT="${1:?usage: build-kit.sh <kit-folder-name>}"
TOOLS_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="$TOOLS_DIR/$KIT"
PUB="$SRC/public"
MODEL="${KIT%-transcription-kit}"

[ -d "$SRC" ] || { echo "ERROR: no kit folder at $SRC" >&2; exit 1; }
for f in README.md transcription-prompt.txt validation.json; do
  [ -s "$SRC/$f" ] || { echo "ERROR: missing or empty $SRC/$f" >&2; exit 1; }
done

strip_frontmatter() {
  awk 'NR==1 && $0=="---" {infm=1; next}
       infm && $0=="---" {infm=0; next}
       !infm {print}' "$1"
}

# A kit must not ship without human-authored instructions.
BODY_NONWS="$(strip_frontmatter "$SRC/README.md" | tr -d '[:space:]')"
[ -n "$BODY_NONWS" ] || {
  echo "ERROR: README.md body is empty — the kit cannot ship without instructions" >&2
  exit 1
}

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

strip_frontmatter "$SRC/README.md" | sed '/./,$!d' > "$STAGE/README.md"
cp "$SRC/transcription-prompt.txt" "$STAGE/transcription-prompt.txt"
cp "$SRC/validation.json" "$STAGE/validation.json"

mkdir -p "$PUB"
rm -f "$PUB/$KIT.zip"
(cd "$STAGE" && zip -q "$PUB/$KIT.zip" README.md transcription-prompt.txt validation.json)
cp "$SRC/transcription-prompt.txt" "$PUB/$MODEL-transcription-prompt.txt"
cp "$SRC/validation.json" "$PUB/$MODEL-validation.json"

echo "Built $PUB/$KIT.zip"
echo "Synced $PUB/$MODEL-transcription-prompt.txt and $PUB/$MODEL-validation.json"
