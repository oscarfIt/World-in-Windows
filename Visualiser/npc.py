from dataclasses import dataclass, field
from typing import List, Optional

from race import Race
from alignment import Alignment
from stat_block import StatBlock
from additional_traits import AdditionalTrait

@dataclass
class NPC:
    name: str
    race: Race
    alignment: Alignment
    stat_block: StatBlock
    appearance: str
    backstory: str
    additional_traits: List[AdditionalTrait]
    # item_ids: List[str] = field(default_factory=list)
    # spell_ids: List[str] = field(default_factory=list)

    def __init__(self, name: str, race: Race, alignment: Alignment, stat_block: StatBlock, appearance: str, backstory: str, additional_traits: Optional[List[AdditionalTrait]] = None):
        self.name = name
        self.race = race
        self.alignment = alignment
        self.stat_block = stat_block
        self.appearance = appearance
        self.backstory = backstory
        self.additional_traits = additional_traits if additional_traits is not None else []

    def to_summary(self) -> dict:
        return {
            "name": self.name,
            "race": self.race.value,
            "alignment": self.alignment.value,
            "appearance": self.appearance[:140] + ("..." if len(self.appearance) > 140 else "")
        }
    