from __future__ import annotations

import json
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup


@dataclass
class JsonLdBlockResult:
    index: int
    valid: bool
    types: list[str]
    error: str | None


@dataclass
class StructuredDataAuditResult:
    json_ld_blocks: int
    valid_json_ld_blocks: int
    invalid_json_ld_blocks: int
    types: list[str]
    blocks: list[JsonLdBlockResult]
    issues: list[str]


def empty_structured_data_result() -> StructuredDataAuditResult:
    return StructuredDataAuditResult(
        json_ld_blocks=0,
        valid_json_ld_blocks=0,
        invalid_json_ld_blocks=0,
        types=[],
        blocks=[],
        issues=[],
    )


def _extract_types(value) -> list[str]:
    types: list[str] = []

    if isinstance(value, dict):
        item_type = value.get("@type")
        if isinstance(item_type, str):
            types.append(item_type)
        elif isinstance(item_type, list):
            types.extend(item for item in item_type if isinstance(item, str))

        for nested in value.values():
            types.extend(_extract_types(nested))

    if isinstance(value, list):
        for item in value:
            types.extend(_extract_types(item))

    return types


def _unique_preserving_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []

    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)

    return unique


def audit_structured_data_html(html: str) -> StructuredDataAuditResult:
    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all(
        "script",
        type=lambda value: bool(value)
        and str(value).lower().split(";", 1)[0].strip() == "application/ld+json",
    )

    if not scripts:
        return StructuredDataAuditResult(
            json_ld_blocks=0,
            valid_json_ld_blocks=0,
            invalid_json_ld_blocks=0,
            types=[],
            blocks=[],
            issues=["missing"],
        )

    blocks: list[JsonLdBlockResult] = []
    all_types: list[str] = []
    issues: list[str] = []

    for index, script in enumerate(scripts, start=1):
        raw_json = script.string if script.string is not None else script.get_text()

        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            blocks.append(
                JsonLdBlockResult(
                    index=index,
                    valid=False,
                    types=[],
                    error=str(exc),
                )
            )
            continue

        block_types = _unique_preserving_order(_extract_types(parsed))
        all_types.extend(block_types)
        blocks.append(
            JsonLdBlockResult(
                index=index,
                valid=True,
                types=block_types,
                error=None,
            )
        )

    if any(not block.valid for block in blocks):
        issues.append("invalid_json_ld")

    if any(block.valid and not block.types for block in blocks):
        issues.append("missing_type")

    return StructuredDataAuditResult(
        json_ld_blocks=len(blocks),
        valid_json_ld_blocks=sum(1 for block in blocks if block.valid),
        invalid_json_ld_blocks=sum(1 for block in blocks if not block.valid),
        types=_unique_preserving_order(all_types),
        blocks=blocks,
        issues=issues,
    )


def audit_structured_data(url: str, timeout: float = 15.0) -> StructuredDataAuditResult:
    try:
        response = httpx.get(
            url,
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": "geo-seo-engine/0.1.0 (+https://example.com)"},
        )
    except httpx.HTTPError as exc:
        return StructuredDataAuditResult(
            json_ld_blocks=0,
            valid_json_ld_blocks=0,
            invalid_json_ld_blocks=0,
            types=[],
            blocks=[],
            issues=[f"request_error: {exc}"],
        )

    return audit_structured_data_html(response.text)
