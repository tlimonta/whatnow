"""Load the saved prompt versions from prompts/ so code and documentation never diverge."""

import re
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"
PROMPT_FILES = {
    "v1": "v1_initial_prompt.md",
    "v2": "v2_structured_prompt.md",
    "v3": "v3_uncertainty_prompt.md",
}
DEFAULT_PROMPT_VERSION = "v3"
PLACEHOLDER = "{user_message}"

_PROMPT_BLOCK = re.compile(r"^```text\n(.*?)^```", re.DOTALL | re.MULTILINE)
_DELIMITER_TAG = re.compile(r"<\s*(/?)\s*user_message\s*>", re.IGNORECASE)


def load_prompt_template(version: str = DEFAULT_PROMPT_VERSION) -> str:
    """Return the ```text block of a prompt file, which holds the prompt itself."""
    if version not in PROMPT_FILES:
        raise ValueError(f"Unknown prompt version {version!r}; expected one of {sorted(PROMPT_FILES)}")
    text = (PROMPTS_DIR / PROMPT_FILES[version]).read_text(encoding="utf-8")
    blocks = _PROMPT_BLOCK.findall(text)
    if len(blocks) != 1 or blocks[0].count(PLACEHOLDER) != 1:
        raise ValueError(f"{PROMPT_FILES[version]} must contain one ```text block with one {PLACEHOLDER}")
    return blocks[0]


def neutralize_delimiters(user_message: str) -> str:
    """Stop user text from closing or reopening the <user_message> block (V3 integration note)."""
    return _DELIMITER_TAG.sub(lambda m: f"[{m.group(1)}user_message]", user_message)


def render_prompt(template: str, user_message: str) -> str:
    # str.replace, not str.format: the templates contain JSON braces.
    return template.replace(PLACEHOLDER, user_message)
