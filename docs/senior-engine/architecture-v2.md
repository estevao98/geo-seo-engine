# Architecture V2 Proposal

Objetivo: propor uma arquitetura senior para evoluir o MVP sem quebrar a CLI atual antes de haver contratos estaveis. Esta proposta e decisao arquitetural, nao implementacao existente.

## Definicao Operacional De Engine Senior

Uma engine senior para este projeto deve entregar diagnostico tecnico, semantico e operacional com evidencia, risco, prioridade e proxima acao. Ela nao promete trafego, ranking, indexacao ou presenca em IA.

| Area | Definicao senior |
|---|---|
| Technical SEO | Detecta problemas tecnicos com modelos consistentes, evidencia por URL, severidade calibrada e acoes executaveis. |
| Crawlability/indexability | Avalia status, robots, noindex, x-robots-tag, canonical, redirects, sitemaps, links internos e conflitos entre sinais. |
| Rendering/JavaScript | Compara HTML inicial e renderizado, identifica conteudo/link/schema dependente de JS e riscos de soft 404. |
| Structured data/schema | Valida JSON-LD, tipos, propriedades requeridas por contexto, coerencia com conteudo visivel e riscos de markup enganoso. |
| Internal linking | Constroi grafo de links, identifica orphan pages, hubs, profundidade, anchors genericos e inconsistencias com canonicals. |
| Performance/Page Experience | Integra PSI/Lighthouse/CWV quando disponivel, separando lab data, field data, thresholds e recomendacoes tecnicas. |
| Content quality | Extrai conteudo principal e avalia utilidade, originalidade, cobertura, autoria, fontes, clareza, atualizacao e satisfacao de intencao. |
| Entity/GEO readiness | Mapeia entidade principal, entidades secundarias, evidencias textuais, schema, links internos e consistencia semantica. |
| Search Console/data integration | Usa GSC para priorizar por page/query/device/country, considerando limites, agregacao e ausencia de dados. |
| Opportunity engine | Converte diagnostico e dados em backlog priorizado por impacto, esforco, confianca, risco e dependencia. |
| Brief/cluster generation | Gera brief e clusters como artefatos de planejamento, com persona, intencao, entidades, links internos e criterios de qualidade. |
| AI visibility readiness | Simula readiness heuristico para experiencias generativas sem prometer inclusao, ranking, citacao ou trafego. |
| Reporting executivo e operacional | Separa resumo executivo, evidencias tecnicas, backlog, riscos, dependencias e proximas acoes. |
| CI/quality gates | Expoe exit codes, thresholds, contratos JSON e checks para impedir regressao tecnica. |
| Seguranca e privacidade | Evita SSRF, limita resposta, redige dados sensiveis, nao persiste credenciais e separa reports publicos de dados privados. |
| Extensibilidade | Permite config e plugins explicitamente registrados, com contratos testados e sem import dinamico inseguro. |

## Principios Arquiteturais

- Separar coleta, parsing, analise, scoring e rendering.
- Tratar URL canonical/normalized como identidade operacional central.
- Tratar issue como objeto tipado, nao string livre.
- Permitir outputs deterministas para JSON, Markdown, CSV e CI.
- Configurar comportamento por projeto sem exigir credenciais.
- Integracoes externas devem ser opcionais e degradar com mensagem clara.
- Toda recomendacao deve carregar evidencia, risco, prioridade e proxima acao.
- GEO deve ser readiness baseado em evidencia, nao promessa de presenca em IA.

## Visao De Pastas

```text
src/geo_seo_engine/
  cli.py
  core/
  config/
  http/
  crawler/
  analyzers/
  content/
  entities/
  integrations/
  scoring/
  reporting/
  opportunities/
  templates/
docs/
examples/
tests/
  fixtures/
```

## Modulos Propostos

### `src/geo_seo_engine/core/`

Responsabilidade: contratos centrais compartilhados por toda a engine.

Input: dados normalizados de URL, responses coletadas, resultados de analyzers e configuracao validada.

Output: modelos estaveis para `AuditRun`, `UrlRecord`, `FetchResult`, `Issue`, `Evidence`, `Recommendation`, `Score`, `Artifact`.

Tipos/modelos:

