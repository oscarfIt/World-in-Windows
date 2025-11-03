from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from stat_block import StatBlock
from spell import Spell

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
    spells: list[Spell] = field(default_factory=list)

    def __init__(self, name: PcClassName, level: int, spells: Optional[list[Spell]] = None):
        super().__init__(name.value + ", Level " + str(level))
        self.name = name
        self.level = level
        self.spells = spells if spells is not None else []

    def display(self):
        return {"type": "pc_class", "name": self.name.value, "level": self.level}

class Barbarian(PcClass):

    def __init__(self, level: int = 1):
        super().__init__(PcClassName.Barbarian, level)

class Bard(PcClass):
    def __init__(self, level: int = 1):
        super().__init__(PcClassName.Bard, level)

class Cleric(PcClass):
    def __init__(self, level: int = 1):
        super().__init__(PcClassName.Cleric, level)

class Druid(PcClass):
    def __init__(self, level: int = 1):
        super().__init__(PcClassName.Druid, level)

class Fighter(PcClass):
    def __init__(self, level: int = 1):
        super().__init__(PcClassName.Fighter, level)

class Monk(PcClass):
    def __init__(self, level: int = 1):
        super().__init__(PcClassName.Monk, level)

class Paladin(PcClass):
    def __init__(self, level: int = 1):
        super().__init__(PcClassName.Paladin, level)

class Ranger(PcClass):
    def __init__(self, level: int = 1):
        super().__init__(PcClassName.Ranger, level)

class Rogue(PcClass):
    def __init__(self, level: int = 1):
        super().__init__(PcClassName.Rogue, level)

class Sorcerer(PcClass):
    def __init__(self, level: int = 1):
        super().__init__(PcClassName.Sorcerer, level)

class Warlock(PcClass):
    def __init__(self, level: int = 1):
        super().__init__(PcClassName.Warlock, level)

class Wizard(PcClass):
    def __init__(self, level: int = 1):
        super().__init__(PcClassName.Wizard, level)


