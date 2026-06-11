# Senior Engine Prompt Pack

Uso: execute um chunk por vez no OpenCode/Codex, na ordem abaixo. Cada prompt assume que o reposititorio esta limpo ou que o operador revisou mudancas pendentes. Nenhum prompt autoriza push.

## Chunk 1. Architecture v2 e schemas estaveis

Objetivo: criar contratos centrais para a engine v2 sem remover a CLI MVP.

Contexto: o repo usa dataclasses e issues como strings em `analyzers/` e `reporting/`. A primeira evolucao deve adicionar modelos v2 tipados e adaptador para issues legadas.

Tarefa: implemente `src/geo_seo_engine/core/` com modelos para severity, issue category, evidence, issue, recommendation, URL identity, audit summary e audit run. Adicione testes de serializacao e validacao. Nao migre todos os analyzers ainda.

Arquivos provaveis: `src/geo_seo_engine/core/__init__.py`, `src/geo_seo_engine/core/models.py`, `src/geo_seo_engine/core/legacy.py`, `tests/test_core_models.py`.

Implementacao esperada: Pydantic v2; enums com strings estaveis; `Issue` com `id`, `title`, `category`, `severity`, `url`, `evidence`, `risk`, `recommendation`, `next_action`, `confidence`; adaptador `legacy_issue_to_issue(source, issue)` minimalista.

Regras obrigatorias: nao quebrar comandos atuais; nao mudar scoring antigo exceto se testes exigirem; nao adicionar dependencias novas sem necessidade; manter JSON serializavel.

Criterios de aceite: testes novos passam; modelos exportam JSON; issue legada vira issue v2 com categoria e severidade default seguras; README nao precisa mudar.

Validacao: `python -m pytest tests/test_core_models.py python -m pytest`.

Mensagem de commit: `feat: add core audit schemas`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: nao registrar URLs privadas em fixtures; use `https://example.com`.

Proibicoes: nao remover dataclasses atuais; nao fazer push; nao criar banco de dados.

## Chunk 2. Config por projeto

Objetivo: adicionar configuracao por projeto com YAML seguro.

Contexto: hoje a CLI recebe apenas URL e algumas flags. A engine senior precisa de escopo, limites e privacidade antes de crawler multi-page.

Tarefa: crie modelos de config, loader YAML e comandos `geo init` e `geo config validate`. Gere um exemplo versionavel sem segredos.

Arquivos provaveis: `src/geo_seo_engine/config/__init__.py`, `src/geo_seo_engine/config/models.py`, `src/geo_seo_engine/config/loader.py`, `src/geo_seo_engine/cli.py`, `examples/geo-seo.example.yml`, `tests/test_config.py`, `tests/test_cli_config.py`.

Implementacao esperada: `ProjectConfig` com `project_name`, `base_url`, `allowed_hosts`, `start_urls`, `sitemap_urls`, `include_patterns`, `exclude_patterns`, `limits`, `http`, `crawler`, `privacy`, `integrations`; defaults conservadores; erro legivel de validacao.

Regras obrigatorias: nao ler `.env`; nao persistir credenciais; `geo init` deve criar arquivo somente se nao existir ou exigir `--force`.

Criterios de aceite: config minima valida; config invalida falha; exemplo YAML nao contem token/chave; CLI atual continua funcionando.

Validacao: `python -m pytest tests/test_config.py tests/test_cli_config.py python -m pytest`.

Mensagem de commit: `feat: add project configuration`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: nomes de variaveis de ambiente podem aparecer em docs, valores reais nao.

Proibicoes: nao commitar `.env`; nao chamar APIs externas.

## Chunk 3. URL normalization

Objetivo: centralizar identidade de URL.

Contexto: robots normaliza sozinho; page/sitemap nao normalizam. Crawler e link graph dependem de regra unica.

Tarefa: implemente utilitario de normalizacao com suporte a base URL, fragment removal, host lower-case, default ports, trailing slash configuravel e remocao opcional de tracking params.

