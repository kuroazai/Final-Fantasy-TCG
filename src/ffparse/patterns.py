"""The patterns, compiled once and ordered by specificity.

Three things wrong with the previous version, all of which it inherited from
being a flat dict checked in insertion order:

**The patterns were recompiled on every call.** Fifty `re.findall` calls per
card, each compiling its pattern from scratch, over several thousand cards.

**`re.findall(pattern.lower(), text.lower())` lowercased the pattern.**
Lowercasing a regex is not safe: `\\S` becomes `\\s`, `\\D` becomes `\\d`, `\\B`
becomes `\\b`, each of which means the opposite of what was written. None of the
patterns used those, so it worked, but it is a landmine under every future
pattern. `re.IGNORECASE` is the thing that was wanted.

**Everything matched at once, so general patterns fired alongside specific
ones.** `r'If'` and `r'Choose'` and `r'ability'` were in the same dict as
`r'If you control ([^"]*),'`, so "If you control X, choose 1 Forward" produced
`['Control Ally', 'Choose Forward', 'conditional', 'Choose']` - four labels for
two clauses, two of them redundant. `r'ability'` also matched inside
"abilities", so both fired.

Here each pattern declares its specificity, the most specific match for a span
of text wins, and a general pattern only applies to text no specific one
claimed.
"""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from .effects import (
    Action,
    Condition,
    Controller,
    Effect,
    Keyword,
    Target,
    Trigger,
    Zone,
)

#: A number as cards write it: 2000, 1, +2000, -1000.
NUMBER = r"([+-]?\d[\d,]*)"
#: A card type.
CARD_TYPE = r"(Forward|Backup|Character|Summon|Monster)"
#: "its owner's" or "their owners'". Written out because the obvious
#: `owners?'?` does not match "owner's": after "owner" the text has "'s",
#: and that pattern wants the apostrophe before an s it has already consumed.
OWNERS = r"owner(?:'s|s'|s)?"


def to_int(raw: str | None) -> int | None:
    """"+2000" -> 2000, "-1000" -> -1000, "2,000" -> 2000, None -> None."""
    if raw is None:
        return None
    cleaned = raw.replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def signed_int(raw: str | None) -> int | None:
    """Like `to_int`, but keeps an explicit sign. "+2000" -> 2000, "-1000" -> -1000."""
    return to_int(raw)


@dataclass
class Rule:
    """One pattern, and how to turn a match into an effect."""

    name: str
    pattern: re.Pattern[str]
    build: Callable[[re.Match[str]], Effect | None]
    #: Higher wins. A rule that reads a number and a target beats one that spots
    #: a bare word.
    specificity: int = 50
    #: What this rule implies about when the ability happens.
    trigger: Trigger | None = None

    def search(self, text: str) -> re.Match[str] | None:
        return self.pattern.search(text)


def _compile(pattern: str) -> re.Pattern[str]:
    """Compile once, case-insensitively.

    `re.IGNORECASE` rather than lowercasing the pattern string, which is what
    the previous version did and which silently inverts any `\\S`, `\\D` or
    `\\B` in a future pattern.
    """
    return re.compile(pattern, re.IGNORECASE)


# -- builders --------------------------------------------------------------

def _controller_from(match: re.Match[str]) -> Controller:
    """Who the target belongs to, from the matched text.

    "opponent controls" and "you control" are the distinction the previous
    version lost entirely: it gave the same label to a card that hits your
    Forward and one that hits theirs.
    """
    whole = match.group(0).lower()
    if "opponent control" in whole:
        return Controller.OPPONENT
    if "you control" in whole:
        return Controller.SELF
    return Controller.ANY


def _target_from(match: re.Match[str]) -> Target:
    groups = match.groupdict()
    count_raw = groups.get("count")
    return Target(
        card_type=(groups.get("type") or "").strip().title(),
        controller=_controller_from(match),
        count=to_int(count_raw) if count_raw else 1,
        up_to="up to" in match.group(0).lower(),
        max_cost=to_int(groups.get("cost")),
    )


