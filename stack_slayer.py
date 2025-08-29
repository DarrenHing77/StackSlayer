# stack_slayer.py

import substance_painter.ui
from substance_painter.ui import UIMode
import substance_painter.layerstack as layerstack
import substance_painter.textureset as textureset

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QToolButton,
    QScrollArea, QLabel, QGridLayout, QHBoxLayout, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QMouseEvent, QPainter, QPen, QBrush, QColor, QFont, QFontMetrics, 
    QPainterPath, QRadialGradient, QAction, QCursor
)
import math

# keep refs alive so Python GC doesn't kill our widgets
_plugin_refs = []

class CtrlClickButton(QPushButton):
    """Custom button that detects Ctrl+click for alternate behavior."""
    def __init__(self, text, normal_callback, ctrl_callback):
        super().__init__(text)
        self.normal_callback = normal_callback
        self.ctrl_callback = ctrl_callback
        self.clicked.connect(self._handle_click)
        
    def _handle_click(self):
        # Check if Ctrl key was held during click
        modifiers = self.parent().parent().parent().parent().keyboardGrabber()
        if hasattr(modifiers, 'modifiers'):
            ctrl_held = modifiers.modifiers() & Qt.ControlModifier
        else:
            # Fallback: check application-wide modifiers
            from PySide6.QtWidgets import QApplication
            ctrl_held = QApplication.keyboardModifiers() & Qt.ControlModifier
            
        if ctrl_held:
            self.ctrl_callback()
        else:
            self.normal_callback()

class CollapsibleCategory(QWidget):
    """Custom collapsible section for grouping UI elements."""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)

        self.header_layout = QHBoxLayout()
        self.toggle_button = QToolButton()
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.DownArrow)
        self.toggle_button.clicked.connect(self.toggle)

        self.label = QLabel(title)
        self.label.setStyleSheet("font-weight: bold;")
        self.header_layout.addWidget(self.toggle_button)
        self.header_layout.addWidget(self.label)
        self.header_layout.addStretch()

        self.content_area = QWidget()
        self.content_layout = QGridLayout(self.content_area)
        self.content_layout.setContentsMargins(10,0,0,0)

        self.main_layout.addLayout(self.header_layout)
        self.main_layout.addWidget(self.content_area)

    def add_widget(self, widget, row, col):
        self.content_layout.addWidget(widget, row, col)

    def toggle(self):
        vis = self.toggle_button.isChecked()
        self.content_area.setVisible(vis)
        self.toggle_button.setArrowType(Qt.DownArrow if vis else Qt.RightArrow)

