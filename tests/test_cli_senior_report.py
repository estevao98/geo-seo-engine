import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app

runner = CliRunner()


def test_cli_senior_report_reads_local_aggregate_json(tmp_path):
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
                            "url": "https://example.com/",
                            "next_action": "Fix the status code.",
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["senior-report", "--input", str(input_path), "--format", "json"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["executive_summary"]["total_findings"] == 1
    assert data["operational_action_queue"][0]["action"] == "Fix the status code."
    assert "content_quality" in data["executive_summary"]["missing_inputs"]


def test_cli_senior_report_writes_output_file(tmp_path):
    input_path = tmp_path / "audits.json"
    output_path = tmp_path / "senior.json"
    input_path.write_text(json.dumps({"technical": {"findings": []}}), encoding="utf-8")

    result = runner.invoke(
        app,
        ["senior-report", "--input", str(input_path), "--format", "json", "--output", str(output_path)],
    )

    assert result.exit_code == 0
    assert f"Output written to {output_path}" in result.stdout
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["report_type"] == "senior_executive_operational"
    assert data["executive_summary"]["available_inputs"] == ["technical"]


def test_cli_senior_report_rejects_non_object_json(tmp_path):
    input_path = tmp_path / "invalid.json"
    input_path.write_text("[]", encoding="utf-8")

    result = runner.invoke(app, ["senior-report", "--input", str(input_path), "--format", "json"])

    assert result.exit_code == 1
    assert "Input JSON must be an object" in result.stderr
