#!/bin/sh
# Download Pyodide (Python for the browser) into web/public/pyodide.
# Only the core files are kept: about 14 MB.
set -e
VERSION=0.26.4
ROOT=$(cd "$(dirname "$0")/.." && pwd)
DEST="$ROOT/web/public/pyodide"
TMP=$(mktemp -d)
cd "$TMP"
npm pack "pyodide@$VERSION" --silent >/dev/null
tar -xzf "pyodide-$VERSION.tgz"
mkdir -p "$DEST"
for f in pyodide.js pyodide.asm.js pyodide.asm.wasm python_stdlib.zip pyodide-lock.json; do
    cp "package/$f" "$DEST/"
done
cp package/README.md "$DEST/README.md"
echo "Pyodide $VERSION is in $DEST"
rm -rf "$TMP"
