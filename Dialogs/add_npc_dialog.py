from PyQt6 import QtWidgets, QtCore
import json
from pathlib import Path


from theme import DMHelperTheme
from repo import Repo

from ..Dataclasses import Race, Alignment, PcClassName, MonsterManual, PcClass, NPC

class AddNPCDialog(QtWidgets.QDialog):
    """Dialog for adding or editing an NPC"""
    def __init__(self, parent=None, edit_npc=None):
        super().__init__(parent)
        self.edit_npc = edit_npc  # NPC being edited, or None for new NPC
        self.original_name = edit_npc.name if edit_npc else None  # Store original name for updates
        
        title = "Edit NPC" if edit_npc else "Add New NPC"
        self.setWindowTitle(title)
        self.resize(500, 700)
        
        # Apply theme
        
        DMHelperTheme.apply_to_dialog(self)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Create form
        form_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(form_widget)
        
        # Name field
        self.name_field = QtWidgets.QLineEdit()
        self.name_field.setPlaceholderText("Enter NPC name...")
        form.addRow("Name*:", self.name_field)
        
        # Race field
        self.race_combo = QtWidgets.QComboBox()
        # Sort races alphabetically by their display value
        sorted_races = sorted(Race, key=lambda r: r.value)
        for race in sorted_races:
            self.race_combo.addItem(race.value, race)
        form.addRow("Race*:", self.race_combo)
        
        # Sex field
        self.sex_combo = QtWidgets.QComboBox()
        self.sex_combo.addItems(["Male", "Female", "Non-binary", "Other"])
        self.sex_combo.setEditable(True)  # Allow custom input
        form.addRow("Sex:", self.sex_combo)

        self.age_field = QtWidgets.QLineEdit()
        self.age_field.setPlaceholderText("Describe the NPC's age...")
        form.addRow("Age:", self.age_field)
        
        # Alignment field
        self.alignment_combo = QtWidgets.QComboBox()
        for alignment in Alignment:
            self.alignment_combo.addItem(alignment.value, alignment)
        form.addRow("Alignment*:", self.alignment_combo)
        
        # Stat Block fields - Type and Selection
        self.stat_block_type_combo = QtWidgets.QComboBox()
        self.stat_block_type_combo.addItems(["Monster Manual", "PC Class"])
        self.stat_block_type_combo.currentTextChanged.connect(self.update_stat_block_options)
        form.addRow("Stat Block Type:", self.stat_block_type_combo)
        
        self.stat_block_selection_combo = QtWidgets.QComboBox()
        form.addRow("Stat Block:", self.stat_block_selection_combo)
        
        # Initialize with Monster Manual options
        self.update_stat_block_options()
        
        # Appearance field
        self.appearance_field = QtWidgets.QTextEdit()
        self.appearance_field.setPlaceholderText("Describe the NPC's physical appearance...")
        self.appearance_field.setMaximumHeight(100)
        form.addRow("Appearance:", self.appearance_field)
        
        # Backstory field
        self.backstory_field = QtWidgets.QTextEdit()
        self.backstory_field.setPlaceholderText("Describe the NPC's background and history...")
        self.backstory_field.setMaximumHeight(120)
        form.addRow("Backstory:", self.backstory_field)
        
        # Additional traits field
        self.traits_field = QtWidgets.QTextEdit()
        self.traits_field.setPlaceholderText("Additional traits (one per line)...")
        self.traits_field.setMaximumHeight(80)
        form.addRow("Additional Traits:", self.traits_field)
        
        # Alive checkbox
        self.alive_checkbox = QtWidgets.QCheckBox("NPC is alive")
        self.alive_checkbox.setChecked(True)  # Default to alive
        self.alive_checkbox.setToolTip("Uncheck if this NPC is deceased")
        form.addRow("Status:", self.alive_checkbox)
        
        layout.addWidget(form_widget)
        
        # Add note about required fields
        note_label = QtWidgets.QLabel("* Required fields")
        note_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(note_label)
        
        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_npc)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Populate fields if editing an existing NPC
        if self.edit_npc:
            self.populate_fields()
        
        # Focus on name field
        self.name_field.setFocus()
    
    def populate_fields(self):
        """Populate form fields when editing an existing NPC"""
        npc = self.edit_npc
        
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
                monster_manual_dir = config.get_monster_manual_pages()
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
            if self.edit_npc and self.edit_npc.stat_block:
                preserve_stat_block = False
                
                if isinstance(self.edit_npc.stat_block, MonsterManual) and stat_block_type == "Monster Manual":
                    # Check if monster name is the same
                    current_monster = self.edit_npc.stat_block.monster_name
                    if current_monster == stat_block_name or current_monster.replace("_", " ").title() == stat_block_name:
                        preserve_stat_block = True
                        stat_block = self.edit_npc.stat_block
                
                elif isinstance(self.edit_npc.stat_block, PcClass) and stat_block_type == "PC Class":
                    # Check if class name is the same
                    current_class = self.edit_npc.stat_block.name.value if hasattr(self.edit_npc.stat_block.name, 'value') else str(self.edit_npc.stat_block.name)
                    if current_class == stat_block_name:
                        preserve_stat_block = True
                        stat_block = self.edit_npc.stat_block
                
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
            if self.edit_npc and hasattr(self.edit_npc, 'campaign_notes'):
                campaign_notes = self.edit_npc.campaign_notes
            
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
            # Find the original ID by looking it up in the repository
            original_id = None
            if self.edit_npc:
                try:
                    repo = Repo(config.data_dir)
                    repo.load_all()
                    # Find the ID by looking through npcs_by_id dictionary
                    for npc_id, npc_obj in repo.npcs_by_id.items():
                        if npc_obj is self.edit_npc or npc_obj.name == self.original_name:
                            original_id = npc_id
                            break
                except Exception as e:
                    print(f"Could not find original ID: {e}")
            
            self.save_npc_to_json(npc, is_edit=self.edit_npc is not None, original_name=self.original_name, original_id=original_id)
            
            QtWidgets.QMessageBox.information(self, "Success", 
                f"NPC '{npc.name}' has been saved successfully!")
            self.accept()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", 
                f"Failed to save NPC:\n{str(e)}")
    
    def save_npc_to_json(self, npc: NPC, is_edit=False, original_name=None, original_id=None):
        """Save the NPC to npcs.json file"""
        
        # Path to npcs.json in the Data directory
        npcs_file = Path(config.data_dir) / "npcs.json"
        
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
                    "Strength": npc.stat_block.ability_scores.Strength,
                    "Dexterity": npc.stat_block.ability_scores.Dexterity,
                    "Constitution": npc.stat_block.ability_scores.Constitution,
                    "Intelligence": npc.stat_block.ability_scores.Intelligence,
                    "Wisdom": npc.stat_block.ability_scores.Wisdom,
                    "Charisma": npc.stat_block.ability_scores.Charisma
                },
                "spells": npc.stat_block.spells if hasattr(npc.stat_block, 'spells') else []
            }
        else:
            # Fallback for other stat block types
            stat_block_data = {
                "type": "basic",
                "name": getattr(npc.stat_block, 'display_name', 'Unknown')
            }
        
        # Use original ID if editing, otherwise generate new ID from name
        if is_edit and original_id:
            npc_id = original_id
        else:
            # Generate a simple ID from the name (lowercase, replace spaces with underscores)
            npc_id = npc.name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
        
        npc_dict = {
            "id": npc_id,
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
        if is_edit and (original_id or original_name):
            # Find and update existing NPC using original ID first, then name as fallback
            updated = False
            for i, existing_npc in enumerate(npcs_data):
                if (original_id and existing_npc.get("id") == original_id) or \
                   (original_name and existing_npc.get("name") == original_name):
                    print(f"Updating existing NPC ID '{original_id}': {original_name} -> {npc.name}")
                    npcs_data[i] = npc_dict
                    updated = True
                    break
            
            if not updated:
                # Original NPC not found, add as new
                print(f"Original NPC '{original_name}' (ID: {original_id}) not found, adding as new")
                npcs_data.append(npc_dict)
        else:
            # Add new NPC
            print(f"Adding new NPC: {npc_dict}")
            npcs_data.append(npc_dict)
        
        # Save back to file
        with open(npcs_file, 'w', encoding='utf-8') as f:
            json.dump(npcs_data, f, indent=2, ensure_ascii=False)
