from PyQt6 import QtWidgets, QtCore
import json
from pathlib import Path
import shutil

from ..theme import DMHelperTheme
from ..repo import Repo

from ..config import Config

from ..Dataclasses import Race, Alignment, PcClassName, MonsterManual, PcClass, NPC, Item, Spell, Condition, Location, SpellSchool, Rarity
from ..AIGen import SoundGenerationMode, SoundGenerator

class AddEntryDialogBase(QtWidgets.QDialog):
    entry_name: str
    edit_entry: NPC | Item | Spell | Location | Condition | None
    vbox_layout: QtWidgets.QVBoxLayout
    form: QtWidgets.QFormLayout
    buttons: QtWidgets.QDialogButtonBox

    def __init__(self, entry_name: str, edit_entry: NPC | Item | Spell | Location | Condition | None = None, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.edit_entry = edit_entry
        self.entry_name = entry_name

        title = f"Edit {entry_name}" if self.edit_entry else f"Add {entry_name}"
        self.setWindowTitle(title)
        self.resize(500, 400)   # Should experiment with this

        DMHelperTheme.apply_theme(self)

        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        form_widget = QtWidgets.QWidget()
        self.form = QtWidgets.QFormLayout(form_widget)

        self.vbox_layout.addWidget(form_widget)

        # Buttons
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.ok_button_slot)
        self.buttons.rejected.connect(self.reject)
        self.vbox_layout.addWidget(self.buttons)

    # Implement this is derived classes
    def ok_button_slot():
        pass
        

