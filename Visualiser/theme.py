# theme.py
# Theming system for the DM Helper application

class DMHelperTheme:
    """Theme manager for DM Helper with D&D inspired styling"""
    
    # Color palette inspired by classic D&D
    COLORS = {
        'background_primary': '#1a1a1a',      # Dark parchment
        'background_secondary': '#2d2d2d',    # Darker areas
        'background_accent': '#3a3a3a',       # Lighter panels
        'text_primary': '#e8e3d3',            # Warm white text
        'text_secondary': '#c4b896',          # Muted gold text
        'accent_primary': '#8b4513',          # Brown leather
        'accent_secondary': '#d4af37',        # Gold highlights
        'success': '#228b22',                 # Forest green
        'warning': '#ff8c00',                 # Dark orange
        'danger': '#dc143c',                  # Crimson
        'border': '#4a4a4a',                  # Subtle borders
        'hover': '#404040',                   # Hover states
        'selection': '#6b4423',               # Brown selection
    }
    
    @classmethod
    def get_main_stylesheet(cls) -> str:
        """Main application stylesheet"""
        c = cls.COLORS
        return f"""
        /* Main Window */
        QMainWindow {{
            background-color: {c['background_primary']};
            color: {c['text_primary']};
            font-family: "Segoe UI", Arial, sans-serif;
        }}
        
        /* Tree View */
        QTreeView {{
            background-color: {c['background_secondary']};
            alternate-background-color: {c['background_accent']};
            color: {c['text_primary']};
            border: 2px solid {c['border']};
            border-radius: 6px;
            selection-background-color: {c['selection']};
            outline: none;
            gridline-color: {c['border']};
        }}
        
        QTreeView::item {{
            height: 28px;
            padding: 4px;
            border-bottom: 1px solid {c['border']};
        }}
        
        QTreeView::item:hover {{
            background-color: {c['hover']};
        }}
        
        QTreeView::item:selected {{
            background-color: {c['selection']};
            color: {c['text_primary']};
        }}
        
        QTreeView::branch {{
            background-color: transparent;
        }}
        
        /* Header */
        QHeaderView::section {{
            background-color: {c['accent_primary']};
            color: {c['text_primary']};
            font-weight: bold;
            border: 1px solid {c['border']};
            padding: 8px;
        }}
        
        /* List Widget */
        QListWidget {{
            background-color: {c['background_secondary']};
            color: {c['text_primary']};
            border: 2px solid {c['border']};
            border-radius: 6px;
            selection-background-color: {c['selection']};
            outline: none;
        }}
        
        QListWidget::item {{
            padding: 6px;
            border-bottom: 1px solid {c['border']};
        }}
        
        QListWidget::item:hover {{
            background-color: {c['hover']};
        }}
        
        QListWidget::item:selected {{
            background-color: {c['selection']};
        }}
        
        /* Line Edit (Search) */
        QLineEdit {{
            background-color: {c['background_accent']};
            color: {c['text_primary']};
            border: 2px solid {c['border']};
            border-radius: 6px;
            padding: 8px;
            font-size: 14px;
        }}
        
        QLineEdit:focus {{
            border-color: {c['accent_secondary']};
            background-color: {c['background_secondary']};
        }}
        
        QLineEdit::placeholder {{
            color: {c['text_secondary']};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {c['accent_primary']};
            color: {c['text_primary']};
            border: 2px solid {c['accent_secondary']};
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: bold;
            min-width: 80px;
        }}
        
        QPushButton:hover {{
            background-color: {c['accent_secondary']};
            color: {c['background_primary']};
            border-color: {c['text_primary']};
            box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.3);
        }}
        
        QPushButton:pressed {{
            background-color: {c['selection']};
            border-color: {c['accent_primary']};
            padding: 11px 19px 9px 21px;  /* Slight offset for pressed effect */
        }}
        
        QPushButton:disabled {{
            background-color: {c['border']};
            color: {c['text_secondary']};
            border-color: {c['text_secondary']};
        }}
        
        /* Splitter */
        QSplitter::handle {{
            background-color: {c['border']};
            width: 2px;
        }}
        
        QSplitter::handle:hover {{
            background-color: {c['accent_secondary']};
        }}
        
        /* Labels */
        QLabel {{
            color: {c['text_primary']};
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {c['background_accent']};
            color: {c['text_secondary']};
            border-top: 1px solid {c['border']};
        }}
        
        /* Scroll Bars */
        QScrollBar:vertical {{
            background-color: {c['background_secondary']};
            width: 12px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {c['accent_primary']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {c['accent_secondary']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: {c['background_secondary']};
            height: 12px;
            border: none;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {c['accent_primary']};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {c['accent_secondary']};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        """
    
    @classmethod
    def get_dialog_stylesheet(cls) -> str:
        """Stylesheet for dialogs and popup windows"""
        c = cls.COLORS
        return f"""
        QMainWindow, QDialog, QWidget {{
            background-color: {c['background_primary']};
            color: {c['text_primary']};
        }}
        
        QScrollArea {{
            background-color: {c['background_secondary']};
            border: 2px solid {c['border']};
            border-radius: 6px;
        }}
        
        QTextBrowser {{
            background-color: {c['background_accent']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            border-radius: 4px;
            padding: 8px;
            selection-background-color: {c['selection']};
        }}
        
        QDialogButtonBox QPushButton {{
            min-width: 100px;
            padding: 8px 16px;
            border: 2px solid {c['border']};
            border-radius: 6px;
            background: {c['background_secondary']};
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }}
        
        QDialogButtonBox QPushButton:hover {{
            background: {c['accent_secondary']};
            border-color: {c['text_primary']};
        }}
        
        QDialogButtonBox QPushButton:pressed {{
            background: {c['selection']};
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
        }}
        """
    
    @classmethod
    def apply_to_application(cls, app):
        """Apply theme to the entire application"""
        app.setStyleSheet(cls.get_main_stylesheet())
    
    @classmethod
    def apply_to_dialog(cls, dialog):
        """Apply theme to a specific dialog/window"""
        dialog.setStyleSheet(cls.get_dialog_stylesheet())