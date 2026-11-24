#!/usr/bin/env python3
"""UI editorial brasileira sobre o checkout Libreon, sem alterar o ODT.

Executar depois de compact-ui, estilos, campos, marca e Fontconfig.
Preserva comandos nativos e motor; substitui barra inferior generica do Writer
por acoes explicitas e alvos de toque maiores no Compose.
"""
from pathlib import Path

ROOT = Path.cwd()

def patch(relative: str, before: str, after: str) -> None:
    path = ROOT / relative
    source = path.read_text(encoding="utf-8")
    count = source.count(before)
    if count != 1:
        raise RuntimeError(f"UI upstream mudou em {relative}: {before[:90]!r} ({count}x)")
    path.write_text(source.replace(before, after, 1), encoding="utf-8")

proto = "engine-office/src/main/java/dev/offlineoffice/office/OfficeProtocol.kt"
client = "engine-office/src/main/java/dev/offlineoffice/office/OfficeClient.kt"
service = "engine-office/src/main/java/dev/offlineoffice/office/OfficeService.kt"
document = "engine-office/src/main/java/dev/offlineoffice/office/OfficeDocument.kt"
session = "app/src/main/java/dev/offlineoffice/app/session/OfficeSession.kt"
ui = "app/src/main/java/dev/offlineoffice/app/ui/AppRoot.kt"

patch(proto,
      "    const val POCKET_UPDATE_FIELDS_INDEXES = 14",
      """    const val POCKET_UPDATE_FIELDS_INDEXES = 14
    const val POCKET_QUICK_FORMAT = 15""")
patch(proto, '    const val KEY_STYLE = "style"',
      '''    const val KEY_STYLE = "style"
    const val KEY_POCKET_FORMAT = "pocketFormat"''')

patch(client,
      "    fun openPocketFields() = send(P.POCKET_OPEN_FIELDS)",
      """    fun pocketQuickFormat(action: String) = send(
        P.POCKET_QUICK_FORMAT, data = Bundle().apply { putString(P.KEY_POCKET_FORMAT, action) }
    )

    fun openPocketFields() = send(P.POCKET_OPEN_FIELDS)""")

patch(service,
      "            P.POCKET_OPEN_FIELDS -> document?.openPocketFields()",
      """            P.POCKET_QUICK_FORMAT -> msg.data.getString(P.KEY_POCKET_FORMAT)
                ?.let { document?.pocketQuickFormat(it) }
            P.POCKET_OPEN_FIELDS -> document?.openPocketFields()""")

patch(document,
      "    fun openPocketFields() {",
      """    /** Atalhos intencionais, sem trocar familia/fonte ou alterar estilos. */
    fun pocketQuickFormat(action: String) {
        if (_state.value != State.Ready || readOnly) return
        val uno = when (action) {
            "bold" -> ".uno:Bold"
            "italic" -> ".uno:Italic"
            "smallcaps" -> ".uno:SmallCaps"
            "left" -> ".uno:LeftPara"
            "center" -> ".uno:CenterPara"
            "right" -> ".uno:RightPara"
            "justify" -> ".uno:JustifyPara"
            "pagebreak" -> ".uno:InsertPagebreak"
            else -> return
        }
        sendPocketUno(uno)
    }

    fun openPocketFields() {""")

patch(document,
      '''            ".uno:InsertFieldCtrl", ".uno:UpdateFields", ".uno:UpdateAllIndexes"''',
      '''            ".uno:InsertFieldCtrl", ".uno:UpdateFields", ".uno:UpdateAllIndexes",
            ".uno:Bold", ".uno:Italic", ".uno:SmallCaps", ".uno:LeftPara",
            ".uno:CenterPara", ".uno:RightPara", ".uno:JustifyPara",
            ".uno:InsertPagebreak"''')

patch(session,
      "    fun openPocketFields() {",
      """    fun pocketQuickFormat(action: String) {
        if (readOnly || !::document.isInitialized) return
        document.pocketQuickFormat(action)
    }

    fun openPocketFields() {""")

# O campo fullScreen upstream é declarado DEPOIS dos controles editoriais.
# Kotlin não permite a referência local antes da declaração; trazê-lo para o
# início do escopo mantém o mesmo estado e preserva BackHandler/FullScreenEffect.
patch(ui,
      "    var showPocketFields by remember { mutableStateOf(false) }",
      """    var fullScreen by remember { mutableStateOf(false) }
    var showPocketFields by remember { mutableStateOf(false) }""")
patch(ui,
      """    // Full-screen reading: the bars go, and back (or the button in the corner) brings them back.
    var fullScreen by remember { mutableStateOf(false) }
    if (active == null) fullScreen = false""",
      """    // Full-screen reading: the bars go, and back (or the button in the corner) brings them back.
    if (active == null) fullScreen = false""")