Arquivos provaveis: `src/geo_seo_engine/core/url.py`, `tests/test_url_normalization.py`, possivelmente `src/geo_seo_engine/config/models.py`.

Implementacao esperada: funcoes puras `normalize_url(raw, base_url=None, options=None)` e `is_same_site(url, allowed_hosts)`; retornar objeto/resultado com raw e normalized.

Regras obrigatorias: preservar query por padrao; remover fragment por padrao; nao fazer rede; documentar qualquer regra destrutiva.

Criterios de aceite: testes cobrem relativo, protocolo relativo, query, fragment, porta default, host case, trailing slash e URL invalida.

Validacao: `python -m pytest tests/test_url_normalization.py python -m pytest`.

Mensagem de commit: `feat: add URL normalization utilities`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: normalizacao nao deve permitir bypass de host allowlist.

Proibicoes: nao modificar crawler inexistente; nao remover comportamento atual da CLI.

## Chunk 4. HTTP client centralizado

Objetivo: substituir fetch disperso por cliente seguro e testavel.

Contexto: `page_audit`, `robots_audit`, `sitemap_audit` e `structured_data_audit` chamam `httpx.get` diretamente.

Tarefa: crie `http/client.py` com `FetchRequest`, `FetchResult` e cliente com timeout, follow redirects, user-agent, max bytes e protecoes basicas. Migre um analyzer por vez, preferencialmente page e structured data primeiro para evitar fetch duplicado.

Arquivos provaveis: `src/geo_seo_engine/http/`, `src/geo_seo_engine/analyzers/page_audit.py`, `src/geo_seo_engine/analyzers/structured_data_audit.py`, `tests/test_http_client.py`, testes existentes.

Implementacao esperada: cliente injetavel; analyzers aceitam HTML/FetchResult quando possivel; erros viram issues padronizadas sem stack trace cru.

Regras obrigatorias: manter comandos atuais; evitar download ilimitado; bloquear host privado somente quando policy estiver ativa para nao quebrar testes locais.

Criterios de aceite: testes antigos e novos passam; fetch duplicado em `audit_site` e reduzido ou preparado por API clara.

Validacao: `python -m pytest tests/test_http_client.py python -m pytest`.

Mensagem de commit: `feat: add centralized HTTP client`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: nao logar headers sensiveis; nao salvar response body em arquivo.

Proibicoes: nao adicionar requests; nao chamar sites reais nos testes.

## Chunk 5. Crawler multi-page

Objetivo: adicionar crawler de escopo limitado.

Contexto: o MVP audita uma URL por vez. O crawler deve usar config, normalizacao e HTTP centralizado.

Tarefa: implemente frontier FIFO simples, dedup por URL normalizada, max_pages, max_depth, include/exclude e extracao de links `<a href>`.

Arquivos provaveis: `src/geo_seo_engine/crawler/__init__.py`, `src/geo_seo_engine/crawler/frontier.py`, `src/geo_seo_engine/crawler/crawler.py`, `src/geo_seo_engine/crawler/extract.py`, `src/geo_seo_engine/cli.py`, `tests/test_crawler.py`, `tests/test_cli_crawl.py`.

Implementacao esperada: comando `geo crawl <url> --max-pages --depth --format json`; resultado inclui URLs visitadas, status, depth, discovered_from e links extraidos.

Regras obrigatorias: nunca crawler infinito; respeitar allowed_hosts; sem concorrencia na primeira versao se isso reduzir risco.

Criterios de aceite: crawl pequeno com fixtures mockadas; loops nao repetem URL; host externo ignorado.

Validacao: `python -m pytest tests/test_crawler.py tests/test_cli_crawl.py python -m pytest`.

Mensagem de commit: `feat: add scoped crawler`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: max_pages default conservador; user-agent configuravel.

Proibicoes: nao usar threads/processos ainda; nao persistir dados privados.