class AddNPCDialog(AddEntryDialogBase):
    """Dialog for adding or editing an NPC"""
    def __init__(self, parent=None, edit_npc=None):
        super().__init__(entry_name="NPC", edit_entry=edit_npc, parent=parent)
        self.original_name = self.edit_entry.name if self.edit_entry else None  # Store original name for updates

        self.resize(500, 700)
                
        # Name field
        self.name_field = QtWidgets.QLineEdit()
        self.name_field.setPlaceholderText("Enter NPC name...")
        self.form.addRow("Name*:", self.name_field)
        
        # Race field
        self.race_combo = QtWidgets.QComboBox()
        # Sort races alphabetically by their display value
        sorted_races = sorted(Race, key=lambda r: r.value)
        for race in sorted_races:
            self.race_combo.addItem(race.value, race)
        self.form.addRow("Race*:", self.race_combo)
        
        # Sex field
        self.sex_combo = QtWidgets.QComboBox()
        self.sex_combo.addItems(["Male", "Female", "Non-binary", "Other"])
        self.sex_combo.setEditable(True)  # Allow custom input
        self.form.addRow("Sex:", self.sex_combo)

        self.age_field = QtWidgets.QLineEdit()
        self.age_field.setPlaceholderText("Describe the NPC's age...")
        self.form.addRow("Age:", self.age_field)
        
        # Alignment field
        self.alignment_combo = QtWidgets.QComboBox()
        for alignment in Alignment:
            self.alignment_combo.addItem(alignment.value, alignment)
        self.form.addRow("Alignment*:", self.alignment_combo)
        
        # Stat Block fields - Type and Selection
        self.stat_block_type_combo = QtWidgets.QComboBox()
        self.stat_block_type_combo.addItems(["Monster Manual", "PC Class"])
        self.stat_block_type_combo.currentTextChanged.connect(self.update_stat_block_options)
        self.form.addRow("Stat Block Type:", self.stat_block_type_combo)
        
        self.stat_block_selection_combo = QtWidgets.QComboBox()
        self.form.addRow("Stat Block:", self.stat_block_selection_combo)
        
        # Initialize with Monster Manual options
        self.update_stat_block_options()
        
        # Appearance field
        self.appearance_field = QtWidgets.QTextEdit()
        self.appearance_field.setPlaceholderText("Describe the NPC's physical appearance...")
        self.appearance_field.setMaximumHeight(100)
        self.form.addRow("Appearance:", self.appearance_field)
        
        # Backstory field
        self.backstory_field = QtWidgets.QTextEdit()
        self.backstory_field.setPlaceholderText("Describe the NPC's background and history...")
        self.backstory_field.setMaximumHeight(120)
        self.form.addRow("Backstory:", self.backstory_field)
        
        # Additional traits field
        self.traits_field = QtWidgets.QTextEdit()
        self.traits_field.setPlaceholderText("Additional traits (one per line)...")
        self.traits_field.setMaximumHeight(80)
        self.form.addRow("Additional Traits:", self.traits_field)
        
        # Alive checkbox
        self.alive_checkbox = QtWidgets.QCheckBox("NPC is alive")
        self.alive_checkbox.setChecked(True)  # Default to alive
        self.alive_checkbox.setToolTip("Uncheck if this NPC is deceased")
        self.form.addRow("Status:", self.alive_checkbox)
        
        # Add note about required fields
        note_label = QtWidgets.QLabel("* Required fields")
        note_label.setStyleSheet("color: #888; font-size: 11px;")
        self.vbox_layout.addWidget(note_label)
                
        # Populate fields if editing an existing NPC
        if self.edit_entry:
            self.populate_fields()
        
        # Focus on name field
        self.name_field.setFocus()
    
    def ok_button_slot(self):
        self.save_npc()
    
    def populate_fields(self):
        """Populate form fields when editing an existing NPC"""
        npc = self.edit_entry
        
        # Name
        self.name_field.setText(npc.name)
        
        # Race
        for i in range(self.race_combo.count()):
            if self.race_combo.itemData(i) == npc.race:
                self.race_combo.setCurrentIndex(i)
                break
        
        # Sex
        self.sex_combo.setCurrentText(npc.sex)
        
        # Age
        if hasattr(npc, 'age') and npc.age:
            self.age_field.setText(npc.age)
        
        # Alignment
        for i in range(self.alignment_combo.count()):
            if self.alignment_combo.itemData(i) == npc.alignment:
                self.alignment_combo.setCurrentIndex(i)
                break
        
        # Stat Block
        if npc.stat_block:
            
            if isinstance(npc.stat_block, MonsterManual):
                self.stat_block_type_combo.setCurrentText("Monster Manual")
                self.update_stat_block_options()  # Update options first
                # Try to find and select the monster
                monster_name = npc.stat_block.monster_name
                for i in range(self.stat_block_selection_combo.count()):
                    if self.stat_block_selection_combo.itemText(i) == monster_name:
                        self.stat_block_selection_combo.setCurrentIndex(i)
                        break
            elif isinstance(npc.stat_block, PcClass):
                self.stat_block_type_combo.setCurrentText("PC Class")
                self.update_stat_block_options()  # Update options first
                # Try to find and select the class
                class_name = npc.stat_block.name.value if hasattr(npc.stat_block.name, 'value') else str(npc.stat_block.name)
                for i in range(self.stat_block_selection_combo.count()):
                    if self.stat_block_selection_combo.itemText(i) == class_name:
                        self.stat_block_selection_combo.setCurrentIndex(i)
                        break
        
        # Appearance
        if npc.appearance:
            self.appearance_field.setPlainText(npc.appearance)
        
        # Backstory
        if npc.backstory:
            self.backstory_field.setPlainText(npc.backstory)
        
        # Additional traits
        if npc.additional_traits:
            traits_text = '\n'.join(npc.additional_traits)
            self.traits_field.setPlainText(traits_text)
        
        # Alive status
        if hasattr(npc, 'alive'):
            self.alive_checkbox.setChecked(npc.alive)
    
    def update_stat_block_options(self):
        """Update the stat block selection combo based on the type selected"""
        self.stat_block_selection_combo.clear()
        
        stat_block_type = self.stat_block_type_combo.currentText()
        
        if stat_block_type == "Monster Manual":
            # Load Monster Manual files from Media/MonsterManual
            try:
                monster_manual_dir = self.config.get_monster_manual_pages()
                if monster_manual_dir.exists():
                    # Get all image files (assuming they're the monster manual pages)
                    image_files = []
                    for ext in ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp']:
                        image_files.extend(monster_manual_dir.glob(ext))
                    
                    # Sort and add to combo
                    monster_names = sorted([f.stem for f in image_files])
                    nice_monster_names = []
                    for name in monster_names:
                        nice_name = name.replace("_", " ").title()
                        nice_monster_names.append(nice_name)
                    self.stat_block_selection_combo.addItems(nice_monster_names)
                else:
                    self.stat_block_selection_combo.addItem("No Monster Manual files found")
            except Exception as e:
                self.stat_block_selection_combo.addItem(f"Error loading Monster Manual: {e}")
                
        elif stat_block_type == "PC Class":
            # Load PC Classes
            try:
                pc_classes = [pc_class.value for pc_class in PcClassName]
                self.stat_block_selection_combo.addItems(sorted(pc_classes))
            except Exception as e:
                # Fallback to common D&D classes if enum not available
                common_classes = ["Barbarian", "Bard", "Cleric", "Druid", "Fighter", 
                                "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", 
                                "Warlock", "Wizard"]
                self.stat_block_selection_combo.addItems(common_classes)
    
    def save_npc(self):
        """Save the NPC (new or edited) to npcs.json"""
        try:
            # Validate required fields
            if not self.name_field.text().strip():
                QtWidgets.QMessageBox.warning(self, "Validation Error", "Name is required!")
                return
            
            # Get selected race and alignment
            race = self.race_combo.currentData()
            alignment = self.alignment_combo.currentData()
            
            # Create stat block based on selection
            stat_block_type = self.stat_block_type_combo.currentText()
            stat_block_name = self.stat_block_selection_combo.currentText()
            
            # If editing and the stat block type/name hasn't changed, preserve the existing stat block
            if self.edit_entry and self.edit_entry.stat_block:
                preserve_stat_block = False
                
                if isinstance(self.edit_entry.stat_block, MonsterManual) and stat_block_type == "Monster Manual":
                    # Check if monster name is the same
                    current_monster = self.edit_entry.stat_block.monster_name
                    if current_monster == stat_block_name or current_monster.replace("_", " ").title() == stat_block_name:
                        preserve_stat_block = True
                        stat_block = self.edit_entry.stat_block
                
                elif isinstance(self.edit_entry.stat_block, PcClass) and stat_block_type == "PC Class":
                    # Check if class name is the same
                    current_class = self.edit_entry.stat_block.name.value if hasattr(self.edit_entry.stat_block.name, 'value') else str(self.edit_entry.stat_block.name)
                    if current_class == stat_block_name:
                        preserve_stat_block = True
                        stat_block = self.edit_entry.stat_block
                
                if not preserve_stat_block:
                    # Stat block type or name changed, create a new one
                    if stat_block_type == "Monster Manual":
                        file_name = stat_block_name.replace(" ", "_").lower()
                        stat_block = MonsterManual(file_name=str(file_name))
                    else:  # PC Class
                        try:
                            pc_class_name = PcClassName(stat_block_name)
                        except ValueError:
                            pc_class_name = type('PcClassName', (), {'value': stat_block_name})()
                        stat_block = PcClass(name=pc_class_name)
            else:
                # Creating a new NPC or no existing stat block
                if stat_block_type == "Monster Manual":
                    file_name = stat_block_name.replace(" ", "_").lower()
                    stat_block = MonsterManual(file_name=str(file_name))
                else:  # PC Class
                    try:
                        pc_class_name = PcClassName(stat_block_name)
                    except ValueError:
                        pc_class_name = type('PcClassName', (), {'value': stat_block_name})()
                    stat_block = PcClass(name=pc_class_name)
            
            # Parse additional traits
            traits_text = self.traits_field.toPlainText().strip()
            traits = [line.strip() for line in traits_text.split('\n') if line.strip()] if traits_text else []
            
            # Get alive status
            alive = self.alive_checkbox.isChecked()
            
            # Preserve campaign_notes if editing
            campaign_notes = ""
            if self.edit_entry and hasattr(self.edit_entry, 'campaign_notes'):
                campaign_notes = self.edit_entry.campaign_notes
            
            # Create NPC object
            npc = NPC(
                name=self.name_field.text().strip(),
                race=race,
                sex=self.sex_combo.currentText().strip(),
                age=self.age_field.text().strip(),
                alignment=alignment,
                stat_block=stat_block,
                appearance=self.appearance_field.toPlainText().strip(),
                backstory=self.backstory_field.toPlainText().strip(),
                additional_traits=traits,
                campaign_notes=campaign_notes,
                alive=alive
            )
            
            # Save to JSON file
            # Find the original name by looking it up in the repository
            original_name = None
            if self.edit_entry:
                try:
                    repo = Repo(self.config.data_dir)
                    repo.load_all()
                    # Find the name by looking through npcs_by_name dictionary
                    for npc_name, npc_obj in repo.npcs_by_name.items():
                        if npc_obj is self.edit_entry or npc_obj.name == self.original_name:
                            original_name = npc_name
                            break
                except Exception as e:
                    print(f"Could not find original name: {e}")

            self.save_npc_to_json(npc, is_edit=self.edit_entry is not None, original_name=self.original_name)
            
            QtWidgets.QMessageBox.information(self, "Success", 
                f"NPC '{npc.name}' has been saved successfully!")
            self.accept()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", 
                f"Failed to save NPC:\n{str(e)}")
    
    def save_npc_to_json(self, npc: NPC, is_edit=False, original_name=None):
        """Save the NPC to npcs.json file"""
        
        # Path to npcs.json in the Data directory
        npcs_file = Path(self.config.data_dir) / "npcs.json"
        
        # Load existing NPCs
        if npcs_file.exists():
            with open(npcs_file, 'r', encoding='utf-8') as f:
                npcs_data = json.load(f)
        else:
            npcs_data = []
        
        # Convert NPC to dictionary format matching repo expectations
        # Handle different stat block types for JSON serialization
        
        if isinstance(npc.stat_block, MonsterManual):
            stat_block_data = {
                "type": "monstermanual",  # No underscore to match repo expectation
                "monster_name": npc.stat_block.monster_name.replace(" ", "_").lower()
            }
        elif isinstance(npc.stat_block, PcClass):
            stat_block_data = {
                "type": "pc_class",
                "class": npc.stat_block.name.value if hasattr(npc.stat_block.name, 'value') else str(npc.stat_block.name),
                "level": npc.stat_block.level,
                "ability_scores": {
                    "strength": npc.stat_block.ability_scores.strength,
                    "dexterity": npc.stat_block.ability_scores.dexterity,
                    "constitution": npc.stat_block.ability_scores.constitution,
                    "intelligence": npc.stat_block.ability_scores.intelligence,
                    "wisdom": npc.stat_block.ability_scores.wisdom,
                    "charisma": npc.stat_block.ability_scores.charisma
                },
                "spells": npc.stat_block.spells if hasattr(npc.stat_block, 'spells') else []
            }
        else:
            # Fallback for other stat block types
            stat_block_data = {
                "type": "basic",
                "name": getattr(npc.stat_block, 'display_name', 'Unknown')
            }
        
        if is_edit and original_name:
            npc_name = original_name
        else:
            npc_name = npc.name

        npc_dict = {
            "name": npc.name,
            "race": npc.race.value,
            "sex": npc.sex,
            "age": npc.age,
            "alignment": npc.alignment.value,
            "stat_block": stat_block_data,
            "appearance": npc.appearance,
            "backstory": npc.backstory,
            "additional_traits": npc.additional_traits,
            "campaign_notes": getattr(npc, 'campaign_notes', ""),
            "alive": getattr(npc, 'alive', True)
        }
        
        # Add or update NPC in the list
        if is_edit and original_name:
            updated = False
            for i, existing_npc in enumerate(npcs_data):
                if (original_name and existing_npc.get("name") == original_name):
                    print(f"Updating existing NPC: {original_name} -> {npc.name}")
                    npcs_data[i] = npc_dict
                    updated = True
                    break
            
            if not updated:
                # Original NPC not found, add as new
                print(f"Original NPC '{original_name}' not found, adding as new")
                npcs_data.append(npc_dict)
        else:
            # Add new NPC
            print(f"Adding new NPC: {npc_dict}")
            npcs_data.append(npc_dict)
        
        # Save back to file
        with open(npcs_file, 'w', encoding='utf-8') as f:
            json.dump(npcs_data, f, indent=2, ensure_ascii=False)

