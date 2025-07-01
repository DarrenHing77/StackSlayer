# StackSlayer

A no-bullshit Substance Painter plugin that speeds up your layer workflow.

## What It Does

**Fill Tools:**
- **Color Fill** - Creates fill layer with mask (white by default, Ctrl+click for black)
- **Roughness Fill** - Same deal but for roughness channel
- **Height Fill** - Height channel fill layer

**Masking & Filters:**
- **HSL Filter** - Adds HSL filter to selected layer
- **Levels Filter** - Adds Levels filter to selected layer

## Installation

1. Copy `stack_slayer.py` and `plugin.json` to your SP plugins folder:
   - **Windows:** `Documents/Adobe/Adobe Substance 3D Painter/python/plugins/`
   - **Mac:** `Documents/Adobe/Adobe Substance 3D Painter/python/plugins/`
   - **Linux:** `Documents/Adobe/Adobe Substance 3D Painter/python/plugins/`

2. Restart Substance Painter
3. Find StackSlayer in your docked panels

## Usage

**Fill Layers:**
- Click any fill button = white mask
- Ctrl+click any fill button = black mask

**Filters:**
- Select a layer first
- Click filter button to add it

## Requirements

- Substance Painter 10.0+ (uses the new layerstack API)

## Why This Exists

Because clicking through menus to add basic layers is fucking tedious. This plugin cuts the bullshit and gets you painting faster.

## Issues?

If something breaks, check the Python console. The plugin prints debug info when things go wrong.
