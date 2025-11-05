# world_in_windows.py
# Minimal PyQt6 app to browse (nested) Locations and see their NPCs.
# Changes from previous version:
# - Left pane is now a QTreeView with two columns: Name | Short Description
# - Locations can be nested (e.g., "The Salty Hound" under "Port Virellon")
# - Short description is visible directly in the tree
#
# pip install PyQt6

from PyQt6 import QtCore, QtGui, QtWidgets
from typing import List, Optional
from pathlib import Path
import json

from knowledge_base import KBEntry, KnowledgeBase
from repo import Repo
from image_generation import ImageGenerator, ImageGenerationMode
from config import Config

from location import Location
from npc import NPC
from stat_block import StatBlock, MonsterManual
from pc_classes import PcClass, PcClassName
from item import Item
from spell import Spell
from class_action import ClassAction



# Global config instance
config = Config()

def _resolve_image_for_npc(npc) -> Path | None:
    for attr in ("portrait_path", "image_path"):
        p = getattr(npc, attr, None)
        if p and Path(p).exists():
            return Path(p)
    guess_file_name = npc.name.replace(" ", "_").lower()
    guess = config.get_npc_portraits() / f"{guess_file_name}.png"
    return guess if guess.exists() else None

def _resolve_image_for_entry(content_type: Spell | Item | ClassAction) -> Path | None:
    if isinstance(content_type, Spell):
        folder = config.get_spell_icons()
    elif isinstance(content_type, Item):
        folder = config.get_item_icons()
    elif isinstance(content_type, ClassAction):
        folder = config.get_ability_icons()
    elif isinstance(content_type, NPC):
        return _resolve_image_for_npc(content_type)
    guess_file_name = content_type.name.replace(" ", "_").lower()
    guess = folder / f"{guess_file_name}.png"
    return guess if guess.exists() else None

# --- Tree model utilities ---
ROLE_LOCATION_PTR = QtCore.Qt.ItemDataRole.UserRole + 1
ROLE_NPC_PTR = QtCore.Qt.ItemDataRole.UserRole + 2   # NEW

def build_tree_model(locations: List[Location]) -> QtGui.QStandardItemModel:
    """
    Build a two-column tree:
    Column 0: Location name
    Column 1: Short description
    """
    model = QtGui.QStandardItemModel()
    model.setHorizontalHeaderLabels(["Location", "Short Description"])

    # Index by object to avoid duplicate insertion
    top_level = [loc for loc in locations if loc.parent is None]

    def make_item(loc: Location) -> List[QtGui.QStandardItem]:
        name_item = QtGui.QStandardItem(loc.name)
        name_item.setEditable(False)
        name_item.setData(loc, ROLE_LOCATION_PTR)
        # Tooltip with more detail
        name_item.setToolTip(f"{loc.name}\n\n{loc.description}")

        desc_item = QtGui.QStandardItem(loc.short_description(80))
        desc_item.setEditable(False)
        desc_item.setToolTip(loc.description)

        return [name_item, desc_item]

    def add_node(parent_item: Optional[QtGui.QStandardItem], loc: Location):
        items = make_item(loc)
        if parent_item is None:
            model.appendRow(items)
        else:
            parent_item.appendRow(items)
        # Recurse for children
        for child in loc.children:
            add_node(items[0], child)

    for loc in top_level:
        add_node(None, loc)

    return model

def filter_tree(tree_view: QtWidgets.QTreeView, model: QtGui.QStandardItemModel, text: str):
    """
    Simple name/description filter that hides non-matching branches.
    Shows a parent if any descendant matches.
    """
    t = text.strip().lower()

    def node_matches(item: QtGui.QStandardItem) -> bool:
        loc: Location = item.data(ROLE_LOCATION_PTR)
        if not loc:
            return False
        hay = " ".join([loc.name, loc.description, loc.region or "", " ".join(loc.tags)]).lower()
        return (t in hay) if t else True

    def apply(item: QtGui.QStandardItem) -> bool:
        # Check self and children
        match_self = node_matches(item)
        any_child_match = False
        for row in range(item.rowCount()):
            child = item.child(row, 0)
            if child:
                child_match = apply(child)
                any_child_match = any_child_match or child_match
        
        visible = match_self or any_child_match
        
        # Hide/show rows using the tree view
        index = item.index()
        if index.isValid():
            tree_view.setRowHidden(index.row(), index.parent(), not visible)
        
        return visible

    # Apply to all top-level nodes
    for r in range(model.rowCount()):
        root_item = model.item(r, 0)
        if root_item:
            apply(root_item)

