# world_in_windows.py
# Minimal PyQt6 app to browse (nested) Locations and see their NPCs.
# Changes from previous version:
# - Left pane is now a QTreeView with two columns: Name | Short Description
# - Locations can be nested (e.g., "The Salty Hound" under "Port Virellon")
# - Short description is visible directly in the tree
#
# pip install PyQt6

import sys
from PyQt6 import QtWidgets

from .Windows.main_window import MainWindow
from .theme import DMHelperTheme
from .knowledge_base import KnowledgeBase
from .repo import Repo
from .config import Config

# Global config instance
config = Config()

# --- App entry ---
def main():
    repo = Repo(config.data_dir)
    repo.load_all()

    kb = KnowledgeBase()
    kb.ingest(repo.spells, repo.items, repo.class_actions)
    kb.ingest_npcs(repo.npcs_by_id.values())
    kb.ingest_conditions(repo.conditions)

    app = QtWidgets.QApplication(sys.argv)
    
    # Apply the D&D themed styling
    DMHelperTheme.apply_to_application(app)
    
    win = MainWindow(repo.locations, kb)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