## Chunk 6. URL inventory audit

Objetivo: gerar inventario operacional de URLs.

Contexto: crawler retorna paginas, mas engine senior precisa de artefato consumivel para relatorios e backlog.

Tarefa: crie `UrlInventory` com uma linha por URL normalizada, status, final_url, source, depth, canonical, noindex, title e issues tecnicas basicas.

Arquivos provaveis: `src/geo_seo_engine/crawler/inventory.py`, `src/geo_seo_engine/reporting/csv.py`, `src/geo_seo_engine/cli.py`, `tests/test_inventory.py`, `tests/test_cli_inventory.py`.

Implementacao esperada: comando `geo audit-inventory <url> --format json|csv|markdown`; CSV com header estavel.

Regras obrigatorias: nao misturar oportunidade editorial; inventario e fato tecnico coletado.

Criterios de aceite: JSON e CSV validos; duplicatas consolidadas; `example.com` em fixtures.

Validacao: `python -m pytest tests/test_inventory.py tests/test_cli_inventory.py python -m pytest`.

Mensagem de commit: `feat: add URL inventory audit`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: paths/queries podem ser dados sensiveis; deixe redaction preparado por config se ja existir.

Proibicoes: nao gravar em `reports/` por padrao.

## Chunk 7. Technical SEO avancado

Objetivo: expandir checks tecnicos multi-page.

Contexto: inventario permite detectar duplicidade, canonical conflicts, redirects e indexability em escala.

Tarefa: implemente analyzer tecnico v2 para duplicate titles/descriptions, canonical ausente/conflitante, noindex, status classes, redirect chains e x-robots-tag quando disponivel.

Arquivos provaveis: `src/geo_seo_engine/analyzers/technical.py`, `src/geo_seo_engine/scoring/`, `tests/test_technical_audit.py`.

Implementacao esperada: issues v2 com evidencia por URL; severidade calibrada; recomendacoes especificas.

Regras obrigatorias: nao duplicar issue antiga se resultado v2 ja cobre; manter adaptador para report antigo.

Criterios de aceite: cada issue tem evidencia e next_action; testes cobrem casos positivos e negativos.

Validacao: `python -m pytest tests/test_technical_audit.py python -m pytest`.

Mensagem de commit: `feat: add advanced technical audit`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: nao inclua conteudo de pagina inteiro na evidencia.

Proibicoes: nao prometer indexacao; nao classificar todo warning como critical.

## Chunk 8. Image audit

Objetivo: auditar imagens com base nas recomendacoes oficiais.

Contexto: Google recomenda imagens via `<img src>`, alt descritivo quando aplicavel, fallback em `<picture>` e otimizacao de velocidade.

Tarefa: crie analyzer de imagens para `img src`, `alt`, `picture` fallback, `srcset`, imagens externas e possivel lazy loading. Broken image check deve ser opcional.

Arquivos provaveis: `src/geo_seo_engine/analyzers/images.py`, `tests/test_image_audit.py`, fixtures HTML.

Implementacao esperada: issues v2 com seletor/URL; severidade baixa/media; flags para checar rede de imagens.

Regras obrigatorias: alt vazio nao e sempre erro; imagens decorativas podem ser aceitaveis.

Criterios de aceite: fixtures cobrem img normal, sem src, picture sem fallback, alt vazio e srcset.

Validacao: `python -m pytest tests/test_image_audit.py python -m pytest`.

Mensagem de commit: `feat: add image SEO audit`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: nao baixar imagens por padrao.

Proibicoes: nao medir tamanho remoto sem flag explicita.

## Chunk 9. Open Graph/Twitter Card audit

Objetivo: auditar metadados sociais sem confundir com SEO core.

Contexto: OG/Twitter ajudam previews e compartilhamento, mas nao devem dominar score tecnico.

Tarefa: implemente analyzer para `og:title`, `og:description`, `og:image`, `og:url`, `og:type`, `twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`.

