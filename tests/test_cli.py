import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app

runner = CliRunner()


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


def test_audit_page_json_output(monkeypatch):
    from geo_seo_engine.analyzers.page_audit import PageAuditResult
    import geo_seo_engine.cli as cli

    def fake_audit_page(url: str):
        return PageAuditResult(
            url=url,
            final_url=url,
            status_code=200,
            title="Example Title",
            meta_description=None,
            h1=["Main Heading"],
            canonical=None,
            meta_robots=None,
            noindex=False,
            internal_links=1,
            external_links=2,
            issues=["missing_canonical"],
        )

    monkeypatch.setattr(cli, "run_page_audit", fake_audit_page)

    result = runner.invoke(
        app,
        ["audit-page", "https://example.com", "--format", "json"],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["url"] == "https://example.com"
    assert data["status_code"] == 200
    assert data["title"] == "Example Title"
    assert data["h1"] == ["Main Heading"]
    assert data["issues"] == ["missing_canonical"]


def test_audit_page_json_output_file(monkeypatch, tmp_path):
    from geo_seo_engine.analyzers.page_audit import PageAuditResult
    import geo_seo_engine.cli as cli

    def fake_audit_page(url: str):
        return PageAuditResult(
            url=url,
            final_url=url,
            status_code=200,
            title="Example Title",
            meta_description="Description",
            h1=["Main Heading"],
            canonical="https://example.com",
            meta_robots=None,
            noindex=False,
            internal_links=1,
            external_links=2,
            issues=[],
        )

    monkeypatch.setattr(cli, "run_page_audit", fake_audit_page)

    output = tmp_path / "reports" / "audit.json"

    result = runner.invoke(
        app,
        [
            "audit-page",
            "https://example.com",
            "--format",
            "json",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert output.exists()

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["title"] == "Example Title"
    assert data["canonical"] == "https://example.com"
    assert data["issues"] == []
