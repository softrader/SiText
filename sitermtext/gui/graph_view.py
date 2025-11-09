"""Graph view dialog showing wiki-links between notes as a simple network.

Nodes are markdown files; edges are [[wiki-links]]. Uses a circular layout for clarity.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPen, QPainter
from PyQt6.QtWidgets import (
    QDialog,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from sitermtext.utils.markdown_parser import extract_wikilinks, normalize_filename


class ClickableNode(QGraphicsEllipseItem):
    """Ellipse item representing a note node that emits activation via the view."""

    def __init__(self, center: QPointF, radius: float, label: str, file_path: Path,
                 angle_rad: float | None = None, show_label: bool = True):
        super().__init__(0, 0, radius * 2, radius * 2)
        self.setPos(center - QPointF(radius, radius))
        self.setBrush(QBrush(QColor("#2b2b2b")))
        self.setPen(QPen(QColor("#7f7f7f"), 1.0))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setToolTip(file_path.name)
        self.label_item = QGraphicsTextItem(label)
        font = QFont()
        font.setPointSize(9)
        self.label_item.setFont(font)
        # Place label radially outward if angle provided; else below
        if angle_rad is not None:
            # radial offset outward from the node
            out_dist = radius + 10
            lx = center.x() + out_dist * float(__import__("math").cos(angle_rad))
            ly = center.y() + out_dist * float(__import__("math").sin(angle_rad))
            # Slight additional offset to avoid overlap with edge of node
            label_rect = self.label_item.boundingRect()
            # Align label to left/right depending on hemisphere
            if __import__("math").cos(angle_rad) >= 0:
                # right side -> anchor left
                self.label_item.setPos(lx + 4, ly - label_rect.height() / 2)
            else:
                # left side -> anchor right
                self.label_item.setPos(lx - label_rect.width() - 4, ly - label_rect.height() / 2)
        else:
            label_rect = self.label_item.boundingRect()
            self.label_item.setPos(center.x() - label_rect.width() / 2, center.y() + radius + 4)
        self.label_item.setVisible(show_label)
        self.file_path = file_path

    def add_to_scene(self, scene: QGraphicsScene):
        scene.addItem(self)
        scene.addItem(self.label_item)


class GraphView(QGraphicsView):
    node_activated = pyqtSignal(Path)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event):
        # Zoom in/out
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            factor = zoom_in_factor
        else:
            factor = zoom_out_factor
        self.scale(factor, factor)

    def mouseDoubleClickEvent(self, event):
        # Activate node on double-click
        item = self.itemAt(event.pos())
        if isinstance(item, ClickableNode):
            self.node_activated.emit(item.file_path)
            event.accept()
            return
        # If label clicked
        if isinstance(item, QGraphicsTextItem):
            # try to find corresponding node by proximity
            pos = self.mapToScene(event.pos())
            items = self.scene().items(pos)
            for it in items:
                if isinstance(it, ClickableNode):
                    self.node_activated.emit(it.file_path)
                    event.accept()
                    return
        super().mouseDoubleClickEvent(event)


class GraphViewDialog(QDialog):
    """Dialog that renders a graph of notes and wiki-links."""

    def __init__(self, notes_directory: Path, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Notes Graph")
        self.setModal(False)
        self.resize(900, 700)

        self._notes_directory = notes_directory

        # UI
        root = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.build_graph)
        toolbar.addWidget(self.refresh_btn)
        self.toggle_labels_btn = QPushButton("Hide Labels")
        self.toggle_labels_btn.clicked.connect(self._toggle_labels)
        toolbar.addWidget(self.toggle_labels_btn)
        toolbar.addStretch()
        root.addLayout(toolbar)

        self.scene = QGraphicsScene(self)
        self.view = GraphView(self)
        self.view.setScene(self.scene)
        root.addWidget(self.view, stretch=1)

        # Keep data for refresh
        self._nodes: Dict[str, Path] = {}
        self._edges: Set[Tuple[str, str]] = set()

        # State
        self._labels_visible: bool = True
        self._node_items: List[ClickableNode] = []

        # Initial build
        self.build_graph()

    def set_notes_directory(self, directory: Path):
        self._notes_directory = directory
        self.build_graph()

    def build_graph(self):
        """Scan markdown files and build a multi-ring circular graph layout."""
        self.scene.clear()
        self._nodes.clear()
        self._edges.clear()
        self._node_items.clear()

        if not self._notes_directory.exists():
            return

        files = list(self._notes_directory.glob("**/*.md"))
        files.sort(key=lambda p: p.relative_to(self._notes_directory).as_posix().lower())

        # Map normalized name -> Path (use full relative path for uniqueness)
        for f in files:
            # Use relative path without .md as key for display and matching
            rel_path = f.relative_to(self._notes_directory)
            key = str(rel_path)[:-3] if str(rel_path).endswith('.md') else str(rel_path)
            self._nodes[normalize_filename(key)] = f

        # Build edges by parsing wiki-links
        for src in files:
            try:
                content = src.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            links = extract_wikilinks(content)
            # Use relative path as key for source
            src_rel = src.relative_to(self._notes_directory)
            src_key = normalize_filename(str(src_rel)[:-3] if str(src_rel).endswith('.md') else str(src_rel))

            for link in links:
                # Normalize the link (could be "foo" or "folder/foo")
                tgt_key = normalize_filename(link)
                if tgt_key == src_key:
                    continue
                # Create edge even if target missing (dangling reference)
                self._edges.add((src_key, tgt_key))
                # Ensure node exists for dangling target (virtual node)
                if tgt_key not in self._nodes:
                    # Use a synthetic Path for display; clicking will create/open
                    filename = link if link.endswith(".md") else f"{link}.md"
                    self._nodes[tgt_key] = self._notes_directory / filename

        # Layout nodes on concentric circles depending on count
        n = len(self._nodes)
        if n == 0:
            return
        import math
        center = QPointF(0, 0)
        base_radius = 180.0
        ring_gap = 120.0
        node_radius = 6.0
        min_arc = (node_radius * 2) + 16.0  # minimum arc length per node

        keys = sorted(self._nodes.keys())
        positions: Dict[str, QPointF] = {}
        angles: Dict[str, float] = {}

        idx = 0
        ring_index = 0
        while idx < n:
            R = base_radius + ring_index * ring_gap
            circumference = 2 * math.pi * R
            capacity = max(8, int(circumference / min_arc))
            end = min(n, idx + capacity)
            chunk = keys[idx:end]
            m = len(chunk)
            if m == 0:
                break
            for j, key in enumerate(chunk):
                angle_rad = (2 * math.pi) * (j / m)
                x = center.x() + R * math.cos(angle_rad)
                y = center.y() + R * math.sin(angle_rad)
                positions[key] = QPointF(x, y)
                angles[key] = angle_rad
            idx = end
            ring_index += 1

        # Draw edges first (lines)
        pen_edge = QPen(QColor("#555555"))
        pen_edge.setWidthF(1.0)
        for (src_key, tgt_key) in self._edges:
            p1 = positions.get(src_key)
            p2 = positions.get(tgt_key)
            if p1 is None or p2 is None:
                continue
            self.scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), pen_edge)

        # Draw nodes
        # Decide label visibility based on count; very large graphs hide labels
        show_labels = self._labels_visible and (n <= 80)
        for key, path in self._nodes.items():
            pos = positions[key]
            angle_rad = angles.get(key)
            node = ClickableNode(pos, node_radius, path.stem, path, angle_rad=angle_rad,
                                 show_label=show_labels)
            node.add_to_scene(self.scene)
            self._node_items.append(node)

        # Fit view
        self.view.setSceneRect(self.scene.itemsBoundingRect().adjusted(-40, -40, 40, 40))
        self.view.fitInView(self.view.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    # Expose node activation signal
    @property
    def node_activated(self):
        return self.view.node_activated

    def _toggle_labels(self):
        # Toggle label visibility and update button label
        self._labels_visible = not self._labels_visible
        new_state = self._labels_visible
        self.toggle_labels_btn.setText("Hide Labels" if new_state else "Show Labels")
        for node in self._node_items:
            # If graph too large, keep labels hidden regardless
            node.label_item.setVisible(new_state and len(self._node_items) <= 80)
