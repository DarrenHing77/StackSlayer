"""
DH SP Tools - Custom Substance Painter Tools
Author: Your Name
Version: 1.2
"""

import json
import os
from pathlib import Path

from PySide6.QtWidgets import QWidget, QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QAction, QKeySequence

import substance_painter.ui as ui
import substance_painter.textureset as textureset
import substance_painter.layerstack as layerstack


# ============================================================================
# CONFIG MANAGER
# ============================================================================

class ConfigManager:
    """Manages plugin configuration and hotkeys."""
    
    DEFAULT_CONFIG = {
        "hotkeys": {
            "cycle_texture_set_up": "Ctrl+Shift+W",
            "cycle_texture_set_down": "Ctrl+Shift+E",
            "cycle_layer_up": "Shift+W",
            "cycle_layer_down": "Shift+E"
        }
    }
    
    def __init__(self):
        # Config file location: same dir as the plugin
        self.config_path = Path(__file__).parent / "dh_sp_tools_config.json"
        self.config = self.load_config()
    
    def load_config(self):
        """Load config from JSON file, create with defaults if missing."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    print(f"DH SP Tools: Config loaded from {self.config_path}")
                    return config
            except Exception as e:
                print(f"DH SP Tools: Error loading config: {e}")
                print("DH SP Tools: Using default config")
        else:
            # Create default config file
            self.save_config(self.DEFAULT_CONFIG)
            print(f"DH SP Tools: Created default config at {self.config_path}")
        
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, config):
        """Save config to JSON file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"DH SP Tools: Error saving config: {e}")
    
    def get_hotkey(self, action_name):
        """Get hotkey for an action."""
        return self.config.get("hotkeys", {}).get(action_name, "")


# ============================================================================
# VIEWPORT OVERLAY
# ============================================================================

