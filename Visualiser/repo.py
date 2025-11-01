# repo.py (new)
import json, pathlib
from typing import Dict, List, Optional

from item import Item
from spell import Spell
from npc import NPC

DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)

class Repo:
    def __init__(self):
        self.items: Dict[str, Item] = {}
        self.spells: Dict[str, Spell] = {}
        self.npcs: Dict[str, NPC] = {}

    # --- load/save ---
    def load_all(self):
        self.items = {x["id"]: Item(**x) for x in self._load_json("items.json")}
        self.spells = {x["id"]: Spell(**x) for x in self._load_json("spells.json")}
        self.npcs   = {x.name: x for x in [NPC(**x) for x in self._load_json("npcs.json")]}

    def save_all(self):
        self._save_json("items.json", [vars(x) for x in self.items.values()])
        self._save_json("spells.json",[vars(x) for x in self.spells.values()])
        self._save_json("npcs.json",  [self._npc_to_dict(x) for x in self.npcs.values()])

    # --- resolution helpers (for hover + dialogs) ---
    def get_items_for_npc(self, npc: NPC) -> List[Item]:
        return [self.items[i] for i in npc.item_ids if i in self.items]

    def get_spells_for_npc(self, npc: NPC) -> List[Spell]:
        return [self.spells[s] for s in npc.spell_ids if s in self.spells]

    # --- private helpers ---
    def _load_json(self, name):
        p = DATA_DIR / name
        return json.loads(p.read_text("utf-8")) if p.exists() else []

    def _save_json(self, name, payload):
        (DATA_DIR / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _npc_to_dict(self, npc: NPC) -> dict:
        d = npc.__dict__.copy()
        d["race"] = npc.race.name
        d["alignment"] = npc.alignment.name
        d["stat_block"] = npc.stat_block.display() if hasattr(npc.stat_block, "display") else None
        return d
