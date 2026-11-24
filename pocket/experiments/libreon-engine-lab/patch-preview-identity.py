#!/usr/bin/env python3
"""Identidade Android exclusiva para prévia pública, SEM chave privada.

Esta variante NÃO atualiza a instalação estável e nunca reutiliza o
applicationId dela. Gradle aplica sua assinatura debug temporária.
"""
from pathlib import Path
import os

file = Path("app/build.gradle.kts")
source = file.read_text(encoding="utf-8")
flavor = os.getenv("POCKET_PREVIEW_FLAVOR", "baseline")
if flavor not in ("baseline", "ux"):
    raise SystemExit("Flavor preview não permitido")
package = "com.ladyrachelsouza.ladywriter.pocket.preview" + (".ux" if flavor == "ux" else "")
for anchor in (
    'applicationId = "dev.libreon.app"',
    'versionCode = 10',
    'versionName = "0.9.5-beta.5"',
):
    if source.count(anchor) != 1:
        raise SystemExit(f"API upstream mudou: {anchor}")

source = source.replace(
    'applicationId = "dev.libreon.app"',
    f'applicationId = "{package}"',
    1,
).replace(
    'versionCode = 10', 'versionCode = 1', 1
).replace(
    'versionName = "0.9.5-beta.5"',
    f'versionName = "0.2.0-preview.{flavor}"', 1
)
file.write_text(source, encoding="utf-8")
print(f"Prévia isolada ({flavor}): {package}, sem secrets.")
