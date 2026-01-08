#!/usr/bin/env python3
"""
ShareX-like Screenshot Tool for macOS

Features:
- Window highlighting on hover
- Region selection with crosshairs
- Optional annotation in Preview
- Copy to clipboard

Usage:
    python screenshot-sharex.py              # Normal mode
    python screenshot-sharex.py --annotate   # With annotation
    python screenshot-sharex.py --install    # Install dependencies

Controls:
    - Move mouse to highlight windows
    - Click to capture highlighted window
    - Hold and drag to select custom region
    - Press Space to toggle between window/region mode
    - Press Escape to cancel
"""

import argparse
import os
import sys
import subprocess
import tempfile
from datetime import datetime
from typing import Optional, Tuple, List, NamedTuple

# Required packages for PyObjC
REQUIRED_PACKAGES = [
    "pyobjc-core",
    "pyobjc-framework-Quartz",
    "pyobjc-framework-Cocoa",
]


def check_dependencies() -> bool:
    """Check if all required dependencies are installed."""
    try:
        import objc
        import Quartz
        import AppKit
        return True
    except ImportError:
        return False


def install_dependencies(quiet: bool = False) -> bool:
    """Install required dependencies using pip."""
    if not quiet:
        print("Installing required dependencies...")
        print(f"Packages: {', '.join(REQUIRED_PACKAGES)}")
        print()

    try:
        # Use the same Python interpreter that's running this script
        python_exe = sys.executable

        # Install packages
        cmd = [python_exe, "-m", "pip", "install", "--upgrade"] + REQUIRED_PACKAGES

        if quiet:
            cmd.append("--quiet")

        result = subprocess.run(
            cmd,
            capture_output=not quiet,
            text=True
        )

        if result.returncode == 0:
            if not quiet:
                print("\n✓ Dependencies installed successfully!")
                print("  Please re-run the script to use it.")
            return True
        else:
            if not quiet:
                print(f"\n✗ Failed to install dependencies:")
                print(result.stderr)
            return False

    except Exception as e:
        if not quiet:
            print(f"\n✗ Error installing dependencies: {e}")
        return False


def prompt_install() -> bool:
    """Prompt user to install dependencies."""
    print("=" * 60)
    print("ShareX-style Screenshot Tool - Dependency Setup")
    print("=" * 60)
    print()
    print("This tool requires PyObjC frameworks to access macOS APIs.")
    print()
    print("Required packages:")
    for pkg in REQUIRED_PACKAGES:
        print(f"  • {pkg}")
    print()
    print(f"Python: {sys.executable}")
    print()

    # Check if running interactively
    if sys.stdin.isatty():
        try:
            response = input("Install now? [Y/n]: ").strip().lower()
            if response in ('', 'y', 'yes'):
                return install_dependencies()
            else:
                print("\nTo install manually, run:")
                print(f"  {sys.executable} -m pip install {' '.join(REQUIRED_PACKAGES)}")
                print("\nOr run this script with --install flag:")
                print(f"  {sys.argv[0]} --install")
                return False
        except (EOFError, KeyboardInterrupt):
            print("\nInstallation cancelled.")
            return False
    else:
        # Non-interactive mode
        print("Run with --install flag to install dependencies:")
        print(f"  {sys.argv[0]} --install")
        print()
        print("Or install manually:")
        print(f"  {sys.executable} -m pip install {' '.join(REQUIRED_PACKAGES)}")
        return False


# Check for --install flag early (before importing PyObjC)
if "--install" in sys.argv:
    success = install_dependencies()
    sys.exit(0 if success else 1)

# Check for --check-installed flag for debugging
if "--check-installed" in sys.argv:
    print("Checking PyObjC installation status...")
    print(f"Python: {sys.executable}")
    print()

    packages_status = []
    for pkg in ["objc", "Quartz", "AppKit", "Foundation"]:
        try:
            __import__(pkg)
            packages_status.append((pkg, "✓ OK"))
        except ImportError as e:
            packages_status.append((pkg, f"✗ {e}"))

    print("Package status:")
    for pkg, status in packages_status:
        print(f"  {pkg}: {status}")

    all_ok = all("OK" in status for _, status in packages_status)
    sys.exit(0 if all_ok else 1)

# Try to import PyObjC modules
_import_error = None
try:
    import objc
    from AppKit import (
        NSApplication,
        NSWindow,
        NSView,
        NSColor,
        NSBezierPath,
        NSScreen,
        NSEvent,
        NSLeftMouseDownMask,
        NSLeftMouseUpMask,
        NSLeftMouseDraggedMask,
        NSMouseMovedMask,
        NSKeyDownMask,
        NSFlagsChangedMask,
        NSApplicationActivationPolicyAccessory,
        NSBorderlessWindowMask,
        NSStatusWindowLevel,
        NSBackingStoreBuffered,
        NSFont,
        NSFontAttributeName,
        NSForegroundColorAttributeName,
        NSTrackingArea,
        NSTrackingMouseMoved,
        NSTrackingActiveAlways,
        NSTrackingInVisibleRect,
        NSCursor,
        NSImage,
        NSPasteboard,
        NSPasteboardTypePNG,
        NSGraphicsContext,
        NSCompositeCopy,
        NSAttributedString,
    )
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGWindowListOptionIncludingWindow,
        kCGWindowListExcludeDesktopElements,
        kCGNullWindowID,
        CGWindowListCreateImage,
        kCGWindowImageDefault,
        kCGWindowImageBoundsIgnoreFraming,
        CGRectMake,
        CGRectNull,
        CGMainDisplayID,
        CGDisplayBounds,
        CGEventSourceFlagsState,
        kCGEventSourceStateHIDSystemState,
        kCGEventFlagMaskShift,
        CGPreflightListenEventAccess,
        CGRequestListenEventAccess,
        # For CGEventTap
        CGEventTapCreate,
        CGEventTapEnable,
        kCGSessionEventTap,
        kCGHeadInsertEventTap,
        kCGEventTapOptionDefault,
        CGEventMaskBit,
        kCGEventKeyDown,
        kCGEventLeftMouseDown,
        kCGEventLeftMouseUp,
        kCGEventMouseMoved,
        kCGEventLeftMouseDragged,
        CGEventGetIntegerValueField,
        kCGKeyboardEventKeycode,
        CFMachPortCreateRunLoopSource,
        CFRunLoopGetCurrent,
        CFRunLoopAddSource,
        kCFRunLoopCommonModes,
    )
    from Foundation import (
        NSMakeRect,
        NSMakePoint,
        NSMakeSize,
        NSZeroRect,
        NSMutableDictionary,
        NSRunLoop,
        NSDefaultRunLoopMode,
        NSDate,
        NSTimer,
        NSObject,
    )
    # Accessibility API for UI element detection
    from ApplicationServices import (
        AXUIElementCreateSystemWide,
        AXUIElementCopyElementAtPosition,
        AXUIElementCopyAttributeValue,
        AXUIElementGetPid,
        AXUIElementCreateApplication,
        kAXErrorSuccess,
    )
    # Accessibility attribute constants (these are string constants)
    kAXRoleAttribute = "AXRole"
    kAXTitleAttribute = "AXTitle"
    kAXPositionAttribute = "AXPosition"
    kAXSizeAttribute = "AXSize"
    kAXFocusedAttribute = "AXFocused"
    kAXChildrenAttribute = "AXChildren"
