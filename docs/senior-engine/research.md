# Senior Engine Research

Data da pesquisa: 2026-06-11.

Objetivo: fundamentar a evolucao do `geo-seo-engine` de MVP de auditoria SEO/GEO para uma engine operacional senior, sem prometer trafego, ranking, indexacao ou presenca em respostas de IA.

## Fontes Pesquisadas

### Fontes oficiais obrigatorias

| Fonte | URL | Uso para o projeto |
|---|---|---|
| Google Search Central SEO Starter Guide | https://developers.google.com/search/docs/fundamentals/seo-starter-guide | Base para priorizar conteudo util, descoberta por links, sitemaps, URLs descritivas, renderizacao e ausencia de promessas de ranking. |
| Google Search Essentials | https://developers.google.com/search/docs/essentials | Base para separar requisitos tecnicos, politicas de spam e boas praticas principais. |
| Google AI features and your website | https://developers.google.com/search/docs/appearance/ai-features | Base para tratar AI Overviews e AI Mode como extensao dos fundamentos de Search, sem requisitos tecnicos adicionais ou promessa de inclusao. |
| Google structured data intro | https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data | Base para JSON-LD, validacao, coerencia com conteudo visivel e prioridade em propriedades completas e corretas. |
| Google JavaScript SEO basics | https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics | Base para diferenciar HTML inicial, HTML renderizado, soft 404, canonicals em JS e links extraidos apos renderizacao. |
| Google canonicalization | https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls | Base para sinais canonicos, conflitos entre sitemap/canonical/redirect e riscos de usar robots.txt ou noindex para canonicalizacao. |
| Google redirects | https://developers.google.com/search/docs/crawling-indexing/301-redirects | Base para classificar redirects permanentes e temporarios e avaliar cadeias/loops. |
| Google robots.txt | https://developers.google.com/search/docs/crawling-indexing/robots/intro | Base para distinguir controle de crawl de controle de indexacao e seguranca. |
| Google sitemaps | https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview | Base para inventario de URLs, descoberta, sites grandes, midia, news e relacionamento com links internos. |
| Google image SEO | https://developers.google.com/search/docs/appearance/google-images | Base para auditoria de `<img>`, `alt`, `src`, `srcset`, fallback de `<picture>`, formatos e performance. |
| Search Console API Search Analytics | https://developers.google.com/webmaster-tools/v1/searchanalytics/query | Base para integracao de dados com autorizacao, dimensoes, filtros, paginacao e limitacoes de amostragem/top rows. |
| PageSpeed Insights API | https://developers.google.com/speed/docs/insights/v5/get-started | Base para integracao externa opcional com PSI, CrUX e Lighthouse, com chave recomendada para uso frequente. |
| Lighthouse docs | https://developer.chrome.com/docs/lighthouse/overview | Base para auditoria programatica e CI de performance, acessibilidade, SEO e boas praticas. |
| schema.org schemas | https://schema.org/docs/schemas.html | Base de vocabulario semantico amplo, com cautela para termos pending/meta/attic. |
| RFC 9309 Robots Exclusion Protocol | https://www.rfc-editor.org/rfc/rfc9309 | Base normativa para parsing de robots.txt, grupos, user-agents, allow/disallow e tratamento de erros/cache. |
| Core Web Vitals | https://web.dev/articles/vitals | Base para LCP, INP, CLS, thresholds e percentil 75 segmentado por mobile/desktop. |
| Page Experience | https://developers.google.com/search/docs/appearance/page-experience | Base para tratar CWV como parte de experiencia geral, sem transformar score perfeito em fim por si so. |
| Crawlable links | https://developers.google.com/search/docs/crawling-indexing/links-crawlable | Base para grafo interno, links `<a href>`, anchor text e links inseridos por JavaScript. |
| Helpful content | https://developers.google.com/search/docs/fundamentals/creating-helpful-content | Base para auditoria de qualidade, originalidade, experiencia, confiabilidade e conteudo people-first. |
| Spam policies | https://developers.google.com/search/docs/essentials/spam-policies | Base para rejeitar doorway pages, cloaking, automacao massiva, keyword stuffing e manipulacao de respostas generativas. |

### Validacao com Playwright

Foi aberta a pagina `https://developers.google.com/search/docs/appearance/ai-features` com Playwright. A pagina redirecionou para `?hl=pt-br` e apresentou o titulo `Recursos de IA e seu site | Central da Pesquisa Google | Documentation | Google for Developers`. Isso confirma que a fonte e publica, atual e localizada, mas o conteudo operacional usado neste documento foi extraido por `fetch` para manter as citacoes textuais rastreaveis.

### Padroes observados em repositorios publicos

Pesquisa feita com `gh_grep`, apenas para inspiracao arquitetural. Nenhum codigo externo foi copiado.

