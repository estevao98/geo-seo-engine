# geo-seo-engine

CLI operacional para auditorias iniciais de SEO técnico e GEO em páginas, robots.txt, sitemaps e sites públicos.

## O que a ferramenta faz hoje

O MVP atual entrega uma CLI chamada `geo` com estes comandos:

- `geo version`: mostra a versão instalada.
- `geo init`: cria um `geo-seo.yml` seguro para configurar um projeto.
- `geo config validate --config geo-seo.yml`: valida a configuração YAML do projeto.
- `geo audit-page <url>`: audita uma página HTML pública.
- `geo audit-sitemap <url>`: audita um sitemap XML ou sitemap index.
- `geo audit-robots <url>`: audita um arquivo robots.txt.
- `geo audit-site <url>`: executa uma auditoria agregada de página, robots.txt, sitemap e structured data JSON-LD.

A auditoria agregada de site também gera:

- score geral do site;
- issues classificadas por severidade;
- `next_action` com a ação prioritária;
- recomendações ordenadas por severidade;
- auditoria básica de structured data/schema via blocos JSON-LD.

## Instalação local

Requisitos:

- Python 3.12 ou superior.

Instale em modo editável a partir da raiz do repositório:

```bash
python -m pip install -e ".[dev]"
```

Confirme a instalação:

```bash
geo version
```

Observação: a flag `geo --version` ainda não está disponível no MVP atual; use o subcomando `geo version`.

## Comandos principais

Criar e validar configuração de projeto:

```bash
geo init
geo config validate --config geo-seo.yml
```

Um exemplo versionado e sem segredos está disponível em [`examples/geo-seo.example.yml`](examples/geo-seo.example.yml).

Auditar uma página pública:

```bash
geo audit-page https://example.com
```

Auditar um sitemap público:

```bash
geo audit-sitemap https://www.google.com/sitemap.xml
```

Auditar um robots.txt público:

```bash
geo audit-robots https://example.com/robots.txt
```

Gerar relatório markdown de auditoria agregada de site:

```bash
geo audit-site https://example.com --format markdown --output /tmp/site-audit-example.md
```

Formatos disponíveis hoje:

- `audit-page`: `table` e `json`.
- `audit-sitemap`: `table` e `json`.
- `audit-robots`: `table` e `json`.
- `audit-site`: `table`, `json` e `markdown`.

## Exemplo resumido de saída

Exemplo de campos do relatório gerado por `geo audit-site --format markdown`:

Um relatório Markdown versionado e seguro está disponível em [`examples/site-audit-example.md`](examples/site-audit-example.md). Ele usa o domínio público neutro `https://example.com` e não contém dados privados, tokens ou exports reais.

```markdown
# Site Audit Report

## Summary

| Field | Value |
|---|---|
| URL | `https://example.com` |
| Score | `75` |
| Next action | `Corrigir a rota do sitemap ou publicar um sitemap XML válido acessível por HTTP 200.` |
| Total issues | `3` |
| Critical issues | `0` |
| High issues | `1` |
| Medium issues | `1` |
| Low issues | `1` |

## Structured Data

| Field | Value |
|---|---|
| JSON-LD blocks | `0` |
| Valid JSON-LD blocks | `0` |
| Invalid JSON-LD blocks | `0` |
| Types | `—` |
```

Os valores variam conforme a URL auditada e as respostas HTTP coletadas no momento da execução.

## Como interpretar o relatório

`score` é a pontuação geral calculada a partir das issues encontradas. A pontuação começa em `100` e subtrai penalidades por severidade: `critical` remove 30 pontos, `high` remove 15, `medium` remove 7 e `low` remove 3. O mínimo exibido é `0`.

`severity` classifica cada issue como `critical`, `high`, `medium` ou `low`. Essa classificação prioriza riscos técnicos como página sem HTTP 200, `noindex`, bloqueios amplos em robots.txt, sitemap inacessível e problemas relevantes de sinais semânticos.

`next_action` é a primeira ação recomendada depois de ordenar as issues por severidade. Quando não há issues, o campo fica sem ação prioritária.

`recommendations` lista a ação sugerida e o motivo para cada issue conhecida. As recomendações são geradas a partir das issues detectadas e também seguem a ordem de severidade.

`structured data audit` verifica blocos `<script type="application/ld+json">` na página auditada pelo comando `audit-site`. A auditoria conta blocos JSON-LD, valida sintaxe JSON, extrai valores `@type` e reporta issues como `missing`, `invalid_json_ld` e `missing_type`.

## Status do MVP

Concluído no MVP atual:

- CLI instalável via entrypoint `geo`.
- Auditoria técnica básica de página HTML pública.
- Auditoria de robots.txt.
- Auditoria de sitemap XML e sitemap index.
- Auditoria agregada de site.
- Relatório em tabela, JSON e markdown conforme o comando.
- Score geral do site.
- Severidade por issue.
- Próxima ação prioritária.
- Recomendações ordenadas por severidade.
- Auditoria básica de structured data JSON-LD.

## Roadmap curto

Próximos incrementos planejados:

- Expandir cobertura de testes e fixtures de auditoria.
- Melhorar mensagens de erro e validação de entrada da CLI.
- Adicionar alias `geo --version` para o comando de versão.
- Ampliar regras de recomendação para novas issues técnicas.
- Evoluir relatórios sem prometer ganho de ranking, indexação ou presença em respostas de IA.

## Planejamento senior

Uma pesquisa critica e operacional para evoluir o MVP em uma engine senior esta em [`docs/senior-engine/`](docs/senior-engine/). Ela inclui fontes pesquisadas, gap analysis, arquitetura v2, roadmap faseado, prompt pack para implementacao futura e comandos sugeridos para issues GitHub.

## Avisos de segurança

- Não commitar `.env`.
- Use `.env.example` apenas com nomes de variáveis e valores vazios ou sintéticos.
- Não commitar relatórios com dados privados.
- Não commitar exports brutos de clientes.
- Não commitar tokens, credenciais, dumps de banco ou arquivos de configuração sensíveis.
- Antes de publicar ou abrir PR, consulte [`SECURITY.md`](SECURITY.md) e rode a varredura recomendada.

## Validação local e CI

O repositório possui gates locais e em GitHub Actions para manter testes,
higiene de diff, smoke checks de import/CLI e bloqueio de arquivos gerados ou
sensíveis alinhados ao fluxo de revisão.

Antes de finalizar uma mudança, rode:

```bash
git status --short
git diff --stat
git diff --check
python -m geo_seo_engine.quality_gates
python -m pytest
```

O CI usa Python 3.13, instala o pacote com dependências de desenvolvimento,
executa smoke checks offline-safe (`import geo_seo_engine` e `geo version`) e
falha com mensagem objetiva se houver arquivos bloqueados versionados.

## O que este repositório não promete

- Não promete crescimento de tráfego.
- Não promete indexação garantida.
- Não promete aparecer em respostas de IA.
- Não usa black hat SEO.
- Não cria conteúdo em massa sem validação.
