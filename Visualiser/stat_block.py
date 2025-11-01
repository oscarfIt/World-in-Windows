# Stat block can be either:
# - Player Character Class (See pc_classes.py)
# - Stat block from the Monster Manual (a scanned image of a page) with additions (optional)
from PIL import Image
from pathlib import Path

from media_paths import MONSTER_MANUAL_PAGES

class StatBlock:
    display_name: str

    def __init__(self, name: str):
        self.display_name =name

    def display(self):
        pass


class MonMan(StatBlock):
    monster_name: str
    image_path: str

    def __init__(self, file_name: str):
        self.monster_name = self.nice_name(file_name)
        super().__init__(self.monster_name)
        self.image_path = (MONSTER_MANUAL_PAGES / f"{file_name}.png")

    def nice_name(self, file_name: str) -> str:
        return file_name.replace("_", " ").title()
    
    def load_image(self):
        p = Path(self.image_path)
        return Image.open(p) if p.exists() else None

    def display(self):
        return {"type": "monster_manual_image", "name": self.monster_name, "path": str(self.image_path)}