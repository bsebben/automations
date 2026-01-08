#!/usr/bin/env python3
"""
ShareX-like Screenshot Tool for macOS

Features:
- Window highlighting on hover
- Region selection with crosshairs
- Optional annotation in Preview
- Copy to clipboard
- Screen recording to GIF

Usage:
    python screenshot-sharex.py              # Normal mode
    python screenshot-sharex.py --annotate   # With annotation
    python screenshot-sharex.py --record     # Record to GIF
    python screenshot-sharex.py --install    # Install dependencies

Controls:
    - Move mouse to highlight windows
    - Click to capture highlighted window
    - Hold and drag to select custom region
    - Press Space to toggle between window/region mode
    - Press Escape to cancel
    - Press ⌘. (Cmd+Period) to stop recording
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

    def __init__(self, annotate: bool = False, save_to_disk: bool = True, record_mode: bool = False):
        self.annotate = annotate
        self.save_to_disk = save_to_disk
        self.record_mode = record_mode
        self.app = NSApplication.sharedApplication()
        self.app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        
        self.windows: List[WindowInfo] = []
        self.highlighted_window: Optional[WindowInfo] = None
        self.highlighted_element: Optional[UIElementInfo] = None
        self.is_dragging = False
        self.drag_start: Optional[Tuple[float, float]] = None
        self.drag_current: Optional[Tuple[float, float]] = None
        # Modes: "auto" (default, smart), "window", "element", "region"
        self.capture_mode = "auto"
        self._annotation_active = False
        self.should_quit = False
        self.captured = False
        
        # Event monitoring
        self.event_tap = None
        self.event_monitor = None
        self.local_monitor = None
        self._debug = os.environ.get('DEBUG', '0') == '1'
        
        # Throttling for mouse move (accessibility API is slow)
        self._last_mouse_update = 0
        self._mouse_throttle_ms = 50  # Only update every 50ms
        
        # Recording state (for --record mode)
        self._recording_process = None
        self._recording_temp_file = None
        self._recording_bounds = None
        self._is_recording = False
        self._recording_outline_window = None
        self._stop_dialog_thread = None
        
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
                        modes = ["auto", "window", "element"]
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
                # Don't set to None - just disable it
            except Exception:
                pass
            self.event_tap = None  # Clear reference after disabling

        # Remove NSEvent monitors
        if self.event_monitor:
            try:
                NSEvent.removeMonitor_(self.event_monitor)
            except Exception:
                pass
            self.event_monitor = None
        if self.local_monitor:
            try:
                NSEvent.removeMonitor_(self.local_monitor)
            except Exception:
                pass
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
        import time
        
        location = NSEvent.mouseLocation()
        screen_y = self._flip_y(location.y)
        
        if self.is_dragging:
            self.drag_current = (location.x, screen_y)
            self._update_overlays()
            return
        
        # Throttle expensive operations (accessibility API is slow)
        current_time = time.time() * 1000  # ms
        
        # Use different throttle rates: window mode is fast, element modes are slow
        needs_element_detection = self.capture_mode in ("auto", "element")
        throttle_ms = 100 if needs_element_detection else 16  # 100ms for element, ~60fps for window
        
        if current_time - self._last_mouse_update < throttle_ms:
            return
        self._last_mouse_update = current_time
        
        if self.capture_mode == "window":
            # Window mode is fast - just iterate the window list
            self._find_window_at(location.x, screen_y)
            self.highlighted_element = None
            
            if self.highlighted_window and self._debug:
                print(f"Window: {self.highlighted_window.owner_name}")
        elif self.capture_mode == "auto":
            # Auto mode: find both element and window (slow due to accessibility API)
            self._find_element_at(location.x, screen_y)
            self._find_window_at(location.x, screen_y)
            
            # Only prefer element if it's significantly smaller than the window
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
            # Element mode (slow due to accessibility API)
            self._find_element_at(location.x, screen_y)
            self._find_window_at(location.x, screen_y)
            
            if self._debug and self.highlighted_element:
                print(f"Element: {self.highlighted_element.role} - {self.highlighted_element.title}")
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
            
            # Filter to only useful UI elements (skip text-level elements)
            # These are structural/interactive elements worth highlighting
            USEFUL_ROLES = {
                # Interactive elements
                "AXButton", "AXCheckBox", "AXRadioButton", "AXSlider",
                "AXTextField", "AXTextArea", "AXComboBox", "AXPopUpButton",
                "AXLink", "AXMenuButton", "AXDisclosureTriangle",
                # Tab/navigation
                "AXTab", "AXTabGroup", "AXToolbar", "AXNavigationBar",
                # Menus
                "AXMenu", "AXMenuItem", "AXMenuBar", "AXMenuBarItem",
                # Containers/structural
                "AXGroup", "AXScrollArea", "AXSplitGroup", "AXSplitter",
                "AXSheet", "AXDrawer", "AXPopover",
                # Lists/tables
                "AXTable", "AXRow", "AXCell", "AXList", "AXOutline", "AXOutlineRow",
                "AXBrowser", "AXColumn",
                # Other useful
                "AXImage", "AXProgressIndicator", "AXBusyIndicator",
                "AXColorWell", "AXDateField", "AXWebArea",
            }
            
            # Skip text-level elements (too granular)
            SKIP_ROLES = {
                "AXStaticText", "AXHeading", "AXParagraph",
                "AXLine", "AXWord", "AXCharacter",
                "AXUnknown", "AXApplication", "AXWindow",  # Too broad
            }
            
            if role in SKIP_ROLES:
                return
            
            # If not in useful roles and not explicitly skipped, still allow if it's a reasonable container
            if role not in USEFUL_ROLES and not role.startswith("AX"):
                return
            
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
                
                # Only highlight if element has reasonable size (min 20x20 to skip tiny elements)
                if width > 20 and height > 15:
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
        """Capture a screen region and copy to clipboard (or start recording in record mode)."""
        # If in recording mode, delegate to recording handler
        if self.record_mode:
            self._handle_recording_capture(x, y, width, height)
            return
        
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
        # Escape single quotes in the message for AppleScript
        safe_message = message.replace("'", "'\\''")
        os.system(f'osascript -e \'display notification "{safe_message}" with title "Screenshot"\'')
    
    # ============================================================
    # RECORDING FUNCTIONALITY (for --record mode)
    # ============================================================
    
    def _check_ffmpeg_installed(self) -> bool:
        """Check if ffmpeg is installed."""
        try:
            result = subprocess.run(
                ["which", "ffmpeg"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _install_ffmpeg(self) -> bool:
        """Prompt to install ffmpeg via Homebrew."""
        from AppKit import NSAlert
        
        alert = NSAlert.alloc().init()
        alert.setMessageText_("ffmpeg Required")
        alert.setInformativeText_(
            "Screen recording requires ffmpeg.\n\n"
            "Would you like to install it via Homebrew?\n\n"
            "(This may take a few minutes)"
        )
        alert.addButtonWithTitle_("Install ffmpeg")
        alert.addButtonWithTitle_("Cancel")
        
        if alert.runModal() != 1000:
            return False
        
        print("Installing ffmpeg via Homebrew...")
        result = os.system("brew install ffmpeg")
        
        if result == 0 and self._check_ffmpeg_installed():
            print("✓ ffmpeg installed successfully!")
            return True
        else:
            print("✗ Failed to install ffmpeg")
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Installation Failed")
            alert.setInformativeText_(
                "Failed to install ffmpeg.\n\n"
                "Install manually with: brew install ffmpeg"
            )
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return False
    
    def _get_screen_capture_devices(self):
        """Get all available screen capture devices with their indices."""
        import re
        devices = {}  # screen_number -> device_index
        try:
            result = subprocess.run(
                ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = result.stderr
            
            for line in output.split('\n'):
                # Match "[AVFoundation indev @ 0x...] [2] Capture screen 0"
                match = re.search(r'\[(\d+)\]\s*Capture screen\s*(\d+)', line)
                if match:
                    device_index = match.group(1)
                    screen_number = int(match.group(2))
                    devices[screen_number] = device_index
                    print(f"Found Capture screen {screen_number} at device index {device_index}")
            
            return devices
        except Exception as e:
            print(f"Error listing devices: {e}")
            return {}
    
    def _find_screen_for_point(self, x: float, y: float):
        """Find which screen contains the given point (in CGWindow coordinates).
        
        Returns (screen_index, screen_origin_x, screen_origin_y, scale_factor) or None.
        """
        screens = NSScreen.screens()
        main_screen = NSScreen.mainScreen()
        main_frame = main_screen.frame()
        
        for idx, screen in enumerate(screens):
            frame = screen.frame()
            # NSScreen uses bottom-left origin, convert to top-left for comparison
            screen_y_top = main_frame.size.height - frame.origin.y - frame.size.height
            
            # Check if point is within this screen (with some tolerance)
            if (frame.origin.x <= x < frame.origin.x + frame.size.width and
                screen_y_top <= y < screen_y_top + frame.size.height):
                
                scale = screen.backingScaleFactor()
                print(f"Point ({x}, {y}) is on screen {idx}: origin=({frame.origin.x}, {screen_y_top}), size={frame.size.width}x{frame.size.height}, scale={scale}")
                return (idx, frame.origin.x, screen_y_top, scale)
        
        # Default to main screen
        print(f"Point ({x}, {y}) not found on any screen, using main screen")
        return (0, 0.0, 0.0, main_screen.backingScaleFactor())
    
    def _start_recording(self, x: float, y: float, width: float, height: float):
        """Start screen recording of the specified region."""
        import time
        
        # Check ffmpeg
        if not self._check_ffmpeg_installed():
            if not self._install_ffmpeg():
                self._show_notification("Recording cancelled - ffmpeg not installed")
                return False
        
        # Create temp file for recording
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._recording_temp_file = os.path.join(temp_dir, f"recording_{timestamp}.mov")
        self._recording_bounds = (x, y, width, height)
        
        # Find which screen the selection is on
        screen_info = self._find_screen_for_point(x, y)
        if not screen_info:
            print("✗ Could not determine screen for selection")
            self._show_notification("Recording failed - could not find screen")
            return False
        
        screen_idx, screen_origin_x, screen_origin_y, scale_factor = screen_info
        
        # Get capture device for this screen
        devices = self._get_screen_capture_devices()
        if screen_idx not in devices:
            # Fall back to screen 0
            print(f"No capture device for screen {screen_idx}, using screen 0")
            screen_idx = 0
            screen_origin_x = 0
            screen_origin_y = 0
        
        if screen_idx not in devices:
            print("✗ No screen capture devices found")
            self._show_notification("Recording failed - no screen capture device found")
            return False
        
        screen_device = devices[screen_idx]
        print(f"Using screen capture device: {screen_device} (screen {screen_idx})")
        print(f"Screen scale factor: {scale_factor}")
        
        # Convert coordinates to be relative to the target screen
        relative_x = x - screen_origin_x
        relative_y = y - screen_origin_y
        
        print(f"Screen-relative coords: ({relative_x}, {relative_y})")
        
        # Scale coordinates for Retina displays
        scaled_x = int(relative_x * scale_factor)
        scaled_y = int(relative_y * scale_factor)
        scaled_width = int(width * scale_factor)
        scaled_height = int(height * scale_factor)
        
        # Ensure width/height are even numbers (required for h264)
        crop_width = scaled_width // 2 * 2
        crop_height = scaled_height // 2 * 2
        crop_x = scaled_x
        crop_y = scaled_y
        
        # Build ffmpeg command for macOS screen capture
        cmd = [
            "ffmpeg",
            "-f", "avfoundation",
            "-capture_cursor", "1",
            "-framerate", "30",
            "-i", f"{screen_device}:none",  # Screen device, no audio
            "-vf", f"crop={crop_width}:{crop_height}:{crop_x}:{crop_y}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-y",
            self._recording_temp_file
        ]
        
        print(f"Starting recording: {crop_width}x{crop_height} at ({crop_x}, {crop_y}) [screen-relative, scaled from {int(relative_x)}, {int(relative_y)}]")
        print(f"Output: {self._recording_temp_file}")
        
        try:
            # Start ffmpeg in background - capture stderr to see errors
            self._recording_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            self._is_recording = True
            
            # Give ffmpeg a moment to start
            time.sleep(0.5)
            
            # Check if ffmpeg is still running
            if self._recording_process.poll() is not None:
                # ffmpeg exited immediately - there was an error
                _, stderr = self._recording_process.communicate()
                print(f"FFmpeg failed to start:\n{stderr.decode('utf-8', errors='ignore')[-500:]}")
                self._show_notification("Recording failed - check ffmpeg output")
                return False
            
            # Show notification
            self._show_notification("Recording started! Click Stop Recording to stop")
            
            return True
            
        except Exception as e:
            print(f"Failed to start recording: {e}")
            self._show_notification(f"Recording failed: {e}")
            return False
    
    def _stop_recording(self):
        """Stop the current recording and convert to GIF."""
        if not self._recording_process:
            return None
        
        print("\nStopping recording...")
        self._is_recording = False
        
        # Close recording outline window first (use orderOut to avoid segfault)
        if self._recording_outline_window:
            try:
                self._recording_outline_window.orderOut_(None)
            except Exception:
                pass
            # Don't set to None here - let the caller handle final cleanup
        
        # Stop ffmpeg
        stderr_output = ""
        try:
            # Send 'q' to ffmpeg to stop gracefully
            self._recording_process.stdin.write(b'q')
            self._recording_process.stdin.flush()
            _, stderr_output = self._recording_process.communicate(timeout=10)
            if stderr_output:
                stderr_output = stderr_output.decode('utf-8', errors='ignore')
        except subprocess.TimeoutExpired:
            print("FFmpeg didn't stop gracefully, terminating...")
            self._recording_process.terminate()
            try:
                _, stderr_output = self._recording_process.communicate(timeout=5)
                if stderr_output:
                    stderr_output = stderr_output.decode('utf-8', errors='ignore')
            except Exception:
                self._recording_process.kill()
        except Exception as e:
            print(f"Error stopping ffmpeg: {e}")
            try:
                self._recording_process.kill()
            except Exception:
                pass
        
        self._recording_process = None
        
        # Check if recording file exists
        if not os.path.exists(self._recording_temp_file):
            print("✗ Recording file not found")
            if stderr_output:
                print(f"FFmpeg output:\n{stderr_output[-1000:]}")  # Last 1000 chars
            self._show_notification("Recording failed - no output file")
            return None
        
        file_size = os.path.getsize(self._recording_temp_file)
        print(f"✓ Recording saved: {file_size} bytes")
        
        # Convert to GIF
        return self._convert_to_gif()
    
    def _convert_to_gif(self) -> Optional[str]:
        """Convert the recorded video to GIF."""
        if not self._recording_temp_file or not os.path.exists(self._recording_temp_file):
            return None
        
        print("Converting to GIF...")
        
        # Generate output path
        import datetime
        now = datetime.datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%B")
        
        screenshots_dir = os.path.expanduser(f"~/Screenshots/{year}/{month}")
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Find next number
        next_num = self._get_next_recording_number(screenshots_dir)
        gif_filename = f"recording-{next_num}.gif"
        gif_path = os.path.join(screenshots_dir, gif_filename)
        
        # Get recording dimensions
        width = int(self._recording_bounds[2]) if self._recording_bounds else 640
        
        # Scale down if too large (max 800px width for reasonable GIF size)
        scale_width = min(width, 800)
        
        # Convert using ffmpeg with optimized GIF settings
        # Two-pass for better quality: generate palette first, then use it
        palette_file = os.path.join(tempfile.gettempdir(), "palette.png")
        
        try:
            # Pass 1: Generate palette
            palette_cmd = [
                "ffmpeg", "-y",
                "-i", self._recording_temp_file,
                "-vf", f"fps=15,scale={scale_width}:-1:flags=lanczos,palettegen=stats_mode=diff",
                palette_file
            ]
            subprocess.run(palette_cmd, capture_output=True, check=True)
            
            # Pass 2: Create GIF using palette
            gif_cmd = [
                "ffmpeg", "-y",
                "-i", self._recording_temp_file,
                "-i", palette_file,
                "-lavfi", f"fps=15,scale={scale_width}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5",
                gif_path
            ]
            subprocess.run(gif_cmd, capture_output=True, check=True)
            
            print(f"✓ GIF saved to: {gif_path}")
            
            # Copy GIF to clipboard (as file reference)
            self._copy_gif_to_clipboard(gif_path)
            
            # Cleanup temp files
            try:
                os.remove(self._recording_temp_file)
                os.remove(palette_file)
            except Exception:
                pass
            
            self._show_notification(f"Recording saved to {gif_filename}!")
            return gif_path
            
        except subprocess.CalledProcessError as e:
            print(f"✗ GIF conversion failed: {e}")
            self._show_notification("GIF conversion failed")
            return None
    
    def _get_next_recording_number(self, screenshots_dir: str) -> int:
        """Find the next available sequential number for recordings."""
        import re
        
        max_num = 0
        pattern = re.compile(r'^recording-(\d+)\.gif$')
        
        if os.path.exists(screenshots_dir):
            for filename in os.listdir(screenshots_dir):
                match = pattern.match(filename)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
        
        return max_num + 1
    
    def _copy_gif_to_clipboard(self, gif_path: str):
        """Copy GIF file to clipboard using osascript (most reliable method)."""
        try:
            # Check file exists
            if not os.path.exists(gif_path):
                print(f"✗ GIF file not found: {gif_path}")
                return False
            
            print(f"Copying to clipboard: {gif_path}")
            
            # Use osascript to copy the file to clipboard - this is the most reliable method
            # It copies as a file reference that can be pasted in Finder, Slack, etc.
            script = f'''
                set theFile to POSIX file "{gif_path}"
                set the clipboard to theFile
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✓ GIF copied to clipboard")
                return True
            else:
                print(f"✗ osascript failed: {result.stderr}")
                # Fall back to NSImage method
                return self._copy_gif_to_clipboard_nsimage(gif_path)
                
        except Exception as e:
            print(f"Could not copy to clipboard: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _copy_gif_to_clipboard_nsimage(self, gif_path: str):
        """Fallback: Copy GIF as NSImage to clipboard."""
        try:
            from Foundation import NSData
            
            # Read the GIF file
            with open(gif_path, 'rb') as f:
                gif_bytes = f.read()
            
            gif_data = NSData.dataWithBytes_length_(gif_bytes, len(gif_bytes))
            if not gif_data:
                print("✗ Could not read GIF file")
                return False
            
            # Create NSImage from GIF data
            image = NSImage.alloc().initWithData_(gif_data)
            if not image:
                print("✗ Could not create image from GIF")
                return False
            
            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            
            # Write the image
            success = pasteboard.writeObjects_([image])
            
            if success:
                print("✓ GIF copied to clipboard (as image)")
                return True
            else:
                print("✗ Failed to write to clipboard")
                return False
                
        except Exception as e:
            print(f"Fallback clipboard copy failed: {e}")
            return False
    
    def _create_recording_outline(self, x: float, y: float, width: float, height: float):
        """Create a simple outline window to show the recording region."""
        # Get main screen for coordinate conversion
        main_screen = NSScreen.mainScreen()
        screen_height = main_screen.frame().size.height
        
        # Convert from top-left (CGWindow) to bottom-left (NSWindow) coordinates
        ns_y = screen_height - y - height
        
        # Create a borderless window for the outline
        frame = NSMakeRect(x - 3, ns_y - 3, width + 6, height + 6)
        
        outline_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            NSBorderlessWindowMask,
            NSBackingStoreBuffered,
            False
        )
        outline_window.setLevel_(NSStatusWindowLevel + 500)
        outline_window.setOpaque_(False)
        outline_window.setBackgroundColor_(NSColor.clearColor())
        outline_window.setIgnoresMouseEvents_(True)
        outline_window.setHasShadow_(False)
        
        # Create a view that draws the outline
        view = RecordingOutlineView.alloc().initWithFrame_(NSMakeRect(0, 0, width + 6, height + 6))
        outline_window.setContentView_(view)
        outline_window.makeKeyAndOrderFront_(None)
        
        return outline_window
    
    def _start_stop_dialog_thread(self):
        """Start a background thread that shows a stop dialog."""
        import threading
        
        def show_dialog():
            # Use osascript to show a dialog - this is guaranteed to work
            result = subprocess.run([
                "osascript", "-e",
                'display dialog "Recording in progress..." buttons {"Stop Recording"} default button 1 with title "Screen Recording" with icon caution'
            ], capture_output=True)
            
            # When dialog is dismissed (button clicked), stop recording
            print("\nStop signal received (dialog)")
            self._is_recording = False
        
        # Run in background thread so it doesn't block
        self._stop_dialog_thread = threading.Thread(target=show_dialog, daemon=True)
        self._stop_dialog_thread.start()
    
    def _handle_recording_capture(self, x: float, y: float, width: float, height: float):
        """Handle capture in recording mode - start recording instead of screenshot."""
        # Disable ALL event monitoring during recording (no click/space/mouse events)
        self._disable_event_monitoring()
        
        # Hide selection overlays
        for window in self.overlay_windows:
            window.orderOut_(None)
        
        # Small delay
        NSRunLoop.currentRunLoop().runUntilDate_(
            NSDate.dateWithTimeIntervalSinceNow_(0.1)
        )
        
        # Create recording outline overlay
        self._recording_outline_window = self._create_recording_outline(x, y, width, height)
        
        # Start recording
        if self._start_recording(x, y, width, height):
            # Show stop dialog in background thread
            self._start_stop_dialog_thread()
            
            # Enter recording loop - wait for stop signal
            self._run_recording_loop()
        
        # Window cleanup is handled in _stop_recording, just clear the reference
        self._recording_outline_window = None
    
    def _run_recording_loop(self):
        """Run loop while recording - wait for stop button click."""
        import time
        
        print("\n" + "=" * 50)
        print("RECORDING IN PROGRESS")
        print("=" * 50)
        print("Click the STOP button to stop recording")
        print("=" * 50 + "\n")
        
        # Run loop while recording - just process events and wait for button click
        start_time = time.time()
        last_print_time = 0
        
        while self._is_recording:
            # Process Cocoa events (including button clicks)
            NSRunLoop.currentRunLoop().runUntilDate_(
                NSDate.dateWithTimeIntervalSinceNow_(0.1)
            )
            
            # Show elapsed time every 5 seconds
            elapsed = int(time.time() - start_time)
            if elapsed > 0 and elapsed != last_print_time and elapsed % 5 == 0:
                print(f"Recording: {elapsed}s elapsed...")
                last_print_time = elapsed
        
        # Small delay before stopping
        time.sleep(0.2)
        
        # Stop recording and convert
        print("Processing recording...")
        try:
            gif_path = self._stop_recording()
            self.captured = gif_path is not None
        except Exception as e:
            print(f"Error during stop: {e}")
            import traceback
            traceback.print_exc()
            self.captured = False
        
        self.should_quit = True
    
    # ============================================================
    # END RECORDING FUNCTIONALITY
    # ============================================================
    
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
        print("  - Space to cycle mode: Auto → Window → Element")
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

        # Close overlay windows safely
        for window in self.overlay_windows:
            try:
                window.orderOut_(None)  # Hide first
            except Exception:
                pass
        self.overlay_windows = []

        return self.captured


class RecordingOutlineView(NSView):
    """Simple view that draws a red outline for recording region."""
    
    def drawRect_(self, rect):
        """Draw a red outline."""
        # Clear background
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(self.bounds())
        
        # Draw red border (3px thick)
        border_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.2, 0.2, 0.9)
        border_color.set()
        
        # Inner rect (the actual recording area)
        inner_rect = NSMakeRect(3, 3, self.bounds().size.width - 6, self.bounds().size.height - 6)
        border_path = NSBezierPath.bezierPathWithRect_(inner_rect)
        border_path.setLineWidth_(3.0)
        border_path.stroke()


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
        # Need to use main screen height for proper multi-monitor conversion
        main_screen = NSScreen.mainScreen()
        main_height = main_screen.frame().size.height
        
        view_x = wx - screen_frame.origin.x
        view_y = main_height - wy - wh - screen_frame.origin.y
        
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
        # Need to use main screen height for proper multi-monitor conversion
        main_screen = NSScreen.mainScreen()
        main_height = main_screen.frame().size.height
        
        view_x = ex - screen_frame.origin.x
        view_y = main_height - ey - eh - screen_frame.origin.y
        
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
        
        # Get main screen height for coordinate conversion
        main_screen = NSScreen.mainScreen()
        main_height = main_screen.frame().size.height
        
        # Calculate bounds
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        # Get top-left corner in CGWindow coords
        left = min(x1, x2)
        top = min(y1, y2)
        
        # Convert to view coordinates (bottom-left origin)
        # Same formula as window/element highlighting
        x = left - screen_frame.origin.x
        y = main_height - top - height - screen_frame.origin.y
        
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
  %(prog)s --record         Record screen region to GIF
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
    parser.add_argument(
        '--record', '-r',
        action='store_true',
        help='Record screen region to GIF instead of taking screenshot'
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
    if args.record:
        print("📹 Recording mode enabled - select region to record")
    
    app = ScreenshotApp(
        annotate=annotate,
        save_to_disk=not args.no_save,
        record_mode=args.record
    )
    success = app.run(timeout=args.timeout)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