class AddSpellDialog(AddEntryDialogBase):
    def __init__(self, parent=None, edit_spell=None):
        super().__init__(entry_name="Spell", edit_entry=edit_spell, parent=parent)
        self.original_name = self.edit_entry.name if self.edit_entry else None
        
        # Spell Name field
        self.name_field = QtWidgets.QLineEdit()
        self.name_field.setPlaceholderText("Enter a name for this spell (e.g., 'Fire Ball', 'Hold Person', 'Disintegrate')...")
        self.form.addRow("Spell Name*:", self.name_field)

        self.level_field = QtWidgets.QSpinBox()
        self.level_field.setRange(0, 9)
        self.level_field.setValue(5)
        self.form.addRow("Level:", self.level_field)

        self.school_field = QtWidgets.QComboBox()
        for school in SpellSchool:
            self.school_field.addItem(school.value, school)
        self.form.addRow("School:", self.school_field)

        self.casting_time_field = QtWidgets.QLineEdit()
        self.casting_time_field.setPlaceholderText("e.g., '1 action', '1 minute', '1 reaction'...")
        self.form.addRow("Casting Time:", self.casting_time_field)

        self.range_field = QtWidgets.QLineEdit()
        self.range_field.setPlaceholderText("e.g., '60ft', 'Touch', 'Self'...")
        self.form.addRow("Range:", self.range_field)

        self.components_field = QtWidgets.QLineEdit()
        self.components_field.setPlaceholderText("e.g., 'V, S, M (a tiny ball of bat guano and sulfur)'...")
        self.form.addRow("Components:", self.components_field)

        self.duration_field = QtWidgets.QLineEdit()
        self.duration_field.setPlaceholderText("e.g., 'Instantaneous', 'Concentration, up to 1 minute'...")
        self.form.addRow("Duration:", self.duration_field)

        self.description_field = QtWidgets.QTextEdit()
        self.description_field.setPlaceholderText("Enter the spell description...")
        self.description_field.setMaximumHeight(150)
        self.form.addRow("Description:", self.description_field)

        self.damage_field = QtWidgets.QLineEdit()
        self.damage_field.setPlaceholderText("e.g., '8d6 fire damage', leave blank if none...")
        self.form.addRow("Damage:", self.damage_field)

        self.upcast_info_field = QtWidgets.QTextEdit()
        self.upcast_info_field.setPlaceholderText("Enter upcast information, or leave default...")
        self.upcast_info_field.setMaximumHeight(100)
        self.form.addRow("Upcast Info:", self.upcast_info_field)

        self.name_field.setFocus()
        
        if self.edit_entry:
            self.populate_fields()
    
    def populate_fields(self):
        spell = self.edit_entry
        self.name_field.setText(spell.name)
        self.level_field.setValue(spell.level)
        
        for i in range(self.school_field.count()):
            if self.school_field.itemData(i) == spell.school:
                self.school_field.setCurrentIndex(i)
                break
        
        self.casting_time_field.setText(spell.casting_time)
        self.range_field.setText(spell.range)
        self.components_field.setText(spell.components)
        self.duration_field.setText(spell.duration)
        self.description_field.setPlainText(spell.description or "")
        self.damage_field.setText(spell.damage or "")
        self.upcast_info_field.setPlainText(spell.upcast_info)

    def ok_button_slot(self):
        self.add_spell()

    def add_spell(self):
        """Save the spell (new) to spells.json"""
        try:
            # Validate required fields
            if not self.name_field.text().strip():
                QtWidgets.QMessageBox.warning(self, "Validation Error", "Spell name is required!")
                return
            
            # Create Spell object
            spell = Spell(
                name=self.name_field.text().strip(),
                level=self.level_field.value(),
                school=self.school_field.currentData(),
                casting_time=self.casting_time_field.text().strip(),
                range=self.range_field.text().strip(),
                components=self.components_field.text().strip(),
                duration=self.duration_field.text().strip(),
                description=self.description_field.toPlainText().strip(),
                damage=self.damage_field.text().strip() if self.damage_field.text().strip() else None,
                upcast_info=self.upcast_info_field.toPlainText().strip() if self.upcast_info_field.toPlainText().strip() else "Casting this spell at higher levels provides no additional benefit."
            )
            
            # Save to JSON file
            self.save_spell_to_json(spell)
            
            QtWidgets.QMessageBox.information(self, "Success", 
                f"Spell '{spell.name}' has been saved successfully!")
            self.accept()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", 
                f"Failed to save spell:\n{str(e)}")
            
    def save_spell_to_json(self, spell: Spell):
        """Save the Spell to spells.json file"""
        
        # Path to spells.json in the Data directory
        spells_file = Path(self.config.data_dir) / "spells.json"
        
        # Load existing Spells
        if spells_file.exists():
            with open(spells_file, 'r', encoding='utf-8') as f:
                spells_data = json.load(f)
        else:
            spells_data = []
        
        # Convert Spell to dictionary format
        spell_dict = {
            "name": spell.name,
            "level": spell.level,
            "school": spell.school.value,
            "casting_time": spell.casting_time,
            "range": spell.range,
            "components": spell.components,
            "duration": spell.duration,
            "description": spell.description,
            "damage": spell.damage,
            "upcast_info": spell.upcast_info,
            "tags": spell.tags,
            "aliases": spell.aliases
        }
        
        if self.edit_entry and self.original_name:
            updated = False
            for i, existing_spell in enumerate(spells_data):
                if existing_spell.get("name") == self.original_name:
                    spells_data[i] = spell_dict
                    updated = True
                    break
            if not updated:
                spells_data.append(spell_dict)
        else:
            spells_data.append(spell_dict)
        
        # Save back to file
        with open(spells_file, 'w', encoding='utf-8') as f:
            json.dump(spells_data, f, indent=2, ensure_ascii=False)

