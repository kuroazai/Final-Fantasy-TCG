"""Parsing rules text."""
from __future__ import annotations

from conftest import ZACK

from ffparse import Action, Controller, Trigger, parse
from ffparse.parser import extract_effects, normalise, split_sentences

# -- the amounts, which the previous version discarded ---------------------

def test_the_damage_amount_is_kept() -> None:
    """The headline fix. The old patterns captured the number and
    `classify_card_intents` returned only the label, so the parser knew a card
    dealt damage and not how much."""
    card = parse("Deal it 2000 damage.")
    effect = card.abilities[0].effects[0]
    assert effect.action is Action.DAMAGE
    assert effect.amount == 2000


def test_the_power_change_keeps_its_sign() -> None:
    assert parse("Zack gains +2000 power.").abilities[0].effects[0].amount == 2000
    assert parse("It loses 1000 power.").abilities[0].effects[0].amount == -1000


def test_a_power_pattern_that_could_never_match_now_does() -> None:
    """The pattern was written `gains +([^"]*) power` and compiled from a
    lowercased string. A later version wrote the `+` as `\\{0,1}`, which
    requires a literal "{0,1}" in the card text and can never match."""
    card = parse("Zack gains +2000 power.")
    assert card.abilities
    assert card.abilities[0].effects[0].amount == 2000


def test_thousands_separators_are_read() -> None:
    assert parse("Deal it 2,000 damage.").abilities[0].effects[0].amount == 2000


# -- targeting -------------------------------------------------------------

def test_whose_forward_it_is() -> None:
    """The old version gave "choose 1 Forward" and "choose 1 Forward opponent
    controls" the same label, and they are not the same card."""
    theirs = parse("Choose 1 Forward opponent controls.")
    assert theirs.abilities[0].effects[0].target.controller is Controller.OPPONENT

    anyones = parse("Choose 1 Forward.")
    assert anyones.abilities[0].effects[0].target.controller is Controller.ANY


def test_up_to_is_not_exactly() -> None:
    """"Choose up to 2" allows choosing one. "Choose 2" does not."""
    up_to = parse("Choose up to 2 Forwards opponent controls.")
    target = up_to.abilities[0].effects[0].target
    assert target.count == 2
    assert target.up_to

    exact = parse("Choose 2 Forwards opponent controls.")
    assert not exact.abilities[0].effects[0].target.up_to


def test_a_cost_restriction_is_captured() -> None:
    card = parse("Choose 1 Forward of cost 3 or less.")
    assert card.abilities[0].effects[0].target.max_cost == 3


def test_all_is_not_one() -> None:
    """`count=None` means all, which is not the same as a count of 1."""
    card = parse("Break all the Forwards.")
    targets = [e.target for a in card.abilities for e in a.effects if e.target]
    assert targets
    assert targets[0].count is None


# -- no redundant labels ---------------------------------------------------

def test_a_specific_condition_suppresses_the_generic_one() -> None:
    """The old output for this sentence was
    `['Control Ally', 'Gains Power', 'conditional']`. `conditional` fired for
    the same "If" that `Control Ally` had already explained, because `r'If'`
    sat in the same dict as `r'If you control ([^"]*),'` and both matched."""
    card = parse("If you control [Card Name (Aerith)], Zack gains +2000 power.")
    kinds = [c.kind for c in card.abilities[0].conditions]

    assert "controls" in kinds
    assert "generic" not in kinds


def test_the_generic_condition_still_fires_when_nothing_specific_matches() -> None:
    card = parse("If it is your turn, deal it 1000 damage.")
    assert any(c.kind == "generic" for c in card.abilities[0].conditions)


def test_a_specific_effect_suppresses_the_general_one() -> None:
    """"Dull them and Freeze them" is one effect, not three. The old version
    had `Dull and Freeze`, `Dull` and `Freeze` all matching."""
    card = parse("Dull them and Freeze them.")
    actions = card.actions
    assert actions == [Action.FREEZE]


def test_overlapping_matches_are_not_double_counted() -> None:
    card = parse("Choose 1 Forward of cost 3 or less.")
    # One targeting effect, not one for "choose n type" and one for the
    # cost-restricted variant.
    assert len(card.abilities[0].effects) == 1


# -- triggers --------------------------------------------------------------

def test_an_enters_field_trigger_is_detected() -> None:
    card = parse("When Zack enters the field, draw 1 card.")
    assert card.abilities[0].trigger is Trigger.ENTERS_FIELD


