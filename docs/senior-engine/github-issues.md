# GitHub Issues Commands

O MCP `github` esta desativado. Estes comandos sao apenas para copiar/executar manualmente depois de confirmar autenticacao do `gh` CLI e revisar os textos. Nao execute automaticamente sem confirmacao explicita.

## Labels Sugeridas

```bash
gh label create "type:epic" --description "Epic issue" --color "5319e7"
gh label create "type:architecture" --description "Architecture and contracts" --color "1d76db"
gh label create "type:feature" --description "Feature implementation" --color "0e8a16"
gh label create "type:docs" --description "Documentation" --color "0075ca"
gh label create "area:technical-seo" --description "Technical SEO" --color "c2e0c6"
gh label create "area:geo" --description "GEO and entity readiness" --color "bfdadc"
gh label create "area:content" --description "Content quality and briefs" --color "fef2c0"
gh label create "area:data" --description "External data integrations" --color "d4c5f9"
gh label create "area:reporting" --description "Reports and exports" --color "fbca04"
gh label create "area:security" --description "Security and privacy" --color "b60205"
gh label create "priority:p0" --description "Foundational/blocking" --color "b60205"
gh label create "priority:p1" --description "High priority" --color "d93f0b"
gh label create "priority:p2" --description "Medium priority" --color "fbca04"
gh label create "priority:p3" --description "Optional/later" --color "c5def5"
```

## Milestones Sugeridos

```bash
gh milestone create "v0.2 Core Contracts" --description "Schemas, project config, URL normalization and centralized HTTP client."
gh milestone create "v0.3 Crawl Inventory" --description "Scoped crawler, URL inventory and advanced technical SEO."
gh milestone create "v0.4 Content And GEO" --description "Content extraction, content quality, entities, GEO readiness and internal linking."
gh milestone create "v0.5 Data And Opportunities" --description "Search Console, performance integrations, opportunity engine, briefs, clusters and senior report."
gh milestone create "v1.0 Automation And Docs" --description "Quality gates, release process and senior documentation."
```

## EPIC Principal

```bash
gh issue create \
  --title "EPIC: evolve geo-seo-engine into a senior SEO/GEO engine" \
  --label "type:epic,priority:p0" \
  --milestone "v1.0 Automation And Docs" \
  --body "Goal: evolve the current MVP into a senior technical SEO, GEO, content, data, reporting and automation engine.\n\nScope:\n- Preserve the existing CLI while introducing stable v2 contracts.\n- Add project config, URL normalization, centralized HTTP, crawler, inventory, advanced audits, content/entity readiness, integrations, opportunities, reports and CI gates.\n- Avoid promises of ranking, traffic, indexation or AI visibility.\n\nReferences:\n- docs/senior-engine/research.md\n- docs/senior-engine/gap-analysis.md\n- docs/senior-engine/architecture-v2.md\n- docs/senior-engine/roadmap.md\n- docs/senior-engine/prompt-pack.md\n\nAcceptance:\n- Work is delivered in small chunks.\n- Every issue includes tests and security review.\n- External integrations are optional and do not require committed credentials."
```

## Issues Por Fase

### 1. Architecture v2 e schemas estaveis

```bash
gh issue create --title "Add architecture v2 core schemas" --label "type:architecture,priority:p0,area:technical-seo" --milestone "v0.2 Core Contracts" --body "Implement core v2 models for audit runs, issues, evidence, recommendations, URL identity and score summaries. Preserve existing MVP CLI. Acceptance: JSON serializable models, tests for validation, legacy issue adapter, no migration of every analyzer yet. Prompt: docs/senior-engine/prompt-pack.md#chunk-1-architecture-v2-e-schemas-estaveis"
```

### 2. Config por projeto

```bash
gh issue create --title "Add project configuration" --label "type:feature,priority:p0,area:security" --milestone "v0.2 Core Contracts" --body "Add geo-seo.yml support, config models, loader, geo init and geo config validate. Acceptance: safe example config, validation errors, no committed secrets, existing CLI unchanged. Prompt: docs/senior-engine/prompt-pack.md#chunk-2-config-por-projeto"
```

### 3. URL normalization

```bash
gh issue create --title "Add URL normalization utilities" --label "type:architecture,priority:p0,area:technical-seo" --milestone "v0.2 Core Contracts" --body "Centralize URL identity and normalization for relative URLs, fragments, default ports, host case, query handling and tracking params. Acceptance: pure functions, broad tests, no network calls. Prompt: docs/senior-engine/prompt-pack.md#chunk-3-url-normalization"
```

### 4. HTTP client centralizado

```bash
gh issue create --title "Add centralized safe HTTP client" --label "type:architecture,priority:p0,area:security" --milestone "v0.2 Core Contracts" --body "Create FetchRequest/FetchResult and a single HTTP client with timeout, redirects, max bytes and safety policy. Acceptance: analyzers can use injected client or FetchResult; tests cover timeout, redirects, max bytes and errors. Prompt: docs/senior-engine/prompt-pack.md#chunk-4-http-client-centralizado"
```

