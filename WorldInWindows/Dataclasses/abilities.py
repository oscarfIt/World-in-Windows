from dataclasses import dataclass

@dataclass
class AbilityScores:
    Strength: int
    Dexterity: int
    Constitution: int
    Intelligence: int
    Wisdom: int
    Charisma: int

    def __init__(self, scores: dict = {}):
        self.Strength = scores.get("Strength", 10)
        self.Dexterity = scores.get("Dexterity", 10)
        self.Constitution = scores.get("Constitution", 10)
        self.Intelligence = scores.get("Intelligence", 10)
        self.Wisdom = scores.get("Wisdom", 10)
        self.Charisma = scores.get("Charisma", 10)