class AddItemDialog(AddEntryDialogBase):
    def __init__(self, parent=None, edit_item=None):
        super().__init__(entry_name="Item", edit_entry=edit_item, parent=parent)
        self.original_name = self.edit_entry.name if self.edit_entry else None
        
        self.name_field = QtWidgets.QLineEdit()
        self.name_field.setPlaceholderText("Enter a name for this item")
        self.form.addRow("Item Name*:", self.name_field)

        self.rarity_field = QtWidgets.QComboBox()
        for rarity in Rarity:
            self.rarity_field.addItem(rarity.value, rarity)
        self.form.addRow("Rarity:", self.rarity_field)

        self.description_field = QtWidgets.QTextEdit()
        self.description_field.setPlaceholderText("Enter the item description...")
        self.description_field.setMaximumHeight(150)
        self.form.addRow("Description:", self.description_field)

        self.attunement_checkbox = QtWidgets.QCheckBox()
        self.form.addRow("Requires Attunement:", self.attunement_checkbox)

        self.name_field.setFocus()
        
        if self.edit_entry:
            self.populate_fields()
    
    def populate_fields(self):
        item = self.edit_entry
        self.name_field.setText(item.name)
        
        for i in range(self.rarity_field.count()):
            if self.rarity_field.itemData(i) == item.rarity:
                self.rarity_field.setCurrentIndex(i)
                break
        
        self.description_field.setPlainText(item.description or "")
        self.attunement_checkbox.setChecked(item.attunement)

    def ok_button_slot(self):
        self.add_item()

    def add_item(self):
        try:
            # Validate required fields
            if not self.name_field.text().strip():
                QtWidgets.QMessageBox.warning(self, "Validation Error", "Item name is required!")
                return
            
            # Create Item object
            item = Item(
                name=self.name_field.text().strip(),
                rarity=self.rarity_field.currentData(),
                description=self.description_field.toPlainText().strip(),
                attunement=self.attunement_checkbox.isChecked()
            )
            
            # Save to JSON file
            self.save_item_to_json(item)

            QtWidgets.QMessageBox.information(self, "Success",
                f"Item '{item.name}' has been saved successfully!")
            self.accept()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error",
                f"Failed to save item:\n{str(e)}")

    def save_item_to_json(self, item: Item):
        """Save the Item to items.json file"""

        # Path to items.json in the Data directory
        items_file = Path(self.config.data_dir) / "items.json"
        
        # Load existing Items
        if items_file.exists():
            with open(items_file, 'r', encoding='utf-8') as f:
                items_data = json.load(f)
        else:
            items_data = []
        
        # Convert Item to dictionary format
        items_dict = {
            "name": item.name,
            "rarity": item.rarity.value,
            "description": item.description,
            "attunement": item.attunement
        }
        
        if self.edit_entry and self.original_name:
            updated = False
            for i, existing_item in enumerate(items_data):
                if existing_item.get("name") == self.original_name:
                    items_data[i] = items_dict
                    updated = True
                    break
            if not updated:
                items_data.append(items_dict)
        else:
            items_data.append(items_dict)
        
        with open(items_file, 'w', encoding='utf-8') as f:
            json.dump(items_data, f, indent=2, ensure_ascii=False)

