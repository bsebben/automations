"""
Screen recording functionality for the screenshot tool.

This module handles:
- Starting/stopping screen recordings using macOS screencapture
- Converting recordings to GIF using ffmpeg
- Recording overlay UI (outline and status pill)
- Keyboard event handling during recording (ESC to cancel, ⌘. to stop)
"""

import os
import signal
import subprocess
import tempfile
import time
from datetime import datetime
from typing import Callable, Optional, Tuple

# Import utilities
from lib.utils import (
    show_notification,
    get_screenshots_dir,
    get_next_recording_number,
    generate_recording_path,
)

# PyObjC imports - these are imported at module level
# The main app ensures PyObjC is available before importing this module
try:
    from AppKit import (
        NSApplication,
        NSWindow,
        NSView,
        NSColor,
        NSBezierPath,
        NSImage,
        NSPasteboard,
        NSBorderlessWindowMask,
        NSBackingStoreBuffered,
        NSStatusWindowLevel,
        NSFont,
        NSFontAttributeName,
        NSForegroundColorAttributeName,
        NSScreen,
        NSString,
        NSMakeRect,
        NSMakePoint,
        NSRunLoop,
        NSDate,
    )
    from Quartz import (
        CGEventTapCreate,
        CGEventTapEnable,
        CGEventMaskBit,
        CGEventGetIntegerValueField,
        CGEventGetFlags,
        kCGSessionEventTap,
        kCGHeadInsertEventTap,
        kCGEventTapOptionDefault,
        kCGEventKeyDown,
        kCGKeyboardEventKeycode,
        kCGEventFlagMaskCommand,
        CFMachPortCreateRunLoopSource,
        CFRunLoopGetCurrent,
        CFRunLoopAddSource,
        CFRunLoopRemoveSource,
        kCFRunLoopCommonModes,
    )
    from Foundation import NSData
    
    PYOBJC_AVAILABLE = True
except ImportError:
    PYOBJC_AVAILABLE = False


class RecordingOutlineView(NSView):
    """View that draws a red outline for recording region with status pill.
    
    The border is drawn OUTSIDE the recording region so it doesn't appear in the capture.
    The pill is drawn ABOVE the recording region in extra space added to the window.
    """
    
    padding = 4  # Default, will be set by _create_outline
    border_width = 3.0
    pill_height = 24  # Extra space at top for pill
    
    def drawRect_(self, rect):
        """Draw a red outline and recording pill."""
        # Clear background
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(self.bounds())
        
        padding = getattr(self, 'padding', 4)
        border_width = getattr(self, 'border_width', 3.0)
        pill_space = getattr(self, 'pill_height', 24)
        
        # The view layout (from bottom to top):
        # - padding: bottom border area
        # - recording_height: the actual recording region (NOT drawn on, just outlined)
        # - padding: top border area  
        # - pill_space: extra space for the pill (ABOVE recording region)
        
        view_height = self.bounds().size.height
        view_width = self.bounds().size.width
        
        # Recording region in view coordinates (bottom-left origin)
        # Recording region starts at (padding, padding) and excludes the pill_space at top
        recording_width = view_width - 2 * padding
        recording_height = view_height - 2 * padding - pill_space
        
        # Draw red border OUTSIDE the recording region
        border_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.2, 0.2, 0.9)
        border_color.set()
        
        # Calculate the border path - offset outward by half the border width
        half_border = border_width / 2
        border_rect = NSMakeRect(
            padding - half_border - 0.5,
            padding - half_border - 0.5,
            recording_width + border_width + 1,
            recording_height + border_width + 1
        )
        border_path = NSBezierPath.bezierPathWithRect_(border_rect)
        border_path.setLineWidth_(border_width)
        border_path.stroke()
        
        # Draw recording pill in the pill_space ABOVE the recording area
        pill_text = "● REC   ⌘. stop  |  ESC cancel"
        font = NSFont.systemFontOfSize_(11)
        
        # Calculate text size
        attrs = {
            NSFontAttributeName: font,
            NSForegroundColorAttributeName: NSColor.whiteColor()
        }
        text_size = NSString.stringWithString_(pill_text).sizeWithAttributes_(attrs)
        
        # Pill dimensions
        pill_padding_h = 6
        pill_padding_v = 3
        pill_width = text_size.width + pill_padding_h * 2
        actual_pill_height = text_size.height + pill_padding_v * 2
        
        # Position pill at top-left, in the pill_space above the recording border
        # The pill_space starts at (padding + recording_height + padding) = view_height - pill_space
        pill_x = padding
        pill_y = view_height - pill_space + (pill_space - actual_pill_height) / 2  # Centered in pill_space
        
        # Draw pill background (red, semi-transparent)
        pill_rect = NSMakeRect(pill_x, pill_y, pill_width, actual_pill_height)
        pill_bg = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.8, 0.1, 0.1, 0.95)
        pill_bg.set()
        pill_path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(pill_rect, 4, 4)
        pill_path.fill()
        
        # Draw text
        text_x = pill_x + pill_padding_h
        text_y = pill_y + (actual_pill_height - text_size.height) / 2
        NSString.stringWithString_(pill_text).drawAtPoint_withAttributes_(
            NSMakePoint(text_x, text_y), attrs
        )


