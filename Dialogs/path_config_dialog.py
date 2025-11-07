from PyQt6 import QtWidgets

from ..config import Config

class PathConfigDialog(QtWidgets.QDialog):
    """Dialog for configuring Data and Media directory paths"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.setWindowTitle("Configure Paths")
        self.setModal(True)
        self.resize(500, 200)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Data directory section
        data_group = QtWidgets.QGroupBox("Data Directory")
        data_layout = QtWidgets.QHBoxLayout(data_group)

        self.data_path_edit = QtWidgets.QLineEdit(self.config.data_dir)
        data_browse_btn = QtWidgets.QPushButton("Browse...")
        data_browse_btn.clicked.connect(self.browse_data_dir)
        
        data_layout.addWidget(self.data_path_edit)
        data_layout.addWidget(data_browse_btn)
        
        # Media directory section
        media_group = QtWidgets.QGroupBox("Media Directory")
        media_layout = QtWidgets.QHBoxLayout(media_group)

        self.media_path_edit = QtWidgets.QLineEdit(self.config.media_dir)
        media_browse_btn = QtWidgets.QPushButton("Browse...")
        media_browse_btn.clicked.connect(self.browse_media_dir)
        
        media_layout.addWidget(self.media_path_edit)
        media_layout.addWidget(media_browse_btn)
        
        # Info labels
        info_label = QtWidgets.QLabel(
            "Data Directory: Contains JSON files (npcs.json, spells.json, etc.)\n"
            "Media Directory: Contains images and audio files"
        )
        info_label.setStyleSheet("color: #888; font-size: 10pt;")
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QtWidgets.QPushButton("OK")
        ok_btn.clicked.connect(self.accept_changes)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        # Add to main layout
        layout.addWidget(data_group)
        layout.addWidget(media_group)
        layout.addWidget(info_label)
        layout.addStretch()
        layout.addLayout(button_layout)
    
    def browse_data_dir(self):
        """Browse for data directory"""
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Data Directory", self.data_path_edit.text()
        )
        if dir_path:
            self.data_path_edit.setText(dir_path)
    
    def browse_media_dir(self):
        """Browse for media directory"""
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Media Directory", self.media_path_edit.text()
        )
        if dir_path:
            self.media_path_edit.setText(dir_path)
    
    def accept_changes(self):
        """Accept and save the new paths"""
        new_data_dir = self.data_path_edit.text().strip()
        new_media_dir = self.media_path_edit.text().strip()
        
        if not new_data_dir or not new_media_dir:
            QtWidgets.QMessageBox.warning(self, "Invalid Paths", 
                                        "Both Data and Media directories must be specified.")
            return
        
        # Update config
        self.config.data_dir = new_data_dir
        self.config.media_dir = new_media_dir
        self.config.save()

        QtWidgets.QMessageBox.information(self, "Paths Updated",
            "Directory paths have been updated. Please restart the application for changes to take effect.")
        
        self.accept()

