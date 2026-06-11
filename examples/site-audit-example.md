# Site Audit Report

## Summary

| Field | Value |
|---|---|
| URL | `https://example.com` |
| Score | `50` |
| Next action | `Adicionar uma tag canonical apontando para a URL canônica da própria página.` |
| Total issues | `6` |
| Critical issues | `0` |
| High issues | `2` |
| Medium issues | `2` |
| Low issues | `2` |
| Page status | `200` |
| Robots status | `404` |
| Sitemap status | `404` |

## Page

| Field | Value |
|---|---|
| Final URL | `https://example.com` |
| Status | `200` |
| Title | `Example Domain` |
| Meta description | `—` |
| H1 | `Example Domain` |
| Canonical | `—` |
| Meta robots | `—` |
| Noindex | `no` |
| Internal links | `0` |
| External links | `1` |

### Page issues

- `missing_meta_description`
- `missing_canonical`

## Robots.txt

| Field | Value |
|---|---|
| URL | `https://example.com/robots.txt` |
| Final URL | `https://example.com/robots.txt` |
| Status | `404` |
| Content-Type | `text/html` |
| User-agents | `—` |
| Allow count | `0` |
| Disallow count | `0` |
| Blocks all | `no` |
| Sitemaps | `—` |

### Robots issues

- `status_code_not_200: 404`
- `robots_txt_4xx_assumed_no_restrictions`

## Sitemap

| Field | Value |
|---|---|
| URL | `https://example.com/sitemap.xml` |
| Final URL | `https://example.com/sitemap.xml` |
| Status | `404` |
| Content-Type | `text/html` |
| Sitemap type | `—` |
| URL count | `0` |
| Duplicate URLs | `0` |
| Invalid URLs | `0` |
| URLs with query | `0` |
| Off-domain URLs | `0` |
| Missing lastmod | `0` |

### Sitemap issues

- `status_code_not_200: 404`

## Structured Data

| Field | Value |
|---|---|
| JSON-LD blocks | `0` |
| Valid JSON-LD blocks | `0` |
| Invalid JSON-LD blocks | `0` |
| Types | `—` |

### JSON-LD blocks

- Nenhum bloco JSON-LD encontrado.

### Structured Data issues

- `missing`

## All issues

- **medium** — `page.missing_meta_description`: Afeta qualidade, clareza ou eficiência de rastreamento.
- **high** — `page.missing_canonical`: Afeta sinais técnicos ou semânticos importantes para SEO.
- **low** — `robots.status_code_not_200: 404`: Erro 4xx em robots.txt, exceto 429, normalmente é tratado como ausência de robots.txt.
- **low** — `robots.robots_txt_4xx_assumed_no_restrictions`: Melhoria recomendada, mas normalmente não bloqueia indexação por si só.
- **high** — `sitemap.status_code_not_200: 404`: Sitemap inacessível prejudica descoberta e validação de URLs importantes.
- **medium** — `structured_data.missing`: Afeta qualidade, clareza ou eficiência de rastreamento.

## Recommendations

- `page.missing_canonical` — **Ação:** Adicionar uma tag canonical apontando para a URL canônica da própria página. **Motivo:** Ajuda a consolidar sinais e reduzir ambiguidade com URLs duplicadas ou variantes.
- `sitemap.status_code_not_200: 404` — **Ação:** Corrigir a rota do sitemap ou publicar um sitemap XML válido acessível por HTTP 200. **Motivo:** Sitemap inacessível prejudica descoberta e validação de URLs importantes.
- `page.missing_meta_description` — **Ação:** Criar uma meta description única, objetiva e alinhada à intenção de busca da página. **Motivo:** Não é fator direto de ranking, mas pode melhorar clareza do snippet e taxa de clique.
- `structured_data.missing` — **Ação:** Adicionar JSON-LD relevante para o tipo real da página, como Organization, WebSite, Article, Product ou FAQPage quando aplicável. **Motivo:** Dados estruturados ajudam mecanismos de busca e experiências generativas a entender entidades, contexto e elegibilidade a recursos enriquecidos.
- `robots.status_code_not_200: 404` — **Ação:** Decidir se o site precisa de robots.txt; se sim, publicar um arquivo válido em /robots.txt. **Motivo:** Um 404 em robots.txt normalmente não bloqueia rastreamento, mas um arquivo válido permite declarar Sitemap e regras explícitas.
- `robots.robots_txt_4xx_assumed_no_restrictions` — **Ação:** Criar robots.txt somente se o site precisar declarar Sitemap ou regras explícitas de rastreamento. **Motivo:** Erro 4xx em robots.txt normalmente não bloqueia rastreamento, mas um arquivo válido melhora clareza operacional.
