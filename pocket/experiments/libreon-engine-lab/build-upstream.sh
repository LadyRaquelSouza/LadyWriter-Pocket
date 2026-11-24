#!/usr/bin/env bash
# Compilacao de APK upstream para arm64 no runner do Actions.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SOURCE="$ROOT/upstream-libreon"
test -f "$SOURCE/app/build.gradle.kts" || { echo "Fonte upstream ausente" >&2; exit 1; }
test -f "$SOURCE/third_party/lok/jniLibs/arm64-v8a/liblo-native-code.so" || {
    echo "LOK nao preparado" >&2; exit 1;
}

# PDFium e arquivos de cabecalho oficiais sao obtidos pelo script upstream.
# Esse projeto usa uma ponte JNI propria separada do engine LOK.
cd "$SOURCE"
bash scripts/fetch-pdfium.sh

# Experimento de uma ABI (a do Moto G05); nao construir artefato x86_64.
python3 - <<'PY'
from pathlib import Path
app = Path("app/build.gradle.kts")
s = app.read_text()
a = 'include("arm64-v8a", "x86_64")'
assert a in s, "O filtro ABI mudou na fonte upstream"
app.write_text(s.replace(a, 'include("arm64-v8a")'))
pdf = Path("engine-pdf/build.gradle.kts")
s = pdf.read_text()
a = 'listOf("arm64-v8a", "x86_64")'
assert s.count(a) >= 2, "A configuracao ABI do PDF mudou"
pdf.write_text(s.replace(a, 'listOf("arm64-v8a")'))
PY

# Compactar apenas a casca Android: preserva a interface e o motor do Collabora.
python3 "$ROOT/pocket/experiments/libreon-engine-lab/compact-ui.py"

# Estilos nomeados do ODT: lista e busca no shell, aplicacao via comando UNO.
python3 "$ROOT/pocket/experiments/libreon-engine-lab/patch-odt-style-selector.py"

# Atalhos para campos Writer e atualizacao explicita de indices/sumario.
python3 "$ROOT/pocket/experiments/libreon-engine-lab/patch-fields-indexes.py"

# LadyWriter Pocket: nome, ícone, telas e créditos em vez da marca do app de laboratório.
python3 "$ROOT/pocket/experiments/libreon-engine-lab/patch-branding.py"

# Corrigir fonte invisivel no LOK: Fontconfig privado do Pocket, nao do Collabora.
python3 "$ROOT/pocket/experiments/libreon-engine-lab/patch-fontconfig-runtime.py"

# Substituir controles genericos por barra editorial e deixar pt-BR no motor e no shell.
python3 "$ROOT/pocket/experiments/libreon-engine-lab/patch-editorial-ux.py"
python3 "$ROOT/pocket/experiments/libreon-engine-lab/patch-localize-ptbr.py"
python3 "$ROOT/pocket/experiments/libreon-engine-lab/patch-variable-inventory.py"
python3 "$ROOT/pocket/experiments/libreon-engine-lab/patch-variable-engine-probe.py"
python3 "$ROOT/pocket/experiments/libreon-engine-lab/patch-native-command-probe.py"

# Identidade, versionCode e assinatura sao fixados a partir de GitHub Secrets.
# Falha fechada se a chave nao foi configurada; nunca volta ao debug efemero.
python3 "$ROOT/pocket/experiments/libreon-engine-lab/patch-stable-signing.py"
bash ./gradlew --no-daemon --stacktrace --max-workers=2 :app:assembleDebug
echo "APK(s) localizados:"
find app/build/outputs/apk/debug -name '*.apk' -printf '%p %s bytes\n'
