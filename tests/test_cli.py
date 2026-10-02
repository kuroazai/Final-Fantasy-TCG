"""The command line."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import ZACK

from ffparse.cli import build_parser, main


def test_every_subcommand_has_a_handler() -> None:
    parser = build_parser()
    actions = [a for a in parser._actions if isinstance(getattr(a, "choices", None), dict)]
    assert actions
    for action in actions:
        for name, sub in action.choices.items():
            assert sub.get_default("handler") is not None, f"{name} has no handler"


def test_text_parses_and_exits_zero(capsys) -> None:
    assert main(["text", ZACK]) == 0
    printed = capsys.readouterr().out
    assert "enters_field" in printed
    assert "damage 2000" in printed


def test_text_exits_two_when_something_is_not_understood(capsys) -> None:
    """So it can gate a script."""
    assert main(["text", "This is flavour text with no rules."]) == 2
    assert "not understood" in capsys.readouterr().out


def test_text_json_is_valid_json(capsys) -> None:
    main(["text", ZACK, "--json"])
    printed = capsys.readouterr().out
    payload = json.loads(printed[printed.index("{"):])

    assert payload["coverage"] == 1.0
    assert len(payload["abilities"]) == 3
    damage = [
        effect
        for ability in payload["abilities"]
        for effect in ability["effects"]
        if effect["action"] == "damage"
    ]
    assert damage[0]["amount"] == 2000


def test_rules_lists_the_patterns_by_specificity(capsys) -> None:
    assert main(["rules"]) == 0
    printed = capsys.readouterr().out
    assert "effect rule(s)" in printed
    assert "trigger rule(s)" in printed


def test_card_reads_a_json_list(tmp_path: Path, capsys) -> None:
    path = tmp_path / "cards.json"
    path.write_text(json.dumps([
        {"Name_EN": "Zack", "Text_EN": ZACK, "Cost": "5"},
        {"Name_EN": "Cloud", "Text_EN": "Haste.", "Cost": "4"},
    ]), encoding="utf-8")

    assert main(["card", str(path)]) == 0
    printed = capsys.readouterr().out
    assert "Zack" in printed
    assert "Cloud" in printed


def test_card_reads_a_keyed_object(tmp_path: Path, capsys) -> None:
    """Community dumps are keyed by card code rather than being a list."""
    path = tmp_path / "cards.json"
    path.write_text(json.dumps({
        "1-100L": {"Name_EN": "Zack", "Text_EN": "Haste."},
    }), encoding="utf-8")

    assert main(["card", str(path)]) == 0
    assert "Zack" in capsys.readouterr().out


def test_card_filters_by_name(tmp_path: Path, capsys) -> None:
    path = tmp_path / "cards.json"
    path.write_text(json.dumps([
        {"Name_EN": "Zack", "Text_EN": "Haste."},
        {"Name_EN": "Cloud", "Text_EN": "Brave."},
    ]), encoding="utf-8")

    main(["card", str(path), "--name", "zack"])
    printed = capsys.readouterr().out
    assert "Zack" in printed
    assert "Cloud" not in printed


def test_card_on_a_name_that_matches_nothing(tmp_path: Path, capsys) -> None:
    path = tmp_path / "cards.json"
    path.write_text(json.dumps([{"Name_EN": "Zack"}]), encoding="utf-8")
    assert main(["card", str(path), "--name", "sephiroth"]) == 1
    assert "no card matching" in capsys.readouterr().out


def test_coverage_reports_over_a_set(tmp_path: Path, capsys) -> None:
    path = tmp_path / "cards.json"
    path.write_text(json.dumps([
        {"Name_EN": "Zack", "Text_EN": ZACK},
        {"Name_EN": "Flavour", "Text_EN": "Just flavour text here."},
        {"Name_EN": "No text", "Text_EN": ""},
    ]), encoding="utf-8")

    assert main(["coverage", str(path)]) == 0
    printed = capsys.readouterr().out
    assert "3 card(s), 2 with rules text" in printed
    assert "understood" in printed


def test_a_missing_file_says_so(capsys, tmp_path: Path) -> None:
    assert main(["card", str(tmp_path / "absent.json")]) == 1
    assert "no card file" in capsys.readouterr().out


def test_invalid_json_says_so(tmp_path: Path, capsys) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    assert main(["card", str(path)]) == 1


def test_json_that_is_not_cards_says_so(tmp_path: Path, capsys) -> None:
    path = tmp_path / "wrong.json"
    path.write_text(json.dumps("just a string"), encoding="utf-8")
    assert main(["card", str(path)]) == 1
    assert "does not hold a list" in capsys.readouterr().out


def test_an_unknown_command_exits() -> None:
    with pytest.raises(SystemExit):
        main(["nonsense"])


def test_output_is_ascii(capsys) -> None:
    """An em-dash crashes a legacy Windows console code page."""
    main(["text", ZACK])
    capsys.readouterr().out.encode("ascii")
    main(["rules"])
    capsys.readouterr().out.encode("ascii")
