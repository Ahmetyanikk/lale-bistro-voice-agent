"""Cross-checks the backend's canonical menu data (app/seed.py) against
olovoice/menu_facts.json — the machine-readable counterpart of the menu
table and vegetarian list in olovoice/knowledge_base.md. Comparing two
structured sources here instead of regex-parsing the markdown prose keeps
this test meaningful without being brittle.
"""

import json
from pathlib import Path

from app.seed import MENU_ITEMS, VEGETARIAN_ITEMS

MENU_FACTS_PATH = Path(__file__).resolve().parent.parent / "olovoice" / "menu_facts.json"


def _backend_facts() -> set[tuple[str, str, float, bool]]:
    return {
        (name, category, price, name in VEGETARIAN_ITEMS)
        for name, category, price, _description in MENU_ITEMS
    }


def _knowledge_base_facts() -> set[tuple[str, str, float, bool]]:
    facts = json.loads(MENU_FACTS_PATH.read_text(encoding="utf-8"))
    return {(f["name"], f["category"], f["price"], f["vegetarian"]) for f in facts}


def test_backend_seed_matches_knowledge_base_menu_facts():
    backend = _backend_facts()
    knowledge_base = _knowledge_base_facts()
    assert backend == knowledge_base


def test_every_vegetarian_item_is_a_real_menu_item():
    names = {name for name, _category, _price, _description in MENU_ITEMS}
    assert VEGETARIAN_ITEMS <= names
