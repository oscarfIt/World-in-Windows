from PyQt6 import QtCore, QtGui, QtWidgets
from pathlib import Path
import json

from ..theme import DMHelperTheme
from ..knowledge_base import KnowledgeBase
from ..repo import Repo
from ..config import Config

from ..Dataclasses import Spell, Item, ClassAction, NPC, Location, PcClass, PcClassName, StatBlock, MonsterManual, Condition
from ..Dialogs import AddNPCDialog, CampaignNotesDialog, HoverPreview, EditPcClassDialog
from ..AIGen import ImageGenerator, ImageGenerationMode

def _resolve_image_for_entry(config: Config, content_type: Spell | Item | ClassAction) -> Path | None:
    if isinstance(content_type, Spell):
        folder = config.get_spell_icons()
    elif isinstance(content_type, Item):
        folder = config.get_item_icons()
    elif isinstance(content_type, ClassAction):
        folder = config.get_ability_icons()
    elif isinstance(content_type, NPC):
        return _resolve_image_for_npc(config, content_type)
    guess_file_name = content_type.name.replace(" ", "_").lower()
    guess = folder / f"{guess_file_name}.png"
    return guess if guess.exists() else None

def _resolve_image_for_npc(config: Config, npc) -> Path | None:
    for attr in ("portrait_path", "image_path"):
        p = getattr(npc, attr, None)
        if p and Path(p).exists():
            return Path(p)
    guess_file_name = npc.name.replace(" ", "_").lower()
    guess = config.get_npc_portraits() / f"{guess_file_name}.png"
    return guess if guess.exists() else None

class QFormDetailWindowBase(QtWidgets.QMainWindow):
    form: QtWidgets.QFormLayout
    buttons: QtWidgets.QDialogButtonBox

    def __init__(self, entry: Spell | Item | ClassAction | NPC | Condition, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.entry = entry
        self.kb = kb
        self.setWindowTitle(f"{entry.__class__.__name__} — {entry.name}")
        self.resize(600, 520)

        DMHelperTheme.apply_theme(self)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        content = QtWidgets.QWidget()
        self.form = QtWidgets.QFormLayout(content)
        self.form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        
        self.form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.form.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.WrapLongRows)

        if not isinstance(entry, Condition):
            icon_path = _resolve_image_for_entry(self.config, entry)
            if icon_path:
                img_label = QtWidgets.QLabel()
                img_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
                pix = QtGui.QPixmap(str(icon_path))
                if not pix.isNull():
                    img_label.setPixmap(pix.scaledToWidth(150, QtCore.Qt.TransformationMode.SmoothTransformation))
                    self.form.addRow(None, img_label)
            elif isinstance(entry, NPC):
                generate_btn = QtWidgets.QPushButton("Generate Portrait")
                generate_btn.setToolTip("Generate an AI portrait for this NPC")
                generate_btn.clicked.connect(self.generate_portrait)    # This is a bit weird but works
                self.form.addRow(None, generate_btn)

        scroll.setWidget(content)

        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        self.buttons.rejected.connect(self.close)
        self.buttons.accepted.connect(self.close)

        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.addWidget(scroll)
        layout.addWidget(self.buttons)
        self.setCentralWidget(central_widget)

    def label(self, text: str) -> QtWidgets.QLabel:
        lab = QtWidgets.QLabel(text)
        lab.setWordWrap(True)
        lab.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse |
            QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        lab.setMinimumWidth(300)
        lab.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        return lab

class SpellDetailWindow(QFormDetailWindowBase):
    def __init__(self, spell: Spell, kb: KnowledgeBase, parent=None):
        super().__init__(spell, kb, parent)

        self.form.addRow("<b>Name:</b>", self.label(spell.name))
        self.form.addRow("<b>Level:</b>", self.label(str(spell.level)))
        self.form.addRow("<b>School:</b>", self.label(spell.school))
        self.form.addRow("<b>Casting Time</b>:", self.label(spell.casting_time))
        self.form.addRow("<b>Range:</b>", self.label(spell.range))
        self.form.addRow("<b>Damage:</b>", self.label(spell.damage if spell.damage else "N/A"))
        self.form.addRow("<b>Components:</b>", self.label(spell.components))
        self.form.addRow("<b>Duration:</b>", self.label(spell.duration))
        self.form.addRow("<b>Upcasting:</b>", self.label(spell.upcast_info))
        self.form.addRow("<b>Description:</b>", self.label(spell.description or ""))


