# stack_slayer.py

import substance_painter.ui
from substance_painter.ui import UIMode
import substance_painter.layerstack as layerstack
import substance_painter.textureset as textureset
import substance_painter.resource as resource

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QGridLayout, 
    QCheckBox, QApplication, QLabel
)
from PySide6.QtCore import Qt

# Keep refs alive so Python GC doesn't kill our widgets
_plugin_refs = []

class ModifierButton(QPushButton):
    """Button that supports Ctrl/Shift modifiers."""
    def __init__(self, text, normal_callback, ctrl_callback=None, shift_callback=None):
        super().__init__(text)
        self.normal_callback = normal_callback
        self.ctrl_callback = ctrl_callback
        self.shift_callback = shift_callback
        self.clicked.connect(self._handle_click)
        
    def _handle_click(self):
        """Handle button clicks with Ctrl/Shift detection."""
        modifiers = QApplication.keyboardModifiers()
        
        if modifiers & Qt.ControlModifier and self.ctrl_callback:
            self.ctrl_callback()
        elif modifiers & Qt.ShiftModifier and self.shift_callback:
            self.shift_callback()
        else:
            self.normal_callback()

class StackSlayer(QWidget):
    """StackSlayer - Fast layer workflow tools."""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("StackSlayerWidget")
        self.setWindowTitle("StackSlayer")
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # === FILL LAYERS SECTION ===
        fill_label = QLabel("Fill Layers")
        fill_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        layout.addWidget(fill_label)
        
        fill_grid = QGridLayout()
        fill_grid.setSpacing(3)
        
        # Row 0
        self.color_btn = ModifierButton(
            "Color",
            lambda: self._add_fill_layer("Color", None),
            lambda: self._add_fill_layer("Color", False),
            lambda: self._add_fill_layer("Color", True)
        )
        self.color_btn.setToolTip("Click: No mask | Ctrl: Black mask | Shift: White mask")
        
        self.rough_btn = ModifierButton(
            "Roughness", 
            lambda: self._add_fill_layer("Roughness", None),
            lambda: self._add_fill_layer("Roughness", False),
            lambda: self._add_fill_layer("Roughness", True)
        )
        self.rough_btn.setToolTip("Click: No mask | Ctrl: Black mask | Shift: White mask")
        
        self.height_btn = ModifierButton(
            "Height",
            lambda: self._add_fill_layer("Height", None),
            lambda: self._add_fill_layer("Height", False),
            lambda: self._add_fill_layer("Height", True)
        )
        self.height_btn.setToolTip("Click: No mask | Ctrl: Black mask | Shift: White mask")
        
        fill_grid.addWidget(self.color_btn, 0, 0)
        fill_grid.addWidget(self.rough_btn, 0, 1)
        fill_grid.addWidget(self.height_btn, 0, 2)
        
        # Row 1
        self.metal_btn = ModifierButton(
            "Metallic",
            lambda: self._add_fill_layer("Metallic", None),
            lambda: self._add_fill_layer("Metallic", False),
            lambda: self._add_fill_layer("Metallic", True)
        )
        self.metal_btn.setToolTip("Click: No mask | Ctrl: Black mask | Shift: White mask")
        
        self.normal_btn = ModifierButton(
            "Normal",
            lambda: self._add_fill_layer("Normal", None),
            lambda: self._add_fill_layer("Normal", False),
            lambda: self._add_fill_layer("Normal", True)
        )
        self.normal_btn.setToolTip("Click: No mask | Ctrl: Black mask | Shift: White mask")
        
        fill_grid.addWidget(self.metal_btn, 1, 0)
        fill_grid.addWidget(self.normal_btn, 1, 1)
        
        layout.addLayout(fill_grid)
        
        # === EFFECTS SECTION ===
        effects_label = QLabel("Effects")
        effects_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(effects_label)
        
        effects_grid = QGridLayout()
        effects_grid.setSpacing(3)
        
        self.hsl_btn = QPushButton("HSL")
        self.hsl_btn.setToolTip("Add HSL Filter to selected layer")
        self.hsl_btn.clicked.connect(self._add_hsl_filter)
        
        self.levels_btn = QPushButton("Levels")
        self.levels_btn.setToolTip("Add Levels Filter to selected layer")
        self.levels_btn.clicked.connect(self._add_levels_filter)
        
        self.blur_btn = QPushButton("Blur")
        self.blur_btn.setToolTip("Add Blur Filter to selected layer")
        self.blur_btn.clicked.connect(self._add_blur_filter)
        
        effects_grid.addWidget(self.hsl_btn, 0, 0)
        effects_grid.addWidget(self.levels_btn, 0, 1)
        effects_grid.addWidget(self.blur_btn, 0, 2)
        
        layout.addLayout(effects_grid)
        
        # === LAYER OPERATIONS SECTION ===
        ops_label = QLabel("Layer Operations")
        ops_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(ops_label)
        
        ops_grid = QGridLayout()
        ops_grid.setSpacing(3)
        
        # Row 0: Generator, Fill, Paint
        self.gen_btn = ModifierButton(
            "Generator",
            lambda: self._add_generator(None),      # Auto-detect
            lambda: self._add_generator("content"),  # Ctrl = content
            lambda: self._add_generator("mask")      # Shift = mask
        )
        self.gen_btn.setToolTip("Add Generator\nClick: Auto | Ctrl: Content | Shift: Mask")
        
        self.fill_effect_btn = ModifierButton(
            "Fill",
            lambda: self._add_fill_effect(None),
            lambda: self._add_fill_effect("content"),
            lambda: self._add_fill_effect("mask")
        )
        self.fill_effect_btn.setToolTip("Add Fill\nClick: Auto | Ctrl: Content | Shift: Mask")
        
        self.paint_effect_btn = ModifierButton(
            "Paint",
            lambda: self._add_paint_effect(None),
            lambda: self._add_paint_effect("content"),
            lambda: self._add_paint_effect("mask")
        )
        self.paint_effect_btn.setToolTip("Add Paint\nClick: Auto | Ctrl: Content | Shift: Mask")
        
        ops_grid.addWidget(self.gen_btn, 0, 0)
        ops_grid.addWidget(self.fill_effect_btn, 0, 1)
        ops_grid.addWidget(self.paint_effect_btn, 0, 2)
        
        # Row 1: Mask operations
        self.black_mask_btn = QPushButton("Black Mask")
        self.black_mask_btn.setToolTip("Add black mask to selected layer")
        self.black_mask_btn.clicked.connect(lambda: self._add_mask(False))
        
        self.white_mask_btn = QPushButton("White Mask")
        self.white_mask_btn.setToolTip("Add white mask to selected layer")
        self.white_mask_btn.clicked.connect(lambda: self._add_mask(True))
        
        self.invert_mask_btn = QPushButton("Invert Mask")
        self.invert_mask_btn.setToolTip("Invert mask of selected layer")
        self.invert_mask_btn.clicked.connect(self._invert_mask)
        
        ops_grid.addWidget(self.black_mask_btn, 1, 0)
        ops_grid.addWidget(self.white_mask_btn, 1, 1)
        ops_grid.addWidget(self.invert_mask_btn, 1, 2)
        
        layout.addLayout(ops_grid)
        
        layout.addStretch()
        self.setLayout(layout)

    def _add_fill_layer(self, channel_name, mask_type=None):
        """Add fill layer with proper channel activation."""
        mask_desc = "no mask" if mask_type is None else ("white mask" if mask_type else "black mask")
        print(f"➕ Adding {channel_name} fill layer w/ {mask_desc}…")
        
        channel_mapping = {
            "Color": textureset.ChannelType.BaseColor,
            "Roughness": textureset.ChannelType.Roughness, 
            "Height": textureset.ChannelType.Height,
            "Normal": textureset.ChannelType.Normal,
            "Metallic": textureset.ChannelType.Metallic
        }
        
        try:
            stack = textureset.get_active_stack()
            position = layerstack.InsertPosition.from_textureset_stack(stack)
            
            layer_node = layerstack.insert_fill(position)
            layer_node.set_name(f"{channel_name} Fill")
            
            if channel_name in channel_mapping:
                layer_node.active_channels = {channel_mapping[channel_name]}
                
                import substance_painter.colormanagement as colormanagement
                white = colormanagement.Color(1.0, 1.0, 1.0)
                layer_node.set_source(channel_mapping[channel_name], white)
            
            if mask_type is not None:
                if mask_type:
                    layer_node.add_mask(layerstack.MaskBackground.White)
                else:
                    layer_node.add_mask(layerstack.MaskBackground.Black)
            
            print(f"✅ {channel_name} fill layer created")
            
        except Exception as e:
            import traceback
            print(f"❌ Error: {e}")
            print(traceback.format_exc())

    def _add_hsl_filter(self):
        """Add HSL filter to selected layer."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ Select a layer first")
                return
            
            selected_layer = selected_nodes[0]
            hsl_resources = resource.search("u:filter n:hsl")
            
            if not hsl_resources:
                print("❌ HSL filter not found")
                return
            
            position = layerstack.InsertPosition.inside_node(selected_layer, layerstack.NodeStack.Content)
            filter_node = layerstack.insert_filter_effect(position, hsl_resources[0].identifier())
            
            if hasattr(selected_layer, 'active_channels'):
                filter_node.active_channels = selected_layer.active_channels
            
            print("✅ HSL filter added")
            
        except Exception as e:
            print(f"❌ Error: {e}")

    def _add_levels_filter(self):
        """Add Levels effect to selected layer."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ Select a layer first")
                return
            
            selected_layer = selected_nodes[0]
            position = layerstack.InsertPosition.inside_node(selected_layer, layerstack.NodeStack.Content)
            levels_node = layerstack.insert_levels_effect(position)
            
            if hasattr(selected_layer, 'active_channels') and selected_layer.active_channels:
                first_channel = list(selected_layer.active_channels)[0]
                levels_node.affected_channel = first_channel
            
            print("✅ Levels effect added")
            
        except Exception as e:
            print(f"❌ Error: {e}")

    def _add_blur_filter(self):
        """Add Blur filter to selected layer."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ Select a layer first")
                return
            
            selected_layer = selected_nodes[0]
            blur_resources = resource.search("u:filter n:blur")
            
            if not blur_resources:
                blur_resources = resource.search('s:starterassets u:filter n:Blur=')
            
            if not blur_resources:
                print("❌ Blur filter not found")
                return
            
            position = layerstack.InsertPosition.inside_node(selected_layer, layerstack.NodeStack.Content)
            filter_node = layerstack.insert_filter_effect(position, blur_resources[0].identifier())
            
            if hasattr(selected_layer, 'active_channels'):
                filter_node.active_channels = selected_layer.active_channels
            
            print("✅ Blur filter added")
            
        except Exception as e:
            print(f"❌ Error: {e}")

    def _add_generator(self, force_target=None):
        """
        Add generator effect.
        Args:
            force_target: None (auto-detect), "content", or "mask"
        """
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ Select a layer first")
                return
            
            selected_node = selected_nodes[0]
            parent = selected_node.get_parent()
            
            # Determine target based on force_target or context
            if force_target == "mask":
                in_mask = True
                target_layer = selected_node if not parent else parent
            elif force_target == "content":
                in_mask = False
                target_layer = selected_node
            else:
                # Auto-detect
                in_mask = False
                target_layer = selected_node
                if parent and hasattr(parent, 'mask_effects'):
                    mask_effects = parent.mask_effects()
                    if selected_node in mask_effects:
                        in_mask = True
                        target_layer = parent
            
            if in_mask:
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Mask)
                gen_node = layerstack.insert_generator_effect(position)
                print("✅ Generator added to mask")
            else:
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Content)
                gen_node = layerstack.insert_generator_effect(position)
                
                if hasattr(target_layer, 'active_channels'):
                    gen_node.active_channels = target_layer.active_channels
                
                print("✅ Generator added to content")
            
        except Exception as e:
            print(f"❌ Error: {e}")

    def _add_fill_effect(self, force_target=None):
        """
        Add fill effect.
        Args:
            force_target: None (auto-detect), "content", or "mask"
        """
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ Select a layer first")
                return
            
            selected_node = selected_nodes[0]
            parent = selected_node.get_parent()
            
            # Determine target based on force_target or context
            if force_target == "mask":
                in_mask = True
                target_layer = selected_node if not parent else parent
            elif force_target == "content":
                in_mask = False
                target_layer = selected_node
            else:
                # Auto-detect
                in_mask = False
                target_layer = selected_node
                if parent and hasattr(parent, 'mask_effects'):
                    mask_effects = parent.mask_effects()
                    if selected_node in mask_effects:
                        in_mask = True
                        target_layer = parent
            
            if in_mask:
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Mask)
                fill_node = layerstack.insert_fill(position)
                print("✅ Fill effect added to mask")
            else:
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Content)
                fill_node = layerstack.insert_fill(position)
                
                if hasattr(target_layer, 'active_channels') and target_layer.active_channels:
                    fill_node.active_channels = target_layer.active_channels
                    
                    import substance_painter.colormanagement as colormanagement
                    white = colormanagement.Color(1.0, 1.0, 1.0)
                    first_channel = list(target_layer.active_channels)[0]
                    fill_node.set_source(first_channel, white)
                
                print("✅ Fill effect added to content")
            
        except Exception as e:
            import traceback
            print(f"❌ Error: {e}")
            print(traceback.format_exc())

    def _add_paint_effect(self, force_target=None):
        """
        Add paint effect.
        Args:
            force_target: None (auto-detect), "content", or "mask"
        """
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ Select a layer first")
                return
            
            selected_node = selected_nodes[0]
            parent = selected_node.get_parent()
            
            # Determine target based on force_target or context
            if force_target == "mask":
                in_mask = True
                target_layer = selected_node if not parent else parent
            elif force_target == "content":
                in_mask = False
                target_layer = selected_node
            else:
                # Auto-detect
                in_mask = False
                target_layer = selected_node
                if parent and hasattr(parent, 'mask_effects'):
                    mask_effects = parent.mask_effects()
                    if selected_node in mask_effects:
                        in_mask = True
                        target_layer = parent
            
            if in_mask:
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Mask)
                paint_node = layerstack.insert_paint(position)
                print("✅ Paint effect added to mask")
            else:
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Content)
                paint_node = layerstack.insert_paint(position)
                
                if hasattr(target_layer, 'active_channels'):
                    paint_node.active_channels = target_layer.active_channels
                
                print("✅ Paint effect added to content")
            
        except Exception as e:
            import traceback
            print(f"❌ Error: {e}")
            print(traceback.format_exc())

    def _add_mask(self, white_mask):
        """Add mask to selected layer."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ Select a layer first")
                return
            
            selected_layer = selected_nodes[0]
            
            if not hasattr(selected_layer, 'add_mask'):
                print("⚠️ Selected node can't have a mask")
                return
            
            if selected_layer.has_mask():
                print("⚠️ Layer already has a mask")
                return
            
            if white_mask:
                selected_layer.add_mask(layerstack.MaskBackground.White)
                print("✅ White mask added")
            else:
                selected_layer.add_mask(layerstack.MaskBackground.Black)
                print("✅ Black mask added")
            
        except Exception as e:
            print(f"❌ Error: {e}")

    def _invert_mask(self):
        """Invert mask by adding invert filter to mask stack."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ Select a layer first")
                return
            
            selected_layer = selected_nodes[0]
            
            if not hasattr(selected_layer, 'has_mask') or not selected_layer.has_mask():
                print("⚠️ Layer has no mask to invert")
                return
            
            # Add invert filter to bottom of mask stack
            position = layerstack.InsertPosition.inside_node(selected_layer, layerstack.NodeStack.Mask)
            
            # Search for invert filter
            invert_resources = resource.search("u:filter n:invert")
            if not invert_resources:
                invert_resources = resource.search("s:starterassets u:filter n:Invert")
            
            if not invert_resources:
                print("❌ Invert filter not found")
                return
            
            layerstack.insert_filter_effect(position, invert_resources[0].identifier())
            print("✅ Mask inverted (added Invert filter)")
            
        except Exception as e:
            print(f"❌ Error: {e}")

def start_plugin():
    """Initialize and show the plugin."""
    global _plugin_refs
    
    widget = StackSlayer()
    substance_painter.ui.add_dock_widget(widget, UIMode.Edition)
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