# --- Main Window ---
class PathConfigDialog(QtWidgets.QDialog):
    """Dialog for configuring Data and Media directory paths"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Paths")
        self.setModal(True)
        self.resize(500, 200)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Data directory section
        data_group = QtWidgets.QGroupBox("Data Directory")
        data_layout = QtWidgets.QHBoxLayout(data_group)
        
        self.data_path_edit = QtWidgets.QLineEdit(config.data_dir)
        data_browse_btn = QtWidgets.QPushButton("Browse...")
        data_browse_btn.clicked.connect(self.browse_data_dir)
        
        data_layout.addWidget(self.data_path_edit)
        data_layout.addWidget(data_browse_btn)
        
        # Media directory section
        media_group = QtWidgets.QGroupBox("Media Directory")
        media_layout = QtWidgets.QHBoxLayout(media_group)
        
        self.media_path_edit = QtWidgets.QLineEdit(config.media_dir)
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
        config.data_dir = new_data_dir
        config.media_dir = new_media_dir
        config.save()
        
        QtWidgets.QMessageBox.information(self, "Paths Updated", 
            "Directory paths have been updated. Please restart the application for changes to take effect.")
        
        self.accept()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, locations: List[Location], kb: KnowledgeBase):
        super().__init__()
        self.setWindowTitle("DM Helper — Locations & NPCs")
        self.resize(1000, 640)
        self.locations = locations
        self.kb = kb

        # Widgets
        self.search = QtWidgets.QLineEdit(placeholderText="Search locations…")
        self.location_tree = QtWidgets.QTreeView()
        self.location_tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.location_tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.location_tree.setAlternatingRowColors(True)
        self.location_tree.setUniformRowHeights(True)
        self.location_tree.setExpandsOnDoubleClick(True)

        self.npc_list = QtWidgets.QListWidget()
        self.npc_list.itemDoubleClicked.connect(self.open_npc_detail)

        # Create menu bar
        self.create_menu_bar()

        # Build model
        self.model = build_tree_model(self.locations)
        self.proxy = QtCore.QSortFilterProxyModel()  # not filtering via proxy; we keep it for header resize behavior
        self.proxy.setSourceModel(self.model)
        self.location_tree.setModel(self.model)
        self.location_tree.header().setStretchLastSection(False)
        self.location_tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.location_tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)

        # Layouts
        left = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.addWidget(self.search)
        left_layout.addWidget(self.location_tree)

        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.addWidget(QtWidgets.QLabel("NPCs in Location:"))
        right_layout.addWidget(self.npc_list)

        splitter = QtWidgets.QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        container = QtWidgets.QWidget()
        root_layout = QtWidgets.QVBoxLayout(container)
        root_layout.addWidget(splitter)
        self.setCentralWidget(container)

        # Signals
        self.search.textChanged.connect(self.on_search_text_changed)
        self.location_tree.selectionModel().selectionChanged.connect(self.on_location_selected)

        # Expand all to reveal nested nodes; select first if present
        self.location_tree.expandAll()
        first_index = self.model.index(0, 0)
        if first_index.isValid():
            self.location_tree.setCurrentIndex(first_index)
            self.on_location_selected()

        self.statusBar().showMessage("Select a location to see its NPCs. Hover a location for full description.")

    def on_search_text_changed(self, text: str):
        filter_tree(self.location_tree, self.model, text)
        # Keep expanded to show matching descendants
        self.location_tree.expandAll()

    def _index_to_location(self, index: QtCore.QModelIndex) -> Optional[Location]:
        if not index.isValid():
            return None
        item = self.model.itemFromIndex(index.siblingAtColumn(0))
        if not item:
            return None
        return item.data(ROLE_LOCATION_PTR)

    def on_location_selected(self):
        indexes = self.location_tree.selectionModel().selectedIndexes()
        if not indexes:
            self.npc_list.clear()
            return
        # Always use column 0 for the data payload
        idx0 = indexes[0].siblingAtColumn(0)
        loc = self._index_to_location(idx0)
        if not loc:
            self.npc_list.clear()
            return
        self.populate_npcs(loc)

    def populate_npcs(self, location: Location):
        self.npc_list.clear()
        for npc in location.npcs:
            item = QtWidgets.QListWidgetItem(npc.name)
            item.setData(ROLE_NPC_PTR, npc)
            # Hover tooltip for NPC
            tooltip = self._npc_tooltip(npc)
            item.setToolTip(tooltip)
            self.npc_list.addItem(item)

    def open_npc_detail(self, item: QtWidgets.QListWidgetItem):
        npc = item.data(ROLE_NPC_PTR)
        if not npc:
            return
        window = NPCDetailWindow(npc, self.kb, self)
        window.show()


    def _npc_tooltip(self, npc: NPC) -> str:
        appearance = npc.appearance or ""
        if len(appearance) > 160:
            appearance = appearance[:160].rstrip() + "…"
        return (f"{npc.name}\n"
                f"Race: {npc.race.value}\n"
                f"Alignment: {npc.alignment.value}\n\n"
                f"{appearance}")

    def create_menu_bar(self):
        """Create the menu bar with File, Edit, NPCs, Spells, Items, and Help menus"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        refresh_action = QtGui.QAction("&Refresh Data", self)
        refresh_action.setShortcut("F5")
        refresh_action.setStatusTip("Reload all location and NPC data")
        refresh_action.triggered.connect(self.refresh_data)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        export_action = QtGui.QAction("&Export...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setStatusTip("Export data to file")
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QtGui.QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings Menu
        settings_menu = menubar.addMenu("&Settings")
        
        configure_paths_action = QtGui.QAction("Configure &Paths...", self)
        configure_paths_action.setStatusTip("Configure Data and Media directory paths")
        configure_paths_action.triggered.connect(self.configure_paths)
        settings_menu.addAction(configure_paths_action)
        
        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        
        find_action = QtGui.QAction("&Find...", self)
        find_action.setShortcut("Ctrl+F")
        find_action.setStatusTip("Focus on search bar")
        find_action.triggered.connect(self.focus_search)
        edit_menu.addAction(find_action)
        
        clear_search_action = QtGui.QAction("&Clear Search", self)
        clear_search_action.setShortcut("Escape")
        clear_search_action.setStatusTip("Clear the search filter")
        clear_search_action.triggered.connect(self.clear_search)
        edit_menu.addAction(clear_search_action)
        
        # NPCs Menu
        npcs_menu = menubar.addMenu("&NPCs")
        
        browse_npcs_action = QtGui.QAction("&Browse All NPCs", self)
        browse_npcs_action.setShortcut("Ctrl+N")
        browse_npcs_action.setStatusTip("Browse all NPCs in the campaign")
        browse_npcs_action.triggered.connect(self.show_npcs)
        npcs_menu.addAction(browse_npcs_action)

        # Locations Menu  
        locations_menu = menubar.addMenu("&Locations")
        
        browse_locations_action = QtGui.QAction("&Browse Locations", self)
        browse_locations_action.setShortcut("Ctrl+L")
        browse_locations_action.setStatusTip("Browse all Locations in the campaign")
        browse_locations_action.triggered.connect(self.show_locations)
        locations_menu.addAction(browse_locations_action)
        
        # Spells Menu
        spells_menu = menubar.addMenu("&Spells")
        
        browse_spells_action = QtGui.QAction("&Browse Spells", self)
        browse_spells_action.setShortcut("Ctrl+S")
        browse_spells_action.setStatusTip("Browse spells and magic")
        browse_spells_action.triggered.connect(self.show_spells)
        spells_menu.addAction(browse_spells_action)
        
        # Items Menu
        items_menu = menubar.addMenu("&Items")
        
        browse_items_action = QtGui.QAction("&Browse Items", self)
        browse_items_action.setShortcut("Ctrl+I")
        browse_items_action.setStatusTip("Browse items and equipment")
        browse_items_action.triggered.connect(self.show_items)
        items_menu.addAction(browse_items_action)
        
        # Sounds Menu
        sounds_menu = menubar.addMenu("&Sounds")
        
        browse_sounds_action = QtGui.QAction("&Browse Sounds", self)
        browse_sounds_action.setShortcut("Ctrl+U")
        browse_sounds_action.setStatusTip("Browse and generate audio clips")
        browse_sounds_action.triggered.connect(self.show_sounds)
        sounds_menu.addAction(browse_sounds_action)
        
        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")
        
        expand_all_action = QtGui.QAction("&Expand All", self)
        expand_all_action.setShortcut("Ctrl+Plus")
        expand_all_action.setStatusTip("Expand all location nodes")
        expand_all_action.triggered.connect(self.location_tree.expandAll)
        tools_menu.addAction(expand_all_action)
        
        collapse_all_action = QtGui.QAction("&Collapse All", self)
        collapse_all_action.setShortcut("Ctrl+Minus")
        collapse_all_action.setStatusTip("Collapse all location nodes")
        collapse_all_action.triggered.connect(self.location_tree.collapseAll)
        tools_menu.addAction(collapse_all_action)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QtGui.QAction("&About", self)
        about_action.setStatusTip("About DM Helper")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def refresh_data(self):
        """Refresh all data from files"""
        QtWidgets.QMessageBox.information(self, "Refresh", "Data refresh functionality coming soon!")
    
    def export_data(self):
        """Export data to a file"""
        QtWidgets.QMessageBox.information(self, "Export", "Export functionality coming soon!")
    
    def configure_paths(self):
        """Configure Data and Media directory paths"""
        dialog = PathConfigDialog(self)
        dialog.exec()
    
    def focus_search(self):
        """Focus on the search bar"""
        self.search.setFocus()
        self.search.selectAll()
    
    def clear_search(self):
        """Clear the search filter"""
        self.search.clear()
    
    def show_about(self):
        """Show about dialog"""
        QtWidgets.QMessageBox.about(self, "About DM Helper", 
            "DM Helper v1.0\n\n"
            "A tool for managing D&D campaign locations and NPCs.\n\n"
            "Built with PyQt6")
        
    def show_npcs(self):
        """Show NPCs browser window"""
        npcs_window = NPCsBrowserWindow(self.kb, self)
        npcs_window.show()

    def show_items(self):
        """Show items browser window"""
        items_window = ItemsBrowserWindow(self.kb, self)
        items_window.show()
    
    def show_sounds(self):
        """Show sounds browser window"""
        sounds_window = SoundsBrowserWindow(self.kb, self)
        sounds_window.show()
    
    def show_spells(self):
        """Show spells browser window"""
        spells_window = SpellsBrowserWindow(self.kb, self)
        spells_window.show()

    def show_locations(self):
        """Show locations browser window"""
        locations_window = LocationsBrowserWindow(self.kb, self.locations, self)
        locations_window.show()
# --- Spells Browser and Detail Windows ---
class SpellsBrowserWindow(QtWidgets.QMainWindow):
    """Window for browsing all Spells in the campaign"""
    def __init__(self, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.kb = kb
        self.setWindowTitle("Spells Browser")
        self.resize(800, 600)

        # Apply dialog theme
        from theme import DMHelperTheme
        DMHelperTheme.apply_to_dialog(self)

        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Title and search
        title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("All Spells")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Search bar
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search Spells...")
        self.search.textChanged.connect(self.filter_spells)
        layout.addWidget(self.search)

        # Spells list
        self.spells_list = QtWidgets.QListWidget()
        self.spells_list.itemDoubleClicked.connect(self.open_spell_detail)
        self.spells_list.setSpacing(2)
        self.spells_list.setUniformItemSizes(True)
        layout.addWidget(self.spells_list)

        # Populate with spells
        self.populate_spells()

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        self.setCentralWidget(central_widget)

    def populate_spells(self):
        """Populate the list with all Spells from the repository"""
        self.spells_list.clear()
        try:
            from repo import Repo
            repo = Repo(config.data_dir)
            repo.load_all()
            all_spells = list(repo.spells)
        except Exception as e:
            print(f"Failed to load spells from repo: {e}")
            all_spells = []
        all_spells.sort(key=lambda x: x.name.lower())
        for spell in all_spells:
            item = QtWidgets.QListWidgetItem(spell.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, spell)
            item.setSizeHint(QtCore.QSize(0, 32))
            tooltip = self.create_spell_tooltip(spell)
            item.setToolTip(tooltip)
            self.spells_list.addItem(item)

    def create_spell_tooltip(self, spell: Spell) -> str:
        desc = spell.description or "No description"
        if len(desc) > 160:
            desc = desc[:160].rstrip() + "…"
        return (f"{spell.name}\nLevel: {spell.level}  School: {spell.school}\n\n{desc}")

    def filter_spells(self, text: str):
        text = text.lower().strip()
        for i in range(self.spells_list.count()):
            item = self.spells_list.item(i)
            spell = item.data(QtCore.Qt.ItemDataRole.UserRole)
            searchable_text = " ".join([
                spell.name,
                str(spell.level),
                spell.school,
                spell.casting_time,
                spell.range,
                spell.components,
                spell.duration,
                spell.description or "",
                " ".join(getattr(spell, "tags", [])),
                " ".join(getattr(spell, "aliases", [])),
            ]).lower()
            item.setHidden(text not in searchable_text if text else False)

    def open_spell_detail(self, item: QtWidgets.QListWidgetItem):
        spell = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not spell:
            return
        window = SpellDetailWindow(spell, self.kb, self)
        window.show()


class SpellDetailWindow(QtWidgets.QMainWindow):
    def __init__(self, spell: Spell, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.spell = spell
        self.kb = kb
        self.setWindowTitle(f"Spell — {spell.name}")
        self.resize(600, 520)

        from theme import DMHelperTheme
        DMHelperTheme.apply_to_dialog(self)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        content = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        
        # Set field growth policy for better macOS compatibility
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.WrapLongRows)

        def label(text: str) -> QtWidgets.QLabel:
            lab = QtWidgets.QLabel(text)
            lab.setWordWrap(True)
            lab.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextSelectableByMouse |
                QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse
            )
            # Set minimum width to ensure proper text display on macOS
            lab.setMinimumWidth(300)
            lab.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
            return lab

        # Icon if available
        icon_path = _resolve_image_for_entry(spell)
        if icon_path:
            img_label = QtWidgets.QLabel()
            img_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
            pix = QtGui.QPixmap(str(icon_path))
            if not pix.isNull():
                img_label.setPixmap(pix.scaledToWidth(150, QtCore.Qt.TransformationMode.SmoothTransformation))
                form.addRow("Icon:", img_label)

        form.addRow("Name:", label(spell.name))
        form.addRow("Level:", label(str(spell.level)))
        form.addRow("School:", label(spell.school))
        form.addRow("Casting Time:", label(spell.casting_time))
        form.addRow("Range:", label(spell.range))
        form.addRow("Damage:", label(spell.damage if spell.damage else "N/A"))
        form.addRow("Components:", label(spell.components))
        form.addRow("Duration:", label(spell.duration))
        form.addRow("Upcasting:", label(spell.upcast_info))
        form.addRow("Description:", label(spell.description or ""))

        scroll.setWidget(content)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.close)
        btns.accepted.connect(self.close)

        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.addWidget(scroll)
        layout.addWidget(btns)
        self.setCentralWidget(central_widget)


