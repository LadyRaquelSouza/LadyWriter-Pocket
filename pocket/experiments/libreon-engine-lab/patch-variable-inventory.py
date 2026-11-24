#!/usr/bin/env python3
"""Catálogo somente leitura dos campos ODT. Não modifica XML nem supõe motor UNO editável."""
from pathlib import Path

root=Path.cwd()
session="app/src/main/java/dev/offlineoffice/app/session/OfficeSession.kt"
ui="app/src/main/java/dev/offlineoffice/app/ui/AppRoot.kt"
def patch(path,old,new):
    f=root/path
    s=f.read_text(encoding="utf-8")
    if s.count(old)!=1: raise RuntimeError(f"{path}: marcador ausente ou ambíguo: {old[:70]}")
    f.write_text(s.replace(old,new,1),encoding="utf-8")

target=root/"app/src/main/java/dev/offlineoffice/app/session/PocketOdtVariables.kt"
if target.exists(): raise RuntimeError("Catálogo já foi criado")
target.write_text("""// SPDX-License-Identifier: GPL-3.0-or-later
package dev.offlineoffice.app.session

import android.util.Xml
import java.io.File
import java.util.zip.ZipFile
import org.xmlpull.v1.XmlPullParser

/** Inventário da última cópia ODT em disco, NÃO um estado vivo do motor Writer. */
object PocketOdtVariables {
    private const val TEXT = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    private const val OFFICE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    data class Entry(
        val name: String,
        val kind: String,
        val value: String,
        val hidden: Boolean,
        val source: String,
        val ordinal: Int,
    )

    /** Nunca grava no arquivo; evita descompactação e limita XML excessivamente grande. */
    fun read(file: File): List<Entry> {
        if (!file.extension.equals("odt", ignoreCase = true)) return emptyList()
        val result = mutableListOf<Entry>()
        ZipFile(file).use { zip ->
            for (source in listOf("content.xml", "styles.xml")) {
                val entry = zip.getEntry(source) ?: continue
                if (entry.size > 24_000_000L) error("XML do documento excede limite de segurança")
                zip.getInputStream(entry).use { stream ->
                    val parser = Xml.newPullParser()
                    parser.setFeature(XmlPullParser.FEATURE_PROCESS_NAMESPACES, true)
                    parser.setInput(stream, "UTF-8")
                    var count = 0
                    while (parser.eventType != XmlPullParser.END_DOCUMENT) {
                        if (parser.eventType == XmlPullParser.START_TAG &&
                            parser.namespace == TEXT &&
                            (parser.name == "variable-set" || parser.name == "variable-get")) {
                            val name = parser.getAttributeValue(TEXT, "name")
                            if (!name.isNullOrBlank()) {
                                count++
                                val kind = if (parser.name == "variable-set") "Definição" else "Exibição"
                                val hidden = parser.getAttributeValue(TEXT, "display") == "none"
                                val stored = parser.getAttributeValue(OFFICE, "string-value")
                                    ?: parser.getAttributeValue(OFFICE, "value")
                                // variable-get exibe o valor no corpo XML, não em office:string-value.
                                val displayText = parser.nextText()
                                val value = stored ?: displayText
                                result.add(Entry(name, kind, value, hidden, source, count))
                            }
                        }
                        parser.next()
                    }
                }
            }
        }
        return result
    }
}
""",encoding="utf-8")

patch(session,"    private lateinit var working: File", """    private lateinit var working: File

    /** Inventário da cópia ODT em disco; edições ainda não salvas podem não aparecer. */
    suspend fun pocketVariableInventory(): List<PocketOdtVariables.Entry> =
        withContext(Dispatchers.IO) { PocketOdtVariables.read(working) }
""")
patch(ui,
      "    var showPocketFields by remember { mutableStateOf(false) }",
      """    var showPocketFields by remember { mutableStateOf(false) }
    var pocketVariableEntries by remember { mutableStateOf<List<dev.offlineoffice.app.session.PocketOdtVariables.Entry>>(emptyList()) }
    var pocketVariableError by remember { mutableStateOf<String?>(null) }
    var pocketVariableLoading by remember { mutableStateOf(false) }""")
patch(ui,
      '''onClick = { showPocketFields = true },
                                modifier = Modifier.weight(1f).heightIn(min = 48.dp),''',
      '''onClick = {
                                    showPocketFields = true
                                    pocketVariableLoading = true
                                    pocketVariableError = null
                                    pocketVariableEntries = emptyList()
                                    val current = pocketOfficeSession
                                    scope.launch {
                                        try {
                                            pocketVariableEntries = current?.pocketVariableInventory().orEmpty()
                                        } catch (ex: Exception) {
                                            pocketVariableError = ex.message ?: "Não foi possível ler campos ODT."
                                        } finally {
                                            pocketVariableLoading = false
                                        }
                                    }
                                },
                                modifier = Modifier.weight(1f).heightIn(min = 48.dp),''')
patch(ui,
      '''    if (showPocketUpdate) {''',
      '''    if (showPocketFields) {
        AlertDialog(
            onDismissRequest = { showPocketFields = false },
            title = { Text("Variáveis do documento") },
            text = {
                Column(Modifier.heightIn(max = 440.dp).verticalScroll(rememberScrollState())) {
                    Text("Inventário da cópia salva em disco. Edições ainda não salvas podem não aparecer.")
                    if (pocketVariableLoading) {
                        CircularProgressIndicator()
                    } else if (pocketVariableError != null) {
                        Text("Erro: " + pocketVariableError)
                    } else if (pocketVariableEntries.isEmpty()) {
                        Text("Nenhuma definição ou exibição encontrada neste ODT.")
                    } else {
                        pocketVariableEntries.forEach { field ->
                            Text(field.name + " • " + field.kind)
                            Text(
                                "Arquivo: " + field.source +
                                " • ocorrência " + field.ordinal +
                                if (field.hidden) " • invisível" else ""
                            )
                            if (field.value.isNotBlank()) Text(field.value)
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showPocketFields = false }) { Text("Fechar") }
            },
        )
    }
    if (showPocketUpdate) {''')
# Elimina diálogo legado duplicado introduzido por patch-fields-indexes.py.
legacy = root / ui
source = legacy.read_text(encoding="utf-8")
first = "    if (showPocketFields) {"
end = "    if (showPocketStyles) {"
if source.count(first) != 2 or source.count(end) != 1:
    raise RuntimeError("Bloco de variáveis do upstream mudou; evitar remoção insegura")
start_index = source.rfind(first)
end_index = source.index(end, start_index)
legacy.write_text(source[:start_index] + source[end_index:], encoding="utf-8")
print("Pocket: inventário ODT somente leitura, acessível em Variáveis.")
