"""ffparse - Final Fantasy TCG rules text, as structured data.

Card text is a small formal language dressed up as English. This reads it.

    from ffparse import parse

    card = parse("When Zack enters the field, choose 1 Forward opponent "
                 "controls. Deal it 2000 damage.")
    for ability in card.abilities:
        print(ability.describe())

    # [enters_field]
    #   search -> 1 Forward (opponent)
    # [enters_field]
    #   damage 2000

The amounts and the targets are kept, which is the half that matters: a card
that deals damage is not usable information, a card that deals 2000 damage to a
Forward the opponent controls is.

`ParsedCard.coverage` and `coverage_report` say how much of a set the patterns
understand, which is the number to watch when changing them.

No dependencies. Card text needs a regex grammar, not a part-of-speech model.
"""
from .effects import (
    Ability,
    Action,
    Condition,
    Controller,
    Effect,
    Keyword,
    ParsedCard,
    Target,
    Trigger,
    Zone,
)
from .models import Card, Deck
from .parser import (
    coverage_report,
    extract_effects,
    normalise,
    parse,
    parse_many,
    parse_sentence,
    split_sentences,
)
from .patterns import RULES, TRIGGER_RULES, Rule, detect_conditions, detect_trigger

__version__ = "1.0.0"

__all__ = [
    "parse", "parse_many", "parse_sentence", "extract_effects",
    "split_sentences", "normalise", "coverage_report",
    "ParsedCard", "Ability", "Effect", "Condition", "Target",
    "Action", "Trigger", "Keyword", "Zone", "Controller",
    "Card", "Deck",
    "Rule", "RULES", "TRIGGER_RULES", "detect_trigger", "detect_conditions",
    "__version__",
]