# --- Items Browser and Detail Windows ---
class ItemsBrowserWindow(QtWidgets.QMainWindow):
    """Window for browsing all Items in the campaign"""
    def __init__(self, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.kb = kb
        self.setWindowTitle("Items Browser")
        self.resize(800, 600)

        # Apply dialog theme
        from theme import DMHelperTheme
        DMHelperTheme.apply_to_dialog(self)

        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Title and search
        title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("All Items")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Search bar
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search Items...")
        self.search.textChanged.connect(self.filter_items)
        layout.addWidget(self.search)

        # Items list
        self.items_list = QtWidgets.QListWidget()
        self.items_list.itemDoubleClicked.connect(self.open_item_detail)
        self.items_list.setSpacing(2)
        self.items_list.setUniformItemSizes(True)
        layout.addWidget(self.items_list)

        # Populate with items
        self.populate_items()

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        self.setCentralWidget(central_widget)

    def populate_items(self):
        """Populate the list with all Items from the repository"""
        self.items_list.clear()
        try:
            from repo import Repo
            repo = Repo(config.data_dir)
            repo.load_all()
            all_items = list(repo.items)
        except Exception as e:
            print(f"Failed to load items from repo: {e}")
            all_items = []
        
        all_items.sort(key=lambda x: x.name.lower())
        for item in all_items:
            item_widget = QtWidgets.QListWidgetItem(item.name)
            item_widget.setData(QtCore.Qt.ItemDataRole.UserRole, item)
            item_widget.setSizeHint(QtCore.QSize(0, 32))
            tooltip = self.create_item_tooltip(item)
            item_widget.setToolTip(tooltip)
            self.items_list.addItem(item_widget)

    def create_item_tooltip(self, item: Item) -> str:
        desc = item.description or "No description"
        if len(desc) > 160:
            desc = desc[:160].rstrip() + "…"
        attunement_text = " (Requires Attunement)" if item.attunement else ""
        return (f"{item.name}\nRarity: {item.rarity}{attunement_text}\n\n{desc}")

    def filter_items(self, text: str):
        text = text.lower().strip()
        for i in range(self.items_list.count()):
            item_widget = self.items_list.item(i)
            item = item_widget.data(QtCore.Qt.ItemDataRole.UserRole)
            searchable_text = " ".join([
                item.name,
                item.rarity,
                item.description or "",
                " ".join(getattr(item, "tags", [])),
                " ".join(getattr(item, "aliases", [])),
                "attunement" if item.attunement else "",
            ]).lower()
            item_widget.setHidden(text not in searchable_text if text else False)

    def open_item_detail(self, item_widget: QtWidgets.QListWidgetItem):
        item = item_widget.data(QtCore.Qt.ItemDataRole.UserRole)
        if not item:
            return
        window = ItemDetailWindow(item, self.kb, self)
        window.show()


class ItemDetailWindow(QtWidgets.QMainWindow):
    def __init__(self, item, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.item = item
        self.kb = kb
        self.setWindowTitle(f"Item — {item.name}")
        self.resize(600, 520)

        from theme import DMHelperTheme
        DMHelperTheme.apply_to_dialog(self)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        content = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        
        # Set field growth policy for better macOS compatibility
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.WrapLongRows)

        def label(text: str) -> QtWidgets.QLabel:
            lab = QtWidgets.QLabel(text)
            lab.setWordWrap(True)
            lab.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextSelectableByMouse |
                QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse
            )
            # Set minimum width to ensure proper text display on macOS
            lab.setMinimumWidth(300)
            lab.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
            return lab

        # Icon if available
        icon_path = _resolve_image_for_entry(item)
        if icon_path:
            img_label = QtWidgets.QLabel()
            img_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
            pix = QtGui.QPixmap(str(icon_path))
            if not pix.isNull():
                img_label.setPixmap(pix.scaledToWidth(80, QtCore.Qt.TransformationMode.SmoothTransformation))
                form.addRow("Icon:", img_label)

        form.addRow("Name:", label(item.name))
        form.addRow("Rarity:", label(item.rarity))
        form.addRow("Attunement:", label("Yes" if item.attunement else "No"))
        form.addRow("Tags:", label(", ".join(getattr(item, "tags", []))))
        form.addRow("Aliases:", label(", ".join(getattr(item, "aliases", []))))
        form.addRow("Description:", label(item.description or ""))

        scroll.setWidget(content)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.close)
        btns.accepted.connect(self.close)

        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.addWidget(scroll)
        layout.addWidget(btns)
        self.setCentralWidget(central_widget)


