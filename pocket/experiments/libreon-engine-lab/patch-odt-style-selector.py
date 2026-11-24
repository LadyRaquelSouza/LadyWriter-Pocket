#!/usr/bin/env python3
"""LadyWriter Pocket: listar e aplicar estilos de paragrafo ODT existentes.

Aplica patch APOS compact-ui.py no checkout temporario Libreon (GPL-3.0+).
Nao modifica definicoes de estilo; requer teste no Moto G05 com copia de ODT.
"""
from pathlib import Path
root = Path.cwd()

def patch(path, before, after):
    p = root / path
    s = p.read_text(encoding="utf-8")
    if s.count(before) != 1:
        raise RuntimeError(f"Fonte upstream mudou em {path}: {s.count(before)} ocorrencias")
    p.write_text(s.replace(before, after, 1), encoding="utf-8")

session = "app/src/main/java/dev/offlineoffice/app/session/OfficeSession.kt"
proto = "engine-office/src/main/java/dev/offlineoffice/office/OfficeProtocol.kt"
client = "engine-office/src/main/java/dev/offlineoffice/office/OfficeClient.kt"
service = "engine-office/src/main/java/dev/offlineoffice/office/OfficeService.kt"
document = "engine-office/src/main/java/dev/offlineoffice/office/OfficeDocument.kt"
ui = "app/src/main/java/dev/offlineoffice/app/ui/AppRoot.kt"

parser_file = root / "app/src/main/java/dev/offlineoffice/app/session/PocketOdtStyles.kt"
assert not parser_file.exists()
parser_file.write_text('''// SPDX-License-Identifier: GPL-3.0-or-later
package dev.offlineoffice.app.session

import android.util.Xml
import java.io.File
import java.util.zip.ZipFile
import org.xmlpull.v1.XmlPullParser

/** Lê estilos nomeados; ignora estilos automáticos temporários. */
internal object PocketOdtStyles {
    private const val OFFICE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    private const val STYLE = "urn:oasis:names:tc:opendocument:xmlns:style:1.0"

    fun paragraphs(file: File): List<String> {
        if (!file.name.endsWith(".odt", ignoreCase = true)) return emptyList()
        val styles = linkedSetOf<String>()
        try {
            ZipFile(file).use { zip ->
                val entry = zip.getEntry("styles.xml") ?: return emptyList()
                if (entry.size > 8_000_000L) return emptyList()
                zip.getInputStream(entry).use { input ->
                    val parser = Xml.newPullParser()
                    parser.setFeature(XmlPullParser.FEATURE_PROCESS_NAMESPACES, true)
                    parser.setInput(input, "UTF-8")
                    var inStyles = false
                    while (parser.eventType != XmlPullParser.END_DOCUMENT) {
                        if (parser.eventType == XmlPullParser.START_TAG) {
                            if (parser.namespace == OFFICE && parser.name == "styles") {
                                inStyles = true
                            } else if (inStyles && parser.namespace == STYLE &&
                                parser.name == "style" &&
                                parser.getAttributeValue(STYLE, "family") == "paragraph") {
                                val label = parser.getAttributeValue(STYLE, "display-name")
                                    ?: parser.getAttributeValue(STYLE, "name")
                                if (!label.isNullOrBlank()) styles.add(label)
                            }
                        } else if (parser.eventType == XmlPullParser.END_TAG &&
                            parser.namespace == OFFICE && parser.name == "styles") {
                            inStyles = false
                        }
                        parser.next()
                    }
                }
            }
        } catch (_: Exception) {
            return emptyList()
        }
        return styles.toList()
    }
}
''', encoding="utf-8")

patch(session, "    private lateinit var working: File", '''    private lateinit var working: File

    /** Estilos nomeados carregados do ODT. */
    var pocketParagraphStyles: List<String> = emptyList()
        private set

    fun applyPocketParagraphStyle(style: String) {
        if (readOnly || style !in pocketParagraphStyles) return
        if (::document.isInitialized) document.applyParagraphStyle(style)
    }''')
patch(session, "        document = OfficeClient(context)", '''        pocketParagraphStyles = withContext(Dispatchers.IO) {
            PocketOdtStyles.paragraphs(working)
        }
        document = OfficeClient(context)''')
patch(proto, "    const val EXPORT_PDF = 11", '''    const val EXPORT_PDF = 11
    const val APPLY_PARAGRAPH_STYLE = 12''')
patch(proto, '    const val KEY_QUERY = "query"', '''    const val KEY_QUERY = "query"
    const val KEY_STYLE = "style"''')