### 5. Crawler multi-page

```bash
gh issue create --title "Add scoped multi-page crawler" --label "type:feature,priority:p1,area:technical-seo" --milestone "v0.3 Crawl Inventory" --body "Implement bounded crawler with frontier, dedup, max_pages, max_depth, include/exclude and link extraction. Acceptance: no infinite crawl, allowed_hosts respected, tests use mocks only. Prompt: docs/senior-engine/prompt-pack.md#chunk-5-crawler-multi-page"
```

### 6. URL inventory audit

```bash
gh issue create --title "Add URL inventory audit" --label "type:feature,priority:p1,area:technical-seo" --milestone "v0.3 Crawl Inventory" --body "Generate URL inventory with status, source, depth, canonical, noindex, title and issues. Acceptance: JSON/CSV/Markdown outputs, one row per normalized URL, safe examples. Prompt: docs/senior-engine/prompt-pack.md#chunk-6-url-inventory-audit"
```

### 7. Technical SEO avancado

```bash
gh issue create --title "Add advanced technical SEO audit" --label "type:feature,priority:p1,area:technical-seo" --milestone "v0.3 Crawl Inventory" --body "Add multi-page checks for metadata duplication, canonical conflicts, redirects, x-robots-tag, status classes and indexability. Acceptance: v2 issues with evidence and next actions. Prompt: docs/senior-engine/prompt-pack.md#chunk-7-technical-seo-avancado"
```

### 8. Image audit

```bash
gh issue create --title "Add image SEO audit" --label "type:feature,priority:p2,area:technical-seo" --milestone "v0.4 Content And GEO" --body "Audit img src, alt, picture fallback, srcset and optional broken image checks. Acceptance: no remote image fetch by default, decorative images handled cautiously. Prompt: docs/senior-engine/prompt-pack.md#chunk-8-image-audit"
```

### 9. Open Graph/Twitter Card audit

```bash
gh issue create --title "Add social metadata audit" --label "type:feature,priority:p3,area:content" --milestone "v0.4 Content And GEO" --body "Audit OG and Twitter Card metadata without treating it as core SEO. Acceptance: low/medium severity only, conflict checks with title/canonical. Prompt: docs/senior-engine/prompt-pack.md#chunk-9-open-graphtwitter-card-audit"
```

### 10. Hreflang/i18n audit

```bash
gh issue create --title "Add hreflang and i18n audit" --label "type:feature,priority:p3,area:technical-seo" --milestone "v0.4 Content And GEO" --body "Audit hreflang syntax, x-default, reciprocal links and canonical compatibility. Acceptance: no issue for monolingual sites unless configured or tags exist. Prompt: docs/senior-engine/prompt-pack.md#chunk-10-hreflangi18n-audit"
```

### 11. JavaScript/rendering audit com Playwright

```bash
gh issue create --title "Add optional JavaScript rendering audit" --label "type:feature,priority:p2,area:technical-seo" --milestone "v0.4 Content And GEO" --body "Use optional Playwright integration to compare initial and rendered HTML signals. Acceptance: dependency optional, no screenshots by default, graceful failure without browser. Prompt: docs/senior-engine/prompt-pack.md#chunk-11-javascriptrendering-audit-com-playwright"
```

### 12. Performance/PageSpeed/Lighthouse integration

```bash
gh issue create --title "Add optional performance integrations" --label "type:feature,priority:p2,area:data" --milestone "v0.5 Data And Opportunities" --body "Integrate PageSpeed Insights and prepare Lighthouse interface. Acceptance: no hardcoded keys, mock tests, clear handling for no credentials and 429/403. Prompt: docs/senior-engine/prompt-pack.md#chunk-12-performancepagespeedlighthouse-integration"
```

### 13. Content extraction

```bash
gh issue create --title "Add main content extraction" --label "type:feature,priority:p1,area:content" --milestone "v0.4 Content And GEO" --body "Extract main content snapshots from HTML using deterministic heuristics. Acceptance: article, landing page, docs, LMS and empty page fixtures; no LLM. Prompt: docs/senior-engine/prompt-pack.md#chunk-13-content-extraction"
```

### 14. Content quality audit

```bash
gh issue create --title "Add content quality audit" --label "type:feature,priority:p1,area:content" --milestone "v0.4 Content And GEO" --body "Evaluate people-first content signals with evidence and caveats. Acceptance: no word-count-only checks, no invented facts, issues separate fact/inference/hypothesis. Prompt: docs/senior-engine/prompt-pack.md#chunk-14-content-quality-audit"
```

### 15. Entity/GEO audit