# --- Sounds Browser Window ---
class SoundsBrowserWindow(QtWidgets.QMainWindow):
    """Window for browsing and generating audio clips"""
    def __init__(self, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.kb = kb
        self.setWindowTitle("Sounds Browser")
        self.resize(800, 600)

        # Apply dialog theme
        from theme import DMHelperTheme
        DMHelperTheme.apply_to_dialog(self)

        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Title and search
        title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("Audio Clips")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Add Sound button
        add_sound_btn = QtWidgets.QPushButton("Add Sound")
        add_sound_btn.setToolTip("Generate a new audio clip")
        add_sound_btn.clicked.connect(self.add_sound)
        title_layout.addWidget(add_sound_btn)
        
        layout.addLayout(title_layout)

        # Search bar
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search audio clips...")
        self.search.textChanged.connect(self.filter_sounds)
        layout.addWidget(self.search)

        # Sounds list
        self.sounds_list = QtWidgets.QListWidget()
        self.sounds_list.setSpacing(2)
        self.sounds_list.setUniformItemSizes(True)
        layout.addWidget(self.sounds_list)

        # Populate with existing sounds
        self.populate_sounds()

        # Control buttons
        control_layout = QtWidgets.QHBoxLayout()
        
        # Play button
        play_btn = QtWidgets.QPushButton("Play")
        play_btn.setToolTip("Play selected audio clip")
        play_btn.clicked.connect(self.play_selected_sound)
        control_layout.addWidget(play_btn)
        
        # Stop button  
        stop_btn = QtWidgets.QPushButton("Stop")
        stop_btn.setToolTip("Stop audio playback")
        stop_btn.clicked.connect(self.stop_sound)
        control_layout.addWidget(stop_btn)
        
        # Delete button
        delete_btn = QtWidgets.QPushButton("Delete")
        delete_btn.setToolTip("Delete selected audio clip")
        delete_btn.clicked.connect(self.delete_selected_sound)
        control_layout.addWidget(delete_btn)
        
        control_layout.addStretch()
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        control_layout.addWidget(close_btn)
        
        layout.addLayout(control_layout)
        self.setCentralWidget(central_widget)

    def populate_sounds(self):
        """Populate the list with existing audio files"""
        self.sounds_list.clear()
        
        # Look for audio files in Media/Audio directory
        audio_dir = config.get_audio_files()
        if not audio_dir.exists():
            return
        
        # Find all audio files
        audio_extensions = {'.mp3', '.wav', '.m4a', '.ogg', '.flac'}
        audio_files = []
        
        for ext in audio_extensions:
            audio_files.extend(audio_dir.glob(f'*{ext}'))
        
        # Sort by name
        audio_files.sort(key=lambda x: x.name.lower())
        
        # Add to list widget
        for audio_file in audio_files:
            item = QtWidgets.QListWidgetItem(audio_file.stem)  # Name without extension
            item.setData(QtCore.Qt.ItemDataRole.UserRole, str(audio_file))  # Store full path
            item.setSizeHint(QtCore.QSize(0, 32))
            
            # Create tooltip with file info
            tooltip = f"File: {audio_file.name}\nPath: {audio_file}"
            try:
                file_size = audio_file.stat().st_size
                tooltip += f"\nSize: {file_size:,} bytes"
            except:
                pass
            item.setToolTip(tooltip)
            
            self.sounds_list.addItem(item)

    def filter_sounds(self, text: str):
        """Filter the sounds list based on search text"""
        text = text.lower().strip()
        
        for i in range(self.sounds_list.count()):
            item = self.sounds_list.item(i)
            # Search in filename
            item.setHidden(text not in item.text().lower() if text else False)

    def add_sound(self):
        """Add/generate a new sound"""
        dialog = AddSoundDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Refresh the sounds list to show the new sound
            self.populate_sounds()

    def play_selected_sound(self):
        """Play the selected audio clip"""
        current_item = self.sounds_list.currentItem()
        if not current_item:
            QtWidgets.QMessageBox.information(self, "No Selection", "Please select an audio clip to play.")
            return
        
        audio_path = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
        try:
            # Try to play using system default audio player
            import subprocess
            import sys
            
            if sys.platform == "win32":
                # Windows
                subprocess.run(['start', '', audio_path], shell=True, check=False)
            elif sys.platform == "darwin":
                # macOS
                subprocess.run(['open', audio_path], check=False)
            else:
                # Linux
                subprocess.run(['xdg-open', audio_path], check=False)
                
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Playback Error", 
                f"Could not play audio file:\n{str(e)}")

    def stop_sound(self):
        """Stop audio playback (placeholder - system dependent)"""
        QtWidgets.QMessageBox.information(self, "Stop", 
            "Audio playback stop is handled by your system's audio player.")

    def delete_selected_sound(self):
        """Delete the selected audio clip"""
        current_item = self.sounds_list.currentItem()
        if not current_item:
            QtWidgets.QMessageBox.information(self, "No Selection", "Please select an audio clip to delete.")
            return
        
        audio_path = Path(current_item.data(QtCore.Qt.ItemDataRole.UserRole))
        
        # Confirm deletion
        reply = QtWidgets.QMessageBox.question(self, "Confirm Delete",
            f"Are you sure you want to delete '{current_item.text()}'?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                audio_path.unlink()  # Delete the file
                self.populate_sounds()  # Refresh the list
                QtWidgets.QMessageBox.information(self, "Deleted", 
                    f"Audio clip '{current_item.text()}' has been deleted.")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Delete Error", 
                    f"Could not delete file:\n{str(e)}")


