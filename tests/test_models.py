"""The card and deck models."""
from __future__ import annotations

import pytest

from ffparse import Card, Deck

# -- the two bugs the dataclass had ---------------------------------------

def test_a_card_requires_nothing_it_should_not_and_rejects_rubbish() -> None:
    """The old version wrote its own `__init__` that did `setattr` over
    `**kwargs`, which replaces the dataclass-generated one and makes every
    field declaration decorative. `Card(nonsense=1)` succeeded and produced an
    object with no `name`."""
    with pytest.raises(TypeError):
        Card(nonsense=1)  # type: ignore[call-arg]


def test_sort_index_is_actually_set() -> None:
    """The old version had `def _post_init__`, one underscore short, so
    `sort_index` was never assigned."""
    card = Card(name="Zack")
    assert card.sort_index == "zack"


def test_cards_can_be_sorted() -> None:
    """`order=True` sorts on the first field, so with `sort_index` unset the
    old version raised `AttributeError: 'Card' object has no attribute
    'sort_index'` on any comparison."""
    cards = [Card(name="Zack"), Card(name="Aerith"), Card(name="Cloud")]
    assert [c.name for c in sorted(cards)] == ["Aerith", "Cloud", "Zack"]


# -- the API's untidy payload ---------------------------------------------

def test_from_api_maps_the_odd_field_names(api_payload: dict) -> None:
    card = Card.from_api(api_payload)
    assert card.name == "Zack"
    assert card.code == "1-100L"
    assert card.card_type == "Forward"
    assert card.category == "VII"


def test_from_api_converts_numbers_from_strings(api_payload: dict) -> None:
    """The API returns them as strings."""
    card = Card.from_api(api_payload)
    assert card.cost == 5
    assert card.power == 9000


def test_from_api_handles_the_api_s_empty_values() -> None:
    card = Card.from_api({"Name_EN": "Summon", "Cost": "3", "Power": "-"})
    assert card.cost == 3
    assert card.power is None  # "-" is the API's "not applicable"


def test_from_api_takes_the_first_image(api_payload: dict) -> None:
    assert Card.from_api(api_payload).image == "https://example.com/1-100L.png"


def test_from_api_ignores_unknown_fields(api_payload: dict) -> None:
    """The old `setattr` loop accepted anything, so a renamed API field became
    a silently missing attribute rather than an error."""
    card = Card.from_api(api_payload)
    assert not hasattr(card, "SomeNewFieldTheApiAdded")


def test_from_api_accepts_the_misspelled_category_alias() -> None:
    """`catagory` was in the old model's public field names."""
    assert Card.from_api({"catagory": "VII"}).category == "VII"


def test_a_card_parses_its_own_text(zack: str) -> None:
    card = Card(name="Zack", text=zack)
    assert len(card.parsed().abilities) == 3


def test_reassigning_text_reparses(zack: str) -> None:
    """Which is why the parse is not cached on the instance."""
    card = Card(name="Zack", text=zack)
    assert card.parsed().abilities
    card.text = "This card has no rules."
    assert card.parsed().abilities == []


# -- deck rules -----------------------------------------------------------

def test_a_deck_enforces_the_copy_limit() -> None:
    """The old model had a `card_limit` field and nothing that used it."""
    deck = Deck()
    zack = Card(name="Zack")
    deck.add(zack, 3)
    with pytest.raises(ValueError, match="exceeds the limit"):
        deck.add(zack)


def test_a_deck_enforces_its_size() -> None:
    deck = Deck(size=10)
    for index in range(3):
        deck.add(Card(name=f"Card {index}"), 3)   # 9 of 10
    assert len(deck.cards) == 9

    with pytest.raises(ValueError, match="over the"):
        deck.add(Card(name="One more"), 3)        # would be 12
    assert len(deck.cards) == 9                   # and nothing was added


def test_a_deck_is_legal_only_at_exactly_the_right_size() -> None:
    deck = Deck(size=6)
    for index in range(2):
        deck.add(Card(name=f"Card {index}"), 3)
    assert deck.is_legal
    assert deck.problems() == []


def test_an_incomplete_deck_says_what_is_wrong() -> None:
    deck = Deck(size=50)
    deck.add(Card(name="Zack"), 3)
    assert not deck.is_legal
    assert any("needs exactly 50" in p for p in deck.problems())


def test_adding_zero_or_fewer_is_refused() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        Deck().add(Card(name="Zack"), 0)


def test_elements_are_counted() -> None:
    deck = Deck()
    deck.add(Card(name="A", element="Fire"), 3)
    deck.add(Card(name="B", element="Ice"), 2)
    assert deck.elements() == {"Fire": 3, "Ice": 2}