RULES: list[Rule] = [
    # -- keywords, the simplest and most specific --------------------------
    Rule("haste", _compile(r"\bHaste\b"),
         lambda m: Effect(Action.GRANT_KEYWORD, keyword=Keyword.HASTE,
                          source_text=m.group(0)), specificity=90),
    Rule("brave", _compile(r"\bBrave\b"),
         lambda m: Effect(Action.GRANT_KEYWORD, keyword=Keyword.BRAVE,
                          source_text=m.group(0)), specificity=90),
    Rule("first strike", _compile(r"\bFirst Strike\b"),
         lambda m: Effect(Action.GRANT_KEYWORD, keyword=Keyword.FIRST_STRIKE,
                          source_text=m.group(0)), specificity=90),
    Rule("ex burst", _compile(r"\bEX BURST\b"),
         lambda m: Effect(Action.GRANT_KEYWORD, keyword=Keyword.EX_BURST,
                          source_text=m.group(0)),
         specificity=95, trigger=Trigger.EX_BURST),

    # -- damage, with the amount -------------------------------------------
    Rule("deal damage", _compile(rf"[Dd]eal (?:it |them )?{NUMBER} damage"),
         lambda m: Effect(Action.DAMAGE, amount=to_int(m.group(1)),
                          source_text=m.group(0)), specificity=95),

    # -- power, with the sign ----------------------------------------------
    Rule("gains power", _compile(rf"gains? {NUMBER} power"),
         lambda m: Effect(Action.MODIFY_POWER, amount=signed_int(m.group(1)),
                          source_text=m.group(0)), specificity=95),
    Rule("loses power", _compile(rf"loses? {NUMBER} power"),
         lambda m: Effect(
             Action.MODIFY_POWER,
             amount=-abs(signed_int(m.group(1)) or 0),
             source_text=m.group(0),
         ), specificity=95),

    # -- targeting ---------------------------------------------------------
    Rule(
        "choose n type of cost",
        _compile(
            rf"[Cc]hoose (?:up to )?(?P<count>\d+) (?P<type>{CARD_TYPE})s?"
            rf" of cost (?P<cost>\d+) or less"
        ),
        lambda m: Effect(Action.SEARCH, target=_target_from(m),
                         source_text=m.group(0)), specificity=90,
    ),
    Rule(
        "choose n type controller",
        _compile(
            rf"[Cc]hoose (?:up to )?(?P<count>\d+) (?P<type>{CARD_TYPE})s?"
            r"(?: (?:your |the )?opponent controls| you control)?"
        ),
        lambda m: Effect(Action.SEARCH, target=_target_from(m),
                         source_text=m.group(0)), specificity=80,
    ),
    Rule(
        "all of type",
        _compile(rf"all (?:the )?(?P<type>{CARD_TYPE})s"),
        lambda m: Effect(
            Action.SEARCH,
            target=Target(card_type=(m.group("type") or "").title(),
                           controller=_controller_from(m), count=None),
            source_text=m.group(0),
        ), specificity=70,
    ),

    # -- state changes -----------------------------------------------------
    Rule("dull and freeze", _compile(r"[Dd]ull (?:it|them) and [Ff]reeze (?:it|them)"),
         lambda m: Effect(Action.FREEZE, source_text=m.group(0)), specificity=92),
    Rule("dull", _compile(r"\b[Dd]ull\b"),
         lambda m: Effect(Action.DULL, source_text=m.group(0)), specificity=60),
    Rule("freeze", _compile(r"\b[Ff]reeze\b"),
         lambda m: Effect(Action.FREEZE, source_text=m.group(0)), specificity=60),
    Rule("break", _compile(r"\b[Bb]reak (?:it|them)\b"),
         lambda m: Effect(Action.BREAK, source_text=m.group(0)), specificity=85),
    Rule("cannot leave", _compile(r"cannot leave the field"),
         lambda m: Effect(Action.PREVENT_LEAVE, source_text=m.group(0)),
         specificity=88),

    # -- cards and zones ---------------------------------------------------
    Rule("draw", _compile(rf"[Dd]raw {NUMBER} card"),
         lambda m: Effect(Action.DRAW, amount=to_int(m.group(1)),
                          zone=Zone.HAND, source_text=m.group(0)), specificity=90),
    Rule("discard", _compile(rf"[Dd]iscard {NUMBER} card"),
         lambda m: Effect(Action.DISCARD, amount=to_int(m.group(1)),
                          zone=Zone.BREAK_ZONE, source_text=m.group(0)),
         specificity=90),
    Rule("return to hand",
         _compile(rf"[Rr]eturn (?:it|them) to (?:its|their) {OWNERS} hands?"),
         lambda m: Effect(Action.RETURN_TO_HAND, zone=Zone.HAND,
                          source_text=m.group(0)), specificity=88),
    Rule("add to hand", _compile(r"[Aa]dd (?:it|them) to your hand"),
         lambda m: Effect(Action.ADD_TO_HAND, zone=Zone.HAND,
                          source_text=m.group(0)), specificity=88),
    Rule("put on top of deck",
         _compile(rf"[Pp]ut (?:it|them) on top of (?:its|their) {OWNERS} deck"),
         lambda m: Effect(Action.RETURN_TO_DECK, zone=Zone.DECK,
                          source_text=m.group(0)), specificity=88),
    Rule("into damage zone", _compile(r"into the [Dd]amage [Zz]one"),
         lambda m: Effect(Action.DAMAGE, zone=Zone.DAMAGE_ZONE,
                          source_text=m.group(0)), specificity=70),
    Rule("remove from game", _compile(rf"[Rr]emove {NUMBER} (?:{CARD_TYPE})s? from the game"),
         lambda m: Effect(Action.DISCARD, amount=to_int(m.group(1)), zone=Zone.GAME,
                          source_text=m.group(0)), specificity=90),

    # -- resources ---------------------------------------------------------
    Rule("produce cp", _compile(r"produce.{0,20}CP"),
         lambda m: Effect(Action.PRODUCE_CP, source_text=m.group(0)),
         specificity=80),
    Rule("reduce cost", _compile(rf"cost.{{0,60}}reduced by {NUMBER}"),
         lambda m: Effect(Action.REDUCE_COST, amount=to_int(m.group(1)),
                          source_text=m.group(0)), specificity=90),

    # -- play and cancel ---------------------------------------------------
    Rule("play character", _compile(rf"[Pp]lay (?:up to )?{NUMBER} (?:{CARD_TYPE})"),
         lambda m: Effect(Action.PLAY_CHARACTER, amount=to_int(m.group(1)),
                          source_text=m.group(0)), specificity=88),
    Rule("cancel", _compile(r"\b[Cc]ancel(?:led|s)?\b"),
         lambda m: Effect(Action.CANCEL, source_text=m.group(0)), specificity=65),
    Rule("activate", _compile(r"\b[Aa]ctivate\b"),
         lambda m: Effect(Action.ACTIVATE, source_text=m.group(0)), specificity=60),
]