class CampaignNotesDialog(QtWidgets.QDialog):
    """Dialog for editing campaign notes for an NPC"""
    def __init__(self, npc: NPC, parent=None):
        super().__init__(parent)
        self.npc = npc
        self.setWindowTitle(f"Campaign Notes - {npc.name}")
        self.resize(600, 500)
        
        # Apply theme
        from theme import DMHelperTheme
        DMHelperTheme.apply_to_dialog(self)
        
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
        npcs_file = Path(config.data_dir) / "npcs.json"
        
        if not npcs_file.exists():
            raise Exception("NPCs file not found")
        
        # Load existing NPCs
        with open(npcs_file, 'r', encoding='utf-8') as f:
            npcs_data = json.load(f)
        
        # Find and update the NPC entry
        npc_updated = False
        for npc_entry in npcs_data:
            # Try to match by name first, then by id if available
            if npc_entry.get("name") == self.npc.name:
                npc_entry["campaign_notes"] = self.npc.campaign_notes
                npc_updated = True
                break
        
        if not npc_updated:
            raise Exception(f"Could not find NPC '{self.npc.name}' in the data file")
        
        # Save back to file
        with open(npcs_file, 'w', encoding='utf-8') as f:
            json.dump(npcs_data, f, indent=2, ensure_ascii=False)