- `Severity`: `critical`, `high`, `medium`, `low`, `info`.
- `IssueCategory`: technical, crawlability, indexability, structured_data, content, entity, performance, security, reporting.
- `Issue`: `id`, `title`, `category`, `severity`, `url`, `evidence`, `risk`, `recommendation`, `next_action`, `confidence`.
- `Evidence`: `source`, `selector`, `value`, `expected`, `observed`, `raw_ref`.
- `UrlIdentity`: `raw_url`, `normalized_url`, `canonical_url`, `final_url`, `host`, `path`, `query`.
- `AuditRun`: `id`, `started_at`, `config`, `summary`, `artifacts`.

Dependencias permitidas: stdlib, `pydantic`, tipos internos sem depender de HTTP, crawler ou reporting.

Riscos: overengineering prematuro; schemas muito rigidos antes de casos reais.

Testes necessarios: serializacao JSON, compatibilidade de campos obrigatorios, ids de issue estaveis, enum validation e snapshots de modelos.

### `src/geo_seo_engine/config/`

Responsabilidade: carregar, validar e documentar configuracao por projeto.

Input: `geo-seo.yml`, flags CLI, variaveis de ambiente permitidas.

Output: `ProjectConfig` validado.

Tipos/modelos:

- `ProjectConfig`: `project_name`, `base_url`, `allowed_hosts`, `start_urls`, `sitemap_urls`, `include_patterns`, `exclude_patterns`, `limits`, `http`, `integrations`, `reporting`, `scoring`.
- `HttpConfig`: timeout, retries, max_bytes, user_agent, follow_redirects.
- `CrawlerConfig`: max_pages, max_depth, concurrency, delay, respect_robots.
- `PrivacyConfig`: redact_queries, redact_paths, output_policy.

Dependencias permitidas: stdlib, `pydantic`, `pyyaml`, `core`.

Riscos: carregar `.env` real por conveniencia; misturar segredo com config versionada.

Testes necessarios: config minima, config completa, erros de validacao, merge de CLI flags, exemplos YAML validos.

### `src/geo_seo_engine/http/`

Responsabilidade: cliente HTTP unico e seguro.

Input: URL normalizada, `HttpConfig`, contexto de crawl.

Output: `FetchResult` com status, final URL, headers, body limitado, bytes, redirect chain, timings, errors.

Tipos/modelos:

- `FetchRequest`: url, method, headers, purpose.
- `FetchResult`: request, status_code, final_url, headers, text/body_ref, content_type, elapsed_ms, redirect_chain, error.
- `FetchPolicy`: allowed_hosts, max_bytes, timeout, retries, backoff, private_ip_block.

Dependencias permitidas: `httpx`, `core`, `config`, stdlib.

Riscos: SSRF, download grande, redirects para host fora do escopo, logs com dados privados.

Testes necessarios: erro de rede, timeout, redirects, max bytes, host bloqueado, IP privado, user-agent, headers e content-type.

### `src/geo_seo_engine/crawler/`

Responsabilidade: descoberta e coleta multi-page com limites.

Input: `ProjectConfig`, seeds, sitemap URLs, robots, frontier.

Output: `CrawlResult`, `UrlInventory`, `LinkGraph`, artefatos CSV/JSON.

Tipos/modelos:

- `FrontierItem`: url, depth, discovered_from, source_type.
- `CrawlPage`: url identity, fetch result, extracted links, indexability hints.
- `UrlInventory`: records por URL com status, canonical, noindex, depth, source.
- `LinkEdge`: source_url, target_url, anchor, rel, discovered_in.

Dependencias permitidas: `core`, `config`, `http`, `analyzers` leves de parsing, stdlib.

Riscos: loops, crawling agressivo, explosao de URLs por parametros, violar escopo.

Testes necessarios: depth, max_pages, include/exclude, dedup, canonical identity, link extraction, robots respect opcional e sitemap seeds.

### `src/geo_seo_engine/analyzers/`

Responsabilidade: regras de auditoria por dominio tecnico.

Input: `FetchResult`, HTML inicial, HTML renderizado, `UrlInventory`, config.

Output: lista de `Issue` e resultados especificos.

Submodulos esperados:

- `page.py`: title, meta description, h1, canonical, meta robots, x-robots-tag, headings, status.
- `robots.py`: RFC 9309, sitemap directives, grupos, bloqueios e warnings.
- `sitemap.py`: urlset/index, recursao, gzip/txt, lastmod, canonical consistency.
- `structured_data.py`: JSON-LD, `@graph`, tipos, propriedades, coerencia basica.
- `open_graph.py`: OG e Twitter Cards.
- `images.py`: img, alt, src, srcset, dimensions, lazy loading, broken images.
- `hreflang.py`: alternates, return tags, canonical same language.
- `rendering.py`: diff inicial/renderizado com Playwright opcional.