#: Highest specificity first, so the loop can stop at the first match for a
#: region of text.
RULES.sort(key=lambda rule: -rule.specificity)


# -- triggers --------------------------------------------------------------

@dataclass
class TriggerRule:
    trigger: Trigger
    pattern: re.Pattern[str]
    specificity: int = 50


TRIGGER_RULES: list[TriggerRule] = [
    TriggerRule(Trigger.EX_BURST, _compile(r"\bEX BURST\b"), 95),
    TriggerRule(Trigger.ENTERS_FIELD, _compile(r"[Ww]hen .{0,40}enters the field"), 90),
    TriggerRule(Trigger.LEAVES_FIELD, _compile(r"[Ww]hen .{0,40}leaves the field"), 90),
    TriggerRule(Trigger.DEALS_DAMAGE,
                _compile(r"[Ww]hen .{0,40}deals damage to your opponent"), 90),
    TriggerRule(Trigger.ATTACKS, _compile(r"[Ww]hen .{0,40}attacks\b"), 80),
    TriggerRule(Trigger.BLOCKS, _compile(r"[Ww]hen .{0,40}blocks\b"), 80),
    TriggerRule(Trigger.ACTIVATED, _compile(r"\bActivate\b"), 60),
]
TRIGGER_RULES.sort(key=lambda rule: -rule.specificity)


def detect_trigger(text: str) -> Trigger:
    """The most specific trigger the text implies, or STATIC."""
    for rule in TRIGGER_RULES:
        if rule.pattern.search(text):
            return rule.trigger
    return Trigger.STATIC


# -- conditions ------------------------------------------------------------

CONDITION_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("controls", _compile(r"[Ii]f you control ([^,.]+)")),
    ("on field", _compile(r"[Ii]f ([^,.]{0,60}) is on the field")),
    ("for each", _compile(r"[Ff]or each ([^,.]{0,40})")),
    ("break zone count", _compile(r"(\d+) cards in your [Bb]reak [Zz]one")),
    ("generic", _compile(r"\b[Ii]f\b")),
]


def detect_conditions(text: str) -> list[Condition]:
    """Prerequisites, most specific first.

    The generic "If" only applies when no specific condition matched, which is
    what stops a card producing both `Control Ally` and `conditional` for the
    same clause.
    """
    found: list[Condition] = []
    for kind, pattern in CONDITION_RULES[:-1]:
        match = pattern.search(text)
        if match:
            detail = match.group(1).strip() if match.groups() else ""
            found.append(Condition(kind, detail))

    if not found:
        kind, pattern = CONDITION_RULES[-1]
        if pattern.search(text):
            found.append(Condition(kind))
    return found


#: Matches the restriction the previous version labelled 'Player Turn Only'.
YOUR_TURN_ONLY = _compile(r"only use this ability during your turn")

#: Sentences that restrict an ability rather than doing anything. They produce
#: no effect, so a naive parser files them as "not understood", and a card is
#: then reported as partly unparsed when in fact every clause was read.
#: They attach to the ability they qualify instead.
RESTRICTIONS: list[tuple[str, re.Pattern[str]]] = [
    ("your turn only", YOUR_TURN_ONLY),
    ("once per turn", _compile(r"only use this ability once per turn")),
    ("field only", _compile(r"while this card is (?:in play|on the field)")),
]


def detect_restriction(text: str) -> str | None:
    """The restriction a sentence expresses, if that is all it does."""
    for name, pattern in RESTRICTIONS:
        if pattern.search(text):
            return name
    return None