class AddLocationDialog(AddEntryDialogBase):
    def __init__(self, parent=None, edit_location=None):
        super().__init__(entry_name="Location", edit_entry=edit_location, parent=parent)
        self.original_name = self.edit_entry.name if self.edit_entry else None
        
        self.name_field = QtWidgets.QLineEdit()
        self.name_field.setPlaceholderText("Enter a name for this location")
        self.form.addRow("Location Name*:", self.name_field)

        self.description_field = QtWidgets.QTextEdit()
        self.description_field.setPlaceholderText("Enter the location description...")
        self.description_field.setMaximumHeight(200)
        self.form.addRow("Description:", self.description_field)

        self.region_field = QtWidgets.QLineEdit()
        self.region_field.setPlaceholderText("Enter the region or area this location belongs to...")
        self.form.addRow("Region/Area:", self.region_field)

        self.parent_field = QtWidgets.QComboBox()
        # Check the locations from locatinos.json
        self.parent_field.addItem("None", None)  # Default option
        locations_file = Path(self.config.data_dir) / "locations.json"
        if locations_file.exists():
            with open(locations_file, 'r', encoding='utf-8') as f:
                locations_data = json.load(f)
                for loc in locations_data:
                    self.parent_field.addItem(loc.get("name", "Unnamed Location"), loc.get("name"))
        self.form.addRow("Parent Location:", self.parent_field)
        
        if self.edit_entry:
            self.populate_fields()
    
    def populate_fields(self):
        location = self.edit_entry
        self.name_field.setText(location.name)
        self.description_field.setPlainText(location.description or "")
        self.region_field.setText(location.region or "")
        
        if location.parent:
            for i in range(self.parent_field.count()):
                if self.parent_field.itemData(i) == location.parent.name:
                    self.parent_field.setCurrentIndex(i)
                    break

    def ok_button_slot(self):
        self.add_location()

    def add_location(self):
        try:
            if not self.name_field.text().strip():
                QtWidgets.QMessageBox.warning(self, "Validation Error", "Location name is required!")
                return
            
            location = Location(
                name=self.name_field.text().strip(),
                description=self.description_field.toPlainText().strip(),
                region=self.region_field.text().strip(),
                parent=self.parent_field.currentData().lower().replace(" ", "_") if self.parent_field.currentData() else None
            )
            
            self.save_location_to_json(location)

            QtWidgets.QMessageBox.information(self, "Success",
                f"Location '{location.name}' has been saved successfully!")
            self.accept()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error",
                f"Failed to save location:\n{str(e)}")
            
    def save_location_to_json(self, location: Location):

        locations_file = Path(self.config.data_dir) / "locations.json"
        
        if locations_file.exists():
            with open(locations_file, 'r', encoding='utf-8') as f:
                locations_data = json.load(f)
        else:
            locations_data = []
        
        location_dict = {
            "name": location.name,
            "description": location.description,
            "region": location.region,
            "parent": location.parent
        }
        
        if self.edit_entry and self.original_name:
            updated = False
            for i, existing_loc in enumerate(locations_data):
                if existing_loc.get("name") == self.original_name:
                    locations_data[i] = location_dict
                    updated = True
                    break
            if not updated:
                locations_data.append(location_dict)
        else:
            locations_data.append(location_dict)
        
        # Save back to file
        with open(locations_file, 'w', encoding='utf-8') as f:
            json.dump(locations_data, f, indent=2, ensure_ascii=False)

