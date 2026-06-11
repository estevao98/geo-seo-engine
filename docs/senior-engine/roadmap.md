# Senior Engine Roadmap

Objetivo: transformar o MVP em engine senior em fases pequenas, testaveis e seguras. Este roadmap nao afirma que as features ja existem.

## Ordem Recomendada

A ordem prioriza contratos, seguranca e identidade de URL antes de crawler, dados e automacao. Sem isso, features avancadas geram duplicacao e relatorios inconsistentes.

## Fases

### 1. Architecture v2 e schemas estaveis

Objetivo: criar contratos centrais para resultados, issues, evidencia, recomendacoes, score e audit run.

Por que vem nesta ordem: sem schema, cada nova feature reforca issues como strings e aumenta acoplamento.

Entregaveis: `core/models.py`, enums, adaptador inicial de issues legadas, docs de contrato.

Arquivos provaveis: `src/geo_seo_engine/core/`, `tests/test_core_models.py`, `docs/architecture.md`.

Comandos CLI novos: nenhum obrigatorio.

Criterios de aceite: modelos serializam para JSON; cada issue tem `id`, `severity`, `category`, `evidence`, `risk`, `next_action`; testes passam.

Testes necessarios: validacao Pydantic, serializacao, campos obrigatorios, adaptador de strings legadas.

Riscos: overengineering e quebra prematura da CLI.

Dependencias: Pydantic ja existe.

Esforco: M.

Obrigatorio: sim.

### 2. Config por projeto

Objetivo: permitir `geo-seo.yml` com base_url, escopo, limites, HTTP, reporting, privacidade e integracoes.

Por que vem nesta ordem: crawler e integracoes precisam de escopo e limites antes de rodar.

Entregaveis: loader YAML, modelos de config, `geo init`, `geo config validate`, exemplo seguro.

Arquivos provaveis: `src/geo_seo_engine/config/`, `examples/geo-seo.example.yml`, `tests/test_config.py`.

Comandos CLI novos: `geo init`, `geo config validate --config geo-seo.yml`.

Criterios de aceite: config minima valida; config invalida falha com mensagem clara; nenhum segredo em exemplo.

Testes necessarios: defaults, merge com flags, allowed_hosts, limites, privacy config.

Riscos: incentivar commit de config com dados privados.

Dependencias: `pyyaml`, Pydantic.

Esforco: M.

Obrigatorio: sim.

### 3. URL normalization

Objetivo: criar identidade de URL consistente para crawl, sitemap, canonical e links.

Por que vem nesta ordem: dedup e grafo dependem de normalizacao.

Entregaveis: normalizer, regras de query tracking, fragment removal, urljoin, host normalization, testes de casos.

Arquivos provaveis: `src/geo_seo_engine/core/url.py`, `tests/test_url_normalization.py`.

Comandos CLI novos: opcional `geo normalize-url <url> --base <base>` para debug.

Criterios de aceite: URLs relativas resolvem; tracking params removidos quando configurado; query preservada quando relevante.

Testes necessarios: http/https, www, porta, slash, fragment, query, IDN se suportado, URL invalida.

Riscos: normalizar agressivamente e perder URLs distintas.

Dependencias: stdlib `urllib.parse`.

Esforco: M.

Obrigatorio: sim.

### 4. HTTP client centralizado

Objetivo: substituir fetches dispersos por cliente unico com politica de seguranca.

Por que vem nesta ordem: reduz duplicacao e habilita crawler seguro.

Entregaveis: `FetchRequest`, `FetchResult`, `HttpClient`, limites de bytes, redirects controlados, bloqueio de host privado.

Arquivos provaveis: `src/geo_seo_engine/http/client.py`, `tests/test_http_client.py`.

Comandos CLI novos: nenhum obrigatorio.

Criterios de aceite: page/robots/sitemap podem receber `FetchResult` ou cliente injetado; erros padronizados.

Testes necessarios: timeout, 404, 500, redirect, redirect fora do escopo, max bytes, headers.

Riscos: quebrar testes atuais; falso positivo de SSRF em uso local legitimo.

Dependencias: `httpx`.

Esforco: M.

Obrigatorio: sim.

### 5. Crawler multi-page

Objetivo: implementar crawl de paginas dentro do escopo com frontier, dedup, profundidade e max_pages.

Por que vem nesta ordem: precisa de config, URL normalization e HTTP client.

Entregaveis: frontier, crawl loop, extracao de links, politeness simples, `CrawlResult`.

