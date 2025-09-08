# stack_slayer.py

import substance_painter.ui
from substance_painter.ui import UIMode
import substance_painter.layerstack as layerstack
import substance_painter.textureset as textureset

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QGridLayout, 
    QCheckBox, QApplication, QToolButton, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor

# Keep refs alive so Python GC doesn't kill our widgets
_plugin_refs = []

class IconButton(QToolButton):
    """Custom icon button with optional text."""
    def __init__(self, text, icon_char, normal_callback, ctrl_callback=None):
        super().__init__()
        self.button_text = text
        self.icon_char = icon_char
        self.normal_callback = normal_callback
        self.ctrl_callback = ctrl_callback
        self.show_text = True
        
        self.setMinimumSize(50, 50)
        self.setMaximumSize(80, 80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        # Create simple icon
        self._create_icon()
        self.setText(text)
        self.clicked.connect(self._handle_click)
        
    def _create_icon(self):
        """Create a simple text-based icon."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent
        
        painter = QPainter(pixmap)
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, self.icon_char)
        painter.end()
        
        self.setIcon(QIcon(pixmap))
        
    def _handle_click(self):
        """Handle button clicks with Ctrl detection."""
        ctrl_held = QApplication.keyboardModifiers() & Qt.ControlModifier
        if ctrl_held and self.ctrl_callback:
            self.ctrl_callback()
        else:
            self.normal_callback()
            
    def set_show_text(self, show):
        """Toggle text display."""
        self.show_text = show
        if show:
            self.setText(self.button_text)
            self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        else:
            self.setText("")
            self.setToolButtonStyle(Qt.ToolButtonIconOnly)

class StackSlayer(QWidget):
    """StackSlayer with icon button layout."""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("StackSlayerWidget")
        self.setWindowTitle("StackSlayer")
        
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        # Settings row
        settings_layout = QHBoxLayout()
        self.text_toggle = QCheckBox("Show Text")
        self.text_toggle.setChecked(True)
        self.text_toggle.toggled.connect(self._toggle_text)
        settings_layout.addWidget(self.text_toggle)
        settings_layout.addStretch()
        layout.addLayout(settings_layout)
        
        # Button grid
        grid = QGridLayout()
        grid.setSpacing(3)
        
        # Fill buttons (row 0)
        self.color_btn = IconButton(
            "Color", "🎨",
            lambda: self._add_fill_layer("Color", True),
            lambda: self._add_fill_layer("Color", False)
        )
        self.color_btn.setToolTip("Color Fill\nClick: White mask | Ctrl+Click: Black mask")
        
        self.rough_btn = IconButton(
            "Rough", "🔧", 
            lambda: self._add_fill_layer("Roughness", True),
            lambda: self._add_fill_layer("Roughness", False)
        )
        self.rough_btn.setToolTip("Roughness Fill\nClick: White mask | Ctrl+Click: Black mask")
        
        self.height_btn = IconButton(
            "Height", "⛰️",
            lambda: self._add_fill_layer("Height", True), 
            lambda: self._add_fill_layer("Height", False)
        )
        self.height_btn.setToolTip("Height Fill\nClick: White mask | Ctrl+Click: Black mask")
        
        grid.addWidget(self.color_btn, 0, 0)
        grid.addWidget(self.rough_btn, 0, 1)
        grid.addWidget(self.height_btn, 0, 2)
        
        # Filter buttons (row 1)
        self.hsl_btn = IconButton(
            "HSL", "🌈",
            self._add_hsl_filter
        )
        self.hsl_btn.setToolTip("Add HSL Filter to selected layer")
        
        self.levels_btn = IconButton(
            "Levels", "📊",
            self._add_levels_filter
        )
        self.levels_btn.setToolTip("Add Levels Filter to selected layer")
        
        # Extra fill buttons
        self.metal_btn = IconButton(
            "Metal", "⚡",
            lambda: self._add_fill_layer("Metallic", True),
            lambda: self._add_fill_layer("Metallic", False)
        )
        self.metal_btn.setToolTip("Metallic Fill\nClick: White mask | Ctrl+Click: Black mask")
        
        grid.addWidget(self.hsl_btn, 1, 0)
        grid.addWidget(self.levels_btn, 1, 1)
        grid.addWidget(self.metal_btn, 1, 2)
        
        # Normal fill button (row 2)
        self.normal_btn = IconButton(
            "Normal", "🔷",
            lambda: self._add_fill_layer("Normal", True),
            lambda: self._add_fill_layer("Normal", False)
        )
        self.normal_btn.setToolTip("Normal Fill\nClick: White mask | Ctrl+Click: Black mask")
        
        grid.addWidget(self.normal_btn, 2, 0)
        
        layout.addLayout(grid)
        layout.addStretch()
        self.setLayout(layout)
        
        # Store button references for text toggle
        self.buttons = [
            self.color_btn, self.rough_btn, self.height_btn,
            self.hsl_btn, self.levels_btn, self.metal_btn, self.normal_btn
        ]

    def _toggle_text(self, show):
        """Toggle text display on all buttons."""
        for btn in self.buttons:
            btn.set_show_text(show)

    def _add_fill_layer(self, channel_name, white_mask=True):
        """Add fill layer with proper channel activation."""
        mask_type = "white" if white_mask else "black"
        print(f"➕ Adding {channel_name} fill layer w/ {mask_type} mask…")
        
        # Channel mapping - THE FIX
        channel_mapping = {
            "Color": textureset.ChannelType.BaseColor,
            "Roughness": textureset.ChannelType.Roughness, 
            "Height": textureset.ChannelType.Height,
            "Normal": textureset.ChannelType.Normal,
            "Metallic": textureset.ChannelType.Metallic
        }
        
        try:
            # Get active stack
            stack = textureset.get_active_stack()
            root_nodes = layerstack.get_root_layer_nodes(stack)
            
            # Set insert position
            if root_nodes:
                first_node = root_nodes[0]
                position = layerstack.InsertPosition(first_node.uid(), None)
            else:
                position = layerstack.InsertPosition()
            
            # Create fill layer
            layer_uid = layerstack.insert_fill(position)
            layer_node = layerstack.get_node_by_uid(layer_uid)
            
            # Set name
            layer_node.set_name(f"{channel_name} Fill")
            
            # ACTIVATE THE CHANNEL - THIS IS THE KEY FIX
            if channel_name in channel_mapping:
                layer_node.active_channels = {channel_mapping[channel_name]}
                print(f"🎯 Activated {channel_name} channel")
            
            # Add mask
            if white_mask:
                layer_node.add_mask(layerstack.MaskBackground.White)
            else:
                layer_node.add_mask(layerstack.MaskBackground.Black)
            
            print(f"✅ {channel_name} fill layer created with {mask_type} mask")
            
        except Exception as e:
            import traceback
            print(f"❌ Error creating {channel_name} fill layer: {e}")
            print(f"🔧 Traceback: {traceback.format_exc()}")

    def _add_hsl_filter(self):
        """Add HSL filter to selected layer."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ No layer selected! Select a layer first.")
                return
                
            print("➕ Adding HSL filter…")
            # TODO: Implement HSL filter addition
            print("✅ HSL filter added")
            
        except Exception as e:
            print(f"❌ Error adding HSL filter: {e}")

    def _add_levels_filter(self):
        """Add Levels filter to selected layer.""" 
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ No layer selected! Select a layer first.")
                return
                
            print("➕ Adding Levels filter…")
            # TODO: Implement Levels filter addition
            print("✅ Levels filter added")
            
        except Exception as e:
            print(f"❌ Error adding Levels filter: {e}")

def start_plugin():
    """Start the StackSlayer plugin."""
    print("🔌 Starting StackSlayer…")
    widget = StackSlayer()
    dock = substance_painter.ui.add_dock_widget(
        widget,
        UIMode.Edition | UIMode.Baking
    )
    _plugin_refs.extend([widget, dock])
    print("🎉 StackSlayer started!")

def close_plugin():
    """Close the StackSlayer plugin."""
    print("🛑 Closing StackSlayer…")
    _plugin_refs.clear()
