from typer.testing import CliRunner

from geo_seo_engine.cli import app


runner = CliRunner()


def test_config_validate_accepts_valid_config(tmp_path):
    config_path = tmp_path / "geo-seo.yml"
    config_path.write_text(
        "project_name: CLI\nbase_url: https://example.com\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["config", "validate", "--config", str(config_path)])

    assert result.exit_code == 0
    assert "Config valid: CLI" in result.stdout


def test_init_creates_config_in_temporary_directory(tmp_path):
    config_path = tmp_path / "geo-seo.yml"

    result = runner.invoke(app, ["init", "--config", str(config_path)])

    assert result.exit_code == 0
    assert config_path.exists()
    content = config_path.read_text(encoding="utf-8")
    assert "project_name: Example Project" in content
    assert "API keys" in content
    assert "token:" not in content.lower()


def test_init_does_not_overwrite_without_force(tmp_path):
    config_path = tmp_path / "geo-seo.yml"
    config_path.write_text("project_name: Existing\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--config", str(config_path)])

    assert result.exit_code == 1
    assert "already exists" in result.stderr
    assert config_path.read_text(encoding="utf-8") == "project_name: Existing\n"


def test_init_overwrites_with_force(tmp_path):
    config_path = tmp_path / "geo-seo.yml"
    config_path.write_text("project_name: Existing\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--config", str(config_path), "--force"])

    assert result.exit_code == 0
    assert "project_name: Example Project" in config_path.read_text(encoding="utf-8")