def test_a_trigger_carries_to_the_next_sentence() -> None:
    """"When Zack enters the field, choose 1 Forward. Deal it 2000 damage." is
    one triggered ability written as two sentences. Parsed independently the
    second becomes an unconditional 2000 damage, which is a different card."""
    card = parse(ZACK)
    triggered = [a for a in card.abilities if a.trigger is Trigger.ENTERS_FIELD]
    assert len(triggered) == 2
    assert any(e.action is Action.DAMAGE for a in triggered for e in a.effects)


def test_a_static_ability_before_a_trigger_stays_static() -> None:
    """The carry is forwards only. The power boost in Zack's first sentence is
    static and must not pick up the trigger from the sentence after it."""
    card = parse(ZACK)
    assert card.abilities[0].trigger is Trigger.STATIC


def test_leaves_field_is_distinct_from_enters_field() -> None:
    card = parse("When this card leaves the field, you lose 1000 power.")
    assert card.abilities[0].trigger is Trigger.LEAVES_FIELD


def test_ex_burst_is_a_trigger_and_a_keyword() -> None:
    card = parse("EX BURST When this card enters the field, draw 1 card.")
    assert card.abilities[0].trigger is Trigger.EX_BURST
    assert card.keywords


# -- restrictions ----------------------------------------------------------

def test_a_restriction_at_the_end_attaches_to_the_ability() -> None:
    """It produces no effect, so sentence-at-a-time parsing files it as not
    understood and the card looks partly unread when every clause was read."""
    card = parse("Discard 1 card: Choose 1 Backup. "
                 "You can only use this ability during your turn.")
    assert card.unparsed == []
    assert card.abilities[0].your_turn_only


def test_a_restriction_at_the_start_attaches_forwards() -> None:
    """Cards write it first as often as last."""
    card = parse("You can only use this ability during your turn. "
                 "Discard 1 card: Choose 1 Backup.")
    assert card.unparsed == []
    assert card.abilities[0].your_turn_only


def test_a_restriction_with_no_ability_is_reported() -> None:
    """Rather than silently dropped: it qualifies nothing, which is worth
    knowing."""
    card = parse("You can only use this ability during your turn.")
    assert card.abilities == []
    assert any("unattached restriction" in u for u in card.unparsed)


# -- honest output ---------------------------------------------------------

def test_flavour_text_is_reported_as_unparsed() -> None:
    """A parser reporting no misses on real data is not accurate, it is not
    looking."""
    card = parse("This card has flavour text only and no rules at all.")
    assert card.abilities == []
    assert len(card.unparsed) == 1
    assert card.coverage == 0.0


def test_coverage_is_the_fraction_of_sentences_understood() -> None:
    card = parse("Deal it 2000 damage. This is flavour text with no rules.")
    assert card.coverage == 0.5


def test_coverage_of_empty_text_is_zero_not_an_error() -> None:
    card = parse("")
    assert card.coverage == 0.0
    assert card.abilities == []


# -- the bits that are not NLP --------------------------------------------

def test_sentence_splitting_handles_pasted_newlines() -> None:
    """Card text is routinely pasted with newlines inside a sentence."""
    text = """If you control [Card Name (Aerith)],
              Zack gains +2000 power."""
    assert len(split_sentences(text)) == 1


def test_sentence_splitting_keeps_bracketed_openings_together() -> None:
    text = "Deal it 2000 damage. [Card Name (Aerith)] gains Haste."
    assert len(split_sentences(text)) == 2


def test_normalise_collapses_whitespace() -> None:
    assert normalise("  a\n\n  b\t c  ") == "a b c"


def test_effects_come_back_in_reading_order() -> None:
    """Rules are tried by specificity, so the matches have to be sorted back."""
    effects = extract_effects("Choose 1 Forward opponent controls and deal it 2000 damage")
    assert [e.action for e in effects] == [Action.SEARCH, Action.DAMAGE]


def test_the_pos_tagging_contributed_nothing() -> None:
    """The previous version ran `nltk.pos_tag(sent_tokenize(text))`.

    `pos_tag` takes a list of words; given sentences it labels each whole
    sentence `NNP`. The loop then used only `sentence[0]`, the text it had been
    given, so the tags were discarded too. This asserts the parse is complete
    without any of it, which is why nltk is no longer a dependency.
    """
    card = parse(ZACK)
    assert card.coverage == 1.0
    assert len(card.abilities) == 3
