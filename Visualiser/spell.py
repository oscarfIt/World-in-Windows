from dataclasses import dataclass, field
from enum import Enum

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
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)