from geo_seo_engine.quality_gates import find_blocked_tracked_paths


def test_sensitive_and_generated_paths_are_blocked():
    paths = [
        ".env",
        ".env.local",
        "reports/raw/export.csv",
        "src/module/__pycache__/file.pyc",
        "search-console-export.json",
        "gsc-data.csv",
        "content-brief-example.json",
        "cluster-output.json",
        "gitleaks-results.json",
        "zap-report.html",
        "terraform.tfstate",
        "geo_seo_engine.egg-info/PKG-INFO",
    ]

    assert find_blocked_tracked_paths(paths) == sorted(paths)


def test_safe_repository_files_are_allowed():
    paths = [
        ".env.example",
        "README.md",
        "examples/site-audit-example.md",
        "src/geo_seo_engine/cli.py",
        "tests/test_cli.py",
    ]

    assert find_blocked_tracked_paths(paths) == []