except ImportError as e:
    _import_error = e

# Handle import failure
if _import_error:
    # Check if packages are actually installed (might be a sandbox/permission issue)
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import objc; print('ok')"],
            capture_output=True,
            text=True,
            timeout=5
        )
        packages_installed = result.returncode == 0 and "ok" in result.stdout
    except Exception:
        packages_installed = False

    if packages_installed:
        # Packages are installed but import failed - likely sandbox issue
        print("=" * 60)
        print("ERROR: PyObjC packages are installed but cannot be loaded")
        print("=" * 60)
        print()
        print(f"Import error: {_import_error}")
        print()
        print("This usually happens when running in a sandboxed environment")
        print("(like Cursor's terminal) that restricts native library loading.")
        print()
        print("Try running the script directly from Terminal.app instead:")
        print(f"  {sys.argv[0]}")
        print()
        sys.exit(1)
    else:
        # Dependencies not installed - prompt to install
        if prompt_install():
            print("\nPlease re-run the script now.")
        sys.exit(1)


class WindowInfo(NamedTuple):
    """Information about a window."""
    window_id: int
    owner_name: str
    window_name: str
    bounds: Tuple[float, float, float, float]  # x, y, width, height
    layer: int


class UIElementInfo(NamedTuple):
    """Information about a UI element within a window."""
    role: str  # e.g., "AXButton", "AXTab", "AXTextField"
    title: str
    bounds: Tuple[float, float, float, float]  # x, y, width, height
    ax_element: object  # The AXUIElement reference


def check_accessibility_permissions() -> bool:
    """Check if the app has accessibility permissions for event monitoring."""
    try:
        # Try the Quartz method first (more reliable)
        if not CGPreflightListenEventAccess():
            print("\n" + "=" * 60)
            print("⚠️  ACCESSIBILITY PERMISSION REQUIRED")
            print("=" * 60)
            print()
            print("This app needs permission to monitor keyboard and mouse events.")
            print()
            print("To grant permission:")
            print("  1. Open System Settings (or System Preferences on older macOS)")
            print("  2. Go to: Privacy & Security → Accessibility")
            print("  3. Click the 🔒 lock icon to make changes")
            print("  4. Click + and add your terminal app (iTerm or Terminal)")
            print("  5. Make sure the checkbox is ✓ enabled")
            print("  6. RESTART your terminal app")
            print("  7. Run this script again")
            print()
            print("Or run this command to open the settings directly:")
            print('  open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"')
            print()

            # Try multiple methods to open System Settings
            opened = False

            # Method 1: Direct URL scheme (macOS Ventura+)
            if not opened:
                result = os.system('open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility" 2>/dev/null')
                if result == 0:
                    opened = True

            # Method 2: System Preferences app (older macOS)
            if not opened:
                result = os.system('open "/System/Applications/System Preferences.app" 2>/dev/null')
                if result == 0:
                    opened = True

            # Method 3: System Settings app (macOS Ventura+)
            if not opened:
                os.system('open "/System/Applications/System Settings.app" 2>/dev/null')

            # Request access (may show system prompt on some macOS versions)
            try:
                CGRequestListenEventAccess()
            except Exception:
                pass

            return False
        return True
    except Exception as e:
        print(f"Warning: Could not check accessibility permissions: {e}")
        # Can't check, let's try to continue anyway
        return True


