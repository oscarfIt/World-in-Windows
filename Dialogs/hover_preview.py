from PyQt6 import QtWidgets, QtCore

class HoverPreview(QtWidgets.QDialog):
    """Small non-modal popup for hover previews."""
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.WindowType.ToolTip)
        self.label = QtWidgets.QLabel()
        self.label.setWordWrap(True)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.label)

    def show_text(self, text: str, global_pos: QtCore.QPoint):
        self.label.setText(text)
        self.adjustSize()
        # Offset a bit so it doesn't sit under the cursor
        self.move(global_pos + QtCore.QPoint(12, 18))
        self.show()
