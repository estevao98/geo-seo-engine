import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app

runner = CliRunner()


def test_cli_opportunity_reads_local_aggregate_json(tmp_path):
    input_path = tmp_path / "audits.json"
    input_path.write_text(
        json.dumps(
            {
                "technical": {
                    "findings": [
                        {
                            "id": "technical.status_not_200",
                            "title": "Status is not 200",
                            "severity": "high",
                            "category": "crawlability",
                            "url": "https://example.com/",
                            "next_action": "Fix the status code.",
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["opportunity", "--input", str(input_path), "--format", "json"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["summary"]["total_opportunities"] == 1
    assert data["opportunities"][0]["finding_id"] == "technical.status_not_200"
    assert data["buckets_by_page"][0]["key"] == "https://example.com/"


def test_cli_opportunity_writes_output_file(tmp_path):
    input_path = tmp_path / "audits.json"
    output_path = tmp_path / "opportunities.json"
    input_path.write_text(json.dumps({"technical": {"findings": []}}), encoding="utf-8")

    result = runner.invoke(
        app,
        ["opportunity", "--input", str(input_path), "--format", "json", "--output", str(output_path)],
    )

    assert result.exit_code == 0
    assert f"Output written to {output_path}" in result.stdout
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["summary"]["total_opportunities"] == 0
    assert data["summary"]["inputs_present"] == ["technical"]


def test_cli_opportunity_rejects_non_object_json(tmp_path):
    input_path = tmp_path / "invalid.json"
    input_path.write_text("[]", encoding="utf-8")

    result = runner.invoke(app, ["opportunity", "--input", str(input_path), "--format", "json"])

    assert result.exit_code == 1
    assert "Input JSON must be an object" in result.stderr
