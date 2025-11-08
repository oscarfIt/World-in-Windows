from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from .stat_block import StatBlock
from .abilities import AbilityScores
from .spell import SpellSlot
from .item import Item

BASE_AC = 10

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
    proficiency_bonus: int
    ability_scores: AbilityScores
    hit_points: int
    armor_class: int
    move_speed: int
    caster_type: CasterType
    spell_save_dc: int
    spell_attack_modifier: int
    weapons: list[Item] = field(default_factory=list)
    spells: list[str] = field(default_factory=list)    # Stored as a string not spell hmm
    spell_slots: list[SpellSlot] = field(default_factory=list)

    def __init__(self, name: PcClassName, level: int = 1, ability_scores: AbilityScores = None, armor_class: Optional[int] = None, spells: Optional[list[str]] = None, weapons: Optional[list[Item]] = None):
        super().__init__(name.value + ", Level " + str(level))
        self.name = name
        self.level = level
        self.proficiency_bonus = self.determine_proficiency_bonus()
        self.ability_scores = ability_scores if ability_scores is not None else AbilityScores()
        self.hit_points = self.determine_hit_points()
        self.move_speed = 30  # Default move speed
        self.caster_type = self.determine_caster_type(name)
        self.spell_save_dc = self.determine_spell_save_dc()
        self.spell_attack_modifier = self.determine_spell_attack_modifier()
        self.spells = spells if spells is not None else []
        self.armor_class = self.determine_default_armor_class() if armor_class is None or armor_class <= 10 else armor_class
        self.spell_slots = self.determine_spell_slots(level, self.caster_type)
        self.weapons = weapons if weapons is not None else []

    def determine_proficiency_bonus(self) -> int:
        match self.level:
            case 1 | 2 | 3 | 4:
                return 2
            case 5 | 6 | 7 | 8:
                return 3
            case 9 | 10 | 11 | 12:
                return 4
            case 13 | 14 | 15 | 16:
                return 5
            case 17 | 18 | 19 | 20:
                return 6
            case _:
                return 2
            
    def determine_hit_points(self) -> int:
        match self.name:
            case PcClassName.Barbarian:
                points_per_level = 7
            case PcClassName.Fighter | PcClassName.Paladin | PcClassName.Ranger:
                points_per_level = 6
            case PcClassName.Bard | PcClassName.Cleric | PcClassName.Druid | PcClassName.Monk | PcClassName.Rogue | PcClassName.Warlock:
                points_per_level = 5
            case PcClassName.Sorcerer | PcClassName.Wizard:
                points_per_level = 4
            case _:
                points_per_level = 5
        return self.level * (points_per_level + self.ability_scores.get_modifier(self.ability_scores.constitution))

    # If not wearing armor
    def determine_default_armor_class(self) -> int:
        match self.name:
            case PcClassName.Barbarian:
                return BASE_AC + self.ability_scores.get_modifier(self.ability_scores.dexterity) + self.ability_scores.get_modifier(self.ability_scores.constitution)
            case PcClassName.Monk:
                return BASE_AC + self.ability_scores.get_modifier(self.ability_scores.dexterity) + self.ability_scores.get_modifier(self.ability_scores.wisdom)
            case PcClassName.Wizard | PcClassName.Sorcerer:
                if "Mage Armor" in self.spells:
                    return 13 + self.ability_scores.get_modifier(self.ability_scores.dexterity)
                else:
                    return BASE_AC + self.ability_scores.get_modifier(self.ability_scores.dexterity)
            case _:
                return BASE_AC + self.ability_scores.get_modifier(self.ability_scores.dexterity)

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
            
    def determine_spellcasting_ability_modifier(self, class_name: PcClassName) -> int:
        match class_name:
            case PcClassName.Cleric | PcClassName.Druid | PcClassName.Ranger:
                return self.ability_scores.get_modifier(self.ability_scores.wisdom)
            case PcClassName.Bard | PcClassName.Paladin | PcClassName.Sorcerer | PcClassName.Warlock:
                return self.ability_scores.get_modifier(self.ability_scores.charisma)
            case PcClassName.Wizard:
                return self.ability_scores.get_modifier(self.ability_scores.intelligence)
            case _:
                return 0
            
    def determine_spell_save_dc(self) -> int:
        spellcasting_ability_mod = self.determine_spellcasting_ability_modifier(self.name)
        return 8 + self.proficiency_bonus + spellcasting_ability_mod
    
    def determine_spell_attack_modifier(self) -> int:
        spellcasting_ability_mod = self.determine_spellcasting_ability_modifier(self.name)
        return self.proficiency_bonus + spellcasting_ability_mod

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