class AddConditionDialog(AddEntryDialogBase):
    def __init__(self, parent=None, edit_condition=None):
        super().__init__(entry_name="Condition", edit_entry=edit_condition, parent=parent)
        self.original_name = self.edit_entry.name if self.edit_entry else None
        
        self.name_field = QtWidgets.QLineEdit()
        self.name_field.setPlaceholderText("Enter a name for this condition")
        self.form.addRow("Condition Name*:", self.name_field)

        self.description_field = QtWidgets.QTextEdit()
        self.description_field.setPlaceholderText("Enter the condition description...")
        self.description_field.setMaximumHeight(200)
        self.form.addRow("Description:", self.description_field)

        self.name_field.setFocus()
        
        if self.edit_entry:
            self.populate_fields()
    
    def populate_fields(self):
        condition = self.edit_entry
        self.name_field.setText(condition.name)
        self.description_field.setPlainText(condition.description or "")

    def ok_button_slot(self):
        self.add_condition()
    
    def add_condition(self):
        try:
            if not self.name_field.text().strip():
                QtWidgets.QMessageBox.warning(self, "Validation Error", "Condition name is required!")
                return
            
            condition = Condition(
                name=self.name_field.text().strip(),
                description=self.description_field.toPlainText().strip()
            )
            
            self.save_condition_to_json(condition)

            QtWidgets.QMessageBox.information(self, "Success",
                f"Condition '{condition.name}' has been saved successfully!")
            self.accept()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error",
                f"Failed to save condition:\n{str(e)}")
            
    def save_condition_to_json(self, condition: Condition):

        conditions_file = Path(self.config.data_dir) / "conditions.json"
        
        if conditions_file.exists():
            with open(conditions_file, 'r', encoding='utf-8') as f:
                conditions_data = json.load(f)
        else:
            conditions_data = []
        
        condition_dict = {
            "name": condition.name,
            "description": condition.description
        }
        
        if self.edit_entry and self.original_name:
            updated = False
            for i, existing_cond in enumerate(conditions_data):
                if existing_cond.get("name") == self.original_name:
                    conditions_data[i] = condition_dict
                    updated = True
                    break
            if not updated:
                conditions_data.append(condition_dict)
        else:
            conditions_data.append(condition_dict)
        
        # Save back to file
        with open(conditions_file, 'w', encoding='utf-8') as f:
            json.dump(conditions_data, f, indent=2, ensure_ascii=False)

