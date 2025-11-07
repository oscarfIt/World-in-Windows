from PyQt6 import QtCore, QtGui, QtWidgets

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, locations: List[Location], kb: KnowledgeBase):
        super().__init__()
        self.setWindowTitle("World in Windows")
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

        # Conditions Menu
        conditions_menu = menubar.addMenu("&Conditions")
        
        browse_conditions_action = QtGui.QAction("&Browse Conditions", self)
        browse_conditions_action.setShortcut("Ctrl+C")
        browse_conditions_action.setStatusTip("Browse D&D conditions and status effects")
        browse_conditions_action.triggered.connect(self.show_conditions)
        conditions_menu.addAction(browse_conditions_action)
        
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
        about_action.setStatusTip("About World in Windows")
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
        QtWidgets.QMessageBox.about(self, "About World in Windows", 
            "World in Windows v1.0\n\n"
            "A tool for managing D&D campaigns.\n\n"
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

    def show_conditions(self):
        """Show conditions browser window"""
        conditions_window = ConditionsBrowserWindow(self.kb, self)
        conditions_window.show()

