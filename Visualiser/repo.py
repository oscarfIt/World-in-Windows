import json
from pathlib import Path
from typing import List, Type, TypeVar

from item import Item
from spell import Spell
from class_action import ClassAction
from npc import NPC

T = TypeVar("T", Spell, Item, ClassAction, NPC)

class Repo:
    def __init__(self, data_dir: str = "Data"):
        self.data_dir = Path(data_dir)
        self.spells: List[Spell] = []
        self.items: List[Item] = []
        self.class_actions: List[ClassAction] = []
        self.npcs: List[NPC] = []

    def load_all(self):
        self.spells = self._load_list("spells.json", Spell)
        self.items = self._load_list("items.json", Item)
        self.class_actions = self._load_list("class_actions.json", ClassAction)
        self.npcs   = self._load_list("npcs.json", NPC)

    def _load_list(self, filename: str, cls: Type[T]) -> List[T]:
        p = self.data_dir / filename
        if not p.exists():
            return []
        raw = json.loads(p.read_text(encoding="utf-8"))
        out: List[T] = []
        for i, d in enumerate(raw):
            try:
                # tolerate missing fields; dataclass defaults handle the rest
                out.append(cls(**d))
            except TypeError as e:
                print(f"[WARN] Skipping {filename}[{i}]: {e}")
        return out

    def save_all(self):
        return
        # self._save_json("items.json", [vars(x) for x in self.items.values()])
        # self._save_json("spells.json",[vars(x) for x in self.spells.values()])
        # self._save_json("npcs.json",  [self._npc_to_dict(x) for x in self.npcs.values()])

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
