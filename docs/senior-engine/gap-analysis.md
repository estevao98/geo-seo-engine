# Senior Engine Gap Analysis

Data da analise: 2026-06-11.

Escopo: analise do estado atual do repositorio local `geo-seo-engine` e comparacao com o objetivo de uma engine senior de SEO tecnico, GEO, conteudo, dados, relatorios e automacao.

## Estado Atual Do Repositorio

### O que o repo ja faz

- Expoe CLI instalavel `geo` via `pyproject.toml`.
- Comandos existentes: `version`, `audit-page`, `audit-sitemap`, `audit-robots`, `audit-site`.
- `audit-page` busca uma pagina publica com `httpx.get`, segue redirects e extrai status, final URL, title, meta description, H1, canonical, meta robots, noindex, links internos e externos.
- `audit-robots` normaliza URL para `/robots.txt`, busca o arquivo, interpreta diretivas basicas, identifica user-agents, allow, disallow, sitemap, crawl-delay, diretivas desconhecidas e `Disallow: /`.
- `audit-sitemap` busca XML, parseia `urlset` e `sitemapindex`, extrai `loc` e `lastmod`, identifica duplicatas, URLs invalidas, URLs com query, URLs fora do dominio e ausencia de `lastmod`.
- `audit-site` agrega page, robots, sitemap e structured data em um resultado unico.
- `structured_data_audit` extrai blocos JSON-LD, valida JSON, conta blocos, extrai `@type` recursivamente e reporta `missing`, `invalid_json_ld`, `missing_type`.
- `reporting/severity.py` classifica issues em `critical`, `high`, `medium`, `low` e calcula score geral com penalidades.
- `reporting/recommendations.py` gera recomendacoes ordenadas por severidade.
- `reporting/markdown.py` renderiza relatorio Markdown de site audit.
- README, SECURITY e exemplo Markdown documentam o MVP e limites de promessa.
- Testes cobrem CLI basica, page audit, robots audit, sitemap audit, structured data, severidade, recomendacoes, site audit e Markdown.

### Pontos fortes

- Escopo do MVP e claro e honesto.
- Separacao minima entre analisadores e reporting ja existe.
- Testes usam monkeypatch e fixtures inline, reduzindo dependencia de rede.
- As issues sao strings simples e faceis de serializar.
- O score tem regra explicita e testada.
- O report Markdown ja inclui summary, issues classificadas e recomendacoes.
- SECURITY.md e `.gitignore` tratam riscos reais de segredos, exports privados, scanner outputs e dados de clientes.
- README evita prometer ranking, indexacao ou presenca em IA.

## Limitacoes Tecnicas

- Cada analisador faz seu proprio `httpx.get`, duplicando user-agent, timeout, follow redirects, tratamento de erro e politica de rede.
- `audit_site` busca a mesma pagina duas vezes: uma em `audit_page` e outra em `audit_structured_data`.
- Nao ha cliente HTTP centralizado com retries, backoff, limite de tamanho, robots awareness, rate limit, cache, headers configuraveis ou observabilidade.
- URL normalization e parcial: robots tem normalizacao propria, sitemap e page usam URL como recebida.
- Nao ha modelo estavel de issue com `id`, `category`, `severity`, `evidence`, `risk`, `recommendation`, `location`, `source_url` e `next_action`.
- Issues como strings com prefixos dificultam evolucao, i18n, filtros, deduplicacao e integracao com CI.
- Dataclasses sao simples, mas nao validam contratos de entrada/saida como Pydantic poderia fazer.
- Sitemap parsing usa `xml.etree.ElementTree.fromstring`, carregando todo o documento em memoria.
- Nao ha suporte a sitemap gzip, sitemap txt, sitemap index recursivo com limite, video/image/news sitemaps ou `lastmod` invalido.
- Robots parser e basico e nao implementa completamente RFC 9309: grupos por user-agent, merge de grupos, matching por caminho, precedencia allow/disallow, wildcards, `$`, cache e erro conforme especificacao.
- Link counting nao resolve URLs relativas com `urljoin`, nao normaliza host, nao diferencia scheme, porta, trailing slash, fragment, query tracking, canonical identity ou hreflang.
- Structured data valida sintaxe JSON-LD, mas nao valida propriedades exigidas por tipo, coerencia com conteudo visivel ou guidelines de rich results.
- Markdown renderer interpola valores diretamente; para dados externos maiores, precisa escaping e controle de tamanho.
- Nao ha persistencia, cache de crawl, inventario de URLs ou grafo de links.
- Nao ha configuracao por projeto, dominio, include/exclude, limites, user-agent, politicas de output ou pesos de score.