class ScreenshotApp:
    """Main screenshot application."""

    def __init__(self, annotate: bool = False, save_to_disk: bool = True):
        self.annotate = annotate
        self.save_to_disk = save_to_disk
        self.app = NSApplication.sharedApplication()
        self.app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

        self.windows: List[WindowInfo] = []
        self.highlighted_window: Optional[WindowInfo] = None
        self.highlighted_element: Optional[UIElementInfo] = None
        self.is_dragging = False
        self.drag_start: Optional[Tuple[float, float]] = None
        self.drag_current: Optional[Tuple[float, float]] = None
        # Modes: "auto" = smart (element > window, drag for region), "window", "element", "region"
        self.capture_mode = "auto"
        self._annotation_active = False
        self.should_quit = False
        self.captured = False

        # Event monitoring
        self.event_tap = None
        self.event_monitor = None
        self.local_monitor = None
        self._debug = os.environ.get('DEBUG', '0') == '1'

        # System-wide accessibility element
        self.system_wide_element = AXUIElementCreateSystemWide()

        if self._debug:
            print(f"System-wide AX element: {self.system_wide_element}")

        # Create overlay windows for each screen
        self.overlay_windows = []
        self.overlay_views = []
        self._create_overlays()

        # Refresh window list
        self._refresh_windows()

        # Set up event monitoring
        self._setup_event_monitors()

    def _create_overlays(self):
        """Create transparent overlay windows for each screen."""
        print(f"Creating overlays for {len(NSScreen.screens())} screen(s)...")

        for i, screen in enumerate(NSScreen.screens()):
            frame = screen.frame()
            print(f"  Screen {i}: {frame.size.width}x{frame.size.height} at ({frame.origin.x}, {frame.origin.y})")

            # Create overlay window
            window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                frame,
                NSBorderlessWindowMask,
                NSBackingStoreBuffered,
                False
            )
            window.setLevel_(NSStatusWindowLevel + 1000)
            window.setOpaque_(False)
            window.setBackgroundColor_(NSColor.clearColor())
            # Allow mouse events to pass through to other windows
            # We'll use global event monitoring to track mouse position
            window.setIgnoresMouseEvents_(True)
            window.setAcceptsMouseMovedEvents_(True)
            window.setHasShadow_(False)
            window.setCollectionBehavior_(1 << 6)  # NSWindowCollectionBehaviorCanJoinAllSpaces

            # Create custom view
            view = OverlayView.alloc().initWithFrame_(NSMakeRect(0, 0, frame.size.width, frame.size.height))
            view.app = self
            window.setContentView_(view)

            window.makeKeyAndOrderFront_(None)

            self.overlay_windows.append(window)
            self.overlay_views.append(view)

        print(f"  Created {len(self.overlay_windows)} overlay window(s)")

    def _refresh_windows(self):
        """Refresh the list of on-screen windows."""
        self.windows = []

        options = kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements
        window_list = CGWindowListCopyWindowInfo(options, kCGNullWindowID)

        if window_list:
            for window_info in window_list:
                # Skip our own overlay windows
                owner = window_info.get('kCGWindowOwnerName', '')
                if owner == 'Python' or owner == 'python3':
                    continue

                # Get window bounds
                bounds_dict = window_info.get('kCGWindowBounds', {})
                if not bounds_dict:
                    continue

                x = bounds_dict.get('X', 0)
                y = bounds_dict.get('Y', 0)
                width = bounds_dict.get('Width', 0)
                height = bounds_dict.get('Height', 0)

                # Skip tiny windows
                if width < 10 or height < 10:
                    continue

                window = WindowInfo(
                    window_id=window_info.get('kCGWindowNumber', 0),
                    owner_name=owner,
                    window_name=window_info.get('kCGWindowName', ''),
                    bounds=(x, y, width, height),
                    layer=window_info.get('kCGWindowLayer', 0)
                )
                self.windows.append(window)

    def _setup_event_monitors(self):
        """Set up global event monitors using CGEventTap for reliable key capture."""
        print("Setting up event monitors...")

        debug = os.environ.get('DEBUG', '0') == '1'
        self._debug = debug

        # Store reference to self for the callback
        app_ref = self

        # CGEventTap callback
        def cg_event_callback(proxy, event_type, event, refcon):
            try:
                # Skip all events if annotation is active
                if app_ref._annotation_active:
                    return event

                if debug:
                    print(f"CGEvent type: {event_type}")

                # Key down event
                if event_type == kCGEventKeyDown:
                    keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
                    if debug:
                        print(f"Key pressed: {keycode}")

                    # Escape key (keycode 53)
                    if keycode == 53:
                        print("Escape pressed - exiting")
                        app_ref.should_quit = True
                        return None  # Consume the event

                    # Space key (keycode 49) - cycle through modes
                    elif keycode == 49:
                        modes = ["auto", "window", "element", "region"]
                        current_idx = modes.index(app_ref.capture_mode) if app_ref.capture_mode in modes else 0
                        app_ref.capture_mode = modes[(current_idx + 1) % len(modes)]
                        mode_names = {"auto": "Auto (Smart)", "window": "Window Only", "element": "Element Only", "region": "Region Only"}
                        print(f"Mode: {mode_names[app_ref.capture_mode]}")
                        app_ref._update_overlays()
                        return None  # Consume the event

                # Mouse events
                elif event_type == kCGEventMouseMoved or event_type == kCGEventLeftMouseDragged:
                    app_ref._handle_mouse_move(None)

                elif event_type == kCGEventLeftMouseDown:
                    if debug:
                        print("Mouse down")
                    app_ref._handle_mouse_down(None)

                elif event_type == kCGEventLeftMouseUp:
                    if debug:
                        print("Mouse up")
                    app_ref._handle_mouse_up(None)

            except Exception as e:
                print(f"Event callback error: {e}")
                import traceback
                traceback.print_exc()

            return event

        # Create event mask for the events we want to capture
        event_mask = (
            CGEventMaskBit(kCGEventKeyDown) |
            CGEventMaskBit(kCGEventLeftMouseDown) |
            CGEventMaskBit(kCGEventLeftMouseUp) |
            CGEventMaskBit(kCGEventMouseMoved) |
            CGEventMaskBit(kCGEventLeftMouseDragged)
        )

        # Create the event tap
        self.event_tap = CGEventTapCreate(
            kCGSessionEventTap,      # Tap at session level
            kCGHeadInsertEventTap,   # Insert at head
            kCGEventTapOptionDefault, # Default options (can modify events)
            event_mask,
            cg_event_callback,
            None  # User info
        )

        if self.event_tap:
            print("  CGEventTap: OK")

            # Create a run loop source and add it to the current run loop
            run_loop_source = CFMachPortCreateRunLoopSource(None, self.event_tap, 0)
            CFRunLoopAddSource(CFRunLoopGetCurrent(), run_loop_source, kCFRunLoopCommonModes)

            # Enable the tap
            CGEventTapEnable(self.event_tap, True)
            print("  Event tap enabled")
        else:
            print("  CGEventTap: FAILED")
            print("  ⚠️  Make sure you have granted Accessibility permissions!")

        # Also set up NSEvent monitors as backup for mouse movement
        mask = 0xFFFFFFFF
        self._ns_mask = mask

        def ns_event_handler(event):
            try:
                event_type = event.type()
                # Mouse moved (type 5) or dragged (type 6)
                if event_type in (5, 6):
                    app_ref._handle_mouse_move(event)
            except:
                pass
            return event

        self._ns_event_handler = ns_event_handler

        self.event_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            mask, ns_event_handler
        )
        self.local_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
            mask, ns_event_handler
        )

        if self.event_monitor:
            print("  NSEvent global monitor: OK")
        if self.local_monitor:
            print("  NSEvent local monitor: OK")

    def _disable_event_monitoring(self):
        """Disable all event monitoring."""
        # Disable event tap
        if self.event_tap:
            try:
                CGEventTapEnable(self.event_tap, False)
            except:
                pass

        # Remove NSEvent monitors
        if self.event_monitor:
            NSEvent.removeMonitor_(self.event_monitor)
            self.event_monitor = None
        if self.local_monitor:
            NSEvent.removeMonitor_(self.local_monitor)
            self.local_monitor = None

    def _enable_event_monitoring(self):
        """Re-enable event monitoring."""
        # Re-create the event tap
        if self.event_tap is None and hasattr(self, '_event_callback'):
            self.event_tap = CGEventTapCreate(
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                kCGEventTapOptionDefault,
                self._event_mask,
                self._event_callback,
                None
            )

            if self.event_tap and hasattr(self, '_run_loop_source'):
                CFRunLoopAddSource(CFRunLoopGetCurrent(), self._run_loop_source, kCFRunLoopCommonModes)
                CGEventTapEnable(self.event_tap, True)

        # Re-create NSEvent monitors
        if self.event_monitor is None and hasattr(self, '_ns_mask'):
            self.event_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                self._ns_mask, self._ns_event_handler
            )

        if self.local_monitor is None and hasattr(self, '_ns_mask'):
            self.local_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
                self._ns_mask, self._ns_event_handler
            )

    def _handle_mouse_move(self, event):
        """Handle mouse movement."""
        location = NSEvent.mouseLocation()
        screen_y = self._flip_y(location.y)

        if self.is_dragging:
            self.drag_current = (location.x, screen_y)
        elif self.capture_mode == "auto":
            # Auto mode: find both element and window
            self._find_element_at(location.x, screen_y)
            self._find_window_at(location.x, screen_y)

            # Only prefer element if it's significantly smaller than the window
            # (i.e., it's actually a sub-element, not the window itself)
            if self.highlighted_element and self.highlighted_window:
                elem_bounds = self.highlighted_element.bounds
                win_bounds = self.highlighted_window.bounds

                elem_area = elem_bounds[2] * elem_bounds[3]
                win_area = win_bounds[2] * win_bounds[3]

                # If element is more than 80% of window size, it's probably the window itself
                if win_area > 0 and elem_area / win_area > 0.8:
                    self.highlighted_element = None  # Treat as window instead
                    if self._debug:
                        print(f"Auto: Window (element too large) - {self.highlighted_window.owner_name}")
                elif self._debug:
                    print(f"Auto: Element - {self.highlighted_element.role}")
            elif self._debug:
                if self.highlighted_window:
                    print(f"Auto: Window - {self.highlighted_window.owner_name}")
        elif self.capture_mode == "element":
            # Find UI element under cursor
            self._find_element_at(location.x, screen_y)
            self._find_window_at(location.x, screen_y)

            if self._debug and self.highlighted_element:
                print(f"Element: {self.highlighted_element.role} - {self.highlighted_element.title}")
        elif self.capture_mode == "window":
            # Find window under cursor
            self._find_window_at(location.x, screen_y)
            self.highlighted_element = None  # Clear element in window-only mode

            if self.highlighted_window and self._debug:
                print(f"Window: {self.highlighted_window.owner_name}")
        elif self.capture_mode == "region":
            # Region mode - clear highlights, only drag works
            self.highlighted_element = None
            self.highlighted_window = None

        self._update_overlays()

    def _handle_mouse_down(self, event):
        """Handle mouse down - start drag for region selection."""
        location = NSEvent.mouseLocation()

        # In all modes, mouse down starts a potential drag for region selection
        # If user just clicks (no drag), we'll capture on mouse up
        self.is_dragging = True
        self.drag_start = (location.x, self._flip_y(location.y))
        self.drag_current = self.drag_start

    def _handle_mouse_up(self, event):
        """Handle mouse up - complete capture."""
        captured = False

        if self.is_dragging and self.drag_start and self.drag_current:
            x1, y1 = self.drag_start
            x2, y2 = self.drag_current

            # Calculate drag distance
            width = abs(x2 - x1)
            height = abs(y2 - y1)

            # If dragged more than 10 pixels, treat as region selection
            if width > 10 or height > 10:
                if width > 5 and height > 5:
                    x = min(x1, x2)
                    y = min(y1, y2)
                    self._capture_region(x, y, width, height)
                    captured = True

        # If not a drag (just a click), capture highlighted item
        if not captured:
            if self.capture_mode == "auto":
                # Auto mode: prefer element, fall back to window
                if self.highlighted_element:
                    self._capture_element(self.highlighted_element)
                elif self.highlighted_window:
                    self._capture_window(self.highlighted_window)
            elif self.capture_mode == "element" and self.highlighted_element:
                self._capture_element(self.highlighted_element)
            elif self.capture_mode == "window" and self.highlighted_window:
                self._capture_window(self.highlighted_window)
            # Region mode only captures via drag, clicks do nothing

        self.is_dragging = False
        self.drag_start = None
        self.drag_current = None

    def _find_window_at(self, x: float, y: float):
        """Find the window at the given screen coordinates."""
        self.highlighted_window = None

        for window in self.windows:
            wx, wy, ww, wh = window.bounds
            if wx <= x <= wx + ww and wy <= y <= wy + wh:
                self.highlighted_window = window
                break

    def _find_element_at(self, x: float, y: float):
        """Find the UI element at the given screen coordinates using Accessibility API."""
        self.highlighted_element = None

        try:
            # Get the element at this position
            # Try different calling conventions for AXUIElementCopyElementAtPosition
            try:
                # Method 1: Returns (error, element) tuple
                result = AXUIElementCopyElementAtPosition(
                    self.system_wide_element,
                    float(x), float(y),
                    None
                )

                if isinstance(result, tuple) and len(result) == 2:
                    error, element = result
                elif isinstance(result, int):
                    error = result
                    element = None
                else:
                    error = -1
                    element = result

            except TypeError:
                # Method 2: element passed as byref
                from ctypes import c_void_p, byref
                element_ptr = c_void_p()
                error = AXUIElementCopyElementAtPosition(
                    self.system_wide_element,
                    float(x), float(y),
                    byref(element_ptr)
                )
                element = element_ptr.value

            if error != kAXErrorSuccess or element is None:
                return

            # Get element attributes
            role = self._get_ax_attribute(element, kAXRoleAttribute) or "Unknown"
            title = self._get_ax_attribute(element, kAXTitleAttribute) or ""

            # Get position and size
            position = self._get_ax_attribute(element, kAXPositionAttribute)
            size = self._get_ax_attribute(element, kAXSizeAttribute)


            if position is not None and size is not None:
                # Extract values from AXValue objects using Quartz functions
                try:
                    from Quartz import AXValueGetValue, kAXValueTypeCGPoint, kAXValueTypeCGSize
                    from Quartz import CGPoint, CGSize

                    # Create mutable structures to receive the values
                    point = CGPoint()
                    size_val = CGSize()

                    # Extract point
                    if AXValueGetValue(position, kAXValueTypeCGPoint, point):
                        pos_x = point.x
                        pos_y = point.y
                    else:
                        pos_x, pos_y = self._parse_ax_value(position)

                    # Extract size
                    if AXValueGetValue(size, kAXValueTypeCGSize, size_val):
                        width = size_val.width
                        height = size_val.height
                    else:
                        width, height = self._parse_ax_value(size)

                except ImportError:
                    # Fallback to parsing
                    pos_x, pos_y = self._parse_ax_value(position)
                    width, height = self._parse_ax_value(size)
                except Exception as e:
                    if self._debug:
                        print(f"AXValue extraction error: {e}")
                    pos_x, pos_y = self._parse_ax_value(position)
                    width, height = self._parse_ax_value(size)

                if self._debug:
                    print(f"Parsed: pos=({pos_x}, {pos_y}), size=({width}, {height})")

                # Only highlight if element has reasonable size
                if width > 5 and height > 5:
                    self.highlighted_element = UIElementInfo(
                        role=role,
                        title=title,
                        bounds=(pos_x, pos_y, width, height),
                        ax_element=element
                    )
        except Exception as e:
            if self._debug:
                print(f"Element detection error: {e}")
                import traceback
                traceback.print_exc()

    def _parse_ax_value(self, value):
        """Parse position or size from AXValue string representation."""
        import re
        val_str = str(value)

        # Try different formats
        # Format: "x:123.0 y:456.0" or "w:100.0 h:200.0"
        xy_match = re.search(r'x:([\d.-]+).*y:([\d.-]+)', val_str)
        if xy_match:
            return float(xy_match.group(1)), float(xy_match.group(2))

        wh_match = re.search(r'w:([\d.-]+).*h:([\d.-]+)', val_str)
        if wh_match:
            return float(wh_match.group(1)), float(wh_match.group(2))

        # Format: "{123, 456}" (CGPoint/CGSize)
        cg_match = re.search(r'\{([\d.-]+),\s*([\d.-]+)\}', val_str)
        if cg_match:
            return float(cg_match.group(1)), float(cg_match.group(2))

        return 0, 0

    def _get_ax_attribute(self, element, attribute):
        """Get an accessibility attribute value from an element."""
        try:
            # Try calling AXUIElementCopyAttributeValue
            result = AXUIElementCopyAttributeValue(element, attribute, None)

            # Handle different return formats
            if isinstance(result, tuple):
                error = result[0]
                value = result[1] if len(result) > 1 else None
            else:
                # Might just return the value directly
                error = kAXErrorSuccess
                value = result

            if error == kAXErrorSuccess and value is not None:
                return value

            if self._debug and attribute in (kAXPositionAttribute, kAXSizeAttribute):
                print(f"  _get_ax_attribute({attribute}): error={error}, result type={type(result)}")

        except Exception as e:
            if self._debug:
                print(f"  _get_ax_attribute({attribute}) exception: {e}")
        return None

    def _flip_y(self, y: float) -> float:
        """Convert from NSScreen coordinates (bottom-left origin) to CGWindow coordinates (top-left origin)."""
        main_screen = NSScreen.mainScreen()
        if main_screen:
            return main_screen.frame().size.height - y
        return y

    def _update_overlays(self):
        """Request redraw of all overlay views."""
        for view in self.overlay_views:
            view.setNeedsDisplay_(True)

    def _capture_window(self, window: WindowInfo):
        """Capture a specific window."""
        x, y, width, height = window.bounds
        self._capture_region(x, y, width, height, window_id=window.window_id)

    def _capture_element(self, element: UIElementInfo):
        """Capture a specific UI element."""
        x, y, width, height = element.bounds
        # Capture as a region (elements don't have window IDs)
        self._capture_region(x, y, width, height)

    def _capture_region(self, x: float, y: float, width: float, height: float, window_id: int = 0):
        """Capture a screen region and copy to clipboard."""
        # Hide overlays before capture
        for window in self.overlay_windows:
            window.orderOut_(None)

        # Small delay to ensure overlays are hidden
        NSRunLoop.currentRunLoop().runUntilDate_(
            NSDate.dateWithTimeIntervalSinceNow_(0.1)
        )

        # Capture the region
        rect = CGRectMake(x, y, width, height)

        if window_id:
            # Capture specific window only (not what's behind it)
            image = CGWindowListCreateImage(
                CGRectNull,  # Use CGRectNull to capture the entire window
                kCGWindowListOptionIncludingWindow,  # Capture just this window
                window_id,
                kCGWindowImageDefault | kCGWindowImageBoundsIgnoreFraming
            )
        else:
            # Capture region from all windows (composite of everything on screen)
            image = CGWindowListCreateImage(
                rect,
                kCGWindowListOptionOnScreenOnly,
                kCGNullWindowID,
                kCGWindowImageDefault
            )

        if image:
            # Convert CGImage to NSImage
            ns_image = NSImage.alloc().initWithCGImage_size_(image, NSMakeSize(width, height))

            # Save to temp file
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = os.path.join(temp_dir, f"screenshot_{timestamp}.png")

            # Get PNG data
            tiff_data = ns_image.TIFFRepresentation()
            if tiff_data:
                from AppKit import NSBitmapImageRep
                bitmap_rep = NSBitmapImageRep.imageRepWithData_(tiff_data)
                png_data = bitmap_rep.representationUsingType_properties_(4, None)  # 4 = NSPNGFileType

                if png_data:
                    png_data.writeToFile_atomically_(temp_path, True)

                    # Save to disk if requested (before annotation so we can save the annotated version)
                    saved_path = None
                    if self.save_to_disk:
                        if self.annotate:
                            # For annotated screenshots, save after annotation (from clipboard)
                            pass  # We'll save after annotation
                        else:
                            # For non-annotated screenshots, save the temp file
                            saved_path = self._save_to_disk(temp_path)

                    if self.annotate:
                        self._annotate_image(temp_path)

                    # Save annotated version to disk if requested
                    if self.save_to_disk and self.annotate:
                        saved_path = self._save_from_clipboard()

                    self._copy_to_clipboard(temp_path)

                    # Show notification
                    if saved_path:
                        self._show_notification(f"Screenshot saved to {os.path.basename(saved_path)} and copied to clipboard!")
                    else:
                        self._show_notification("Screenshot copied to clipboard!")

                    # Cleanup
                    try:
                        os.remove(temp_path)
                    except:
                        pass

        self.captured = True
        self.should_quit = True

    def _is_shottr_installed(self) -> bool:
        """Check if Shottr is installed."""
        shottr_paths = [
            "/Applications/Shottr.app",
            os.path.expanduser("~/Applications/Shottr.app"),
        ]
        return any(os.path.exists(p) for p in shottr_paths)

    def _install_shottr(self) -> bool:
        """Attempt to install Shottr via Homebrew."""
        from AppKit import NSAlert

        # Check if Homebrew is installed
        brew_installed = os.path.exists("/opt/homebrew/bin/brew") or os.path.exists("/usr/local/bin/brew")

        if not brew_installed:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Shottr Not Installed")
            alert.setInformativeText_("Shottr is not installed and Homebrew is not available for automatic installation.\n\nPlease install manually from: https://shottr.cc/")
            alert.addButtonWithTitle_("Open Website")
            alert.addButtonWithTitle_("Use Preview Instead")

            if alert.runModal() == 1000:  # First button
                os.system('open "https://shottr.cc/"')
            return False

        # Ask user if they want to install
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Install Shottr?")
        alert.setInformativeText_("Shottr is a free screenshot annotation tool that's much better than Preview.\n\nWould you like to install it now via Homebrew?\n\n(This may take a minute)")
        alert.addButtonWithTitle_("Install Shottr")
        alert.addButtonWithTitle_("Use Preview Instead")

        if alert.runModal() != 1000:  # Not first button
            return False

        print("Installing Shottr via Homebrew...")
        result = os.system("brew install --cask shottr")

        if result == 0 and self._is_shottr_installed():
            print("✓ Shottr installed successfully!")

            # Show success message
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Shottr Installed!")
            alert.setInformativeText_("Shottr has been installed successfully.\n\nAnnotation shortcuts:\n• 'a' - Arrow\n• 't' - Text\n• 'r' - Rectangle\n• 'h' - Highlight\n• 'b' - Blur")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return True
        else:
            print("✗ Failed to install Shottr")
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Installation Failed")
            alert.setInformativeText_("Failed to install Shottr. You can install it manually from:\nhttps://shottr.cc/")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return False

    def _annotate_image(self, filepath: str):
        """Open image in Shottr (or Preview as fallback) for annotation."""
        from AppKit import NSAlert

        # Check if Shottr is installed, offer to install if not
        if not self._is_shottr_installed():
            if not self._install_shottr():
                # User declined or install failed, use Preview
                print("Using Preview for annotations...")
                os.system(f'open -a Preview "{filepath}"')

                alert = NSAlert.alloc().init()
                alert.setMessageText_("Annotation Mode (Preview)")
                alert.setInformativeText_("Make your annotations in Preview, then save (⌘S) and click OK.")
                alert.addButtonWithTitle_("OK")
                alert.addButtonWithTitle_("Cancel")
                alert.runModal()

                os.system('osascript -e \'tell application "Preview" to close front document saving no\' 2>/dev/null')
                return

        # DISABLE event monitoring during annotation to prevent clicks from triggering capture
        print("Pausing event monitoring for annotation...")
        self._annotation_active = True
        self._disable_event_monitoring()

        try:
            # Get clipboard state before opening Shottr
            from AppKit import NSPasteboard, NSPasteboardTypePNG
            pasteboard = NSPasteboard.generalPasteboard()
            initial_clipboard_count = pasteboard.changeCount()

            # Use Shottr - open the file with the standard macOS open command
            os.system(f'open -a Shottr "{filepath}"')

            print("Shottr opened. Make your annotations and save (⌘S)")
            print("Shottr automatically copies to clipboard when you save!")
            print("Waiting for clipboard to update... (or press Escape to cancel)")

            # Monitor clipboard for changes (Shottr saves to clipboard)
            import time
            from Foundation import NSRunLoop, NSDate

            start_time = time.time()
            while time.time() - start_time < 300:  # 5 minute timeout
                # Process pending events (required for clipboard updates when running from Alfred)
                NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))

                # Check if clipboard changed (indicating Shottr saved)
                current_count = pasteboard.changeCount()
                if current_count != initial_clipboard_count:
                    # Verify it's an image
                    if pasteboard.dataForType_(NSPasteboardTypePNG):
                        print("✓ Clipboard updated - annotation complete!")
                        break

                # Check for Escape key only if running interactively (has a TTY)
                if sys.stdin.isatty():
                    import select
                    try:
                        if select.select([sys.stdin], [], [], 0)[0]:
                            key = sys.stdin.read(1)
                            if ord(key) == 27:  # Escape
                                print("✓ Annotation cancelled")
                                break
                    except (OSError, IOError):
                        pass  # Ignore stdin errors in non-interactive mode

                time.sleep(0.1)  # Poll every 100ms

        except KeyboardInterrupt:
            print("✓ Annotation cancelled")
        finally:
            # RE-ENABLE event monitoring
            print("Resuming event monitoring...")
            self._annotation_active = False
            self._enable_event_monitoring()

    def _get_next_screenshot_number(self, screenshots_dir: str) -> int:
        """Find the next available sequential number for screenshots in the directory."""
        import re

        max_num = 0
        pattern = re.compile(r'^screenshot-(\d+)\.png$')

        if os.path.exists(screenshots_dir):
            for filename in os.listdir(screenshots_dir):
                match = pattern.match(filename)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num

        return max_num + 1

    def _save_to_disk(self, filepath: str):
        """Save screenshot to ~/Screenshots/YYYY/MMM/ folder structure."""
        import datetime
        import shutil

        try:
            # Get current date
            now = datetime.datetime.now()
            year = now.strftime("%Y")
            month = now.strftime("%B")  # January, February, March, etc.

            # Create folder path
            screenshots_dir = os.path.expanduser(f"~/Screenshots/{year}/{month}")

            # Create directories if they don't exist
            os.makedirs(screenshots_dir, exist_ok=True)

            # Generate sequential filename
            next_num = self._get_next_screenshot_number(screenshots_dir)
            filename = f"screenshot-{next_num}.png"
            dest_path = os.path.join(screenshots_dir, filename)

            # Copy the file
            shutil.copy2(filepath, dest_path)

            print(f"✓ Screenshot saved to: {dest_path}")
            return dest_path

        except Exception as e:
            print(f"✗ Failed to save screenshot: {e}")
            return None

    def _save_from_clipboard(self):
        """Save the current clipboard image to ~/Screenshots/YYYY/MonthName/ folder structure."""
        import datetime

        try:
            # Get current date
            now = datetime.datetime.now()
            year = now.strftime("%Y")
            month = now.strftime("%B")  # January, February, March, etc.

            # Create folder path
            screenshots_dir = os.path.expanduser(f"~/Screenshots/{year}/{month}")

            # Create directories if they don't exist
            os.makedirs(screenshots_dir, exist_ok=True)

            # Generate sequential filename
            next_num = self._get_next_screenshot_number(screenshots_dir)
            filename = f"screenshot-{next_num}.png"
            dest_path = os.path.join(screenshots_dir, filename)

            # Get image from clipboard
            pasteboard = NSPasteboard.generalPasteboard()
            if pasteboard.dataForType_(NSPasteboardTypePNG):
                # Read image data from clipboard
                image_data = pasteboard.dataForType_(NSPasteboardTypePNG)
                if image_data:
                    # Write to file
                    image_data.writeToFile_atomically_(dest_path, True)
                    print(f"✓ Annotated screenshot saved to: {dest_path}")
                    return dest_path

            print("✗ No image data found in clipboard")
            return None

        except Exception as e:
            print(f"✗ Failed to save annotated screenshot: {e}")
            return None

    def _copy_to_clipboard(self, filepath: str):
        """Copy image file to clipboard."""
        image = NSImage.alloc().initWithContentsOfFile_(filepath)
        if image:
            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            pasteboard.writeObjects_([image])

    def _show_notification(self, message: str):
        """Show a system notification."""
        os.system(f'osascript -e \'display notification "{message}" with title "Screenshot"\'')

    def run(self, timeout: float = 30.0):
        """Run the application with optional timeout.

        Args:
            timeout: Maximum seconds to wait before auto-exit (default 30s, 0 = no timeout)
        """
        import time

        print("\n" + "=" * 50)
        print("ShareX Screenshot Tool")
        print("=" * 50)
        print(f"  Windows detected: {len(self.windows)}")
        print(f"  Timeout: {timeout}s" if timeout > 0 else "  Timeout: disabled")
        print()
        print("Controls:")
        print("  - Move mouse to highlight (element if found, else window)")
        print("  - Click to capture highlighted item")
        print("  - Drag to select a custom region")
        print("  - Space to cycle mode: Auto → Window → Element → Region")
        print("  - Escape to cancel")
        print("=" * 50)
        print()

        # Activate app
        self.app.activateIgnoringOtherApps_(True)

        start_time = time.time()

        # Run loop
        while not self.should_quit:
            NSRunLoop.currentRunLoop().runUntilDate_(
                NSDate.dateWithTimeIntervalSinceNow_(0.016)  # ~60fps
            )

            # Check timeout
            if timeout > 0:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    print(f"\nTimeout after {timeout} seconds. Exiting...")
                    self.should_quit = True

        # Cleanup
        print("Cleaning up...")

        self._disable_event_monitoring()

        # Close overlay windows
        for window in self.overlay_windows:
            window.close()

        return self.captured