Arquivos provaveis: `src/geo_seo_engine/analyzers/social.py`, `tests/test_social_audit.py`.

Implementacao esperada: checks de ausencia, duplicidade e conflito obvio com canonical/title; severidade baixa/media.

Regras obrigatorias: nao tratar ausencia de Twitter Card como high; output deve dizer que e metadata social.

Criterios de aceite: fixtures com completo, ausente, conflito e duplicado.

Validacao: `python -m pytest tests/test_social_audit.py python -m pytest`.

Mensagem de commit: `feat: add social metadata audit`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: nao validar imagem remota por padrao.

Proibicoes: nao prometer CTR ou ranking.

## Chunk 10. Hreflang/i18n audit

Objetivo: adicionar auditoria internacional opcional.

Contexto: hreflang so deve gerar ruido quando site configurar multiplos idiomas ou tags forem encontradas.

Tarefa: implemente parser de `link rel="alternate" hreflang`, validacao de codigo, x-default, retorno reciproco dentro do inventario e canonical compatibilidade.

Arquivos provaveis: `src/geo_seo_engine/analyzers/hreflang.py`, `tests/test_hreflang_audit.py`.

Implementacao esperada: issues v2; analyzer pode operar em uma pagina ou inventario.

Regras obrigatorias: se nao houver hreflang e config nao exigir i18n, nao gerar issue.

Criterios de aceite: testes para reciproco, ausente, x-default, idioma invalido e canonical conflito.

Validacao: `python -m pytest tests/test_hreflang_audit.py python -m pytest`.

Mensagem de commit: `feat: add hreflang audit`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: nao seguir alternates fora do escopo sem config.

Proibicoes: nao classificar site monolingue como erro.

## Chunk 11. JavaScript/rendering audit com Playwright

Objetivo: comparar HTML inicial e renderizado.

Contexto: Google processa crawl, rendering e indexing; conteudo ou links dependentes de JS podem alterar diagnostico.

Tarefa: adicione integracao opcional com Playwright para renderizar pagina, extrair HTML renderizado e comparar title, meta description, canonical, robots, links e JSON-LD com HTML inicial.

Arquivos provaveis: `src/geo_seo_engine/integrations/playwright.py`, `src/geo_seo_engine/analyzers/rendering.py`, `tests/test_rendering_audit.py`.

Implementacao esperada: comando `geo audit-rendering`; timeout e wait configuraveis; falha graciosa se Playwright nao instalado.

Regras obrigatorias: snapshots/screenshot desativados por padrao; nao salvar HTML renderizado sem `--output` explicito.

Criterios de aceite: testes com mock; diff de sinais funciona; CLI explica dependencia opcional.

Validacao: `python -m pytest tests/test_rendering_audit.py python -m pytest`.

Mensagem de commit: `feat: add optional rendering audit`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: HTML renderizado pode conter dados privados; nao versionar outputs.

Proibicoes: nao tornar Playwright dependencia obrigatoria sem decisao explicita.

## Chunk 12. Performance/PageSpeed/Lighthouse integration

Objetivo: integrar performance opcional com PSI/Lighthouse.

Contexto: PageSpeed Insights retorna dados CrUX/Lighthouse; Lighthouse pode rodar CLI/Node. A engine deve degradar sem credencial.

Tarefa: implemente cliente PSI com endpoint `runPagespeed`, strategy mobile/desktop, categorias e parser de LCP/INP/CLS quando presentes. Lighthouse local pode ser interface stub se ficar grande.

Arquivos provaveis: `src/geo_seo_engine/integrations/pagespeed.py`, `src/geo_seo_engine/analyzers/performance.py`, `tests/test_pagespeed_integration.py`.

Implementacao esperada: comando `geo audit-performance`; API key via env opcional; resposta mockada nos testes; issues com lab vs field separados.

Regras obrigatorias: nao hardcodar chave; nao chamar API real nos testes; tratar 429/403.

