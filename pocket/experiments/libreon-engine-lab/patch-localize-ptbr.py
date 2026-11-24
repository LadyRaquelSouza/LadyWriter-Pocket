#!/usr/bin/env python3
"""Portugues brasileiro para LadyWriter Pocket.

Frontend Collabora ja inclui pacotes pt-BR. O Libreon forca 'en-US' no URL.
A casca Compose contem mensagens hardcoded em ingles; localizamos as partes
do fluxo editorial ODT, sem substituir valores de campos, estilos ou licencas.
Aplicar depois de branding + UX editorial.
"""
from pathlib import Path

ROOT = Path.cwd()
document = ROOT / "engine-office/src/main/java/dev/offlineoffice/office/OfficeDocument.kt"
source = document.read_text(encoding="utf-8")
needle = '.appendQueryParameter("lang", "en-US")'
assert source.count(needle) == 1, "Idioma do Collabora foi alterado no upstream"
# Os controles de zoom são injetados pelo próprio Libreon em JavaScript,
# portanto não aparecem na lista de Text("...") do Compose.
zoom_labels = {
    "'Fit width'": "'Ajustar à largura'",
    "'Zoom out'": "'Diminuir zoom'",
    "'Zoom in'": "'Aumentar zoom'",
    "'. Choose a zoom level'": "'. Escolher nível de zoom'",
}
source = source.replace(needle, '.appendQueryParameter("lang", "pt-BR")', 1)
for english, translated in zoom_labels.items():
    if source.count(english) != 1:
        raise SystemExit(f"Controle de zoom mudou: {english}")
    source = source.replace(english, translated, 1)
document.write_text(source, encoding="utf-8")

translations = {
    "Settings": "Configurações",
    "Back": "Voltar",
    "Appearance": "Aparência",
    "Follow system": "Seguir o sistema",
    "Light": "Claro",
    "Dark": "Escuro",
    "Light or dark, as set on this device": "Claro ou escuro, conforme o aparelho",
    "Office documents follow the app theme. To read one document with light pages while the app is dark, use Light pages in its menu.": "No editor, as cores da página podem ser diferentes do tema. Use Inverter fundo quando necessário.",
    "Tabs": "Abas",
    "Tab bar on wide screens": "Abas em telas largas",
    "Shown in landscape and on tablets. The arrow button in the top bar also hides it.": "Aparecem na horizontal e em tablets.",
    "About": "Sobre",
    "Open-source licenses": "Licenças de código aberto",
    "Report a problem or suggest a feature": "Relatar problema ou sugerir melhoria",
    "Opens Libreon on GitHub in your browser": "Abre o projeto LadyWriter no GitHub",
    "Opens in your browser": "Abre no navegador",
    "No browser found to open $url": "Nenhum navegador disponível para abrir $url",
    "  Open a document": "  Abrir documento",
    "Search open, recent and closed files": "Buscar documentos",
    "Search on device": "Buscar no aparelho",
    "Open tabs": "Documentos abertos",
    "Recent": "Recentes",
    "Recently closed": "Fechados recentemente",
    "Closed ": "Fechado em ",
    "Unsaved changes": "Alterações não salvas",
    "Clear": "Limpar",
    "Pinned": "Fixado",
    " · re-pick to open": " · selecionar novamente",
    "No files match \"$query\"": "Nenhum documento corresponde a \"$query\"",
    "Word, Excel, PowerPoint, PDF, Apple Pages, Numbers and Keynote, and text files open here. Everything stays on this device.": "Abra seus manuscritos e continue escrevendo. Os arquivos permanecem neste aparelho.",
    "No ads, no accounts, no internet. Everything stays on this device.": "Sem anúncios, contas ou internet obrigatória. Seus textos permanecem no aparelho.",
    "Open": "Abrir",
    "Search open documents": "Buscar documentos abertos",
    "Move up": "Mover para cima",
    "Move down": "Mover para baixo",
    "Close": "Fechar",
    "Close find": "Fechar busca",
    "Find in document": "Buscar no documento",
    "Previous match": "Ocorrência anterior",
    "Next match": "Próxima ocorrência",
    "No matches": "Nenhuma ocorrência",
    "Got it": "Entendi",
    "Reload": "Recarregar",
    "Word count": "Contagem de palavras",
    "Not available": "Indisponível",
    "Words": "Palavras",
    "Characters": "Caracteres",
    "Save signed document": "Salvar documento assinado",
    "Save as new file": "Salvar como novo arquivo",
    "Overwrite original": "Substituir original",
    "PDF saved": "PDF salvo",
    "Could not save the PDF": "Não foi possível salvar o PDF",
    "Cannot open file": "Não foi possível abrir o arquivo",
    "Save": "Salvar",
    "Don't save": "Não salvar",
    "Cancel": "Cancelar",
    "Discard": "Descartar",
    "Keep": "Manter",
    "More": "Mais opções",
    "Open…": "Abrir…",
    "Save as…": "Salvar como…",
    "Share": "Compartilhar",
    "Share as PDF": "Compartilhar em PDF",
    "Export as PDF…": "Exportar PDF…",
    "Full screen": "Tela cheia",
    "Light pages": "Páginas claras",
    "Discard changes": "Descartar alterações",
    "Close tab": "Fechar documento",
    "Close all tabs": "Fechar todos os documentos",
    "Clear Home": "Limpar início",
    "Your changes will be lost if you don't save them.": "As alterações serão perdidas se você não salvar.",
    "File changed elsewhere": "Arquivo alterado em outro aplicativo",
    "Overwrite": "Substituir",
    "Save as copy": "Salvar uma cópia",
    "Your edits since the last save will be lost and the document reopens as it was saved.": "As alterações desde o último salvamento serão perdidas. O arquivo voltará à versão salva.",
    "Close all tabs?": "Fechar todos os documentos?",
    "Close all": "Fechar todos",
    "Unsaved changes are lost. Your files themselves are not deleted.": "Alterações não salvas serão perdidas, mas os arquivos não serão apagados.",
    "Unsaved changes were restored.": "Alterações não salvas foram recuperadas.",
}

