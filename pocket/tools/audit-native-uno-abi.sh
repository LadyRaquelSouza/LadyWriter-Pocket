#!/usr/bin/env bash
# Audita o motor Android distribuído, sem recompilar e sem invocar métodos.
# Não afirma que símbolos exportados garantem acesso a XTextDocument.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APK_URL="https://github.com/jainiakhil/Libreon/releases/download/v0.9.5-beta.5/Libreon-0.9.5-beta.5-arm64-v8a.apk"
APK_HASH="6c973344e01bcc987ad8cc16bfea04550aa9b3aa6e6d258af235554541b06ed5"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
command -v readelf >/dev/null
command -v unzip >/dev/null
command -v curl >/dev/null
curl --fail --location --retry 2 --silent --show-error "$APK_URL" -o "$tmp/upstream.apk"
printf '%s  %s\n' "$APK_HASH" "$tmp/upstream.apk" | sha256sum -c -
unzip -Z1 "$tmp/upstream.apk" | grep '^lib/arm64-v8a/.*\.so$' > "$tmp/libs.txt"
echo "Bibliotecas do APK original:"
cat "$tmp/libs.txt"
while IFS= read -r path; do
  unzip -p "$tmp/upstream.apk" "$path" > "$tmp/$(basename "$path")"
done < "$tmp/libs.txt"
echo
echo "Procurando entradas JNI, LOK e potenciais mecanismos UNO públicos:"
for path in "$tmp/"*.so; do
  echo "== $(basename "$path") =="
  readelf -Ws --wide "$path" 2>/dev/null \
    | awk '$7!="UND" && ($8 ~ /Java_org_libreoffice|Java_.*LOActivity|lok_init|uno_|getLibreOfficeKitHandle/) { print $8 }' \
    | sort -u | head -80 || true
done
echo
echo "ATENÇÃO: este relatório apenas lista símbolos exportados, quando presentes."
echo "Não demonstra acesso ao documento ativo e não habilita edição de variáveis."
