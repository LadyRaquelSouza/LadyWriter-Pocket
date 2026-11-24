#!/usr/bin/env python3
"""Experimento reversivel sobre checkout temporario GPL do Lib reon.
Nao alterar mecanismos de renderizacao/edicao nem perder dados com fechamento de abas.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[3] / "upstream-libreon"
file = root / "app/src/main/java/dev/offlineoffice/app/ui/AppRoot.kt"
text = file.read_text(encoding="utf-8")
patches = (
    (
        'if (maxWidth >= 600.dp && tabList.isNotEmpty() && tabBar) {',
        'if (active == null && maxWidth >= 600.dp && tabList.isNotEmpty() && tabBar) {',
    ),
    (
        'TabCountChip(count = tabList.size, onClick = { showSwitcher = true })',
        'if (active == null && tabList.isNotEmpty()) TabCountChip(count = tabList.size, onClick = { showSwitcher = true })',
    ),
)
for before, after in patches:
    if text.count(before) != 1:
        raise SystemExit(f"Codigo upstream nao coincide: {before}")
    text = text.replace(before, after)
file.write_text(text, encoding="utf-8")
print("Interface de documento: sem barra de abas e contador; menu Salvar/Pesquisar preservado.")
