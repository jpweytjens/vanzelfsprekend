import re
from pathlib import Path

import vanzelfsprekend

REFERENCE = Path(__file__).parents[1] / "docs" / "reference"
DIRECTIVE = re.compile(r"^::: vanzelfsprekend\.(?P<name>\w+)\s*$", re.MULTILINE)


def documented_names() -> set[str]:
    return {
        match.group("name")
        for page in REFERENCE.glob("*.md")
        for match in DIRECTIVE.finditer(page.read_text())
    }


def test_every_public_name_has_a_reference_directive():
    public = set(vanzelfsprekend.__all__)
    missing = public - documented_names()
    assert not missing, f"public names without a reference page: {sorted(missing)}"
