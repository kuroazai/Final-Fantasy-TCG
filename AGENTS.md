# AGENTS.md

Notes for anyone, human or otherwise, changing this code.

## What this is

A parser for Final Fantasy TCG rules text. Text in, structured effects out. No
dependencies, no network, no model.

Four modules and one direction of flow:

```
effects.py    the vocabulary. Nothing imports upward from here.
patterns.py   regexes, each with a builder that makes an Effect
parser.py     sentence splitting, specificity resolution, cross-sentence rules
models.py     Card and Deck, which call parse()
```

## Start here

```bash
pip install -e ".[dev]"
pytest
ffparse rules
ffparse text "When Zack enters the field, deal it 2000 damage."
```

`ffparse rules` prints every pattern with its specificity, which is the thing to
look at before adding one.

## The rules that matter

**Keep the captured values.** The whole reason this exists is that the previous
version matched `Deal it ([^"]*) damage`, captured "2000", and returned the
string `'Deal it damage'`. An `Effect` carries its `amount`, its `target` and
the text it came from. A rule that drops a number it matched is not finished.

**Specificity, not insertion order.** Every `Rule` declares one, `RULES` is
sorted descending, and `extract_effects` will not offer a span of text to a less
specific rule once a more specific one has claimed it. That is what stops
`r'If'` firing alongside `r'If you control ([^"]*),'`, which is what produced
three labels for two clauses before.

**Compile once, and use `re.IGNORECASE`.** Never lowercase a pattern string.
The previous version did `re.findall(pattern.lower(), text.lower())`, which
turns `\S` into `\s`, `\D` into `\d` and `\B` into `\b` — each the opposite of
what was written. No pattern used those, so it worked, and it was a landmine
under every future one. There is a test asserting every rule carries the flag.

**Report what you did not understand.** `ParsedCard.unparsed` and `coverage`
exist so a change to `patterns.py` can be measured. A parser that reports no
misses on real card text is not accurate, it is not looking. Run
`ffparse coverage` on a card dump before and after an edit.

**No dependencies.** CI asserts it, by importing every module and checking
`nltk`, `openai`, `langchain`, `selenium`, `requests`, `redis`, `pymongo` and
`bs4` are absent from `sys.modules`. If you find yourself wanting one, ask what
it would do that a regex over a formal language does not.

**ASCII output.** An em-dash crashes a legacy Windows console code page.

**3.10 is the floor.** No `datetime.UTC`, `StrEnum` or `tomllib`. mypy targets
3.10 here and will catch it; there are no third-party stubs to get in the way.

## Adding a pattern

1. Write it in `patterns.py` with a builder returning an `Effect`.
2. Give it a specificity. Higher means more specific. A rule that reads a number
   and a target belongs above 85; a bare keyword match belongs below 65.
3. Add a test with **real card wording**. Invented text that happens to match
   proves nothing.
4. Run `ffparse coverage` on a card dump. If the number went down, the new rule
   is claiming text a better rule was handling.

Check the existing specificities first. A new rule inserted at the wrong level
will shadow a more specific one, and the symptom is a card losing detail rather
than an error.

## Why the sentence splitter is hand-rolled

It is one regex, and that is on purpose. Card text has no abbreviations, no
decimals and no quoted dialogue, so the cases a trained tokeniser exists for do
not arise. The previous version used `nltk.sent_tokenize` and then
`nltk.pos_tag` on the *sentences*, which labels each whole sentence `NNP` and is
meaningless, and then discarded the tags anyway. `test_the_pos_tagging_contributed_nothing`
pins that the parse is complete without any of it.

## Things that look like bugs and are not

- A trigger carries from one sentence to the next. "When X enters the field,
  choose 1 Forward. Deal it 2000 damage." is one ability in two sentences, and
  parsing them independently makes the second an unconditional 2000 damage. The
  carry is forwards only, so a static ability written before a triggered one
  stays static.
- `Target.count` of `None` means "all", which is not the same as 1. "Break all
  the Forwards" is not "Break 1 Forward".
- A restriction sentence produces no `Effect`. It attaches to the ability it
  qualifies instead, in either direction, and one with no ability anywhere on
  the card is reported as unattached rather than dropped.
- `Card.parsed()` reparses on every call rather than caching. It is cheap, and
  caching would go stale the moment `text` is reassigned; there is a test.
- `OWNERS` is spelled out as `owner(?:'s|s'|s)?` rather than `owners?'?`. The
  obvious form never matches "owner's", because after "owner" the text has "'s"
  and the pattern wants the apostrophe before an s it has already consumed.
- `ffparse text` exits 2 when something is unparsed. That is a signal, not a
  failure, so it can gate a script.
