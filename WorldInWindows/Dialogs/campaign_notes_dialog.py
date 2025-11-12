from PyQt6 import QtWidgets
from pathlib import Path
import json

from ..theme import DMHelperTheme
from ..config import Config

from ..Dataclasses import NPC

class CampaignNotesDialog(QtWidgets.QDialog):
    """Dialog for editing campaign notes for an NPC"""
    def __init__(self, npc: NPC, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.npc = npc
        self.setWindowTitle(f"Campaign Notes - {npc.name}")
        self.resize(600, 500)
        
        # Apply theme
        DMHelperTheme.apply_theme(self)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Title
        title_label = QtWidgets.QLabel(f"Campaign Notes for {npc.name}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Notes text editor
        self.notes_editor = QtWidgets.QTextEdit()
        self.notes_editor.setPlaceholderText("Enter campaign notes here...\n\nYou can record anything that happens during the campaign involving this character:\n- Player interactions\n- Story developments\n- Combat notes\n- Character development\n- Quest involvement\n- etc.")
        
        # Set the current campaign notes if they exist
        if hasattr(npc, 'campaign_notes') and npc.campaign_notes:
            self.notes_editor.setPlainText(npc.campaign_notes)
        
        layout.addWidget(self.notes_editor)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        # Clear button
        clear_btn = QtWidgets.QPushButton("Clear")
        clear_btn.setToolTip("Clear all notes")
        clear_btn.clicked.connect(self.clear_notes)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        # Save & Close buttons
        save_btn = QtWidgets.QPushButton("Save")
        save_btn.setToolTip("Save changes to campaign notes")
        save_btn.clicked.connect(self.save_notes)
        save_btn.setDefault(True)  # Make it the default button
        button_layout.addWidget(save_btn)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.setToolTip("Close without saving")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Focus on the text editor
        self.notes_editor.setFocus()
    
    def clear_notes(self):
        """Clear all notes after confirmation"""
        if self.notes_editor.toPlainText().strip():
            reply = QtWidgets.QMessageBox.question(self, "Clear Notes",
                "Are you sure you want to clear all campaign notes?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self.notes_editor.clear()
    
    def save_notes(self):
        """Save the campaign notes to the NPC and update the JSON file"""
        try:
            # Update the NPC's campaign_notes field
            new_notes = self.notes_editor.toPlainText().strip()
            self.npc.campaign_notes = new_notes
            
            # Save to JSON file
            self.save_npc_to_json()
            
            QtWidgets.QMessageBox.information(self, "Success", 
                "Campaign notes saved successfully!")
            self.accept()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", 
                f"Failed to save campaign notes:\n{str(e)}")
    
    def save_npc_to_json(self):
        """Update the NPC entry in npcs.json with the new campaign notes"""
        # Path to npcs.json
        npcs_file = Path(self.config.data_dir) / "npcs.json"
        
        if not npcs_file.exists():
            raise Exception("NPCs file not found")
        
        # Load existing NPCs
        with open(npcs_file, 'r', encoding='utf-8') as f:
            npcs_data = json.load(f)
        
        # Find and update the NPC entry
        npc_updated = False
        for npc_entry in npcs_data:
            if npc_entry.get("name") == self.npc.name:
                npc_entry["campaign_notes"] = self.npc.campaign_notes
                npc_updated = True
                break
        
        if not npc_updated:
            raise Exception(f"Could not find NPC '{self.npc.name}' in the data file")
        
        # Save back to file
        with open(npcs_file, 'w', encoding='utf-8') as f:
            json.dump(npcs_data, f, indent=2, ensure_ascii=False)