patch(ui,
      "    var showPocketFields by remember { mutableStateOf(false) }",
      """    var showPocketFields by remember { mutableStateOf(false) }
    var showPocketAlign by remember { mutableStateOf(false) }
    var showPocketUpdate by remember { mutableStateOf(false) }
    var pocketBarCollapsed by remember { mutableStateOf(false) }
    val pocketImeVisible = WindowInsets.ime.getBottom(LocalDensity.current) > 0
    val pocketKeyboardController = LocalSoftwareKeyboardController.current
    val pocketAndroidView = LocalView.current
    BackHandler(enabled = pocketImeVisible && active != null) {
        pocketKeyboardController?.hide()
        val input = pocketAndroidView.context.getSystemService(
            android.content.Context.INPUT_METHOD_SERVICE
        ) as? android.view.inputmethod.InputMethodManager
        input?.hideSoftInputFromWindow(pocketAndroidView.windowToken, 0)
    }
    // Modo imersivo somente durante a edição, nunca enquanto o teclado está aberto.
    DisposableEffect(active?.id, pocketImeVisible, fullScreen) {
        var ctx: android.content.Context = pocketAndroidView.context
        while (ctx is android.content.ContextWrapper && ctx !is android.app.Activity) {
            ctx = ctx.baseContext
        }
        val window = (ctx as? android.app.Activity)?.window
        val decor = window?.decorView
        val previousFlags = decor?.systemUiVisibility
        if (decor != null && active != null && !pocketImeVisible && !fullScreen) {
            decor.systemUiVisibility = previousFlags!! or (
                android.view.View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY or
                android.view.View.SYSTEM_UI_FLAG_HIDE_NAVIGATION or
                android.view.View.SYSTEM_UI_FLAG_FULLSCREEN or
                android.view.View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION or
                android.view.View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN or
                android.view.View.SYSTEM_UI_FLAG_LAYOUT_STABLE
            )
        }
        onDispose {
            if (decor != null && previousFlags != null) {
                decor.systemUiVisibility = previousFlags
            }
        }
    }""")

# Os controles essenciais, grandes e sempre descobriveis, ficam na casca
# Android. O menu profundo do Collabora permanece para funcoes avancadas.
bar = '''        bottomBar = {
            if (!fullScreen && pocketOfficeSession != null && !pocketOfficeSession.readOnly) {
                Surface(color = MaterialTheme.colorScheme.surface) {
                    Column(
                        Modifier.fillMaxWidth().padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        if (!pocketImeVisible) {
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                                TextButton(
                                    onClick = { pocketBarCollapsed = !pocketBarCollapsed },
                                    modifier = Modifier.heightIn(min = 40.dp),
                                ) {
                                    Text(if (pocketBarCollapsed) "Mostrar ferramentas ▴" else "Recolher ferramentas ▾")
                                }
                            }
                        }
                        if (!pocketImeVisible && !pocketBarCollapsed) {
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            OutlinedButton(
                                onClick = { pocketStyleSearch = ""; showPocketStyles = true },
                                modifier = Modifier.weight(1f).heightIn(min = 48.dp),
                                enabled = pocketOfficeSession.pocketParagraphStyles.isNotEmpty(),
                                contentPadding = PaddingValues(horizontal = 3.dp),
                            ) { Text("Estilos", maxLines = 1) }
                            OutlinedButton(
                                onClick = { showPocketFields = true },
                                modifier = Modifier.weight(1f).heightIn(min = 48.dp),
                                contentPadding = PaddingValues(horizontal = 3.dp),
                            ) { Text("Variáveis", maxLines = 1) }
                            OutlinedButton(
                                onClick = { showPocketUpdate = true },
                                modifier = Modifier.weight(1f).heightIn(min = 48.dp),
                                contentPadding = PaddingValues(horizontal = 3.dp),
                            ) { Text("Sumário", maxLines = 1) }
                            OutlinedButton(
                                onClick = { pocketOfficeSession.pocketQuickFormat("pagebreak") },
                                modifier = Modifier.weight(1.4f).heightIn(min = 52.dp),
                                contentPadding = PaddingValues(horizontal = 1.dp),
                            ) { Text("Quebra\\nde página", maxLines = 2, textAlign = TextAlign.Center) }
                        }
                        Row(
                            Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(4.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            TextButton(
                                onClick = { pocketOfficeSession.pocketQuickFormat("bold") },
                                modifier = Modifier.weight(1f).heightIn(min = 48.dp),
                            ) { Text("B", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold) }
                            TextButton(
                                onClick = { pocketOfficeSession.pocketQuickFormat("italic") },
                                modifier = Modifier.weight(1f).heightIn(min = 48.dp),
                            ) { Text("I", style = MaterialTheme.typography.titleMedium, fontStyle = FontStyle.Italic) }
                            TextButton(
                                onClick = { pocketOfficeSession.pocketQuickFormat("smallcaps") },
                                modifier = Modifier.weight(1.55f).heightIn(min = 48.dp),
                                contentPadding = PaddingValues(horizontal = 2.dp),
                            ) { Text("Versalete", maxLines = 1) }
                            TextButton(
                                onClick = { showPocketAlign = true },
                                modifier = Modifier.weight(1.45f).heightIn(min = 48.dp),
                                contentPadding = PaddingValues(horizontal = 2.dp),
                            ) { Text("Alinhar", maxLines = 1) }
                        }
                        }
                    }
                }
            }
        },
'''
patch(ui,
      "        },\n    ) { padding ->",
      "        },\n" + bar + "    ) { padding ->")

