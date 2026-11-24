#!/usr/bin/env python3
"""Atalhos editoriais seguros: campos Writer e atualizacao de sumario.

APLICAR apos patch-odt-style-selector.py, no checkout Libreon temporario.
A insercao/edicao se faz pelo dialogo nativo do Writer, nunca por substituicao
do XML ou insercao de texto literal no ODT. O comando e sua UI no Android
precisam ser validados em copia sintética, antes de uso em manuscritos.
"""
from pathlib import Path

ROOT = Path.cwd()


def patch(path: str, before: str, after: str) -> None:
    file = ROOT / path
    source = file.read_text(encoding="utf-8")
    count = source.count(before)
    if count != 1:
        raise SystemExit(f"Upstream alterado: {path}: {before[:80]!r}, {count} ocorrencias")
    file.write_text(source.replace(before, after, 1), encoding="utf-8")


session = "app/src/main/java/dev/offlineoffice/app/session/OfficeSession.kt"
proto = "engine-office/src/main/java/dev/offlineoffice/office/OfficeProtocol.kt"
client = "engine-office/src/main/java/dev/offlineoffice/office/OfficeClient.kt"
service = "engine-office/src/main/java/dev/offlineoffice/office/OfficeService.kt"
document = "engine-office/src/main/java/dev/offlineoffice/office/OfficeDocument.kt"
ui = "app/src/main/java/dev/offlineoffice/app/ui/AppRoot.kt"

patch(proto,
      "    const val APPLY_PARAGRAPH_STYLE = 12",
      """    const val APPLY_PARAGRAPH_STYLE = 12
    /** Abre o dialogo do proprio motor Writer; nao reescreve XML. */
    const val POCKET_OPEN_FIELDS = 13
    /** Atualiza campos e depois todos os indices (inclusive sumario). */
    const val POCKET_UPDATE_FIELDS_INDEXES = 14""")

patch(client,
      "    fun applyParagraphStyle(name: String) = send(",
      """    /** Dialogo nativo de campos Writer, inclusive variaveis Set/Show. */
    fun openPocketFields() = send(P.POCKET_OPEN_FIELDS)

    /** Os dois comandos UNO sao distintos e intencionais, nunca por tecla. */
    fun updatePocketFieldsAndIndexes() = send(P.POCKET_UPDATE_FIELDS_INDEXES)

    fun applyParagraphStyle(name: String) = send(""")

patch(service,
      "            P.APPLY_PARAGRAPH_STYLE -> {",
      """            P.POCKET_OPEN_FIELDS -> document?.openPocketFields()
            P.POCKET_UPDATE_FIELDS_INDEXES -> document?.updatePocketFieldsAndIndexes()
            P.APPLY_PARAGRAPH_STYLE -> {""")

patch(document,
      "    fun applyParagraphStyle(name: String) {",
      '''    /**
     * A requisicao abre a janela completa de campos do Writer (Variaveis).
     * O motor escolhe os formatos/semanticas; nenhuma mutacao direta de ODT.
     */
    fun openPocketFields() {
        if (_state.value != State.Ready || readOnly) return
        sendPocketUno(".uno:InsertFieldCtrl")
    }

    /**
     * Atualizar campos F9 nao atualiza sumario. Enviar os dois comandos na
     * mesma fila WebView: primeiro campos; depois indices/sumario.
     * Nao forcar Save e nao alterar dados ao carregar um documento.
     */
    fun updatePocketFieldsAndIndexes() {
        if (_state.value != State.Ready || readOnly) return
        sendPocketUno(".uno:UpdateFields", ".uno:UpdateAllIndexes")
    }

    private fun sendPocketUno(vararg commands: String) {
        val valid = setOf(
            ".uno:InsertFieldCtrl", ".uno:UpdateFields", ".uno:UpdateAllIndexes"
        )
        if (commands.isEmpty() || commands.any { it !in valid }) return
        val lines = commands.joinToString(separator = "\\n") { command ->
            "map.sendUnoCommand(" + org.json.JSONObject.quote(command) + ");"
        }
        val js = """
            (() => {
              const map = window.app && window.app.map;
              if (!map || typeof map.sendUnoCommand !== 'function') {
                return "Pocket: UNO indisponivel";
              }
              __COMMANDS__
              return "Pocket: comandos UNO enviados";
            })();
        """.trimIndent().replace("__COMMANDS__", lines)
        webView.post {
            webView.evaluateJavascript(js) { result ->
                android.util.Log.d("PocketFields", "UNO dispatch: " + result)
                // O retorno indica apenas envio, nunca sucesso da alteração.
                // Informar indisponibilidade em vez de deixar o botão mudo.
                if (result.contains("UNO indisponivel")) {
                    android.widget.Toast.makeText(
                        webView.context,
                        "O motor do documento está indisponível. Reabra o arquivo antes de tentar novamente.",
                        android.widget.Toast.LENGTH_LONG
                    ).show()
                }
            }
        }
    }

    fun applyParagraphStyle(name: String) {''')

patch(session,
      "    fun applyPocketParagraphStyle(style: String) {",
      """    /** Acoes de campo sao exclusivas de ODT editavel. */
    fun openPocketFields() {
        if (readOnly || !::document.isInitialized) return
        document.openPocketFields()
    }

    fun updatePocketFieldsAndIndexes() {
        if (readOnly || !::document.isInitialized) return
        document.updatePocketFieldsAndIndexes()
    }

    fun applyPocketParagraphStyle(style: String) {""")

patch(ui,
      "    var pocketStyleSearch by remember { mutableStateOf(\"\") }",
      """    var pocketStyleSearch by remember { mutableStateOf("") }
    var showPocketFields by remember { mutableStateOf(false) }""")

patch(ui,
      "                                onClose = { requestClose(active) },",
      """                                onClose = { requestClose(active) },
                                onPocketFields = if (pocketOfficeSession != null &&
                                    !pocketOfficeSession.readOnly) ({ showPocketFields = true }) else null,""")

patch(ui,
      "                                onClose = {},",
      """                                onClose = {},
                                onPocketFields = null,""")

patch(ui,
      "    onWordCount: () -> Unit,",
      """    onWordCount: () -> Unit,
    onPocketFields: (() -> Unit)?,""")

patch(ui,
      """                DropdownMenuItem(
                    text = { Text("Word count") },""",
      """                onPocketFields?.let { fields ->
                    DropdownMenuItem(
                        text = { Text("Campos e sumário") },
                        onClick = { expanded = false; fields() },
                    )
                }
                DropdownMenuItem(
                    text = { Text("Word count") },""")

patch(ui,
      "    if (showPocketStyles) {",
      """    if (showPocketFields) {
        AlertDialog(
            onDismissRequest = { showPocketFields = false },
            title = { Text("Inserir variável ou campo") },
            text = {
                Text(
                    "Abre o painel de campos do Writer na posição do cursor. " +
                    "A criação e a edição de variáveis ainda são experimentais: " +
                    "teste em uma cópia ODT. Para atualizar índices, use Sumário."
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    showPocketFields = false
                    pocketOfficeSession?.openPocketFields()
                }) { Text("Inserir…") }
            },
            dismissButton = {
                TextButton(onClick = { showPocketFields = false }) {
                    Text("Cancelar")
                }
            },
        )
    }

    if (showPocketStyles) {""")

print("Pocket: menu Campos e sumario ligado a UNO via OfficeClient/Service.")