Criterios de aceite: sem credencial gera mensagem clara; com response mockada gera score/metrics/issues.

Validacao: `python -m pytest tests/test_pagespeed_integration.py python -m pytest`.

Mensagem de commit: `feat: add PageSpeed performance audit`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: env vars podem ser mencionadas, valores reais nunca.

Proibicoes: nao salvar JSON bruto em `reports/`.

## Chunk 13. Content extraction

Objetivo: extrair conteudo principal para auditorias de conteudo e GEO.

Contexto: hoje o page audit extrai metadados, mas nao o corpo principal.

Tarefa: crie `ContentSnapshot` e extrator heuristico com title, h1, headings, main text, word count, links internos, imagens e baixa confianca quando o conteudo parecer template.

Arquivos provaveis: `src/geo_seo_engine/content/__init__.py`, `src/geo_seo_engine/content/extraction.py`, `tests/test_content_extraction.py`.

Implementacao esperada: usar BeautifulSoup; priorizar `main`, `article`, roles e fallback para body; remover nav/footer/script/style.

Regras obrigatorias: nao usar LLM; nao inventar resumo; preservar apenas trechos necessarios nos resultados.

Criterios de aceite: fixtures para artigo, landing, docs, LMS e pagina vazia.

Validacao: `python -m pytest tests/test_content_extraction.py python -m pytest`.

Mensagem de commit: `feat: add content extraction`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: texto de pagina pode ser privado; nao incluir fixtures reais.

Proibicoes: nao adicionar readability externa sem justificativa.

## Chunk 14. Content quality audit

Objetivo: auditar qualidade de conteudo com criterios acionaveis.

Contexto: fontes oficiais priorizam conteudo util, confiavel e people-first. O analyzer deve separar fato, inferencia e hipotese.

Tarefa: implemente checks para alinhamento title/H1, clareza de intencao, autoria/fonte quando aplicavel, atualizacao, estrutura, conteudo muito raso, claims sem evidencia textual e duplicidade interna basica se houver inventario.

Arquivos provaveis: `src/geo_seo_engine/content/quality.py`, `tests/test_content_quality.py`.

Implementacao esperada: `ContentQualityResult` com sinais e issues; severidade cautelosa; recomendacoes sem prometer ranking.

Regras obrigatorias: nao usar contagem de palavras como criterio unico; nao inventar autoridade/autoria.

Criterios de aceite: cada issue tem evidencia e caveat; fixtures cobrem casos bons e ruins.

Validacao: `python -m pytest tests/test_content_quality.py python -m pytest`.

Mensagem de commit: `feat: add content quality audit`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: nao armazenar textos longos em snapshots versionados.

Proibicoes: nao gerar conteudo final para publicar.

## Chunk 15. Entity/GEO audit

Objetivo: medir readiness semantico e de entidades.

Contexto: GEO no repo significa otimizacao para experiencias generativas sem hack ou promessa. A auditoria deve depender de evidencias.

Tarefa: crie modelos de entidade principal/secundarias, evidence spans, schema alignment e `GeoReadinessResult`. Implemente heuristicas simples baseadas em title/H1/schema/headings/texto.

Arquivos provaveis: `src/geo_seo_engine/entities/__init__.py`, `src/geo_seo_engine/entities/audit.py`, `tests/test_geo_entity_audit.py`.

Implementacao esperada: output com clareza, consistencia, evidencia, autoridade e cobertura; caveat obrigatorio sobre nao prometer IA.

Regras obrigatorias: nao usar LLM; nao inventar entidades ausentes; nao prometer citacao em AI Overviews/AI Mode.

Criterios de aceite: entidade clara passa; entidade ambigua gera issue; schema contraditorio gera issue.

Validacao: `python -m pytest tests/test_geo_entity_audit.py python -m pytest`.

Mensagem de commit: `feat: add GEO entity readiness audit`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: entidades de cliente em fixtures devem ser sinteticas.

Proibicoes: nao chamar APIs de IA.