class AddSoundDialog(QtWidgets.QDialog):
    """Dialog for generating new audio clips"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Sound Clip")
        self.resize(500, 400)
        
        # Apply theme
        from theme import DMHelperTheme
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
        from sound_generation import AudioGenerationMode
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
            audio_dir = config.get_audio_files()
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
                import shutil
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
                progress.setWindowTitle("Generating with Stability AI")
                progress.setAutoClose(False)
                progress.setAutoReset(False)
                progress.setCancelButton(None)
                progress.show()
                
                # Process events to show the dialog immediately
                QtWidgets.QApplication.processEvents()
                
                try:
                    # Generate the sound
                    from sound_generation import SoundGenerator
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


class NPCDetailWindow(QtWidgets.QMainWindow):
    def __init__(self, npc: NPC, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.npc = npc
        self.kb = kb
        self.setWindowTitle(f"NPC — {npc.name}")
        self.resize(600, 520)
        
        # Apply dialog theme
        from theme import DMHelperTheme
        DMHelperTheme.apply_to_dialog(self)

        # Use a scroll area in case backstory is long
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)

        content = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        
        # Set field growth policy for better macOS compatibility
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.WrapLongRows)

        # Helper to make selectable, wrapped labels with minimum width
        def label(text: str) -> QtWidgets.QLabel:
            lab = QtWidgets.QLabel(text)
            lab.setWordWrap(True)
            lab.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextSelectableByMouse |
                QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse
            )
            # Set minimum width to ensure proper text display on macOS
            lab.setMinimumWidth(300)
            lab.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
            return lab

        portrait_path = _resolve_image_for_npc(npc)
        if portrait_path:
            img_label = QtWidgets.QLabel()
            img_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
            pix = QtGui.QPixmap(str(portrait_path))
            if not pix.isNull():
                # scale to a smaller width for this dialog; keeps aspect ratio
                img_label.setPixmap(pix.scaledToWidth(300, QtCore.Qt.TransformationMode.SmoothTransformation))
                form.addRow("Portrait:", img_label)
        else:
            generate_btn = QtWidgets.QPushButton("Generate Portrait")
            generate_btn.setToolTip("Generate an AI portrait for this NPC")
            generate_btn.clicked.connect(self.generate_portrait)
            form.addRow("Portrait:", generate_btn)

        form.addRow("Name:", label(npc.name))
        form.addRow("Race:", label(npc.race.value))
        form.addRow("Sex:", label(npc.sex))
        form.addRow("Age:", label(npc.age))
        form.addRow("Alignment:", label(npc.alignment.value))

        # Appearance / Backstory as large wrapped labels
        form.addRow("Appearance:", label(npc.appearance or ""))
        form.addRow("Backstory:", label(npc.backstory or ""))

        # StatBlock info (simple for now)
        sb = npc.stat_block
        sb_text = sb.display_name if sb else "None"
        self.stat_btn = QtWidgets.QPushButton(sb_text)
        self.stat_btn.setEnabled(sb is not None)
        self.stat_btn.clicked.connect(self.open_statblock)
        form.addRow("Stat Block:", self.stat_btn)

        scroll.setWidget(content)

        # Buttons (Edit, Campaign Notes, and Close)
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close
        )
        
        # Add custom Edit button
        edit_btn = QtWidgets.QPushButton("Edit")
        edit_btn.setToolTip("Edit this NPC")
        edit_btn.clicked.connect(self.edit_npc)
        btns.addButton(edit_btn, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        
        # Add custom Campaign Notes button
        campaign_notes_btn = QtWidgets.QPushButton("Campaign Notes")
        campaign_notes_btn.setToolTip("View and edit campaign notes for this NPC")
        campaign_notes_btn.clicked.connect(self.open_campaign_notes)
        btns.addButton(campaign_notes_btn, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        
        btns.rejected.connect(self.close)
        btns.accepted.connect(self.close)

        # Central widget setup for QMainWindow
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.addWidget(scroll)
        layout.addWidget(btns)
        self.setCentralWidget(central_widget)

    def open_statblock(self):
        if not self.npc.stat_block:
            return
        window = StatBlockWindow(self.npc.stat_block, self.kb, self.npc.additional_traits, self)
        window.show()

    def generate_portrait(self):
        """Generate an AI portrait for this NPC with loading dialog and auto-refresh"""
        try:
            # Show loading dialog
            progress = QtWidgets.QProgressDialog("Generating portrait...", "Cancel", 0, 0, self)
            progress.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Stability AI Image Generation")
            progress.setAutoClose(False)  # Don't auto-close so we control it
            progress.setAutoReset(False)
            progress.setCancelButton(None)  # Remove cancel button for simplicity
            progress.show()
            
            # Process events to show the dialog immediately
            QtWidgets.QApplication.processEvents()
            
            # Generate the portrait
            image_generator = ImageGenerator()
            image_generator.create_character_portrait(self.npc, ImageGenerationMode.CORE)
            
            # Close the progress dialog
            progress.close()
            
            # Check if the portrait was actually created
            portrait_path = _resolve_image_for_npc(self.npc)
            if portrait_path and Path(portrait_path).exists():
                # Portrait generated successfully - show success message
                QtWidgets.QMessageBox.information(self, "Success", 
                    f"Portrait generated successfully for {self.npc.name}!")
                
                # Reload the window to show the new portrait
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
        # Store the current window position and size
        geometry = self.geometry()
        
        # Create a new window with the same NPC
        new_window = NPCDetailWindow(self.npc, self.kb, self.parent())
        new_window.setGeometry(geometry)  # Keep same position/size
        new_window.show()
        
        # Close the current window
        self.close()

    def open_campaign_notes(self):
        """Open the campaign notes dialog for this NPC"""
        dialog = CampaignNotesDialog(self.npc, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # NPC's campaign_notes have been updated, optionally refresh the window
            pass
        

class StatBlockWindow(QtWidgets.QMainWindow):
    def __init__(self, sb: StatBlock, kb: KnowledgeBase, traits: list | None = None, parent=None):
        super().__init__(parent)
        self.sb = sb
        self.kb = kb
        self.traits = traits if traits is not None else []
        
        # Apply dialog theme
        from theme import DMHelperTheme
        DMHelperTheme.apply_to_dialog(self)
        
        self._hover = HoverPreview(self)

        self.setWindowTitle("Stat Block")
        self.resize(640, 720)

        # Central widget setup for QMainWindow
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Scrollable content
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        content = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(content)
        vbox.setContentsMargins(12, 12, 12, 12)
        vbox.setSpacing(10)

        # Helper label
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

        # Branch on StatBlock type
        if isinstance(sb, PcClass):
            # Minimal info from PcClass (name + level)
            vbox.addWidget(label("Player Class", bold=True))
            name = getattr(sb, "name", None)
            level = getattr(sb, "level", None)
            spells = getattr(sb, "spells", [])
            weapons = getattr(sb, "weapons", [])
            vbox.addWidget(label(f"Class: {getattr(name, 'value', str(name) or 'Unknown')}"))
            vbox.addWidget(label(f"Level: {level if level is not None else 'Unknown'}"))
            
            # Add Ability Scores
            ability_scores = getattr(sb, "ability_scores", None)
            if ability_scores:
                vbox.addWidget(label("Ability Scores", bold=True))
                
                # Create two-column layout for ability scores
                abilities_widget = QtWidgets.QWidget()
                abilities_layout = QtWidgets.QHBoxLayout(abilities_widget)
                abilities_layout.setContentsMargins(0, 0, 0, 0)
                
                # Left column: STR, DEX, CON
                left_column = QtWidgets.QVBoxLayout()
                left_column.addWidget(label(f"Strength: {ability_scores.Strength}"))
                left_column.addWidget(label(f"Dexterity: {ability_scores.Dexterity}"))
                left_column.addWidget(label(f"Constitution: {ability_scores.Constitution}"))
                
                # Right column: INT, WIS, CHA
                right_column = QtWidgets.QVBoxLayout()
                right_column.addWidget(label(f"Intelligence: {ability_scores.Intelligence}"))
                right_column.addWidget(label(f"Wisdom: {ability_scores.Wisdom}"))
                right_column.addWidget(label(f"Charisma: {ability_scores.Charisma}"))
                
                abilities_layout.addLayout(left_column)
                abilities_layout.addLayout(right_column)
                vbox.addWidget(abilities_widget)
            
            # Add Spell Slots
            spell_slots = getattr(sb, "spell_slots", [])
            if spell_slots:
                vbox.addWidget(label("Spell Slots", bold=True))
                for slot in spell_slots:
                    # Create horizontal layout for each spell level
                    slot_widget = QtWidgets.QWidget()
                    slot_layout = QtWidgets.QHBoxLayout(slot_widget)
                    slot_layout.setContentsMargins(0, 0, 0, 0)
                    
                    # Add level label
                    level_label = label(f"Level {slot.level}:")
                    slot_layout.addWidget(level_label)
                    
                    # Add checkboxes for each slot
                    for i in range(slot.count):
                        checkbox = QtWidgets.QCheckBox()
                        checkbox.setToolTip(f"Spell slot {i+1}")
                        checkbox.setChecked(True)  # Start all slots as available (checked/blue)
                        
                        # Custom styling for solid blue fill when checked
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
                    
                    # Add stretch to push everything to the left
                    slot_layout.addStretch()
                    vbox.addWidget(slot_widget)

            # Add Weapons (Items) heading and linkified spells display
            vbox.addWidget(label("Weapons", bold=True))
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

            # Add Spells heading and linkified spells display
            vbox.addWidget(label("Spells", bold=True))
            spells_text = ', '.join(spells) if spells else 'None'
            spells_tb = QtWidgets.QTextBrowser()
            spells_tb.setOpenExternalLinks(False)
            spells_tb.setOpenLinks(False)
            spells_tb.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
            spells_tb.setReadOnly(True)
            spells_tb.setAcceptRichText(True)
            spells_tb.setMouseTracking(True)
            spells_tb.viewport().setMouseTracking(True)
            
            html = self.kb.linkify(spells_text)
            spells_tb.setHtml(f"<div style='font-size: 12pt; line-height: 1.35'>{html}</div>")
            spells_tb.anchorClicked.connect(self._on_anchor_clicked)
            spells_tb.highlighted.connect(self._on_link_hovered)
            vbox.addWidget(spells_tb)

        elif isinstance(sb, MonsterManual):
            vbox.addWidget(label("Monster Manual Entry", bold=True))

            # Try to load the PNG page
            sb_image = getattr(sb, "stat_block_image", None)
            name = getattr(sb, "monster_name", "Unknown")
            vbox.addWidget(label(f"Name: {name}"))

            img_label = QtWidgets.QLabel()
            img_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
            if sb_image:
                sb_image_path = config.get_monster_manual_pages() / sb_image
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
            # Unknown StatBlock type
            vbox.addWidget(label("Unknown StatBlock type.", bold=True))
            vbox.addWidget(label(f"Class: {sb.__class__.__name__}"))

        # === Additional Information ===
        vbox.addSpacing(8)
        vbox.addWidget(self._bold_label("Additional Information"))
        if not self.traits:
            vbox.addWidget(self._plain_label("— (none provided) —"))
        else:
            for t in self.traits:
                tb = QtWidgets.QTextBrowser()
                tb.setOpenExternalLinks(False)  # we'll handle clicks
                tb.setOpenLinks(False)
                tb.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
                tb.setReadOnly(True)
                tb.setAcceptRichText(True)

                tb.setMouseTracking(True)  # needed for hover events
                tb.viewport().setMouseTracking(True)

                html = self.kb.linkify(t)
                tb.setHtml(f"<div style='font-size: 12pt; line-height: 1.35'>{html}</div>")
                tb.anchorClicked.connect(self._on_anchor_clicked)
                tb.highlighted.connect(self._on_link_hovered)  # hover signal gives URL as text
                vbox.addWidget(tb)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.close)
        btns.accepted.connect(self.close)
        layout.addWidget(btns)
        
        # Set the central widget
        self.setCentralWidget(central_widget)

    def _plain_label(self, text: str) -> QtWidgets.QLabel:
        lab = QtWidgets.QLabel(text)
        lab.setWordWrap(True)
        lab.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse |
                                    QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse)
        return lab

    def _bold_label(self, text: str) -> QtWidgets.QLabel:
        lab = self._plain_label(text)
        f = lab.font(); f.setBold(True); lab.setFont(f)
        return lab
    
    def _on_link_hovered(self, qurl: QtCore.QUrl):
        # url is the anchor text (we set href to label)
        if not qurl or qurl.isEmpty():
            self._hover.hide()
            return
        
        name = QtCore.QUrl.fromPercentEncoding(qurl.toEncoded())
        entry = self.kb.resolve(name)

        if not entry:
            self._hover.hide()
            return
        # Position near cursor
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
        else:
            QtWidgets.QMessageBox.warning(self, "Unknown Entry",
                "The selected entry type is not recognized.")
        window.show()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Keep monster image scaled to width while preserving aspect ratio."""
        super().resizeEvent(event)
        if hasattr(self, "_image_label") and hasattr(self, "_image_pixmap"):
            area_w = self.width() - 64  # approximate padding
            if area_w > 100:
                scaled = self._image_pixmap.scaledToWidth(area_w, QtCore.Qt.TransformationMode.SmoothTransformation)
                self._image_label.setPixmap(scaled)

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

