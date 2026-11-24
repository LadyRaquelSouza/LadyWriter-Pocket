#!/usr/bin/env python3
"""Teste sem Android SDK, APK ou chave real para o patch de identidade/assinatura."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "experiments/libreon-engine-lab/patch-stable-signing.py"
FAKE_GRADLE = """plugins {
    alias(libs.plugins.android.application)
}

android {
    namespace = "dev.offlineoffice.app"
    defaultConfig {
        applicationId = "dev.libreon.app"
        minSdk = 31
        versionCode = 10
        versionName = "0.9.5-beta.5"
    }
}
"""


class StableSigningPatchTest(unittest.TestCase):
    def test_patch_does_not_write_secret_and_increases_version(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            app = base / "app"
            app.mkdir()
            gradle = app / "build.gradle.kts"
            gradle.write_text(FAKE_GRADLE)
            key = base / "key.p12"
            key.write_bytes(b"fake-key-not-valid")
            env = dict(os.environ,
                POCKET_SIGNING_PASSWORD="test-only-password-123456",
                POCKET_KEYSTORE_FILE=str(key),
                GITHUB_RUN_NUMBER="27",
            )
            proc = subprocess.run(
                [sys.executable, str(SCRIPT)], cwd=base, env=env,
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            result = gradle.read_text()
            self.assertIn('applicationId = "com.ladyrachelsouza.ladywriter.pocket"', result)
            self.assertIn('versionCode = 10027', result)
            self.assertIn('versionName = "0.2.0-laboratorio.27"', result)
            self.assertIn('signingConfig = signingConfigs.getByName("pocketStable")', result)
            self.assertNotIn("test-only-password-123456", result)
            self.assertNotIn("test-only-password-123456", proc.stdout + proc.stderr)
            self.assertNotIn(str(key), result)

    def test_no_secret_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            app = base / "app"
            app.mkdir()
            gradle = app / "build.gradle.kts"
            gradle.write_text(FAKE_GRADLE)
            env = {k: v for k, v in os.environ.items()
                   if k not in {"POCKET_SIGNING_PASSWORD", "POCKET_KEYSTORE_FILE"}}
            env["GITHUB_RUN_NUMBER"] = "1"
            proc = subprocess.run(
                [sys.executable, str(SCRIPT)], cwd=base, env=env,
                capture_output=True, text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(gradle.read_text(), FAKE_GRADLE)


if __name__ == "__main__":
    unittest.main()