class OverlayView(NSView):
    """Custom view for drawing the overlay."""

    app = None

    def drawRect_(self, rect):
        """Draw the overlay."""
        if not self.app:
            return

        # Get drawing context
        context = NSGraphicsContext.currentContext()
        if not context:
            return

        # Clear background
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(self.bounds())

        # Draw semi-transparent overlay
        overlay_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.3)
        overlay_color.set()
        NSBezierPath.fillRect_(self.bounds())

        # Get screen info for coordinate conversion
        screen = self.window().screen()
        if not screen:
            return
        screen_frame = screen.frame()

        # Draw highlighted window, element, or drag region
        if self.app.is_dragging and self.app.drag_start and self.app.drag_current:
            # Check if actually dragging (moved more than a few pixels)
            x1, y1 = self.app.drag_start
            x2, y2 = self.app.drag_current
            if abs(x2 - x1) > 5 or abs(y2 - y1) > 5:
                self._draw_drag_region(screen_frame)
            else:
                # Still looks like a click, show highlight
                self._draw_highlight_for_mode(screen_frame)
        else:
            self._draw_highlight_for_mode(screen_frame)

        # Draw mode indicator
        self._draw_mode_indicator()

        # Draw instructions
        self._draw_instructions()

    def _draw_highlighted_window(self, screen_frame):
        """Draw highlight around the selected window."""
        window = self.app.highlighted_window
        wx, wy, ww, wh = window.bounds

        # Convert coordinates (CGWindow uses top-left, NSView uses bottom-left)
        view_x = wx - screen_frame.origin.x
        view_y = screen_frame.size.height - wy - wh - screen_frame.origin.y

        window_rect = NSMakeRect(view_x, view_y, ww, wh)

        # Clear the window area (make it transparent)
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(window_rect)

        # Draw border (bright blue for windows)
        border_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.5, 1.0, 1.0)
        border_color.set()
        border_path = NSBezierPath.bezierPathWithRect_(window_rect)
        border_path.setLineWidth_(4.0)
        border_path.stroke()

        # Draw window info label
        info_text = f"{window.owner_name}"
        if window.window_name:
            info_text += f" - {window.window_name}"

        self._draw_label(info_text, view_x, view_y + wh + 5)

    def _draw_highlighted_element(self, screen_frame):
        """Draw highlight around the selected UI element."""
        element = self.app.highlighted_element
        ex, ey, ew, eh = element.bounds

        # Convert coordinates (Accessibility uses top-left, NSView uses bottom-left)
        view_x = ex - screen_frame.origin.x
        view_y = screen_frame.size.height - ey - eh - screen_frame.origin.y

        element_rect = NSMakeRect(view_x, view_y, ew, eh)

        # Clear the element area (make it transparent)
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(element_rect)

        # Draw border (bright green for elements)
        border_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.9, 0.3, 1.0)
        border_color.set()
        border_path = NSBezierPath.bezierPathWithRect_(element_rect)
        border_path.setLineWidth_(3.0)
        border_path.stroke()

        # Draw element info label
        role_name = element.role.replace("AX", "")  # Remove AX prefix for readability
        info_text = role_name
        if element.title:
            info_text += f": {element.title}"

        self._draw_label(info_text, view_x, view_y + eh + 5)

    def _draw_drag_region(self, screen_frame):
        """Draw the drag selection region."""
        x1, y1 = self.app.drag_start
        x2, y2 = self.app.drag_current

        # Calculate bounds
        x = min(x1, x2) - screen_frame.origin.x
        y = screen_frame.size.height - max(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        region_rect = NSMakeRect(x, y, width, height)

        # Clear the region (make it transparent)
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(region_rect)

        # Draw border
        border_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.4, 0.2, 1.0)
        border_color.set()
        border_path = NSBezierPath.bezierPathWithRect_(region_rect)
        border_path.setLineWidth_(2.0)
        border_path.stroke()

        # Draw dimensions
        dim_text = f"{int(width)} × {int(height)}"
        self._draw_label(dim_text, x, y + height + 5)

    def _draw_highlight_for_mode(self, screen_frame):
        """Draw the appropriate highlight based on current mode."""
        mode = self.app.capture_mode

        if mode == "auto":
            # Auto mode: prefer element, fall back to window
            if self.app.highlighted_element:
                self._draw_highlighted_element(screen_frame)
            elif self.app.highlighted_window:
                self._draw_highlighted_window(screen_frame)
        elif mode == "element":
            if self.app.highlighted_element:
                self._draw_highlighted_element(screen_frame)
        elif mode == "window":
            if self.app.highlighted_window:
                self._draw_highlighted_window(screen_frame)
        # Region mode doesn't draw highlights (only drag region)

    def _draw_mode_indicator(self):
        """Draw the current mode indicator."""
        mode_names = {
            "auto": "Auto Mode",
            "window": "Window Only",
            "element": "Element Only",
            "region": "Region Only"
        }
        mode_text = mode_names.get(self.app.capture_mode, "Unknown Mode")

        # Draw background
        bg_rect = NSMakeRect(10, self.bounds().size.height - 40, 130, 30)
        bg_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.7)
        bg_color.set()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bg_rect, 5, 5).fill()

        # Draw text
        text_color = NSColor.whiteColor()
        attrs = {
            NSFontAttributeName: NSFont.boldSystemFontOfSize_(12),
            NSForegroundColorAttributeName: text_color
        }
        attr_string = NSAttributedString.alloc().initWithString_attributes_(mode_text, attrs)
        attr_string.drawAtPoint_(NSMakePoint(20, self.bounds().size.height - 32))

    def _draw_instructions(self):
        """Draw usage instructions."""
        instructions = "Click: Capture  |  Drag: Select region  |  Space: Cycle mode  |  Esc: Cancel"

        # Draw background
        text_width = 580
        bg_rect = NSMakeRect(
            (self.bounds().size.width - text_width) / 2,
            10,
            text_width,
            25
        )
        bg_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.7)
        bg_color.set()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bg_rect, 5, 5).fill()

        # Draw text
        text_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.8, 0.8, 0.8, 1.0)
        attrs = {
            NSFontAttributeName: NSFont.systemFontOfSize_(11),
            NSForegroundColorAttributeName: text_color
        }
        attr_string = NSAttributedString.alloc().initWithString_attributes_(instructions, attrs)
        attr_string.drawAtPoint_(NSMakePoint(bg_rect.origin.x + 10, 15))

    def _draw_label(self, text: str, x: float, y: float):
        """Draw a label at the given position."""
        # Truncate long text
        if len(text) > 50:
            text = text[:47] + "..."

        # Calculate text size
        attrs = {
            NSFontAttributeName: NSFont.boldSystemFontOfSize_(11),
            NSForegroundColorAttributeName: NSColor.whiteColor()
        }
        attr_string = NSAttributedString.alloc().initWithString_attributes_(text, attrs)
        text_size = attr_string.size()

        # Draw background
        padding = 4
        bg_rect = NSMakeRect(
            x - padding,
            y - padding,
            text_size.width + padding * 2,
            text_size.height + padding * 2
        )
        bg_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.8)
        bg_color.set()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bg_rect, 3, 3).fill()

        # Draw text
        attr_string.drawAtPoint_(NSMakePoint(x, y))

    def acceptsFirstResponder(self):
        return True

    def canBecomeKeyView(self):
        return True