patch(client, "    fun clearFind() = send(P.FIND_CLEAR)", '''    fun clearFind() = send(P.FIND_CLEAR)

    fun applyParagraphStyle(name: String) = send(
        P.APPLY_PARAGRAPH_STYLE, data = Bundle().apply { putString(P.KEY_STYLE, name) }
    )''')
patch(service, "            P.FIND_CLEAR -> document?.clearFind()", '''            P.FIND_CLEAR -> document?.clearFind()
            P.APPLY_PARAGRAPH_STYLE -> {
                msg.data.getString(P.KEY_STYLE)?.takeIf { it.isNotBlank() }?.let {
                    document?.applyParagraphStyle(it)
                }
            }''')
patch(document, '    fun clearFind() = webView.post { webView.evaluateJavascript("app.searchService.resetSelection()", null) }', '''    fun clearFind() = webView.post { webView.evaluateJavascript("app.searchService.resetSelection()", null) }

    /** Executa um estilo ja existente por meio do mesmo motor Collabora da pagina. */
    fun applyParagraphStyle(name: String) {
        if (_state.value != State.Ready || readOnly || name.isBlank()) return
        val js = """
            (() => {
              const style = __STYLE_NAME__;
              const map = window.app && window.app.map;
              if (map && typeof map.sendUnoCommand === 'function') {
                map.sendUnoCommand('.uno:StyleApply', {
                  Style: { type: 'string', value: style },
                  FamilyName: { type: 'string', value: 'ParagraphStyles' }
                });
              }
            })();
        """.trimIndent().replace("__STYLE_NAME__", org.json.JSONObject.quote(name))
        webView.post { webView.evaluateJavascript(js, null) }
    }''')
patch(ui, "import androidx.compose.material3.OutlinedButton", '''import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField''')
patch(ui, "import androidx.compose.foundation.layout.fillMaxSize", '''import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.fillMaxSize''')
patch(ui, "import dev.offlineoffice.app.session.DocumentTools", '''import dev.offlineoffice.app.session.DocumentTools
import dev.offlineoffice.app.session.OfficeSession''')
patch(ui, "    val active = tabList.firstOrNull { it.id == activeId }?.takeUnless { showHome }", '''    val active = tabList.firstOrNull { it.id == activeId }?.takeUnless { showHome }
    val pocketOfficeSession = active?.let { sessions[it.id] as? SessionState.Ready }
        ?.session as? OfficeSession
    var showPocketStyles by remember { mutableStateOf(false) }
    var pocketStyleSearch by remember { mutableStateOf("") }''')
patch(ui, '''                            IconButton(onClick = { save(active) }, enabled = active.dirty) {
                                Icon(Icons.Outlined.Save, "Salvar")
                            }''', '''                            IconButton(
                                onClick = { pocketStyleSearch = ""; showPocketStyles = true },
                                enabled = pocketOfficeSession != null &&
                                    !pocketOfficeSession.readOnly &&
                                    pocketOfficeSession.pocketParagraphStyles.isNotEmpty(),
                            ) {
                                Text("Aa", style = MaterialTheme.typography.titleMedium)
                            }
                            IconButton(onClick = { save(active) }, enabled = active.dirty) {
                                Icon(Icons.Outlined.Save, "Salvar")
                            }''')
patch(ui, '''    if (fullScreen) {
        // A popup is its own window''', '''    if (showPocketStyles) {
        AlertDialog(
            onDismissRequest = { showPocketStyles = false },
            title = { Text("Estilos deste documento") },
            text = {
                Column {
                    OutlinedTextField(
                        value = pocketStyleSearch,
                        onValueChange = { pocketStyleSearch = it },
                        label = { Text("Procurar estilo") },
                        singleLine = true,
                    )
                    Column(Modifier.heightIn(max = 420.dp).verticalScroll(rememberScrollState())) {
                        pocketOfficeSession?.pocketParagraphStyles
                            ?.filter { it.contains(pocketStyleSearch, ignoreCase = true) }
                            ?.forEach { style ->
                                TextButton(onClick = {
                                    pocketOfficeSession.applyPocketParagraphStyle(style)
                                    showPocketStyles = false
                                }) { Text(style) }
                            }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showPocketStyles = false }) { Text("Fechar") }
            },
        )
    }
    if (fullScreen) {
        // A popup is its own window''')

print("Patch ODT estilos instalado; despacho UNO requer validacao no aparelho.")
