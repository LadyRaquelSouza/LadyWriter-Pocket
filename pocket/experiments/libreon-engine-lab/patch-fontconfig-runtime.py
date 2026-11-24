#!/usr/bin/env python3
"""Registra as fontes empacotadas no Fontconfig real do LibreOfficeKit Android.

No APK herdado do Collabora, unpack/etc/fonts/fonts.conf lista apenas
/system/fonts e usa cache /data/data/org.collabora.app/fontconfig.
O Pocket tem outro identificador e extrai fontes em dataDir/user/fonts.
Corrige os caminhos em runtime após copiar assets e antes das libs nativas.
"""
from pathlib import Path

file = Path("engine-office/src/main/java/dev/offlineoffice/office/OfficeEngine.kt")
text = file.read_text(encoding="utf-8")
needle = '                copyAssets(app.assets, "unpack", File(app.applicationInfo.dataDir))\n'
assert text.count(needle) == 1, "OfficeEngine upstream mudou (copyAssets)"
text = text.replace(needle, needle + '                configurePocketFontconfig(app)\n', 1)

helper_anchor = '    private fun copyAssets(assets: AssetManager, from: String, to: File) {\n'
assert text.count(helper_anchor) == 1, "OfficeEngine upstream mudou (copyAssets method)"
helper = r'''    /**
     * Fontes são extraídas em dataDir/user/fonts. O fonts.conf original só
     * enumera /system/fonts e usa cache do org.collabora.app, que não é o
     * package do LadyWriter Pocket. Corrigir antes do loadLibrary.
     * O assets stamp garante execução após updates do APK.
     */
    private fun configurePocketFontconfig(app: Context) {
        val root = File(app.applicationInfo.dataDir)
        val fonts = File(root, "user/fonts")
        val conf = File(root, "etc/fonts/fonts.conf")
        if (!conf.isFile || !fonts.isDirectory) {
            Log.w(TAG, "Pocket fonts/config not found, keeping Android system fonts")
            return
        }
        val cache = File(app.cacheDir, "fontconfig")
        if (!cache.isDirectory && !cache.mkdirs()) {
            Log.w(TAG, "Could not make fontconfig cache directory")
        }
        val original = conf.readText()
        val start = "<fontconfig>"
        val originalCache = "<cachedir>/data/data/org.collabora.app/fontconfig</cachedir>"
        if (!original.contains(start) || !original.contains(originalCache)) {
            Log.w(TAG, "Unexpected fonts.conf schema; leaving original intact")
            return
        }
        val updated = original
            .replace(start, start + "\n<dir>" + fonts.absolutePath + "</dir>")
            .replace(originalCache, "<cachedir>" + cache.absolutePath + "</cachedir>")
        conf.writeText(updated)
        Log.i(TAG, "Pocket fontconfig updated with app-private fonts and cache")
    }

'''
text = text.replace(helper_anchor, helper + helper_anchor, 1)
file.write_text(text, encoding="utf-8")
print("OfficeEngine Fontconfig: fontes e cache privados configurados.")
