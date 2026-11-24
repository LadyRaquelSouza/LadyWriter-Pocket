#!/usr/bin/env python3
"""Identidade Android exclusiva para prévia pública, SEM chave privada.

Esta variante NÃO atualiza a instalação estável e nunca reutiliza o
applicationId dela. Gradle aplica sua assinatura debug temporária.
"""
from pathlib import Path

file = Path("app/build.gradle.kts")
source = file.read_text(encoding="utf-8")
for anchor in (
    'applicationId = "dev.libreon.app"',
    'versionCode = 10',
    'versionName = "0.9.5-beta.5"',
):
    if source.count(anchor) != 1:
        raise SystemExit(f"API upstream mudou: {anchor}")

source = source.replace(
    'applicationId = "dev.libreon.app"',
    'applicationId = "com.ladyrachelsouza.ladywriter.pocket.preview"',
    1,
).replace(
    'versionCode = 10', 'versionCode = 1', 1
).replace(
    'versionName = "0.9.5-beta.5"',
    'versionName = "0.2.0-preview.public"', 1
)
file.write_text(source, encoding="utf-8")
print("Prévia isolada, debug assinado pelo runner, sem usar secrets.")
