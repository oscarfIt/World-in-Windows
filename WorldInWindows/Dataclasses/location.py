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
    
    def get_children(self, all_locations: List['Location']) -> List['Location']:
        """Get all direct children of this location from a list of all locations."""
        return [loc for loc in all_locations if loc.parent == self]
    
    def get_all_descendants(self, all_locations: List['Location']) -> List['Location']:
        """Get all descendants (children, grandchildren, etc.) recursively."""
        descendants = []
        children = self.get_children(all_locations)
        for child in children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants(all_locations))
        return descendants

    def get_npc_names(self) -> List[str]:
        return [npc.name for npc in self.npcs]
    
    def get_all_npcs_with_inheritance(self, all_locations: List['Location']) -> List[NPC]:
        """Get all NPCs including those inherited from child locations."""
        all_npcs = list(self.npcs)  # Start with direct NPCs
        
        # Add NPCs from all child locations recursively
        for child in self.get_children(all_locations):
            child_npcs = child.get_all_npcs_with_inheritance(all_locations)
            for npc in child_npcs:
                if npc not in all_npcs:
                    all_npcs.append(npc)
        
        return all_npcs

    def set_parent(self, parent: Optional["Location"]):
        """Set the parent location."""
        self.parent = parent

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