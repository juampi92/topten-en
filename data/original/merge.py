#!/usr/bin/env python3
"""Merge paired JSON card files into a unified cards.json."""

import argparse
import json
import os
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge {number}_A.json and {number}_B.json card files."
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing _A.json and _B.json files.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for the merged cards.json.",
    )
    return parser.parse_args()


def discover_groups(input_dir: Path) -> dict[int, dict[str, Path]]:
    """Discover _A.json and _B.json files and group by numeric prefix."""
    groups: dict[int, dict[str, Path]] = {}
    pattern = re.compile(r"^(\d+)_(A|B)\.json$")

    for entry in input_dir.iterdir():
        if not entry.is_file():
            continue
        match = pattern.match(entry.name)
        if not match:
            continue
        number = int(match.group(1))
        suffix = match.group(2)
        groups.setdefault(number, {})[suffix] = entry

    return groups


def load_cards(path: Path | None) -> dict[tuple[int, int], dict]:
    """Load cards from a JSON file into a position map."""
    if path is None or not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    cards = data.get("cards", [])
    return {
        (card["position"]["row"], card["position"]["col"]): card
        for card in cards
    }


def collect_prompts(a_card: dict | None, b_card: dict | None) -> list[str]:
    """Collect non-empty prompts in fixed order: A top, A bottom, B top, B bottom."""
    prompts: list[str] = []
    for card in (a_card, b_card):
        if card is not None:
            for key in ("prompt_top", "prompt_bottom"):
                value = card.get(key, "")
                if isinstance(value, str):
                    stripped = value.strip()
                    if stripped:
                        prompts.append(stripped)
    return prompts


def merge_group(a_path: Path | None, b_path: Path | None) -> list[list[str]]:
    """Merge cards from A and B files into a list of prompt lists."""
    a_map = load_cards(a_path)
    b_map = load_cards(b_path)

    all_positions = set(a_map.keys()) | set(b_map.keys())

    # Sort by row then col for deterministic ordering
    sorted_positions = sorted(all_positions, key=lambda p: (p[0], p[1]))

    result: list[list[str]] = []
    for pos in sorted_positions:
        prompts = collect_prompts(a_map.get(pos), b_map.get(pos))
        result.append(prompts)

    return result


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_path = Path(args.output)

    if not input_dir.is_dir():
        raise SystemExit(f"Input directory does not exist: {input_dir}")

    groups = discover_groups(input_dir)

    if not groups:
        raise SystemExit(f"No matching _A.json or _B.json files found in {input_dir}")

    all_cards: list[dict] = []
    card_id = 1

    for number in sorted(groups.keys()):
        group = groups[number]
        a_path = group.get("A")
        b_path = group.get("B")
        prompt_lists = merge_group(a_path, b_path)
        for prompts in prompt_lists:
            all_cards.append({"id": card_id, "prompts": prompts})
            card_id += 1

    output = {"cards": all_cards}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Wrote {len(all_cards)} cards to {output_path}")


if __name__ == "__main__":
    main()
