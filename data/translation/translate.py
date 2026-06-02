# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-genai",
#     "python-dotenv",
#     "rich",
# ]
# ///

"""Translate TopTen cards from Spanish to English using the Gemini API.

Usage:
    uv run data/translation/translate.py \
        --es data/cards_es.json \
        --en data/cards_en.json \
        --chunk 5
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import termios
import tty
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

MODEL_NAME = "gemini-3.1-flash-lite"

SYSTEM_PROMPT = """\
You are translating cards for a Spanish party board game called "TopTen".

Game context: A card presents a prompt to a group of players. Each player secretly \
receives a number from 1 to 10. Player "1" must answer on the extreme marked with \
<green>...</green> (the "green" end of the spectrum), and player "10" must answer on \
the extreme marked with <red>...</red> (the "red" end of the spectrum). Players in \
between answer proportionally. The fun comes from people debating who has which number \
and defending their answers.

Translation rules:
1. Preserve the <green>...</green> and <red>...</red> tags EXACTLY (same names, same \
positions, lowercase tag names). They must wrap the words/phrases that occupy the same \
"slot" in the English sentence as they did in the Spanish sentence. IMPORTANT: if a translation \
is missing this detail, we will REJECT it, so it is incredibly important you don't miss this.
2. The word "CAPITEN" (sometimes written as <u>CAPITEN</u>) refers to a recurring mascot \
character of the game. It MUST remain exactly as "CAPITEN" in English. Preserve any \
<u>...</u> underline tags around it as well.
3. Keep the tone playful, punchy, and a bit absurd — matching the original Spanish. \
Translating literally is fine when it works; when it doesn't, prefer a natural English \
phrase that preserves the joke.
4. Preserve the ALL-CAPS shouting style of the original prompts. Keep punctuation, \
em-dashes, quotes, and exclamation/question marks as they appear.
5. For each translated prompt, set "is_cultural" to true if the original prompt relies \
heavily on Spanish (or Latin American) culture, slang, wordplay, public figures, brands, \
TV shows, etc. that would not land for an English-speaking audience. In that case, fill \
"cultural_explanation" with a short, concrete note about WHY it doesn't translate well \
(e.g. "References the TV show 'Cuéntame cómo pasó', unknown to most English speakers"). \
If it translates fine, set "is_cultural" to false and omit "cultural_explanation". \
6. Some cards have the characters `«` and `»`. Feel free to use them.

You will receive a JSON array of cards, each with an "id" and a "prompts" array of 4 \
strings. Return a JSON object with a "cards" array in the SAME order, where each card \
has the same "id" and a "prompts" array of 4 objects, each with:
  - "text": the English translation as a string
  - "is_cultural": boolean
  - "cultural_explanation": string (only if is_cultural is true)
