#!/usr/bin/env bash
# POC de fidelidade tipografica: inclui Arapey no motor LOK empacotado.
# Fontes e licenca baixadas de google/fonts (SIL OFL) durante o GitHub Actions.
# NAO baixa nada em tempo de execucao no Android e NAO inclui fontes no Git.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT="$ROOT/upstream-libreon/third_party/lok/assets"
FONT_DIR="$OUT/unpack/user/fonts"
LICENSE_DIR="$OUT/licenses/arapey"

test -d "$OUT/unpack/user/fonts" || {
  echo "Diretorio original de fontes do motor LOK ausente" >&2
  exit 1
}
mkdir -p "$FONT_DIR" "$LICENSE_DIR"

BASE="https://raw.githubusercontent.com/google/fonts/main/ofl/arapey"
# Valores de SHA-1 de blobs Git obtidos do repositorio google/fonts
# na consulta de 23/11/2026. git hash-object verifica tambem tamanho/conteudo.
download_checked() {
  local filename="$1"
  local sha_git_expected="$2"
  local destination="$3"
  curl --fail --location --retry 2 --silent --show-error \
    --proto '=https' --tlsv1.2 "$BASE/$filename" -o "$destination"
  local actual
  actual="$(git hash-object "$destination")"
  if [ "$actual" != "$sha_git_expected" ]; then
    echo "Integridade falhou: $filename ($actual != $sha_git_expected)" >&2
    exit 1
  fi
}

download_checked "Arapey-Regular.ttf" \
  "62d178f6155c75e6f723ba42e4e429787927ff65" \
  "$FONT_DIR/Arapey-Regular.ttf"
download_checked "Arapey-Italic.ttf" \
  "5ade9b41ad231bedfb20c84e03c37cdce9c7f46c" \
  "$FONT_DIR/Arapey-Italic.ttf"
download_checked "OFL.txt" \
  "395582fe2bb32c198010fe8b77cd3301513fe9de" \
  "$LICENSE_DIR/OFL.txt"

# Este teste nao substitui uma biblioteca de fontes importadas via SAF.

# Segunda familia pedida pela autora: Grenze Gotisch (Google Fonts, SIL OFL).
# O arquivo publicado e uma fonte VARIAVEL. Para compatibilidade com o LOK
# compilado, tambem geramos uma instancia estatica Medium (peso 500).
GRENZE_BASE="https://raw.githubusercontent.com/google/fonts/main/ofl/grenzegotisch"
GRENZE_FILE="$FONT_DIR/GrenzeGotisch-Variable.ttf"
GRENZE_LICENSE="$OUT/licenses/grenze-gotisch/OFL.txt"
mkdir -p "$(dirname "$GRENZE_LICENSE")"
curl --fail --location --retry 2 --silent --show-error \
  --proto '=https' --tlsv1.2 \
  "$GRENZE_BASE/GrenzeGotisch%5Bwght%5D.ttf" -o "$GRENZE_FILE"
test "$(git hash-object "$GRENZE_FILE")" = "5d093c0a18ebe84b594dd0175e435693d1a48c43" || {
  echo "Integridade da fonte Grenze Gotisch falhou" >&2
  exit 1
}
curl --fail --location --retry 2 --silent --show-error \
  --proto '=https' --tlsv1.2 \
  "$GRENZE_BASE/OFL.txt" -o "$GRENZE_LICENSE"
test "$(git hash-object "$GRENZE_LICENSE")" = "03e84a8b44d4ec69dfe1a3e66481623c898c5a81" || {
  echo "Integridade da licenca Grenze Gotisch falhou" >&2
  exit 1
}

# Instancia estaticamente o wght=500, evitando depender de suporte a fontes
# variaveis no fontconfig/LibreOfficeKit. FontTools e instalado no runner apenas.
VENV_DIR="$(mktemp -d)"
trap 'rm -rf "$VENV_DIR"' EXIT
python3 -m venv "$VENV_DIR/venv"
"$VENV_DIR/venv/bin/pip" --disable-pip-version-check -q install 'fonttools>=4.50,<5'
"$VENV_DIR/venv/bin/python" - "$GRENZE_FILE" "$FONT_DIR/GrenzeGotisch-Medium.ttf" <<'PY'
from pathlib import Path
import sys
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

