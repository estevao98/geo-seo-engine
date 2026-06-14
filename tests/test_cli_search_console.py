import json

from typer.testing import CliRunner

from geo_seo_engine.cli import app

runner = CliRunner()


def test_cli_search_console_analytics_outputs_json_from_local_input(tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text(
        json.dumps(
            [
                {
                    "query": "geo seo",
                    "page": "https://example.com/page",
                    "date": "2026-01-15",
                    "country": "BR",
                    "device": "mobile",
                    "clicks": 5,
                    "impressions": 25,
                    "ctr": 0.2,
                    "position": 2.5,
                }
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["search-console-analytics", "--input", str(input_path), "--format", "json"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["aggregate"]["clicks"] == 5
    assert data["rows"][0]["normalized_page"] == "https://example.com/page"
    assert data["groups"]["by_query"][0]["key"] == "geo seo"


def test_cli_search_console_analytics_writes_output_file(tmp_path):
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "result.json"
    input_path.write_text(
        "query,page,date,country,device,clicks,impressions,ctr,position\n"
        "geo seo,https://example.com/page,2026-01-15,BR,mobile,5,25,0.2,2.5\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["search-console-analytics", "--input", str(input_path), "--format", "json", "--output", str(output_path)],
    )

    assert result.exit_code == 0
    assert f"Output written to {output_path}" in result.stdout
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["aggregate"]["impressions"] == 25


def test_cli_search_console_analytics_rejects_unsupported_input(tmp_path):
    input_path = tmp_path / "input.txt"
    input_path.write_text("not supported", encoding="utf-8")

    result = runner.invoke(app, ["search-console-analytics", "--input", str(input_path), "--format", "json"])

    assert result.exit_code == 1
    assert "must be a .json or .csv file" in result.stderr