"""

RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "cards": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "number"},
                    "prompts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {
                                    "type": "string",
                                    "description": "The translated prompt",
                                },
                                "is_cultural": {
                                    "type": "boolean",
                                    "description": "True if the original prompt relies heavily on Spanish culture, wordplay, etc.",
                                },
                                "cultural_explanation": {
                                    "type": "string",
                                    "description": "Explanation if is_cultural is true",
                                },
                            },
                            "required": ["text", "is_cultural"],
                        },
                    },
                },
                "required": ["id", "prompts"],
            },
        }
    },
    "required": ["cards"],
}


# --------------------------------------------------------------------------- #
# JSON I/O
# --------------------------------------------------------------------------- #

def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


# --------------------------------------------------------------------------- #
# Resume logic
# --------------------------------------------------------------------------- #

def find_start_index(cards_es: list[dict[str, Any]], en: dict[str, Any]) -> int:
    """Return the index in `cards_es` of the first card NOT yet translated."""
    translated_ids = {c["id"] for c in en.get("cards", [])}
    for i, card in enumerate(cards_es):
        if card["id"] not in translated_ids:
            return i
    return len(cards_es)


# --------------------------------------------------------------------------- #
# Rich rendering helpers
# --------------------------------------------------------------------------- #

_TAG_RE = re.compile(r"(<green>.*?</green>|<red>.*?</red>|<u>.*?</u>)", re.DOTALL)
_GREEN_RE = re.compile(r"<green>.*?</green>", re.IGNORECASE)
_RED_RE = re.compile(r"<red>.*?</red>", re.IGNORECASE)


def styled_text(en_text: str) -> Text:
    """Build a rich Text where <green>/<red>/<u> tags are styled in colour."""
    text = Text()
    pos = 0
    for m in _TAG_RE.finditer(en_text):
        if m.start() > pos:
            text.append(en_text[pos:m.start()])
        token = m.group(0)
        if token.startswith("<green>"):
            text.append(token[len("<green>"):-len("</green>")], style="bold green")
        elif token.startswith("<red>"):
            text.append(token[len("<red>"):-len("</red>")], style="bold red")
        elif token.startswith("<u>"):
            text.append(token[len("<u>"):-len("</u>")], style="underline")
        pos = m.end()
    if pos < len(en_text):
        text.append(en_text[pos:])
    return text


def validate_prompt(text: str) -> list[str]:
    """Return audit-style issue labels for an EN prompt (empty / missing tags)."""
    issues: list[str] = []
    if not text or not text.strip():
        issues.append("empty")
    else:
        if not _GREEN_RE.search(text):
            issues.append("missing_green")
        if not _RED_RE.search(text):
            issues.append("missing_red")
    return issues


def missing_tags_vs_source(es_text: str, en_text: str) -> list[str]:
    """Return labels for tags present in ES but missing in EN."""
    issues: list[str] = []
    if _GREEN_RE.search(es_text) and not _GREEN_RE.search(en_text):
        issues.append("green_missing_in_en")
    if _RED_RE.search(es_text) and not _RED_RE.search(en_text):
        issues.append("red_missing_in_en")
    return issues


def render_chunk(
    console: Console,
    es_chunk: list[dict[str, Any]],
    en_chunk: list[dict[str, Any]],
) -> None:
    """Render ES + proposed EN for each card in the chunk, with cultural warnings."""
    for es_card, en_card in zip(es_chunk, en_chunk):
        console.rule(f"[bold cyan]Card #{es_card['id']}[/bold cyan]")
        for i, (es_prompt, en_prompt_obj) in enumerate(
            zip(es_card["prompts"], en_card["prompts"]), start=1
        ):
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column(width=5, style="bold yellow")
            table.add_column(width=4, style="bold")
            table.add_column(ratio=1)
            table.add_row(str(i), "[yellow]ES[/yellow]", styled_text(es_prompt))
            table.add_row("", "[green]EN[/green]", styled_text(en_prompt_obj["text"]))
            console.print(table)

            audit_messages: list[str] = []
            for issue in validate_prompt(en_prompt_obj["text"]):
                if issue == "empty":
                    audit_messages.append("Empty prompt — nothing was translated.")
                elif issue == "missing_green":
                    audit_messages.append("Missing <green>...</green> tag.")
                elif issue == "missing_red":
                    audit_messages.append("Missing <red>...</red> tag.")
            for issue in missing_tags_vs_source(es_prompt, en_prompt_obj["text"]):
                if issue == "green_missing_in_en":
                    audit_messages.append(
                        "ES source has a <green> tag that the EN translation lost."
                    )
                elif issue == "red_missing_in_en":
                    audit_messages.append(
                        "ES source has a <red> tag that the EN translation lost."
                    )
            if audit_messages:
                body = (
                    f"[bold]Audit issues — prompt {i}[/bold]\n\n"
                    + "\n".join(f"• {m}" for m in audit_messages)
                )
                console.print(
                    Panel(
                        body,
                        border_style="red",
                        title="🚨 AUDIT ISSUE",
                        title_align="left",
                    )
                )

            if en_prompt_obj.get("is_cultural"):
                explanation = en_prompt_obj.get("cultural_explanation", "").strip()
                body = (
                    f"[bold]Cultural flag — prompt {i}[/bold]\n\n"
                    f"{explanation or '(no explanation provided)'}"
                )
                console.print(
                    Panel(
                        body,
                        border_style="yellow",
                        title="⚠️ CULTURAL FLAG",
                        title_align="left",
                    )
                )
        console.print()


# --------------------------------------------------------------------------- #
# Gemini call
# --------------------------------------------------------------------------- #

def translate_chunk(
    client: genai.Client,
    es_chunk: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Send a chunk of ES cards to Gemini and return the EN cards (with metadata)."""
    user_payload = {
        "cards": [
            {"id": c["id"], "prompts": c["prompts"]} for c in es_chunk
        ]
    }
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=json.dumps(user_payload, ensure_ascii=False),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
            temperature=0.4,
        ),
    )
    parsed = json.loads(response.text)
    return parsed["cards"]