Dependencias permitidas: `core`, `config`, BeautifulSoup, XML parsers, integracoes somente via interfaces.

Riscos: duplicar fetch; misturar regra com report; checks de baixa confianca com severidade alta.

Testes necessarios: fixtures HTML/XML/robots, cada issue com evidencia, golden JSON, casos negativos e severidade esperada.

### `src/geo_seo_engine/content/`

Responsabilidade: extracao e avaliacao de conteudo principal.

Input: HTML, URL, metadados, config de idioma/persona.

Output: `ContentSnapshot`, `ContentQualityResult`, issues e oportunidades.

Tipos/modelos:

- `ContentSnapshot`: title, h1, main_text, word_count, headings, tables, lists, media_refs.
- `ContentSignal`: originalidade inferida, cobertura, fontes, autoria, atualizacao, clareza, gaps.
- `SearchIntent`: informational, commercial, transactional, navigational, support, comparison.

Dependencias permitidas: `core`, BeautifulSoup, heuristicas internas; dependencias de readability somente apos decisao explicita.

Riscos: heuristicas confundirem template com conteudo; transformar avaliacao em word count; inventar fatos.

Testes necessarios: artigos, landing pages, docs, LMS, paginas vazias, conteudo em tabs, conteudo com boilerplate.

### `src/geo_seo_engine/entities/`

Responsabilidade: modelar entidades e readiness GEO.

Input: `ContentSnapshot`, structured data, links internos, config de negocio.

Output: `EntityProfile`, `GeoReadinessResult`, issues e recomendacoes.

Tipos/modelos:

- `EntityProfile`: primary_entity, secondary_entities, entity_type, evidence_spans, same_as, schema_types.
- `GeoReadinessResult`: clarity, consistency, evidence, authority, coverage, caveats.

Dependencias permitidas: `core`, `content`, `analyzers.structured_data` via resultados.

Riscos: inventar entidades; overclaim sobre IA; classificar sem evidencia textual.

Testes necessarios: paginas com entidade clara, entidade ambigua, schema contraditorio, ausencia de fonte/autoria.

### `src/geo_seo_engine/integrations/`

Responsabilidade: integrar fontes externas opcionais.

Input: config, credenciais por ambiente, URLs/inventario.

Output: dados normalizados e issues de integracao.

Submodulos:

- `search_console.py`: Search Analytics API.
- `pagespeed.py`: PageSpeed Insights API.
- `lighthouse.py`: Lighthouse local/CI quando habilitado.
- `playwright.py`: renderizacao e snapshots controlados.

Dependencias permitidas: clientes oficiais quando necessario, `http`, `core`, `config`.

Riscos: logs de credenciais, quota, dados privados, resultados incompletos, custos de execucao.

Testes necessarios: mocks de API, ausencia de credencial, erro 401/403/429, paginacao, cache e serializacao.

### `src/geo_seo_engine/scoring/`

Responsabilidade: pontuacao e priorizacao.

Input: issues, inventario, dados GSC, config de pesos.

Output: `Scorecard`, severidade final, prioridade e quality gates.

Tipos/modelos:

- `Scorecard`: technical_score, content_score, entity_score, performance_score, overall_score.
- `Priority`: impact, effort, confidence, risk, urgency.
- `QualityGateResult`: passed, failed_rules, exit_code.

Dependencias permitidas: `core`, `config`.

Riscos: score arbitrario parecer verdade absoluta; misturar severidade tecnica com impacto de negocio.

Testes necessarios: calibracao de penalidades, gates, pesos customizados, regressao de ordering.

### `src/geo_seo_engine/reporting/`

Responsabilidade: renderizar artefatos sem recalcular diagnostico.

Input: `AuditRun`, `Scorecard`, issues, oportunidades.

Output: Markdown, JSON, CSV, table.

Tipos/modelos:

- `ReportBundle`: paths, formats, generated_at.
- `ExecutiveSummary`: top risks, top actions, scorecards, dependencies.
- `OperationalBacklog`: issues agrupadas por prioridade e dono.

Dependencias permitidas: `core`, `scoring`, `opportunities`, `jinja2`, `rich`.

