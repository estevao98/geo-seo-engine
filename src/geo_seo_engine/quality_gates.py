from __future__ import annotations

import fnmatch
import subprocess
import sys
from collections.abc import Iterable


BLOCKED_PATH_PATTERNS = (
    "__pycache__",
    "*.pyc",
    ".env",
    ".env.*",
    "reports/raw",
    "site-audit-example.json",
    "robots-audit-example.json",
    "sitemap-audit-google.json",
    "page-audit-example.json",
    "search-console*.json",
    "search-console*.csv",
    "gsc*.json",
    "gsc*.csv",
    "opportunity*.json",
    "content-brief*.json",
    "brief*.json",
    "cluster*.json",
    "content-cluster*.json",
    "ai-readiness*.json",
    "readiness*.json",
    "senior-report*.json",
    "executive-report*.json",
    "operational-report*.json",
    "report-output*.json",
    "gitleaks*.json",
    "detect-secrets*.json",
    "semgrep*.json",
    "bandit*.json",
    "pip-audit*.json",
    "zap-report*",
    "trivy*.json",
    "grype*.json",
    "terraform.tfstate",
    "site_config.json",
    "*.egg-info",
)

ALLOWED_PATHS = {".env.example"}


def find_blocked_tracked_paths(paths: Iterable[str]) -> list[str]:
    blocked: set[str] = set()

    for raw_path in paths:
        path = raw_path.strip().replace("\\", "/")
        if not path or path in ALLOWED_PATHS:
            continue

        parts = path.split("/")
        name = parts[-1]

        if "__pycache__" in parts:
            blocked.add(path)
            continue

        if any(part.endswith(".egg-info") for part in parts):
            blocked.add(path)
            continue

        if path == "reports/raw" or path.startswith("reports/raw/"):
            blocked.add(path)
            continue

        for pattern in BLOCKED_PATH_PATTERNS:
            if pattern in {"__pycache__", "reports/raw", "*.egg-info"}:
                continue
            if fnmatch.fnmatchcase(name, pattern):
                blocked.add(path)
                break

    return sorted(blocked)


def _tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()


def main() -> int:
    blocked_paths = find_blocked_tracked_paths(_tracked_paths())
    if not blocked_paths:
        print("Generated/sensitive-file guard passed: no blocked tracked files found.")
        return 0

    print("Generated/sensitive-file guard failed. Remove these tracked files:", file=sys.stderr)
    for path in blocked_paths:
        print(f"- {path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