source, target = map(Path, sys.argv[1:3])
font = TTFont(source)
assert "fvar" in font, "Fonte esperada nao e variavel"
font = instantiateVariableFont(font, {"wght": 500}, inplace=True)
assert "fvar" not in font, "Instancia precisa ser estatica"
font["OS/2"].usWeightClass = 500
names = font["name"]
for name_id, label in {
    1: "Grenze Gotisch",
    2: "Medium",
    4: "Grenze Gotisch Medium",
    6: "GrenzeGotisch-Medium",
    16: "Grenze Gotisch",
    17: "Medium",
}.items():
    names.setName(label, name_id, 3, 1, 0x0409)
    names.setName(label, name_id, 1, 0, 0)
font.save(target)
print(f"Instancia estatica {target.name} criada: {target.stat().st_size} bytes")

# ODTs criados no Writer podem pedir "Grenze Gotisch Medium" como FAMILIA,
# enquanto a fonte original se identifica como familia "Grenze Gotisch"
# e subfamilia "Medium". Nao alterar o manuscrito nem a fonte original.
# Adicionar um segundo rosto, com os mesmos contornos do peso 500, exposto
# como familia literal "Grenze Gotisch Medium" + estilo Regular.
# O alias tem nome PostScript unico para evitar colisao com a instancia normal.
alias_target = target.with_name("GrenzeGotisch-Medium-FamilyAlias.ttf")
alias = TTFont(target)
alias["OS/2"].usWeightClass = 400  # estilo Regular da familia alias; glifos permanecem wght=500
alias["OS/2"].fsSelection = (alias["OS/2"].fsSelection | 0x40) & ~(0x01 | 0x20)
alias_names = {
    1: "Grenze Gotisch Medium",
    2: "Regular",
    4: "Grenze Gotisch Medium",
    6: "GrenzeGotischMedium-PocketAlias",
    16: "Grenze Gotisch Medium",
    17: "Regular",
}
for name_id, label in alias_names.items():
    alias["name"].setName(label, name_id, 3, 1, 0x0409)
    alias["name"].setName(label, name_id, 1, 0, 0)
alias.save(alias_target)
alias.close()

# Conferencia antes do APK: cada nome requerido precisa estar na familia,
# nao somente no "full font name" ou no nome do arquivo TTF.
for font_file, expected_family in (
    (target, "Grenze Gotisch"),
    (alias_target, "Grenze Gotisch Medium"),
):
    checked = TTFont(font_file)
    win_name = checked["name"].getName(1, 3, 1, 0x0409)
    assert win_name is not None and win_name.toUnicode() == expected_family, (
        font_file, win_name, expected_family
    )
    assert "fvar" not in checked, "Fontes estaticas obrigatorias"
    checked.close()
    print(f"Familia validada: {expected_family} -> {font_file.name}")
PY

# A familia vista pelo Fontconfig e mais relevante que o nome do arquivo.
if command -v fc-scan >/dev/null 2>&1; then
  "$VENV_DIR/venv/bin/python" - "$FONT_DIR" <<'PY'
from pathlib import Path
import subprocess
import sys
directory = Path(sys.argv[1])
for filename, expected in (
    ("GrenzeGotisch-Medium.ttf", "Grenze Gotisch"),
    ("GrenzeGotisch-Medium-FamilyAlias.ttf", "Grenze Gotisch Medium"),
):
    path = directory / filename
    family = subprocess.check_output(
        ["fc-scan", "--format", "%{family}\\n", str(path)], text=True
    ).splitlines()[0]
    assert expected in family.split(","), (filename, expected, family)
    print("Fontconfig OK:", filename, family)
PY
fi

echo "Arapey e Grenze Gotisch (familia original + alias literal Medium) incorporadas ao motor."
du -h "$FONT_DIR"/GrenzeGotisch-*.ttf "$GRENZE_LICENSE"

du -h "$FONT_DIR"/Arapey-*.ttf "$LICENSE_DIR"/OFL.txt
