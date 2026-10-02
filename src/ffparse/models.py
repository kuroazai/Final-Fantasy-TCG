"""The card itself.

The previous version declared twenty typed dataclass fields and then wrote its
own `__init__`:

    @dataclass(order=True, frozen=False)
    class Card:
        sort_index: str = field(init=True, repr=False)
        name: str
        ...
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

A custom `__init__` replaces the one the decorator generates, so every field
declaration became decorative. `Card(nonsense=1)` succeeded and produced an
object with no `name`, no type checking and no required fields.

It also had `def _post_init__`, one underscore short of `__post_init__`, so
`sort_index` was never assigned. Since `order=True` sorts on the first field,
sorting any two cards raised `AttributeError: 'Card' object has no attribute
'sort_index'`.

Both are fixed by deleting the custom `__init__` and letting the dataclass do
its job. `from_api` handles the untidy keys from the card API, which is what the
`**kwargs` constructor was presumably for.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields

from .effects import ParsedCard
from .parser import parse

#: The API's field names, mapped onto this model's. The misspelling `catagory`
#: was in the previous version's public field names; it is accepted here as an
#: input alias and spelled correctly on the model.
API_ALIASES = {
    "Name_EN": "name",
    "Text_EN": "text",
    "Code": "code",
    "Element": "element",
    "Cost": "cost",
    "Power": "power",
    "Job_EN": "job",
    "Category_1": "category",
    "catagory": "category",
    "Type_EN": "card_type",
    "Rarity": "rarity",
    "Set": "boxset",
    "images": "image",
}


def _as_int(value: object) -> int | None:
    """The card API returns numbers as strings, and absent ones as "" or "-"."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text in {"-", "null", "None"}:
        return None
    # Power is written "9000" but also "9,000" in some sets.
    try:
        return int(text.replace(",", ""))
    except ValueError:
        return None


@dataclass(order=True)
class Card:
    """One card.

    `order=True` with `sort_index` first, and `sort_index` is actually set now,
    in a `__post_init__` spelled correctly.
    """

    sort_index: str = field(init=False, repr=False, compare=True)
    name: str = ""
    text: str = ""
    code: str = ""
    element: str = ""
    card_type: str = ""
    job: str = ""
    category: str = ""
    rarity: str = ""
    boxset: str = ""
    image: str = ""
    cost: int | None = None
    power: int | None = None

    def __post_init__(self) -> None:
        # Two underscores. The previous version had one, so this never ran and
        # sorting raised AttributeError.
        self.sort_index = self.name.lower()

    @classmethod
    def from_api(cls, payload: dict) -> Card:
        """Build from the card API's own field names.

        Unknown keys are ignored rather than set as attributes. The previous
        version's `setattr` loop accepted anything, so a renamed API field
        became a silently missing attribute instead of an error.
        """
        known = {f.name for f in fields(cls) if f.init}
        values: dict[str, object] = {}

        for key, value in payload.items():
            name = API_ALIASES.get(key, key)
            if name not in known:
                continue
            if name in {"cost", "power"}:
                values[name] = _as_int(value)
            elif isinstance(value, list):
                # `images` comes back as a list; take the first.
                values[name] = str(value[0]) if value else ""
            else:
                values[name] = "" if value is None else str(value).strip()

        return cls(**values)  # type: ignore[arg-type]

    # -- the parsed text ---------------------------------------------------
    def parsed(self) -> ParsedCard:
        """The rules text, as structured effects. Parsed on each call, which is
        cheap, and keeps `Card` free of cached state that could go stale when
        `text` is reassigned."""
        return parse(self.text)

    def describe(self) -> str:
        lines = [
            f"{self.name} [{self.code}]" if self.code else self.name,
            f"  {self.card_type} / {self.element}"
            + (f" / cost {self.cost}" if self.cost is not None else "")
            + (f" / {self.power} power" if self.power is not None else ""),
        ]
        if self.text:
            parsed = self.parsed()
            lines.append("  " + parsed.describe().replace("\n", "\n  "))
        return "\n".join(lines)


@dataclass
class Deck:
    """A deck, with the rules the game actually imposes.

    The previous version had a `card_limit` field on `Card` and nothing that
    used it.
    """

    #: Final Fantasy TCG decks are exactly 50 cards.
    size: int = 50
    #: And at most 3 copies of any one card, by name.
    copies_per_card: int = 3
    cards: list[Card] = field(default_factory=list)

    def add(self, card: Card, quantity: int = 1) -> None:
        if quantity < 1:
            raise ValueError("quantity must be at least 1")
        existing = self.count_of(card.name)
        if existing + quantity > self.copies_per_card:
            raise ValueError(
                f"{card.name}: {existing + quantity} copies exceeds the limit of "
                f"{self.copies_per_card}"
            )
        if len(self.cards) + quantity > self.size:
            raise ValueError(
                f"deck would hold {len(self.cards) + quantity} cards, over the "
                f"{self.size}-card limit"
            )
        self.cards.extend([card] * quantity)

    def count_of(self, name: str) -> int:
        return sum(1 for card in self.cards if card.name == name)

    @property
    def is_legal(self) -> bool:
        return len(self.cards) == self.size and all(
            self.count_of(name) <= self.copies_per_card
            for name in {c.name for c in self.cards}
        )

    def problems(self) -> list[str]:
        found = []
        if len(self.cards) != self.size:
            found.append(f"{len(self.cards)} cards, needs exactly {self.size}")
        for name in sorted({c.name for c in self.cards}):
            count = self.count_of(name)
            if count > self.copies_per_card:
                found.append(f"{name}: {count} copies, limit {self.copies_per_card}")
        return found

    def elements(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for card in self.cards:
            counts[card.element] = counts.get(card.element, 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: -kv[1]))

    def describe(self) -> str:
        lines = [f"{len(self.cards)}/{self.size} cards"]
        for element, count in self.elements().items():
            lines.append(f"  {element or 'none':<12}{count:>4}")
        problems = self.problems()
        if problems:
            lines.append("  not legal:")
            lines += [f"    {p}" for p in problems]
        return "\n".join(lines)
