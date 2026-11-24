# Frente principal: fluidez do editor no Android

**Estado:** planejamento técnico e critérios mensuráveis; implementação ainda não testada no Moto G05.

## Alvo

O LadyWriter Pocket deve abrir e editar documentos ODT com fidelidade à paginação Writer, sem comprometer navegação, zoom ou a passagem entre leitura e edição. A base atual utiliza Libreon, WebView Collabora, LibreOfficeKit e uma surface Android entregue por processo `:office`; **não** existe renderer próprio escrito do zero.

## Hipóteses a medir antes de reescrever o motor

1. **Zoom e rolagem:** custo de tiles, animações de zoom, invalidação de camada e repaginação. Analisar eventos do front-end e limites do motor, não substituir todo o renderizador sem medição.
2. **Retenção de posição:** identificar coordenadas de documento/zoom e página âncora; nas trocas de modo preservar viewport, posição visível e, em edição, seleção/cursor quando possível.
3. **Leitura ↔ edição:** reutilizar a mesma sessão `OfficeDocument`, `WebView`, `SurfaceControlViewHost`; medir se o editor muda `editmode` ou reinicializa páginas.
4. **Teclado:** detectar mudanças de IME sem duplicar reflow; retorno Android deve esconder IME antes de sair do documento.
5. **Telhas (tiles) e memoria:** medir pedidos repetidos, invalidates, quadros descartados, uso de RAM e tempo até estabilizar após zoom.

## Instrumentação sem dados privados

Criar um ODT sintético paginado (curto/médio/longo) com cabeçalhos, rodapés, estilos, fontes redistribuíveis, campos fictícios e imagens criadas para teste. Não copiar o texto, as imagens nem as fontes embutidas do manuscrito privado.

Instrumentar logs com estatísticas agregadas, sem nomes de arquivos, paths locais ou conteúdo selecionado. Evitar logar mensagens integrais do documento. Capturar:
- intervalo entre gesto e estabilidade de viewport;
- quantidade de `tile`/`tilecombine` durante zoom/rolagem;
- tempo e número de repaginações; saltos de âncora e reposicionamento;
- tempo de alternância leitura/edição e perda de seleção;
- percentis de jank e memória antes/depois.

## Ordem de implantação

- **F0:** baseline no Moto G05 com ODT sintético e instrumentação sem conteúdo.
- **F1:** transições leitura/edição sem recarga do documento.
- **F2:** zoom ancorado no gesto, sem saltos perceptíveis, preservando página visível.
- **F3:** controle de invalidação/repetição de tiles e previsibilidade da rolagem.
- **F4:** compatibilidade teclado, rotação, voltar e retomada de app.
- **F5:** regressão de fidelidade ODT, salvamento, Undo e estabilidade.

## Aceite

Sem perda de conteúdo, sem redimensionamento irreversível de páginas, sem alteração involuntária de estilo/campo e sem novo pacote Android. Medir resultado no dispositivo: CI de patches sozinho não prova suavidade nem correção visual.

**Não confundir essa frente com o gerenciador de variáveis:** ele permanece pendência separada.
