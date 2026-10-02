"""The command line.

    ffparse text "When Zack enters the field, deal it 2000 damage"
    ffparse card cards.json --name Zack
    ffparse coverage cards.json          how much of a set the patterns read
    ffparse rules                        every pattern, by specificity

`coverage` is the one that matters when changing `patterns.py`: run it before
and after an edit and the numbers say whether it helped.

Output is ASCII, because an em-dash crashes a legacy Windows console code page.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import Card
from .parser import coverage_report, parse
from .patterns import RULES, TRIGGER_RULES


def _load_cards(path: str) -> list[Card]:
    """Read a card dump.

    Accepts a list of objects, or an object whose values are the cards, which
    is how the official API and the common community dumps differ.
    """
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"no card file at {source}")

    payload = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        # Either {"cards": [...]} or {"1-001H": {...}, ...}
        if "cards" in payload and isinstance(payload["cards"], list):
            payload = payload["cards"]
        else:
            payload = list(payload.values())

    if not isinstance(payload, list):
        raise ValueError(f"{source.name} does not hold a list of cards")

    return [Card.from_api(entry) for entry in payload if isinstance(entry, dict)]


# -- commands --------------------------------------------------------------

def cmd_text(args: argparse.Namespace) -> int:
    """Parse rules text given on the command line."""
    parsed = parse(" ".join(args.text))
    print(parsed.describe())
    if args.json:
        print()
        print(json.dumps(_as_dict(parsed), indent=2))
    # Non-zero when something was not understood, so this can gate a script.
    return 2 if parsed.unparsed else 0


def cmd_card(args: argparse.Namespace) -> int:
    try:
        cards = _load_cards(args.file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(exc)
        return 1

    if args.name:
        wanted = args.name.lower()
        cards = [c for c in cards if wanted in c.name.lower()]
        if not cards:
            print(f"no card matching {args.name!r}")
            return 1

    for card in cards[: args.limit]:
        print(card.describe())
        print()
    if len(cards) > args.limit:
        print(f"... and {len(cards) - args.limit} more")
    return 0


def cmd_coverage(args: argparse.Namespace) -> int:
    """How much of a card set the patterns understand."""
    try:
        cards = _load_cards(args.file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(exc)
        return 1

    with_text = [c for c in cards if c.text.strip()]
    print(f"{len(cards)} card(s), {len(with_text)} with rules text")
    print()
    print(coverage_report([c.parsed() for c in with_text]))
    return 0


def cmd_rules(args: argparse.Namespace) -> int:
    """Every pattern, most specific first.

    Specificity is what stops a general pattern firing alongside the specific
    one that already explained a clause, so it is worth being able to see.
    """
    print(f"{len(RULES)} effect rule(s), most specific first")
    for rule in RULES:
        print(f"  [{rule.specificity:>3}] {rule.name:<24}{rule.pattern.pattern}")
    print()
    print(f"{len(TRIGGER_RULES)} trigger rule(s)")
    for trigger_rule in TRIGGER_RULES:
        print(f"  [{trigger_rule.specificity:>3}] "
              f"{trigger_rule.trigger.value:<16}{trigger_rule.pattern.pattern}")
    return 0


def _as_dict(parsed) -> dict:  # noqa: ANN001
    """The parse as plain JSON, for piping into something else."""
    return {
        "text": parsed.text,
        "coverage": parsed.coverage,
        "abilities": [
            {
                "trigger": ability.trigger.value,
                "your_turn_only": ability.your_turn_only,
                "conditions": [
                    {"kind": c.kind, "detail": c.detail} for c in ability.conditions
                ],
                "effects": [
                    {
                        "action": effect.action.value,
                        "amount": effect.amount,
                        "keyword": effect.keyword.value if effect.keyword else None,
                        "zone": effect.zone.value if effect.zone else None,
                        "target": None if effect.target is None else {
                            "card_type": effect.target.card_type,
                            "controller": effect.target.controller.value,
                            "count": effect.target.count,
                            "up_to": effect.target.up_to,
                            "max_cost": effect.target.max_cost,
                        },
                        "source_text": effect.source_text,
                    }
                    for effect in ability.effects
                ],
            }
            for ability in parsed.abilities
        ],
        "unparsed": parsed.unparsed,
    }


# -- wiring ----------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ffparse",
        description="Turn Final Fantasy TCG rules text into structured effects.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    text = subparsers.add_parser("text", help="parse rules text")
    text.add_argument("text", nargs="+")
    text.add_argument("--json", action="store_true", help="also print it as JSON")
    text.set_defaults(handler=cmd_text)

    card = subparsers.add_parser("card", help="parse cards from a JSON dump")
    card.add_argument("file")
    card.add_argument("--name", help="only cards whose name contains this")
    card.add_argument("--limit", type=int, default=10)
    card.set_defaults(handler=cmd_card)

    coverage = subparsers.add_parser(
        "coverage", help="how much of a card set the patterns understand")
    coverage.add_argument("file")
    coverage.set_defaults(handler=cmd_coverage)

    subparsers.add_parser("rules", help="every pattern, by specificity").set_defaults(
        handler=cmd_rules)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
