"""What a card's rules text means, as data.

A trading card's text is a small, highly regular formal language dressed up as
English. "When Zack enters the field, choose 1 Forward opponent controls. Deal
it 2000 damage." has a trigger, a target and an effect with a magnitude, and all
three are needed to reason about a board.

The previous version returned a list of labels: `['Enters Field', 'Choose
Forward', 'Deal it damage']`. The patterns captured the numbers, and then
`classify_card_intents` threw the capture groups away and kept only the label.
So the parser knew the card dealt damage and not how much, which is the half
that matters.

These dataclasses are what it returns instead.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Trigger(str, Enum):
    """When an effect happens."""

    #: No trigger: a static property like Haste or Brave.
    STATIC = "static"
    ENTERS_FIELD = "enters_field"
    LEAVES_FIELD = "leaves_field"
    DEALS_DAMAGE = "deals_damage"
    #: Paid with a cost, usable on your turn.
    ACTIVATED = "activated"
    #: An EX BURST, which only triggers when drawn as damage.
    EX_BURST = "ex_burst"
    ATTACKS = "attacks"
    BLOCKS = "blocks"


class Action(str, Enum):
    """What the effect does."""

    DAMAGE = "damage"
    MODIFY_POWER = "modify_power"
    DULL = "dull"
    FREEZE = "freeze"
    BREAK = "break"
    ACTIVATE = "activate"
    DRAW = "draw"
    DISCARD = "discard"
    SEARCH = "search"
    RETURN_TO_HAND = "return_to_hand"
    RETURN_TO_DECK = "return_to_deck"
    PLAY_CHARACTER = "play_character"
    ADD_TO_HAND = "add_to_hand"
    PRODUCE_CP = "produce_cp"
    REDUCE_COST = "reduce_cost"
    CANCEL = "cancel"
    GRANT_KEYWORD = "grant_keyword"
    PREVENT_LEAVE = "prevent_leave"


class Keyword(str, Enum):
    """Static abilities that are their own whole effect."""

    HASTE = "Haste"
    BRAVE = "Brave"
    FIRST_STRIKE = "First Strike"
    EX_BURST = "EX BURST"


class Zone(str, Enum):
    FIELD = "field"
    HAND = "hand"
    DECK = "deck"
    BREAK_ZONE = "break_zone"
    DAMAGE_ZONE = "damage_zone"
    GAME = "game"


class Controller(str, Enum):
    """Whose cards an effect can touch. The distinction the previous version
    lost: it labelled "choose 1 Forward opponent controls" and "choose 1
    Forward" identically, and they are not the same card."""

    ANY = "any"
    SELF = "self"
    OPPONENT = "opponent"


@dataclass(frozen=True)
class Target:
    """What an effect is applied to."""

    #: "Forward", "Backup", "Character", "Summon", or "" when it is implicit.
    card_type: str = ""
    controller: Controller = Controller.ANY
    #: How many. None means "all" or unspecified, which is not the same as one.
    count: int | None = 1
    #: True for "up to N", where fewer is allowed.
    up_to: bool = False
    #: A cost restriction, as in "of cost 3 or less".
    max_cost: int | None = None

    def describe(self) -> str:
        parts = []
        if self.count is None:
            parts.append("all")
        else:
            parts.append(f"up to {self.count}" if self.up_to else str(self.count))
        parts.append(self.card_type or "card(s)")
        if self.controller is not Controller.ANY:
            parts.append(f"({self.controller.value})")
        if self.max_cost is not None:
            parts.append(f"cost <= {self.max_cost}")
        return " ".join(parts)


@dataclass(frozen=True)
class Condition:
    """A prerequisite. "If you control [Card Name (Aerith)]" is one."""

    kind: str
    #: What has to be true, as written.
    detail: str = ""

    def describe(self) -> str:
        return f"{self.kind}: {self.detail}" if self.detail else self.kind


@dataclass
class Effect:
    """One effect, with its magnitude.

    `amount` is the field the previous version discarded. A card that deals
    damage is not usable information; a card that deals 2000 damage is.
    """

    action: Action
    amount: int | None = None
    target: Target | None = None
    keyword: Keyword | None = None
    zone: Zone | None = None
    #: The matched text, so a reader can check the parse against the card.
    source_text: str = ""

    def describe(self) -> str:
        parts = [self.action.value]
        if self.amount is not None:
            parts.append(f"{self.amount:+d}" if self.action is Action.MODIFY_POWER
                         else str(self.amount))
        if self.keyword is not None:
            parts.append(self.keyword.value)
        if self.target is not None:
            parts.append(f"-> {self.target.describe()}")
        if self.zone is not None:
            parts.append(f"[{self.zone.value}]")
        return " ".join(parts)


@dataclass
class Ability:
    """A trigger, its conditions, and the effects that follow."""

    trigger: Trigger = Trigger.STATIC
    conditions: list[Condition] = field(default_factory=list)
    effects: list[Effect] = field(default_factory=list)
    #: The sentence this came from.
    source_text: str = ""
    #: Only usable on your own turn.
    your_turn_only: bool = False

    @property
    def is_empty(self) -> bool:
        return not self.effects

    def describe(self) -> str:
        lines = [f"[{self.trigger.value}]"]
        for condition in self.conditions:
            lines.append(f"  if {condition.describe()}")
        for effect in self.effects:
            lines.append(f"  {effect.describe()}")
        if self.your_turn_only:
            lines.append("  (your turn only)")
        return "\n".join(lines)


@dataclass
class ParsedCard:
    """Everything understood from one card's text."""

    text: str
    abilities: list[Ability] = field(default_factory=list)
    #: Sentences no pattern matched. The honest output: a parser that reports
    #: nothing unmatched on real data is not accurate, it is not looking.
    unparsed: list[str] = field(default_factory=list)

    @property
    def keywords(self) -> list[Keyword]:
        return [
            effect.keyword
            for ability in self.abilities
            for effect in ability.effects
            if effect.keyword is not None
        ]

    @property
    def actions(self) -> list[Action]:
        return [e.action for a in self.abilities for e in a.effects]

    @property
    def coverage(self) -> float:
        """The fraction of sentences that produced at least one effect.

        The number to watch when changing patterns. The previous version had no
        equivalent, so there was no way to tell whether an edit improved the
        parser or quietly broke it.
        """
        total = len(self.abilities) + len(self.unparsed)
        return round(len(self.abilities) / total, 4) if total else 0.0

    def describe(self) -> str:
        lines = [f"{len(self.abilities)} ability(ies), "
                 f"coverage {self.coverage:.0%}"]
        for ability in self.abilities:
            lines.append(ability.describe())
        if self.unparsed:
            lines.append(f"  {len(self.unparsed)} sentence(s) not understood:")
            lines += [f"    {s[:70]}" for s in self.unparsed]
        return "\n".join(lines)
