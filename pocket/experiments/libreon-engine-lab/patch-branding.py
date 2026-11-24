#!/usr/bin/env python3
"""Personaliza o nome e a identidade visual do laboratório LadyWriter Pocket.
O simbolo usa ponta de caneta editorial, em vez de livro aberto dominante.

Aplicado SOMENTE ao checkout temporário GPL-3.0-or-later do Libreon no
GitHub Actions. Conserva os créditos e avisos das licenças de terceiros.
Não copia imagens da marca Libreon para a identidade visual Pocket.
"""
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path.cwd()
RES = ROOT / "app/src/main/res"
SRC = ROOT / "app/src/main/java/dev/offlineoffice/app/ui"


def replace_once(relative: Path, original: str, changed: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    if text.count(original) != 1:
        raise SystemExit(f"Fonte mudou, não alterei {relative}: esperada 1 ocorrência de {original!r}")
    path.write_text(text.replace(original, changed, 1), encoding="utf-8")


strings = RES / "values/strings.xml"
replace_once(strings.relative_to(ROOT),
             '<string name="app_name">Libreon</string>',
             '<string name="app_name">LadyWriter Pocket</string>')
replace_once(strings.relative_to(ROOT),
             '<string name="app_tagline">Work freely</string>',
             '<string name="app_tagline">Seu livro, em qualquer lugar</string>')

# Marca Pocket: a ponta de caneta e o simbolo central. Fonte unica de verdade:
# recursos Android mantidos em pocket/branding/ no repositorio LadyWriter.
# O notebook/SDK local nao e necessario.
branding = Path(__file__).resolve().parents[2] / "branding"
for source_name, target_name in (
    ("ladywriter-mark.xml", "ladywriter_mark.xml"),
    ("ladywriter-mark-monochrome.xml", "ladywriter_mark_monochrome.xml"),
):
    original_art = branding / source_name
    if not original_art.is_file():
        raise SystemExit(f"Icone ausente do repositorio: {original_art}")
    drawable = RES / "drawable" / target_name
    drawable.parent.mkdir(parents=True, exist_ok=True)
    if drawable.exists():
        raise SystemExit(f"Recurso ja existe no checkout upstream: {drawable}")
    ET.parse(original_art)
    drawable.write_text(original_art.read_text(encoding="utf-8"), encoding="utf-8")
    ET.parse(drawable)

for filename in ("ic_launcher.xml", "ic_launcher_round.xml"):
    file = RES / "mipmap-anydpi" / filename
    original = file.read_text(encoding="utf-8")
    if original.count("@mipmap/ic_launcher_foreground") != 1:
        raise SystemExit(f"Não localizei foreground esperado em {filename}")
    if original.count("@mipmap/ic_launcher_monochrome") != 1:
        raise SystemExit(f"Não localizei monochrome esperado em {filename}")
    file.write_text(original
        .replace("@mipmap/ic_launcher_foreground", "@drawable/ladywriter_mark")
        .replace("@mipmap/ic_launcher_monochrome", "@drawable/ladywriter_mark_monochrome"),
        encoding="utf-8")
    ET.parse(file)

replace_once(Path("app/src/main/res/values/ic_launcher_background.xml"),
             "#F8FAFC", "#22162E")

# Home e cabeçalho deixam de desenhar o logotipo de terceiro.
for filename in ("AppRoot.kt", "HomeScreen.kt", "SettingsScreen.kt"):
    file = SRC / filename
    original = file.read_text(encoding="utf-8")
    if original.count("R.drawable.libreon_logo") != 1:
        raise SystemExit(f"Logo esperado mudou em {filename}")
    file.write_text(original.replace("R.drawable.libreon_logo",
                                     "R.drawable.ladywriter_mark"),
                    encoding="utf-8")

# Evita direcionar bug reports do Pocket para o mantenedor do Libreon.
replace_once(Path("app/src/main/java/dev/offlineoffice/app/ui/SettingsScreen.kt"),
             'private const val ISSUES_URL = "https://github.com/jainiakhil/Libreon/issues"',
             'private const val ISSUES_URL = "https://github.com/LadyRaquelSouza/LadyWriter-Pocket/issues"')
replace_once(Path("app/src/main/java/dev/offlineoffice/app/ui/SettingsScreen.kt"),
             'Text("Opens Libreon on GitHub in your browser")',
             'Text("Abre as Issues do LadyWriter Pocket no GitHub")')
replace_once(Path("app/src/main/java/dev/offlineoffice/app/ui/SettingsScreen.kt"),
             'Text("Report a problem or suggest a feature")',
             'Text("Reportar problema ou sugerir melhoria")')

# Convite de doação do aplicativo de terceiro não faz sentido na interface Pocket.
# Os créditos ao criador do Libreon continuam em "Open-source licenses".
replace_once(Path("app/src/main/java/dev/offlineoffice/app/ui/SettingsScreen.kt"),
             "                CoffeeBanner(onClick = { openInBrowser(context, COFFEE_URL) })\n",
             "")

# Este texto explica a derivação sem fazer parecer que Libreon é o nome do app.
replace_once(Path("app/src/main/java/dev/offlineoffice/app/ui/LicensesDialog.kt"),
             '"Libreon is free software, licensed under the GNU General Public License v3.0 or later. " +\n'
             '                        "It has no network access, no accounts and no analytics."',
             '"LadyWriter Pocket usa componentes derivados do Libreon (GPL-3.0-or-later), " +\n'
             '                        "além de LibreOffice e Collabora. Veja as licenças de terceiros abaixo."')

# Outras mensagens voltadas ao usuário com nome de app antigo.
replace_once(Path("app/src/main/java/dev/offlineoffice/app/ui/viewers/text/TextDialogs.kt"),
             'Text("Libreon does not open links.",',
             'Text("O LadyWriter Pocket não abre links internamente.",')

assert (ROOT / "app/src/main/AndroidManifest.xml").read_text().count(
    'android:label="@string/app_name"') == 1
print("Marca visual, launcher, nome de sistema, telas e créditos Pocket preparados.")