class ViewportOverlay(QLabel):
    """
    Transparent overlay widget that appears at the bottom of the viewport
    and fades out after a few seconds.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup appearance
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: #FFFFFF;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        self.setAlignment(Qt.AlignCenter)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Opacity animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)
        
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.finished.connect(self.hide)
        
        # Auto-hide timer
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._start_fade_out)
        
        self.hide()
    
    def show_message(self, text, duration=2000):
        """Show a message that fades out after duration ms."""
        self.setText(text)
        self.adjustSize()
        self._position_at_bottom()
        
        # Reset and show
        self.opacity_effect.setOpacity(1.0)
        self.show()
        self.raise_()  # Make sure it's on top
        
        # Start hide timer
        self.hide_timer.stop()
        self.fade_animation.stop()
        self.hide_timer.start(duration)
    
    def _start_fade_out(self):
        """Begin the fade out animation."""
        self.fade_animation.start()
    
    def _position_at_bottom(self):
        """Position the overlay at the bottom center of the main window."""
        if self.parent():
            parent_rect = self.parent().rect()
            margin = 50
            
            x = (parent_rect.width() - self.width()) // 2
            y = parent_rect.height() - self.height() - margin
            
            self.move(x, y)


# ============================================================================
# TEXTURE SET CYCLER
# ============================================================================

class TextureSetCycler:
    """Handles cycling through texture sets with hotkeys."""
    
    def __init__(self, overlay_widget, config_manager):
        self.overlay = overlay_widget
        self.config = config_manager
        self.current_index = 0
        self.action_up = None
        self.action_down = None
    
    def setup_hotkeys(self):
        """Register the hotkey actions."""
        hotkey_up = self.config.get_hotkey("cycle_texture_set_up")
        hotkey_down = self.config.get_hotkey("cycle_texture_set_down")
        
        # Up action
        self.action_up = QAction("Cycle Texture Set Up")
        self.action_up.setShortcut(QKeySequence(hotkey_up))
        self.action_up.triggered.connect(self.cycle_up)
        ui.add_action(ui.ApplicationMenu.Edit, self.action_up)
        
        # Down action
        self.action_down = QAction("Cycle Texture Set Down")
        self.action_down.setShortcut(QKeySequence(hotkey_down))
        self.action_down.triggered.connect(self.cycle_down)
        ui.add_action(ui.ApplicationMenu.Edit, self.action_down)
        
        print(f"  - {hotkey_up}: Cycle Texture Set Up")
        print(f"  - {hotkey_down}: Cycle Texture Set Down")
    
    def cycle_up(self):
        """Cycle to the previous texture set."""
        self._cycle(-1)
    
    def cycle_down(self):
        """Cycle to the next texture set."""
        self._cycle(1)
    
    def _cycle(self, direction):
        """Cycle texture set by direction (+1 or -1)."""
        sets = textureset.all_texture_sets()
        
        if not sets:
            self.overlay.show_message("⚠️ No Texture Sets", 1500)
            return
        
        # Cycle with wrap-around
        self.current_index = (self.current_index + direction) % len(sets)
        active_set = sets[self.current_index]
        
        # Set active
        try:
            stack = active_set.all_stacks()[0]
            textureset.set_active_stack(stack)
            
            # Show overlay
            set_name = active_set.name()
            direction_arrow = "⬆️" if direction < 0 else "⬇️"
            message = f"{direction_arrow} {set_name} ({self.current_index + 1}/{len(sets)})"
            self.overlay.show_message(message, 2000)
            
        except Exception as e:
            self.overlay.show_message(f"❌ Error: {str(e)}", 2000)
    
    def cleanup(self):
        """Remove the actions when plugin closes."""
        if self.action_up:
            ui.delete_ui_element(self.action_up)
        if self.action_down:
            ui.delete_ui_element(self.action_down)


# ============================================================================
# LAYER CYCLER
# ============================================================================

class LayerCycler:
    """Handles cycling through layers with hotkeys."""
    
    def __init__(self, overlay_widget, config_manager):
        self.overlay = overlay_widget
        self.config = config_manager
        self.action_up = None
        self.action_down = None
    
    def setup_hotkeys(self):
        """Register the hotkey actions."""
        hotkey_up = self.config.get_hotkey("cycle_layer_up")
        hotkey_down = self.config.get_hotkey("cycle_layer_down")
        
        # Up action
        self.action_up = QAction("Cycle Layer Up")
        self.action_up.setShortcut(QKeySequence(hotkey_up))
        self.action_up.triggered.connect(self.cycle_up)
        ui.add_action(ui.ApplicationMenu.Edit, self.action_up)
        
        # Down action
        self.action_down = QAction("Cycle Layer Down")
        self.action_down.setShortcut(QKeySequence(hotkey_down))
        self.action_down.triggered.connect(self.cycle_down)
        ui.add_action(ui.ApplicationMenu.Edit, self.action_down)
        
        print(f"  - {hotkey_up}: Cycle Layer Up")
        print(f"  - {hotkey_down}: Cycle Layer Down")
    
    def cycle_up(self):
        """Cycle to the previous layer in the stack."""
        self._cycle_layer(-1)
    
    def cycle_down(self):
        """Cycle to the next layer in the stack."""
        self._cycle_layer(1)
    
    def _cycle_layer(self, direction):
        """Cycle layer by direction (+1 or -1)."""
        try:
            # Get active stack
            active_stack = textureset.get_active_stack()
            if not active_stack:
                self.overlay.show_message("⚠️ No Active Stack", 1500)
                return
            
            # Get all layers in the stack
            all_layers = self._get_all_layers(active_stack)
            
            if not all_layers:
                self.overlay.show_message("⚠️ No Layers", 1500)
                return
            
            # Get currently selected layers
            selected = layerstack.get_selected_nodes(active_stack)
            
            if not selected:
                # Nothing selected, select first/last
                target_layer = all_layers[0] if direction > 0 else all_layers[-1]
            else:
                # Find index of first selected layer
                current_layer = selected[0]
                try:
                    current_idx = all_layers.index(current_layer)
                    # Cycle with wrap-around
                    new_idx = (current_idx + direction) % len(all_layers)
                    target_layer = all_layers[new_idx]
                except ValueError:
                    # Current selection not in list, select first
                    target_layer = all_layers[0]
            
            # Select the layer
            layerstack.set_selected_nodes([target_layer])
            
            # Show overlay
            layer_name = target_layer.get_name()
            layer_type = type(target_layer).__name__.replace("Layer", "").replace("Node", "")
            direction_arrow = "⬆️" if direction < 0 else "⬇️"
            message = f"{direction_arrow} {layer_name} ({layer_type})"
            self.overlay.show_message(message, 1500)
            
        except Exception as e:
            self.overlay.show_message(f"❌ Error: {str(e)}", 2000)
    
    def _get_all_layers(self, stack):
        """Recursively get all layers in a stack (including nested)."""
        layers = []
        
        def traverse(node):
            layers.append(node)
            # Check if it's a group and traverse children
            if hasattr(node, 'children'):
                try:
                    for child in reversed(node.children()):  # Reversed for top-to-bottom order
                        traverse(child)
                except:
                    pass
        
        # Start from root - USE THE CORRECT FUNCTION
        try:
            root_nodes = layerstack.get_root_layer_nodes(stack)
            for node in reversed(root_nodes):
                traverse(node)
        except Exception as e:
            print(f"Error traversing layers: {e}")
        
        return layers
    
    def cleanup(self):
        """Remove the actions when plugin closes."""
        if self.action_up:
            ui.delete_ui_element(self.action_up)
        if self.action_down:
            ui.delete_ui_element(self.action_down)


# ============================================================================
# PLUGIN MAIN
# ============================================================================

_plugin_overlay = None
_plugin_config = None
_plugin_texture_cycler = None
_plugin_layer_cycler = None


def start_plugin():
    """Called when plugin is loaded."""
    global _plugin_overlay, _plugin_config, _plugin_texture_cycler, _plugin_layer_cycler
    
    # Load config
    _plugin_config = ConfigManager()
    
    # Get main window
    main_window = ui.get_main_window()
    
    # Create overlay
    _plugin_overlay = ViewportOverlay(main_window)
    
    # Create texture set cycler
    _plugin_texture_cycler = TextureSetCycler(_plugin_overlay, _plugin_config)
    _plugin_texture_cycler.setup_hotkeys()
    
    # Create layer cycler
    _plugin_layer_cycler = LayerCycler(_plugin_overlay, _plugin_config)
    _plugin_layer_cycler.setup_hotkeys()
    
    print("DH SP Tools: Plugin loaded ✓")


def close_plugin():
    """Called when plugin is unloaded."""
    global _plugin_overlay, _plugin_config, _plugin_texture_cycler, _plugin_layer_cycler
    
    if _plugin_texture_cycler:
        _plugin_texture_cycler.cleanup()
        _plugin_texture_cycler = None
    
    if _plugin_layer_cycler:
        _plugin_layer_cycler.cleanup()
        _plugin_layer_cycler = None
    
    if _plugin_overlay:
        _plugin_overlay.deleteLater()
        _plugin_overlay = None
    
    _plugin_config = None
    
    print("DH SP Tools: Plugin unloaded")


if __name__ == "__main__":
    start_plugin()