# Screenshot Tool

A ShareX-style screenshot and screen recording tool for macOS. Highlights windows and UI elements as you hover, supports region selection, annotation via Shottr, and GIF recording.

## Quick Start

### ShareX Mode (Recommended)

Trigger via Alfred hotkey. The tool opens a full-screen overlay where you can:

- **Hover** to highlight windows or UI elements
- **Click** to capture the highlighted target
- **Drag** to select a custom region
- **Space** to cycle modes: Auto → Window → Element
- **Escape** to cancel

Screenshots are saved to `~/Screenshots/YYYY/Month/` and copied to clipboard.

### CLI

```bash
# Screenshot (saves to disk + clipboard)
./screenshot-annotate.sh

# Screenshot with Shottr annotation
./screenshot-annotate.sh --annotate

# Clipboard only (no disk save)
./screenshot-annotate.sh --no-save

# Record a region to GIF
./screenshot-annotate.sh --record

# Open screenshots folder
./screenshot-annotate.sh --open-dir

# Install dependencies
./screenshot-annotate.sh --install
```

### Recording Controls

After selecting a region in `--record` mode:

- **⌘.** (Cmd+Period) to stop and save as GIF
- **Escape** to cancel

## Alfred Setup

Point an Alfred workflow hotkey at `screenshot-annotate.sh`. The shell wrapper handles Python resolution, dependency checks, and concurrency (double-tap safe).

Suggested bindings:

| Hotkey | Command |
|--------|---------|
| `Cmd+Shift+5` | `./screenshot-annotate.sh` |
| `Cmd+Shift+Ctrl+5` | `./screenshot-annotate.sh --annotate` |
| `Cmd+Shift+6` | `./screenshot-annotate.sh --record` |

## Dependencies

- **Python 3** with PyObjC (`pyobjc-core`, `pyobjc-framework-Quartz`, `pyobjc-framework-Cocoa`)
- **ffmpeg** (for GIF recording): `brew install ffmpeg`
- **Shottr** (optional, for annotation): `brew install --cask shottr`

Run `./screenshot-annotate.sh --install` to install Python dependencies.

## Permissions

The tool needs two macOS permissions (System Settings → Privacy & Security):

- **Accessibility** — for event monitoring (keyboard/mouse)
- **Screen Recording** — for capturing screen content

Grant these to your terminal app (iTerm, Terminal) or Alfred.

## File Structure

```
screenshot-tool/
├── screenshot-annotate.sh    # Shell wrapper (Alfred entry point)
├── screenshot-sharex.py      # Main Python app
├── lib/
│   ├── recorder.py           # Screen recording + GIF conversion
│   ├── utils.py              # Notifications, file paths, sound
│   ├── models.py             # WindowInfo, UIElementInfo
│   └── dependencies.py       # Dep checking and installation
└── README.md
```

## Troubleshooting

### "GIF conversion failed"

ffmpeg's Homebrew libraries can break after upgrades. Fix with:

```bash
brew reinstall ffmpeg
```

The tool will detect this and tell you in the notification.

### "Accessibility permission required"

Grant Accessibility to your terminal app, then **restart the terminal**. The permission doesn't take effect until relaunch.

### Screenshots are offset on multi-monitor setups

The tool uses the primary display (origin 0,0) for coordinate conversion. If captures are misaligned, check that your primary display is set correctly in System Settings → Displays → Arrangement.
