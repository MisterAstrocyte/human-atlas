#!/usr/bin/env bash
# Make this app work when hosted under a subpath (GitHub Pages) as well as at a
# domain root (local serve, Vercel). Safe to run more than once.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
echo "==> Patching source for subpath hosting"
python3 - <<'PY'
import json, re, pathlib
def rw(p, fn):
    f = pathlib.Path(p); s = f.read_text(); n = fn(s)
    if n != s: f.write_text(n); print("   patched", p)
    else: print("   already ok", p)

def page(s):
    if 'const asset=' not in s:
        s = s.replace("export default function Home",
          "const asset=(p:string)=>`${import.meta.env.BASE_URL}${p}`.replace(/([^:])\\/{2,}/g,'$1/');\nexport default function Home", 1)
    for f in ('atlas.json','atlas-de.json','info-de.json'):
        s = s.replace(f"fetch('/models/{f}'", f"fetch(asset('models/{f}')")
    return s

def scene(s):
    old = "fetch(compressed?chunk.gzip!:chunk.url,{signal:abort.signal})"
    new = ("fetch(`${import.meta.env.BASE_URL}${(compressed?chunk.gzip!:chunk.url)"
           ".replace(/^\\//,'')}`.replace(/([^:])\\/{2,}/g,'$1/'),{signal:abort.signal})")
    return s.replace(old, new) if old in s else s

def vite(s):
    return s if 'base:process.env.BASE_PATH' in s else s.replace(
        "export default defineConfig({root:", "export default defineConfig({base:process.env.BASE_PATH||'/',root:")

def tsc(s):
    return s if '"vite/client"' in s else s.replace('"types": [', '"types": [\n      "vite/client",', 1)

rw('app/page.tsx', page); rw('app/scene.tsx', scene)
rw('vite.config.ts', vite); rw('tsconfig.json', tsc)

# belt and braces: make the chunk URLs inside atlas.json relative
p = pathlib.Path('public/models/atlas.json'); a = json.loads(p.read_text()); changed = False
for c in a.get('chunks', []):
    for k in ('url','gzip'):
        if isinstance(c.get(k), str) and c[k].startswith('/'):
            c[k] = c[k].lstrip('/'); changed = True
if changed: p.write_text(json.dumps(a, separators=(',',':'))); print("   made chunk URLs relative in atlas.json")
else: print("   chunk URLs already relative")
PY
echo "==> Type-check and build"
npm run check
BASE_PATH="/human-atlas/" npm run build
echo "==> Verifying built output references the subpath"
grep -q '/human-atlas/assets/' dist/index.html && echo "   index.html OK"
echo "==> Committing"
git add -A
git commit -m "Serve models correctly from GitHub Pages subpath" || echo "   nothing to commit"
git push
echo
echo "Pushed. Watch the Actions tab; the site updates in a few minutes."
echo "Then reload with Ctrl+Shift+R."
