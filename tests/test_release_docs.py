from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_docs_cover_current_cli_commands_and_gates() -> None:
    usage = (ROOT / "docs/senior-engine/usage.md").read_text(encoding="utf-8")
    release = (ROOT / "docs/senior-engine/release-process.md").read_text(encoding="utf-8")
    maintenance = (ROOT / "docs/senior-engine/maintenance.md").read_text(encoding="utf-8")

    expected_commands = [
        "geo version",
        "geo init",
        "geo config validate",
        "geo audit-page",
        "geo audit-robots",
        "geo audit-sitemap",
        "geo audit-site",
        "geo crawl",
        "geo inventory",
        "geo audit-technical",
        "geo extract-content",
        "geo audit-content-quality",
        "geo audit-entity-readiness",
        "geo audit-internal-links",
        "geo audit-images",
        "geo audit-social",
        "geo audit-hreflang",
        "geo audit-rendering",
        "geo audit-performance",
        "geo search-console-analytics",
        "geo opportunity",
        "geo content-brief",
        "geo content-cluster",
        "geo ai-readiness",
        "geo senior-report",
    ]

    for command in expected_commands:
        assert command in usage

    expected_gates = [
        "git status --short",
        "git diff --stat",
        "git diff --check",
        "python -m geo_seo_engine.quality_gates",
        "python -m pytest",
    ]

    for gate in expected_gates:
        assert gate in release

    assert "Python 3.13" in release
    assert "Generated and sensitive file guard" in release
    assert "quality_gates" in maintenance
    assert "nao promet" in usage.lower()


def test_readme_showcases_senior_engine_without_unsupported_claims() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    expected_sections = [
        "## What It Solves",
        "## Feature Overview",
        "## Quickstart",
        "## Example Workflow",
        "## Module Map",
        "## Why Deterministic And Local-First",
        "## Safety And Data Policy",
        "## Documentation",
        "## Status And Release Readiness",
        "## Non-Promises And Limitations",
    ]

    for section in expected_sections:
        assert section in readme

    expected_links = [
        "docs/senior-engine/usage.md",
        "docs/senior-engine/release-process.md",
        "docs/senior-engine/maintenance.md",
        "SECURITY.md",
    ]

    for link in expected_links:
        assert link in readme

    safe_commands = [
        'python -m pip install -e ".[dev]"',
        "geo version",
        "geo init",
        "geo config validate --config geo-seo.yml",
        "git diff --check",
        "python -m geo_seo_engine.quality_gates",
        "python -m pytest",
    ]

    for command in safe_commands:
        assert command in readme

    assert "/tmp/" in readme
    assert "Does not promise traffic growth" in readme
    assert "Does not create or recommend black hat SEO" in readme