Arquivos provaveis: `src/geo_seo_engine/crawler/`, `tests/test_crawler.py`.

Comandos CLI novos: `geo crawl <url> --max-pages 100 --depth 2 --format json`.

Criterios de aceite: respeita max_pages/depth/scope; dedup funciona; sem rede real nos testes.

Testes necessarios: links relativos, nofollow, fragments, loops, include/exclude, host externo.

Riscos: crawling agressivo; explosao de URLs.

Dependencias: fases 2-4.

Esforco: L.

Obrigatorio: sim.

### 6. URL inventory audit

Objetivo: produzir inventario de URLs com status, origem, profundidade, canonical, noindex e issues.

Por que vem nesta ordem: transforma crawl em artefato operacional.

Entregaveis: `UrlInventory`, export JSON/CSV/Markdown summary.

Arquivos provaveis: `src/geo_seo_engine/crawler/inventory.py`, `src/geo_seo_engine/reporting/csv.py`.

Comandos CLI novos: `geo audit-inventory <url> --format csv --output inventory.csv`.

Criterios de aceite: inventario tem uma linha por URL normalizada; fontes registradas; CSV valido.

Testes necessarios: duplicatas, canonical diferente, noindex, status diverso, output CSV.

Riscos: confundir URL descoberta com URL indexavel.

Dependencias: fase 5.

Esforco: M.

Obrigatorio: sim.

### 7. Technical SEO avancado

Objetivo: expandir checks tecnicos com base no inventario.

Por que vem nesta ordem: checks avancados precisam de varias URLs.

Entregaveis: canonical conflicts, redirect chains, x-robots-tag, duplicate titles/descriptions, thin metadata, status classes.

Arquivos provaveis: `src/geo_seo_engine/analyzers/technical.py`, `tests/test_technical_audit.py`.

Comandos CLI novos: `geo audit-technical <url>`.

Criterios de aceite: issues v2 com evidencia e severidade; nao duplica regras MVP sem necessidade.

Testes necessarios: redirect loops, duplicate metadata, canonical mismatch, noindex header.

Riscos: severidade exagerada para problemas contextuais.

Dependencias: fases 1, 5, 6.

Esforco: L.

Obrigatorio: sim.

### 8. Image audit

Objetivo: auditar imagens para descoberta, acessibilidade basica e performance operacional.

Por que vem nesta ordem: depende de parsing de paginas e inventario.

Entregaveis: checks de `img src`, `alt`, `picture` fallback, lazy loading, broken images opcional.

Arquivos provaveis: `src/geo_seo_engine/analyzers/images.py`, fixtures HTML.

Comandos CLI novos: incluido em `audit-technical` ou `geo audit-images`.

Criterios de aceite: reporta evidencias por seletor/URL; nao classifica alt vazio decorativo como erro automaticamente sem contexto.

Testes necessarios: img normal, picture, srcset, data URI, alt vazio, imagem externa.

Riscos: falsos positivos em imagens decorativas.

Dependencias: fase 7.

Esforco: M.

Obrigatorio: opcional P2.

### 9. Open Graph/Twitter Card audit

Objetivo: auditar metadados sociais e previews.

Por que vem nesta ordem: util para produto e conteudo, mas nao bloqueia technical core.

Entregaveis: checks OG title/description/image/url/type e Twitter card.

Arquivos provaveis: `src/geo_seo_engine/analyzers/social.py`.

Comandos CLI novos: incluido em `audit-content` ou `geo audit-social`.

Criterios de aceite: distingue SEO core de social metadata; severidade baixa/media.

Testes necessarios: OG completo, incompleto, conflito com canonical.

Riscos: inflar prioridade de metadados sociais.

Dependencias: fase 7.

Esforco: S.

Obrigatorio: opcional.

### 10. Hreflang/i18n audit

Objetivo: auditar alternates internacionais.

Por que vem nesta ordem: relevante apenas para sites multi-idioma.

Entregaveis: hreflang syntax, return tags, x-default, canonical same language.

Arquivos provaveis: `src/geo_seo_engine/analyzers/hreflang.py`.

Comandos CLI novos: `geo audit-hreflang <url>` ou flag em site audit.

Criterios de aceite: ativado por config; nao gera ruido em site monolingue.

Testes necessarios: pares reciprocos, erro de idioma, x-default, canonical conflito.

Riscos: complexidade alta para pouco valor em sites monolingues.

Dependencias: inventario e canonical.

Esforco: M.

