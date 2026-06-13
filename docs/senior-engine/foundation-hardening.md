# Foundation hardening

Este documento descreve os contratos atuais da fundacao do `geo-seo-engine` apos as issues #3 a #9. Ele serve como checklist antes de criar novas camadas como image SEO, social metadata, hreflang, rendering, content, GEO entities ou integracoes externas.

## Camadas da fundacao

`src/geo_seo_engine/core/` define modelos compartilhados e utilitarios puros. `Severity`, `IssueCategory`, `Evidence` e os modelos de issue/audit sao contratos estaveis para achados, evidencia, risco, recomendacao e proxima acao. `normalize_url`, `resolve_url` e `is_same_site` resolvem identidade de URL sem fazer rede.

`src/geo_seo_engine/config/` valida configuracao de projeto. `ProjectConfig` centraliza `base_url`, hosts permitidos, URLs iniciais, padroes de inclusao/exclusao, politicas HTTP, crawler, privacidade e integracoes. A configuracao decide escopo, mas nao executa crawling nem requests.

`src/geo_seo_engine/http/` e a unica camada fundacional com permissao direta para fazer rede. `HttpClient` retorna `FetchResult` e concentra timeout, redirects, user-agent, limite de bytes, retries e bloqueio opcional de hosts privados. Testes de integracao devem injetar fake client ou `httpx.MockTransport`.

`src/geo_seo_engine/crawler/` descobre URLs internas com uma frontier FIFO limitada por `CrawlOptions`. Ele pode fazer rede apenas por meio de um `HttpClient` injetado ou criado internamente. O crawler extrai links estaticos de HTML, respeita hosts permitidos, deduplica URLs normalizadas e registra URLs ignoradas com motivo.

`src/geo_seo_engine/inventory/` transforma `CrawlResult` em inventario. `build_url_inventory` nao faz rede; ele resume paginas ja buscadas em `InventoryResult`, status codes, content types, profundidade, erros, redirects e skipped URLs.

`src/geo_seo_engine/technical/` transforma inventario em findings tecnicos. `run_technical_audit` nao faz rede; ele consome `InventoryResult` e emite `TechnicalAuditFinding` com evidencia, risco, recomendacao, proxima acao, categoria e severidade.

`src/geo_seo_engine/cli.py` orquestra comandos publicos. A CLI pode disparar rede apenas quando chama funcoes que passam pelo crawler/HTTP client. Ela deve preservar saidas JSON estaveis para automacao e testes.

## Quem pode fazer rede

Permitido:

- `HttpClient.fetch` e `fetch_url` em `src/geo_seo_engine/http/`.
- `crawl_site`, indiretamente, apenas por meio de `HttpClient`.
- comandos CLI que chamam `crawl_site`, como `geo crawl`, `geo inventory` e `geo audit-technical`.

Nao permitido:

- `core`: modelos e URL utilities devem ser puros.
- `config`: validacao de configuracao nao deve buscar recursos externos.
- `inventory`: deve consumir somente `CrawlResult`.
- `technical`: deve consumir somente `InventoryResult`.
- testes de fundacao: devem usar fake HTTP, fake client ou `MockTransport`.

## Fluxo principal

O fluxo fundacional e:

```text
crawl_site(start_url, CrawlOptions, HttpClient)
  -> CrawlResult
build_url_inventory(CrawlResult)
  -> InventoryResult
run_technical_audit(InventoryResult, TechnicalAuditOptions)
  -> TechnicalAuditResult
```

`crawl_site` normaliza o start URL, limita escopo por host, busca HTML, extrai links internos e registra paginas, descobertas, skipped URLs e erros.

`build_url_inventory` preserva as URLs crawleadas e calcula summaries: total de paginas, HTML/non-HTML, sucesso, redirects, erros, skipped URLs, profundidade maxima, limite de paginas e contagens por status/content type.

`run_technical_audit` interpreta o inventario e emite findings controlados como status diferente de 200, erro de fetch, URL non-HTML, redirect, pagina profunda, zero links, limite de paginas atingido, muitos skipped URLs e final URLs duplicadas.

## Boundaries entre modulos

`core` nao deve importar crawler, inventory, technical, analyzers ou CLI.

`config` pode ser usado por HTTP/crawler/CLI, mas nao deve depender deles.

`http` pode depender de configuracao HTTP, mas nao deve conhecer regras de auditoria.

`crawler` pode depender de `core` e `http`, mas nao deve produzir findings tecnicos.

`inventory` pode depender dos modelos do crawler, mas nao deve refazer requests nem extrair conteudo.

`technical` pode depender do inventario e dos modelos core, mas nao deve crawlear, renderizar JavaScript ou chamar APIs externas.

`cli` pode orquestrar as camadas, serializar JSON e escrever arquivos, mas nao deve duplicar regras de auditoria.

## Comandos CLI principais

`geo crawl URL` executa um crawl interno limitado e retorna `CrawlResult` em JSON.

`geo inventory URL` executa crawl e monta `InventoryResult` em JSON.

`geo audit-technical URL` executa crawl, inventory e auditoria tecnica, retornando `TechnicalAuditResult` em JSON.

Flags importantes incluem `--max-pages`, `--max-depth`, `--allowed-host`, `--include-pattern`, `--exclude-pattern`, `--max-depth-warning`, `--high-skipped-urls-warning`, `--no-non-html-findings`, `--no-redirect-findings` e `--no-zero-links-findings`.

## Politica de promessas

O projeto deve entregar diagnostico tecnico e operacional com evidencia, risco, prioridade e proxima acao. Ele nao deve prometer ranking, trafego, indexacao, citacao, presenca ou visibilidade em experiencias de IA.

Recomendacoes devem ser formuladas como melhoria de qualidade, rastreabilidade, experiencia, consistencia tecnica ou capacidade de diagnostico. Quando uma inferencia for incerta, o output deve deixar claro que se trata de hipotese ou sinal, nao garantia.

## Validacao antes de novas camadas

Antes de implementar uma nova camada, valide a fundacao com:

```bash
python -m pytest
git diff --check
```

Para qualquer novo teste de integracao, confirme que:

- nao ha rede real em testes;
- HTML sintetico cobre o comportamento esperado;
- `crawl_site -> build_url_inventory -> run_technical_audit` continua funcionando;
- summaries permanecem coerentes com as paginas crawleadas;
- findings incluem evidencia, risco, recomendacao e proxima acao;
- nao foram adicionados artefatos brutos, segredos, `.env`, `__pycache__`, `.pyc`, exports privados ou outputs de scanners.

Se um bug real aparecer durante esse hardening, corrija o menor ponto possivel sem antecipar features de produto fora do escopo.
