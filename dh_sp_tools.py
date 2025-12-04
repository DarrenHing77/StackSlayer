"""
DH SP Tools - Custom Substance Painter Tools
Author: Your Name
Version: 1.3
"""

import json
import os
from pathlib import Path

from PySide6.QtWidgets import (QWidget, QLabel, QGraphicsOpacityEffect, QDialog,
                               QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
                               QPushButton, QMessageBox)
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
            "cycle_texture_set_down": "Ctrl+Shift+S",
            "cycle_layer_up": "Ctrl+W",
            "cycle_layer_down": "Ctrl+S",
            "cycle_effect_up": "Ctrl+Shift+Q",
            "cycle_effect_down": "Ctrl+Shift+A",
            "toggle_mask_content": "`"
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

    def update_hotkey(self, action_name, new_hotkey):
        """Update a hotkey and save the config."""
        if "hotkeys" not in self.config:
            self.config["hotkeys"] = {}
        self.config["hotkeys"][action_name] = new_hotkey
        self.save_config(self.config)


# ============================================================================
# SETTINGS DIALOG
# ============================================================================

class SettingsDialog(QDialog):
    """Dialog for editing plugin hotkeys."""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.setWindowTitle("DH SP Tools - Hotkey Settings")
        self.setMinimumWidth(500)

        # Store input fields
        self.hotkey_inputs = {}

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Create the settings UI."""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Edit hotkeys below. Use format like 'Ctrl+W', 'Shift+A', '`', etc.\n"
            "Changes require plugin reload to take effect."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Form for hotkeys
        form_layout = QFormLayout()

        # Define friendly names for each action
        action_labels = {
            "cycle_texture_set_up": "Cycle Texture Set Up:",
            "cycle_texture_set_down": "Cycle Texture Set Down:",
            "cycle_layer_up": "Cycle Layer Up:",
            "cycle_layer_down": "Cycle Layer Down:",
            "cycle_effect_up": "Cycle Effect Up:",
            "cycle_effect_down": "Cycle Effect Down:",
            "toggle_mask_content": "Toggle Mask/Content:"
        }

        # Create input field for each hotkey
        for action_name, label_text in action_labels.items():
            current_hotkey = self.config.get_hotkey(action_name)
            input_field = QLineEdit(current_hotkey)
            input_field.setPlaceholderText("e.g., Ctrl+W, Shift+A, `")
            self.hotkey_inputs[action_name] = input_field
            form_layout.addRow(label_text, input_field)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()

        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_button)

        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save")
        save_button.setDefault(True)
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

    def reset_to_defaults(self):
        """Reset all hotkeys to default values."""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Reset all hotkeys to default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            for action_name, input_field in self.hotkey_inputs.items():
                default_hotkey = ConfigManager.DEFAULT_CONFIG["hotkeys"].get(action_name, "")
                input_field.setText(default_hotkey)

    def save_settings(self):
        """Save the hotkey settings."""
        # Update config with new values
        for action_name, input_field in self.hotkey_inputs.items():
            new_hotkey = input_field.text().strip()
            self.config.update_hotkey(action_name, new_hotkey)

        QMessageBox.information(
            self,
            "Settings Saved",
            "Hotkey settings saved!\n\nPlease reload the plugin for changes to take effect:\n"
            "Python → DH SP Tools → Reload Plugin"
        )

        self.accept()


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
        """Get all layers and groups in a stack at the current level only."""
        layers = []

        # Get root level nodes only, don't traverse into groups
        try:
            root_nodes = layerstack.get_root_layer_nodes(stack)
            # Reversed for top-to-bottom order
            layers = list(reversed(root_nodes))
        except Exception as e:
            print(f"Error getting layers: {e}")

        return layers
    
    def cleanup(self):
        """Remove the actions when plugin closes."""
        if self.action_up:
            ui.delete_ui_element(self.action_up)
        if self.action_down:
            ui.delete_ui_element(self.action_down)


# ============================================================================
# EFFECT CYCLER (NEW)
# ============================================================================

class EffectCycler:
    """Handles cycling through effects in a layer."""
    
    def __init__(self, overlay_widget, config_manager):
        self.overlay = overlay_widget
        self.config = config_manager
        self.action_up = None
        self.action_down = None
    
    def setup_hotkeys(self):
        """Register the hotkey actions."""
        hotkey_up = self.config.get_hotkey("cycle_effect_up")
        hotkey_down = self.config.get_hotkey("cycle_effect_down")
        
        # Up action
        self.action_up = QAction("Cycle Effect Up")
        self.action_up.setShortcut(QKeySequence(hotkey_up))
        self.action_up.triggered.connect(self.cycle_up)
        ui.add_action(ui.ApplicationMenu.Edit, self.action_up)
        
        # Down action
        self.action_down = QAction("Cycle Effect Down")
        self.action_down.setShortcut(QKeySequence(hotkey_down))
        self.action_down.triggered.connect(self.cycle_down)
        ui.add_action(ui.ApplicationMenu.Edit, self.action_down)
        
        print(f"  - {hotkey_up}: Cycle Effect Up")
        print(f"  - {hotkey_down}: Cycle Effect Down")
    
    def cycle_up(self):
        """Cycle to previous effect."""
        self._cycle_effect(-1)
    
    def cycle_down(self):
        """Cycle to next effect."""
        self._cycle_effect(1)
    
    def _cycle_effect(self, direction):
        """Cycle through effects and filters by direction (+1 or -1)."""
        try:
            stack = textureset.get_active_stack()
            selected = layerstack.get_selected_nodes(stack)

            if not selected:
                self.overlay.show_message("⚠️ Select a layer first", 1500)
                return

            current_node = selected[0]

            # Get parent layer if we're already on an effect
            parent = current_node.get_parent()
            if parent and hasattr(parent, 'content_effects'):
                target_layer = parent
            else:
                target_layer = current_node

            # Determine if we're in mask mode
            selection_type = layerstack.get_selection_type(target_layer)
            is_mask_mode = selection_type == layerstack.SelectionType.Mask

            # Gather effects based on selection type
            # Note: content_effects() and mask_effects() return ALL effect types
            # including Fill, Paint, Filter, Generator, etc.
            all_items = []
            content_items = []
            mask_items = []

            if is_mask_mode:
                # When mask is selected, cycle through mask effects only
                if hasattr(target_layer, 'mask_effects'):
                    mask_items = target_layer.mask_effects()
                all_items = mask_items
            else:
                # When content is selected, cycle through both content and mask effects
                if hasattr(target_layer, 'content_effects'):
                    content_items = target_layer.content_effects()
                if hasattr(target_layer, 'mask_effects'):
                    mask_items = target_layer.mask_effects()
                all_items = content_items + mask_items

            if not all_items:
                location = "mask" if is_mask_mode else "layer"
                self.overlay.show_message(f"⚠️ No effects/filters in {location}", 1500)
                return

            # Find current item index
            try:
                current_idx = all_items.index(current_node)
                new_idx = (current_idx + direction) % len(all_items)
            except ValueError:
                # If current node isn't in the list, select first item
                new_idx = 0

            # Select the item
            new_item = all_items[new_idx]
            layerstack.set_selected_nodes([new_item])

            # Show overlay
            item_name = new_item.get_name()
            item_type = type(new_item).__name__.replace("Effect", "").replace("Filter", "").replace("Node", "")
            is_mask = new_item in mask_items
            location = "Mask" if is_mask else "Content"
            direction_arrow = "⬆️" if direction < 0 else "⬇️"
            message = f"{direction_arrow} {item_name} ({item_type} - {location})"
            self.overlay.show_message(message, 1500)

        except Exception as e:
            self.overlay.show_message(f"❌ Error: {str(e)}", 2000)
    
    def cleanup(self):
        """Remove the actions when plugin closes."""
        if self.action_up:
            ui.delete_ui_element(self.action_up)
        if self.action_down:
            ui.delete_ui_element(self.action_down)


# ============================================================================
# MASK/CONTENT TOGGLER (NEW)
# ============================================================================

class MaskContentToggler:
    """Handles toggling between mask and content selection."""
    
    def __init__(self, overlay_widget, config_manager):
        self.overlay = overlay_widget
        self.config = config_manager
        self.action = None
    
    def setup_hotkeys(self):
        """Register the hotkey action."""
        hotkey = self.config.get_hotkey("toggle_mask_content")
        
        self.action = QAction("Toggle Mask/Content")
        self.action.setShortcut(QKeySequence(hotkey))
        self.action.triggered.connect(self.toggle)
        ui.add_action(ui.ApplicationMenu.Edit, self.action)
        
        print(f"  - {hotkey}: Toggle Mask/Content")
    
    def toggle(self):
        """Toggle between mask and content selection."""
        try:
            stack = textureset.get_active_stack()
            selected = layerstack.get_selected_nodes(stack)

            if not selected:
                self.overlay.show_message("⚠️ Select a layer first", 1500)
                return

            layer = selected[0]

            if not hasattr(layer, 'has_mask'):
                self.overlay.show_message("⚠️ Layer doesn't support masks", 1500)
                return

            current_type = layerstack.get_selection_type(layer)

            # Toggle logic
            if current_type == layerstack.SelectionType.Content:
                if layer.has_mask():
                    layerstack.set_selection_type(layer, layerstack.SelectionType.Mask)
                    self.overlay.show_message("🎭 Switched to Mask", 1500)
                else:
                    self.overlay.show_message("⚠️ Layer has no mask", 1500)
            elif current_type == layerstack.SelectionType.Mask:
                layerstack.set_selection_type(layer, layerstack.SelectionType.Content)
                self.overlay.show_message("🎨 Switched to Content", 1500)
            else:
                # Default to content if in properties or other state
                layerstack.set_selection_type(layer, layerstack.SelectionType.Content)
                self.overlay.show_message("🎨 Switched to Content", 1500)

        except Exception as e:
            self.overlay.show_message(f"❌ Error: {str(e)}", 2000)
    
    def cleanup(self):
        """Remove the action when plugin closes."""
        if self.action:
            ui.delete_ui_element(self.action)


# ============================================================================
# PLUGIN MAIN
# ============================================================================

_plugin_overlay = None
_plugin_config = None
_plugin_texture_cycler = None
_plugin_layer_cycler = None
_plugin_effect_cycler = None
_plugin_mask_toggler = None
_plugin_settings_action = None


def show_settings_dialog():
    """Show the hotkey settings dialog."""
    global _plugin_config
    if _plugin_config:
        dialog = SettingsDialog(_plugin_config, ui.get_main_window())
        dialog.exec()


def start_plugin():
    """Called when plugin is loaded."""
    global _plugin_overlay, _plugin_config, _plugin_texture_cycler, _plugin_layer_cycler
    global _plugin_effect_cycler, _plugin_mask_toggler, _plugin_settings_action

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

    # Create effect cycler (NEW)
    _plugin_effect_cycler = EffectCycler(_plugin_overlay, _plugin_config)
    _plugin_effect_cycler.setup_hotkeys()

    # Create mask/content toggler (NEW)
    _plugin_mask_toggler = MaskContentToggler(_plugin_overlay, _plugin_config)
    _plugin_mask_toggler.setup_hotkeys()

    # Add settings menu item
    _plugin_settings_action = QAction("DH SP Tools Settings...")
    _plugin_settings_action.triggered.connect(show_settings_dialog)
    ui.add_action(ui.ApplicationMenu.Edit, _plugin_settings_action)

    print("DH SP Tools: Plugin loaded ✓")
    print("  Access settings via: Edit → DH SP Tools Settings...")


def close_plugin():
    """Called when plugin is unloaded."""
    global _plugin_overlay, _plugin_config, _plugin_texture_cycler, _plugin_layer_cycler
    global _plugin_effect_cycler, _plugin_mask_toggler, _plugin_settings_action

    if _plugin_texture_cycler:
        _plugin_texture_cycler.cleanup()
        _plugin_texture_cycler = None

    if _plugin_layer_cycler:
        _plugin_layer_cycler.cleanup()
        _plugin_layer_cycler = None

    if _plugin_effect_cycler:
        _plugin_effect_cycler.cleanup()
        _plugin_effect_cycler = None

    if _plugin_mask_toggler:
        _plugin_mask_toggler.cleanup()
        _plugin_mask_toggler = None

    if _plugin_settings_action:
        ui.delete_ui_element(_plugin_settings_action)
        _plugin_settings_action = None

    if _plugin_overlay:
        _plugin_overlay.deleteLater()
        _plugin_overlay = None

    _plugin_config = None

    print("DH SP Tools: Plugin unloaded")


if __name__ == "__main__":
    start_plugin()