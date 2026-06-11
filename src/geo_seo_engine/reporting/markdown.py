from __future__ import annotations

from geo_seo_engine.analyzers.site_audit import SiteAuditResult
from geo_seo_engine.reporting.severity import classify_issues, severity_counts


def markdown_list(items: list[str]) -> str:
    if not items:
        return "- Nenhum item encontrado."
    return "\n".join(f"- `{item}`" for item in items)


def markdown_classified_issues(items: list[str]) -> str:
    classified = classify_issues(items)
    if not classified:
        return "- Nenhum item encontrado."

    return "\n".join(
        f"- **{item.severity}** — `{item.issue}`: {item.reason}"
        for item in classified
    )


def render_site_markdown(result: SiteAuditResult) -> str:
    page = result.page
    robots = result.robots
    sitemap = result.sitemap

    return f"""# Site Audit Report

## Summary

| Field | Value |
|---|---|
| URL | `{result.url}` |
| Total issues | `{len(result.issues)}` |
| Critical issues | `{severity_counts(result.issues)["critical"]}` |
| High issues | `{severity_counts(result.issues)["high"]}` |
| Medium issues | `{severity_counts(result.issues)["medium"]}` |
| Low issues | `{severity_counts(result.issues)["low"]}` |
| Page status | `{page.status_code}` |
| Robots status | `{robots.status_code}` |
| Sitemap status | `{sitemap.status_code}` |

## Page

| Field | Value |
|---|---|
| Final URL | `{page.final_url}` |
| Status | `{page.status_code}` |
| Title | `{page.title or "—"}` |
| Meta description | `{page.meta_description or "—"}` |
| H1 | `{", ".join(page.h1) if page.h1 else "—"}` |
| Canonical | `{page.canonical or "—"}` |
| Meta robots | `{page.meta_robots or "—"}` |
| Noindex | `{"yes" if page.noindex else "no"}` |
| Internal links | `{page.internal_links}` |
| External links | `{page.external_links}` |

### Page issues

{markdown_list(page.issues)}

## Robots.txt

| Field | Value |
|---|---|
| URL | `{robots.url}` |
| Final URL | `{robots.final_url}` |
| Status | `{robots.status_code}` |
| Content-Type | `{robots.content_type or "—"}` |
| User-agents | `{", ".join(robots.user_agents) if robots.user_agents else "—"}` |
| Allow count | `{robots.allow_count}` |
| Disallow count | `{robots.disallow_count}` |
| Blocks all | `{"yes" if robots.blocks_all else "no"}` |
| Sitemaps | `{", ".join(robots.sitemap_urls) if robots.sitemap_urls else "—"}` |

### Robots issues

{markdown_list(robots.issues)}

## Sitemap

| Field | Value |
|---|---|
| URL | `{sitemap.url}` |
| Final URL | `{sitemap.final_url}` |
| Status | `{sitemap.status_code}` |
| Content-Type | `{sitemap.content_type or "—"}` |
| Sitemap type | `{sitemap.sitemap_type or "—"}` |
| URL count | `{sitemap.url_count}` |
| Duplicate URLs | `{len(sitemap.duplicate_urls)}` |
| Invalid URLs | `{len(sitemap.invalid_urls)}` |
| URLs with query | `{len(sitemap.urls_with_query)}` |
| Off-domain URLs | `{len(sitemap.off_domain_urls)}` |
| Missing lastmod | `{sitemap.missing_lastmod_count}` |

### Sitemap issues

{markdown_list(sitemap.issues)}

## All issues

{markdown_classified_issues(result.issues)}
"""