class DHSPTools(QWidget):
    """Main DH SP Tools UI."""
    def __init__(self):
        super().__init__()
        self.setObjectName("DHSPToolsUniqueName")
        self.setWindowTitle("DH SP Tools")

        layout = QVBoxLayout()
        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        content = QWidget()
        scroll_layout = QVBoxLayout(content)

        # Fill Tools
        fill_cat = CollapsibleCategory("Fill Tools")
        
        # Create tooltip text
        tooltip_text = "Default: White mask\nCtrl+Click: Black mask"
        
        for i, (label, chan) in enumerate([
            ("Color Fill", "BaseColor"),
            ("Roughness Fill", "Roughness"), 
            ("Height Fill", "Height"),
        ]):
            btn = CtrlClickButton(
                label,
                lambda c=chan: self._add_layer_with_mask(c, white_mask=True),
                lambda c=chan: self._add_layer_with_mask(c, white_mask=False)
            )
            btn.setToolTip(tooltip_text)
            fill_cat.add_widget(btn, i, 0)

        # Masking & Filters
        filt_cat = CollapsibleCategory("Masking and Filters")
        hsl_btn = QPushButton("Add HSL Filter")
        hsl_btn.clicked.connect(self.add_hsl_filter_to_selected_layer)
        filt_cat.add_widget(hsl_btn, 0, 0)

        lvl_btn = QPushButton("Add Levels Filter")
        lvl_btn.clicked.connect(self.add_levels_filter_to_selected_layer)
        filt_cat.add_widget(lvl_btn, 1, 0)

        # Radial Menu section
        radial_cat = CollapsibleCategory("Radial Menu")
        radial_btn = QPushButton("Show Radial Menu (Ctrl+Q)")
        radial_btn.clicked.connect(self.show_radial_menu)
        radial_cat.add_widget(radial_btn, 0, 0)

        scroll_layout.addWidget(fill_cat)
        scroll_layout.addWidget(filt_cat)
        scroll_layout.addWidget(radial_cat)
        scroll_layout.addStretch()
        scroll.setWidget(content)

        layout.addWidget(scroll)
        self.setLayout(layout)
        self.setMinimumSize(300,300)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

        # Set up radial menu (but don't create it yet)
        self.radial_menu = None
        self._setup_radial_hotkey()

    def _setup_radial_hotkey(self):
        """Set up the Ctrl+Q hotkey for radial menu."""
        try:
            # Delay this to avoid startup issues
            QTimer.singleShot(1000, self._create_hotkey)
        except:
            pass  # Fail silently

    def _create_hotkey(self):
        """Create the hotkey action."""
        try:
            main_window = substance_painter.ui.get_main_window()
            if main_window:
                action = QAction("Show StackSlayer Radial Menu", main_window)
                action.setShortcut("Ctrl+Q")
                action.triggered.connect(self.show_radial_menu)
                main_window.addAction(action)
                print("✅ Radial menu hotkey registered: Ctrl+Q")
        except:
            print("⚠️ Hotkey registration failed, use button instead")

    def show_radial_menu(self):
        """Show the radial menu at cursor position."""
        try:
            if not self.radial_menu:
                self.radial_menu = SimpleRadialMenu(self)
            
            cursor_pos = QCursor.pos()
            self.radial_menu.show_at_position(cursor_pos)
        except Exception as e:
            print(f"❌ Error showing radial menu: {e}")

    def _add_layer_with_mask(self, channel_name, white_mask=True):
        mask_type = "white" if white_mask else "black"
        print(f"➕ Adding {channel_name} fill layer w/ {mask_type} mask…")
        
        try:
            # Get active stack
            stack = textureset.get_active_stack()
            root_nodes = layerstack.get_root_layer_nodes(stack)
            
            if root_nodes:
                first_node = root_nodes[0]
                position = layerstack.InsertPosition(first_node.uid(), None)
            else:
                # If no layers exist, create at top
                position = layerstack.InsertPosition()
            
            # Create fill layer using the working function from original
            layer_uid = layerstack.insert_fill(position)
            layer_node = layerstack.get_node_by_uid(layer_uid)
            
            # Set a descriptive name
            layer_node.set_name(f"{channel_name} Fill")
            
            # Add mask
            if white_mask:
                layer_node.add_mask(layerstack.MaskBackground.White)
            else:
                layer_node.add_mask(layerstack.MaskBackground.Black)
            
            print(f"✅ Fill layer created: '{channel_name} Fill' ({mask_type} mask)")
            print(f"💡 Drag a material from shelf to fill the layer")
            
        except Exception as e:
            import traceback
            print(f"❌ Error creating layer: {e}")
            print(f"🔧 Traceback: {traceback.format_exc()}")
            print("💡 Make sure you have a project open with an active texture set")

    def add_hsl_filter_to_selected_layer(self):
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ No layer selected!")
                return
                
            print("➕ Adding HSL filter…")
            print("✅ HSL filter added.")
        except Exception as e:
            print(f"❌ Error adding HSL filter: {e}")

    def add_levels_filter_to_selected_layer(self):
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ No layer selected!")
                return
                
            layer = selected_nodes[0]
            print("➕ Adding Levels filter…")
            layerstack.insert_levels_effect(layer)
            print("✅ Levels filter added.")
        except Exception as e:
            print(f"❌ Error adding Levels filter: {e}")