## Chunk 16. Internal linking graph

Objetivo: construir grafo interno para arquitetura de informacao.

Contexto: links internos ajudam descoberta e contexto. A engine precisa diagnosticar profundidade, paginas orfas, anchors e links para canonicals.

Tarefa: implemente nodes/edges a partir do crawl, export JSON/CSV e analyzer de internal links.

Arquivos provaveis: `src/geo_seo_engine/crawler/link_graph.py`, `src/geo_seo_engine/analyzers/internal_links.py`, `tests/test_link_graph.py`.

Implementacao esperada: edge com source, target, anchor, rel, depth; detectar orphan dentro de sitemap/inventario, anchor vazio/generico e link para URL nao-canonica.

Regras obrigatorias: nao adicionar NetworkX salvo se realmente necessario; estrutura simples primeiro.

Criterios de aceite: grafo pequeno testado; CSV de nodes/edges valido; anchors preservados.

Validacao: `python -m pytest tests/test_link_graph.py python -m pytest`.

Mensagem de commit: `feat: add internal link graph`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: anchors podem revelar informacao privada; use fixtures sinteticas.

Proibicoes: nao gerar graficos binarios/imagens no repo.

## Chunk 17. Search Console integration

Objetivo: integrar Search Console Search Analytics de forma opcional.

Contexto: GSC requer autorizacao e retorna dados agregados/top rows. A engine deve usar dados para priorizar, nao como verdade completa.

Tarefa: implemente cliente GSC com service injetavel, request builder, dimensoes, filtros, rowLimit/startRow e normalizacao de linhas.

Arquivos provaveis: `src/geo_seo_engine/integrations/search_console.py`, `tests/test_search_console_integration.py`, docs de config.

Implementacao esperada: comando `geo gsc query`; sem credencial deve falhar com instrucao segura; testes com mock do service.

Regras obrigatorias: nao commitar credenciais; nao gravar exports brutos; nao chamar API real nos testes.

Criterios de aceite: response com rows normaliza clicks, impressions, ctr, position, keys; sem rows tratado.

Validacao: `python -m pytest tests/test_search_console_integration.py python -m pytest`.

Mensagem de commit: `feat: add Search Console integration`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: mencione env vars apenas com nomes; redija queries/URLs se config pedir.

Proibicoes: nao salvar `credentials.json`, `token.json` ou exports reais.

## Chunk 18. Opportunity engine

Objetivo: converter diagnostico em backlog priorizado.

Contexto: issues indicam problemas; oportunidades devem agrupar acoes por impacto, esforco, confianca, risco e dependencia.

Tarefa: crie `Opportunity`, priorizador e agrupamento por URL/categoria. Use GSC se disponivel, mas funcione sem dados externos.

Arquivos provaveis: `src/geo_seo_engine/opportunities/__init__.py`, `src/geo_seo_engine/opportunities/engine.py`, `tests/test_opportunity_engine.py`.

Implementacao esperada: oportunidades com `title`, `rationale`, `evidence`, `target_url`, `priority`, `dependencies`, `caveats`; dedup de issues relacionadas.

Regras obrigatorias: nao prometer resultado; marcar ausencia de dados como caveat.

Criterios de aceite: ranking deterministico; oportunidades com e sem GSC; nenhuma oportunidade sem evidencia.

Validacao: `python -m pytest tests/test_opportunity_engine.py python -m pytest`.

Mensagem de commit: `feat: add opportunity engine`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: nao usar dados reais de GSC em tests.

Proibicoes: nao gerar paginas ou conteudo automaticamente.

## Chunk 19. Brief generator

Objetivo: gerar briefs executaveis para oportunidades validadas.

Contexto: briefs devem orientar humanos, nao publicar conteudo automaticamente.

Tarefa: crie modelo `Brief` e renderer Markdown com persona, intencao, entidade, entidades secundarias, outline, perguntas a responder, fontes necessarias, links internos, criterios de qualidade e riscos.

