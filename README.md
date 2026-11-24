# LadyWriter Pocket 📱

Editor Android experimental para leitura e edição de documentos ODT com foco em fidelidade visual, privacidade local e experiência fluida em telefones.

**Projeto independente do LadyWriter Library.** Compartilha apenas a marca; não depende do código, dos bancos, das funcionalidades ou do ciclo de releases do LadyWriter completo.

## Situação

Este repositório é uma extração nova e seletiva do laboratório Pocket antes hospedado em um repositório privado. Seu histórico Git começa aqui. O código de protótipos ainda **não é garantia de que cada recurso funcione no Android**. Não usar builds experimentais com o único exemplar de um manuscrito.

O trabalho é feito pelo telefone com CI no GitHub. Alvo inicial de testes: Android arm64, Moto G05. Base técnica: [Libreon](https://github.com/jainiakhil/Libreon) `v0.9.5-beta.5`, com Collabora/LibreOfficeKit.

## Prioridade atual: fluidez de página

- Navegação e rolagem sem engasgos visíveis, especialmente em ODTs extensos.
- Zoom responsivo que preserve o ponto observado, evitando saltos de página.
- Transição entre leitura e edição sem recriação desnecessária do documento.
- Restauração de cursor, seleção e página ao recolher/abrir teclado.
- Medições de latência, consumo de memória, jank e custo de repaginação no aparelho.

As variáveis ODT e o sumário são funcionalidades planejadas, **não recursos já resolvidos**. Os testes UNO desktop não comprovam editor de variáveis no Android.

## Organização

- `pocket/experiments/libreon-engine-lab/`: scripts que aplicam mudanças na base pública Libreon fixada.
- `pocket/tests/`: fixtures sintéticas e provas desktop UNO.
- `pocket/branding/`: identidade visual.
- `.github/workflows/validate-pocket.yml`: CI de patches **sem chaves de assinatura**, permitido em contribuições públicas.

## Builds de prévia pelo GitHub Actions

O workflow manual `Pocket - APK de prévia pública sem secrets` recompila o editor a partir do Libreon e gera um APK debug para `com.ladyrachelsouza.ladywriter.pocket.preview`. **É um aplicativo de teste separado**, não atualiza a versão `com.ladyrachelsouza.ladywriter.pocket` existente no telefone, e a assinatura temporária não serve para distribuição permanente. O fluxo depende da confirmação de compilação Android, que não é provada pelos testes estáticos de patches. Nunca abrir documentos pessoais únicos na prévia; usar uma cópia.

Por segurança, o build permanece exclusivamente manual na branch padrão, sem `secrets`. Antes de liberar o workflow, revisar o código da PR e integrar a fundação independente.

## Privacidade e assinatura

Nenhum manuscrito, credencial, keystore, artefato sensível ou histórico do repositório privado deve ser adicionado. **Não existe workflow público de geração de chave de assinatura.** A assinatura atual do Pocket deve permanecer em cofre restrito; uma nova chave arbitrária não atualizaria o aplicativo instalado. Não executar builds de PRs externos com secrets.

## Desenvolvimento

A integração com o motor Libreon ainda precisa de compilação, instrumentação e testes no telefone. O pipeline público inicial verifica a reprodução dos patches, não produz APK assinado. Downloads de dependências do upstream devem ser verificados por commit ou SHA-256. Arquivos de código e recursos derivados respeitam as licenças de seus respectivos projetos, inclusive GPL-3.0-or-later para as modificações derivadas do Libreon.

## Aviso de migração

**Não** importar a árvore ou o histórico Git de `LadyWriter` para cá. O LadyWriter Library e este editor Android são projetos autônomos.
