#!/usr/bin/env python3
# /// script
# dependencies = []
# ///

import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
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


def analyze_file(file_path: Path) -> list[Finding]:
    green_re = re.compile(r"<green>.*?</green>", re.IGNORECASE)
    red_re = re.compile(r"<red>.*?</red>", re.IGNORECASE)

    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    findings: list[Finding] = []
    for card in data.get("cards", []):
        pos = card.get("position", {})
        row = pos.get("row", "?")
        col = pos.get("col", "?")

        top = card.get("prompt_top", "") or ""
        bottom = card.get("prompt_bottom", "") or ""

        empty_top = not top.strip()
        empty_bottom = not bottom.strip()

        top_has_green = bool(green_re.search(top))
        bottom_has_green = bool(green_re.search(bottom))
        top_has_red = bool(red_re.search(top))
        bottom_has_red = bool(red_re.search(bottom))
        missing_green = not (top_has_green and bottom_has_green)
        missing_red = not (top_has_red and bottom_has_red)

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

    return findings


def main() -> None:
    target_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/original/game_cards_data")
    target_dir = target_dir.resolve()

    if not target_dir.is_dir():
        print(f"Target directory not found: {target_dir}", file=sys.stderr)
        sys.exit(1)

    json_files = sorted(target_dir.glob("*.json"))
    if not json_files:
        print(f"No .json files found in {target_dir}")
        sys.exit(0)

    all_findings: list[Finding] = []
    total_cards = 0

    for file_path in json_files:
        findings = analyze_file(file_path)
        all_findings.extend(findings)
        # Count total cards by re-reading (cheap for this data size)
        with file_path.open("r", encoding="utf-8") as f:
            total_cards += len(json.load(f).get("cards", []))

    print(f"Analyzed {len(json_files)} files, {total_cards} total cards.\n")

    if not all_findings:
        print("No issues found.")
        sys.exit(0)

    empty_count = sum(1 for f in all_findings if f.empty_top or f.empty_bottom)
    missing_green_count = sum(1 for f in all_findings if f.missing_green)
    missing_red_count = sum(1 for f in all_findings if f.missing_red)

    print("Summary")
    print("=" * 50)
    print(f"  Empty prompt (top or bottom): {empty_count}")
    print(f"  Missing <green>...</green>:     {missing_green_count}")
    print(f"  Missing <red>...</red>:       {missing_red_count}")
    print(f"  Cards with any issue:       {len(all_findings)}")
    print()

    print(f"{'File':<12} {'Row':>3} {'Col':>3} {'EmptyTop':>8} {'EmptyBot':>8} {'NoGreen':>7} {'NoRed':>5}")
    print("-" * 50)
    for f in all_findings:
        print(
            f"{f.file:<12} {f.row:>3} {f.col:>3} "
            f"{'YES' if f.empty_top else '':>8} "
            f"{'YES' if f.empty_bottom else '':>8} "
            f"{'YES' if f.missing_green else '':>7} "
            f"{'YES' if f.missing_red else '':>5}"
        )

    sys.exit(1 if all_findings else 0)


if __name__ == "__main__":
    main()
