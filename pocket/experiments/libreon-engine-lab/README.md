# Laboratório de motor ODT no Android (Libreon)

**Experimento isolado**, não é o produto LadyWriter Pocket. Objetivo: produzir um APK de teste de um editor que realmente use LibreOfficeKit e o front-end do Collabora, para testar o requisito visual WYSIWYG em Moto G05 sem compilar o LibreOffice no Garuda.

## Base examinada

- **Projeto de terceiros:** [Libreon](https://github.com/jainiakhil/Libreon), GPL-3.0-or-later. Autoria e identidade do aplicativo original permanecem do projeto original.
- **Versão fixada:** [v0.9.5-beta.5](https://github.com/jainiakhil/Libreon/releases/tag/v0.9.5-beta.5).
- **Commit imutável esperado:** `f1f8c95c7b2dfd8a26ccdbd5e17883b6c7cbfc09`.
- **Motor pré-compilado para arm64:** extraído **somente para o experimento** do APK oficial de código aberto correspondente, conferido por SHA-256 antes da extração.
- **Limitação de licenciamento:** qualquer redistribuição de binários e modificações deve cumprir GPL-3.0+, MPL-2.0 e as licenças de dependências. Consulte documentação original e preserve avisos.
- **Código do LadyWriter principal permanece intocado.** A clonagem de terceiros ocorre somente no runner temporário do Actions.

## Por que este teste?

A base Collabora requer o motor compilado primeiro. Os executores hospedados padrão para repositórios privados têm espaço restrito (tipicamente 14 GB). Compilar o motor completo sem dimensionamento é arriscado. O Libreon possui um editor Android WYSIWYG já funcional e um APK oficial com o motor, permitindo ensaiar uma reconstrução **a partir de código-fonte fixado + binários de release correspondentes**.

**Isto não valida automaticamente:** fidelidade de fundos/cabeçalhos em ODTs complexos, campos `DataNarrativa`, comentários, sumários, estabilidade em 1.201 páginas ou segurança de salvamento no Moto G05. Esses pontos precisam ser testados manualmente em cópias.

## Protocolo de compilação na nuvem

Workflow [Pocket - Laboratorio motor ODT](https://github.com/LadyRaquelSouza/LadyWriter-Pocket/actions/workflows/pocket-engine-lab.yml):

1. Clona **Libreon** no commit acima dentro do runner.
2. Baixa o APK oficial arm64 desse release e verifica SHA-256 publicado no GitHub.
3. Extrai bibliotecas do motor LibreOffice/Collabora e recursos correspondentes para `third_party/lok/` do checkout temporário.
4. Obtém PDFium a partir do upstream, ajusta apenas o filtro de ABI para ARM64 e compila APK de depuração usando Gradle.
5. Publica o APK como artefato do Actions se o build passar.

Não envia manuscritos pessoais nem depende de SSD local. O laboratório é uma dependência experimental upstream, **não** um fork aprovado como base permanente do Pocket.

## Teste no Moto G05

- Instalar como aplicativo **Libreon de laboratório** (nome do upstream).
- Usar **cópia** de um ODT de teste, nunca o único original.
- Observar fundos, fontes, cabeçalhos, rodapés, quebra de página e digitação.
- Conferir no computador o ODT salvo após a edição.
- Medir abertura e navegação em documento grande; reportar travamentos.
- Registrar se a variável invisível no corpo altera a data exibida no cabeçalho depois de repaginar.

### Não confundir produtos

- **Sonda LadyWriter Pocket 0.1.0:** validou instalação e escolha de ODT; não edita.
- **Libreon Lab:** experimento com motor real de outro projeto; pode editar, mas ainda precisa demonstrar os requisitos no G05.
- **LadyWriter Pocket final:** editor especializado que desenvolveremos após validar arquitetura e licenças.

## Fontes

- [Código e README do Libreon](https://github.com/jainiakhil/Libreon)
- [Arquitetura do Libreon](https://github.com/jainiakhil/Libreon/blob/v0.9.5-beta.5/docs/architecture.md)
- [Licenças de terceiros no Libreon](https://github.com/jainiakhil/Libreon/blob/v0.9.5-beta.5/docs/licenses.md)
- [Instruções oficiais Collabora Android](https://www.collaboraoffice.org/post/build-code-android/)
