from dataclasses import dataclass, field

@dataclass
class Spell:
    name: str
    level: int
    school: str
    casting_time: str
    range: str
    components: str
    duration: str
    description: str
    damage: str | None = None
    upcast_info: str = "Casting this spell at higher levels provides no additional benefit."
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)

@dataclass
class SpellSlot:
    level: int
    count: int