class ScreenRecorder:
    """Handles screen recording functionality.
    
    This class encapsulates all recording logic:
    - Starting/stopping recordings using macOS screencapture
    - Converting recordings to GIF using ffmpeg
    - Managing the recording overlay UI
    - Handling keyboard events during recording
    """
    
    def __init__(
        self,
        get_primary_screen_height: Callable[[], float],
        main_event_tap=None,
        debug: bool = False
    ):
        """Initialize the screen recorder.
        
        Args:
            get_primary_screen_height: Callback to get the primary display height
            main_event_tap: Optional reference to main app's event tap (for re-enabling)
            debug: Enable debug output
        """
        self._get_primary_screen_height = get_primary_screen_height
        self._main_event_tap = main_event_tap
        self._debug = debug
        
        # Recording state
        self._process: Optional[subprocess.Popen] = None
        self._temp_file: Optional[str] = None
        self._bounds: Optional[Tuple[float, float, float, float]] = None
        self._crop: Optional[dict] = None
        self._is_recording = False
        self._cancelled = False
        
        # UI state
        self._outline_window = None
        
        # Keyboard event tap for recording controls
        self._event_tap = None
        self._run_loop_source = None
        self._keyboard_callback = None
    
    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording
    
    @property
    def was_cancelled(self) -> bool:
        """Check if recording was cancelled."""
        return self._cancelled
    
    def start(self, x: float, y: float, width: float, height: float) -> bool:
        """Start screen recording of the specified region.
        
        Args:
            x, y: Top-left corner in CGWindow coordinates
            width, height: Size of the region
            
        Returns:
            True if recording started successfully
        """
        # Create temp file for recording
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._temp_file = os.path.join(temp_dir, f"recording_{timestamp}.mov")
        self._bounds = (x, y, width, height)
        
        # No cropping needed - screencapture records exactly the region we specify
        self._crop = None
        
        # Use macOS native screencapture command with -R for region
        cmd = [
            "screencapture",
            "-v",  # Video recording mode
            "-R", f"{int(x)},{int(y)},{int(width)},{int(height)}",  # Region to capture
            self._temp_file
        ]
        
        print(f"Recording region: {int(width)}x{int(height)} at ({int(x)}, {int(y)})")
        print(f"Output: {self._temp_file}")
        if self._debug:
            print(f"Command: {' '.join(cmd)}")
        
        try:
            # Start screencapture
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            self._is_recording = True
            
            # Give it a moment to start
            time.sleep(0.5)
            
            # Check if screencapture is still running
            if self._process.poll() is not None:
                exit_code = self._process.returncode
                _, stderr = self._process.communicate()
                print(f"screencapture failed (exit code {exit_code}): {stderr.decode('utf-8', errors='ignore')}")
                show_notification("Recording failed - check screen recording permissions")
                return False
            
            print(f"✓ Recording started (PID: {self._process.pid})")
            show_notification("Recording started! Press ⌘. to stop")
            
            return True
            
        except Exception as e:
            print(f"Failed to start recording: {e}")
            show_notification(f"Recording failed: {e}")
            return False
    
    def stop(self, cancelled: bool = False) -> Optional[str]:
        """Stop the current recording and optionally convert to GIF.
        
        Args:
            cancelled: If True, discard the recording instead of saving
            
        Returns:
            Path to the GIF file, or None if cancelled/failed
        """
        if not self._process:
            return None
        
        if cancelled:
            print("\nCancelling recording...")
        else:
            print("\nStopping recording...")
        self._is_recording = False
        
        # Hide recording UI
        self._hide_outline()
        
        # Check if recording process is still running
        poll_result = self._process.poll()
        if poll_result is not None:
            print(f"⚠️  Recording process already exited with code {poll_result}")
            self._process = None
            if poll_result != 0:
                return None
        else:
            # Stop recording using SIGINT (Ctrl+C equivalent)
            try:
                print(f"Stopping recording (PID: {self._process.pid})...")
                self._process.send_signal(signal.SIGINT)
                self._process.wait(timeout=5)
                print("✓ Recording stopped")
            except subprocess.TimeoutExpired:
                print("Recording didn't stop with SIGINT, terminating...")
                self._process.terminate()
                try:
                    self._process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    print("Recording didn't respond to SIGTERM, killing...")
                    self._process.kill()
                    self._process.wait()
            except Exception as e:
                print(f"Error stopping recording: {e}")
                try:
                    self._process.kill()
                    self._process.wait()
                except Exception:
                    pass
            
            self._process = None
        
        # Check if recording file exists
        if not self._temp_file or not os.path.exists(self._temp_file):
            print("✗ Recording file not found")
            if not cancelled:
                show_notification("Recording failed - no output file")
            return None
        
        # If cancelled, just clean up temp file
        if cancelled:
            try:
                os.remove(self._temp_file)
                print("✓ Recording cancelled, temp file cleaned up")
            except Exception:
                pass
            show_notification("Recording cancelled")
            return None
        
        file_size = os.path.getsize(self._temp_file)
        print(f"✓ Recording saved: {file_size} bytes")
        
        # Convert to GIF
        return self._convert_to_gif()
    
    def cancel(self):
        """Cancel the current recording."""
        self._cancelled = True
        self._is_recording = False
    
    def signal_stop(self):
        """Signal that recording should stop (save, not cancel)."""
        self._is_recording = False
    
    def _convert_to_gif(self) -> Optional[str]:
        """Convert the recorded video to GIF."""
        if not self._temp_file or not os.path.exists(self._temp_file):
            return None
        
        print("Converting to GIF...")
        
        # Generate output path
        screenshots_dir = get_screenshots_dir()
        gif_path = generate_recording_path(screenshots_dir)
        gif_filename = os.path.basename(gif_path)
        
        # Get crop info (we recorded full screen and crop during conversion)
        if self._crop:
            crop_filter = f"crop={self._crop['width']}:{self._crop['height']}:{self._crop['x']}:{self._crop['y']},"
            output_width = self._crop['width']
            print(f"Applying crop: {self._crop['width']}x{self._crop['height']} at ({self._crop['x']}, {self._crop['y']})")
        else:
            crop_filter = ""
            output_width = int(self._bounds[2]) if self._bounds else 640
        
        # Scale down if too large (max 800px width for reasonable GIF size)
        scale_width = min(output_width, 800)
        
        # Convert using ffmpeg with optimized GIF settings
        palette_file = os.path.join(tempfile.gettempdir(), "palette.png")
        
        try:
            # Pass 1: Generate palette
            palette_cmd = [
                "ffmpeg", "-y",
                "-i", self._temp_file,
                "-vf", f"{crop_filter}fps=15,scale={scale_width}:-1:flags=lanczos,palettegen=stats_mode=diff",
                palette_file
            ]
            print(f"Generating palette...")
            result = subprocess.run(palette_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Palette generation failed: {result.stderr[-500:]}")
                raise subprocess.CalledProcessError(result.returncode, palette_cmd)
            
            # Pass 2: Create GIF using palette
            gif_cmd = [
                "ffmpeg", "-y",
                "-i", self._temp_file,
                "-i", palette_file,
                "-lavfi", f"{crop_filter}fps=15,scale={scale_width}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5",
                gif_path
            ]
            print(f"Creating GIF...")
            result = subprocess.run(gif_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"GIF creation failed: {result.stderr[-500:]}")
                raise subprocess.CalledProcessError(result.returncode, gif_cmd)
            
            print(f"✓ GIF saved to: {gif_path}")
            
            # Copy GIF to clipboard
            self._copy_to_clipboard(gif_path)
            
            # Cleanup temp files
            try:
                os.remove(self._temp_file)
                os.remove(palette_file)
            except Exception:
                pass
            
            show_notification(f"Recording saved to {gif_filename}!")
            return gif_path
            
        except subprocess.CalledProcessError as e:
            print(f"✗ GIF conversion failed: {e}")
            show_notification("GIF conversion failed")
            return None
    
    def _copy_to_clipboard(self, gif_path: str) -> bool:
        """Copy GIF file to clipboard using osascript."""
        try:
            if not os.path.exists(gif_path):
                print(f"✗ GIF file not found: {gif_path}")
                return False
            
            print(f"Copying to clipboard: {gif_path}")
            
            # Use osascript to copy the file to clipboard
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
                return self._copy_to_clipboard_nsimage(gif_path)
                
        except Exception as e:
            print(f"Could not copy to clipboard: {e}")
            return False
    
    def _copy_to_clipboard_nsimage(self, gif_path: str) -> bool:
        """Fallback: Copy GIF as NSImage to clipboard."""
        try:
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
    
    def create_outline(self, x: float, y: float, width: float, height: float):
        """Create the recording outline overlay window.
        
        Args:
            x, y: Top-left corner in CGWindow coordinates
            width, height: Size of the region
        """
        main_height = self._get_primary_screen_height()
        
        # Convert from CGWindow coords (top-left origin) to NSWindow coords (bottom-left origin)
        ns_x = x
        ns_y = main_height - y - height
        
        if self._debug:
            print(f"Recording outline: CGWindow({x}, {y}, {width}, {height}) -> NSWindow({ns_x}, {ns_y})")
            print(f"  main_height={main_height}")
        
        # Border thickness and padding
        border_width = 3.0
        padding = int(border_width) + 1  # 4px padding ensures border is fully outside
        pill_height = 24  # Extra space at top for the recording pill
        
        # Create window frame
        frame = NSMakeRect(
            ns_x - padding, 
            ns_y - padding,
            width + padding * 2, 
            height + padding * 2 + pill_height
        )
        
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
        # NSWindowSharingNone (0) = exclude from screen recordings/captures
        outline_window.setSharingType_(0)
        
        # Create a view that draws the outline
        view = RecordingOutlineView.alloc().initWithFrame_(
            NSMakeRect(0, 0, width + padding * 2, height + padding * 2 + pill_height)
        )
        view.padding = padding
        view.border_width = border_width
        view.pill_height = pill_height
        outline_window.setContentView_(view)
        outline_window.makeKeyAndOrderFront_(None)
        
        self._outline_window = outline_window
    
    def _hide_outline(self):
        """Hide and clean up the recording outline window."""
        if self._outline_window:
            try:
                self._outline_window.orderOut_(None)
                self._outline_window.close()
            except Exception:
                pass
            self._outline_window = None
        
        # Process events to ensure the window actually disappears
        NSRunLoop.currentRunLoop().runUntilDate_(
            NSDate.dateWithTimeIntervalSinceNow_(0.05)
        )
    
    def setup_keyboard_monitor(self):
        """Set up CGEventTap for recording controls (ESC to cancel, ⌘. to stop)."""
        
        def recording_keyboard_callback(proxy, event_type, event, refcon):
            """Handle keyboard events during recording."""
            if event_type == kCGEventKeyDown:
                key_code = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
                flags = CGEventGetFlags(event)
                
                # ESC key (keyCode 53) - cancel recording
                if key_code == 53:
                    print("\nRecording cancelled (ESC)")
                    self._cancelled = True
                    self._is_recording = False
                    return None  # Consume the event
                
                # ⌘. (Command + Period, keyCode 47) - stop recording
                if key_code == 47 and (flags & kCGEventFlagMaskCommand):
                    print("\nStop signal received (⌘.)")
                    self._is_recording = False
                    return None  # Consume the event
            
            return event
        
        # Store callback reference to prevent garbage collection
        self._keyboard_callback = recording_keyboard_callback
        
        # Create event tap for keyboard events only
        event_mask = CGEventMaskBit(kCGEventKeyDown)
        
        self._event_tap = CGEventTapCreate(
            kCGSessionEventTap,
            kCGHeadInsertEventTap,
            kCGEventTapOptionDefault,
            event_mask,
            self._keyboard_callback,
            None
        )
        
        if self._event_tap:
            # Create run loop source and add to current run loop
            self._run_loop_source = CFMachPortCreateRunLoopSource(
                None, self._event_tap, 0
            )
            CFRunLoopAddSource(
                CFRunLoopGetCurrent(),
                self._run_loop_source,
                kCFRunLoopCommonModes
            )
            # Enable the tap
            CGEventTapEnable(self._event_tap, True)
            print("Recording keyboard monitor active (ESC=cancel, ⌘.=stop)")
        else:
            print("Warning: Failed to create recording keyboard event tap")
    
    def remove_keyboard_monitor(self):
        """Remove the recording keyboard event tap."""
        if self._event_tap:
            try:
                CGEventTapEnable(self._event_tap, False)
                if self._run_loop_source:
                    CFRunLoopRemoveSource(
                        CFRunLoopGetCurrent(),
                        self._run_loop_source,
                        kCFRunLoopCommonModes
                    )
                    self._run_loop_source = None
            except Exception as e:
                print(f"Warning: Error removing recording keyboard monitor: {e}")
            self._event_tap = None
        self._keyboard_callback = None
    
    def run_loop(self):
        """Run the recording loop - wait for keyboard shortcut to stop."""
        print("\n" + "=" * 50)
        print("● RECORDING IN PROGRESS")
        print("=" * 50)
        print("  ⌘.  (Command+Period) to stop and save")
        print("  ESC to cancel")
        print("=" * 50 + "\n")
        
        start_time = time.time()
        last_print_time = 0
        last_tap_check = 0
        
        while self._is_recording:
            # Process Cocoa events
            NSRunLoop.currentRunLoop().runUntilDate_(
                NSDate.dateWithTimeIntervalSinceNow_(0.1)
            )
            
            current_time = time.time()
            
            # Re-enable event tap periodically (it can time out and be disabled by macOS)
            if current_time - last_tap_check > 1.0:
                if self._main_event_tap:
                    try:
                        CGEventTapEnable(self._main_event_tap, True)
                    except Exception:
                        pass
                last_tap_check = current_time
            
            # Show elapsed time every 5 seconds
            elapsed = int(current_time - start_time)
            if elapsed > 0 and elapsed != last_print_time and elapsed % 5 == 0:
                print(f"Recording: {elapsed}s elapsed...")
                last_print_time = elapsed
        
        # Hide the recording overlay immediately
        self._hide_outline()
        
        # Process recording result
        print("Processing recording...")
        try:
            gif_path = self.stop(cancelled=self._cancelled)
            return gif_path is not None
        except Exception as e:
            print(f"Error during stop: {e}")
            import traceback
            traceback.print_exc()
            return False

