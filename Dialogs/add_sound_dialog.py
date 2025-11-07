from PyQt6 import QtWidgets, QtCore
from pathlib import Path
import shutil

from ..theme import DMHelperTheme
from ..config import Config

from ..AIGen import SoundGenerator, AudioGenerationMode

class AddSoundDialog(QtWidgets.QDialog):
    """Dialog for generating new audio clips"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.setWindowTitle("Add Sound Clip")
        self.resize(500, 400)
        
        # Apply theme
        DMHelperTheme.apply_to_dialog(self)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Create form
        form_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(form_widget)
        
        # Sound Name field
        self.name_field = QtWidgets.QLineEdit()
        self.name_field.setPlaceholderText("Enter a name for this sound (e.g., 'Cow Mooing', 'Sword Clang', 'Tavern Ambience')...")
        form.addRow("Sound Name*:", self.name_field)
        
        # Sound Description field
        self.description_field = QtWidgets.QTextEdit()
        self.description_field.setPlaceholderText("Describe the sound for AI generation (e.g., 'a cow mooing in a field', 'sword hitting shield', 'tavern ambience')...")
        self.description_field.setMaximumHeight(100)
        form.addRow("Description for AI:", self.description_field)
        
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
        form.addRow("Sound File:", file_widget)
        
        # Duration field
        self.duration_field = QtWidgets.QSpinBox()
        self.duration_field.setRange(1, 60)
        self.duration_field.setValue(5)
        self.duration_field.setSuffix(" seconds")
        form.addRow("Duration:", self.duration_field)
        
        # Mode field
        self.mode_combo = QtWidgets.QComboBox()
        for mode in AudioGenerationMode:
            self.mode_combo.addItem(mode.value.replace('_', ' ').title(), mode)
        form.addRow("Audio Type:", self.mode_combo)
        
        layout.addWidget(form_widget)
        
        # Add note about required fields
        note_label = QtWidgets.QLabel("* Required fields")
        note_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(note_label)
        
        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.generate_sound)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
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