patch(ui,
      "import androidx.compose.foundation.layout.fillMaxSize",
      """import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.ime
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.platform.LocalView
import androidx.compose.runtime.DisposableEffect
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.heightIn
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.foundation.layout.fillMaxSize""")

patch(ui,
      "    if (showPocketFields) {",
      """    if (showPocketUpdate) {
        AlertDialog(
            onDismissRequest = { showPocketUpdate = false },
            title = { Text("Atualizar campos e sumário?") },
            text = { Text("Em livros longos, recalcular os campos e a numeração pode levar algum tempo. Salve a cópia depois de conferir o resultado.") },
            confirmButton = {
                TextButton(onClick = {
                    showPocketUpdate = false
                    pocketOfficeSession?.updatePocketFieldsAndIndexes()
                }) { Text("Atualizar") }
            },
            dismissButton = {
                TextButton(onClick = { showPocketUpdate = false }) { Text("Cancelar") }
            },
        )
    }
    if (showPocketAlign) {
        AlertDialog(
            onDismissRequest = { showPocketAlign = false },
            title = { Text("Alinhamento do parágrafo") },
            text = {
                Column {
                    listOf(
                        "Esquerda" to "left", "Centro" to "center",
                        "Direita" to "right", "Justificado" to "justify"
                    ).forEach { (label, action) ->
                        TextButton(
                            onClick = {
                                showPocketAlign = false
                                pocketOfficeSession?.pocketQuickFormat(action)
                            },
                            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
                        ) { Text(label) }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showPocketAlign = false }) { Text("Fechar") }
            },
        )
    }
    if (showPocketFields) {""")

# A barra nativa ja da acesso aos estilos, sem ocupacao de mais um icone "Aa"
# microscopico na barra superior de 56 dp. O dialogo existente fica preservado.
patch(ui,
      '''                            IconButton(
                                onClick = { pocketStyleSearch = ""; showPocketStyles = true },
                                enabled = pocketOfficeSession != null &&
                                    !pocketOfficeSession.readOnly &&
                                    pocketOfficeSession.pocketParagraphStyles.isNotEmpty(),
                            ) {
                                Text("Aa", style = MaterialTheme.typography.titleMedium)
                            }
''',
      "")

# CSS somente para o Writer ODT; barra do Calc/Impress/PDF nao muda.
# A barra inferior original e redundante e usa botoes pequenos de formatacao
# direta, que competem com os estilos documentais.
css = ROOT / "third_party/lok/assets/dist/branding.css"
assert css.is_file(), "Assets da WebView nao foram preparados"
with css.open("a", encoding="utf-8") as writer:
    writer.write("""
/* LadyWriter Pocket: edicao editorial com controles acessiveis em Compose.
   Ocultar APENAS a barra de formatacao generica do Writer em smartphones. */
body[data-docType='text'] #toolbar-down {
  display: none !important;
  height: 0 !important;
  min-height: 0 !important;
}
body[data-docType='text'] #toolbar-up {
  min-height: 46px !important;
}
body[data-docType='text'] #toolbar-up .w2ui-tb-button,
body[data-docType='text'] #toolbar-up .w2ui-tb-drop {
  min-width: 44px !important;
  min-height: 44px !important;
}
body[data-docType='text'] #mobile-wizard .mobile-wizard.ui-treeview-entry,
body[data-docType='text'] #mobile-wizard .ui-treeview-entry {
  min-height: 44px;
}
""")

patch(ui,
      "    BackHandler(enabled = active != null) { showHome = true }",
      "    BackHandler(enabled = active != null && !pocketImeVisible) { showHome = true }")
patch(ui,
      "    BackHandler(enabled = fullScreen) { fullScreen = false }",
      "    BackHandler(enabled = fullScreen && !pocketImeVisible) { fullScreen = false }")

print("Pocket: Voltar prioriza IME; quebra de pagina acessivel.")
