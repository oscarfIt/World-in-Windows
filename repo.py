import json
from pathlib import Path
from typing import List, Type, TypeVar, Dict, Optional

from .Dataclasses import Item, Spell, ClassAction, NPC, Race, Location, Condition, StatBlock, MonsterManual, PcClass, PcClassName, AbilityScores, Alignment

T = TypeVar("T", Spell, Item, ClassAction, NPC)

def _parse_enum(enum_cls, value: str):
    try:
        return enum_cls(value)
    except Exception:
        return getattr(enum_cls, value)

class Repo:
    def __init__(self, data_dir: str = "Data"):
        self.data_dir = Path(data_dir)
        self.spells: List[Spell] = []
        self.items: List[Item] = []
        self.class_actions: List[ClassAction] = []
        self.conditions: List[Condition] = []

        # NPCs & fast lookup maps
        self.npcs: List[NPC] = []
        self.npcs_by_id: Dict[str, NPC] = {}
        self.npcs_by_name: Dict[str, NPC] = {}

        # Items/Spells maps (by name) — useful for KB / linking
        self.items_by_name: Dict[str, Item] = {}
        self.spells_by_name: Dict[str, Spell] = {}
        self.class_actions_by_name: Dict[str, ClassAction] = {}
        self.conditions_by_name: Dict[str, Condition] = {}

        # Locations (top-level only; child locations reachable via .children)
        self.locations: List[Location] = []

    def load_all(self):
        self.spells = self._load_list("spells.json", Spell)
        self.items = self._load_list("items.json", Item)
        self.class_actions = self._load_list("class_actions.json", ClassAction)
        self.conditions = self._load_list("conditions.json", Condition)

        self.spells_by_name = {s.name: s for s in self.spells}
        self.items_by_name = {i.name: i for i in self.items}
        self.class_actions_by_name = {a.name: a for a in self.class_actions}
        self.conditions_by_name = {c.name: c for c in self.conditions}

        # 2) NPCs (build stat blocks from spec)
        npcs_raw = self._read_json("npcs.json")
        self._build_npcs(npcs_raw)

        # 3) Locations (create shells, attach NPCs, set nesting)
        locs_raw = self._read_json("locations.json")
        self._build_locations(locs_raw)

    def _read_json(self, filename: str):
        p = self.data_dir / filename
        if not p.exists():
            return []
        return json.loads(p.read_text(encoding="utf-8"))

    def _load_list(self, filename: str, cls):
        raw = self._read_json(filename)
        out = []
        for i, d in enumerate(raw):
            try:
                out.append(cls(**d))
            except TypeError as e:
                print(f"[WARN] Skipping {filename}[{i}]: {e}")
        return out


    def _build_npcs(self, npcs_raw: List[dict]) -> None:
        for i, row in enumerate(npcs_raw):
            try:
                sb = self._build_stat_block(row.get("stat_block"))

                # Accept additional_traits as list[str] OR list[dict] with 'description'
                add_traits = row.get("additional_traits", [])
                norm_traits = []
                for t in add_traits:
                    if isinstance(t, str):
                        norm_traits.append(t)
                    elif isinstance(t, dict) and "description" in t:
                        norm_traits.append(t["description"])

                # NPC constructor may be original or extended; handle both
                try:
                    npc = NPC(
                        name=row["name"],
                        race=_parse_enum(Race, row["race"]),
                        sex=row.get("sex", ""),
                        age=row.get("age", ""),
                        alignment=_parse_enum(Alignment, row["alignment"]),
                        stat_block=sb if sb is not None else StatBlock(),
                        appearance=row.get("appearance", ""),
                        backstory=row.get("backstory", ""),
                        additional_traits=norm_traits,  # works if your NPC supports it
                        campaign_notes=row.get("campaign_notes", ""),  # Include campaign notes
                        alive=row.get("alive", True)  # Include alive status
                    )
                except TypeError:
                    # Fallback to legacy signature (no additional_traits)
                    npc = NPC(
                        name=row["name"],
                        race=_parse_enum(Race, row["race"]),
                        sex=row.get("sex", ""),
                        age=row.get("age", ""),
                        alignment=_parse_enum(Alignment, row["alignment"]),
                        stat_block=sb if sb is not None else StatBlock(),
                        appearance=row.get("appearance", ""),
                        backstory=row.get("backstory", ""),
                    )
                    # attach as attribute for UI if needed
                    setattr(npc, "additional_traits", norm_traits)
                    setattr(npc, "campaign_notes", row.get("campaign_notes", ""))

                nid = row.get("id", row["name"])
                self.npcs.append(npc)
                self.npcs_by_id[nid] = npc
                self.npcs_by_name[npc.name] = npc

            except Exception as e:
                print(f"[WARN] Skipping npcs.json[{i}]: {e}")


    def _build_locations(self, locs_raw: List[dict]) -> None:
        # First pass: create Location shells
        loc_objs: Dict[str, Location] = {}
        for i, row in enumerate(locs_raw):
            try:
                loc = Location(
                    name=row["name"],
                    description=row.get("description", ""),
                    region=row.get("region"),
                    tags=row.get("tags", []),
                    npcs=[],
                )
                loc_objs[row.get("id", row["name"])] = loc
            except Exception as e:
                print(f"[WARN] Skipping locations.json[{i}] (shell): {e}")

        # Second pass: attach NPCs
        for row in locs_raw:
            loc = loc_objs.get(row.get("id", row["name"]))
            if not loc:
                continue
            for nid in row.get("npc_ids", []):
                npc = self.npcs_by_id.get(nid) or self.npcs_by_name.get(nid)
                if npc:
                    try:
                        loc.add_npc(npc)
                    except Exception:
                        # if not dataclass, ensure list append works
                        if npc not in loc.npcs:
                            loc.npcs.append(npc)

        # Third pass: establish nesting
        for row in locs_raw:
            parent = loc_objs.get(row.get("id", row["name"]))
            if not parent:
                continue
            for child_id in row.get("children", []):
                child = loc_objs.get(child_id)
                if child:
                    try:
                        parent.add_child(child)
                    except Exception:
                        # Fallback if add_child not present
                        child.parent = parent
                        parent.children = getattr(parent, "children", [])
                        if child not in parent.children:
                            parent.children.append(child)

        # Fourth pass: propagate NPCs from child to parent locations
        # Only propagate from leaf nodes (locations with no children) to avoid redundancy
        leaf_locations = [loc for loc in loc_objs.values() if not getattr(loc, 'children', [])]
        for loc in leaf_locations:
            if hasattr(loc, 'propagate_npcs_to_parent'):
                loc.propagate_npcs_to_parent()

        # Top-level locations (no parent)
        self.locations = [l for l in loc_objs.values() if getattr(l, "parent", None) is None]



    def _build_stat_block(self, spec: Optional[dict]) -> Optional[StatBlock]:
        if not spec:
            return None
        t = spec.get("type", "").lower()
        if t == "monstermanual":
            # The MonsterManual class will compose the image path from this name
            return MonsterManual(spec["monster_name"])
        if t == "pc_class":
            cls_name = PcClassName(spec.get("class", "Wizard"))
            level = int(spec.get("level", 1))
            ability_scores = AbilityScores(spec.get("ability_scores", {}))
            spells = spec.get("spells", [])
            pc = PcClass(cls_name, level, ability_scores, spells)
            return pc
        # Fallback to empty StatBlock
        return StatBlock()
    

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
