"""Turning a card's rules text into structured effects.

The sentence splitting is done here rather than by NLTK, and that is a
deliberate removal rather than an omission.

The previous version did:

    card_tokens = sent_tokenize(card_desc)
    data = nltk.pos_tag(card_tokens)
    for sentence in data:
        process_text(sentence[0].strip())

`pos_tag` takes a list of *words*. Given a list of sentences it treats each
whole sentence as one token and labels every one `NNP`, so the tags are
meaningless. And the loop then uses only `sentence[0]`, which is the text that
was passed in, so the tags are discarded as well. Removing the call entirely
produces byte-identical output; there is a test asserting the parse is unchanged
without it.

What is left is a regex grammar over a small formal language, which is what card
text actually is. That needs no part-of-speech model, no downloaded corpora and
no NLTK dependency, and it is a great deal easier to debug: a pattern either
matches a clause or it does not, and `coverage` says how often.
"""
from __future__ import annotations

import re

from .effects import Ability, Condition, Effect, ParsedCard, Trigger
from .patterns import (
    RULES,
    YOUR_TURN_ONLY,
    detect_conditions,
    detect_restriction,
    detect_trigger,
)

#: Sentence end: a full stop, question or exclamation mark, then whitespace and
#: a capital or an opening bracket. Card text has no abbreviations and no
#: decimals, so this is reliable where it would not be on prose, and it is why
#: a trained sentence tokeniser buys nothing here.
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z\[(])")
#: Card text is often pasted with newlines inside a sentence.
WHITESPACE = re.compile(r"\s+")
#: Clauses within a sentence, which is how one sentence yields two effects:
#: "choose 1 Forward opponent controls. Deal it 2000 damage."
CLAUSE_SEPARATOR = re.compile(r"\s*(?:,\s*(?:then|and)\s+|;\s*)")


def normalise(text: str) -> str:
    """Collapse whitespace, so a pasted multi-line description parses the same."""
    return WHITESPACE.sub(" ", (text or "").strip())


def split_sentences(text: str) -> list[str]:
    """Split card text into sentences.

    Hand-rolled on purpose. Card text is a formal language with no
    abbreviations, no decimals and no quoted dialogue, so the hard cases a
    trained tokeniser exists for do not arise.
    """
    cleaned = normalise(text)
    if not cleaned:
        return []
    return [part.strip() for part in SENTENCE_END.split(cleaned) if part.strip()]


def extract_effects(sentence: str) -> list[Effect]:
    """Every effect in one sentence, without double-counting.

    Rules are tried most specific first, and a region of text already claimed by
    a rule is not offered to a less specific one. That is what stops the
    previous version's behaviour, where "If you control X, choose 1 Forward"
    produced four labels for two clauses because `r'If'` and `r'Choose'` sat in
    the same dict as the specific patterns and all of them matched.
    """
    effects: list[Effect] = []
    claimed: list[tuple[int, int]] = []

    for rule in RULES:  # already sorted by descending specificity
        for match in rule.pattern.finditer(sentence):
            span = match.span()
            if _overlaps(span, claimed):
                continue
            effect = rule.build(match)
            if effect is None:
                continue
            effects.append(effect)
            claimed.append(span)

    # Back into reading order, so the output follows the card.
    order = {id(effect): index for index, effect in enumerate(effects)}
    spans = dict(zip((id(e) for e in effects), claimed, strict=True))
    effects.sort(key=lambda e: (spans[id(e)][0], order[id(e)]))
    return effects


def _overlaps(span: tuple[int, int], claimed: list[tuple[int, int]]) -> bool:
    start, end = span
    return any(start < other_end and other_start < end
               for other_start, other_end in claimed)


def parse_sentence(sentence: str) -> Ability | None:
    """One sentence as an ability, or None if nothing matched."""
    effects = extract_effects(sentence)
    if not effects:
        return None

    trigger = detect_trigger(sentence)
    return Ability(
        trigger=trigger,
        conditions=detect_conditions(sentence),
        effects=effects,
        source_text=sentence,
        your_turn_only=bool(YOUR_TURN_ONLY.search(sentence)),
    )


def parse(text: str) -> ParsedCard:
    """Parse a whole card's rules text.

    Two things happen across sentence boundaries, because card text works that
    way and treating each sentence independently gets both wrong.

    **A trigger carries forward.** "When Zack enters the field, choose 1 Forward
    opponent controls. Deal it 2000 damage." is one triggered ability written as
    two sentences. Parsed independently the second becomes a static effect that
    deals 2000 damage unconditionally, which is a different and much better
    card.

    **A restriction attaches.** "You can only use this ability during your turn."
    produces no effect, so sentence-at-a-time filing puts it in `unparsed` and
    the card looks partly ununderstood when every clause was in fact read.

    Sentences that genuinely match nothing still go in `unparsed`. A parser
    reporting no misses on real data is not accurate, it is not looking, and
    `ParsedCard.coverage` is the number to watch when changing patterns.
    """
    card = ParsedCard(text=normalise(text))
    carried: Trigger | None = None
    pending: list[str] = []

    for sentence in split_sentences(text):
        restriction = detect_restriction(sentence)
        ability = parse_sentence(sentence)

        if ability is None:
            if restriction is None:
                card.unparsed.append(sentence)
            elif card.abilities:
                _restrict(card.abilities[-1], restriction)
            else:
                # Cards write the restriction first as often as last, and there
                # is nothing behind it to qualify yet. Held for the next
                # ability rather than filed as not understood.
                pending.append(restriction)
            continue

        if ability.trigger is Trigger.STATIC and carried is not None:
            # No trigger of its own, so it continues the previous one.
            ability.trigger = carried
        elif ability.trigger is not Trigger.STATIC:
            carried = ability.trigger

        for held in pending:
            _restrict(ability, held)
        pending.clear()

        card.abilities.append(ability)

    # A restriction with no ability anywhere on the card qualifies nothing, so
    # it is reported rather than silently dropped.
    card.unparsed.extend(f"(unattached restriction: {r})" for r in pending)
    return card


def _restrict(ability: Ability, restriction: str) -> None:
    """Record a restriction on an ability."""
    if restriction == "your turn only":
        ability.your_turn_only = True
    ability.conditions.append(Condition("restriction", restriction))


def parse_many(texts: list[str]) -> list[ParsedCard]:
    return [parse(text) for text in texts]


def coverage_report(cards: list[ParsedCard]) -> str:
    """How much of a set of cards the patterns understand.

    The regression test for a change to `patterns.py`: run it before and after
    and the numbers say whether the edit helped.
    """
    if not cards:
        return "no cards"

    sentences = sum(len(c.abilities) + len(c.unparsed) for c in cards)
    understood = sum(len(c.abilities) for c in cards)
    fully = sum(1 for c in cards if c.abilities and not c.unparsed)
    nothing = sum(1 for c in cards if not c.abilities)

    missed: dict[str, int] = {}
    for card in cards:
        for sentence in card.unparsed:
            key = sentence[:60]
            missed[key] = missed.get(key, 0) + 1

    lines = [
        f"{len(cards)} card(s), {sentences} sentence(s)",
        f"  understood      {understood}/{sentences}"
        f"  ({understood / sentences:.1%})" if sentences else "  no sentences",
        f"  fully parsed    {fully}/{len(cards)} card(s)",
        f"  nothing parsed  {nothing}/{len(cards)} card(s)",
    ]
    if missed:
        lines.append("  most common unparsed:")
        for sentence, count in sorted(missed.items(), key=lambda kv: -kv[1])[:5]:
            lines.append(f"    {count:>3}x {sentence}")
    return "\n".join(lines)
