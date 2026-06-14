import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app

runner = CliRunner()


def test_cli_audit_performance_imports_local_json_without_network(tmp_path, monkeypatch):
    import geo_seo_engine.cli as cli

    original_run_performance_audit = cli.run_performance_audit

    def fake_run_performance_audit(pages, options=None, start_url=None):
        assert options is None
        assert start_url == "https://example.com/override"
        assert pages[0].page_url == "https://example.com/override"
        return original_run_performance_audit(pages, options=options, start_url=start_url)

    monkeypatch.setattr(cli, "run_performance_audit", fake_run_performance_audit)
    input_path = tmp_path / "pagespeed.json"
    input_path.write_text(
        json.dumps(
            {
                "lighthouseResult": {
                    "finalUrl": "https://example.com/",
                    "categories": {"performance": {"score": 0.49}},
                    "audits": {
                        "largest-contentful-paint": {
                            "title": "Largest Contentful Paint",
                            "numericValue": 4200,
                            "displayValue": "4.2 s",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "audit-performance",
            "--input",
            str(input_path),
            "--page-url",
            "https://example.com/override",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["start_url"] == "https://example.com/override"
    assert data["pages"][0]["performance_score"] == 49
    assert "performance.low_score" in [finding["id"] for finding in data["findings"]]
    assert "performance.lcp_slow" in [finding["id"] for finding in data["findings"]]


def test_cli_audit_performance_writes_output_file(tmp_path):
    input_path = tmp_path / "pagespeed.json"
    output_path = tmp_path / "result.json"
    input_path.write_text(json.dumps({"lighthouseResult": {"finalUrl": "https://example.com/"}}), encoding="utf-8")

    result = runner.invoke(
        app,
        ["audit-performance", "--input", str(input_path), "--format", "json", "--output", str(output_path)],
    )

    assert result.exit_code == 0
    assert f"Output written to {output_path}" in result.stdout
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["pages"][0]["page_url"] == "https://example.com/"


def test_cli_audit_performance_rejects_invalid_json(tmp_path):
    input_path = tmp_path / "invalid.json"
    input_path.write_text("[]", encoding="utf-8")

    result = runner.invoke(app, ["audit-performance", "--input", str(input_path), "--format", "json"])

    assert result.exit_code == 1
    assert "Input JSON must be an object" in result.stderr