## Riscos Arquiteturais

- Crescer adicionando checks dentro dos mesmos arquivos vai aumentar acoplamento entre fetch, parsing, regras, scoring e rendering.
- Manter issues como strings vai gerar regras duplicadas em severidade, recomendacoes, report e testes.
- Sem URL identity estavel, o crawler futuro pode produzir duplicatas, loops, relatarios inconsistentes e comparacoes historicas erradas.
- Sem HTTP centralizado, integracoes futuras terao comportamento inconsistente e dificil de debugar.
- Sem fixtures compartilhadas, testes vao crescer com HTML/XML inline repetido e baixa cobertura de casos reais.
- Sem separacao entre coleta e analise, nao sera facil comparar HTML inicial vs renderizado, PSI vs crawl local ou Search Console vs inventario.
- Sem politica de privacidade no modelo de dados, dados de clientes podem vazar para reports versionados.

## Acoplamentos Identificados

- `cli.py` conhece detalhes de renderizacao table/json/markdown e chama diretamente analisadores.
- `site_audit.py` orquestra fetches, structured data, sitemap selection, prefixo de issues, scoring e next action indiretamente via `SiteAuditResult.__post_init__`.
- `recommendations.py` depende de convencao textual de issue e de `classify_issue`.
- `severity.py` depende de prefixos textuais e regex de status code.
- `markdown.py` depende diretamente dos dataclasses dos analisadores, dificultando criar report a partir de um modelo v2 generico.
- `structured_data_audit.py` busca pagina propria em vez de receber HTML ja coletado por page audit.

## Lacunas De Testes

- Falta teste para erro de rede em cada analisador.
- Falta teste para timeout, redirects, final URL e content-type variado.
- Falta teste para URL relativa, protocolo relativo, host com `www`, porta, query, fragment e trailing slash.
- Falta teste para HTML sem `content-type` ou com charset.
- Falta teste para multiplas canonicals, canonical relativa, canonical fora do dominio e canonical conflitante com final URL.
- Falta teste para meta robots com `noindex,nofollow`, `x-robots-tag` header e conflitos entre header e HTML.
- Falta teste para robots com multiplos grupos, user-agent especifico, wildcard, `$`, comentarios inline e regras vazias.
- Falta teste para sitemap gzip, sitemap txt, sitemap index recursivo, namespace alternativo, XML grande, `lastmod` invalido e URLs com espacos.
- Falta teste para JSON-LD com `@graph`, array raiz, tipos aninhados, blocos vazios e conteudo dinamico.
- Falta teste snapshot/golden para Markdown senior e JSON output versionado.
- Falta teste CLI para `--output` em `audit-site`, `audit-robots`, `audit-sitemap` e validacao de URL invalida.

## Lacunas De Produto

- Nao ha conceito de projeto/site configurado.
- Nao ha auditoria multi-page real nem inventario de URLs.
- Nao ha crawl budget, profundidade, include/exclude, limite de paginas, politeness ou rate limit.
- Nao ha historico, comparacao entre execucoes ou baseline.
- Nao ha relatorio executivo separado de backlog operacional.
- Nao ha export CSV para inventario, issues e oportunidades.
- Nao ha priorizacao por impacto potencial, esforco, confianca, evidencias e dependencias.
- Nao ha modo CI com thresholds e exit code controlado.
- Nao ha integracao com Search Console para dados de query/page/device/country.
- Nao ha integracao com PSI/Lighthouse para performance e page experience.
- Nao ha geracao de briefs, clusters ou oportunidades baseada em entidades e intencao.

## Lacunas De CLI

- `geo --version` ainda nao existe; apenas `geo version`.
- Os comandos usam `--format`, mas o help de `audit-site` diz `table or json` mesmo aceitando `markdown`.
- Nao ha `--config`.
- Nao ha `--max-pages`, `--depth`, `--include`, `--exclude`, `--concurrency`, `--delay`, `--user-agent`.
- Nao ha `--fail-on`, `--min-score`, `--quiet`, `--verbose`, `--no-color` ou `--debug`.
- Nao ha comandos para `init`, `config validate`, `crawl`, `inventory`, `report`, `opportunities`, `brief`, `cluster`.
- Nao ha padronizacao de exit codes por falha tecnica vs issues SEO.
- Nao ha validacao forte de URL de entrada antes do fetch.

