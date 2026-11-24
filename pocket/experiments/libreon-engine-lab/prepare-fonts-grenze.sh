#!/usr/bin/env bash
# Instala a fonte de titulo Grenze Gotisch OFL no motor LibreOfficeKit.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
BASE="$ROOT/upstream-libreon/third_party/lok/assets"
FONT_DIR="$BASE/unpack/user/fonts"
LICENSE_DIR="$BASE/licenses/grenze-gotisch"
test -d "$FONT_DIR" || { echo "Diretorio de fontes LOK ausente" >&2; exit 1; }
mkdir -p "$LICENSE_DIR"
fetch_checked() {
 local filename="$1" expected="$2" dest="$3"
 curl -fL --retry 2 --silent --show-error --proto '=https' --tlsv1.2 \
   "https://raw.githubusercontent.com/google/fonts/main/ofl/grenzegotisch/$filename" -o "$dest"
 local actual
 actual="$(git hash-object "$dest")"
 test "$actual" = "$expected" || {
    echo "Hash Git inesperado: $filename $actual != $expected" >&2
    exit 1
 }
}
fetch_checked 'GrenzeGotisch%5Bwght%5D.ttf' \
    '5d093c0a18ebe84b594dd0175e435693d1a48c43' \
    "$FONT_DIR/GrenzeGotisch-Variable.ttf"
fetch_checked 'OFL.txt' \
    '03e84a8b44d4ec69dfe1a3e66481623c898c5a81' \
    "$LICENSE_DIR/OFL.txt"
echo "Grenze Gotisch com peso 500 Medium instalada no motor, com licença OFL."
