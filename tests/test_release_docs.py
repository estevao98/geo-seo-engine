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
