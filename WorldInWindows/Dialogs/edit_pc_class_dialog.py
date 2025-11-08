from PyQt6 import QtWidgets

from ..theme import DMHelperTheme

from ..Dataclasses import PcClass

class EditPcClassDialog(QtWidgets.QDialog):
    """Dialog for editing a PC Class stat block"""
    def __init__(self, pc_class: PcClass, npc=None, parent=None):
        super().__init__(parent)
        self.pc_class = pc_class
        self.npc = npc  # Optional: the NPC this stat block belongs to
        
        self.setWindowTitle("Edit PC Class Stat Block")
        self.resize(500, 700)
        
        # Apply theme
        DMHelperTheme.apply_to_dialog(self)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Scroll area for form
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        form_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(form_widget)
        
        # Class name (read-only)
        class_name = getattr(pc_class.name, 'value', str(pc_class.name))
        name_label = QtWidgets.QLabel(class_name)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        form.addRow("Class:", name_label)
        
        # Level
        self.level_spin = QtWidgets.QSpinBox()
        self.level_spin.setRange(1, 20)
        self.level_spin.setValue(pc_class.level if pc_class.level else 1)
        form.addRow("Level:", self.level_spin)
        
        form.addRow(QtWidgets.QLabel(""))  # Spacer
        
        # Ability Scores
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
        
        # Spells
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
        
        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