class ItemDetailWindow(QFormDetailWindowBase):
    def __init__(self, item, kb: KnowledgeBase, parent=None):
        super().__init__(item, kb, parent)

        self.form.addRow("<b>Name:</b>", self.label(item.name))
        self.form.addRow("<b>Rarity:</b>", self.label(item.rarity))
        self.form.addRow("<b>Attunement:</b>", self.label("Yes" if item.attunement else "No"))
        self.form.addRow("<b>Tags:</b>", self.label(", ".join(getattr(item, "tags", []))))
        self.form.addRow("<b>Aliases:</b>", self.label(", ".join(getattr(item, "aliases", []))))
        self.form.addRow("<b>Description:</b>", self.label(item.description or ""))


class NPCDetailWindow(QFormDetailWindowBase):
    npc: NPC

    def __init__(self, npc: NPC, kb: KnowledgeBase, parent=None):
        self.npc = npc
        super().__init__(npc, kb, parent)

        self.form.addRow("<b>Name:</b>", self.label(npc.name))
        self.form.addRow("<b>Race:</b>", self.label(npc.race.value))
        self.form.addRow("<b>Sex:</b>", self.label(npc.sex))
        self.form.addRow("<b>Age:</b>", self.label(npc.age))
        self.form.addRow("<b>Alignment:</b>", self.label(npc.alignment.value))

        status_label = self.label("Alive ✓" if npc.alive else "Deceased ☠️")
        if not npc.alive:
            status_label.setStyleSheet("color: #cc0000; font-weight: bold;")
        else:
            status_label.setStyleSheet("color: #00aa00; font-weight: bold;")
        self.form.addRow("<b>Status:</b>", status_label)

        self.form.addRow("<b>Appearance:</b>", self.label(npc.appearance or ""))
        self.form.addRow("<b>Backstory:</b>", self.label(npc.backstory or ""))

        sb = npc.stat_block
        sb_text = sb.display_name if sb else "None"
        self.stat_btn = QtWidgets.QPushButton(sb_text)
        self.stat_btn.setEnabled(sb is not None)
        self.stat_btn.clicked.connect(self.open_statblock)
        self.form.addRow("<b>Stat Block:</b>", self.stat_btn)
        
        edit_btn = QtWidgets.QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_npc)
        self.buttons.addButton(edit_btn, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        
        campaign_notes_btn = QtWidgets.QPushButton("Campaign Notes")
        campaign_notes_btn.clicked.connect(self.open_campaign_notes)
        self.buttons.addButton(campaign_notes_btn, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        
        delete_btn = QtWidgets.QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_npc)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        self.buttons.addButton(delete_btn, QtWidgets.QDialogButtonBox.ButtonRole.DestructiveRole)
        
    def open_statblock(self):
        if not self.npc.stat_block:
            return
        window = StatBlockDetailWindow(self.npc.stat_block, self.kb, self.npc.additional_traits, self)
        window.show()

    def generate_portrait(self):
        """Generate an AI portrait for this NPC with loading dialog and auto-refresh"""
        try:
            progress = QtWidgets.QProgressDialog("Generating portrait...", "Cancel", 0, 0, self)
            progress.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Stability AI Image Generation")
            progress.setAutoClose(False)  # Don't auto-close so we control it
            progress.setAutoReset(False)
            progress.setCancelButton(None)  # Remove cancel button for simplicity
            progress.show()
            
            QtWidgets.QApplication.processEvents()
            
            image_generator = ImageGenerator()
            image_generator.create_character_portrait(self.npc, ImageGenerationMode.CORE)
            
            progress.close()
            
            portrait_path = _resolve_image_for_npc(self.config, self.npc)
            if portrait_path and Path(portrait_path).exists():
                # Portrait generated successfully - show success message
                QtWidgets.QMessageBox.information(self, "Success", 
                    f"Portrait generated successfully for {self.npc.name}!")
                
                self.reload_window()
            else:
                QtWidgets.QMessageBox.warning(self, "Error", 
                    "Portrait generation completed but image file was not found. Please check the Media/NPCs directory.")
                    
        except Exception as e:
            # Make sure to close progress dialog on error
            if 'progress' in locals():
                progress.close()
            QtWidgets.QMessageBox.critical(self, "Error", 
                f"Failed to generate portrait:\n{str(e)}")

    def edit_npc(self):
        """Edit this NPC using the edit dialog"""
        dialog = AddNPCDialog(self, edit_npc=self.npc)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Reload the window to show updated NPC data
            self.reload_window()

    def reload_window(self):
        """Reload the NPC detail window to show updated portrait"""
        geometry = self.geometry()
        
        new_window = NPCDetailWindow(self.npc, self.kb, self.parent())
        new_window.setGeometry(geometry)  # Keep same position/size
        new_window.show()
        
        self.close()

    def open_campaign_notes(self):
        """Open the campaign notes dialog for this NPC"""
        dialog = CampaignNotesDialog(self.npc, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # NPC's campaign_notes have been updated, optionally refresh the window
            pass

    def delete_npc(self):
        """Delete this NPC permanently after confirmation"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Delete NPC",
            f"Are you sure? This will permanently delete {self.npc.name}.",
            QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel,
            QtWidgets.QMessageBox.StandardButton.Cancel  # Default to Cancel
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Ok:
            try:
                npcs_file = Path(self.config.data_dir) / "npcs.json"
                
                if npcs_file.exists():
                    with open(npcs_file, 'r', encoding='utf-8') as f:
                        npcs_data = json.load(f)
                    
                    # Find and remove the NPC by name
                    original_count = len(npcs_data)
                    npcs_data = [npc for npc in npcs_data if npc.get("name") != self.npc.name]
                    
                    if len(npcs_data) < original_count:
                        # NPC was found and removed
                        with open(npcs_file, 'w', encoding='utf-8') as f:
                            json.dump(npcs_data, f, indent=2, ensure_ascii=False)
                        
                        QtWidgets.QMessageBox.information(
                            self,
                            "NPC Deleted",
                            f"{self.npc.name} has been permanently deleted."
                        )
                        
                        self.close()
                        
                        if self.parent() and hasattr(self.parent(), 'populate_npcs'):
                            self.parent().populate_npcs()
                    else:
                        QtWidgets.QMessageBox.warning(
                            self,
                            "Not Found",
                            f"Could not find {self.npc.name} in the database."
                        )
                else:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Error",
                        "NPCs data file not found."
                    )
                    
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete NPC:\n{str(e)}"
                )

class LocationDetailWindow(QtWidgets.QMainWindow):
    def __init__(self, location: Location, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.location = location
        self.kb = kb
        self.setWindowTitle(f"Location — {location.name}")
        self.resize(700, 600)

        DMHelperTheme.apply_theme(self)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        content = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(content)
        vbox.setContentsMargins(12, 12, 12, 12)
        vbox.setSpacing(10)

        def label(text: str, bold: bool = False):
            lab = QtWidgets.QLabel(text)
            lab.setWordWrap(True)
            lab.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextSelectableByMouse |
                QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse
            )
            if bold:
                f = lab.font()
                f.setBold(True)
                lab.setFont(f)
            return lab

        vbox.addWidget(label(location.name, bold=True))
        vbox.addWidget(label(f"Region: {location.region or 'Unknown'}"))
        vbox.addWidget(label(f"Description: {location.description or 'No description'}"))
        
        tags = ", ".join(location.tags) if location.tags else "None"
        vbox.addWidget(label(f"Tags: {tags}"))

        vbox.addSpacing(10)

        vbox.addWidget(label("NPCs in this Location:", bold=True))
        
        if location.npcs:
            for npc in location.npcs:
                # Create a horizontal layout for NPC name and remove button
                npc_layout = QtWidgets.QHBoxLayout()
                
                # NPC name button (clickable to open details)
                npc_item = QtWidgets.QPushButton(npc.name)
                npc_item.setToolTip(npc.appearance or "")
                npc_item.clicked.connect(lambda checked, n=npc: self.open_npc_detail(n))
                npc_item.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding: 8px;
                        margin: 2px 0;
                        border: 1px solid #666;
                        border-radius: 4px;
                        background-color: #ffffff;
                        color: #2c3e50;
                        font-weight: bold;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #e8f4f8;
                        border-color: #3498db;
                        color: #1e3a5f;
                    }
                    QPushButton:pressed {
                        background-color: #d6eaf8;
                    }
                """)
                npc_layout.addWidget(npc_item)
                
                # Remove button
                remove_btn = QtWidgets.QPushButton("Remove")
                remove_btn.setToolTip(f"Remove {npc.name} from this location")
                remove_btn.clicked.connect(lambda checked, n=npc: self.remove_npc_from_location(n))
                remove_btn.setMaximumWidth(70)
                remove_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ff6b6b;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        padding: 5px;
                        margin: 2px 0;
                    }
                    QPushButton:hover {
                        background-color: #ff5252;
                    }
                """)
                npc_layout.addWidget(remove_btn)
                
                # Create widget to hold the layout
                npc_widget = QtWidgets.QWidget()
                npc_widget.setLayout(npc_layout)
                vbox.addWidget(npc_widget)
        else:
            vbox.addWidget(label("No NPCs in this location"))

        vbox.addSpacing(10)

        vbox.addWidget(label("Add NPC to Location:", bold=True))
        
        self.npc_dropdown = QtWidgets.QComboBox()
        self.populate_npc_dropdown()
        vbox.addWidget(self.npc_dropdown)
        
        add_npc_layout = QtWidgets.QHBoxLayout()
        add_btn = QtWidgets.QPushButton("Add NPC to Location")
        add_btn.clicked.connect(self.add_npc_to_location)
        add_npc_layout.addWidget(add_btn)
        add_npc_layout.addStretch()
        vbox.addLayout(add_npc_layout)

        vbox.addSpacing(10)

        vbox.addWidget(label("Loot in this Location:", bold=True))
        
        if location.loot:
            for item in location.loot:
                # Create a button for each item (clickable to open details)
                item_btn = QtWidgets.QPushButton(item.name)
                item_btn.setToolTip(item.description or "")
                item_btn.clicked.connect(lambda checked, i=item: self.open_item_detail(i))
                item_btn.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding: 8px;
                        margin: 2px 0;
                        border: 1px solid #666;
                        border-radius: 4px;
                        background-color: #fff8dc;
                        color: #8b4513;
                        font-weight: bold;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #ffebcd;
                        border-color: #daa520;
                        color: #654321;
                    }
                    QPushButton:pressed {
                        background-color: #ffe4b5;
                    }
                """)
                vbox.addWidget(item_btn)
        else:
            vbox.addWidget(label("No loot in this location"))

        scroll.setWidget(content)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.close)
        btns.accepted.connect(self.close)

        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.addWidget(scroll)
        layout.addWidget(btns)
        self.setCentralWidget(central_widget)

    def populate_npc_dropdown(self):
        """Populate dropdown with NPCs not already in this location"""
        self.npc_dropdown.clear()
        
        try:
            repo = Repo(self.config.data_dir)
            repo.load_all()
            all_npcs = list(repo.npcs)
            
            existing_npc_names = {npc.name for npc in self.location.npcs}
            
            available_npcs = [npc for npc in all_npcs if npc.name not in existing_npc_names]
            
            if not available_npcs:
                self.npc_dropdown.addItem("No NPCs available to add", None)
                return
                
            available_npcs.sort(key=lambda x: x.name.lower())
            
            for npc in available_npcs:
                self.npc_dropdown.addItem(npc.name, npc)
                
        except Exception as e:
            print(f"Error loading NPCs: {e}")
            self.npc_dropdown.addItem("Error loading NPCs", None)

    def add_npc_to_location(self):
        """Add selected NPC to this location"""
        npc = self.npc_dropdown.currentData()
        if not npc:
            QtWidgets.QMessageBox.information(self, "No NPC Selected", 
                "Please select an NPC to add to this location.")
            return
        
        existing_npc_names = {existing_npc.name for existing_npc in self.location.npcs}
        if npc.name in existing_npc_names:
            QtWidgets.QMessageBox.information(self, "NPC Already Present", 
                f"'{npc.name}' is already in '{self.location.name}'.")
            return
        
        try:
            self.location.add_npc(npc)
            
            self.save_locations_to_json()
            
            QtWidgets.QMessageBox.information(self, "NPC Added", 
                f"'{npc.name}' has been added to '{self.location.name}'.")
            
            self.refresh_window()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", 
                f"Failed to add NPC to location:\n{str(e)}")

    def remove_npc_from_location(self, npc):
        """Remove an NPC from this location"""
        reply = QtWidgets.QMessageBox.question(self, "Remove NPC",
            f"Are you sure you want to remove '{npc.name}' from '{self.location.name}'?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                # Remove NPC from location
                self.location.remove_npc(npc)
                
                # Save changes to locations.json
                self.save_locations_to_json()
                
                # Show success message
                QtWidgets.QMessageBox.information(self, "NPC Removed", 
                    f"'{npc.name}' has been removed from '{self.location.name}'.")
                
                # Refresh the window to show the updated list
                self.refresh_window()
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", 
                    f"Failed to remove NPC from location:\n{str(e)}")

    def open_npc_detail(self, npc):
        """Open the NPC detail window"""
        window = NPCDetailWindow(npc, self.kb, self)
        window.show()

    def open_item_detail(self, item):
        """Open the Item detail window"""
        window = ItemDetailWindow(item, self.kb, self)
        window.show()

    def refresh_window(self):
        """Refresh the location detail window to show updated data"""
        geometry = self.geometry()
        
        new_window = LocationDetailWindow(self.location, self.kb, self.parent())
        new_window.setGeometry(geometry)  # Keep same position/size
        new_window.show()
        
        self.close()

    def save_locations_to_json(self):
        """Update the locations.json file with current location data"""
        try:
            # Path to locations.json
            locations_file = Path(self.config.data_dir) / "locations.json"
            
            if not locations_file.exists():
                raise Exception("Locations file not found")
            
            # Load existing locations data
            with open(locations_file, 'r', encoding='utf-8') as f:
                locations_data = json.load(f)
            
            # Find and update the location entry
            location_updated = False
            for loc_entry in locations_data:
                # Match by name (locations should have unique names)
                if loc_entry.get("name") == self.location.name:
                    # Update the npc_ids field with current NPCs
                    loc_entry["npc_ids"] = [npc.name for npc in self.location.npcs]
                    location_updated = True
                    break
            
            if not location_updated:
                raise Exception(f"Could not find location '{self.location.name}' in the data file")
            
            # Save back to file
            with open(locations_file, 'w', encoding='utf-8') as f:
                json.dump(locations_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving locations: {e}")
            # Don't show error to user for now, just log it
            # QtWidgets.QMessageBox.warning(self, "Save Error", 
            #     f"Could not save changes to locations file:\n{str(e)}")

    def open_npc_detail(self, npc: NPC):
        """Open the NPC detail window"""
        window = NPCDetailWindow(npc, self.kb, self)
        window.show()

class ConditionDetailWindow(QFormDetailWindowBase):
    def __init__(self, condition, kb: KnowledgeBase, parent=None):
        self.condition = condition
        super().__init__(condition, kb, parent)
        
        self.form.addRow("<b>Name:</b>", self.label(condition.name))
        self.form.addRow("<b>Description:</b>", self.label(condition.description or ""))

class StatBlockDetailWindow(QtWidgets.QMainWindow):
    def __init__(self, sb: StatBlock, kb: KnowledgeBase, traits: list | None = None, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.sb = sb
        self.kb = kb
        self.traits = traits if traits is not None else []
        
        DMHelperTheme.apply_theme(self)
        
        self._hover = HoverPreview(self)

        self.setWindowTitle("Stat Block")
        self.resize(640, 720)

        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        content = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(content)
        vbox.setContentsMargins(12, 12, 12, 12)
        vbox.setSpacing(10)

        def label(text: str, bold: bool = False):
            lab = QtWidgets.QLabel(text)
            lab.setWordWrap(True)
            lab.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextSelectableByMouse |
                QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse
            )
            if bold:
                f = lab.font()
                f.setBold(True)
                lab.setFont(f)
            return lab
        
        def field_label(field_name: str, value: str):
            lab = QtWidgets.QLabel(f"<b>{field_name}:</b> {value}")
            lab.setWordWrap(True)
            lab.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextSelectableByMouse |
                QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse
            )
            return lab
        
        # Helper for section headings with enhanced styling
        def section_heading(text: str):
            lab = QtWidgets.QLabel(text)
            lab.setStyleSheet("""
                font-size: 14pt;
                font-weight: bold;
                color: white;
                border-bottom: 2px solid #4A90E2;
                padding-bottom: 4px;
                margin-top: 8px;
                margin-bottom: 4px;
            """)
            return lab

        if isinstance(sb, PcClass):
            vbox.addWidget(section_heading("Player Class"))
            name = getattr(sb, "name", None)
            level = getattr(sb, "level", None)
            spells = getattr(sb, "spells", [])
            weapons = getattr(sb, "weapons", [])
            armor_class = getattr(sb, "armor_class", None)
            hit_points = getattr(sb, "hit_points", None)
            move_speed = getattr(sb, "move_speed", None)
            proficiency_bonus = getattr(sb, "proficiency_bonus", None)
            spell_save_dc = getattr(sb, "spell_save_dc", None)
            spell_attack_modifier = getattr(sb, "spell_attack_modifier", None)
            
            class_info_widget = QtWidgets.QWidget()
            class_info_layout = QtWidgets.QHBoxLayout(class_info_widget)
            class_info_layout.setContentsMargins(0, 0, 0, 0)
            
            left_column = QtWidgets.QVBoxLayout()
            left_column.addWidget(field_label("Class", getattr(name, 'value', str(name) or 'Unknown')))
            left_column.addWidget(field_label("Level", str(level if level is not None else 'Unknown')))
            if armor_class is not None:
                left_column.addWidget(field_label("Armor Class", str(armor_class)))
            if hit_points is not None:
                left_column.addWidget(field_label("Hit Points", str(hit_points)))
            
            right_column = QtWidgets.QVBoxLayout()
            if move_speed is not None:
                right_column.addWidget(field_label("Move Speed", f"{move_speed} ft"))
            if proficiency_bonus is not None:
                right_column.addWidget(field_label("Proficiency Bonus", f"+{proficiency_bonus}"))
            if spell_save_dc is not None:
                right_column.addWidget(field_label("Spell Save DC", str(spell_save_dc)))
            if spell_attack_modifier is not None:
                sign = "+" if spell_attack_modifier >= 0 else ""
                right_column.addWidget(field_label("Spell Attack Modifier", f"{sign}{spell_attack_modifier}"))
            
            class_info_layout.addLayout(left_column)
            class_info_layout.addLayout(right_column)
            vbox.addWidget(class_info_widget)
            
            ability_scores = getattr(sb, "ability_scores", None)
            if ability_scores:
                vbox.addWidget(section_heading("Ability Scores"))
                
                abilities_widget = QtWidgets.QWidget()
                abilities_layout = QtWidgets.QHBoxLayout(abilities_widget)
                abilities_layout.setContentsMargins(0, 0, 0, 0)
                
                left_column = QtWidgets.QVBoxLayout()
                left_column.addWidget(field_label("Strength", str(ability_scores.strength)))
                left_column.addWidget(field_label("Dexterity", str(ability_scores.dexterity)))
                left_column.addWidget(field_label("Constitution", str(ability_scores.constitution)))

                right_column = QtWidgets.QVBoxLayout()
                right_column.addWidget(field_label("Intelligence", str(ability_scores.intelligence)))
                right_column.addWidget(field_label("Wisdom", str(ability_scores.wisdom)))
                right_column.addWidget(field_label("Charisma", str(ability_scores.charisma)))
                
                abilities_layout.addLayout(left_column)
                abilities_layout.addLayout(right_column)
                vbox.addWidget(abilities_widget)
            
            spell_slots = getattr(sb, "spell_slots", [])
            if spell_slots:
                vbox.addWidget(section_heading("Spell Slots"))
                mage_armor_cast = False
                if sb.name == PcClassName.Wizard or sb.name == PcClassName.Sorcerer:
                    mage_armor_cast = "Mage Armor" in spells
                for slot in spell_slots:
                    slot_widget = QtWidgets.QWidget()
                    slot_layout = QtWidgets.QHBoxLayout(slot_widget)
                    slot_layout.setContentsMargins(0, 0, 0, 0)
                    
                    level_label = field_label(f"Level {slot.level}", "")
                    slot_layout.addWidget(level_label)
                    
                    for i in range(slot.count):
                        checkbox = QtWidgets.QCheckBox()
                        checkbox.setToolTip(f"Spell slot {i+1}")
                        if mage_armor_cast and slot.level == 1 and i == slot.count - 1:
                            checkbox.setChecked(False)  # Last slot used for Mage Armor
                        else:
                            checkbox.setChecked(True)  # Start all slots as available (checked/blue)
                        
                        checkbox.setStyleSheet("""
                            QCheckBox::indicator {
                                width: 16px;
                                height: 16px;
                                border: 2px solid #555;
                                border-radius: 3px;
                                background-color: transparent;
                            }
                            QCheckBox::indicator:checked {
                                background-color: #4A90E2;
                                border: 2px solid #357ABD;
                            }
                            QCheckBox::indicator:unchecked {
                                background-color: transparent;
                                border: 2px solid #555;
                            }
                        """)
                        
                        slot_layout.addWidget(checkbox)
                    
                    slot_layout.addStretch()
                    vbox.addWidget(slot_widget)

            vbox.addWidget(section_heading("Weapons"))
            weapons_text = ', '.join(weapons) if weapons else 'None'
            weapons_tb = QtWidgets.QTextBrowser()
            weapons_tb.setOpenExternalLinks(False)
            weapons_tb.setOpenLinks(False)
            weapons_tb.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
            weapons_tb.setReadOnly(True)
            weapons_tb.setAcceptRichText(True)
            weapons_tb.setMouseTracking(True)
            weapons_tb.viewport().setMouseTracking(True)
            
            html = self.kb.linkify(weapons_text)
            weapons_tb.setHtml(f"<div style='font-size: 12pt; line-height: 1.35'>{html}</div>")
            weapons_tb.anchorClicked.connect(self._on_anchor_clicked)
            weapons_tb.highlighted.connect(self._on_link_hovered)
            vbox.addWidget(weapons_tb)

            vbox.addWidget(section_heading("Spells"))
            if not spells:
                spells_text = 'None'
            else:
                mid_point = (len(spells) + 1) // 2
                left_spells = spells[:mid_point]
                right_spells = spells[mid_point:]
                
                left_html = self.kb.linkify('<br>'.join(left_spells))
                right_html = self.kb.linkify('<br>'.join(right_spells)) if right_spells else ''
                
                spells_text = f"""
                <table width="100%" style="border: none;">
                    <tr style="vertical-align: top;">
                        <td width="50%" style="border: none; padding-right: 10px;">{left_html}</td>
                        <td width="50%" style="border: none; padding-left: 10px;">{right_html}</td>
                    </tr>
                </table>
                """
            
            spells_tb = QtWidgets.QTextBrowser()
            spells_tb.setOpenExternalLinks(False)
            spells_tb.setOpenLinks(False)
            spells_tb.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
            spells_tb.setReadOnly(True)
            spells_tb.setAcceptRichText(True)
            spells_tb.setMouseTracking(True)
            spells_tb.viewport().setMouseTracking(True)
            
            spells_tb.setHtml(f"<div style='font-size: 12pt; line-height: 1.35'>{spells_text}</div>")
            spells_tb.anchorClicked.connect(self._on_anchor_clicked)
            spells_tb.highlighted.connect(self._on_link_hovered)
            vbox.addWidget(spells_tb)

        elif isinstance(sb, MonsterManual):
            vbox.addWidget(label("Monster Manual Entry", bold=True))

            sb_image = getattr(sb, "stat_block_image", None)
            name = getattr(sb, "monster_name", "Unknown")
            vbox.addWidget(label(f"Name: {name}"))

            img_label = QtWidgets.QLabel()
            img_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
            if sb_image:
                sb_image_path = self.config.get_monster_manual_pages() / sb_image
                pix = QtGui.QPixmap(str(sb_image_path))
                if not pix.isNull():
                    # scale-to-fit width while keeping aspect
                    img_label.setPixmap(pix)
                    # We'll scale after widget shows (see resizeEvent override below)
                    self._image_label = img_label
                    self._image_pixmap = pix
                else:
                    img_label.setText(f"(Image not found or failed to load)\n{sb_image_path}")
            else:
                img_label.setText("(No image path specified)")
            vbox.addWidget(img_label)

        else:
            vbox.addWidget(label("Unknown StatBlock type.", bold=True))
            vbox.addWidget(label(f"Class: {sb.__class__.__name__}"))

        # === Additional Information ===
        vbox.addSpacing(8)
        vbox.addWidget(self._bold_label("Additional Information"))
        if not self.traits:
            vbox.addWidget(self._plain_label("— (none provided) —"))
        else:
            tb = QtWidgets.QTextBrowser()
            tb.setOpenExternalLinks(False)  # we'll handle clicks
            tb.setOpenLinks(False)
            tb.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
            tb.setReadOnly(True)
            tb.setAcceptRichText(True)

            tb.setMouseTracking(True)  # needed for hover events
            tb.viewport().setMouseTracking(True)

            combined_html = ""
            for i, t in enumerate(self.traits):
                html = self.kb.linkify(t)
                if i > 0:
                    combined_html += "<br><br>"
                combined_html += html
            
            tb.setHtml(f"<div style='font-size: 12pt; line-height: 1.35'>{combined_html}</div>")
            tb.anchorClicked.connect(self._on_anchor_clicked)
            tb.highlighted.connect(self._on_link_hovered)  # hover signal gives URL as text
            vbox.addWidget(tb)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.close)
        btns.accepted.connect(self.close)
        
        if isinstance(sb, PcClass):
            edit_btn = QtWidgets.QPushButton("Edit")
            edit_btn.setToolTip("Edit PC Class stat block")
            edit_btn.clicked.connect(self.edit_pc_class)
            btns.addButton(edit_btn, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        
        layout.addWidget(btns)
        
        self.setCentralWidget(central_widget)

    def _plain_label(self, text: str) -> QtWidgets.QLabel:
        lab = QtWidgets.QLabel(text)
        lab.setWordWrap(True)
        lab.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse |
                                    QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse)
        return lab

    def _bold_label(self, text: str) -> QtWidgets.QLabel:
        """Create a section heading label with enhanced styling"""
        lab = QtWidgets.QLabel(text)
        lab.setStyleSheet("""
            font-size: 14pt;
            font-weight: bold;
            color: white;
            border-bottom: 2px solid #4A90E2;
            padding-bottom: 4px;
            margin-top: 8px;
            margin-bottom: 4px;
        """)
        return lab
    
    def _on_link_hovered(self, qurl: QtCore.QUrl):
        if not qurl or qurl.isEmpty():
            self._hover.hide()
            return
        
        name = QtCore.QUrl.fromPercentEncoding(qurl.toEncoded())
        entry = self.kb.resolve(name)

        if not entry:
            self._hover.hide()
            return
        pos = QtGui.QCursor.pos()
        self._hover.show_text(entry.hover_description, pos)

    def _on_anchor_clicked(self, url: QtCore.QUrl):
        name = url.toString()
        entry = self.kb.resolve(name)
        if not entry:
            return
        if isinstance(entry.content, Spell):
            window = SpellDetailWindow(entry.content, self.kb, self)
        elif isinstance(entry.content, Item):
            window = ItemDetailWindow(entry.content, self.kb, self)
        elif isinstance(entry.content, ClassAction):
            # Not implemented yet
            QtWidgets.QMessageBox.information(self, "Not Implemented",
                "Class Action detail view is not implemented yet.")
        elif isinstance(entry.content, NPC):
            window = NPCDetailWindow(entry.content, self.kb, self)
        elif isinstance(entry.content, Condition):
            window = ConditionDetailWindow(entry.content, self.kb, self)
        else:
            QtWidgets.QMessageBox.warning(self, "Unknown Entry",
                "The selected entry type is not recognized.")
        window.show()

    def edit_pc_class(self):
        """Open dialog to edit PC Class stat block"""
        if not isinstance(self.sb, PcClass):
            return
        
        # Try to get the NPC from the parent window
        npc = None
        parent = self.parent()
        if isinstance(parent, NPCDetailWindow):
            npc = parent.npc
            
        dialog = EditPcClassDialog(self.sb, npc, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Reload the window to show updated stat block
            self.reload_window()
    
    def reload_window(self):
        """Reload the stat block window to show updated data"""
        # Store the current window position and size
        geometry = self.geometry()
        
        # Create a new window with the same stat block (which has been updated)
        new_window = StatBlockDetailWindow(self.sb, self.kb, self.traits, self.parent())
        new_window.setGeometry(geometry)  # Keep same position/size
        new_window.show()
        
        # Close the current window
        self.close()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Keep monster image scaled to width while preserving aspect ratio."""
        super().resizeEvent(event)
        if hasattr(self, "_image_label") and hasattr(self, "_image_pixmap"):
            area_w = self.width() - 64  # approximate padding
            if area_w > 100:
                scaled = self._image_pixmap.scaledToWidth(area_w, QtCore.Qt.TransformationMode.SmoothTransformation)
                self._image_label.setPixmap(scaled)