## Lacunas De Seguranca E Privacidade

- User-agent atual usa `(+https://example.com)`, que e neutro, mas nao identifica documentacao real do crawler.
- Nao ha allowlist/denylist de hosts, bloqueio de IP privado/local ou protecao contra SSRF se a CLI for usada em automacao com input externo.
- Nao ha limite de bytes de resposta, podendo consumir memoria em respostas grandes.
- Nao ha controle de redirects para hosts inesperados.
- Nao ha politica de sanitizacao para reports com URLs, queries e conteudo possivelmente privado.
- Nao ha segredo no repo atual, mas integracoes GSC/PSI futuras precisam usar variaveis de ambiente e nunca persistir credenciais.
- Nao ha log redaction porque ainda nao ha logging estruturado.

## Lacunas De Documentacao

- README documenta MVP, mas nao contratos de dados ou schema de issue.
- Nao ha docs de arquitetura interna.
- Nao ha guia de contribuicao especifico para novos analyzers.
- Nao ha fixtures documentadas.
- Nao ha matriz de severidade documentada alem do texto no README.
- Nao ha docs de seguranca operacional para crawling em escala.
- Nao ha exemplos de config por projeto.

## Lacunas Para Escala

- Crawler multi-page exige frontier, dedup, scope e persistencia leve antes de aumentar checks.
- Sitemaps grandes precisam streaming e limites.
- Page fetching precisa cache e rate limit por host.
- Reports grandes precisam sumarizacao, filtros e arquivos separados.
- Grafo de links precisa estrutura propria e export para analise.
- Performance externa precisa filas, quota, retry e cache por URL/strategy.
- Search Console precisa paginacao, janelas de data, limites e tratamento de top rows.

## Lacunas Especificas Para GEO

- Nao ha modelo de entidade principal e entidades secundarias por pagina.
- Nao ha extracao de conteudo principal.
- Nao ha avaliacao de evidencia factual, autoria, fonte, atualizacao, escopo ou incerteza.
- Nao ha avaliacao de cobertura por intencao de busca.
- Nao ha ligacao entre structured data e conteudo visivel.
- Nao ha auditoria de perguntas/respostas, definicoes, comparacoes, glossario ou conteudo de suporte.
- Nao ha analise de anchor text e contexto de links internos para reforco semantico.
- Nao ha simulacao cautelosa de readiness para respostas generativas. Quando existir, deve ser apresentada como heuristica interna, nao como previsao de presenca em IA.

## Prioridades Recomendadas

| Prioridade | Gap | Motivo |
|---|---|---|
| P0 | Schemas v2 de issue/result/config | Evita crescimento baseado em strings e reports acoplados. |
| P0 | URL normalization | Base para crawler, sitemap, canonical, links e dedup. |
| P0 | HTTP client centralizado | Reduz duplicacao, risco de SSRF, memoria e comportamento inconsistente. |
| P1 | Config por projeto | Necessaria para SaaS, LMS, Melura e sites com escopo diferente. |
| P1 | Crawler multi-page com limites | Base para inventario, link graph e auditoria senior. |
| P1 | Inventario de URLs | Transforma auditoria pontual em sistema operacional. |
| P1 | Structured data v2 | Checar coerencia, tipos e evidencias sem prometer rich results. |
| P2 | Content extraction e content quality | Base para GEO e oportunidades. |
| P2 | Internal linking graph | Base para crawlability, clusters e entidades. |
| P2 | Search Console integration | Dados reais para priorizar oportunidades. |
| P2 | PSI/Lighthouse integration | Performance operacional e CI. |
| P3 | Briefs, clusters e AI readiness | So depois de inventario, conteudo, entidades e dados. |

## Hipoteses A Validar

- Pydantic v2 sera suficiente para schemas estaveis sem adicionar complexidade excessiva.
- SQLite local pode ser util depois do crawler, mas nao deve ser introduzido antes de estabilizar contratos.
- NetworkX pode ajudar no grafo de links, mas talvez uma estrutura propria simples seja melhor no inicio.
- Playwright deve ser opcional por custo e dependencia, usado apenas em rendering audit e snapshots controlados.
- PSI via API deve vir antes de Lighthouse local se o objetivo for simplicidade operacional, mas Lighthouse CI pode ser melhor para quality gates.
- Um plugin registry simples e explicito e preferivel a entrypoints dinamicos ate haver demanda real de extensao externa.
