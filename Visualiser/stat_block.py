# Stat block can be either:
# - Player Character Class (See pc_classes.py)
# - Stat block from the Monster Manual (a scanned image of a page) with additions (optional)
from PIL import Image
from pathlib import Path

from media_paths import MONSTER_MANUAL_PAGES

class StatBlock:
    def __init__(self):
        pass

    def display(self):
        pass


class MonMan(StatBlock):
    monster_name: str
    image_path: str

    def __init__(self, name: str):
        super().__init__()
        self.monster_name = name
        self.image_path = (MONSTER_MANUAL_PAGES / f"{name}.png")

    def load_image(self):
        p = Path(self.image_path)
        return Image.open(p) if p.exists() else None

    def display(self):
        return {"type": "monster_manual_image", "name": self.monster_name, "path": str(self.image_path)}