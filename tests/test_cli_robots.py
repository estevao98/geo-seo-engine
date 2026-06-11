import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app

runner = CliRunner()


def test_audit_robots_json_output(monkeypatch):
    from geo_seo_engine.analyzers.robots_audit import RobotsAuditResult
    import geo_seo_engine.cli as cli

    def fake_audit_robots(url: str):
        return RobotsAuditResult(
            url="https://example.com/robots.txt",
            final_url="https://example.com/robots.txt",
            status_code=200,
            content_type="text/plain",
            line_count=3,
            user_agents=["*"],
            allow_count=0,
            disallow_count=1,
            sitemap_urls=["https://example.com/sitemap.xml"],
            crawl_delay_count=0,
            unknown_directives=[],
            blocks_all=False,
            issues=[],
        )

    monkeypatch.setattr(cli, "run_robots_audit", fake_audit_robots)

    result = runner.invoke(
        app,
        ["audit-robots", "https://example.com", "--format", "json"],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["url"] == "https://example.com/robots.txt"
    assert data["user_agents"] == ["*"]
    assert data["sitemap_urls"] == ["https://example.com/sitemap.xml"]


def test_audit_robots_table_output_is_not_duplicated(monkeypatch):
    from geo_seo_engine.analyzers.robots_audit import RobotsAuditResult
    import geo_seo_engine.cli as cli

    def fake_audit_robots(url: str):
        return RobotsAuditResult(
            url="https://example.com/robots.txt",
            final_url="https://example.com/robots.txt",
            status_code=200,
            content_type="text/plain",
            line_count=3,
            user_agents=["*"],
            allow_count=0,
            disallow_count=1,
            sitemap_urls=[],
            crawl_delay_count=0,
            unknown_directives=[],
            blocks_all=False,
            issues=["missing_sitemap_directive"],
        )

    monkeypatch.setattr(cli, "run_robots_audit", fake_audit_robots)

    result = runner.invoke(app, ["audit-robots", "https://example.com"])

    assert result.exit_code == 0
    assert result.stdout.count("Robots Audit") == 1


def test_audit_robots_rejects_markdown_format():
    result = runner.invoke(
        app,
        ["audit-robots", "https://example.com/robots.txt", "--format", "markdown"],
    )

    assert result.exit_code != 0