Obrigatorio: opcional.

### 11. JavaScript/rendering audit com Playwright

Objetivo: comparar HTML inicial e renderizado para conteudo, links, canonical, robots e JSON-LD.

Por que vem nesta ordem: Playwright e pesado e deve vir depois de pipeline estavel.

Entregaveis: integracao opcional, screenshots/snapshots controlados, diff de sinais.

Arquivos provaveis: `src/geo_seo_engine/integrations/playwright.py`, `src/geo_seo_engine/analyzers/rendering.py`.

Comandos CLI novos: `geo audit-rendering <url> --wait 3`.

Criterios de aceite: roda somente quando habilitado; falha graciosamente sem browser; sem snapshots privados por padrao.

Testes necessarios: mocks/fixtures, pagina com JS inserindo title/link/schema, timeout.

Riscos: custo, flakiness, dados privados em screenshots.

Dependencias: fases 1-7.

Esforco: L.

Obrigatorio: opcional P2.

### 12. Performance/PageSpeed/Lighthouse integration

Objetivo: integrar PSI e/ou Lighthouse para performance e page experience.

Por que vem nesta ordem: dados externos devem enriquecer, nao definir, o core.

Entregaveis: cliente PSI opcional, parse de CWV/Lighthouse, cache, thresholds.

Arquivos provaveis: `src/geo_seo_engine/integrations/pagespeed.py`, `src/geo_seo_engine/integrations/lighthouse.py`.

Comandos CLI novos: `geo audit-performance <url> --strategy mobile`.

Criterios de aceite: sem chave deve funcionar em modo limitado ou explicar dependencia; nao loga credenciais.

Testes necessarios: resposta PSI mockada, 429, sem dados field, categorias, thresholds.

Riscos: quota, latencia, falsa precisao de lab data.

Dependencias: config e HTTP.

Esforco: M/L.

Obrigatorio: opcional P2.

### 13. Content extraction

Objetivo: extrair conteudo principal de paginas para auditoria editorial e GEO.

Por que vem nesta ordem: conteudo precisa de HTML e inventario estaveis.

Entregaveis: `ContentSnapshot`, boilerplate removal basico, headings, texto, media refs.

Arquivos provaveis: `src/geo_seo_engine/content/extraction.py`.

Comandos CLI novos: `geo extract-content <url> --format markdown`.

Criterios de aceite: extracao e deterministica em fixtures; sinaliza baixa confianca quando heuristica falha.

Testes necessarios: artigo, landing page, docs, LMS, pagina curta, template com nav/footer.

Riscos: confundir boilerplate com conteudo.

Dependencias: crawler/page fetch.

Esforco: M.

Obrigatorio: sim para GEO.

### 14. Content quality audit

Objetivo: avaliar conteudo util, claro, completo e confiavel sem inventar fatos.

Por que vem nesta ordem: depende de content extraction.

Entregaveis: regras de titulo/H1 alinhados, cobertura de intencao, fontes, autoria, atualizacao, duplicidade interna.

Arquivos provaveis: `src/geo_seo_engine/content/quality.py`.

Comandos CLI novos: `geo audit-content <url>`.

Criterios de aceite: cada recomendacao separa fato, inferencia e hipotese; sem word-count como regra isolada.

Testes necessarios: pagina boa, pagina rasa, pagina sem autoria, pagina com claims sem fonte.

Riscos: subjetividade e overreach.

Dependencias: fase 13.

Esforco: L.

Obrigatorio: sim para engine senior.

### 15. Entity/GEO audit

Objetivo: medir readiness semantico para entidades e experiencias generativas.

Por que vem nesta ordem: precisa de conteudo, schema e links.

Entregaveis: entidade principal, secundarias, evidencias, schema alignment, gaps de contexto.

Arquivos provaveis: `src/geo_seo_engine/entities/`.

Comandos CLI novos: `geo audit-geo <url>`.

Criterios de aceite: nao promete presenca em IA; evidencia textual obrigatoria para entidade.

Testes necessarios: entidade clara, ambigua, contraditoria, sem schema, com schema incoerente.

Riscos: hype, alucinacao de entidades, falso senso de certeza.

Dependencias: fases 7, 13, 14.

Esforco: L.

Obrigatorio: sim.

### 16. Internal linking graph

Objetivo: construir grafo de links internos e diagnosticar arquitetura de informacao.

Por que vem nesta ordem: precisa de crawl multi-page e content/entity signals.

