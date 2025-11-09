from PyQt6 import QtCore, QtGui, QtWidgets
import subprocess
import sys
from pathlib import Path
from typing import List

from ..theme import DMHelperTheme
from ..repo import Repo
from ..config import Config

from ..knowledge_base import KnowledgeBase      # HMMMMMM

from ..Dataclasses import Spell, Item, NPC, Location
from ..Dialogs import AddSoundDialog, AddNPCDialog

from .detail_windows import SpellDetailWindow, ItemDetailWindow, NPCDetailWindow, LocationDetailWindow, ConditionDetailWindow


ROLE_NPC_PTR = QtCore.Qt.ItemDataRole.UserRole + 2  # Defined here and in main_window.py, gross

# Base class
class BrowserWindowBase(QtWidgets.QMainWindow):
    central_widget: QtWidgets.QWidget
    vbox_layout: QtWidgets.QVBoxLayout
    title_layout: QtWidgets.QHBoxLayout
    button_layout: QtWidgets.QHBoxLayout

    entry_list: QtWidgets.QListWidget

    def __init__(self, entry_to_browse: str, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.kb = kb
        self.setWindowTitle(f"{entry_to_browse} Browser")
        self.resize(800, 600)

        DMHelperTheme.apply_theme(self)

        self.central_widget = QtWidgets.QWidget()
        self.vbox_layout = QtWidgets.QVBoxLayout(self.central_widget)

        # Title and search
        self.title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel(f"All {entry_to_browse}s")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        self.title_layout.addWidget(title_label)
        self.title_layout.addStretch()
        self.vbox_layout.addLayout(self.title_layout)

        add_entry_btn = QtWidgets.QPushButton(f"Add {entry_to_browse}")
        add_entry_btn.clicked.connect(self.add_entry)
        self.title_layout.addWidget(add_entry_btn)

        # Search bar
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText(f"Search {entry_to_browse}s...")
        self.search.textChanged.connect(self.filter_entries)
        self.vbox_layout.addWidget(self.search)

        # Entry list
        self.entry_list = QtWidgets.QListWidget()
        self.entry_list.itemDoubleClicked.connect(self.open_entry_detail)
        self.entry_list.setSpacing(2)
        self.entry_list.setUniformItemSizes(True)
        self.vbox_layout.addWidget(self.entry_list)

        # Populate with entries
        self.populate_entries()

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addStretch()
        self.button_layout.addWidget(close_btn)
        self.vbox_layout.addLayout(self.button_layout)

        self.setCentralWidget(self.central_widget)

    # Following methods to be defined in derived classes

    def populate_entries(self, new_entries: List):
        self.entry_list.clear()
        new_entries.sort(key=lambda x: x.name.lower())
        for entry in new_entries:
            item = QtWidgets.QListWidgetItem(entry.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, entry)
            item.setSizeHint(QtCore.QSize(0, 32))
            self.entry_list.addItem(item)

    def filter_entries(self):
        pass

    def open_entry_detail(self):
        pass

    def add_entry(self):
        pass

class SpellBrowserWindow(BrowserWindowBase):
    def __init__(self, kb: KnowledgeBase, parent=None):
        super().__init__("Spell", kb, parent)

    def populate_entries(self):
        try:
            repo = Repo(self.config.data_dir)
            repo.load_all()
            all_spells = list(repo.spells)
        except Exception as e:
            print(f"Failed to load spells from repo: {e}")
            all_spells = []
        super().populate_entries(all_spells)

    def filter_entries(self, text: str):
        text = text.lower().strip()
        for i in range(self.entry_list.count()):
            item = self.entry_list.item(i)
            spell = item.data(QtCore.Qt.ItemDataRole.UserRole)
            searchable_text = " ".join([
                spell.name,
                str(spell.level),
                spell.school,
                spell.casting_time,
                spell.range,
                spell.components,
                spell.duration,
                spell.description or "",
                " ".join(getattr(spell, "tags", [])),
                " ".join(getattr(spell, "aliases", [])),
            ]).lower()
            item.setHidden(text not in searchable_text if text else False)

    def open_entry_detail(self, item: QtWidgets.QListWidgetItem):
        spell = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not spell:
            return
        window = SpellDetailWindow(spell, self.kb, self)
        window.show()

class ItemBrowserWindow(BrowserWindowBase):
    def __init__(self, kb: KnowledgeBase, parent=None):
        super().__init__("Item", kb, parent)

    def populate_entries(self):
        try:
            repo = Repo(self.config.data_dir)
            repo.load_all()
            all_items = list(repo.items)
        except Exception as e:
            print(f"Failed to load items from repo: {e}")
            all_items = []
        super().populate_entries(all_items)

    def filter_entries(self, text: str):
        text = text.lower().strip()
        for i in range(self.entry_list.count()):
            item_widget = self.entry_list.item(i)
            item = item_widget.data(QtCore.Qt.ItemDataRole.UserRole)
            searchable_text = " ".join([
                item.name,
                item.rarity,
                item.description or "",
                " ".join(getattr(item, "tags", [])),
                " ".join(getattr(item, "aliases", [])),
                "attunement" if item.attunement else "",
            ]).lower()
            item_widget.setHidden(text not in searchable_text if text else False)

    def open_entry_detail(self, item_widget: QtWidgets.QListWidgetItem):
        item = item_widget.data(QtCore.Qt.ItemDataRole.UserRole)
        if not item:
            return
        window = ItemDetailWindow(item, self.kb, self)
        window.show()

class SoundBrowserWindow(BrowserWindowBase):
    """Window for browsing and generating audio clips"""
    def __init__(self, kb: KnowledgeBase, parent=None):
        super().__init__("Sound", kb, parent)
                        
        # Play button
        play_btn = QtWidgets.QPushButton("Play")
        play_btn.clicked.connect(self.play_selected_sound)
        self.button_layout.insertWidget(0, play_btn)
        
        # Stop button  
        stop_btn = QtWidgets.QPushButton("Stop")
        stop_btn.clicked.connect(self.stop_sound)
        self.button_layout.insertWidget(1, stop_btn)
        
        # Delete button
        delete_btn = QtWidgets.QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_selected_sound)
        self.button_layout.insertWidget(2, delete_btn)
        
    def populate_entries(self):
        # This implementation is a bit different so we don't call the super's method
        self.entry_list.clear()
        
        # Look for audio files in Media/Audio directory
        audio_dir = self.config.get_audio_files()
        if not audio_dir.exists():
            return
        
        # Find all audio files
        audio_extensions = {'.mp3', '.wav', '.m4a', '.ogg', '.flac'}
        audio_files = []
        
        for ext in audio_extensions:
            audio_files.extend(audio_dir.glob(f'*{ext}'))
        
        # Sort by name
        audio_files.sort(key=lambda x: x.name.lower())
        
        # Add to list widget
        for audio_file in audio_files:
            item = QtWidgets.QListWidgetItem(audio_file.stem)  # Name without extension
            item.setData(QtCore.Qt.ItemDataRole.UserRole, str(audio_file))  # Store full path
            item.setSizeHint(QtCore.QSize(0, 32))
            self.entry_list.addItem(item)

    def filter_entries(self, text: str):
        """Filter the sounds list based on search text"""
        text = text.lower().strip()
        
        for i in range(self.entry_list.count()):
            item = self.entry_list.item(i)
            # Search in filename
            item.setHidden(text not in item.text().lower() if text else False)

    def add_entry(self):
        """Add/generate a new sound"""
        dialog = AddSoundDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Refresh the sounds list to show the new sound
            self.populate_entries()

    def play_selected_sound(self):
        """Play the selected audio clip"""
        current_item = self.entry_list.currentItem()
        if not current_item:
            QtWidgets.QMessageBox.information(self, "No Selection", "Please select an audio clip to play.")
            return
        
        audio_path = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
        try:
            # Try to play using system default audio player
            
            if sys.platform == "win32":
                # Windows
                subprocess.run(['start', '', audio_path], shell=True, check=False)
            elif sys.platform == "darwin":
                # macOS
                subprocess.run(['open', audio_path], check=False)
            else:
                # Linux
                subprocess.run(['xdg-open', audio_path], check=False)
                
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Playback Error", 
                f"Could not play audio file:\n{str(e)}")

    def stop_sound(self):
        """Stop audio playback (placeholder - system dependent)"""
        QtWidgets.QMessageBox.information(self, "Stop", 
            "Audio playback stop is handled by your system's audio player.")

    def delete_selected_sound(self):
        """Delete the selected audio clip"""
        current_item = self.entry_list.currentItem()
        if not current_item:
            QtWidgets.QMessageBox.information(self, "No Selection", "Please select an audio clip to delete.")
            return
        
        audio_path = Path(current_item.data(QtCore.Qt.ItemDataRole.UserRole))
        
        # Confirm deletion
        reply = QtWidgets.QMessageBox.question(self, "Confirm Delete",
            f"Are you sure you want to delete '{current_item.text()}'?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                audio_path.unlink()  # Delete the file
                self.populate_entries()  # Refresh the list
                QtWidgets.QMessageBox.information(self, "Deleted", 
                    f"Audio clip '{current_item.text()}' has been deleted.")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Delete Error", 
                    f"Could not delete file:\n{str(e)}")

