#!/usr/bin/env bash
# Migrate this atlas to BodyParts3D / Anatomography 4.3.
# Usage:  bash scripts/migrate-43.sh /path/to/body_parts_3d_api/meshes
set -euo pipefail
SRC="${1:?Pass the folder containing the 4.3 .obj files (meshes/ from the 4.3 repo)}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$ROOT/.bp43-objs"

echo "==> 1/5  Normalising file names (FJ1234_BP..._FMA..._name.obj -> FJ1234.obj)"
rm -rf "$WORK"; mkdir -p "$WORK"
count=0
for f in "$SRC"/*.obj; do
  b="$(basename "$f")"; id="${b%%_*}"
  # skip Git LFS pointer files, which are ~130 bytes of text
  if head -c 40 "$f" | grep -q 'git-lfs'; then
    echo "!! $b is an LFS pointer, not geometry. Run: git lfs install && git lfs pull"; exit 1
  fi
  cp "$f" "$WORK/$id.obj"; count=$((count+1))
done
echo "    $count meshes staged"

echo "==> 2/5  Converting geometry (mm/Z-up -> m/Y-up, 16-bit normals, binary chunks)"
python3 "$ROOT/scripts/convert-anatomy.py" "$WORK" "$ROOT/data43/concepts43.json" "$ROOT/data43/systems43.json"

echo "==> 3/5  Simplifying meshes"
node "$ROOT/scripts/optimize-anatomy.mjs" atlas.json

echo "==> 4/5  Compressing chunks"
node "$ROOT/scripts/compress-models.mjs"

echo "==> 5/5  Installing German names and info box"
cp "$ROOT/data43/atlas-de.json" "$ROOT/public/models/atlas-de.json"
cp "$ROOT/data43/info-de.json"  "$ROOT/public/models/info-de.json"
rm -rf "$WORK"

node "$ROOT/scripts/validate-atlas.mjs"
echo
echo "Done. Now run:  npm run build && npx serve dist -l 3016"
