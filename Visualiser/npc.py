from dataclasses import dataclass, field
from typing import List

from race import Race
from alignment import Alignment
from stat_block import StatBlock

@dataclass
class NPC:
    name: str
    race: Race
    alignment: Alignment
    stat_block: StatBlock
    appearance: str
    backstory: str
    item_ids: List[str] = field(default_factory=list)
    spell_ids: List[str] = field(default_factory=list)

    def __init__(self, name: str, race: Race, alignment: Alignment, stat_block: StatBlock, appearance: str, backstory: str):
        self.name = name
        self.race = race
        self.alignment = alignment
        self.stat_block = stat_block
        self.appearance = appearance
        self.backstory = backstory

    def to_summary(self) -> dict:
        return {
            "name": self.name,
            "race": self.race.value,
            "alignment": self.alignment.value,
            "appearance": self.appearance[:140] + ("..." if len(self.appearance) > 140 else "")
        }
    