class AddSoundDialog(AddEntryDialogBase):
    def __init__(self, parent=None):
        super().__init__(entry_name="Sound", parent=parent)
        
        # Sound Name field
        self.name_field = QtWidgets.QLineEdit()
        self.name_field.setPlaceholderText("Enter a name for this sound (e.g., 'Cow Mooing', 'Sword Clang', 'Tavern Ambience')...")
        self.form.addRow("Sound Name*:", self.name_field)
        
        # Sound Description field
        self.description_field = QtWidgets.QTextEdit()
        self.description_field.setPlaceholderText("Describe the sound for AI generation (e.g., 'a cow mooing in a field', 'sword hitting shield', 'tavern ambience')...")
        self.description_field.setMaximumHeight(100)
        self.form.addRow("Description for AI:", self.description_field)
        
        # Sound File field with browse button
        file_layout = QtWidgets.QHBoxLayout()
        self.file_field = QtWidgets.QLineEdit()
        self.file_field.setPlaceholderText("Leave blank to generate with AI, or browse for existing file...")
        self.browse_btn = QtWidgets.QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_field)
        file_layout.addWidget(self.browse_btn)
        
        file_widget = QtWidgets.QWidget()
        file_widget.setLayout(file_layout)
        self.form.addRow("Sound File:", file_widget)
        
        # Duration field
        self.duration_field = QtWidgets.QSpinBox()
        self.duration_field.setRange(1, 60)
        self.duration_field.setValue(5)
        self.duration_field.setSuffix(" seconds")
        self.form.addRow("Duration:", self.duration_field)
        
        # Mode field
        self.mode_combo = QtWidgets.QComboBox()
        for mode in SoundGenerationMode:
            self.mode_combo.addItem(mode.value.replace('_', ' ').title(), mode)
        self.form.addRow("Audio Type:", self.mode_combo)
                
        # Add note about required fields
        note_label = QtWidgets.QLabel("* Required fields")
        note_label.setStyleSheet("color: #888; font-size: 11px;")
        self.vbox_layout.addWidget(note_label)
        
        # Focus on name field
        self.name_field.setFocus()
    
    def browse_file(self):
        """Browse for an existing audio file"""
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setWindowTitle("Select Audio File")
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.m4a *.ogg *.flac);;All Files (*)")
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        
        if file_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.file_field.setText(selected_files[0])
    
    def ok_button_slot(self):
        self.generate_sound()

    def generate_sound(self):
        """Generate or add the sound clip"""
        try:
            # Validate required fields
            sound_name = self.name_field.text().strip()
            if not sound_name:
                QtWidgets.QMessageBox.warning(self, "Validation Error", "Sound name is required!")
                return
            
            # Get form values
            description = self.description_field.toPlainText().strip()
            file_path = self.file_field.text().strip()
            duration = float(self.duration_field.value())
            mode = self.mode_combo.currentData()
            
            # Create audio directory if it doesn't exist
            audio_dir = self.config.get_audio_files()
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            # Create safe filename from sound name
            safe_name = sound_name.replace(' ', '_').lower()
            safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-")
            
            if file_path:
                # Copy existing file to audio directory
                source_file = Path(file_path)
                if not source_file.exists():
                    QtWidgets.QMessageBox.warning(self, "File Error", "Selected file does not exist!")
                    return
                
                # Determine extension from source file
                extension = source_file.suffix
                target_path = audio_dir / f"{safe_name}{extension}"
                
                # Copy the file
                shutil.copy2(source_file, target_path)
                
                QtWidgets.QMessageBox.information(self, "Success", 
                    f"Sound '{sound_name}' added successfully!\nCopied to: {target_path}")
                
            else:
                # Generate with AI
                if not description:
                    QtWidgets.QMessageBox.warning(self, "Validation Error", 
                        "Description is required for AI generation!")
                    return
                
                # Show loading dialog
                progress = QtWidgets.QProgressDialog("Generating sound clip...", "Cancel", 0, 0, self)
                progress.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
                progress.setWindowTitle("Stability AI Sound Generation")
                progress.setAutoClose(False)
                progress.setAutoReset(False)
                progress.setCancelButton(None)
                progress.show()
                
                # Process events to show the dialog immediately
                QtWidgets.QApplication.processEvents()
                
                try:
                    # Generate the sound
                    sound_generator = SoundGenerator()
                    audio_path = sound_generator.generate_and_save_sound(description, safe_name, duration, mode)
                    
                    # Close the progress dialog
                    progress.close()
                    
                    QtWidgets.QMessageBox.information(self, "Success", 
                        f"Sound '{sound_name}' generated successfully!\nSaved to: {audio_path}")
                        
                except Exception as gen_error:
                    progress.close()
                    QtWidgets.QMessageBox.critical(self, "Generation Error", 
                        f"Failed to generate sound:\n{str(gen_error)}")
                    return
            
            self.accept()
            
        except Exception as e:
            # Make sure to close progress dialog on error
            if 'progress' in locals():
                progress.close()
            QtWidgets.QMessageBox.critical(self, "Error", 
                f"Failed to generate sound:\n{str(e)}")
