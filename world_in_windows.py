# world_in_windows.py
# Minimal PyQt6 app to browse (nested) Locations and see their NPCs.
# Changes from previous version:
# - Left pane is now a QTreeView with two columns: Name | Short Description
# - Locations can be nested (e.g., "The Salty Hound" under "Port Virellon")
# - Short description is visible directly in the tree
#
# pip install PyQt6

import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from typing import List, Optional
from pathlib import Path
import json

from .Dataclasses import Spell, Item, ClassAction, NPC, Location, StatBlock, MonsterManual, PcClass, PcClassName
from .Windows import MainWindow

from theme import DMHelperTheme
from knowledge_base import KBEntry, KnowledgeBase
from repo import Repo
from image_generation import ImageGenerator, ImageGenerationMode
from config import Config

# Global config instance
config = Config()

# --- Tree model utilities ---
ROLE_LOCATION_PTR = QtCore.Qt.ItemDataRole.UserRole + 1
ROLE_NPC_PTR = QtCore.Qt.ItemDataRole.UserRole + 2   # NEW

def build_tree_model(locations: List[Location]) -> QtGui.QStandardItemModel:
    """
    Build a two-column tree:
    Column 0: Location name
    Column 1: Short description
    """
    model = QtGui.QStandardItemModel()
    model.setHorizontalHeaderLabels(["Location", "Short Description"])

    # Index by object to avoid duplicate insertion
    top_level = [loc for loc in locations if loc.parent is None]

    def make_item(loc: Location) -> List[QtGui.QStandardItem]:
        name_item = QtGui.QStandardItem(loc.name)
        name_item.setEditable(False)
        name_item.setData(loc, ROLE_LOCATION_PTR)
        # Tooltip with more detail
        name_item.setToolTip(f"{loc.name}\n\n{loc.description}")

        desc_item = QtGui.QStandardItem(loc.short_description(80))
        desc_item.setEditable(False)
        desc_item.setToolTip(loc.description)

        return [name_item, desc_item]

    def add_node(parent_item: Optional[QtGui.QStandardItem], loc: Location):
        items = make_item(loc)
        if parent_item is None:
            model.appendRow(items)
        else:
            parent_item.appendRow(items)
        # Recurse for children
        for child in loc.children:
            add_node(items[0], child)

    for loc in top_level:
        add_node(None, loc)

    return model

def filter_tree(tree_view: QtWidgets.QTreeView, model: QtGui.QStandardItemModel, text: str):
    """
    Simple name/description filter that hides non-matching branches.
    Shows a parent if any descendant matches.
    """
    t = text.strip().lower()

    def node_matches(item: QtGui.QStandardItem) -> bool:
        loc: Location = item.data(ROLE_LOCATION_PTR)
        if not loc:
            return False
        hay = " ".join([loc.name, loc.description, loc.region or "", " ".join(loc.tags)]).lower()
        return (t in hay) if t else True

    def apply(item: QtGui.QStandardItem) -> bool:
        # Check self and children
        match_self = node_matches(item)
        any_child_match = False
        for row in range(item.rowCount()):
            child = item.child(row, 0)
            if child:
                child_match = apply(child)
                any_child_match = any_child_match or child_match
        
        visible = match_self or any_child_match
        
        # Hide/show rows using the tree view
        index = item.index()
        if index.isValid():
            tree_view.setRowHidden(index.row(), index.parent(), not visible)
        
        return visible

    # Apply to all top-level nodes
    for r in range(model.rowCount()):
        root_item = model.item(r, 0)
        if root_item:
            apply(root_item)


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
