# StackSlayer

A no-bullshit Substance Painter plugin that speeds up your layer workflow with hotkey-driven layer creation.

## Features

### Fill Layers (with Modifier Keys)
Quickly add fill layers for any channel with optional masking:
- **Color Fill**
- **Roughness Fill**
- **Height Fill**
- **Metallic Fill**
- **Normal Fill**

**Modifier Keys:**
- Click: No mask
- Ctrl+Click: Black mask
- Shift+Click: White mask

### Effects (with Content/Mask Control)
Add effects to your layers with smart targeting:
- **HSL Filter**
- **Levels**
- **Blur**

**Modifier Keys:**
- Click: Auto-detect (adds to content or mask based on selection)
- Ctrl+Click: Force add to content stack
- Shift+Click: Force add to mask stack

### Layer Operations
Advanced layer operations with the same modifier key system:
- **Generator** - Add procedural generators
- **Fill** - Add fill effects
- **Paint** - Add paint layers/effects
- **Anchor Point** - Add anchor points for referencing

**Modifier Keys:**
- Click: Auto-detect (selection-based)
- Ctrl+Click: Force add to content stack
- Shift+Click: Force add to mask stack

### Mask Operations
Quick mask manipulation:
- **Black Mask** - Add black mask to selected layer
- **White Mask** - Add white mask to selected layer
- **Invert Mask** - Invert mask using filter

### UI Features
- **Collapsible Sections** - Click headers to collapse/expand categories
- **Compact Design** - Smaller buttons (24px height) for efficient screen space
- **Scalable Width** - Resizes between 200-400px

## Installation

1. Copy `stack_slayer.py` to your Substance Painter plugins folder:
   - **Windows:** `Documents/Adobe/Adobe Substance 3D Painter/python/plugins/`
   - **Mac:** `Documents/Adobe/Adobe Substance 3D Painter/python/plugins/`
   - **Linux:** `Documents/Adobe/Adobe Substance 3D Painter/python/plugins/`

2. Restart Substance Painter
3. Find StackSlayer in your docked panels

## Usage

### Fill Layers
Just click any fill button. Hold Ctrl for black mask, Shift for white mask.

### Effects
Select a layer, then:
- Click an effect button to auto-add (detects if you're in mask or content)
- Ctrl+Click to force add to content
- Shift+Click to force add to mask

### Layer Operations
Same deal as effects - select where you want to add, use modifiers to control content vs mask placement.

### Organizing Your Workspace
Click the section headers ("Fill Layers", "Effects", "Layer Operations") to collapse sections you don't need right now.

## Requirements

- Substance Painter 10.0+ (uses the new layerstack API)

## Why This Exists

Because clicking through menus to add basic layers and effects is fucking tedious. This plugin cuts the bullshit and gets you painting faster. The modifier key system means you can build complex layer stacks without ever touching a menu.

## Issues?

Check the Python console if something breaks. The plugin prints debug info for all operations.
