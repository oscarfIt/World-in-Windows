from PyQt6 import QtWidgets
import json
from pathlib import Path

from ..theme import DMHelperTheme

from ..Dataclasses import PcClass, AbilityScores

class EditPcClassDialog(QtWidgets.QDialog):
    """Dialog for editing a PC Class stat block"""
    def __init__(self, pc_class: PcClass, npc=None, parent=None):
        super().__init__(parent)
        self.pc_class = pc_class
        self.npc = npc
        
        self.setWindowTitle("Edit PC Class Stat Block")
        self.resize(500, 700)
        
        DMHelperTheme.apply_to_dialog(self)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        form_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(form_widget)
        
        class_name = getattr(pc_class.name, 'value', str(pc_class.name))
        name_label = QtWidgets.QLabel(class_name)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        form.addRow("Class:", name_label)
        
        self.level_spin = QtWidgets.QSpinBox()
        self.level_spin.setRange(1, 20)
        self.level_spin.setValue(pc_class.level if pc_class.level else 1)
        form.addRow("Level:", self.level_spin)
        
        # Add Armour Class field
        self.ac_spin = QtWidgets.QSpinBox()
        self.ac_spin.setRange(1, 30)
        self.ac_spin.setValue(pc_class.armour_class if pc_class.armour_class else 10)
        form.addRow("Armour Class:", self.ac_spin)
        
        form.addRow(QtWidgets.QLabel(""))  # Spacer
        
        ability_scores_label = QtWidgets.QLabel("Ability Scores")
        ability_scores_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        form.addRow(ability_scores_label)
        
        self.str_spin = QtWidgets.QSpinBox()
        self.str_spin.setRange(1, 30)
        self.str_spin.setValue(pc_class.ability_scores.strength if pc_class.ability_scores else 10)
        form.addRow("Strength:", self.str_spin)
        
        self.dex_spin = QtWidgets.QSpinBox()
        self.dex_spin.setRange(1, 30)
        self.dex_spin.setValue(pc_class.ability_scores.dexterity if pc_class.ability_scores else 10)
        form.addRow("Dexterity:", self.dex_spin)
        
        self.con_spin = QtWidgets.QSpinBox()
        self.con_spin.setRange(1, 30)
        self.con_spin.setValue(pc_class.ability_scores.constitution if pc_class.ability_scores else 10)
        form.addRow("Constitution:", self.con_spin)
        
        self.int_spin = QtWidgets.QSpinBox()
        self.int_spin.setRange(1, 30)
        self.int_spin.setValue(pc_class.ability_scores.intelligence if pc_class.ability_scores else 10)
        form.addRow("Intelligence:", self.int_spin)
        
        self.wis_spin = QtWidgets.QSpinBox()
        self.wis_spin.setRange(1, 30)
        self.wis_spin.setValue(pc_class.ability_scores.wisdom if pc_class.ability_scores else 10)
        form.addRow("Wisdom:", self.wis_spin)
        
        self.cha_spin = QtWidgets.QSpinBox()
        self.cha_spin.setRange(1, 30)
        self.cha_spin.setValue(pc_class.ability_scores.charisma if pc_class.ability_scores else 10)
        form.addRow("Charisma:", self.cha_spin)
        
        form.addRow(QtWidgets.QLabel(""))  # Spacer
        
        spells_label = QtWidgets.QLabel("Spells")
        spells_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        form.addRow(spells_label)
        
        self.spells_field = QtWidgets.QTextEdit()
        self.spells_field.setPlaceholderText("Enter spell names, one per line...")
        self.spells_field.setMaximumHeight(150)
        if pc_class.spells:
            self.spells_field.setPlainText('\n'.join(pc_class.spells))
        form.addRow("Spell List:", self.spells_field)
        
        scroll.setWidget(form_widget)
        layout.addWidget(scroll)
        
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save(self):
        """Save the edited stat block"""
        try:            
            self.pc_class.level = self.level_spin.value()
            print("Saving level:", self.pc_class.level)
            
            self.pc_class.armour_class = self.ac_spin.value()
            
            self.pc_class.ability_scores = AbilityScores(
                strength=self.str_spin.value(),
                dexterity=self.dex_spin.value(),
                constitution=self.con_spin.value(),
                intelligence=self.int_spin.value(),
                wisdom=self.wis_spin.value(),
                charisma=self.cha_spin.value()
            )
            
            spells_text = self.spells_field.toPlainText().strip()
            self.pc_class.spells = [line.strip() for line in spells_text.split('\n') if line.strip()]
            
            if self.npc:
                from ..config import Config
                config = Config()
                npcs_file = Path(config.data_dir) / "npcs.json"
                
                if npcs_file.exists():
                    with open(npcs_file, 'r', encoding='utf-8') as f:
                        npcs_data = json.load(f)
                    
                    # Find and update the NPC
                    for npc_entry in npcs_data:
                        if npc_entry.get("name") == self.npc.name:
                            # Update the stat block data
                            if npc_entry.get("stat_block", {}).get("type") == "pc_class":
                                npc_entry["stat_block"]["level"] = self.pc_class.level
                                npc_entry["stat_block"]["armour_class"] = self.pc_class.armour_class
                                npc_entry["stat_block"]["ability_scores"] = {
                                    "strength": self.pc_class.ability_scores.strength,
                                    "dexterity": self.pc_class.ability_scores.dexterity,
                                    "constitution": self.pc_class.ability_scores.constitution,
                                    "intelligence": self.pc_class.ability_scores.intelligence,
                                    "wisdom": self.pc_class.ability_scores.wisdom,
                                    "charisma": self.pc_class.ability_scores.charisma
                                }
                                npc_entry["stat_block"]["spells"] = self.pc_class.spells
                                break
                    
                    # Save back to file
                    with open(npcs_file, 'w', encoding='utf-8') as f:
                        json.dump(npcs_data, f, indent=2, ensure_ascii=False)
            
            QtWidgets.QMessageBox.information(self, "Success", 
                "PC Class stat block has been updated!")
            self.accept()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", 
                f"Failed to save stat block:\n{str(e)}")
