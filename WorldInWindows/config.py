from pathlib import Path
import json

# --- Configuration system ---
CONFIG_FILE = Path("config.json")

class Config:
    def __init__(self):
        self.data_dir = "Data"
        self.media_dir = "Media"
        self.load()
    
    def load(self):
        """Load configuration from file"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.data_dir = data.get("data_dir", "Data")
                    self.media_dir = data.get("media_dir", "Media")
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
    
    def save(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "data_dir": self.data_dir,
                    "media_dir": self.media_dir
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")

    def mk_dirs(self):
        Path(self.get_npc_portraits()).mkdir(parents=True, exist_ok=True)
        Path(self.get_spell_icons()).mkdir(parents=True, exist_ok=True)
        Path(self.get_item_icons()).mkdir(parents=True, exist_ok=True)
        Path(self.get_ability_icons()).mkdir(parents=True, exist_ok=True)
        Path(self.get_monster_manual_pages()).mkdir(parents=True, exist_ok=True)
        Path(self.get_audio_files()).mkdir(parents=True, exist_ok=True)

    def get_media_root(self) -> Path:
        return Path(self.media_dir)

    def get_npc_portraits(self) -> Path:
        return self.get_media_root() / "NPCs"

    def get_spell_icons(self) -> Path:
        return self.get_media_root() / "Spells"

    def get_item_icons(self) -> Path:
        return self.get_media_root() / "Items"

    def get_ability_icons(self) -> Path:
        return self.get_media_root() / "Abilities"

    def get_monster_manual_pages(self) -> Path:
        return self.get_media_root() / "MonsterManual"
    
    def get_audio_files(self) -> Path:
        return self.get_media_root() / "Audio"
    
    def get_image_references(self) -> Path:
        return self.get_media_root() / "Image References"