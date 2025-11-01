from dataclasses import dataclass, field
from enum import Enum

class SpellSchool(Enum):
    Abjuration = "Abjuration"
    Conjuration = "Conjuration"
    Divination = "Divination"
    Enchantment = "Enchantment"
    Evocation = "Evocation"
    Illusion = "Illusion"
    Necromancy = "Necromancy"
    Transmutation = "Transmutation"


@dataclass
class Spell:
    id: str
    name: str
    level: int
    school: SpellSchool
    casting_time: str
    range: str
    components: str
    duration: str
    short_description: str
    full_description: str
    tags: list[str] = field(default_factory=list)