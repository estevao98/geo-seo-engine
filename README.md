# geo-seo-engine

`geo-seo-engine` is a local-first SEO + GEO command-line engine for auditing, planning and reporting organic growth work with deterministic, reviewable outputs.

It is built for technical SEO workflows, SaaS/content teams, consultants, maintainers and contributors who need clear diagnostics, evidence, risks, priorities and next actions without depending on private dashboards or opaque SaaS state.

## What It Solves

- Turns scattered SEO checks into a reproducible CLI workflow.
- Audits technical, content, entity, internal linking, image, social, hreflang, rendering and performance signals.
- Converts local evidence into prioritized opportunities, content briefs, cluster plans, AI-readiness signals and senior reports.
- Keeps generated artifacts, client data and credentials out of the repository by default.
- Documents limitations explicitly instead of promising rankings, traffic or AI inclusion.

## Feature Overview

Current capabilities include:

- Project config bootstrap and validation with `geo init` and `geo config validate`.
- Public URL audits for pages, robots.txt, sitemaps, structured data and aggregated site reports.
- Bounded internal crawling with host, depth, page and include/exclude controls.
- URL inventory and technical findings from crawled data.
- Content extraction and deterministic content-quality checks.
- Entity-readiness checks for publisher, authorship and topical signals.
- Internal-link graph, image, social metadata and hreflang audits.
- Static rendering comparison and local PageSpeed/Lighthouse JSON analysis.
- Local Search Console export summarization without credentials.
- Opportunity prioritization, content briefs, content clusters, AI-readiness simulation and senior reporting from local JSON inputs.

## Quickstart

Requirements:

- Python 3.12 or newer.
- Network access only for commands that fetch public URLs.

Install from the repository root:

```bash
python -m pip install -e ".[dev]"
geo version
```

Create and validate a safe project config:

```bash
geo init
geo config validate --config geo-seo.yml
```

A versioned, synthetic example is available at [`examples/geo-seo.example.yml`](examples/geo-seo.example.yml). Do not put tokens, credentials, raw exports or private client data in `geo-seo.yml`.

## Example Workflow

Start with a conservative crawl and write generated output outside the repository:

```bash
geo crawl https://example.com \
  --max-pages 25 \
  --max-depth 2 \
  --allowed-host example.com \
  --output /tmp/example-crawl.json
```

Run focused audits:

```bash
geo audit-site https://example.com --format markdown --output /tmp/example-site-audit.md
geo inventory https://example.com --format json --output /tmp/example-inventory.json
geo audit-technical https://example.com --format json --output /tmp/example-technical.json
geo audit-content-quality https://example.com --format json --output /tmp/example-content-quality.json
geo audit-entity-readiness https://example.com --format json --output /tmp/example-entity-readiness.json
```

Then use local JSON inputs to plan and report:

```bash
geo opportunity --input /tmp/audits.json --format json --output /tmp/opportunities.json
geo content-brief --input /tmp/audits.json --format json --output /tmp/content-briefs.json
geo content-cluster --input /tmp/planning.json --format json --output /tmp/content-clusters.json
geo ai-readiness --input /tmp/planning.json --format json --output /tmp/ai-readiness.json
geo senior-report --input /tmp/planning.json --format json --output /tmp/senior-report.json
```

The workflow is intentionally evidence-driven:

```text
config -> http -> crawler -> inventory -> audits -> opportunities -> planning -> readiness -> senior report
```

## Module Map

| Area | Modules | Purpose |
|---|---|---|
| Setup and policy | `config`, `quality_gates` | Validate project scope and block generated or sensitive tracked files. |
| Collection | `http`, `crawler`, `inventory` | Fetch public URLs safely, crawl within limits and summarize discovered pages. |
| Technical SEO | `analyzers`, `technical`, `rendering`, `performance` | Audit pages, robots, sitemaps, structured data, technical inventory, rendering and local performance payloads. |
| Content and entities | `content`, `content_quality`, `entity_readiness` | Extract main content and inspect deterministic usefulness, coverage, authorship and publisher signals. |
| Site graph and metadata | `internal_links`, `images`, `social`, `i18n` | Review links, image markup, social metadata and hreflang annotations. |
| Planning | `opportunities`, `content_briefs`, `content_clusters`, `ai_readiness` | Convert evidence into backlog items, briefs, clusters and generative-search readiness signals. |
| Reporting | `senior_report`, `reporting`, `cli` | Serialize operational outputs for humans, automation and handoff. |

## Why Deterministic And Local-First

- CLI commands return inspectable tables, JSON or Markdown.
- Planning modules operate on provided local inputs instead of hidden remote state.
- Findings are rule-based and should include evidence, risk, priority and next action.
- Network access is explicit: URL audits and crawls fetch public resources; local analyzers consume files already supplied by the operator.
- Generated reports and private exports should be written to `/tmp` or another non-versioned location.

## Safety And Data Policy

Do not commit:

- `.env` or real environment files.
- Tokens, service accounts, credentials or database dumps.
- Raw Search Console, Analytics, scanner or private client exports.
- Generated reports with private data.
- `site_config.json`, `terraform.tfstate` or `reports/raw`.

Before publishing changes, run the local gates and review [`SECURITY.md`](SECURITY.md):

```bash
git status --short
git diff --stat
git diff --check
python -m geo_seo_engine.quality_gates
python -m pytest
```

## Documentation

- [`docs/senior-engine/usage.md`](docs/senior-engine/usage.md): setup, CLI commands, safe operation and output interpretation.
- [`docs/senior-engine/release-process.md`](docs/senior-engine/release-process.md): release checklist, local gates, CI behavior and safe-file policy.
- [`docs/senior-engine/maintenance.md`](docs/senior-engine/maintenance.md): module responsibilities, troubleshooting and handoff notes.
- [`docs/senior-engine/architecture-v2.md`](docs/senior-engine/architecture-v2.md): senior engine architecture.
- [`docs/senior-engine/foundation-hardening.md`](docs/senior-engine/foundation-hardening.md): foundation contracts and implemented boundaries.
- [`docs/senior-engine/roadmap.md`](docs/senior-engine/roadmap.md): completed senior roadmap context.
- [`CONTRIBUTING.md`](CONTRIBUTING.md): contribution workflow.
- [`SECURITY.md`](SECURITY.md): security expectations and reporting guidance.

## Status And Release Readiness

The senior roadmap is complete for the current local CLI engine. The repository includes usage, release and maintenance documentation, local quality gates and CI checks for import smoke tests, CLI smoke tests, whitespace hygiene, sensitive/generated file guards and the pytest suite.

The current project state is suitable as a portfolio-grade, public-facing SEO/GEO engine foundation. Future API, SaaS, dashboard or managed-service layers are outside this README's scope.

## Non-Promises And Limitations

- Does not promise traffic growth, ranking improvement, indexing, AI citation or inclusion in generative answers.
- Does not create or recommend black hat SEO, PBNs, cloaking, doorway pages, spam or artificial backlinks.
- Does not replace expert review; outputs are evidence and heuristics for prioritization.
- Does not fetch private dashboards or use credentials unless a future integration explicitly documents that behavior.
- Does not make claims from missing data; absent evidence should be treated as a limitation or hypothesis.
