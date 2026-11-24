#!/usr/bin/env python3
"""Validação offline e sem dependências da documentação do Pocket."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "README.md",
    ROOT / "CONTRIBUINDO.md",
    ROOT / "docs" / "PLANO-TECNICO-E-TESTES.md",
    ROOT / "docs" / "ROADMAP.md",
    ROOT / "docs" / "ARQUITETURA-EM-AVALIACAO.md",
]
errors = []

for path in DOCS:
    if not path.is_file():
        errors.append(f"Arquivo ausente: {path.relative_to(ROOT)}")
        continue
    text = path.read_text(encoding="utf-8")
    if not text.startswith("# "):
        errors.append(f"Falta titulo Markdown H1: {path.relative_to(ROOT)}")
    if "\x00" in text or not text.strip():
        errors.append(f"Conteudo invalido: {path.relative_to(ROOT)}")
    for destination in re.findall(r"\]\(([^)]+)\)", text):
        if re.match(r"^(https?://|mailto:|#)", destination):
            continue
        local = (path.parent / destination.split("#", 1)[0]).resolve()
        if not local.is_relative_to(ROOT.resolve()):
            errors.append(f"Link fora de pocket/: {destination} em {path.name}")
        elif not local.exists():
            errors.append(f"Link quebrado: {destination} em {path.name}")

for required in ("WYSIWYG", "DataNarrativa", "Moto G05", "1.201"):
    if not any(path.is_file() and required in path.read_text(encoding="utf-8") for path in DOCS):
        errors.append(f"Requisito essencial ausente da documentacao: {required}")

if errors:
    print("\n".join(f"ERRO: {error}" for error in errors), file=sys.stderr)
    sys.exit(1)
print(f"OK: {len(DOCS)} documentos verificados, links internos validos.")
