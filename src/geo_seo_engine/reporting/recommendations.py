from __future__ import annotations

from dataclasses import dataclass

from geo_seo_engine.reporting.severity import classify_issue


_SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


@dataclass(frozen=True)
class IssueRecommendation:
    issue: str
    action: str
    rationale: str


def recommend_issue(issue: str) -> IssueRecommendation:
    if issue.startswith("page.missing_canonical"):
        return IssueRecommendation(
            issue=issue,
            action="Adicionar uma tag canonical apontando para a URL canônica da própria página.",
            rationale="Ajuda a consolidar sinais e reduzir ambiguidade com URLs duplicadas ou variantes.",
        )

    if issue.startswith("page.missing_meta_description"):
        return IssueRecommendation(
            issue=issue,
            action="Criar uma meta description única, objetiva e alinhada à intenção de busca da página.",
            rationale="Não é fator direto de ranking, mas pode melhorar clareza do snippet e taxa de clique.",
        )

    if issue.startswith("page.missing_title"):
        return IssueRecommendation(
            issue=issue,
            action="Adicionar um title único, descritivo e específico para a página.",
            rationale="O title é um dos principais sinais usados para representar a página nos resultados de busca.",
        )

    if issue.startswith("page.missing_h1"):
        return IssueRecommendation(
            issue=issue,
            action="Adicionar um H1 claro e único que descreva o tema principal da página.",
            rationale="Ajuda usuários e mecanismos a entenderem rapidamente o assunto principal.",
        )

    if issue.startswith("page.meta_robots_noindex"):
        return IssueRecommendation(
            issue=issue,
            action="Remover noindex apenas se a página realmente deve aparecer em mecanismos de busca.",
            rationale="A diretiva noindex pode impedir a presença da página no índice.",
        )

    if issue.startswith("robots.disallow_all_found"):
        return IssueRecommendation(
            issue=issue,
            action="Revisar o Disallow: / e remover o bloqueio se páginas públicas devem ser rastreadas.",
            rationale="Um bloqueio amplo pode impedir rastreamento de áreas importantes do site.",
        )

    if issue.startswith("robots.status_code_not_200"):
        return IssueRecommendation(
            issue=issue,
            action="Decidir se o site precisa de robots.txt; se sim, publicar um arquivo válido em /robots.txt.",
            rationale="Um 404 em robots.txt normalmente não bloqueia rastreamento, mas um arquivo válido permite declarar Sitemap e regras explícitas.",
        )

    if issue.startswith("robots.missing_sitemap_directive"):
        return IssueRecommendation(
            issue=issue,
            action="Adicionar uma diretiva Sitemap: apontando para o sitemap principal.",
            rationale="Facilita a descoberta do sitemap por crawlers.",
        )

    if issue.startswith("robots.robots_txt_4xx_assumed_no_restrictions"):
        return IssueRecommendation(
            issue=issue,
            action="Criar robots.txt somente se o site precisar declarar Sitemap ou regras explícitas de rastreamento.",
            rationale="Erro 4xx em robots.txt normalmente não bloqueia rastreamento, mas um arquivo válido melhora clareza operacional.",
        )

    if issue.startswith("sitemap.status_code_not_200"):
        return IssueRecommendation(
            issue=issue,
            action="Corrigir a rota do sitemap ou publicar um sitemap XML válido acessível por HTTP 200.",
            rationale="Sitemap inacessível prejudica descoberta e validação de URLs importantes.",
        )

    if issue.startswith("sitemap.urls_with_query_found"):
        return IssueRecommendation(
            issue=issue,
            action="Remover URLs com parâmetros do sitemap ou substituir pela URL canônica limpa.",
            rationale="Sitemaps devem priorizar URLs canônicas, públicas e indexáveis.",
        )

    if issue.startswith("sitemap.duplicate_urls_found"):
        return IssueRecommendation(
            issue=issue,
            action="Deduplicar URLs no sitemap.",
            rationale="Reduz ruído operacional e melhora a confiabilidade do sitemap.",
        )

    if issue.startswith("sitemap.off_domain_urls_found"):
        return IssueRecommendation(
            issue=issue,
            action="Remover URLs fora do domínio esperado ou separar por sitemap apropriado.",
            rationale="Evita ambiguidade e inconsistência operacional no sitemap.",
        )

    if issue.startswith("sitemap.invalid_urls_found"):
        return IssueRecommendation(
            issue=issue,
            action="Corrigir URLs inválidas no sitemap.",
            rationale="URLs inválidas não são úteis para rastreamento nem indexação.",
        )

    return IssueRecommendation(
        issue=issue,
        action="Revisar manualmente a issue e definir ação corretiva.",
        rationale="Ainda não há recomendação específica cadastrada para essa issue.",
    )


def recommend_issues(issues: list[str]) -> list[IssueRecommendation]:
    sorted_issues = sorted(
        issues,
        key=lambda issue: _SEVERITY_ORDER[classify_issue(issue).severity],
    )
    return [recommend_issue(issue) for issue in sorted_issues]
