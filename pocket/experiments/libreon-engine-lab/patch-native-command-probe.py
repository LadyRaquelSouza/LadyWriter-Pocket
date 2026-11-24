#!/usr/bin/env python3
"""Teste explícito do canal JNI já existente, sem alegar sucesso semântico.

Executa .uno:WordCountDialog somente mediante toque da usuária.
O retorno NATIVE_CALL_RETURNED confirma apenas que a chamada JNI retornou.
Aplicar após patch-variable-engine-probe.py.
"""
from pathlib import Path

ROOT = Path.cwd()
def patch(path, before, after):
    file = ROOT / path
    source = file.read_text(encoding="utf-8")
    count = source.count(before)
    if count != 1:
        raise RuntimeError(f"{path}: esperado 1 marcador, encontrado {count}: {before[:80]}")
    file.write_text(source.replace(before, after, 1), encoding="utf-8")

proto = "engine-office/src/main/java/dev/offlineoffice/office/OfficeProtocol.kt"
client = "engine-office/src/main/java/dev/offlineoffice/office/OfficeClient.kt"
service = "engine-office/src/main/java/dev/offlineoffice/office/OfficeService.kt"
document = "engine-office/src/main/java/dev/offlineoffice/office/OfficeDocument.kt"
ui = "app/src/main/java/dev/offlineoffice/app/ui/AppRoot.kt"

patch(proto, "    const val POCKET_PROBE_RESULT = 116",
      """    const val POCKET_PROBE_RESULT = 116
    const val POCKET_PROBE_NATIVE_COMMAND = 17""")

patch(client, "    fun probePocketEngine() = send(P.POCKET_PROBE_ENGINE)",
      """    fun probePocketNativeCommand() = send(P.POCKET_PROBE_NATIVE_COMMAND)

    fun probePocketEngine() = send(P.POCKET_PROBE_ENGINE)""")

patch(service, "            P.POCKET_PROBE_ENGINE -> {",
      """            P.POCKET_PROBE_NATIVE_COMMAND -> {
                val receiver: (String) -> Unit = { result ->
                    send(P.POCKET_PROBE_RESULT, data = messageBundle(result))
                }
                val current = document
                if (current == null) receiver("DOCUMENT_UNAVAILABLE")
                else scope.launch {
                    current.probePocketNativeCommand(receiver)
                }
            }
            P.POCKET_PROBE_ENGINE -> {""")

patch(document, "    private val pendingSave = AtomicReference<CompletableDeferred<Boolean>?>(null)",
      """    private val pendingSave = AtomicReference<CompletableDeferred<Boolean>?>(null)
    /** Uma única sonda em andamento; resposta nunca representa edição de variáveis. */
    private val pocketProbePending = AtomicReference<CompletableDeferred<String>?>(null)""")

patch(document, "        socket.enqueue(message)", """        // O retorno JNI é assíncrono. A chamada native ter retornado não
        // significa que o UNO executou o comando.
        if (message.size < 4096 && message.startsWithAscii("unocommandresult:")) {
            val body = String(message, Charsets.UTF_8).substringAfter("unocommandresult:").trim()
            runCatching { org.json.JSONObject(body) }.getOrNull()?.let { result ->
                if (result.optString("commandName") == ".uno:WordCountDialog") {
                    val status = when (result.optString("success", "")) {
                        "true" -> "NATIVE_RESULT_SUCCESS"
                        "false" -> "NATIVE_RESULT_FAILURE"
                        else -> "NATIVE_RESULT_UNKNOWN"
                    }
                    pocketProbePending.get()?.complete(status)
                }
            }
        }
        socket.enqueue(message)""")

patch(document, "    fun probePocketEngine(report: (String) -> Unit) {",
      '''    /**
     * Sonda JNI não mutante, com espera do evento unocommandresult.
     * Nem SUCCESS comprova suporte para manipular campos SetExpression.
     */
    suspend fun probePocketNativeCommand(report: (String) -> Unit) {
        if (_state.value != State.Ready) {
            report("ENGINE_NOT_READY")
            return
        }
        if (readOnly) {
            report("DOCUMENT_READ_ONLY")
            return
        }
        val pending = CompletableDeferred<String>()
        if (!pocketProbePending.compareAndSet(null, pending)) {
            report("NATIVE_PROBE_BUSY")
            return
        }
        try {
            OfficeEngine.call {
                bridge.postUnoCommand(".uno:WordCountDialog", null, true)
            }
            report(
                kotlinx.coroutines.withTimeout(10_000L) { pending.await() }
            )
        } catch (timeout: kotlinx.coroutines.TimeoutCancellationException) {
            report("NATIVE_RESULT_TIMEOUT")
        } catch (error: Exception) {
            android.util.Log.w("PocketNativeProbe", "JNI probe failed", error)
            report("NATIVE_CALL_FAILED")
        } finally {
            pocketProbePending.compareAndSet(pending, null)
        }
    }

    fun probePocketEngine(report: (String) -> Unit) {''')

patch(ui, '''"DISPATCH_AVAILABLE" -> "Conexão ativa. Edição de variáveis ainda não validada."''',
      '''"DISPATCH_AVAILABLE" -> "Conexão ativa. Edição de variáveis ainda não validada."
                "NATIVE_RESULT_SUCCESS" -> "Comando JNI confirmado pelo motor. Edição de variáveis ainda não comprovada."
                "NATIVE_RESULT_FAILURE" -> "O motor informou falha ao executar o comando de teste."
                "NATIVE_RESULT_UNKNOWN" -> "O motor respondeu sem indicar sucesso ou falha."
                "NATIVE_RESULT_TIMEOUT" -> "O motor não confirmou o comando. Tempo esgotado."
                "NATIVE_PROBE_BUSY" -> "Há um teste de conexão em andamento."
                "NATIVE_CALL_FAILED" -> "A chamada nativa falhou. Não edite variáveis."''')

patch(ui, '''                    }) { Text("Verificar conexão do editor") }''',
      '''                    }) { Text("Verificar conexão do editor") }
                    TextButton(onClick = {
                        pocketEngineStatus = "Testando chamada nativa…"
                        pocketOfficeSession?.document?.probePocketNativeCommand()
                    }) { Text("Testar JNI (contagem de palavras)") }''')

print("Pocket: prova JNI de comando não mutante ligada à interface, sem alterações ODT.")
