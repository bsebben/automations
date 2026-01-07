# Screenshot Tool - Now in automations repository

# macOS Screenshot with Annotation Tool

A collection of scripts and configurations for taking screenshots with optional annotation on macOS.

## Features

- **Interactive Selection**: Select a region or press Space to capture a specific window
- **ShareX-Style Mode**: Window/region highlighting as you hover (like ShareX on Windows)
- **Annotation Support**: Optionally open in Preview to add annotations before copying
- **Clipboard Integration**: Automatically copies the final screenshot to clipboard
- **Multiple Implementation Options**: Choose the setup that works best for you

## Quick Start

### Option 1: Shell Script (Simplest)

```bash
# Make executable (if not already)
chmod +x scripts/screenshot-annotate.sh

# Take screenshot and copy to clipboard
./scripts/screenshot-annotate.sh

# Take screenshot with annotation
./scripts/screenshot-annotate.sh --annotate

# ShareX-style mode with window highlighting
./scripts/screenshot-annotate.sh --sharex

# ShareX mode + annotation
./scripts/screenshot-annotate.sh --sharex --annotate
```

The script also auto-detects if Shift is held when invoked (requires Python with Quartz).

### ShareX-Style Mode (Window Highlighting)

For ShareX-like window highlighting behavior, use the `--sharex` flag or run the Python script directly:

```bash
# Install requirements first
pip install pyobjc pyobjc-framework-Quartz pyobjc-framework-Cocoa

# Run ShareX-style screenshot
./scripts/screenshot-sharex.py

# With annotation
./scripts/screenshot-sharex.py --annotate
```

**ShareX Mode Controls:**
- **Move mouse**: Highlight windows under cursor
- **Click**: Capture the highlighted window
- **Drag**: Select a custom region
- **Space**: Toggle between window mode and region mode
- **Escape**: Cancel

### Option 2: Hammerspoon (Recommended for Power Users)

[Hammerspoon](https://www.hammerspoon.org/) provides the best experience with proper hotkey binding.

1. **Install Hammerspoon**:
   ```bash
   brew install --cask hammerspoon
   ```

2. **Add the configuration**:
   ```bash
   # Either copy the entire file as your init.lua
   cp scripts/screenshot-hammerspoon.lua ~/.hammerspoon/init.lua
   
   # Or require it from your existing init.lua
   echo 'require("screenshot-hammerspoon")' >> ~/.hammerspoon/init.lua
   cp scripts/screenshot-hammerspoon.lua ~/.hammerspoon/
   ```

3. **Reload Hammerspoon**: Click the Hammerspoon menu bar icon → Reload Config

4. **Use the hotkeys**:
   - `Cmd+Shift+5`: Take screenshot → copy to clipboard
   - `Cmd+Shift+Ctrl+5`: Take screenshot → annotate → copy to clipboard
   - `Cmd+Alt+S`: Take screenshot (hold Shift additionally for annotation mode)

### Option 3: Automator Quick Action

Best for integration with System Keyboard Shortcuts.

1. **Open Automator** (Applications → Automator)

2. **Create new Quick Action**:
   - Choose "Quick Action" as document type
   - Set "Workflow receives" to "no input" in "any application"

3. **Add "Run AppleScript" action**:
   - Search for "Run AppleScript" in the actions library
   - Drag it to the workflow
   - Copy the contents of `screenshot-annotate.applescript`

4. **Save the Quick Action**:
   - Save as "Screenshot to Clipboard"
   - For annotation version, create another with `property annotateMode : true`

5. **Assign keyboard shortcut**:
   - System Settings → Keyboard → Keyboard Shortcuts → Services
   - Find your Quick Action under "General"
   - Assign a shortcut (e.g., `Cmd+Shift+4` or `Cmd+Shift+Ctrl+4`)

## File Descriptions

| File | Description |
|------|-------------|
| `screenshot-annotate.sh` | Bash wrapper script with all modes (`--annotate`, `--sharex`) |
| `screenshot-sharex.py` | Python app with ShareX-style window highlighting |
| `screenshot-hammerspoon.lua` | Hammerspoon module with hotkey bindings |
| `screenshot-annotate.applescript` | AppleScript for Automator Quick Actions |

## How It Works

### Standard Mode
1. **Screenshot Capture**: Uses macOS's built-in `screencapture` command with `-i` flag for interactive region/window selection

2. **Annotation**: Opens the screenshot in Preview.app, which has built-in markup tools:
   - Shapes (rectangles, circles, arrows)
   - Text annotations
   - Highlighting
   - Drawing tools
   - Signatures

3. **Clipboard Copy**: Reads the PNG file and copies it to the system clipboard using AppleScript or Hammerspoon APIs

### ShareX Mode
1. **Window Detection**: Uses Quartz Window Services API to get all on-screen windows and their bounds

2. **Overlay Display**: Creates transparent overlay windows covering all screens with:
   - Semi-transparent dark overlay
   - Clear "cutout" showing the highlighted window/region
   - Border highlighting and window info labels
   - Mode indicator and instructions

3. **Real-time Tracking**: Monitors mouse position to highlight windows as you hover

4. **Capture**: Uses `CGWindowListCreateImage` for high-quality window/region capture

## Requirements

### For Basic Mode
- macOS (tested on 10.15+)
- Bash shell

### For ShareX Mode
```bash
pip install pyobjc pyobjc-framework-Quartz pyobjc-framework-Cocoa
```

### For Shift Key Detection
```bash
pip install pyobjc-framework-Quartz
```

## Customization

### Changing Hotkeys (Hammerspoon)

Edit `screenshot-hammerspoon.lua`:

```lua
-- Change from Cmd+Shift+5 to your preferred combo
hs.hotkey.bind({"cmd", "shift"}, "5", function()
    screenshot.capture(false)
end)
```

### Using a Different Annotation App

Edit the shell script's `annotate_in_preview` function:

```bash
# For Skitch
open -a Skitch "$image_file"

# For Pixelmator Pro
open -a "Pixelmator Pro" "$image_file"

# For Annotate (if installed)
open -a Annotate "$image_file"
```

### Disabling Notifications

In `screenshot-hammerspoon.lua`:
```lua
screenshot.notifySound = false
```

## Troubleshooting

### "Operation not permitted" errors

Grant permissions in System Settings:
- **Screen Recording**: System Settings → Privacy & Security → Screen Recording → Enable for Terminal/Hammerspoon
- **Accessibility**: System Settings → Privacy & Security → Accessibility → Enable for Hammerspoon (if using)

### Shift detection not working in shell script

The shell script uses Python's Quartz module for modifier key detection. Ensure you have:
```bash
# Check if pyobjc is installed
python3 -c "from Quartz import CGEventSourceFlagsState; print('OK')"

# If not, install it
pip3 install pyobjc-framework-Quartz
```

### Hammerspoon not responding

1. Check Hammerspoon is running (look for icon in menu bar)
2. Reload config: Menu bar icon → Reload Config
3. Check Console.app for Hammerspoon errors

## Tips

- **Quick window capture**: After pressing the screenshot hotkey, press `Space` to switch to window selection mode
- **Cancel screenshot**: Press `Escape` at any time to cancel
- **Preview shortcuts**: 
  - `Cmd+Shift+A` opens the markup toolbar
  - `Cmd+S` saves your annotations
  - `Cmd+W` closes the document

## License

MIT License - Feel free to modify and distribute.