# Traduzimos apenas as literais completas, sem mexer em nomes de variaveis,
# enums, status do motor, comandos, propriedades ODF e licencas.
app = ROOT / "app/src/main/java/dev/offlineoffice/app"
counts = {}
for file in app.rglob("*.kt"):
    old = file.read_text(encoding="utf-8")
    s = old
    for key, value in translations.items():
        literal = '"' + key + '"'
        if literal in s:
            counts[key] = counts.get(key, 0) + s.count(literal)
            s = s.replace(literal, '"' + value + '"')
    if s != old:
        file.write_text(s, encoding="utf-8")

# Mensagens interpoladas: traduzir APENAS segmentos delimitados pelas aspas.
# Nunca aplicar substituicao global em palavras como Saved ou All, que sao
# parte de identificadores Kotlin (SaveResult.Saved, confirmCloseAll etc.).
safe_fragments = {
    '"Save failed: ': '"Falha ao salvar: ',
    '"Saved ': '"Salvo: ',
    '"Cannot reopen ': '"Não foi possível reabrir ',
    '"Pick ': '"Selecione ',
    ' again with Open to reopen it"': ' novamente em Abrir para reabrir"',
    ': it may have moved or been deleted"': ': arquivo movido ou apagado"',
    ' can no longer be opened without picking it again"': ' deve ser selecionado novamente para abrir"',
    '"Could not open ': '"Não foi possível abrir ',
    '"Save changes to ': '"Salvar alterações em ',
    '"Discard changes to ': '"Descartar alterações em ',
    ' was modified by another app since you opened it."': ' foi alterado em outro aplicativo depois de aberto."',
    '"All ': '"Todos os ',
    ' open documents will be closed. You can reopen them from Recently closed."': ' documentos abertos serão fechados. Você pode reabri-los em Fechados recentemente."',
    '"This closes every open tab and removes all recent and recently closed files from Home. ': '"Fecha os documentos abertos e limpa as listas de recentes. ',
}
for filename in ("ui/AppRoot.kt", "ui/HomeScreen.kt", "ui/SettingsScreen.kt"):
    file = app / filename
    s = file.read_text(encoding="utf-8")
    for a, b in safe_fragments.items():
        s = s.replace(a, b)
    # Guardas: identificadores de codigo nao sao textos localizaveis.
    if filename.endswith("AppRoot.kt"):
        for required in ("SaveResult.Saved", "confirmCloseAll", "onCloseAll", "closeAll()"):
            assert required in s, f"Identificador Kotlin indevidamente traduzido: {required}"
    file.write_text(s, encoding="utf-8")

assert all(x in counts for x in ["Settings", "Open tabs", "Word count", "Save", "Cancel"]), counts
print(f"Pocket pt-BR: {len(counts)} literais da interface Android, mais idioma nativo Collabora.")
