import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app

runner = CliRunner()


def test_cli_content_brief_reads_local_json(tmp_path):
    input_path = tmp_path / "audits.json"
    input_path.write_text(
        json.dumps(
            {
                "content_quality": {
                    "findings": [
                        {
                            "id": "content.thin",
                            "title": "Thin content",
                            "severity": "medium",
                            "category": "content",
                            "page_url": "https://example.com/a",
                            "next_action": "Expand useful details.",
                            "evidence": [{"source": "content_quality", "observed": 100, "expected": 300}],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["content-brief", "--input", str(input_path), "--format", "json"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["summary"]["total_briefs"] == 1
    assert data["briefs"][0]["source_finding_ids"] == ["content.thin"]
    assert data["briefs"][0]["evidence"][0]["source"] == "content_quality"


def test_cli_content_brief_writes_output_file(tmp_path):
    input_path = tmp_path / "audits.json"
    output_path = tmp_path / "content-brief.json"
    input_path.write_text(json.dumps({"main_content": {"pages": []}}), encoding="utf-8")

    result = runner.invoke(
        app,
        ["content-brief", "--input", str(input_path), "--format", "json", "--output", str(output_path)],
    )

    assert result.exit_code == 0
    assert f"Output written to {output_path}" in result.stdout
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["summary"]["total_briefs"] == 0


def test_cli_content_brief_rejects_non_object_json(tmp_path):
    input_path = tmp_path / "invalid.json"
    input_path.write_text("[]", encoding="utf-8")

    result = runner.invoke(app, ["content-brief", "--input", str(input_path), "--format", "json"])

    assert result.exit_code == 1
    assert "Input JSON must be an object" in result.stderr