class NPCsBrowserWindow(QtWidgets.QMainWindow):
    """Window for browsing all NPCs in the campaign"""
    def __init__(self, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.kb = kb
        self.setWindowTitle("NPCs Browser")
        self.resize(800, 600)
        
        # Apply dialog theme
        from theme import DMHelperTheme
        DMHelperTheme.apply_to_dialog(self)
        
        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Title and search
        title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("All NPCs")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Add NPC button
        add_npc_btn = QtWidgets.QPushButton("Add NPC")
        add_npc_btn.setToolTip("Create a new NPC")
        add_npc_btn.clicked.connect(self.add_npc)
        title_layout.addWidget(add_npc_btn)
        
        layout.addLayout(title_layout)
        
        # Search bar
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search NPCs...")
        self.search.textChanged.connect(self.filter_npcs)
        layout.addWidget(self.search)
        
        # NPCs list
        self.npcs_list = QtWidgets.QListWidget()
        self.npcs_list.itemDoubleClicked.connect(self.open_npc_detail)
        
        # Set proper spacing and sizing for list items
        self.npcs_list.setSpacing(2)
        self.npcs_list.setUniformItemSizes(True)
        
        layout.addWidget(self.npcs_list)
        
        # Populate with NPCs
        self.populate_npcs()
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        self.setCentralWidget(central_widget)
        
    def populate_npcs(self):
        """Populate the list with all NPCs from the repository"""
        self.npcs_list.clear()
        
        # Load NPCs directly from the repository (freshly loaded from JSON)
        try:
            from repo import Repo
            repo = Repo(config.data_dir)
            repo.load_all()  # This will reload from JSON files including any new NPCs
            
            # Get all NPCs from the repository
            all_npcs = list(repo.npcs_by_id.values())
            
        except Exception as e:
            # Fallback to knowledge base if repo loading fails
            print(f"Failed to load from repo: {e}")
            all_npcs = []
            if hasattr(self.kb, 'entries'):
                # Extract NPC entries from knowledge base
                for entry in self.kb.entries.values():
                    if entry.kind == "npc":
                        # This is a fallback - we won't have the full NPC object
                        # but at least we can show the names
                        pass
        
        # Sort NPCs by name
        all_npcs.sort(key=lambda x: x.name.lower())
        
        # Add to list widget
        for npc in all_npcs:
            item = QtWidgets.QListWidgetItem(npc.name)
            item.setData(ROLE_NPC_PTR, npc)
            
            # Set proper item size for better spacing
            item.setSizeHint(QtCore.QSize(0, 32))  # Height of 32 pixels for each item
            
            # Create tooltip with NPC info
            tooltip = self.create_npc_tooltip(npc)
            item.setToolTip(tooltip)
            
            self.npcs_list.addItem(item)
    
    def create_npc_tooltip(self, npc: NPC) -> str:
        """Create a tooltip for an NPC"""
        appearance = npc.appearance or "No appearance description"
        if len(appearance) > 160:
            appearance = appearance[:160].rstrip() + "…"
        
        return (f"{npc.name}\n"
                f"Race: {npc.race.value}\n" 
                f"Alignment: {npc.alignment.value}\n\n"
                f"{appearance}")
    
    def filter_npcs(self, text: str):
        """Filter the NPCs list based on search text"""
        text = text.lower().strip()
        
        for i in range(self.npcs_list.count()):
            item = self.npcs_list.item(i)
            npc = item.data(ROLE_NPC_PTR)
            
            # Search in name, race, alignment, and appearance
            searchable_text = " ".join([
                npc.name,
                npc.race.value,
                npc.alignment.value,
                npc.appearance or "",
                npc.backstory or ""
            ]).lower()
            
            # Show/hide based on search match
            item.setHidden(text not in searchable_text if text else False)
    
    def open_npc_detail(self, item: QtWidgets.QListWidgetItem):
        """Open the NPC detail window"""
        npc = item.data(ROLE_NPC_PTR)
        if not npc:
            return
        window = NPCDetailWindow(npc, self.kb, self)
        window.show()
    
    def add_npc(self):
        """Add a new NPC"""
        dialog = AddNPCDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Refresh the NPCs list to show the new NPC
            # populate_npcs() will reload data from JSON files
            self.populate_npcs()

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
        from theme import DMHelperTheme
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
        from race import Race
        for race in Race:
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
        from alignment import Alignment
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
                from pc_classes import PcClassName
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
            stat_block_selection = self.stat_block_selection_combo.currentText()
            
            if stat_block_type == "Monster Manual":
                file_name = stat_block_selection.replace(" ", "_").lower()
                stat_block = MonsterManual(file_name=str(file_name))
            else:  # PC Class
                # Try to get the enum value, fallback to creating from string
                try:
                    pc_class_name = PcClassName(stat_block_selection)
                except ValueError:
                    # If the selection isn't in the enum, create a custom one
                    pc_class_name = type('PcClassName', (), {'value': stat_block_selection})()
                
                stat_block = PcClass(name=pc_class_name, level=1)  # Default to level 1
            
            # Parse additional traits
            traits_text = self.traits_field.toPlainText().strip()
            traits = [line.strip() for line in traits_text.split('\n') if line.strip()] if traits_text else []
            
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
                additional_traits=traits
            )
            
            # Save to JSON file
            # Find the original ID by looking it up in the repository
            original_id = None
            if self.edit_npc:
                try:
                    from repo import Repo
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
                "level": npc.stat_block.level
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
            "campaign_notes": getattr(npc, 'campaign_notes', "")
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

