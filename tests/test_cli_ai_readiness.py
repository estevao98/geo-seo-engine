import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app

runner = CliRunner()


def test_cli_ai_readiness_reads_local_json(tmp_path):
    input_path = tmp_path / "audits.json"
    input_path.write_text(
        json.dumps(
            {
                "main_content": {
                    "pages": [
                        {
                            "page_url": "https://example.com/a",
                            "title": "Example A",
                            "headings": [{"level": 1, "text": "Example A"}],
                            "word_count": 350,
                            "paragraph_count": 3,
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["ai-readiness", "--input", str(input_path), "--format", "json"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["summary"]["total_targets"] == 1
    assert data["findings"][0]["page_url"] == "https://example.com/a"
    assert "limitations" in data["findings"][0]


def test_cli_ai_readiness_writes_output_file(tmp_path):
    input_path = tmp_path / "audits.json"
    output_path = tmp_path / "readiness.json"
    input_path.write_text(json.dumps({"main_content": {"pages": []}}), encoding="utf-8")

    result = runner.invoke(
        app,
        ["ai-readiness", "--input", str(input_path), "--format", "json", "--output", str(output_path)],
    )

    assert result.exit_code == 0
    assert f"Output written to {output_path}" in result.stdout
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["summary"]["total_targets"] == 0


def test_cli_ai_readiness_rejects_non_object_json(tmp_path):
    input_path = tmp_path / "invalid.json"
    input_path.write_text("[]", encoding="utf-8")

    result = runner.invoke(app, ["ai-readiness", "--input", str(input_path), "--format", "json"])

    assert result.exit_code == 1
    assert "Input JSON must be an object" in result.stderr
