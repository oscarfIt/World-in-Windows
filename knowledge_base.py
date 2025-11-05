# --- Hover knowledge base (minimal, inline for now) --------------------------
from dataclasses import dataclass
import re
from typing import Dict, Tuple, Optional, Iterable

from spell import Spell
from item import Item
from class_action import ClassAction
from npc import NPC
from condition import Condition

def _npc_summary(n: NPC, max_len=180) -> str:
    text = n.appearance.strip() or n.backstory.strip()
    return (text if len(text) <= max_len else text[:max_len].rstrip() + "…")

@dataclass
class KBEntry:
    content: Spell | Item | ClassAction | NPC | Condition
    name: str
    hover_description: str

class KnowledgeBase:
    def __init__(self):
        self.entries: Dict[str, KBEntry] = {}
        self._aliases: Dict[str, str] = {}         # alias(lower) → canonical key
        self._pattern: Optional[re.Pattern] = None # compiled linkify regex

    def add_entry(self, entry: KBEntry):
        key = entry.name
        self.entries[key] = entry
        # invalidate compiled pattern
        self._pattern = None

    def add_alias(self, alias: str, canonical_name: str):
        self._aliases[alias.lower()] = canonical_name
        self._pattern = None

    def create_kb_entry(self, content: Spell | Item | ClassAction | NPC | Condition) -> KBEntry:
        if isinstance(content, Spell) or isinstance(content, Item) or isinstance(content, ClassAction) or isinstance(content, Condition):
            desc = content.description.strip()
        elif isinstance(content, NPC):
            desc = _npc_summary(content)
        # return KBEntry(kind=kind, name=ability.name, description=ability.description)
        return KBEntry(content=content, name=content.name, hover_description=desc)

    # def add(self, kind: str, name: str, description: str):
    #     self.entries[name] = KBEntry(kind=kind, name=name, description=description)

    def resolve(self, label: str) -> Optional[KBEntry]:
        if label in self.entries:
            return self.entries[label]
        canon = self._aliases.get(label.lower())
        return self.entries.get(canon) if canon else None

    # def resolve(self, name: str) -> Optional[KBEntry]:
    #     return self.entries.get(name)

    def ingest(self, spells: Iterable[Spell], items: Iterable[Item], actions: Iterable[ClassAction]):
        for s in spells:
            self.add_entry(self.create_kb_entry(s))
            for a in getattr(s, "aliases", []):
                self.add_alias(a, s.name)

        for it in items:
            self.add_entry(self.create_kb_entry(it))
            for a in getattr(it, "aliases", []):
                self.add_alias(a, it.name)

        for ac in actions:
            self.add_entry(self.create_kb_entry(ac))
            for a in getattr(ac, "aliases", []):
                self.add_alias(a, ac.name)

    def ingest_npcs(self, npcs: Iterable[NPC], alias_key: str = "aliases"):
        for n in npcs:
            self.add_entry(KBEntry(content=n, name=n.name, hover_description=_npc_summary(n)))
            # If you store aliases with the NPC JSON, add them
            aliases = getattr(n, alias_key, None) or []
            for a in aliases:
                self.add_alias(a, n.name)

    def ingest_conditions(self, conditions: Iterable[Condition]):
        for c in conditions:
            self.add_entry(self.create_kb_entry(c))
            # Add common aliases for conditions if needed
            for a in getattr(c, "aliases", []):
                self.add_alias(a, c.name)

    def _compile_pattern(self):
        # Build a single regex of all keys + aliases, longest-first.
        labels = set(self.entries.keys())
        labels.update(self._aliases.keys())
        if not labels:
            self._pattern = None
            return
        parts = sorted((re.escape(x) for x in labels), key=len, reverse=True)
        # Use word boundaries where possible; allow spaces in multi-word names.
        self._pattern = re.compile(r'(?<!\w)(' + "|".join(parts) + r')(?!\w)', flags=re.IGNORECASE)

    def linkify(self, text: str) -> str:
        if self._pattern is None:
            self._compile_pattern()
        if not self._pattern:
            return text

        def repl(m: re.Match):
            label = m.group(1)
            # Keep the original casing for display; href uses the canonical lookup label
            # We’ll resolve case-insensitively in _on_link_hovered/_on_anchor_clicked
            return f'<a href="{label}">{label}</a>'
        
        return self._pattern.sub(repl, text)

    # def linkify(self, text: str) -> str:
    #     """
    #     Replace any known entry names in `text` with HTML anchors.
    #     Longest-first to avoid partial overlaps.
    #     """
    #     if not self.entries:
    #         return text
    #     # Escape names for regex, sort by length desc
    #     names = sorted((re.escape(k) for k in self.entries.keys()),
    #                    key=len, reverse=True)
    #     # Use word boundaries where sensible (handles multi-word too)
    #     pattern = re.compile(r'(?<!\w)(' + '|'.join(names) + r')(?!\w)')
    #     def repl(m):
    #         label = m.group(1)
    #         # href contains the plain name; we'll parse it later
    #         return f'<a href="{label}">{label}</a>'
    #     # Basic HTML wrapping; convert newlines if you use multi-line traits
    #     html = pattern.sub(repl, text)
    #     return html
