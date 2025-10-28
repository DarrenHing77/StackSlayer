# stack_slayer.py

import substance_painter.ui
from substance_painter.ui import UIMode
import substance_painter.layerstack as layerstack
import substance_painter.textureset as textureset
import substance_painter.resource as resource

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QGridLayout, 
    QCheckBox, QApplication, QLabel, QToolButton, QFrame
)
from PySide6.QtCore import Qt

# Keep refs alive so Python GC doesn't kill our widgets
_plugin_refs = []

class CollapsibleSection(QWidget):
    """Collapsible section with header and content."""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.is_collapsed = False
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Header button
        self.header_btn = QToolButton()
        self.header_btn.setText(title)
        self.header_btn.setCheckable(True)
        self.header_btn.setChecked(True)
        self.header_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background: palette(button);
                padding: 4px;
                font-weight: bold;
                text-align: left;
            }
            QToolButton:hover {
                background: palette(midlight);
            }
        """)
        self.header_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.header_btn.setArrowType(Qt.DownArrow)
        self.header_btn.clicked.connect(self.toggle)
        
        # Content frame
        self.content_frame = QFrame()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 2, 0, 2)
        self.content_frame.setLayout(self.content_layout)
        
        layout.addWidget(self.header_btn)
        layout.addWidget(self.content_frame)
        self.setLayout(layout)
        
    def toggle(self):
        """Toggle collapsed state."""
        self.is_collapsed = not self.is_collapsed
        self.content_frame.setVisible(not self.is_collapsed)
        self.header_btn.setArrowType(Qt.RightArrow if self.is_collapsed else Qt.DownArrow)
        
    def add_widget(self, widget):
        """Add widget to content area."""
        self.content_layout.addWidget(widget)
        
    def add_layout(self, layout):
        """Add layout to content area."""
        self.content_layout.addLayout(layout)

class ModifierButton(QPushButton):
    """Button that supports Ctrl/Shift modifiers."""
    def __init__(self, text, normal_callback, ctrl_callback=None, shift_callback=None):
        super().__init__(text)
        self.normal_callback = normal_callback
        self.ctrl_callback = ctrl_callback
        self.shift_callback = shift_callback
        self.clicked.connect(self._handle_click)
        
        # Compact sizing
        self.setMaximumHeight(24)
        
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
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)
        
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # === FILL LAYERS SECTION ===
        fill_section = CollapsibleSection("Fill Layers")
        
        fill_grid = QGridLayout()
        fill_grid.setSpacing(2)
        
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
        
        fill_section.add_layout(fill_grid)
        layout.addWidget(fill_section)
        
        # === EFFECTS SECTION ===
        effects_section = CollapsibleSection("Effects")
        
        effects_grid = QGridLayout()
        effects_grid.setSpacing(2)
        
        self.hsl_btn = ModifierButton(
            "HSL",
            lambda: self._add_hsl_filter(None),
            lambda: self._add_hsl_filter("content"),
            lambda: self._add_hsl_filter("mask")
        )
        self.hsl_btn.setToolTip("Add HSL Filter\nClick: Auto | Ctrl: Content | Shift: Mask")
        
        self.levels_btn = ModifierButton(
            "Levels",
            lambda: self._add_levels_filter(None),
            lambda: self._add_levels_filter("content"),
            lambda: self._add_levels_filter("mask")
        )
        self.levels_btn.setToolTip("Add Levels\nClick: Auto | Ctrl: Content | Shift: Mask")
        
        self.blur_btn = ModifierButton(
            "Blur",
            lambda: self._add_blur_filter(None),
            lambda: self._add_blur_filter("content"),
            lambda: self._add_blur_filter("mask")
        )
        self.blur_btn.setToolTip("Add Blur Filter\nClick: Auto | Ctrl: Content | Shift: Mask")
        
        effects_grid.addWidget(self.hsl_btn, 0, 0)
        effects_grid.addWidget(self.levels_btn, 0, 1)
        effects_grid.addWidget(self.blur_btn, 0, 2)
        
        effects_section.add_layout(effects_grid)
        layout.addWidget(effects_section)
        
        # === LAYER OPERATIONS SECTION ===
        ops_section = CollapsibleSection("Layer Operations")
        
        ops_grid = QGridLayout()
        ops_grid.setSpacing(2)
        
        # Row 0: Generator, Fill, Paint
        self.gen_btn = ModifierButton(
            "Generator",
            lambda: self._add_generator(None),
            lambda: self._add_generator("content"),
            lambda: self._add_generator("mask")
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
        self.black_mask_btn.setMaximumHeight(24)
        self.black_mask_btn.setToolTip("Add black mask to selected layer")
        self.black_mask_btn.clicked.connect(lambda: self._add_mask(False))
        
        self.white_mask_btn = QPushButton("White Mask")
        self.white_mask_btn.setMaximumHeight(24)
        self.white_mask_btn.setToolTip("Add white mask to selected layer")
        self.white_mask_btn.clicked.connect(lambda: self._add_mask(True))
        
        self.invert_mask_btn = QPushButton("Invert Mask")
        self.invert_mask_btn.setMaximumHeight(24)
        self.invert_mask_btn.setToolTip("Invert mask of selected layer")
        self.invert_mask_btn.clicked.connect(self._invert_mask)
        
        ops_grid.addWidget(self.black_mask_btn, 1, 0)
        ops_grid.addWidget(self.white_mask_btn, 1, 1)
        ops_grid.addWidget(self.invert_mask_btn, 1, 2)
        
        # Row 2: Anchor Point
        self.anchor_btn = ModifierButton(
            "Anchor Point",
            lambda: self._add_anchor_point(None),
            lambda: self._add_anchor_point("content"),
            lambda: self._add_anchor_point("mask")
        )
        self.anchor_btn.setToolTip("Add Anchor Point\nClick: Auto | Ctrl: Content | Shift: Mask")
        
        ops_grid.addWidget(self.anchor_btn, 2, 0, 1, 3)  # Span all 3 columns
        
        ops_section.add_layout(ops_grid)
        layout.addWidget(ops_section)
        
        # Push everything to top
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

    def _add_hsl_filter(self, target_stack):
        """Add HSL filter to selected layer."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ Select a layer first")
                return
            
            selected_node = selected_nodes[0]
            parent = selected_node.get_parent()
            
            # Determine target
            in_mask = False
            target_layer = selected_node
            
            if target_stack == "mask":
                if not hasattr(selected_node, 'has_mask') or not selected_node.has_mask():
                    print("⚠️ Layer needs a mask first")
                    return
                in_mask = True
            elif target_stack == "content":
                in_mask = False
            else:
                # Auto-detect
                if parent and hasattr(parent, 'mask_effects'):
                    mask_effects = parent.mask_effects()
                    if selected_node in mask_effects:
                        in_mask = True
                        target_layer = parent
            
            hsl_resources = resource.search("u:filter n:hsl")
            if not hsl_resources:
                print("❌ HSL filter not found")
                return
            
            if in_mask:
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Mask)
                layerstack.insert_filter_effect(position, hsl_resources[0].identifier())
                print("✅ HSL filter added to mask")
            else:
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Content)
                filter_node = layerstack.insert_filter_effect(position, hsl_resources[0].identifier())
                if hasattr(target_layer, 'active_channels'):
                    filter_node.active_channels = target_layer.active_channels
                print("✅ HSL filter added to content")
            
        except Exception as e:
            print(f"❌ Error: {e}")

    def _add_levels_filter(self, target_stack):
        """Add Levels effect to selected layer."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ Select a layer first")
                return
            
            selected_node = selected_nodes[0]
            parent = selected_node.get_parent()
            
            # Determine target
            in_mask = False
            target_layer = selected_node
            
            if target_stack == "mask":
                if not hasattr(selected_node, 'has_mask') or not selected_node.has_mask():
                    print("⚠️ Layer needs a mask first")
                    return
                in_mask = True
            elif target_stack == "content":
                in_mask = False
            else:
                # Auto-detect
                if parent and hasattr(parent, 'mask_effects'):
                    mask_effects = parent.mask_effects()
                    if selected_node in mask_effects:
                        in_mask = True
                        target_layer = parent
            
            if in_mask:
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Mask)
                layerstack.insert_levels_effect(position)
                print("✅ Levels effect added to mask")
            else:
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Content)
                levels_node = layerstack.insert_levels_effect(position)
                if hasattr(target_layer, 'active_channels') and target_layer.active_channels:
                    first_channel = list(target_layer.active_channels)[0]
                    levels_node.affected_channel = first_channel
                print("✅ Levels effect added to content")
            
        except Exception as e:
            print(f"❌ Error: {e}")

    def _add_blur_filter(self, target_stack):
        """Add Blur filter to selected layer."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ Select a layer first")
                return
            
            selected_node = selected_nodes[0]
            parent = selected_node.get_parent()
            
            # Determine target
            in_mask = False
            target_layer = selected_node
            
            if target_stack == "mask":
                if not hasattr(selected_node, 'has_mask') or not selected_node.has_mask():
                    print("⚠️ Layer needs a mask first")
                    return
                in_mask = True
            elif target_stack == "content":
                in_mask = False
            else:
                # Auto-detect
                if parent and hasattr(parent, 'mask_effects'):
                    mask_effects = parent.mask_effects()
                    if selected_node in mask_effects:
                        in_mask = True
                        target_layer = parent
            
            blur_resources = resource.search("u:filter n:blur")
            if not blur_resources:
                blur_resources = resource.search('s:starterassets u:filter n:Blur=')
            if not blur_resources:
                print("❌ Blur filter not found")
                return
            
            if in_mask:
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Mask)
                layerstack.insert_filter_effect(position, blur_resources[0].identifier())
                print("✅ Blur filter added to mask")
            else:
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Content)
                filter_node = layerstack.insert_filter_effect(position, blur_resources[0].identifier())
                if hasattr(target_layer, 'active_channels'):
                    filter_node.active_channels = target_layer.active_channels
                print("✅ Blur filter added to content")
            
        except Exception as e:
            print(f"❌ Error: {e}")

    def _add_generator(self, target_stack):
        """Add generator effect to selected layer's content or mask."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ Select a layer first")
                return
            
            selected_node = selected_nodes[0]
            parent = selected_node.get_parent()
            
            # Determine if we're in mask context
            in_mask = False
            target_layer = selected_node
            
            if target_stack == "mask":
                if not hasattr(selected_node, 'has_mask') or not selected_node.has_mask():
                    print("⚠️ Layer needs a mask first")
                    return
                in_mask = True
            elif target_stack == "content":
                in_mask = False
            else:
                # Auto-detect
                if parent and hasattr(parent, 'mask_effects'):
                    mask_effects = parent.mask_effects()
                    if selected_node in mask_effects:
                        in_mask = True
                        target_layer = parent
            
            if in_mask:
                # Add to mask stack
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Mask)
                gen_node = layerstack.insert_generator_effect(position)
                print("✅ Generator added to mask")
            else:
                # Add to content stack
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Content)
                gen_node = layerstack.insert_generator_effect(position)
                
                if hasattr(target_layer, 'active_channels'):
                    gen_node.active_channels = target_layer.active_channels
                
                print("✅ Generator added to content")
            
        except Exception as e:
            print(f"❌ Error: {e}")

    def _add_fill_effect(self, target_stack):
        """Add fill effect to selected layer's content or mask."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ Select a layer first")
                return
            
            selected_node = selected_nodes[0]
            parent = selected_node.get_parent()
            
            # Determine if we're in mask context
            in_mask = False
            target_layer = selected_node
            
            if target_stack == "mask":
                if not hasattr(selected_node, 'has_mask') or not selected_node.has_mask():
                    print("⚠️ Layer needs a mask first")
                    return
                in_mask = True
            elif target_stack == "content":
                in_mask = False
            else:
                # Auto-detect
                if parent and hasattr(parent, 'mask_effects'):
                    mask_effects = parent.mask_effects()
                    if selected_node in mask_effects:
                        in_mask = True
                        target_layer = parent
            
            if in_mask:
                # Add to mask stack
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Mask)
                fill_node = layerstack.insert_fill(position)
                print("✅ Fill effect added to mask")
            else:
                # Add to content stack
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Content)
                fill_node = layerstack.insert_fill(position)
                
                # Set white color and match channels for content
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

    def _add_paint_effect(self, target_stack):
        """Add paint effect to selected layer's content or mask."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ Select a layer first")
                return
            
            selected_node = selected_nodes[0]
            parent = selected_node.get_parent()
            
            # Determine if we're in mask context
            in_mask = False
            target_layer = selected_node
            
            if target_stack == "mask":
                if not hasattr(selected_node, 'has_mask') or not selected_node.has_mask():
                    print("⚠️ Layer needs a mask first")
                    return
                in_mask = True
            elif target_stack == "content":
                in_mask = False
            else:
                # Auto-detect
                if parent and hasattr(parent, 'mask_effects'):
                    mask_effects = parent.mask_effects()
                    if selected_node in mask_effects:
                        in_mask = True
                        target_layer = parent
            
            if in_mask:
                # Add to mask stack
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Mask)
                paint_node = layerstack.insert_paint(position)
                print("✅ Paint effect added to mask")
            else:
                # Add to content stack
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
    
    def _add_anchor_point(self, target_stack):
        """Add anchor point to selected layer's content or mask."""
        try:
            stack = textureset.get_active_stack()
            selected_nodes = layerstack.get_selected_nodes(stack)
            
            if not selected_nodes:
                print("⚠️ Select a layer first")
                return
            
            selected_node = selected_nodes[0]
            parent = selected_node.get_parent()
            
            # Determine if we're in mask context
            in_mask = False
            target_layer = selected_node
            
            if target_stack == "mask":
                if not hasattr(selected_node, 'has_mask') or not selected_node.has_mask():
                    print("⚠️ Layer needs a mask first")
                    return
                in_mask = True
            elif target_stack == "content":
                in_mask = False
            else:
                # Auto-detect
                if parent and hasattr(parent, 'mask_effects'):
                    mask_effects = parent.mask_effects()
                    if selected_node in mask_effects:
                        in_mask = True
                        target_layer = parent
            
            if in_mask:
                # Add to mask stack
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Mask)
                layerstack.insert_anchor_point_effect(position, "Anchor Point")
                print("✅ Anchor point added to mask")
            else:
                # Add to content stack
                position = layerstack.InsertPosition.inside_node(target_layer, layerstack.NodeStack.Content)
                layerstack.insert_anchor_point_effect(position, "Anchor Point")
                print("✅ Anchor point added to content")
            
        except Exception as e:
            import traceback
            print(f"❌ Error: {e}")
            print(traceback.format_exc())

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