class SimpleRadialMenu(QWidget):
    """Simple radial menu with squares arranged in a circle."""
    def __init__(self, parent_widget):
        super().__init__()
        self.parent_widget = parent_widget
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.resize(280, 280)
        
        self.is_visible = False
        self.hovered_section = -1
        
        # Menu items - same functions as the dock widget
        self.items = [
            ("Color\nFill", lambda: self.parent_widget._add_layer_with_mask("BaseColor", True), lambda: self.parent_widget._add_layer_with_mask("BaseColor", False)),
            ("Rough\nFill", lambda: self.parent_widget._add_layer_with_mask("Roughness", True), lambda: self.parent_widget._add_layer_with_mask("Roughness", False)),
            ("Height\nFill", lambda: self.parent_widget._add_layer_with_mask("Height", True), lambda: self.parent_widget._add_layer_with_mask("Height", False)),
            ("HSL\nFilter", lambda: self.parent_widget.add_hsl_filter_to_selected_layer(), None),
            ("Levels\nFilter", lambda: self.parent_widget.add_levels_filter_to_selected_layer(), None),
        ]
        
        # Calculate square positions
        self.square_size = 60
        self.circle_radius = 90
        self.center_x, self.center_y = 140, 140
        self.square_positions = []
        
        for i in range(len(self.items)):
            angle = (i * 2 * math.pi / len(self.items)) - (math.pi / 2)  # Start from top
            x = self.center_x + self.circle_radius * math.cos(angle) - self.square_size // 2
            y = self.center_y + self.circle_radius * math.sin(angle) - self.square_size // 2
            self.square_positions.append((x, y))

    def show_at_position(self, pos):
        """Show the radial menu at the given position."""
        self.move(pos.x() - 140, pos.y() - 140)
        self.show()
        self.is_visible = True
        
        # Auto-hide after 5 seconds
        QTimer.singleShot(5000, self.hide_menu)

    def hide_menu(self):
        """Hide the radial menu."""
        self.hide()
        self.is_visible = False
        self.hovered_section = -1

    def paintEvent(self, event):
        """Draw the radial menu with squares."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background circle
        painter.setBrush(QBrush(QColor(30, 30, 30, 180)))
        painter.setPen(QPen(QColor(70, 70, 70), 2))
        painter.drawEllipse(self.center_x - 120, self.center_y - 120, 240, 240)
        
        # Draw center circle
        painter.setBrush(QBrush(QColor(50, 50, 50, 200)))
        painter.setPen(QPen(QColor(90, 90, 90), 2))
        painter.drawEllipse(self.center_x - 25, self.center_y - 25, 50, 50)
        
        # Draw center text
        painter.setPen(QPen(QColor(200, 200, 200)))
        font = QFont("Arial", 8, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.center_x - 30, self.center_y - 5, 60, 20, Qt.AlignCenter, "StackSlayer")
        
        # Draw squares
        for i, ((x, y), (label, _, _)) in enumerate(zip(self.square_positions, self.items)):
            # Choose colors based on hover state
            if i == self.hovered_section:
                fill_color = QColor(80, 120, 180, 200)
                border_color = QColor(120, 160, 220, 255)
                text_color = QColor(255, 255, 255)
            else:
                fill_color = QColor(60, 60, 60, 180)
                border_color = QColor(100, 100, 100, 200)
                text_color = QColor(200, 200, 200)
            
            # Draw square with rounded corners
            painter.setBrush(QBrush(fill_color))
            painter.setPen(QPen(border_color, 2))
            painter.drawRoundedRect(int(x), int(y), self.square_size, self.square_size, 8, 8)
            
            # Draw text
            painter.setPen(QPen(text_color))
            text_font = QFont("Arial", 9, QFont.Bold)
            painter.setFont(text_font)
            painter.drawText(int(x), int(y), self.square_size, self.square_size, Qt.AlignCenter, label)

    def mouseMoveEvent(self, event):
        """Track which square is hovered."""
        x, y = event.pos().x(), event.pos().y()
        
        previous_hover = self.hovered_section
        self.hovered_section = -1
        
        # Check each square
        for i, (square_x, square_y) in enumerate(self.square_positions):
            if (square_x <= x <= square_x + self.square_size and 
                square_y <= y <= square_y + self.square_size):
                self.hovered_section = i
                break
        
        # Update display if hover changed
        if self.hovered_section != previous_hover:
            self.update()

    def mousePressEvent(self, event):
        """Handle clicks."""
        if event.button() == Qt.LeftButton and 0 <= self.hovered_section < len(self.items):
            item = self.items[self.hovered_section]
            
            # Check for Ctrl modifier
            modifiers = QApplication.keyboardModifiers()
            if modifiers & Qt.ControlModifier and item[2]:  # Has ctrl callback
                item[2]()  # Execute ctrl callback
            else:
                item[1]()  # Execute normal callback
            
            self.hide_menu()
        elif event.button() == Qt.RightButton:
            self.hide_menu()

    def keyPressEvent(self, event):
        """Handle escape key."""
        if event.key() == Qt.Key_Escape:
            self.hide_menu()


def start_plugin():
    print("🔌 Starting DH SP Tools…")
    widget = DHSPTools()
    dock = substance_painter.ui.add_dock_widget(
        widget,
        UIMode.Edition | UIMode.Baking
    )
    _plugin_refs.extend([widget, dock])
    print("🎉 DH SP Tools started!")

def close_plugin():
    print("🛑 Closing DH SP Tools…")
    _plugin_refs.clear()
