# dming_tool_qt.py
# Minimal PyQt6 app to browse (nested) Locations and see their NPCs.
# Changes from previous version:
# - Left pane is now a QTreeView with two columns: Name | Short Description
# - Locations can be nested (e.g., "The Salty Hound" under "Port Virellon")
# - Short description is visible directly in the tree
#
# pip install PyQt6

from PyQt6 import QtCore, QtGui, QtWidgets
from typing import List, Optional
from location import Location
from npc import NPC
from race import Race
from alignment import Alignment
from stat_block import StatBlock  # placeholder

# -----------------------
# Demo data (object-based)
# -----------------------
def seed_data() -> List[Location]:
    sb = StatBlock()

    eldeth = NPC(
        name="Eldeth Merryweather",
        race=Race.Human,
        alignment=Alignment.Lawful_Good,
        stat_block=sb,
        appearance="Weathered captain with a sharp gaze and a sea-green coat.",
        backstory="Long-time captain of the Silver Gull, famed for fair prices and safe passage."
    )
    nox = NPC(
        name="Nox",
        race=Race.Bugbear,
        alignment=Alignment.Lawful_Neutral,
        stat_block=sb,
        appearance="Broad-shouldered bugbear first mate, keeps order with few words.",
        backstory="Swore loyalty to Eldeth after she saved his crew from pirates."
    )
    grimda = NPC(
        name="Grimda Stonecask",
        race=Race.Dwarf,
        alignment=Alignment.True_Neutral,
        stat_block=sb,
        appearance="Stout dwarf with ink-stained fingers and a ledger always in hand.",
        backstory="Quartermaster of Port Virellon’s warehouses; knows every crate by smell."
    )
    jessira = NPC(
        name="Jessira Thorne",
        race=Race.Tiefling,
        alignment=Alignment.Chaotic_Neutral,
        stat_block=sb,
        appearance="Red-skinned tiefling with a sly smile and a pocketful of keys.",
        backstory="Smuggler-turned-fixer; can procure a berth—or make one disappear."
    )

    # Top-level locations
    port_virellon = Location(
        name="Port Virellon",
        description="A rough but busy port ferrying commoners to the great city of Thalendir.",
        region="Coastal Lowlands",
        tags=["port", "urban", "seedy"],
        npcs=[grimda, jessira, eldeth, nox]
    )
    thalendir_gate = Location(
        name="Thalendir South Gate",
        description="Tall gates of green-black stone; city watch inspects every cart.",
        region="Thalendir",
        tags=["gate", "urban", "checkpoint"],
        npcs=[]
    )

    # Child location nested under Port Virellon (as requested)
    salty_hound = Location(
        name="The Salty Hound",
        description="A dockside tavern with creaky floors, strong ale, and stronger rumors.",
        region="Port Virellon Docks",
        tags=["tavern", "urban"],
        npcs=[jessira, grimda]
    )
    port_virellon.add_child(salty_hound)

    return [port_virellon, thalendir_gate]

# -----------------------
# Tree model utilities
# -----------------------
ROLE_LOCATION_PTR = QtCore.Qt.ItemDataRole.UserRole + 1

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

def filter_tree(model: QtGui.QStandardItemModel, text: str):
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
            child_match = apply(child)
            any_child_match = any_child_match or child_match
        visible = match_self or any_child_match
        item.setHidden(not visible)
        # Keep description column visibility aligned
        sibling_desc = item.siblingAtColumn(1)
        if sibling_desc.isValid():
            model.itemFromIndex(sibling_desc).setHidden(not visible)
        return visible

    # Apply to all top-level nodes
    for r in range(model.rowCount()):
        root_item = model.item(r, 0)
        apply(root_item)

# -----------------------
# Main Window
# -----------------------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, locations: List[Location]):
        super().__init__()
        self.setWindowTitle("DM Helper — Locations & NPCs")
        self.resize(1000, 640)
        self.locations = locations

        # Widgets
        self.search = QtWidgets.QLineEdit(placeholderText="Search locations…")
        self.location_tree = QtWidgets.QTreeView()
        self.location_tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.location_tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.location_tree.setAlternatingRowColors(True)
        self.location_tree.setUniformRowHeights(True)
        self.location_tree.setExpandsOnDoubleClick(True)

        self.npc_list = QtWidgets.QListWidget()

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
        filter_tree(self.model, text)
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
            # Hover tooltip for NPC
            tooltip = self._npc_tooltip(npc)
            item.setToolTip(tooltip)
            self.npc_list.addItem(item)

    def _npc_tooltip(self, npc: NPC) -> str:
        appearance = npc.appearance or ""
        if len(appearance) > 160:
            appearance = appearance[:160].rstrip() + "…"
        return (f"{npc.name}\n"
                f"Race: {npc.race.value}\n"
                f"Alignment: {npc.alignment.value}\n\n"
                f"{appearance}")

# -----------------------
# App entry
# -----------------------
def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow(seed_data())
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
