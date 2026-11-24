#!/usr/bin/env python3
"""Gera ODT sintético para teste de variáveis, sem dados de manuscritos privados."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
import xml.etree.ElementTree as ET
import sys

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
    "manifest": "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0",
}
for p,u in NS.items(): ET.register_namespace(p,u)
def q(p,n): return "{"+NS[p]+"}"+n
def e(parent,p,name,attrs=None,text=None):
    item=ET.SubElement(parent,q(p,name),{q(k.split(":")[0],k.split(":")[1]):v for k,v in (attrs or {}).items()})
    if text is not None: item.text=text
    return item
def xml(root): return ET.tostring(root,encoding="utf-8",xml_declaration=True)
def make(path):
    root=ET.Element(q("office","document-content"),{q("office","version"):"1.2"})
    aut=e(root,"office","automatic-styles")
    s=e(aut,"style","style",{"style:name":"Page1","style:family":"paragraph"})
    e(s,"style","paragraph-properties",{"fo:break-before":"page"})
    body=e(root,"office","body")
    text=e(body,"office","text")
    decls=e(text,"text","variable-decls")
    e(decls,"text","variable-decl",{"office:value-type":"string","text:name":"DataNarrativa"})
    samples=["Dia Um • Exemplo fictício","Dia Dois • Exemplo fictício"]
    for i,val in enumerate(samples):
        heading=e(text,"text","h",{"text:outline-level":"1",**({"text:style-name":"Page1"} if i else {})})
        e(heading,"text","variable-set",{"text:name":"DataNarrativa","text:display":"none","office:value-type":"string","office:string-value":val})
        heading[-1].tail="Capítulo "+str(i+1)
        e(text,"text","p",text="Texto artificial, criado exclusivamente para validar campos ODT.")
    styles=ET.Element(q("office","document-styles"),{q("office","version"):"1.2"})
    autos=e(styles,"office","automatic-styles")
    page=e(autos,"style","page-layout",{"style:name":"PM1"})
    e(page,"style","page-layout-properties",{"fo:page-width":"15.24cm","fo:page-height":"22.86cm","fo:margin-left":"2cm","fo:margin-right":"2cm","fo:margin-top":"2cm","fo:margin-bottom":"2cm"})
    masters=e(styles,"office","master-styles")
    mp=e(masters,"style","master-page",{"style:name":"Standard","style:page-layout-name":"PM1"})
    header=e(mp,"style","header")
    par=e(header,"text","p")
    e(par,"text","variable-get",{"text:name":"DataNarrativa"},samples[0])
    manifest=ET.Element(q("manifest","manifest"),{q("manifest","version"):"1.2"})
    for full,media in [("/","application/vnd.oasis.opendocument.text"),("content.xml","text/xml"),("styles.xml","text/xml")]:
        e(manifest,"manifest","file-entry",{"manifest:full-path":full,"manifest:media-type":media})
    with ZipFile(path,"w") as z:
        z.writestr("mimetype","application/vnd.oasis.opendocument.text",compress_type=ZIP_STORED)
        for name,data in [("content.xml",xml(root)),("styles.xml",xml(styles)),("META-INF/manifest.xml",xml(manifest))]:
            z.writestr(name,data,compress_type=ZIP_DEFLATED)
    with ZipFile(path) as z:
        content=ET.fromstring(z.read("content.xml"))
        heads=ET.fromstring(z.read("styles.xml"))
        definitions=list(content.iter(q("text","variable-set")))
        references=list(heads.iter(q("text","variable-get")))
        assert len(definitions)==2 and len(references)==1
        assert all(x.attrib[q("text","display")]=="none" for x in definitions)
        assert [x.attrib[q("office","string-value")] for x in definitions]==samples
    print("Fixture ODT gerada e validada estruturalmente:",path)

if __name__=="__main__":
    make(Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/pocket-datanarrativa-fixture.odt"))
