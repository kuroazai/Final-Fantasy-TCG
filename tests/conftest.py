"""Shared fixtures.

The card text is real Final Fantasy TCG wording, which is the only kind worth
testing a parser for. Invented text that happens to match the patterns proves
nothing.
"""
from __future__ import annotations

import pytest

#: The example the previous version shipped in its `__main__` block.
ZACK = (
    "If you control [Card Name (Aerith)], Zack gains +2000 power. "
    "When Zack enters the field, choose 1 Forward opponent controls. "
    "Deal it 2000 damage."
)

CARDS = {
    "keywords": "Haste, Brave, First Strike.",
    "ex_burst": "EX BURST When this card enters the field, draw 1 card.",
    "control": "Choose up to 2 Forwards opponent controls. Dull them and Freeze them.",
    "removal": "Choose 1 Forward of cost 3 or less. Break it.",
    "restriction_first": (
        "You can only use this ability during your turn. "
        "Discard 1 card: Choose 1 Backup. Return it to its owner's hand."
    ),
    "restriction_last": (
        "Discard 1 card: Choose 1 Backup. "
        "You can only use this ability during your turn."
    ),
    "flavour_only": "This card has flavour text only and no rules at all.",
    "leaves": "When this card leaves the field, you lose 1000 power.",
    "cost": (
        "The cost required to cast this card is reduced by 2 for every 3 "
        "cards in your Break Zone."
    ),
}


@pytest.fixture
def zack() -> str:
    return ZACK


@pytest.fixture
def cards() -> dict[str, str]:
    return dict(CARDS)


@pytest.fixture
def api_payload() -> dict:
    """A card as the official API returns it: numbers as strings, odd keys."""
    return {
        "Name_EN": "Zack",
        "Text_EN": ZACK,
        "Code": "1-100L",
        "Element": "Fire",
        "Cost": "5",
        "Power": "9000",
        "Type_EN": "Forward",
        "Job_EN": "SOLDIER",
        "Category_1": "VII",
        "Rarity": "L",
        "Set": "Opus I",
        "images": ["https://example.com/1-100L.png"],
        "SomeNewFieldTheApiAdded": "ignored",
    }