Entregaveis: grafo, orphan pages, profundidade, hubs, anchor text, links para canonical.

Arquivos provaveis: `src/geo_seo_engine/crawler/link_graph.py`, `src/geo_seo_engine/analyzers/internal_links.py`.

Comandos CLI novos: `geo link-graph <url> --format csv`.

Criterios de aceite: export de nodes/edges; anchors preservados; URLs normalizadas.

Testes necessarios: grafo pequeno, pagina orfa, anchor vazio, links para redirect/canonical.

Riscos: dependencia pesada desnecessaria; grafo grande demais para Markdown.

Dependencias: fases 5, 6, 13, 15.

Esforco: L.

Obrigatorio: sim.

### 17. Search Console integration

Objetivo: trazer dados reais de performance para priorizar oportunidades.

Por que vem nesta ordem: so faz sentido quando ha inventario e URLs normalizadas.

Entregaveis: cliente GSC, auth via ambiente, query por page/query/device/country/date, paginacao.

Arquivos provaveis: `src/geo_seo_engine/integrations/search_console.py`.

Comandos CLI novos: `geo gsc query --site-url sc-domain:example.com --days 28`.

Criterios de aceite: sem credencial falha com instrucao segura; nao grava dados brutos por padrao.

Testes necessarios: response mockada, sem rows, paginacao, filtros, 401/403.

Riscos: dados privados, top rows incompletos, dependencia de API externa.

Dependencias: config, URL identity, privacy config.

Esforco: L.

Obrigatorio: opcional P2, obrigatorio para opportunity engine data-driven.

### 18. Opportunity engine

Objetivo: priorizar backlog por impacto, esforco, confianca, risco e dependencia.

Por que vem nesta ordem: precisa de issues, inventario, conteudo, links e opcionalmente GSC.

Entregaveis: `Opportunity`, scoring de oportunidades, dedup, agrupamento.

Arquivos provaveis: `src/geo_seo_engine/opportunities/engine.py`.

Comandos CLI novos: `geo opportunities <url> --format markdown`.

Criterios de aceite: oportunidades incluem evidencia e caveats; nao inventam dados ausentes.

Testes necessarios: com e sem GSC, issues duplicadas, impacto baixo/alto, dependencia tecnica.

Riscos: transformar recomendacoes em promessas.

Dependencias: fases 1, 6, 14, 16, 17 opcional.

Esforco: L.

Obrigatorio: sim para produto senior.

### 19. Brief generator

Objetivo: gerar briefs de conteudo executaveis e seguros.

Por que vem nesta ordem: brief deve vir de oportunidade validada, nao de keyword solta.

Entregaveis: template de brief com persona, intencao, entidade, outline, fontes necessarias, links internos e criterios de qualidade.

Arquivos provaveis: `src/geo_seo_engine/opportunities/briefs.py`, `templates/brief.md.j2`.

Comandos CLI novos: `geo brief create --opportunity-id ...`.

Criterios de aceite: brief separa fatos conhecidos, hipoteses e pesquisa pendente.

Testes necessarios: brief completo, ausencia de dados, links internos sugeridos.

Riscos: gerar conteudo generico ou inventar fontes.

Dependencias: fase 18.

Esforco: M.

Obrigatorio: opcional P3.

### 20. Cluster generator

Objetivo: planejar clusters de conteudo sem criar doorway pages.

Por que vem nesta ordem: depende de entidades, links e oportunidades.

Entregaveis: pillar/supporting pages, intents, entidades, linking plan, criterios anti-doorway.

Arquivos provaveis: `src/geo_seo_engine/opportunities/clusters.py`.

Comandos CLI novos: `geo cluster plan <url>`.

Criterios de aceite: rejeita clusters duplicados/fracos; cada pagina proposta tem valor proprio.

Testes necessarios: cluster valido, duplicado, doorway-like, falta de entidade.

Riscos: criar massa de paginas sem valor.

Dependencias: fases 15, 16, 18.

Esforco: M/L.

Obrigatorio: opcional.

### 21. AI visibility readiness simulation

Objetivo: simular readiness para experiencias generativas com caveats fortes.

Por que vem nesta ordem: so e responsavel apos entidades, conteudo e dados.

Entregaveis: checklist de readiness, perguntas provaveis, evidencias, lacunas e riscos.

Arquivos provaveis: `src/geo_seo_engine/entities/ai_readiness.py`.

Comandos CLI novos: `geo ai-readiness <url>`.