# --- Locations Browser and Detail Windows ---
class LocationsBrowserWindow(QtWidgets.QMainWindow):
    """Window for browsing all Locations in the campaign"""
    def __init__(self, kb: KnowledgeBase, locations: List[Location], parent=None):
        super().__init__(parent)
        self.kb = kb
        self.locations = locations
        self.setWindowTitle("Locations Browser")
        self.resize(900, 600)

        # Apply dialog theme
        from theme import DMHelperTheme
        DMHelperTheme.apply_to_dialog(self)

        # Central widget and layout
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Title and search
        title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("All Locations")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Search bar
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search Locations...")
        self.search.textChanged.connect(self.filter_locations)
        layout.addWidget(self.search)

        # Locations list
        self.locations_list = QtWidgets.QListWidget()
        self.locations_list.itemDoubleClicked.connect(self.open_location_detail)
        self.locations_list.setSpacing(2)
        self.locations_list.setUniformItemSizes(True)
        layout.addWidget(self.locations_list)

        # Populate with locations
        self.populate_locations()

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        self.setCentralWidget(central_widget)

    def populate_locations(self):
        """Populate the list with all Locations from the repository"""
        self.locations_list.clear()
        
        # Get all locations (including nested ones)
        all_locations = []
        def collect_locations(locs):
            for loc in locs:
                all_locations.append(loc)
                if hasattr(loc, 'children') and loc.children:
                    collect_locations(loc.children)
        
        collect_locations(self.locations)
        all_locations.sort(key=lambda x: x.name.lower())
        
        for loc in all_locations:
            item = QtWidgets.QListWidgetItem(loc.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, loc)
            item.setSizeHint(QtCore.QSize(0, 32))
            tooltip = self.create_location_tooltip(loc)
            item.setToolTip(tooltip)
            self.locations_list.addItem(item)

    def create_location_tooltip(self, loc: Location) -> str:
        desc = loc.description or "No description"
        if len(desc) > 160:
            desc = desc[:160].rstrip() + "…"
        return f"{loc.name}\nRegion: {loc.region or '-'}\nNPCs: {len(loc.npcs)}\n\n{desc}"

    def filter_locations(self, text: str):
        text = text.lower().strip()
        for i in range(self.locations_list.count()):
            item = self.locations_list.item(i)
            loc = item.data(QtCore.Qt.ItemDataRole.UserRole)
            searchable_text = " ".join([
                loc.name,
                loc.region or "",
                loc.description or "",
                " ".join(getattr(loc, "tags", [])),
            ]).lower()
            item.setHidden(text not in searchable_text if text else False)

    def open_location_detail(self, item: QtWidgets.QListWidgetItem):
        loc = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not loc:
            return
        window = LocationDetailWindow(loc, self.kb, self)
        window.show()


class LocationDetailWindow(QtWidgets.QMainWindow):
    def __init__(self, location: Location, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.location = location
        self.kb = kb
        self.setWindowTitle(f"Location — {location.name}")
        self.resize(700, 600)

        # Apply dialog theme
        from theme import DMHelperTheme
        DMHelperTheme.apply_to_dialog(self)

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

        # Location details
        vbox.addWidget(label(location.name, bold=True))
        vbox.addWidget(label(f"Region: {location.region or 'Unknown'}"))
        vbox.addWidget(label(f"Description: {location.description or 'No description'}"))
        
        # Tags
        tags = ", ".join(location.tags) if location.tags else "None"
        vbox.addWidget(label(f"Tags: {tags}"))

        vbox.addSpacing(10)

        # NPCs in this location
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

        # Add NPC to location section
        vbox.addWidget(label("Add NPC to Location:", bold=True))
        
        # NPC dropdown
        self.npc_dropdown = QtWidgets.QComboBox()
        self.populate_npc_dropdown()
        vbox.addWidget(self.npc_dropdown)
        
        # Add NPC button
        add_npc_layout = QtWidgets.QHBoxLayout()
        add_btn = QtWidgets.QPushButton("Add NPC to Location")
        add_btn.clicked.connect(self.add_npc_to_location)
        add_npc_layout.addWidget(add_btn)
        add_npc_layout.addStretch()
        vbox.addLayout(add_npc_layout)

        scroll.setWidget(content)

        # Close button at bottom
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
            from repo import Repo
            repo = Repo(config.data_dir)
            repo.load_all()
            all_npcs = list(repo.npcs)
            
            # Get names of NPCs already in this location for comparison
            existing_npc_names = {npc.name for npc in self.location.npcs}
            
            # Only show NPCs not already in this location (compare by name)
            available_npcs = [npc for npc in all_npcs if npc.name not in existing_npc_names]
            
            if not available_npcs:
                self.npc_dropdown.addItem("No NPCs available to add", None)
                return
                
            # Sort by name
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
        
        # Check if NPC is already in this location (double-check to prevent duplicates)
        existing_npc_names = {existing_npc.name for existing_npc in self.location.npcs}
        if npc.name in existing_npc_names:
            QtWidgets.QMessageBox.information(self, "NPC Already Present", 
                f"'{npc.name}' is already in '{self.location.name}'.")
            return
        
        try:
            # Add NPC to location
            self.location.add_npc(npc)
            
            # Save changes to locations.json
            self.save_locations_to_json()
            
            # Show success message
            QtWidgets.QMessageBox.information(self, "NPC Added", 
                f"'{npc.name}' has been added to '{self.location.name}'.")
            
            # Refresh the window to show the updated list
            self.refresh_window()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", 
                f"Failed to add NPC to location:\n{str(e)}")

    def remove_npc_from_location(self, npc):
        """Remove an NPC from this location"""
        # Confirm removal
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

    def refresh_window(self):
        """Refresh the location detail window to show updated data"""
        # Store the current window position and size
        geometry = self.geometry()
        
        # Create a new window with the same location
        new_window = LocationDetailWindow(self.location, self.kb, self.parent())
        new_window.setGeometry(geometry)  # Keep same position/size
        new_window.show()
        
        # Close the current window
        self.close()

    def save_locations_to_json(self):
        """Update the locations.json file with current location data"""
        try:
            # Path to locations.json
            locations_file = Path(config.data_dir) / "locations.json"
            
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


# --- App entry ---
def main():
    import sys
    from theme import DMHelperTheme  # Import our theme

    repo = Repo(config.data_dir)
    repo.load_all()

    kb = KnowledgeBase()
    kb.ingest(repo.spells, repo.items, repo.class_actions)
    kb.ingest_npcs(repo.npcs_by_id.values())

    app = QtWidgets.QApplication(sys.argv)
    
    # Apply the D&D themed styling
    DMHelperTheme.apply_to_application(app)
    
    win = MainWindow(repo.locations, kb)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
