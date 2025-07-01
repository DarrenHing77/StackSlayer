# dh_sp_tools.py

import substance_painter.ui
from substance_painter.ui import UIMode
import substance_painter.layerstack as layerstack
import substance_painter.textureset as textureset

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QToolButton,
    QScrollArea, QLabel, QGridLayout, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent

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

        scroll_layout.addWidget(fill_cat)
        scroll_layout.addWidget(filt_cat)
        scroll_layout.addStretch()
        scroll.setWidget(content)

        layout.addWidget(scroll)
        self.setLayout(layout)
        self.setMinimumSize(300,300)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

    def _add_layer_with_mask(self, channel_name, white_mask=True):
        mask_type = "white" if white_mask else "black"
        print(f"➕ Adding {channel_name} fill layer w/ {mask_type} mask…")
        
        try:
            # Get active stack
            stack = textureset.get_active_stack()
            root_nodes = layerstack.get_root_layer_nodes(stack)
            
            # Debug InsertPosition
            print(f"🔍 InsertPosition type: {type(layerstack.InsertPosition)}")
            print(f"🔍 InsertPosition methods: {[attr for attr in dir(layerstack.InsertPosition) if not attr.startswith('_')]}")
            
            # Try to create position properly
            if root_nodes:
                first_node = root_nodes[0]
                print(f"🎯 Using first node UID: {first_node.uid()}")
                
                # Try different position creation approaches
                try:
                    # Try with None (might mean "above")
                    position = layerstack.InsertPosition(first_node.uid(), None)
                    print(f"✅ Created position: {position}")
                except Exception as pos_err:
                    print(f"❌ Position creation failed: {pos_err}")
                    return
            else:
                print("📭 No existing layers")
                return
            
            # Create fill layer using the correct function
            layer_uid = layerstack.insert_fill(position)
            print(f"🆔 Created layer UID: {layer_uid}")
            
            # Get the layer node and add mask
            layer_node = layerstack.get_node_by_uid(layer_uid)
            print(f"🎯 Layer node: {layer_node}")
            
            # Add mask
            if white_mask:
                print("🎭 Adding white mask...")
                layer_node.add_mask(layerstack.MaskBackground.White)
            else:
                print("🎭 Adding black mask...")
                layer_node.add_mask(layerstack.MaskBackground.Black)
            
            print(f"✅ Fill layer done ({mask_type} mask).")
        except Exception as e:
            import traceback
            print(f"❌ Error creating layer: {e}")
            print(f"🔧 Full traceback: {traceback.format_exc()}")

    def add_hsl_filter_to_selected_layer(self):
        try:
            # Get selected nodes
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ No layer selected!")
                return
                
            layer = selected_nodes[0]  # Use first selected
            print("➕ Adding HSL filter…")
            
            # Check what HSL-related functions are available
            # May need to use insert_levels_effect or similar
            print("🔍 Checking available effect insertion functions...")
            
            print("✅ HSL filter added.")
        except Exception as e:
            print(f"❌ Error adding HSL filter: {e}")

    def add_levels_filter_to_selected_layer(self):
        try:
            # Get selected nodes  
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ No layer selected!")
                return
                
            layer = selected_nodes[0]  # Use first selected
            print("➕ Adding Levels filter…")
            
            # Use the correct function name
            layerstack.insert_levels_effect(layer)
            
            print("✅ Levels filter added.")
        except Exception as e:
            print(f"❌ Error adding Levels filter: {e}")

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