Criterios de aceite: sem promessa de ranking/citacao; output diz que e heuristica interna.

Testes necessarios: output contem caveats, evidencia obrigatoria, falha sem conteudo suficiente.

Riscos: hype e expectativas erradas.

Dependencias: fases 14, 15, 18.

Esforco: M.

Obrigatorio: opcional P3.

### 22. Senior report

Objetivo: gerar relatorio executivo e operacional completo.

Por que vem nesta ordem: precisa consolidar diagnostico, oportunidades e scorecards.

Entregaveis: Markdown senior, JSON senior, CSV de backlog, sumario executivo, apendice tecnico.

Arquivos provaveis: `src/geo_seo_engine/reporting/senior.py`, `templates/senior-report.md.j2`.

Comandos CLI novos: `geo report senior <url> --output report.md`.

Criterios de aceite: inclui diagnostico, evidencia, risco, prioridade, proxima acao e dependencias.

Testes necessarios: golden report, escaping, report grande, sem oportunidades.

Riscos: relatorio longo demais e pouco acionavel.

Dependencias: fases 1, 6, 18.

Esforco: L.

Obrigatorio: sim.

### 23. CI/quality gates

Objetivo: permitir uso em pipeline com thresholds e exit codes.

Por que vem nesta ordem: gates precisam de scores e reports estaveis.

Entregaveis: `geo check`, `--fail-on critical`, `--min-score`, JSON de resultado.

Arquivos provaveis: `src/geo_seo_engine/scoring/gates.py`, `tests/test_quality_gates.py`.

Comandos CLI novos: `geo check <url> --config geo-seo.yml`.

Criterios de aceite: exit code previsivel; docs de CI; nao falha por warnings opcionais se config nao exigir.

Testes necessarios: pass/fail, thresholds, critical issue, sem rede com fixtures.

Riscos: bloquear deploy por falso positivo.

Dependencias: scoring e senior report.

Esforco: M.

Obrigatorio: sim para automacao.

### 24. Release process

Objetivo: formalizar versao, changelog, checks e artefatos.

Por que vem nesta ordem: apos contratos e CLI senior.

Entregaveis: versioning, changelog, release checklist, package build test.

Arquivos provaveis: `CHANGELOG.md`, `.github/workflows/`, docs release.

Comandos CLI novos: nenhum.

Criterios de aceite: checklist roda testes, diff check, secrets scan e build local.

Testes necessarios: `python -m pytest`, build se configurado.

Riscos: publicar pacote com docs prometendo features futuras.

Dependencias: estabilidade do core.

Esforco: S/M.

Obrigatorio: sim antes de distribuicao.

### 25. Senior documentation

Objetivo: documentar uso, arquitetura, config, analyzers, seguranca, exemplos e contribuicao.

Por que vem nesta ordem: docs devem refletir comportamento implementado, nao roadmap.

Entregaveis: guia de usuario, dev guide, analyzer guide, config reference, security runbook, exemplos.

Arquivos provaveis: `docs/user-guide.md`, `docs/developer-guide.md`, `docs/config-reference.md`.

Comandos CLI novos: nenhum.

Criterios de aceite: cada comando documentado tem teste ou exemplo valido; avisos de nao promessa presentes.

Testes necessarios: comandos de exemplo, varredura de segredos, links manuais.

Riscos: docs desatualizadas ou gigantes.

Dependencias: fases implementadas.

Esforco: M.

Obrigatorio: sim.

## Marcos Sugeridos

| Milestone | Fases | Resultado |
|---|---|---|
| v0.2 Core Contracts | 1-4 | Schemas, config, URL normalization e HTTP seguro. |
| v0.3 Crawl Inventory | 5-7 | Crawler, inventario e technical SEO multi-page. |
| v0.4 Content And GEO | 8-16 | Conteudo, entidades, GEO readiness, links internos e checks opcionais. |
| v0.5 Data And Opportunities | 17-22 | GSC/PSI opcionais, oportunidades, briefs, clusters, report senior. |
| v1.0 Automation And Docs | 23-25 | CI gates, release process e documentacao senior. |

## Regras De Priorizacao

- Bloqueadores de arquitetura e seguranca vencem features visiveis.
- Integracoes externas devem ser opcionais e testadas com mocks.
- Features GEO so entram depois de conteudo, entidades e evidencias.
- Qualquer geracao de brief/cluster deve conter criterios anti-spam e anti-doorway.
- Reports devem mostrar dependencias externas e limites de confianca.
