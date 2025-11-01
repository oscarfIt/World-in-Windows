from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class Rarity(Enum):
    Common = "Common"
    Uncommon = "Uncommon"
    Rare = "Rare"
    Very_Rare = "Very Rare"
    Legendary = "Legendary"
    Artifact = "Artifact"

@dataclass
class Item:
    id: str
    name: str
    rarity: Rarity
    description: str
    attunement: bool = False
    tags: List[str] = field(default_factory=list)
