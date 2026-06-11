# Site Audit Report

Example report generated from the public neutral domain `https://example.com`.
Values may change when the audit is executed again because they depend on live HTTP responses.

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

- **high** — `sitemap.status_code_not_200: 404`: Sitemap inacessível reduz descoberta e validação de URLs.
- **medium** — `page.missing_meta_description`: Meta description ausente reduz controle do snippet e clareza editorial.
- **low** — `robots.status_code_not_200: 404`: Robots.txt inacessível deve ser revisado, mas ausência de bloqueio explícito costuma ter impacto limitado.

## Recommendations

- `sitemap.status_code_not_200: 404` — **Ação:** Corrigir a rota do sitemap ou publicar um sitemap XML válido acessível por HTTP 200. **Motivo:** Sitemaps ajudam mecanismos de busca a descobrir URLs canônicas e datas de atualização.
- `page.missing_meta_description` — **Ação:** Escrever uma meta description única, factual e alinhada à intenção da página. **Motivo:** A descrição melhora a clareza do resultado e reduz ambiguidade para usuários e sistemas de recuperação.
- `robots.status_code_not_200: 404` — **Ação:** Publicar um robots.txt simples com diretivas explícitas e referência ao sitemap quando aplicável. **Motivo:** Um robots.txt válido torna regras de rastreamento e descoberta mais previsíveis.
