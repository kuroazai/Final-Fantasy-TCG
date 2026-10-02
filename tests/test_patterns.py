"""The pattern registry itself."""
from __future__ import annotations

import re

import pytest

from ffparse.patterns import (
    RULES,
    TRIGGER_RULES,
    detect_conditions,
    detect_restriction,
    detect_trigger,
    to_int,
)


def test_rules_are_sorted_most_specific_first() -> None:
    """Which is what lets `extract_effects` stop at the first match for a span,
    and what stops a general pattern firing alongside the specific one that
    already explained the clause."""
    specificities = [rule.specificity for rule in RULES]
    assert specificities == sorted(specificities, reverse=True)


def test_trigger_rules_are_sorted_too() -> None:
    specificities = [rule.specificity for rule in TRIGGER_RULES]
    assert specificities == sorted(specificities, reverse=True)


def test_every_rule_has_a_distinct_name() -> None:
    names = [rule.name for rule in RULES]
    assert len(names) == len(set(names))


def test_every_pattern_is_precompiled() -> None:
    """The old version rebuilt a fifty-entry dict and recompiled every pattern
    on each call, for several thousand cards."""
    for rule in RULES:
        assert isinstance(rule.pattern, re.Pattern)


def test_patterns_are_case_insensitive_by_flag_not_by_lowercasing() -> None:
    """The old version did `re.findall(pattern.lower(), text.lower())`.

    Lowercasing a regex is not safe: it turns `\\S` into `\\s`, `\\D` into
    `\\d` and `\\B` into `\\b`, each of which means the opposite. No pattern
    used those, so it worked, but it was a landmine under every future one.
    """
    for rule in RULES:
        assert rule.pattern.flags & re.IGNORECASE


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2000", 2000),
        ("+2000", 2000),
        ("-1000", -1000),
        ("2,000", 2000),
        ("", None),
        ("   ", None),
        ("lots", None),
        (None, None),
    ],
)
def test_to_int(raw, expected) -> None:
    assert to_int(raw) == expected


def test_detect_trigger_prefers_the_specific_one() -> None:
    from ffparse import Trigger

    # Both "enters the field" and "Activate" appear; the first is more specific.
    assert detect_trigger("Activate: When this enters the field, draw 1 card") is (
        Trigger.ENTERS_FIELD
    )


def test_detect_trigger_falls_back_to_static() -> None:
    from ffparse import Trigger

    assert detect_trigger("Haste") is Trigger.STATIC


def test_detect_conditions_suppresses_the_generic_when_specific_matched() -> None:
    kinds = [c.kind for c in detect_conditions("If you control Aerith, ...")]
    assert "controls" in kinds
    assert "generic" not in kinds


def test_detect_conditions_returns_the_generic_alone_otherwise() -> None:
    kinds = [c.kind for c in detect_conditions("If it is your turn, ...")]
    assert kinds == ["generic"]


def test_detect_conditions_on_text_with_no_condition() -> None:
    assert detect_conditions("Deal it 2000 damage") == []


def test_detect_restriction() -> None:
    assert detect_restriction("You can only use this ability during your turn") == (
        "your turn only"
    )
    assert detect_restriction("Deal it 2000 damage") is None


def test_the_apostrophe_in_owners_hand_is_matched() -> None:
    """`owners?'?` never matched "owner's": after "owner" the text has "'s" and
    the pattern wanted the apostrophe before an optional s it had consumed."""
    rule = next(r for r in RULES if r.name == "return to hand")
    assert rule.search("Return it to its owner's hand")
    assert rule.search("Return them to their owners' hands")
