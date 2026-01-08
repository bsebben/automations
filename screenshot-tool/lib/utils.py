"""
Utility functions for the screenshot tool.

These are pure utility functions that don't depend on application state.
"""

import os
import re
from datetime import datetime
from typing import Optional


def show_notification(message: str, title: str = "Screenshot"):
    """Show a system notification using osascript."""
    # Escape single quotes in the message for AppleScript
    safe_message = message.replace("'", "'\\''")
    os.system(f'osascript -e \'display notification "{safe_message}" with title "{title}"\'')


def get_screenshots_dir() -> str:
    """Get the screenshots directory path for the current date.
    
    Returns path in format: ~/Screenshots/YYYY/Month/
    Creates the directory if it doesn't exist.
    """
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%B")  # January, February, March, etc.
    
    screenshots_dir = os.path.expanduser(f"~/Screenshots/{year}/{month}")
    os.makedirs(screenshots_dir, exist_ok=True)
    
    return screenshots_dir


def get_next_screenshot_number(screenshots_dir: str) -> int:
    """Find the next available sequential number for screenshots in the directory.
    
    Looks for files matching 'screenshot-N.png' and returns N+1 for the highest N found.
    """
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


def get_next_recording_number(screenshots_dir: str) -> int:
    """Find the next available sequential number for recordings in the directory.
    
    Looks for files matching 'recording-N.gif' and returns N+1 for the highest N found.
    """
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


def flip_y_coordinate(y: float, screen_height: float) -> float:
    """Convert between coordinate systems.
    
    macOS uses two coordinate systems:
    - NSScreen/NSView: bottom-left origin, y increases upward
    - CGWindow: top-left origin, y increases downward
    
    This function flips y between them.
    
    Args:
        y: The y coordinate to flip
        screen_height: The height of the reference screen
        
    Returns:
        The flipped y coordinate
    """
    return screen_height - y


def generate_screenshot_path(screenshots_dir: str) -> str:
    """Generate the full path for a new screenshot file.
    
    Returns path like: ~/Screenshots/2024/January/screenshot-42.png
    """
    next_num = get_next_screenshot_number(screenshots_dir)
    filename = f"screenshot-{next_num}.png"
    return os.path.join(screenshots_dir, filename)


def generate_recording_path(screenshots_dir: str) -> str:
    """Generate the full path for a new recording file.
    
    Returns path like: ~/Screenshots/2024/January/recording-7.gif
    """
    next_num = get_next_recording_number(screenshots_dir)
    filename = f"recording-{next_num}.gif"
    return os.path.join(screenshots_dir, filename)