Riscos: vazar dados privados; reports gigantes; Markdown quebrado por conteudo externo.

Testes necessarios: golden files, escaping, truncamento, JSON schema, CSV headers.

### `src/geo_seo_engine/opportunities/`

Responsabilidade: transformar diagnosticos em oportunidades priorizadas.

Input: issues, content snapshots, entities, GSC, link graph.

Output: `Opportunity`, `Brief`, `Cluster`, backlog.

Tipos/modelos:

- `Opportunity`: title, rationale, evidence, target_url, target_intent, expected_outcome, caveats, priority.
- `Brief`: persona, intent, entity, outline, sources_needed, internal_links, quality_criteria.
- `Cluster`: pillar, supporting_pages, intents, entities, linking_plan.

Dependencias permitidas: `core`, `content`, `entities`, `integrations` normalizadas.

Riscos: gerar conteudo generico; inventar dados; criar doorway pages.

Testes necessarios: oportunidades sem GSC, com GSC, duplicatas, briefs com fontes obrigatorias, rejeicao de doorway.

### `src/geo_seo_engine/templates/`

Responsabilidade: templates versionados de reports, briefs e configs.

Input: modelos ja normalizados.

Output: arquivos renderizados.

Dependencias permitidas: `jinja2`, `core`, `reporting`.

Riscos: logica demais em template; markdown dificil de testar.

Testes necessarios: renderizacao minima, escaping, snapshots.

### `docs/`

Responsabilidade: documentacao do projeto, arquitetura, roadmap, exemplos e runbooks.

Input: decisoes arquiteturais, fontes externas e comportamento real da CLI.

Output: guias para usuarios e desenvolvedores.

Riscos: docs prometerem features ainda nao implementadas.

Testes necessarios: revisao manual, links, exemplos de comandos atuais vs futuros claramente separados.

### `examples/`

Responsabilidade: exemplos seguros, sinteticos e pequenos.

Input: dominios neutros, fixtures publicas, outputs gerados.

Output: Markdown/JSON anonimizados permitidos.

Riscos: commitar dados reais de clientes ou exports brutos.

Testes necessarios: varredura de segredos e artefatos proibidos.

### `tests/fixtures/`

Responsabilidade: fixtures HTML, XML, robots, JSON-LD, API mocks e golden reports.

Input: casos sinteticos.

Output: dados deterministas para testes.

Riscos: fixtures grandes demais; dados reais; snapshots fragilizados.

Testes necessarios: organizacao por dominio, fixtures pequenas, nomes claros.

## Fluxo De Dados V2

1. CLI carrega `ProjectConfig`.
2. URL normalization valida seeds e escopo.
3. HTTP client coleta robots/sitemap/seeds com politicas de seguranca.
4. Crawler descobre URLs por sitemap e links, respeitando limites.
5. Analyzers processam HTML, robots, sitemap, structured data, imagens, hreflang, rendering e performance.
6. Content e entities geram snapshots e readiness com evidencia.
7. Scoring calcula severidade, scorecards e quality gates.
8. Opportunities transforma diagnosticos em backlog, briefs e clusters.
9. Reporting renderiza JSON/Markdown/CSV/table.
10. CI usa exit code e thresholds configurados.

## Compatibilidade Com O MVP

- Manter comandos atuais funcionando durante a transicao.
- Introduzir modelos v2 em paralelo antes de migrar renderers.
- Converter issues antigas para `Issue` v2 por adaptador temporario somente enquanto houver comandos MVP.
- Evitar grandes reescritas sem testes de contrato.

## Decisoes Propostas

- Usar Pydantic para schemas v2 e manter dataclasses antigas ate a migracao.
- Implementar URL normalization antes do crawler.
- Implementar HTTP client centralizado antes de qualquer novo analyzer que faca rede.
- Implementar plugin registry simples e interno somente apos estabilizar analyzers v2.
- Tratar Playwright, PSI, Lighthouse e GSC como extras opcionais.
- Nao adicionar banco de dados ate haver necessidade concreta de historico ou cache persistente.

## Riscos Globais

- Crescer escopo para ferramenta tudo-em-um antes de consolidar contratos.
- Transformar GEO em marketing vazio.
- Aumentar dependencias pesadas sem modos opcionais.
- Criar reports bonitos mas pouco acionaveis.
- Ignorar privacidade ao lidar com GSC, queries, URLs privadas e relatorios de clientes.
