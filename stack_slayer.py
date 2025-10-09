# stack_slayer.py

import substance_painter.ui
from substance_painter.ui import UIMode
import substance_painter.layerstack as layerstack
import substance_painter.textureset as textureset
import substance_painter.resource as resource

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QGridLayout, 
    QCheckBox, QApplication, QToolButton, QSizePolicy, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor

# Keep refs alive so Python GC doesn't kill our widgets
_plugin_refs = []

class IconButton(QToolButton):
    """Custom icon button with optional text and modifier key support."""
    def __init__(self, text, icon_char, normal_callback, ctrl_callback=None, shift_callback=None):
        super().__init__()
        self.button_text = text
        self.icon_char = icon_char
        self.normal_callback = normal_callback
        self.ctrl_callback = ctrl_callback
        self.shift_callback = shift_callback
        self.show_text = True
        
        self.setMinimumSize(50, 50)
        self.setMaximumSize(80, 80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        self._create_icon()
        self.setText(text)
        self.clicked.connect(self._handle_click)
        
    def _create_icon(self):
        """Create a simple text-based icon."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))
        
        painter = QPainter(pixmap)
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, self.icon_char)
        painter.end()
        
        self.setIcon(QIcon(pixmap))
        
    def _handle_click(self):
        """Handle button clicks with Ctrl/Shift detection."""
        modifiers = QApplication.keyboardModifiers()
        
        # Check Ctrl first, then Shift, then default
        if modifiers & Qt.ControlModifier and self.ctrl_callback:
            self.ctrl_callback()
        elif modifiers & Qt.ShiftModifier and self.shift_callback:
            self.shift_callback()
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
    """StackSlayer with categorized layout."""
    
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
        
        # === FILL LAYERS SECTION ===
        fill_label = QLabel("Fill Layers")
        fill_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        layout.addWidget(fill_label)
        
        fill_grid = QGridLayout()
        fill_grid.setSpacing(3)
        
        # Row 0: Color, Rough, Height
        self.color_btn = IconButton(
            "Color", "🎨",
            lambda: self._add_fill_layer("Color", None),
            lambda: self._add_fill_layer("Color", False),
            lambda: self._add_fill_layer("Color", True)
        )
        self.color_btn.setToolTip("Color Fill\nClick: No mask | Ctrl: Black mask | Shift: White mask")
        
        self.rough_btn = IconButton(
            "Rough", "🔧", 
            lambda: self._add_fill_layer("Roughness", None),
            lambda: self._add_fill_layer("Roughness", False),
            lambda: self._add_fill_layer("Roughness", True)
        )
        self.rough_btn.setToolTip("Roughness Fill\nClick: No mask | Ctrl: Black mask | Shift: White mask")
        
        self.height_btn = IconButton(
            "Height", "⛰️",
            lambda: self._add_fill_layer("Height", None),
            lambda: self._add_fill_layer("Height", False),
            lambda: self._add_fill_layer("Height", True)
        )
        self.height_btn.setToolTip("Height Fill\nClick: No mask | Ctrl: Black mask | Shift: White mask")
        
        fill_grid.addWidget(self.color_btn, 0, 0)
        fill_grid.addWidget(self.rough_btn, 0, 1)
        fill_grid.addWidget(self.height_btn, 0, 2)
        
        # Row 1: Metal, Normal
        self.metal_btn = IconButton(
            "Metal", "⚡",
            lambda: self._add_fill_layer("Metallic", None),
            lambda: self._add_fill_layer("Metallic", False),
            lambda: self._add_fill_layer("Metallic", True)
        )
        self.metal_btn.setToolTip("Metallic Fill\nClick: No mask | Ctrl: Black mask | Shift: White mask")
        
        self.normal_btn = IconButton(
            "Normal", "🔷",
            lambda: self._add_fill_layer("Normal", None),
            lambda: self._add_fill_layer("Normal", False),
            lambda: self._add_fill_layer("Normal", True)
        )
        self.normal_btn.setToolTip("Normal Fill\nClick: No mask | Ctrl: Black mask | Shift: White mask")
        
        fill_grid.addWidget(self.metal_btn, 1, 0)
        fill_grid.addWidget(self.normal_btn, 1, 1)
        
        layout.addLayout(fill_grid)
        
        # === EFFECTS SECTION ===
        effects_label = QLabel("Effects (select layer first)")
        effects_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(effects_label)
        
        effects_grid = QGridLayout()
        effects_grid.setSpacing(3)
        
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
        
        self.blur_btn = IconButton(
            "Blur", "💫",
            self._add_blur_filter
        )
        self.blur_btn.setToolTip("Add Blur Filter to selected layer")
        
        effects_grid.addWidget(self.hsl_btn, 0, 0)
        effects_grid.addWidget(self.levels_btn, 0, 1)
        effects_grid.addWidget(self.blur_btn, 0, 2)
        
        layout.addLayout(effects_grid)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Store button references for text toggle
        self.buttons = [
            self.color_btn, self.rough_btn, self.height_btn,
            self.metal_btn, self.normal_btn,
            self.hsl_btn, self.levels_btn, self.blur_btn
        ]

    def _toggle_text(self, show):
        """Toggle text display on all buttons."""
        for btn in self.buttons:
            btn.set_show_text(show)

    def _add_fill_layer(self, channel_name, mask_type=None):
        """
        Add fill layer with proper channel activation.
        
        Args:
            channel_name: The channel to activate
            mask_type: None (no mask), True (white mask), False (black mask)
        """
        mask_desc = "no mask" if mask_type is None else ("white mask" if mask_type else "black mask")
        print(f"➕ Adding {channel_name} fill layer w/ {mask_desc}…")
        
        # Channel mapping
        channel_mapping = {
            "Color": textureset.ChannelType.BaseColor,
            "Roughness": textureset.ChannelType.Roughness, 
            "Height": textureset.ChannelType.Height,
            "Normal": textureset.ChannelType.Normal,
            "Metallic": textureset.ChannelType.Metallic
        }
        
        try:
            # Get active stack and insert position at top
            stack = textureset.get_active_stack()
            position = layerstack.InsertPosition.from_textureset_stack(stack)
            
            # Create fill layer (returns node directly)
            layer_node = layerstack.insert_fill(position)
            
            # Set name
            layer_node.set_name(f"{channel_name} Fill")
            
            # ACTIVATE CHANNEL
            if channel_name in channel_mapping:
                layer_node.active_channels = {channel_mapping[channel_name]}
                print(f"🎯 Activated {channel_name} channel")
            
            # SET DEFAULT WHITE COLOR
            import substance_painter.colormanagement as colormanagement
            white = colormanagement.Color(1.0, 1.0, 1.0)
            if channel_name in channel_mapping:
                layer_node.set_source(channel_mapping[channel_name], white)
                print(f"🎨 Set white color")
            
            # ADD MASK
            if mask_type is not None:
                if mask_type:
                    layer_node.add_mask(layerstack.MaskBackground.White)
                    print(f"🎭 Added white mask")
                else:
                    layer_node.add_mask(layerstack.MaskBackground.Black)
                    print(f"🎭 Added black mask")
            
            print(f"✅ {channel_name} fill layer created")
            
        except Exception as e:
            import traceback
            print(f"❌ Error creating {channel_name} fill layer: {e}")
            print(f"🔧 Traceback: {traceback.format_exc()}")

    def _add_hsl_filter(self):
        """Add HSL filter to selected layer's content stack."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ No layer selected! Select a layer first.")
                return
            
            selected_layer = selected_nodes[0]
            print(f"➕ Adding HSL filter to {selected_layer.get_name()}…")
            
            # Find HSL filter resource
            hsl_resources = resource.search("u:filter n:hsl")
            if not hsl_resources:
                print("❌ HSL filter not found in resources")
                return
            
            # Insert into content stack
            position = layerstack.InsertPosition.inside_node(selected_layer, layerstack.NodeStack.Content)
            filter_node = layerstack.insert_filter_effect(position, hsl_resources[0].identifier())
            
            # Match channels to parent layer
            if hasattr(selected_layer, 'active_channels'):
                filter_node.active_channels = selected_layer.active_channels
                print(f"🎯 Matched channels: {filter_node.active_channels}")
            
            print("✅ HSL filter added")
            
        except Exception as e:
            import traceback
            print(f"❌ Error adding HSL filter: {e}")
            print(f"🔧 Traceback: {traceback.format_exc()}")

    def _add_levels_filter(self):
        """Add Levels effect to selected layer's content stack."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ No layer selected! Select a layer first.")
                return
            
            selected_layer = selected_nodes[0]
            print(f"➕ Adding Levels filter to {selected_layer.get_name()}…")
            
            # Insert levels effect
            position = layerstack.InsertPosition.inside_node(selected_layer, layerstack.NodeStack.Content)
            levels_node = layerstack.insert_levels_effect(position)
            
            # Set affected channel to match first active channel of parent
            if hasattr(selected_layer, 'active_channels') and selected_layer.active_channels:
                first_channel = list(selected_layer.active_channels)[0]
                levels_node.affected_channel = first_channel
                print(f"🎯 Set affected channel: {first_channel}")
            
            print("✅ Levels effect added")
            
        except Exception as e:
            import traceback
            print(f"❌ Error adding Levels filter: {e}")
            print(f"🔧 Traceback: {traceback.format_exc()}")

    def _add_blur_filter(self):
        """Add Blur filter to selected layer's content stack."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ No layer selected! Select a layer first.")
                return
            
            selected_layer = selected_nodes[0]
            print(f"➕ Adding Blur filter to {selected_layer.get_name()}…")
            
            # Find Blur filter - try different search patterns
            blur_resources = resource.search("u:filter n:blur")
            if not blur_resources:
                # Try with equals sign for exact match
                blur_resources = resource.search('s:starterassets u:filter n:Blur=')
            
            if not blur_resources:
                print("❌ Blur filter not found in resources")
                return
            
            # Insert into content stack
            position = layerstack.InsertPosition.inside_node(selected_layer, layerstack.NodeStack.Content)
            filter_node = layerstack.insert_filter_effect(position, blur_resources[0].identifier())
            
            # Match channels to parent layer
            if hasattr(selected_layer, 'active_channels'):
                filter_node.active_channels = selected_layer.active_channels
                print(f"🎯 Matched channels: {filter_node.active_channels}")
            
            print("✅ Blur filter added")
            
        except Exception as e:
            import traceback
            print(f"❌ Error adding Blur filter: {e}")
            print(f"🔧 Traceback: {traceback.format_exc()}")

def start_plugin():
    """Initialize and show the plugin."""
    global _plugin_refs
    
    # Create widget
    widget = StackSlayer()
    
    # Dock it
    substance_painter.ui.add_dock_widget(widget, UIMode.Edition)
    
    # Keep reference
    _plugin_refs.append(widget)
    
    print("🚀 StackSlayer loaded")

def close_plugin():
    """Clean up when plugin is closed."""
    global _plugin_refs
    
    for widget in _plugin_refs:
        substance_painter.ui.delete_ui_element(widget)
    
    _plugin_refs.clear()
    print("👋 StackSlayer unloaded")

if __name__ == "__main__":
    start_plugin()
