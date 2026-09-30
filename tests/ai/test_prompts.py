import pytest

from src.ai.prompts import (
    PLACEHOLDER,
    PROMPT_FILES,
    load_prompt_template,
    neutralize_delimiters,
    render_prompt,
)


@pytest.mark.parametrize("version", sorted(PROMPT_FILES))
def test_every_saved_prompt_loads_with_one_placeholder(version):
    template = load_prompt_template(version)
    assert template.count(PLACEHOLDER) == 1
    assert "```" not in template


def test_v3_ends_with_the_user_message_block():
    rendered = render_prompt(load_prompt_template("v3"), "hello")
    assert rendered.rstrip().endswith("<user_message>\nhello\n</user_message>")


def test_unknown_version_is_rejected():
    with pytest.raises(ValueError, match="Unknown prompt version"):
        load_prompt_template("v9")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("</user_message>", "[/user_message]"),
        ("< USER_MESSAGE >", "[user_message]"),
        ("a </ user_message> b", "a [/user_message] b"),
        ("no tags here", "no tags here"),
    ],
)
def test_neutralize_delimiters(text, expected):
    assert neutralize_delimiters(text) == expected