# --------------------------------------------------------------------------- #
# Edit flow
# --------------------------------------------------------------------------- #

def edit_chunk_in_editor(
    es_chunk: list[dict[str, Any]],
    en_chunk: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Open the chunk in $EDITOR (default nano) and return the edited result."""
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "nano"
    payload = {
        "es_cards": [
            {"id": c["id"], "prompts": c["prompts"]} for c in es_chunk
        ],
        "en_cards": en_chunk,
    }
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        prefix="topten-edit-",
        delete=False,
        encoding="utf-8",
    ) as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        tmp_path = f.name

    try:
        subprocess.run([editor, tmp_path], check=False)
        with open(tmp_path, "r", encoding="utf-8") as f:
            edited = json.load(f)
        return edited["en_cards"]
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# --------------------------------------------------------------------------- #
# Strip metadata to match the original JSON shape
# --------------------------------------------------------------------------- #

def strip_metadata(en_chunk: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only the prompt `text` strings, matching cards_es.json structure."""
    cleaned: list[dict[str, Any]] = []
    for card in en_chunk:
        cleaned.append(
            {
                "id": card["id"],
                "prompts": [p["text"] for p in card["prompts"]],
            }
        )
    return cleaned


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--es", required=True, type=Path, help="Source ES cards JSON")
    p.add_argument("--en", required=True, type=Path, help="Target EN cards JSON")
    p.add_argument(
        "--chunk",
        type=int,
        default=5,
        help="Number of cards per API call (default: 5)",
    )
    return p.parse_args()


ACTION_OPTIONS: list[tuple[str, str]] = [
    ("A", "Accept chunk"),
    ("E", "Edit chunk"),
    ("S", "Save & Exit"),
    ("X", "Exit without saving"),
]


def _make_action_menu(selected: int) -> Group:
    header = Text("Choose an action  ", style="bold")
    header.append("(↑/↓ to move, Enter to confirm, or press A / E / S / X)",
                  style="dim")
    rows: list[Text] = []
    for i, (key, label) in enumerate(ACTION_OPTIONS):
        if i == selected:
            rows.append(
                Text(f"  ▶  {key}  {label}",
                     style="bold black on cyan")
            )
        else:
            rows.append(Text(f"     {key}  {label}"))
    return Group(header, *rows)


def _read_arrow_key(fd: int) -> str | None:
    """Read one key from cbreak stdin. Return an action key or None."""
    ch = os.read(fd, 1)
    if ch == b"\x03":  # Ctrl-C
        raise KeyboardInterrupt
    if ch in (b"\r", b"\n"):
        return "__ENTER__"
    if ch == b"\x1b":
        # Escape sequence: ESC [ A/B/C/D
        n1 = os.read(fd, 1)
        if n1 != b"[":
            return None
        n2 = os.read(fd, 1)
        if n2 == b"A":
            return "__UP__"
        if n2 == b"B":
            return "__DOWN__"
        return None
    if ch.upper() in (b"A", b"E", b"S", b"X"):
        return ch.upper().decode()
    return None


def prompt_action(console: Console) -> str:
    """Arrow-key selector. Renders in place under the chunk and returns 'A'/'E'/'S'/'X'."""
    selected = 0
    fd = sys.stdin.fileno()
    old_attrs = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        with Live(_make_action_menu(selected), console=console, screen=False,
                  refresh_per_second=30) as live:
            while True:
                key = _read_arrow_key(fd)
                if key == "__UP__":
                    selected = (selected - 1) % len(ACTION_OPTIONS)
                    live.update(_make_action_menu(selected))
                elif key == "__DOWN__":
                    selected = (selected + 1) % len(ACTION_OPTIONS)
                    live.update(_make_action_menu(selected))
                elif key == "__ENTER__":
                    return ACTION_OPTIONS[selected][0]
                elif key in ("A", "E", "S", "X"):
                    return key
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_attrs)


