from dataclasses import dataclass, field
from typing import List, Optional

from npc import NPC

@dataclass
class Location:
    name: str
    description: str
    region: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    npcs: List[NPC] = field(default_factory=list)

    parent: Optional['Location'] = None
    children: List['Location'] = field(default_factory=list)

    def add_npc(self, npc: NPC):
        if npc not in self.npcs:
            self.npcs.append(npc)

    def remove_npc(self, npc: NPC):
        if npc in self.npcs:
            self.npcs.remove(npc)

    def get_npc_names(self) -> List[str]:
        return [npc.name for npc in self.npcs]

    def add_child(self, child: "Location"):
        """Nest a child location under this location."""
        if child not in self.children:
            self.children.append(child)
            child.parent = self

    def short_description(self, max_len: int = 80) -> str:
        """Shortened description for list views/columns."""
        d = (self.description or "").strip()
        return (d if len(d) <= max_len else d[:max_len].rstrip() + "…")
 

    def summary(self) -> dict:
        return {
            "name": self.name,
            "region": self.region or "",
            "npc_count": len(self.npcs),
            "tags": self.tags
        }