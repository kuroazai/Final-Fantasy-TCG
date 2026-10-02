# ffparse

Final Fantasy TCG rules text, turned into data you can reason about.

Card text is a small formal language wearing English as a costume. "When Zack
enters the field, choose 1 Forward opponent controls. Deal it 2000 damage." has
a trigger, a target and an effect with a magnitude, and anything that wants to
evaluate a board needs all three.

```bash
pip install -e ".[dev]"
ffparse text "When Zack enters the field, choose 1 Forward opponent controls. Deal it 2000 damage."
```

```
2 ability(ies), coverage 100%
[enters_field]
  search -> 1 Forward (opponent)
[enters_field]
  damage 2000
```

No dependencies. Card text needs a regex grammar, not a language model.

---

## What you get

```python
from ffparse import parse

card = parse("If you control [Card Name (Aerith)], Zack gains +2000 power.")
effect = card.abilities[0].effects[0]

effect.action        # Action.MODIFY_POWER
effect.amount        # 2000
card.abilities[0].conditions[0].detail   # "[Card Name (Aerith)]"
```

The amounts and the targets are the point. A card that deals damage is not
usable information; a card that deals 2000 damage to a Forward the opponent
controls is.

The previous version returned a list of labels:

```python
['Control Ally', 'Gains Power', 'conditional']
```

Its patterns captured the numbers, and then `classify_card_intents` kept only
the label and discarded every capture group. So the parser knew a card dealt
damage and not how much, which is the half that matters.

It also produced three labels for two clauses: `conditional` fired for the same
"If" that `Control Ally` had already explained, because `r'If'` sat in the same
flat dict as `r'If you control ([^"]*),'` and both matched. `r'ability'` matched
inside "abilities", so both fired too.

Here every rule declares a specificity, the most specific match for a span of
text wins, and a general rule only sees text no specific one claimed.

## Why there is no NLTK

The previous version did this:

```python
card_tokens = sent_tokenize(card_desc)
data = nltk.pos_tag(card_tokens)
for sentence in data:
    process_text(sentence[0].strip())
```

`pos_tag` takes a list of **words**. Given a list of sentences it treats each
whole sentence as a single token and labels every one `NNP`. The tags are
meaningless. And the loop then uses only `sentence[0]`, which is the text that
was passed in, so the tags are discarded as well.

Removing the call produces byte-identical output. There is a test asserting the
parse is complete without it, which is why `nltk` is no longer a dependency and
no corpora are downloaded.

What replaced it is a sentence splitter of one regex. Card text has no
abbreviations, no decimals and no quoted dialogue, so the hard cases a trained
tokeniser exists for do not arise, and a pattern that either matches a clause or
does not is a great deal easier to debug than a tagger that is quietly wrong.

## Coverage, which is the number that matters

A parser that reports no misses on real data is not accurate, it is not looking.
So unparsed sentences are kept and counted:

```bash
$ ffparse coverage cards.json
7 card(s), 7 with rules text

7 card(s), 13 sentence(s)
  understood      12/13  (92.3%)
  fully parsed    6/7 card(s)
  nothing parsed  1/7 card(s)
  most common unparsed:
      1x This card has flavour text only and no rules at all.
```

That is the test fixture, which is the only card set measured here: a full card
dump is Square Enix's data and is not shipped with this repository. Point it at
your own and the same report tells you where the patterns fall short on the sets
you care about.

The one miss above is flavour text with no rules in it, which *should* be
unparsed.

Run it before and after editing `patterns.py` and the numbers say whether the
edit helped. The previous version had no equivalent, so there was no way to tell
an improvement from a regression.

## Two things that cross sentence boundaries

Card text works this way, and treating each sentence independently gets both
wrong.

**A trigger carries forward.** "When Zack enters the field, choose 1 Forward
opponent controls. Deal it 2000 damage." is one triggered ability written as two
sentences. Parsed independently the second becomes a static effect dealing 2000
damage unconditionally, which is a different and much better card.

**A restriction attaches.** "You can only use this ability during your turn."
produces no effect at all, so sentence-at-a-time filing puts it in `unparsed`
and the card looks half-understood when every clause was read. It attaches to
the ability it qualifies, forwards or backwards, since cards write it at either
end. A restriction with no ability anywhere on the card is reported rather than
dropped, because it qualifies nothing and that is worth knowing.

## The card model

```python
from ffparse import Card

card = Card.from_api(payload)   # the API's own field names, numbers as strings
card.cost        # 5, an int
card.parsed()    # the structured text
```

The previous model declared twenty typed dataclass fields and then wrote its own
`__init__`:

```python
@dataclass(order=True)
class Card:
    sort_index: str = field(init=True, repr=False)
    name: str
    ...
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
```

A custom `__init__` replaces the one the decorator generates, so every field
declaration was decorative. `Card(nonsense=1)` succeeded and produced an object
with no `name`, no types and no required fields.

It also had `def _post_init__` — one underscore short of `__post_init__` — so
`sort_index` was never assigned. `order=True` sorts on the first field, so
comparing any two cards raised:

```
AttributeError: 'Card' object has no attribute 'sort_index'
```

Both fixed by deleting the custom `__init__`. `from_api` handles the untidy keys
and string-typed numbers the API actually returns, and ignores fields it does
not know rather than setting them as attributes, so a renamed API field is not a
silently missing one.

`Deck` enforces the rules the game imposes: exactly 50 cards, at most 3 copies
by name. The old model had a `card_limit` field and nothing that used it.

## Commands

```bash
ffparse text "<rules text>"       parse text; --json for machine output
ffparse card cards.json --name Zack
ffparse coverage cards.json       how much of a set the patterns read
ffparse rules                     every pattern, by specificity
```

`text` exits 2 when something was not understood, so it can gate a script.
`card` accepts a JSON list or an object keyed by card code, which is how the
official API and the community dumps differ.

## Layout

```
src/ffparse/
├── effects.py    the vocabulary: Trigger, Action, Target, Effect, Ability
├── patterns.py   the rules, compiled once, ordered by specificity
├── parser.py     sentences in, structured abilities out
├── models.py     Card and Deck
└── cli.py        the commands
```

## Development

```bash
pip install -e ".[dev]"
pytest              # 80 tests
ruff check src tests
mypy
```

The test fixtures are real card wording. Invented text that happens to match the
patterns proves nothing about a parser.

CI asserts the package has no runtime dependencies, by importing every module
and checking that `nltk`, `openai`, `langchain`, `selenium`, `requests`, `redis`,
`pymongo` and `bs4` are all absent from `sys.modules`. The previous
`requirements.txt` required every one of them, and the part that worked was
regex over card text.

## What this is not

The repository's original goal was an agent that plays the game. That part was
aspiration: `openai_player.py` was a class of `pass` statements, `config.py` and
`prepare_db.py` were empty files, and the OpenAI key in `main.py` was the
literal string `'YOUR_API_KEY'`. Those are gone.

What was actually built, and is worth having, is the layer underneath: a reader
that turns card text into effects a rules engine could evaluate. That is the
hard and reusable half, and an agent is a great deal easier to write on top of
structured effects than on top of a list of labels.

## Licence

MIT. See [LICENSE](LICENSE). Final Fantasy and the card game are Square Enix's;
this parses text, and ships none of it.
