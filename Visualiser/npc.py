from dataclasses import dataclass, field
from typing import List, Optional

from race import Race
from alignment import Alignment
from stat_block import StatBlock

@dataclass
class NPC:
    name: str
    race: Race
    sex: str
    age: str    # young | adult | middle-aged | old | venerable
    alignment: Alignment
    stat_block: StatBlock
    appearance: str
    backstory: str
    additional_traits: List[str]

    def __init__(self, name: str, race: Race, sex: str, age: str, alignment: Alignment, stat_block: StatBlock, appearance: str, backstory: str, additional_traits: Optional[List[str]] = None):
        self.name = name
        self.race = race
        self.sex = sex
        self.age = age
        self.alignment = alignment
        self.stat_block = stat_block
        self.appearance = appearance
        self.backstory = backstory
        self.additional_traits = additional_traits if additional_traits is not None else []

    def to_prompt(self) -> str:
        base_prompt = f"A full-length character portrait of a {self.age}, {self.sex} {self.race.value} who is {self.alignment.value} aligned."
        appearance_prompt = f" Appearance details: {self.appearance}."
        return base_prompt + appearance_prompt

    def to_summary(self) -> dict:
        return {
            "name": self.name,
            "race": self.race.value,
            "sex": self.sex,
            "age": self.age,
            "alignment": self.alignment.value,
            "appearance": self.appearance[:140] + ("..." if len(self.appearance) > 140 else "")
        }
    