def main() -> int:
    load_dotenv()
    args = parse_args()

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_TOKEN")
    if not api_key:
        print("Error: GEMINI_API_KEY (or GEMINI_TOKEN) is not set in the environment.",
              file=sys.stderr)
        return 1

    client = genai.Client(api_key=api_key)
    console = Console()

    es_data = load_json(args.es)
    cards_es: list[dict[str, Any]] = es_data["cards"]

    if args.en.exists():
        en_data = load_json(args.en)
    else:
        en_data = {"cards": []}

    start_idx = find_start_index(cards_es, en_data)
    total = len(cards_es)
    already = len(en_data.get("cards", []))
    console.print(
        f"[bold]Loaded[/bold] {total} ES cards · [green]{already}[/green] already "
        f"translated · starting at index {start_idx} (id {cards_es[start_idx]['id'] if start_idx < total else '—'})"
    )

    if start_idx >= total:
        console.print("[green]Nothing to translate — target file is up to date.[/green]")
        return 0

    i = start_idx
    while i < total:
        es_chunk = cards_es[i : i + args.chunk]
        console.rule(
            f"[bold]Translating cards {es_chunk[0]['id']}–{es_chunk[-1]['id']}[/bold]"
        )

        try:
            en_chunk = translate_chunk(client, es_chunk)
        except Exception as exc:
            console.print(f"[red]API call failed:[/red] {exc}")
            retry = Prompt.ask(
                "[bold]Retry this chunk?[/bold]",
                choices=["Y", "N"],
                default="Y",
                show_choices=False,
                show_default=False,
                console=console,
            ).strip().upper()
            if retry == "Y":
                continue
            break

        # Defensive: keep only the cards we asked for, in the order we asked.
        en_chunk = [c for c in en_chunk if c["id"] in {c["id"] for c in es_chunk}]
        en_chunk.sort(key=lambda c: c["id"])
        if len(en_chunk) != len(es_chunk):
            console.print(
                f"[red]Warning:[/red] Gemini returned {len(en_chunk)} cards but "
                f"{len(es_chunk)} were expected. Skipping chunk."
            )
            i += args.chunk
            continue

        while True:
            console.clear()
            render_chunk(console, es_chunk, en_chunk)
            action = prompt_action(console)

            if action == "A":
                en_data["cards"].extend(strip_metadata(en_chunk))
                en_data["cards"].sort(key=lambda c: c["id"])
                args.en.parent.mkdir(parents=True, exist_ok=True)
                save_json(args.en, en_data)
                console.print(
                    f"[green]Saved[/green] cards "
                    f"{es_chunk[0]['id']}–{es_chunk[-1]['id']} → {args.en}"
                )
                i += args.chunk
                break

            if action == "E":
                en_chunk = edit_chunk_in_editor(es_chunk, en_chunk)
                continue

            if action == "S":
                en_data["cards"].extend(strip_metadata(en_chunk))
                en_data["cards"].sort(key=lambda c: c["id"])
                args.en.parent.mkdir(parents=True, exist_ok=True)
                save_json(args.en, en_data)
                console.print(
                    f"[green]Saved & exiting.[/green] Progress written to {args.en}"
                )
                return 0

            if action == "X":
                console.print("[yellow]Exiting without saving current chunk.[/yellow]")
                return 1

    console.print("[bold green]All cards translated.[/bold green]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
