#!/usr/bin/env python3
"""Otimização conservadora de controles de zoom: deduplica comandos por frame.

NÃO altera o zoom de gesto do Collabora nem reescreve geometria/paginação.
Executar após patch-editorial-ux.py e antes de patch-stable-signing.py.
"""
from pathlib import Path

path = Path("engine-office/src/main/java/dev/offlineoffice/office/OfficeDocument.kt")
source = path.read_text(encoding="utf-8")
old = """              const map = app.map;
              const zoomTo = (level) => app.zoomControl.zoomTo(
                Math.max(map.getMinZoom(), Math.min(map.getMaxZoom(), level)), undefined, false);"""
new = """              const map = app.map;
              // Uma rajada de toques não precisa solicitar vários lotes de tiles
              // no mesmo frame. Preserva o zoom discreto e sem animação do upstream.
              let pendingZoom = null;
              let scheduledZoom = 0;
              let requestedZoom = null;
              map.on('zoomend', () => { requestedZoom = null; });
              const zoomTo = (level) => {
                pendingZoom = Math.max(map.getMinZoom(), Math.min(map.getMaxZoom(), level));
                requestedZoom = pendingZoom;
                if (scheduledZoom) return;
                scheduledZoom = requestAnimationFrame(() => {
                  scheduledZoom = 0;
                  const next = pendingZoom;
                  pendingZoom = null;
                  if (next !== null && next !== map.getZoom())
                    app.zoomControl.zoomTo(next, undefined, false);
                });
              };
              const zoomStep = (delta) => zoomTo(
                (requestedZoom === null ? map.getZoom() : requestedZoom) + delta);"""
if source.count(old) != 1:
    raise SystemExit("Controle de zoom original não corresponde ao upstream fixado.")
source = source.replace(old, new, 1)
for a,b in [
    ("() => zoomTo(map.getZoom() - 1)", "() => zoomStep(-1)"),
    ("() => zoomTo(map.getZoom() + 1)", "() => zoomStep(1)")
]:
    if source.count(a) != 1:
        raise SystemExit("Botão zoom esperado ausente: " + a)
    source = source.replace(a,b,1)
path.write_text(source,encoding="utf-8")
print("Pocket: comandos de zoom agrupados por frame, sem animação intermediária.")
