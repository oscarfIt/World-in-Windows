from dataclasses import dataclass

@dataclass
class ClassAction:
    name: str
    description: str
    aliases: list[str] = None