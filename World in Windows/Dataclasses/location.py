from dataclasses import dataclass, field
from typing import List, Optional

from .npc import NPC
from .item import Item

@dataclass
class Location:
    name: str
    description: str
    region: Optional[str] = None
    npcs: List[NPC] = field(default_factory=list)
    loot: List[Item] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    parent: Optional['Location'] = None
    children: List['Location'] = field(default_factory=list)

    def add_npc(self, npc: NPC):
        if npc not in self.npcs:
            self.npcs.append(npc)

    def remove_npc(self, npc: NPC):
        if npc in self.npcs:
            self.npcs.remove(npc)

    def propagate_npcs_to_parent(self):
        """Propagate this location's NPCs to its parent location if they're not already there."""
        if self.parent is not None:
            for npc in self.npcs:
                if npc not in self.parent.npcs:
                    self.parent.npcs.append(npc)
            # Recursively propagate up the chain
            self.parent.propagate_npcs_to_parent()

    def get_npc_names(self) -> List[str]:
        return [npc.name for npc in self.npcs]
    
    def get_all_npcs_with_inheritance(self) -> List[NPC]:
        """Get all NPCs including those inherited from child locations."""
        all_npcs = list(self.npcs)  # Start with direct NPCs
        
        # Add NPCs from all child locations recursively
        for child in self.children:
            child_npcs = child.get_all_npcs_with_inheritance()
            for npc in child_npcs:
                if npc not in all_npcs:
                    all_npcs.append(npc)
        
        return all_npcs

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