class NPCBrowserWindow(BrowserWindowBase):
    """Window for browsing all NPCs in the campaign"""
    def __init__(self, kb: KnowledgeBase, parent=None):
        super().__init__("NPC", kb, parent)
                        
    def populate_entries(self):
        # This implementation is a bit different so we don't call the super's method
        self.entry_list.clear()
        
        # Load NPCs directly from the repository (freshly loaded from JSON)
        try:
            repo = Repo(self.config.data_dir)
            repo.load_all()  # This will reload from JSON files including any new NPCs
            
            # Get all NPCs from the repository
            all_npcs = list(repo.npcs_by_id.values())
            
        except Exception as e:
            # Fallback to knowledge base if repo loading fails
            print(f"Failed to load from repo: {e}")
            all_npcs = []
            if hasattr(self.kb, 'entries'):
                # Extract NPC entries from knowledge base
                for entry in self.kb.entries.values():
                    if isinstance(entry.content, NPC):
                        # This is a fallback - we won't have the full NPC object
                        # but at least we can show the names
                        pass
        
        # Sort NPCs by name
        all_npcs.sort(key=lambda x: x.name.lower())
        
        # Add to list widget
        for npc in all_npcs:
            # Add deceased indicator to name if not alive
            display_name = npc.name
            if not npc.alive:
                display_name = f"{npc.name} ☠️ [DECEASED]"
            
            item = QtWidgets.QListWidgetItem(display_name)
            item.setData(ROLE_NPC_PTR, npc)
            
            # Set proper item size for better spacing
            item.setSizeHint(QtCore.QSize(0, 32))  # Height of 32 pixels for each item
            
            # Style deceased NPCs differently
            if not npc.alive:
                item.setForeground(QtGui.QColor("#888888"))  # Gray text for deceased
                font = item.font()
                font.setItalic(True)
                item.setFont(font)
            self.entry_list.addItem(item)
    
    def filter_entries(self, text: str):
        """Filter the NPCs list based on search text"""
        text = text.lower().strip()
        
        for i in range(self.entry_list.count()):
            item = self.entry_list.item(i)
            npc = item.data(ROLE_NPC_PTR)
            
            # Search in name, race, alignment, and appearance
            searchable_text = " ".join([
                npc.name,
                npc.race.value,
                npc.alignment.value,
                npc.appearance or "",
                npc.backstory or ""
            ]).lower()
            
            # Show/hide based on search match
            item.setHidden(text not in searchable_text if text else False)
    
    def open_entry_detail(self, item: QtWidgets.QListWidgetItem):
        """Open the NPC detail window"""
        npc = item.data(ROLE_NPC_PTR)
        if not npc:
            return
        window = NPCDetailWindow(npc, self.kb, self)
        window.show()
    
    def add_entry(self):
        """Add a new NPC"""
        dialog = AddNPCDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Refresh the NPCs list to show the new NPC
            # populate_entries() will reload data from JSON files
            self.populate_entries()