def check_shift_pressed() -> bool:
    """Check if Shift key is currently pressed."""
    flags = CGEventSourceFlagsState(kCGEventSourceStateHIDSystemState)
    return (flags & kCGEventFlagMaskShift) != 0


def main():
    parser = argparse.ArgumentParser(
        description="ShareX-like screenshot tool for macOS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Controls:
  Move mouse     Highlight windows (in window mode)
  Click          Capture highlighted window
  Drag           Select custom region
  Space          Toggle between window/region mode
  Escape         Cancel

Examples:
  %(prog)s                  Take screenshot and save to disk
  %(prog)s --annotate       Annotate screenshot and save to disk
  %(prog)s --no-save        Take screenshot for clipboard only
  %(prog)s --install        Install required dependencies
        """
    )
    parser.add_argument(
        '--annotate', '-a',
        action='store_true',
        help='Open screenshot in Preview for annotation before copying to clipboard'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save screenshot to disk (clipboard only)'
    )
    parser.add_argument(
        '--check-shift',
        action='store_true',
        help='Auto-detect Shift key for annotation mode'
    )
    parser.add_argument(
        '--timeout', '-t',
        type=float,
        default=30.0,
        help='Timeout in seconds before auto-exit (default: 30, 0 = no timeout)'
    )
    parser.add_argument(
        '--install',
        action='store_true',
        help='Install required PyObjC dependencies and exit'
    )

    args = parser.parse_args()

    # Check accessibility permissions
    if not check_accessibility_permissions():
        print("\n❌ Cannot run without accessibility permissions.")
        print("   Please grant permission and try again.")
        sys.exit(1)

    print("✓ Accessibility permissions OK")

    # Check for Shift key if requested
    annotate = args.annotate
    if args.check_shift and not annotate:
        annotate = check_shift_pressed()
        if annotate:
            print("Shift key detected - annotation mode enabled")

    # Run the app
    app = ScreenshotApp(annotate=annotate, save_to_disk=not args.no_save)
    success = app.run(timeout=args.timeout)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

