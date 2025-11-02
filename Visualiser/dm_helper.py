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

from knowledge_base import KBEntry, KnowledgeBase
from repo import Repo

from location import Location
from npc import NPC
from race import Race
from alignment import Alignment
from stat_block import StatBlock  # placeholder
from pc_classes import PcClass
from stat_block import MonMan
from spell import Spell
from item import Item
from class_action import ClassAction

# -----------------------
# Tree model utilities
# -----------------------
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

class NPCDetailWindow(QtWidgets.QMainWindow):
    def __init__(self, npc: NPC, kb: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.npc = npc
        self.kb = kb
        self.setWindowTitle(f"NPC — {npc.name}")
        self.resize(520, 520)

        # Use a scroll area in case backstory is long
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)

        content = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        # Helper to make selectable, wrapped labels
        def label(text: str) -> QtWidgets.QLabel:
            lab = QtWidgets.QLabel(text)
            lab.setWordWrap(True)
            lab.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextSelectableByMouse |
                QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse
            )
            return lab

        form.addRow("Name:", label(npc.name))
        form.addRow("Race:", label(npc.race.value))
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

        # Buttons (Close only)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
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

class StatBlockWindow(QtWidgets.QMainWindow):
    def __init__(self, sb: StatBlock, kb: KnowledgeBase, traits: list | None = None, parent=None):
        super().__init__(parent)
        self.sb = sb
        self.kb = kb
        self.traits = traits if traits is not None else []

        # self.kb = KnowledgeBase()  

        # self.kb.add("spell", "FireBall",
        #             "A bright streak flashes to a point you choose then blossoms with a low roar into an explosion of flame (8d6 fire in a 20-ft radius, DEX save for half).")
        # self.kb.add("ability", "Fuel The Fire",
        #             "When an ally casts a fire spell within 5 m, you can ignite latent embers to empower the next fire effect you cast.")
        
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
            vbox.addWidget(label(f"Class: {getattr(name, 'value', str(name) or 'Unknown')}"))
            vbox.addWidget(label(f"Level: {level if level is not None else 'Unknown'}"))

        elif isinstance(sb, MonMan):
            vbox.addWidget(label("Monster Manual Entry", bold=True))

            # Try to load the PNG page
            path = getattr(sb, "image_path", None)
            name = getattr(sb, "monster_name", "Unknown")
            vbox.addWidget(label(f"Name: {name}"))

            img_label = QtWidgets.QLabel()
            img_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
            if path:
                pix = QtGui.QPixmap(str(path))
                if not pix.isNull():
                    # scale-to-fit width while keeping aspect
                    img_label.setPixmap(pix)
                    # We'll scale after widget shows (see resizeEvent override below)
                    self._image_label = img_label
                    self._image_pixmap = pix
                else:
                    img_label.setText(f"(Image not found or failed to load)\n{path}")
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
        self._hover.show_text(entry.description, pos)

    def _on_anchor_clicked(self, url: QtCore.QUrl):
        name = url.toString()
        entry = self.kb.resolve(name)
        if not entry:
            return
        dlg = EntryDetailDialog(entry, self)
        dlg.exec()

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

class EntryDetailDialog(QtWidgets.QDialog):
    """Click-through dialog with full description."""
    def __init__(self, entry: KBEntry, parent=None):
        super().__init__(parent)
        self.setWindowTitle(entry.name)
        self.resize(420, 320)
        title = QtWidgets.QLabel(f"{entry.kind.title()}: {entry.name}")
        f = title.font(); f.setBold(True); title.setFont(f)
        body = QtWidgets.QLabel(entry.description)
        body.setWordWrap(True)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.reject)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(body)
        layout.addWidget(btns)


# -----------------------
# App entry
# -----------------------
def main():
    import sys

    repo = Repo()
    repo.load_all()

    kb = KnowledgeBase()
    kb.ingest(repo.spells, repo.items, repo.class_actions)
    kb.ingest_npcs(repo.npcs_by_id.values())

    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow(repo.locations, kb)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