| Padrao pesquisado | Exemplos encontrados | Extracao util |
|---|---|---|
| URL normalization | `searxng/searxng`, `home-assistant/core`, `onyx-dot-app/onyx` | Normalizacao deve ser modulo isolado, testado por casos de URL relativa, protocolo ausente, query params, barras finais e canonical identity. |
| Sitemap parsing | `apify/crawlee-python`, `GateNLP/ultimate-sitemap-parser` | Sitemaps grandes devem ser parseados por streaming/SAX quando possivel; index recursivo precisa de limite de profundidade e deduplicacao. |
| Crawler/frontier | `spacetime-crawler4py`, `CyberYozh-data/yozh-scraper`, `crawl4ai-mcp-server` | Crawler senior precisa separar frontier, dedup, scope, rate limit, fetcher e parser. |
| CLI Typer modular | `HKUDS/DeepTutor`, `oumi-ai/oumi`, `flower` | Para crescer, a CLI deve migrar para subapps por dominio (`audit`, `crawl`, `report`, `config`, `integrations`). |
| Plugin registry | `spyder-ide/spyder`, `saleor/saleor`, `django-cms/django-cms`, `OCRmyPDF` | Plugins devem ser registrados explicitamente, filtrados por config e com contratos estaveis, evitando import dinamico inseguro por caminho arbitrario no MVP. |
| PageSpeed integration | `GoogleChromeLabs/psi`, `GoogleChrome/lighthouse`, `GoogleChromeLabs/bubblewrap` | Integracoes PSI usam endpoint `runPagespeed`, categorias, strategy, tratamento de quota e output JSON versionado. |
| Search Console integration | `googleapis/google-api-python-client`, `getredash/redash`, `dagster-open-platform` | Integracao GSC deve aceitar `siteUrl`, dimensoes, filtros, rowLimit/startRow, OAuth/service account via ambiente e mensagens claras para ausencia de dados. |
| Content extraction | Usos de `readability.Document` em projetos de extracao | Extracao de conteudo principal e util, mas deve ser tratada como heuristica falivel e validada com fixtures. |
| Config settings | Usos de `pydantic_settings.BaseSettings` | Config senior pode combinar arquivo de projeto, variaveis de ambiente e defaults tipados, sem carregar `.env` real do repo. |

## Resumo Critico Das Fontes

### O que e confiavel

- Fundamentos do Google Search Central sao a referencia primaria para rastreamento, indexacao, links, sitemaps, robots, canonicals, redirects, JavaScript SEO, structured data e politicas de spam.
- A documentacao de AI features do Google afirma que AI Overviews e AI Mode usam os mesmos fundamentos de Search e que nao ha requisitos tecnicos adicionais para aparecer como link de suporte alem de estar indexado e elegivel com snippet.
- Search Console e a fonte operacional mais confiavel para performance agregada em Search, mas seus dados sao limitados, agregados e podem nao retornar todas as linhas.
- PageSpeed Insights e Lighthouse sao fontes operacionais uteis para laboratorio, CrUX e regressao tecnica, mas nao substituem analise de conteudo, intencao, indexabilidade e negocio.
- RFC 9309 e referencia normativa para robots.txt; a documentacao do Google e referencia especifica para comportamento do Googlebot.
- schema.org e vocabulario amplo; a documentacao do Google deve prevalecer quando a pergunta for elegibilidade de rich results no Google.

### O que exige cautela

- Structured data pode ajudar entendimento e elegibilidade a recursos enriquecidos, mas markup incorreto, invisivel ao usuario ou incompleto deve ser penalizado. Mais schema nao significa melhor SEO.
- Core Web Vitals sao importantes para experiencia e podem contribuir para Search, mas score perfeito nao garante ranking.
- Sitemaps ajudam descoberta, especialmente em sites grandes, novos, com midia ou news, mas links internos continuam essenciais.
- Robots.txt nao e mecanismo de seguranca nem metodo confiavel para remover URLs do indice.
- Conteudo extraido por heuristicas como readability deve ser revisado por regras de qualidade e evidencia do DOM, nao tratado como verdade absoluta.

### O que e hype ou deve ser rejeitado

- Prometer presenca em AI Overviews, AI Mode, ChatGPT, Perplexity ou qualquer mecanismo generativo.
- Criar conteudo em massa para manipular ranking ou respostas de IA.
- Tratar GEO como checklist separado de SEO tecnico, conteudo util, entidades verificaveis e dados estruturados coerentes.
- Usar doorway pages, dominios expirados, PBN, backlinks artificiais, cloaking, keyword stuffing ou paginas geradas por variacao geografica sem valor proprio.
- Adicionar schema que contradiz o conteudo visivel ou inventa reviews, estatisticas, autores, cases, precos, disponibilidade ou credenciais.
- Priorizar `llms.txt`, prompts publicos ou arquivos especulativos como fase core sem validacao de impacto e sem suporte claro das fontes oficiais pesquisadas.

## Implicacoes Para O Projeto

- A engine v2 deve continuar separando fato, inferencia, hipotese e recomendacao em todos os reports.
- GEO deve ser implementado como readiness: entidade principal, entidades secundarias, evidencia textual, links internos, dados estruturados, autoria, fontes, experiencia e cobertura de intencao. Nao deve ser vendido como tecnica de inclusao em IA.
- A arquitetura deve sair de analisadores que fazem fetch proprio e ir para um pipeline com modelos estaveis, HTTP centralizado, URL normalization, crawler, inventario, analisadores plugaveis, scoring e report.
- A primeira prioridade nao e adicionar dezenas de checks; e estabilizar schemas, config, URL identity, fetch policy, fixtures e contratos de issue.
- Integracoes externas como Search Console, PageSpeed e Lighthouse devem ser opcionais, config-driven, com tratamento de ausencia de credenciais e sem logs de credenciais.
- Relatorios senior devem mostrar evidencia, risco, prioridade e proxima acao, alem de separar diagnostico tecnico de oportunidade editorial.
- Automacao futura deve ser incremental e auditavel, com quality gates para impedir regressao de contrato, Markdown invalido, JSON invalido e vazamento de dados sensiveis.