Arquivos provaveis: `src/geo_seo_engine/opportunities/briefs.py`, `src/geo_seo_engine/templates/brief.md.j2`, `tests/test_brief_generator.py`.

Implementacao esperada: comando `geo brief create --opportunity-id`; se faltar dados, incluir `pesquisa pendente` em vez de inventar.

Regras obrigatorias: nao criar artigo final; nao inventar fontes, estatisticas ou cases.

Criterios de aceite: brief contem todos os campos obrigatorios; links internos sugeridos vêm do grafo/inventario.

Validacao: `python -m pytest tests/test_brief_generator.py python -m pytest`.

Mensagem de commit: `feat: add content brief generator`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: briefs podem conter estrategia privada; docs devem recomendar output fora do Git para clientes.

Proibicoes: nao usar API de LLM.

## Chunk 20. Cluster generator

Objetivo: planejar clusters sem doorway pages.

Contexto: clusters devem ter valor proprio por pagina e reforcar arquitetura interna, nao gerar variacoes massivas.

Tarefa: crie `ClusterPlan` com pillar, supporting pages, intents, entities, target URLs existentes/propostas, linking plan e criterio anti-doorway.

Arquivos provaveis: `src/geo_seo_engine/opportunities/clusters.py`, `tests/test_cluster_generator.py`.

Implementacao esperada: comando `geo cluster plan`; rejeitar propostas duplicadas ou sem intencao distinta.

Regras obrigatorias: incluir aviso contra conteudo em massa; exigir entidade/intencao para cada pagina.

Criterios de aceite: cluster valido renderiza; cluster doorway-like e rejeitado/rebaixado.

Validacao: `python -m pytest tests/test_cluster_generator.py python -m pytest`.

Mensagem de commit: `feat: add content cluster planner`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: nao incluir estrategia real de cliente em fixtures.

Proibicoes: nao criar arquivos de paginas finais.

## Chunk 21. AI visibility readiness simulation

Objetivo: simular readiness para experiencias generativas com caveats.

Contexto: Google afirma que AI features usam fundamentos de Search e nao ha requisito tecnico extra. A simulacao deve ser heuristica interna.

Tarefa: crie `AIReadinessResult` com perguntas provaveis, evidencias, lacunas, riscos e recomendacoes, baseado em conteudo, entidades, schema e links.

Arquivos provaveis: `src/geo_seo_engine/entities/ai_readiness.py`, `tests/test_ai_readiness.py`.

Implementacao esperada: output sempre inclui `Nao garante presenca, citacao, ranking ou trafego`; sem evidencia suficiente, score baixo e recomendacao de pesquisa.

Regras obrigatorias: nao chamar LLM; nao prometer AI Overviews/AI Mode; separar hipotese de fato.

Criterios de aceite: testes verificam caveat obrigatorio; nenhuma pergunta sem evidencia/entidade.

Validacao: `python -m pytest tests/test_ai_readiness.py python -m pytest`.

Mensagem de commit: `feat: add AI readiness simulation`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: nao usar prompts externos ou dados sensiveis.

Proibicoes: nao usar termos como garantia, ranking garantido ou citacao garantida.

## Chunk 22. Senior report

Objetivo: gerar report executivo e operacional consolidado.

Contexto: report atual Markdown e MVP. Report senior deve consolidar issues v2, scorecards, inventario, oportunidades e riscos.

Tarefa: implemente renderer `senior` com summary executivo, scorecards, top risks, top actions, backlog operacional, dependencias, apendice tecnico e caveats.

Arquivos provaveis: `src/geo_seo_engine/reporting/senior.py`, `src/geo_seo_engine/templates/senior-report.md.j2`, `tests/test_senior_report.py`.

Implementacao esperada: comando `geo report senior <url> --format markdown|json`; JSON e Markdown com mesmo modelo base.

Regras obrigatorias: report nao recalcula diagnostico; apenas renderiza modelos; escapar Markdown quando necessario.

