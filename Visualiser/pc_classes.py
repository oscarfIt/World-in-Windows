from dataclasses import dataclass, field
from enum import Enum

from stat_block import StatBlock

class PcClassName(Enum):
    Barbarian = "Barbarian"
    Bard = "Bard"
    Cleric = "Cleric"
    Druid = "Druid"
    Fighter = "Fighter"
    Monk = "Monk"
    Paladin = "Paladin"
    Ranger = "Ranger"
    Rogue = "Rogue"
    Sorcerer = "Sorcerer"
    Warlock = "Warlock"
    Wizard = "Wizard"


@dataclass
class PcClass(StatBlock):
    name : PcClassName
    level : int

    def __init__(self, name: PcClassName, level: int):
        super().__init__()
        self.name = name
        self.level = level

    def display(self):
        return {"type": "pc_class", "name": self.name.value, "level": self.level}

class Barbarian(PcClass):
    pass

class Bard(PcClass):
    pass

class Cleric(PcClass):
    pass

class Druid(PcClass):
    pass

class Fighter(PcClass):
    pass

class Monk(PcClass):
    pass

class Paladin(PcClass):
    pass

class Ranger(PcClass):
    pass

class Rogue(PcClass):
    pass

class Sorcerer(PcClass):
    pass

class Warlock(PcClass):
    pass

class Wizard(PcClass):
    pass



