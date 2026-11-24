#!/usr/bin/env bash
# Experimento reprodutivel: usa fonte GPL do Libreon e bibliotecas correspondentes
# ao APK oficial, com SHA-256 fixado (binarios nao sao modificados).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
UPSTREAM_SHA="f1f8c95c7b2dfd8a26ccdbd5e17883b6c7cbfc09"
UPSTREAM_TAG="v0.9.5-beta.5"
APK_SHA256="6c973344e01bcc987ad8cc16bfea04550aa9b3aa6e6d258af235554541b06ed5"
APK_URL="https://github.com/jainiakhil/Libreon/releases/download/${UPSTREAM_TAG}/Libreon-0.9.5-beta.5-arm64-v8a.apk"
SOURCE="$ROOT/upstream-libreon"
mkdir -p "$ROOT"
git clone --depth=1 --branch="$UPSTREAM_TAG" https://github.com/jainiakhil/Libreon.git "$SOURCE"
ACTUAL_SHA="$(git -C "$SOURCE" rev-parse HEAD)"
test "$ACTUAL_SHA" = "$UPSTREAM_SHA" || {
    echo "Commit upstream inesperado: $ACTUAL_SHA (esperado $UPSTREAM_SHA)" >&2
    exit 1
}
echo "Fonte upstream verificada: $UPSTREAM_TAG@$UPSTREAM_SHA"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl --fail --location --retry 2 --silent --show-error "$APK_URL" -o "$TMP/upstream.apk"
echo "$APK_SHA256  $TMP/upstream.apk" | sha256sum -c -

echo "Bibliotecas nativas no APK original:"
unzip -Z1 "$TMP/upstream.apk" | grep '^lib/arm64-v8a/.*\.so$' || true
echo "Recursos do motor no APK original:"
unzip -Z1 "$TMP/upstream.apk" | grep '^assets/' | head -25 || true

unzip -q "$TMP/upstream.apk" 'lib/arm64-v8a/*' 'assets/*' -d "$TMP/extracted"
test -f "$TMP/extracted/lib/arm64-v8a/liblo-native-code.so" || {
    echo "APK nao contem liblo-native-code.so; verificacao de layout necessaria" >&2
    exit 1
}
test -d "$TMP/extracted/assets/dist" || {
    echo "APK nao contem recursos Collabora em assets/dist" >&2
    exit 1
}

# Bibliotecas do motor somente: o modulo PDF separado compila o proprio bridge JNI.
mkdir -p "$SOURCE/third_party/lok/jniLibs/arm64-v8a" "$SOURCE/third_party/lok/assets"
for lib in "$TMP/extracted/lib/arm64-v8a/"*.so; do
    case "$(basename "$lib")" in
        *pdf*|*Pdf*) echo "Separada para PDF: $(basename "$lib")";;
        *) cp "$lib" "$SOURCE/third_party/lok/jniLibs/arm64-v8a/";;
    esac
done
cp -a "$TMP/extracted/assets/." "$SOURCE/third_party/lok/assets/"

echo "Bibliotecas LOK preparadas:"
find "$SOURCE/third_party/lok/jniLibs/arm64-v8a" -type f -maxdepth 1 -printf '%f %s bytes\n'
du -sh "$SOURCE/third_party/lok" || true
echo "Preparacao de motor concluida, sem transferencia para o Garuda."