```bash
gh issue create --title "Add GEO entity readiness audit" --label "type:feature,priority:p1,area:geo" --milestone "v0.4 Content And GEO" --body "Map primary/secondary entities, evidence spans, schema alignment and GEO readiness. Acceptance: no AI visibility promise, no LLM, evidence required. Prompt: docs/senior-engine/prompt-pack.md#chunk-15-entitygeo-audit"
```

### 16. Internal linking graph

```bash
gh issue create --title "Add internal linking graph" --label "type:feature,priority:p1,area:technical-seo" --milestone "v0.4 Content And GEO" --body "Build internal link graph with nodes, edges, anchors, depth, orphan pages and canonical consistency. Acceptance: JSON/CSV exports and tests for graph cases. Prompt: docs/senior-engine/prompt-pack.md#chunk-16-internal-linking-graph"
```

### 17. Search Console integration

```bash
gh issue create --title "Add Search Console Search Analytics integration" --label "type:feature,priority:p2,area:data" --milestone "v0.5 Data And Opportunities" --body "Add optional GSC client with dimensions, filters, rowLimit/startRow and safe auth via environment. Acceptance: mock tests, no credentials committed, no raw exports by default. Prompt: docs/senior-engine/prompt-pack.md#chunk-17-search-console-integration"
```

### 18. Opportunity engine

```bash
gh issue create --title "Add opportunity engine" --label "type:feature,priority:p1,area:content" --milestone "v0.5 Data And Opportunities" --body "Convert issues, inventory, content, links and optional GSC data into prioritized opportunities. Acceptance: every opportunity has evidence and caveats; no promises. Prompt: docs/senior-engine/prompt-pack.md#chunk-18-opportunity-engine"
```

### 19. Brief generator

```bash
gh issue create --title "Add content brief generator" --label "type:feature,priority:p3,area:content" --milestone "v0.5 Data And Opportunities" --body "Generate safe briefs from validated opportunities with persona, intent, entities, outline, sources needed, internal links and quality criteria. Acceptance: no final article generation and no invented sources. Prompt: docs/senior-engine/prompt-pack.md#chunk-19-brief-generator"
```

### 20. Cluster generator

```bash
gh issue create --title "Add content cluster planner" --label "type:feature,priority:p3,area:content" --milestone "v0.5 Data And Opportunities" --body "Plan clusters with pillar/supporting pages, intents, entities and internal linking while rejecting doorway-like plans. Acceptance: anti-doorway criteria tested. Prompt: docs/senior-engine/prompt-pack.md#chunk-20-cluster-generator"
```

### 21. AI visibility readiness simulation

```bash
gh issue create --title "Add AI readiness simulation" --label "type:feature,priority:p3,area:geo" --milestone "v0.5 Data And Opportunities" --body "Add heuristic AI readiness report based on content, entities, schema and links. Acceptance: mandatory caveat that it does not guarantee presence, citation, ranking or traffic. Prompt: docs/senior-engine/prompt-pack.md#chunk-21-ai-visibility-readiness-simulation"
```

### 22. Senior report

```bash
gh issue create --title "Add senior executive and operational report" --label "type:feature,priority:p1,area:reporting" --milestone "v0.5 Data And Opportunities" --body "Render senior Markdown/JSON reports with executive summary, scorecards, risks, actions, backlog and technical appendix. Acceptance: golden tests, escaping, evidence/risk/priority/next action present. Prompt: docs/senior-engine/prompt-pack.md#chunk-22-senior-report"
```

### 23. CI/quality gates

```bash
gh issue create --title "Add CI quality gates" --label "type:feature,priority:p1,area:reporting" --milestone "v1.0 Automation And Docs" --body "Add geo check with fail-on, min-score, JSON result and stable exit codes. Acceptance: pass/fail tests and no external network in CI by default. Prompt: docs/senior-engine/prompt-pack.md#chunk-23-ciquality-gates"
```

### 24. Release process

```bash
gh issue create --title "Document release process" --label "type:docs,priority:p2" --milestone "v1.0 Automation And Docs" --body "Add changelog and release checklist for tests, diff check, secrets scan and build validation. Acceptance: no publishing, tags or gh release automation without explicit approval. Prompt: docs/senior-engine/prompt-pack.md#chunk-24-release-process"
```

### 25. Senior documentation

```bash
gh issue create --title "Add senior user and developer documentation" --label "type:docs,priority:p1" --milestone "v1.0 Automation And Docs" --body "Document implemented commands, config, analyzer development, crawling safety and examples. Acceptance: docs distinguish implemented behavior from roadmap and contain no private data. Prompt: docs/senior-engine/prompt-pack.md#chunk-25-senior-documentation"
```

## Ordem De Execucao Recomendada

1. Criar labels e milestones.
2. Criar EPIC principal.
3. Criar issues das fases 1 a 25.
4. Linkar issues menores na EPIC manualmente ou por comentario.
5. Antes de executar qualquer fase, abrir o prompt correspondente em `docs/senior-engine/prompt-pack.md`.
