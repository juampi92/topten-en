#!/usr/bin/env python3
"""Shared utilities for card extraction, validation, and auditing."""

import json
import re
from dataclasses import dataclass
from pathlib import Path


green_re = re.compile(r"<green>.*?</green>", re.IGNORECASE)
red_re = re.compile(r"<red>.*?</red>", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    """Represents a single card-level audit finding."""

    file: str
    row: int
    col: int
    empty_top: bool
    empty_bottom: bool
    missing_green: bool
    missing_red: bool

    @property
    def has_issue(self) -> bool:
        return (
            self.empty_top
            or self.empty_bottom
            or self.missing_green
            or self.missing_red
        )


def audit_file(file_path: Path) -> tuple[int, list[Finding]]:
    """Audit a single JSON file and return (total_cards, findings)."""
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    findings: list[Finding] = []
    cards = data.get("cards", [])
    for card in cards:
        pos = card.get("position", {})
        row = pos.get("row", "?")
        col = pos.get("col", "?")

        top = card.get("prompt_top", "") or ""
        bottom = card.get("prompt_bottom", "") or ""

        empty_top = not top.strip()
        empty_bottom = not bottom.strip()

        combined = f"{top} {bottom}"
        missing_green = not green_re.search(combined)
        missing_red = not red_re.search(combined)

        finding = Finding(
            file=file_path.name,
            row=row,
            col=col,
            empty_top=empty_top,
            empty_bottom=empty_bottom,
            missing_green=missing_green,
            missing_red=missing_red,
        )
        if finding.has_issue:
            findings.append(finding)

    return len(cards), findings


def format_summary(total: int, findings: list[Finding]) -> str:
    """Return a human-readable audit summary."""
    empty_count = sum(1 for f in findings if f.empty_top or f.empty_bottom)
    missing_green_count = sum(1 for f in findings if f.missing_green)
    missing_red_count = sum(1 for f in findings if f.missing_red)

    lines = [
        f"",
        f"Audit — {total} cards analyzed",
        f"  Empty prompts : {empty_count}",
        f"  Missing green : {missing_green_count}",
        f"  Missing red   : {missing_red_count}",
    ]

    if not findings:
        lines.append("  → 100% clean")
    else:
        lines.append(f"  ⚠ {len(findings)} cards with issues")
        for f in findings:
            issues = []
            if f.empty_top:
                issues.append("empty_top")
            if f.empty_bottom:
                issues.append("empty_bottom")
            if f.missing_green:
                issues.append("no_green")
            if f.missing_red:
                issues.append("no_red")
            lines.append(f"    [{f.file}] row {f.row}, col {f.col}: {', '.join(issues)}")

    return "\n".join(lines)
