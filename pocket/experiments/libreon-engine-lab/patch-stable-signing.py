#!/usr/bin/env python3
"""Prepara assinatura, ID e versionamento estáveis no checkout TEMPORÁRIO do Libreon.

Não grava keystore nem senha no repositório, e nunca modifica o código original
que já está versionado. O APK gerado deve atualizar a instalação anterior do
mesmo pacote, desde que assinada com o MESMO certificado.
"""
from pathlib import Path
import os

app = Path("app/build.gradle.kts")
source = app.read_text(encoding="utf-8")

# Fail closed: GitHub Actions recebe dados de Secrets apenas em runtime.
password = os.getenv("POCKET_SIGNING_PASSWORD", "")
keyfile = os.getenv("POCKET_KEYSTORE_FILE", "")
run = os.getenv("GITHUB_RUN_NUMBER", "")

if len(password) < 16 or not keyfile or not Path(keyfile).is_file():
    raise SystemExit("Chave permanente ausente. Configure GitHub Secrets antes do build.")
if not run.isdecimal() or int(run) >= 100_000:
    raise SystemExit("GITHUB_RUN_NUMBER inválido para o versionamento.")

# Verifica versão da fonte antes de qualquer patch.
assert source.count('applicationId = "dev.libreon.app"') == 1
assert source.count('versionCode = 10') == 1
assert source.count('versionName = "0.9.5-beta.5"') == 1

source = source.replace(
    'applicationId = "dev.libreon.app"',
    'applicationId = "com.ladyrachelsouza.ladywriter.pocket"',
    1,
)
source = source.replace(
    "versionCode = 10",
    f"versionCode = {10000 + int(run)}",
    1,
)
source = source.replace(
    'versionName = "0.9.5-beta.5"',
    f'versionName = "0.2.0-laboratorio.{run}"',
    1,
)

# Um bloco android adicional configura apenas a variante de laboratorio; a
# chave, identificador de alias e senha são lidos em runtime pelo Gradle.
source += """
// LadyWriter Pocket Lab: assinatura estavel entre executores GitHub Actions.
android {
    signingConfigs {
        create("pocketStable") {
            storeFile = file(System.getenv("POCKET_KEYSTORE_FILE")
                ?: throw GradleException("POCKET_KEYSTORE_FILE nao configurado"))
            storePassword = System.getenv("POCKET_SIGNING_PASSWORD")
                ?: throw GradleException("POCKET_SIGNING_PASSWORD nao configurado")
            keyAlias = "ladywriter-pocket"
            keyPassword = System.getenv("POCKET_SIGNING_PASSWORD")
                ?: throw GradleException("POCKET_SIGNING_PASSWORD nao configurado")
            storeType = "PKCS12"
        }
    }
    buildTypes {
        getByName("debug") {
            signingConfig = signingConfigs.getByName("pocketStable")
        }
    }
}
"""

app.write_text(source, encoding="utf-8")
print(
    "ID fixo e versao crescente configurados; assinatura privada gerenciada "
    f"pelo GitHub Secrets (versionCode={10000 + int(run)})."
)
