from dataclasses import dataclass

@dataclass
class AbilityScores:
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int

    def __init__(self, strength: int = 10, dexterity: int = 10, constitution: int = 10, intelligence: int = 10, wisdom: int = 10, charisma: int = 10):
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence
        self.wisdom = wisdom
        self.charisma = charisma