Criterios de aceite: golden Markdown; JSON valido; report contem diagnostico, evidencia, risco, prioridade e proxima acao.

Validacao: `python -m pytest tests/test_senior_report.py python -m pytest`.

Mensagem de commit: `feat: add senior report`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: outputs de clientes devem ir para caminhos ignorados; exemplos sinteticos apenas.

Proibicoes: nao salvar automaticamente em `reports/` versionado.

## Chunk 23. CI/quality gates

Objetivo: permitir uso em pipeline com exit code previsivel.

Contexto: uma engine senior deve falhar CI quando thresholds configurados forem violados.

Tarefa: implemente `geo check` com `--fail-on`, `--min-score`, `--config`, `--format json` e exit codes documentados.

Arquivos provaveis: `src/geo_seo_engine/scoring/gates.py`, `src/geo_seo_engine/cli.py`, `tests/test_quality_gates.py`, `tests/test_cli_check.py`.

Implementacao esperada: `QualityGateResult` com passed, failed_rules, exit_code; falha tecnica diferente de falha de gate.

Regras obrigatorias: nao falhar por checks opcionais desabilitados; mensagens claras para CI.

Criterios de aceite: testes para pass, fail por critical, fail por score, erro tecnico.

Validacao: `python -m pytest tests/test_quality_gates.py tests/test_cli_check.py python -m pytest`.

Mensagem de commit: `feat: add SEO quality gates`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: CI nao deve imprimir segredos de env.

Proibicoes: nao adicionar workflow que chama sites reais sem permissao.

## Chunk 24. Release process

Objetivo: formalizar processo de release seguro.

Contexto: antes de distribuicao, o projeto precisa de checklist, changelog e build validation.

Tarefa: adicione `CHANGELOG.md`, checklist de release e, se fizer sentido, workflow local/documentado para testes, diff check, secrets scan e build.

Arquivos provaveis: `CHANGELOG.md`, `docs/release-process.md`, `.github/workflows/ci.yml` se autorizado pelo contexto.

Implementacao esperada: docs com comandos; CI basico roda tests sem secrets; README aponta para release docs se necessario.

Regras obrigatorias: nao publicar pacote; nao criar release GitHub; nao adicionar tokens.

Criterios de aceite: comandos documentados funcionam localmente; workflow nao depende de credenciais.

Validacao: `python -m pytest && git diff --check`.

Mensagem de commit: `docs: add release process`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: secrets scan deve tolerar falsos positivos documentais revisados.

Proibicoes: nao fazer tag, push ou gh release.

## Chunk 25. Senior documentation

Objetivo: documentar comportamento implementado para usuario e desenvolvedor.

Contexto: docs devem refletir features reais, nao roadmap futuro.

Tarefa: crie guias de usuario, configuracao, desenvolvimento de analyzers, seguranca operacional de crawling e exemplos sinteticos.

Arquivos provaveis: `docs/user-guide.md`, `docs/config-reference.md`, `docs/developer-guide.md`, `docs/analyzer-guide.md`, `docs/crawling-safety.md`, `examples/`.

Implementacao esperada: cada comando documentado deve existir; exemplos usam `example.com`; limites e nao promessas aparecem claramente.

Regras obrigatorias: separar MVP atual de features futuras; nao incluir dados reais; nao inflar README.

Criterios de aceite: docs claras, comandos validos, varredura de segredos limpa ou falsos positivos documentados.

Validacao: `python -m pytest && git diff --check && grep -RniE 'api[_-]?key|token|secret|password|passwd|credential|bearer|private[_-]?key' . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ || true`.

Mensagem de commit: `docs: add senior engine documentation`.

Comando de validacao pos-OpenCode: `git status --short && git diff --check && python -m pytest`.

Observacoes de seguranca: documentar falsos positivos se houver nomes de variaveis.

Proibicoes: nao prometer ranking, trafego, indexacao ou presenca em IA.
