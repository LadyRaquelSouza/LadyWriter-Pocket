#!/usr/bin/env python3
"""Sonda não destrutiva da conexão Android ↔ WebView ↔ Collabora.

Não chama comandos UNO nem modifica ODT. Retorna estado por Messenger com
identificador de requisição; resposta de JS não demonstra capacidades de escrita.
Aplicar após patch-variable-inventory.py.
"""
from pathlib import Path
ROOT=Path.cwd()
def patch(path,old,new):
    p=ROOT/path
    s=p.read_text(encoding="utf-8")
    if s.count(old)!=1: raise RuntimeError(f"{path}: marcador ambíguo/ausente: {old[:80]}")
    p.write_text(s.replace(old,new,1),encoding="utf-8")
proto="engine-office/src/main/java/dev/offlineoffice/office/OfficeProtocol.kt"
client="engine-office/src/main/java/dev/offlineoffice/office/OfficeClient.kt"
service="engine-office/src/main/java/dev/offlineoffice/office/OfficeService.kt"
document="engine-office/src/main/java/dev/offlineoffice/office/OfficeDocument.kt"
ui="app/src/main/java/dev/offlineoffice/app/ui/AppRoot.kt"
patch(proto,"    const val POCKET_QUICK_FORMAT = 15", """    const val POCKET_QUICK_FORMAT = 15
    const val POCKET_PROBE_ENGINE = 16
    const val POCKET_PROBE_RESULT = 116""")
patch(client,"    fun openPocketFields() = send(P.POCKET_OPEN_FIELDS)", """    private val _pocketEngineProbe = MutableSharedFlow<String>(extraBufferCapacity = 4)
    val pocketEngineProbe: SharedFlow<String> = _pocketEngineProbe.asSharedFlow()

    fun probePocketEngine() = send(P.POCKET_PROBE_ENGINE)

    fun openPocketFields() = send(P.POCKET_OPEN_FIELDS)""")
patch(client,"            P.SELECTION -> selections[msg.arg1]?.complete(msg.peekData()?.getString(P.KEY_MESSAGE))", """            P.SELECTION -> selections[msg.arg1]?.complete(msg.peekData()?.getString(P.KEY_MESSAGE))
            P.POCKET_PROBE_RESULT -> msg.data.getString(P.KEY_MESSAGE)?.let {
                _pocketEngineProbe.tryEmit(it)
            }""")
patch(service,"            P.POCKET_QUICK_FORMAT -> msg.data.getString(P.KEY_POCKET_FORMAT)", """            P.POCKET_PROBE_ENGINE -> {
                val receiver: (String) -> Unit = { result ->
                    send(P.POCKET_PROBE_RESULT, data = messageBundle(result))
                }
                document?.probePocketEngine(receiver) ?: receiver("DOCUMENT_UNAVAILABLE")
            }
            P.POCKET_QUICK_FORMAT -> msg.data.getString(P.KEY_POCKET_FORMAT)""")
patch(document,"    fun openPocketFields() {", '''    /** Diagnóstico somente leitura. Nunca despacha comandos UNO. */
    fun probePocketEngine(report: (String) -> Unit) {
        if (_state.value != State.Ready) {
            report("ENGINE_NOT_READY")
            return
        }
        if (readOnly) {
            report("DOCUMENT_READ_ONLY")
            return
        }
        webView.post {
            webView.evaluateJavascript(
                """
                (() => {
                  try {
                    if (!window.app) return 'APP_UNAVAILABLE';
                    if (!window.app.map) return 'MAP_UNAVAILABLE';
                    if (typeof window.app.map.sendUnoCommand !== 'function')
                        return 'UNO_DISPATCH_UNAVAILABLE';
                    return 'DISPATCH_AVAILABLE';
                  } catch (_) {
                    return 'PROBE_ERROR';
                  }
                })();
                """.trimIndent()
            ) { result ->
                val value = runCatching { org.json.JSONTokener(result).nextValue() as? String }
                    .getOrNull() ?: "PROBE_INVALID_RESPONSE"
                report(value)
            }
        }
    }

    fun openPocketFields() {''')
patch(ui,"    var pocketVariableLoading by remember { mutableStateOf(false) }", """    var pocketVariableLoading by remember { mutableStateOf(false) }
    var pocketEngineStatus by remember { mutableStateOf("Não verificado") }
    LaunchedEffect(pocketOfficeSession) {
        pocketOfficeSession?.document?.pocketEngineProbe?.collect {
            pocketEngineStatus = when (it) {
                "DISPATCH_AVAILABLE" -> "Conexão ativa. Edição de variáveis ainda não validada."
                "ENGINE_NOT_READY" -> "Documento ainda não está pronto."
                "DOCUMENT_READ_ONLY" -> "Documento aberto somente para leitura."
                "DOCUMENT_UNAVAILABLE" -> "Motor do documento indisponível."
                "APP_UNAVAILABLE", "MAP_UNAVAILABLE" -> "Interface Collabora desconectada."
                "UNO_DISPATCH_UNAVAILABLE" -> "Envio de comandos indisponível."
                else -> "Falha na verificação: " + it
            }
        }
    }""")
patch(ui,'    if (showPocketUpdate) {', '''    if (showPocketUpdate) {''')
# Botão integrado ao diálogo do inventário, sem fingir que já existe escrita.
patch(ui,
      '''                    Text("Inventário da cópia salva em disco. Edições ainda não salvas podem não aparecer.")''',
      '''                    Text("Inventário da cópia salva em disco. Edições ainda não salvas podem não aparecer.")
                    Text("Motor: " + pocketEngineStatus)
                    TextButton(onClick = {
                        pocketEngineStatus = "Verificando…"
                        pocketOfficeSession?.document?.probePocketEngine()
                    }) { Text("Verificar conexão do editor") }''')
print("Pocket: sonda WebView/UNO não destrutiva com retorno Android implementada.")
