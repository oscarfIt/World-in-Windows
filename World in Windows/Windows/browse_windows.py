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

class SpellBrowserWindow(QtWidgets.QMainWindow):
    """Window for browsing all Spells in the campaign"""
    def __init__(self, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.kb = kb
        self.setWindowTitle("Spells Browser")
        self.resize(800, 600)

        # Apply dialog theme
        DMHelperTheme.apply_to_dialog(self)

        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Title and search
        title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("All Spells")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Search bar
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search Spells...")
        self.search.textChanged.connect(self.filter_spells)
        layout.addWidget(self.search)

        # Spells list
        self.spells_list = QtWidgets.QListWidget()
        self.spells_list.itemDoubleClicked.connect(self.open_spell_detail)
        self.spells_list.setSpacing(2)
        self.spells_list.setUniformItemSizes(True)
        layout.addWidget(self.spells_list)

        # Populate with spells
        self.populate_spells()

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        self.setCentralWidget(central_widget)

    def populate_spells(self):
        """Populate the list with all Spells from the repository"""
        self.spells_list.clear()
        try:
            repo = Repo(self.config.data_dir)
            repo.load_all()
            all_spells = list(repo.spells)
        except Exception as e:
            print(f"Failed to load spells from repo: {e}")
            all_spells = []
        all_spells.sort(key=lambda x: x.name.lower())
        for spell in all_spells:
            item = QtWidgets.QListWidgetItem(spell.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, spell)
            item.setSizeHint(QtCore.QSize(0, 32))
            tooltip = self.create_spell_tooltip(spell)
            item.setToolTip(tooltip)
            self.spells_list.addItem(item)

    def create_spell_tooltip(self, spell: Spell) -> str:
        desc = spell.description or "No description"
        if len(desc) > 160:
            desc = desc[:160].rstrip() + "…"
        return (f"{spell.name}\nLevel: {spell.level}  School: {spell.school}\n\n{desc}")

    def filter_spells(self, text: str):
        text = text.lower().strip()
        for i in range(self.spells_list.count()):
            item = self.spells_list.item(i)
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

    def open_spell_detail(self, item: QtWidgets.QListWidgetItem):
        spell = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not spell:
            return
        window = SpellDetailWindow(spell, self.kb, self)
        window.show()

class ItemBrowserWindow(QtWidgets.QMainWindow):
    """Window for browsing all Items in the campaign"""
    def __init__(self, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.kb = kb
        self.setWindowTitle("Items Browser")
        self.resize(800, 600)

        # Apply dialog theme
        DMHelperTheme.apply_to_dialog(self)

        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Title and search
        title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("All Items")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Search bar
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search Items...")
        self.search.textChanged.connect(self.filter_items)
        layout.addWidget(self.search)

        # Items list
        self.items_list = QtWidgets.QListWidget()
        self.items_list.itemDoubleClicked.connect(self.open_item_detail)
        self.items_list.setSpacing(2)
        self.items_list.setUniformItemSizes(True)
        layout.addWidget(self.items_list)

        # Populate with items
        self.populate_items()

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        self.setCentralWidget(central_widget)

    def populate_items(self):
        """Populate the list with all Items from the repository"""
        self.items_list.clear()
        try:
            repo = Repo(self.config.data_dir)
            repo.load_all()
            all_items = list(repo.items)
        except Exception as e:
            print(f"Failed to load items from repo: {e}")
            all_items = []
        
        all_items.sort(key=lambda x: x.name.lower())
        for item in all_items:
            item_widget = QtWidgets.QListWidgetItem(item.name)
            item_widget.setData(QtCore.Qt.ItemDataRole.UserRole, item)
            item_widget.setSizeHint(QtCore.QSize(0, 32))
            tooltip = self.create_item_tooltip(item)
            item_widget.setToolTip(tooltip)
            self.items_list.addItem(item_widget)

    def create_item_tooltip(self, item: Item) -> str:
        desc = item.description or "No description"
        if len(desc) > 160:
            desc = desc[:160].rstrip() + "…"
        attunement_text = " (Requires Attunement)" if item.attunement else ""
        return (f"{item.name}\nRarity: {item.rarity}{attunement_text}\n\n{desc}")

    def filter_items(self, text: str):
        text = text.lower().strip()
        for i in range(self.items_list.count()):
            item_widget = self.items_list.item(i)
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

    def open_item_detail(self, item_widget: QtWidgets.QListWidgetItem):
        item = item_widget.data(QtCore.Qt.ItemDataRole.UserRole)
        if not item:
            return
        window = ItemDetailWindow(item, self.kb, self)
        window.show()

class SoundBrowserWindow(QtWidgets.QMainWindow):
    """Window for browsing and generating audio clips"""
    def __init__(self, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.kb = kb
        self.setWindowTitle("Sounds Browser")
        self.resize(800, 600)

        # Apply dialog theme
        DMHelperTheme.apply_to_dialog(self)

        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Title and search
        title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("Audio Clips")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Add Sound button
        add_sound_btn = QtWidgets.QPushButton("Add Sound")
        add_sound_btn.setToolTip("Generate a new audio clip")
        add_sound_btn.clicked.connect(self.add_sound)
        title_layout.addWidget(add_sound_btn)
        
        layout.addLayout(title_layout)

        # Search bar
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search audio clips...")
        self.search.textChanged.connect(self.filter_sounds)
        layout.addWidget(self.search)

        # Sounds list
        self.sounds_list = QtWidgets.QListWidget()
        self.sounds_list.setSpacing(2)
        self.sounds_list.setUniformItemSizes(True)
        layout.addWidget(self.sounds_list)

        # Populate with existing sounds
        self.populate_sounds()

        # Control buttons
        control_layout = QtWidgets.QHBoxLayout()
        
        # Play button
        play_btn = QtWidgets.QPushButton("Play")
        play_btn.setToolTip("Play selected audio clip")
        play_btn.clicked.connect(self.play_selected_sound)
        control_layout.addWidget(play_btn)
        
        # Stop button  
        stop_btn = QtWidgets.QPushButton("Stop")
        stop_btn.setToolTip("Stop audio playback")
        stop_btn.clicked.connect(self.stop_sound)
        control_layout.addWidget(stop_btn)
        
        # Delete button
        delete_btn = QtWidgets.QPushButton("Delete")
        delete_btn.setToolTip("Delete selected audio clip")
        delete_btn.clicked.connect(self.delete_selected_sound)
        control_layout.addWidget(delete_btn)
        
        control_layout.addStretch()
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        control_layout.addWidget(close_btn)
        
        layout.addLayout(control_layout)
        self.setCentralWidget(central_widget)

    def populate_sounds(self):
        """Populate the list with existing audio files"""
        self.sounds_list.clear()
        
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
            
            # Create tooltip with file info
            tooltip = f"File: {audio_file.name}\nPath: {audio_file}"
            try:
                file_size = audio_file.stat().st_size
                tooltip += f"\nSize: {file_size:,} bytes"
            except:
                pass
            item.setToolTip(tooltip)
            
            self.sounds_list.addItem(item)

    def filter_sounds(self, text: str):
        """Filter the sounds list based on search text"""
        text = text.lower().strip()
        
        for i in range(self.sounds_list.count()):
            item = self.sounds_list.item(i)
            # Search in filename
            item.setHidden(text not in item.text().lower() if text else False)

    def add_sound(self):
        """Add/generate a new sound"""
        dialog = AddSoundDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Refresh the sounds list to show the new sound
            self.populate_sounds()

    def play_selected_sound(self):
        """Play the selected audio clip"""
        current_item = self.sounds_list.currentItem()
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
        current_item = self.sounds_list.currentItem()
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
                self.populate_sounds()  # Refresh the list
                QtWidgets.QMessageBox.information(self, "Deleted", 
                    f"Audio clip '{current_item.text()}' has been deleted.")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Delete Error", 
                    f"Could not delete file:\n{str(e)}")

class NPCBrowserWindow(QtWidgets.QMainWindow):
    """Window for browsing all NPCs in the campaign"""
    def __init__(self, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.kb = kb
        self.setWindowTitle("NPCs Browser")
        self.resize(800, 600)
        
        # Apply dialog theme
        DMHelperTheme.apply_to_dialog(self)
        
        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Title and search
        title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("All NPCs")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Add NPC button
        add_npc_btn = QtWidgets.QPushButton("Add NPC")
        add_npc_btn.setToolTip("Create a new NPC")
        add_npc_btn.clicked.connect(self.add_npc)
        title_layout.addWidget(add_npc_btn)
        
        layout.addLayout(title_layout)
        
        # Search bar
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search NPCs...")
        self.search.textChanged.connect(self.filter_npcs)
        layout.addWidget(self.search)
        
        # NPCs list
        self.npcs_list = QtWidgets.QListWidget()
        self.npcs_list.itemDoubleClicked.connect(self.open_npc_detail)
        
        # Set proper spacing and sizing for list items
        self.npcs_list.setSpacing(2)
        self.npcs_list.setUniformItemSizes(True)
        
        layout.addWidget(self.npcs_list)
        
        # Populate with NPCs
        self.populate_npcs()
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        self.setCentralWidget(central_widget)
        
    def populate_npcs(self):
        """Populate the list with all NPCs from the repository"""
        self.npcs_list.clear()
        
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
            
            # Create tooltip with NPC info
            tooltip = self.create_npc_tooltip(npc)
            item.setToolTip(tooltip)
            
            self.npcs_list.addItem(item)
    
    def create_npc_tooltip(self, npc: NPC) -> str:
        """Create a tooltip for an NPC"""
        appearance = npc.appearance or "No appearance description"
        if len(appearance) > 160:
            appearance = appearance[:160].rstrip() + "…"
        
        return (f"{npc.name}\n"
                f"Race: {npc.race.value}\n" 
                f"Alignment: {npc.alignment.value}\n\n"
                f"{appearance}")
    
    def filter_npcs(self, text: str):
        """Filter the NPCs list based on search text"""
        text = text.lower().strip()
        
        for i in range(self.npcs_list.count()):
            item = self.npcs_list.item(i)
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
    
    def open_npc_detail(self, item: QtWidgets.QListWidgetItem):
        """Open the NPC detail window"""
        npc = item.data(ROLE_NPC_PTR)
        if not npc:
            return
        window = NPCDetailWindow(npc, self.kb, self)
        window.show()
    
    def add_npc(self):
        """Add a new NPC"""
        dialog = AddNPCDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Refresh the NPCs list to show the new NPC
            # populate_npcs() will reload data from JSON files
            self.populate_npcs()

class LocationBrowserWindow(QtWidgets.QMainWindow):
    """Window for browsing all Locations in the campaign"""
    def __init__(self, kb: KnowledgeBase, locations: List[Location], parent=None):
        super().__init__(parent)
        self.kb = kb
        self.locations = locations
        self.setWindowTitle("Locations Browser")
        self.resize(900, 600)

        # Apply dialog theme
        DMHelperTheme.apply_to_dialog(self)

        # Central widget and layout
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Title and search
        title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("All Locations")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Search bar
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search Locations...")
        self.search.textChanged.connect(self.filter_locations)
        layout.addWidget(self.search)

        # Locations list
        self.locations_list = QtWidgets.QListWidget()
        self.locations_list.itemDoubleClicked.connect(self.open_location_detail)
        self.locations_list.setSpacing(2)
        self.locations_list.setUniformItemSizes(True)
        layout.addWidget(self.locations_list)

        # Populate with locations
        self.populate_locations()

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        self.setCentralWidget(central_widget)

    def populate_locations(self):
        """Populate the list with all Locations from the repository"""
        self.locations_list.clear()
        
        # Get all locations (including nested ones)
        all_locations = []
        def collect_locations(locs):
            for loc in locs:
                all_locations.append(loc)
                if hasattr(loc, 'children') and loc.children:
                    collect_locations(loc.children)
        
        collect_locations(self.locations)
        all_locations.sort(key=lambda x: x.name.lower())
        
        for loc in all_locations:
            item = QtWidgets.QListWidgetItem(loc.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, loc)
            item.setSizeHint(QtCore.QSize(0, 32))
            tooltip = self.create_location_tooltip(loc)
            item.setToolTip(tooltip)
            self.locations_list.addItem(item)

    def create_location_tooltip(self, loc: Location) -> str:
        desc = loc.description or "No description"
        if len(desc) > 160:
            desc = desc[:160].rstrip() + "…"
        return f"{loc.name}\nRegion: {loc.region or '-'}\nNPCs: {len(loc.npcs)}\n\n{desc}"

    def filter_locations(self, text: str):
        text = text.lower().strip()
        for i in range(self.locations_list.count()):
            item = self.locations_list.item(i)
            loc = item.data(QtCore.Qt.ItemDataRole.UserRole)
            searchable_text = " ".join([
                loc.name,
                loc.region or "",
                loc.description or "",
                " ".join(getattr(loc, "tags", [])),
            ]).lower()
            item.setHidden(text not in searchable_text if text else False)

    def open_location_detail(self, item: QtWidgets.QListWidgetItem):
        loc = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not loc:
            return
        window = LocationDetailWindow(loc, self.kb, self)
        window.show()

class ConditionBrowserWindow(QtWidgets.QMainWindow):
    """Window for browsing all Conditions in the campaign"""
    def __init__(self, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.kb = kb
        self.setWindowTitle("Conditions Browser")
        self.resize(800, 600)

        # Apply dialog theme
        DMHelperTheme.apply_to_dialog(self)

        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Title and search
        title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("All Conditions")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Search bar
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search Conditions...")
        self.search.textChanged.connect(self.filter_conditions)
        layout.addWidget(self.search)

        # Conditions list
        self.conditions_list = QtWidgets.QListWidget()
        self.conditions_list.itemDoubleClicked.connect(self.open_condition_detail)
        self.conditions_list.setSpacing(2)
        self.conditions_list.setUniformItemSizes(True)
        layout.addWidget(self.conditions_list)

        # Populate with conditions
        self.populate_conditions()

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        self.setCentralWidget(central_widget)

    def populate_conditions(self):
        """Populate the list with all Conditions from the repository"""
        self.conditions_list.clear()
        try:
            repo = Repo(self.config.data_dir)
            repo.load_all()
            all_conditions = list(repo.conditions)
        except Exception as e:
            print(f"Failed to load conditions from repo: {e}")
            all_conditions = []
        all_conditions.sort(key=lambda x: x.name.lower())
        for condition in all_conditions:
            item = QtWidgets.QListWidgetItem(condition.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, condition)
            item.setSizeHint(QtCore.QSize(0, 32))
            tooltip = self.create_condition_tooltip(condition)
            item.setToolTip(tooltip)
            self.conditions_list.addItem(item)

    def create_condition_tooltip(self, condition) -> str:
        desc = condition.description or "No description"
        if len(desc) > 160:
            desc = desc[:160].rstrip() + "…"
        return f"{condition.name}\n\n{desc}"

    def filter_conditions(self, text: str):
        text = text.lower().strip()
        for i in range(self.conditions_list.count()):
            item = self.conditions_list.item(i)
            condition = item.data(QtCore.Qt.ItemDataRole.UserRole)
            searchable_text = " ".join([
                condition.name,
                condition.description or "",
            ]).lower()
            item.setHidden(text not in searchable_text if text else False)

    def open_condition_detail(self, item: QtWidgets.QListWidgetItem):
        condition = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not condition:
            return
        window = ConditionDetailWindow(condition, self.kb, self)
        window.show()
