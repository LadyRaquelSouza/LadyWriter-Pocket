#!/usr/bin/env python3
"""Prova independente: SetExpression por posição no corpo, GetExpression no cabeçalho.

Roda no LibreOffice desktop de teste, nunca no manuscrito real. Requer:
  /usr/bin/python3 com python3-uno; soffice; pdftotext (poppler-utils).
Não demonstra ainda que o app Android consiga inserir/editar campos.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import time
import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.style.BreakType import PAGE_BEFORE

def prop(name, value):
    item = PropertyValue()
    item.Name = name
    item.Value = value
    return item

def connect(port):
    context = uno.getComponentContext()
    resolver = context.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", context
    )
    for _ in range(60):
        try:
            return resolver.resolve(
                f"uno:socket,host=localhost,port={port};urp;StarOffice.ComponentContext"
            )
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("LibreOffice UNO não iniciou")

def main():
    with tempfile.TemporaryDirectory(prefix="pocket-fields-proof-") as folder:
        work = Path(folder)
        port = 20189
        office = subprocess.Popen(
            ["soffice", f"-env:UserInstallation={uno.systemPathToFileUrl(str(work / 'profile'))}",
             "--headless", "--norestore", "--nodefault",
             f"--accept=socket,host=localhost,port={port};urp;StarOffice.ServiceManager"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            ctx = connect(port)
            desktop = ctx.ServiceManager.createInstanceWithContext(
                "com.sun.star.frame.Desktop", ctx
            )
            doc = desktop.loadComponentFromURL(
                "private:factory/swriter", "_blank", 0, (prop("Hidden", True),)
            )
            try:
                master = doc.createInstance(
                    "com.sun.star.text.FieldMaster.SetExpression"
                )
                master.Name = "DataNarrativa"
                master.SubType = 3  # SetVariableType.STRING, NÃO SEQUENCE (1)
                style = doc.StyleFamilies.getByName("PageStyles").getByName("Standard")
                style.HeaderIsOn = True
                header = style.HeaderText
                get = doc.createInstance("com.sun.star.text.TextField.GetExpression")
                get.Content = "DataNarrativa"
                get.SubType = 3
                header.insertTextContent(header.createTextCursor(), get, False)

                text = doc.Text
                cursor = text.createTextCursor()
                assignments = []
                values = ["Dia Um", "Dia Dois", "Dia Três"]
                for i, value in enumerate(values):
                    if i:
                        text.insertControlCharacter(cursor, PARAGRAPH_BREAK, False)
                        cursor.BreakType = PAGE_BEFORE
                    field = doc.createInstance(
                        "com.sun.star.text.TextField.SetExpression"
                    )
                    field.attachTextFieldMaster(master)
                    field.SubType = 3
                    field.Content = value
                    field.IsVisible = False
                    text.insertTextContent(cursor, field, False)
                    assignments.append(field)
                    text.insertString(cursor, f"Capítulo {i + 1}\n", False)
                    text.insertString(cursor, "Texto de teste fictício. " * 25, False)

                # Edita exclusivamente a atribuição intermediária.
                assignments[1].Content = "Dia Dois Corrigido"
                doc.TextFields.refresh()
                odt = work / "variaveis-posicionais.odt"
                pdf = work / "variaveis-posicionais.pdf"
                doc.storeAsURL(
                    uno.systemPathToFileUrl(str(odt)),
                    (prop("FilterName", "writer8"), prop("Overwrite", True))
                )
                doc.storeToURL(
                    uno.systemPathToFileUrl(str(pdf)),
                    (prop("FilterName", "writer_pdf_Export"), prop("Overwrite", True))
                )
            finally:
                doc.close(True)

            pages = subprocess.check_output(
                ["pdftotext", "-layout", str(pdf), "-"], text=True
            ).split("\f")
            pages = [p for p in pages if p.strip()]
            expected = ["Dia Um", "Dia Dois Corrigido", "Dia Três"]
            assert len(pages) == 3, f"Esperadas 3 páginas, vieram {len(pages)}"
            for index, (page, value) in enumerate(zip(pages, expected)):
                first_line = page.strip().splitlines()[0].strip()
                assert first_line == value, (
                    f"Página {index + 1}: cabeçalho {first_line!r}, esperado {value!r}"
                )
                assert f"Capítulo {index + 1}" in page
            from zipfile import ZipFile
            from xml.etree import ElementTree as ET
            ns = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
            with ZipFile(odt) as archive:
                root = ET.fromstring(archive.read("content.xml"))
                styles = ET.fromstring(archive.read("styles.xml"))
            sets = list(root.iter(ns + "variable-set"))
            gets = list(styles.iter(ns + "variable-get"))
            assert len(sets) == 3, "Atribuições deveriam permanecer em 3 locais"
            assert len(gets) == 1, "Cabeçalho foi montado uma vez"
            assert all(v not in pages[i] for i, v in enumerate(
                ["Dia Dois Corrigido", "Dia Três", "Dia Um"]
            )), "Uma atribuição alterou cabeçalho de outra página"
            print("APROVADO: 3 atribuições, 1 campo Get no cabeçalho, "
                  "edição localizada e paginação preservada.")
        finally:
            office.terminate()
            try:
                office.wait(timeout=5)
            except subprocess.TimeoutExpired:
                office.kill()

if __name__ == "__main__":
    main()
