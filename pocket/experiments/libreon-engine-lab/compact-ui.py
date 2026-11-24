#!/usr/bin/env python3
"""Patch experimental do shell Libreon para um foco editorial de documento único.

Não modifica o motor ODT. Mantém o menu de operações para salvar/exportar e o
botão Home. A tira de abas deixa de ocupar altura na tela; se vários documentos
forem abertos, permanecem acessíveis pela tela inicial.
"""
from pathlib import Path

src = Path("app/src/main/java/dev/offlineoffice/app/ui/AppRoot.kt")
text = src.read_text(encoding="utf-8")
start_marker = "    Scaffold(\n        topBar = {"
end_marker = "\n    ) { padding ->"
assert text.count(start_marker) == 1, "Scaffold da fonte upstream mudou"
start = text.index(start_marker)
end = text.index(end_marker, start)
old = text[start:end]

# A barra de documento vira uma linha de 48 dp.
# A Home conserva menu e alternador de documentos.
replacement = """    Scaffold(
        topBar = {
            if (!fullScreen) {
                if (active != null) {
                    Surface(color = MaterialTheme.colorScheme.surface) {
                        Row(
                            modifier = Modifier.fillMaxWidth().height(56.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            IconButton(onClick = { showHome = true }) {
                                Icon(Icons.Outlined.Home, "Documentos")
                            }
                            Text(
                                active.displayName,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                                modifier = Modifier.weight(1f),
                                style = MaterialTheme.typography.titleSmall,
                            )
                            IconButton(
                                onClick = { tools(active)?.findRequests?.tryEmit(Unit) },
                                enabled = tools(active) != null,
                            ) {
                                Icon(Icons.Outlined.Search, "Localizar no documento")
                            }
                            IconButton(onClick = { save(active) }, enabled = active.dirty) {
                                Icon(Icons.Outlined.Save, "Salvar")
                            }
                            OverflowMenu(
                                hasActive = true,
                                onOpen = onOpen,
                                onSaveAs = { onSaveAs(active.id, active.displayName) },
                                onClose = { requestClose(active) },
                                onWordCount = {
                                    tools(active)?.let {
                                        wordCount = WordCountRequest(active.displayName, it)
                                    }
                                },
                                onShare = { asPdf ->
                                    onShare(active.id, active.displayName, asPdf)
                                },
                                onExportPdf = active.takeIf {
                                    it.kind.engine == DocumentKind.Engine.OFFICE
                                }?.let { tab ->
                                    { onExportPdf(tab.id, tab.displayName) }
                                },
                                onFullScreen = { fullScreen = true },
                                onDiscard = active.takeIf { it.dirty }?.let { tab ->
                                    { confirmDiscard = tab }
                                },
                                lightPages = active.takeIf { dark }?.let {
                                    it.id in lightTabs
                                },
                                onLightPages = { light ->
                                    settings.setLightPages(active.id, light)
                                },
                                onCloseAll = if (tabList.isNotEmpty())
                                    ({ confirmCloseAll = true }) else null,
                                onClearHome = null,
                                onSettings = { showSettings = true },
                                onLicenses = { showLicenses = true },
                            )
                        }
                    }
                } else {
                    TopAppBar(
                        title = { HomeTitle() },
                        actions = {
                            IconButton(onClick = onOpen) {
                                Icon(Icons.Outlined.FolderOpen, "Abrir ODT")
                            }
                            if (tabList.size > 1) {
                                TabCountChip(
                                    count = tabList.size,
                                    onClick = { showSwitcher = true },
                                )
                            }
                            OverflowMenu(
                                hasActive = false,
                                onOpen = onOpen,
                                onSaveAs = {},
                                onClose = {},
                                onWordCount = {},
                                onShare = {},
                                onExportPdf = null,
                                onFullScreen = { fullScreen = true },
                                onDiscard = null,
                                lightPages = null,
                                onLightPages = {},
                                onCloseAll = if (tabList.isNotEmpty())
                                    ({ confirmCloseAll = true }) else null,
                                onClearHome = { confirmClearHome = true },
                                onSettings = { showSettings = true },
                                onLicenses = { showLicenses = true },
                            )
                        }
                    )
                }
            }
        },"""
text = text[:start] + replacement + text[end:]

needle = "import androidx.compose.foundation.layout.fillMaxSize"
assert needle in text
text = text.replace(needle, "import androidx.compose.foundation.layout.fillMaxWidth\nimport androidx.compose.foundation.layout.height\n" + needle, 1)

# Build tag/pacote distinto do laboratorio anterior, sem conflito de assinatura.
src.write_text(text, encoding="utf-8")
print("UI editorial compacta instalada: sem aba dupla, 48 dp no documento.")
