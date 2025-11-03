from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from stat_block import StatBlock
from spell import Spell, SpellSlot

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

class CasterType(Enum):
    Full = "Full"
    Half = "Half"
    Third = "Third"
    Pact = "Pact"
    NoneType = "None"


@dataclass
class PcClass(StatBlock):
    name : PcClassName
    level : int
    caster_type: CasterType
    spells: list[Spell] = field(default_factory=list)
    spell_slots: list[SpellSlot] = field(default_factory=list)

    def __init__(self, name: PcClassName, level: int, spells: Optional[list[Spell]] = None):
        super().__init__(name.value + ", Level " + str(level))
        self.name = name
        self.level = level
        self.caster_type = self.determine_caster_type(name)
        self.spells = spells if spells is not None else []
        self.spell_slots = self.determine_spell_slots(level, self.caster_type)

    def determine_caster_type(self, name: PcClassName) -> CasterType:
        match name:
            case PcClassName.Bard | PcClassName.Cleric | PcClassName.Druid | PcClassName.Sorcerer | PcClassName.Wizard:
                return CasterType.Full
            case PcClassName.Paladin | PcClassName.Ranger:
                return CasterType.Half
            # case PcClassName.Rogue:   Need subclass implementation for this
            #     return CasterType.Third
            case PcClassName.Warlock:
                return CasterType.Pact
            case _:
                return CasterType.NoneType

    # Implemented up to level 12
    def determine_spell_slots(self, level: int, caster_type: CasterType) -> list[SpellSlot]:
        match caster_type:
            case CasterType.Full:
                match level:
                    case 1:
                        return [SpellSlot(1, 2)]
                    case 2:
                        return [SpellSlot(1, 3)]
                    case 3:
                        return [SpellSlot(1, 4), SpellSlot(2, 2)]
                    case 4:
                        return [SpellSlot(1, 4), SpellSlot(2, 3)]
                    case 5:
                        return [SpellSlot(1, 4), SpellSlot(2, 3), SpellSlot(3, 2)]
                    case 6:
                        return [SpellSlot(1, 4), SpellSlot(2, 3), SpellSlot(3, 3)]
                    case 7:
                        return [SpellSlot(1, 4), SpellSlot(2, 3), SpellSlot(3, 3), SpellSlot(4, 1)]
                    case 8:
                        return [SpellSlot(1, 4), SpellSlot(2, 3), SpellSlot(3, 3), SpellSlot(4, 2)]
                    case 9:
                        return [SpellSlot(1, 4), SpellSlot(2, 3), SpellSlot(3, 3), SpellSlot(4, 3), SpellSlot(5, 1)]
                    case 10:
                        return [SpellSlot(1, 4), SpellSlot(2, 3), SpellSlot(3, 3), SpellSlot(4, 3), SpellSlot(5, 2)]
                    case 11 | 12:
                        return [SpellSlot(1, 4), SpellSlot(2, 3), SpellSlot(3, 3), SpellSlot(4, 3), SpellSlot(5, 2), SpellSlot(6, 1)]
            case CasterType.Half:
                match level:
                    case 1 | 2:
                        return [SpellSlot(1, 2)]
                    case 3 | 4:
                        return [SpellSlot(1, 3)]
                    case 5 | 6:
                        return [SpellSlot(1, 4), SpellSlot(2, 2)]
                    case 7 | 8:
                        return [SpellSlot(1, 4), SpellSlot(2, 3)]
                    case 9 | 10:
                        return [SpellSlot(1, 4), SpellSlot(2, 3), SpellSlot(3, 2)]
                    case 11 | 12:
                        return [SpellSlot(1, 4), SpellSlot(2, 3), SpellSlot(3, 3)]
            case CasterType.Third:
                match level:
                    case 1 | 2:
                        return []
                    case 3:
                        return [SpellSlot(1, 2)]
                    case 4 | 5 | 6:
                        return [SpellSlot(1, 3)]
                    case 7 | 8 | 9:
                        return [SpellSlot(1, 4), SpellSlot(2, 2)]
                    case 10 | 11 | 12:
                        return [SpellSlot(1, 4), SpellSlot(2, 3)]
            case CasterType.Pact:
                match level:
                    case 1:
                        return [SpellSlot(1, 1)]
                    case 2:
                        return [SpellSlot(1, 2)]
                    case 3 | 4:
                        return [SpellSlot(2, 2)]
                    case 5 | 6:
                        return [SpellSlot(3, 2)]
                    case 7 | 8:
                        return [SpellSlot(4, 2)]
                    case 9 | 10:
                        return [SpellSlot(5, 2)]
                    case 11 | 12:
                        return [SpellSlot(5, 3)]
            case CasterType.NoneType:
                return []

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


