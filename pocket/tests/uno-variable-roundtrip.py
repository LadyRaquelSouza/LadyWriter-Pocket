#!/usr/bin/python3
"""Prova real de criação de SetExpression por UNO no LibreOffice desktop.

Executar via /usr/bin/python3 com python3-uno + LibreOffice instalados.
Cria um ODT SOMENTE sintético, valida duas definições textuais invisíveis
e uma exibição em cabeçalho. Não implica acesso UNO no motor Android.
"""
import subprocess
import tempfile
import time
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

import uno
from com.sun.star.beans import PropertyValue

TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"
VALUES = ("Dia Um • Exemplo fictício", "Dia Dois • Exemplo fictício")


def property_value(name, value):
    item = PropertyValue()
    item.Name = name
    item.Value = value
    return item


def connect(port):
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local
    )
    for _ in range(100):
        try:
            return resolver.resolve(
                f"uno:socket,host=localhost,port={port};urp;StarOffice.ComponentContext"
            )
        except Exception:
            time.sleep(0.1)
    raise RuntimeError("Não foi possível conectar ao LibreOffice de testes")


def create_and_check(destination: Path, port: int):
    context = connect(port)
    desktop = context.ServiceManager.createInstanceWithContext(
        "com.sun.star.frame.Desktop", context
    )
    doc = desktop.loadComponentFromURL(
        "private:factory/swriter", "_blank", 0, (property_value("Hidden", True),)
    )
    assert doc is not None
    master = doc.createInstance("com.sun.star.text.FieldMaster.SetExpression")
    master.Name = "DataNarrativa"
    # SetVariableType.STRING é 3. O valor 1 criaria SEQUENCE e corromperia
    # a semântica que estamos tentando preservar.
    master.SubType = 3

    for i, value in enumerate(VALUES):
        cursor = doc.Text.createTextCursor()
        cursor.gotoEnd(False)
        field = doc.createInstance("com.sun.star.text.TextField.SetExpression")
        field.attachTextFieldMaster(master)
        field.SubType = 3
        field.Content = value
        field.IsVisible = False
        doc.Text.insertTextContent(cursor, field, False)
        if i == 1:
            # Edita somente a segunda definição; a primeira deve permanecer igual.
            field.Content = "Dia Dois Revisado • Exemplo fictício"
        doc.Text.insertString(cursor, f"Capítulo {i + 1}\n", False)

    page_style = doc.StyleFamilies.getByName("PageStyles").getByName("Standard")
    page_style.HeaderIsOn = True
    header = page_style.HeaderText
    reference = doc.createInstance("com.sun.star.text.TextField.GetExpression")
    reference.SubType = 3
    reference.Content = "DataNarrativa"
    header.insertTextContent(header.createTextCursor(), reference, False)

    doc.TextFields.refresh()
    doc.storeAsURL(
        uno.systemPathToFileUrl(str(destination)),
        (property_value("FilterName", "writer8"),
         property_value("Overwrite", True)),
    )
    doc.close(True)

    with ZipFile(destination) as archive:
        body = ET.fromstring(archive.read("content.xml"))
        styles = ET.fromstring(archive.read("styles.xml"))
    definitions = list(body.iter(TEXT + "variable-set"))
    references = list(styles.iter(TEXT + "variable-get"))
    assert len(definitions) == 2, f"Definições: {len(definitions)}"
    assert len(references) == 1, f"Exibições: {len(references)}"
    assert all(item.get(TEXT + "name") == "DataNarrativa" for item in definitions)
    assert all(item.get(TEXT + "display") == "none" for item in definitions)
    assert tuple(item.get(OFFICE + "string-value") for item in definitions) == (
        VALUES[0], "Dia Dois Revisado • Exemplo fictício"
    )
    assert references[0].get(TEXT + "name") == "DataNarrativa"
    print("UNO tipado → ODT → XML: duas definições invisíveis, edição isolada e cabeçalho preservados")


def main():
    with tempfile.TemporaryDirectory(prefix="pocket-uno-") as temp:
        root = Path(temp)
        port = 20273
        process = subprocess.Popen(
            [
                "soffice",
                "-env:UserInstallation=" + (root / "profile").as_uri(),
                "--headless",
                "--norestore",
                "--nodefault",
                "--nologo",
                f"--accept=socket,host=localhost,port={port};urp;StarOffice.ComponentContext",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            create_and_check(root / "synthetic-fields.odt", port)
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