class LocationBrowserWindow(BrowserWindowBase):
    def __init__(self, kb: KnowledgeBase, locations: List[Location], parent=None):
        self.locations = locations
        super().__init__("Location", kb, parent)

    def populate_entries(self):
        # Get all locations (including nested ones)
        all_locations = []
        def collect_locations(locs):
            for loc in locs:
                all_locations.append(loc)
                if hasattr(loc, 'children') and loc.children:
                    collect_locations(loc.children)
        
        collect_locations(self.locations)
        super().populate_entries(all_locations)

    def filter_entries(self, text: str):
        text = text.lower().strip()
        for i in range(self.entry_list.count()):
            item = self.entry_list.item(i)
            loc = item.data(QtCore.Qt.ItemDataRole.UserRole)
            searchable_text = " ".join([
                loc.name,
                loc.region or "",
                loc.description or "",
                " ".join(getattr(loc, "tags", [])),
            ]).lower()
            item.setHidden(text not in searchable_text if text else False)

    def open_entry_detail(self, item: QtWidgets.QListWidgetItem):
        loc = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not loc:
            return
        window = LocationDetailWindow(loc, self.kb, self)
        window.show()

class ConditionBrowserWindow(BrowserWindowBase):
    def __init__(self, kb: KnowledgeBase, parent=None):
        super().__init__("Condition", kb, parent)

    def populate_entries(self):
        try:
            repo = Repo(self.config.data_dir)
            repo.load_all()
            all_conditions = list(repo.conditions)
        except Exception as e:
            print(f"Failed to load conditions from repo: {e}")
            all_conditions = []
        super().populate_entries(all_conditions)

    def filter_entries(self, text: str):
        text = text.lower().strip()
        for i in range(self.entry_list.count()):
            item = self.entry_list.item(i)
            condition = item.data(QtCore.Qt.ItemDataRole.UserRole)
            searchable_text = " ".join([
                condition.name,
                condition.description or "",
            ]).lower()
            item.setHidden(text not in searchable_text if text else False)

    def open_entry_detail(self, item: QtWidgets.QListWidgetItem):
        condition = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not condition:
            return
        window = ConditionDetailWindow(condition, self.kb, self)
        window.show()
