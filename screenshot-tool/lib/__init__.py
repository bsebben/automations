"""
Screenshot Tool Library

Utility modules for the ShareX-style screenshot tool.
"""

from .models import WindowInfo, UIElementInfo
from .utils import (
    show_notification,
    get_screenshots_dir,
    get_next_screenshot_number,
    get_next_recording_number,
    flip_y_coordinate,
    generate_screenshot_path,
    generate_recording_path,
)
from .dependencies import (
    REQUIRED_PACKAGES,
    check_dependencies,
    install_dependencies,
    prompt_install,
    handle_early_flags,
    handle_import_error,
    check_accessibility_permissions,
)

__all__ = [
    # Models
    "WindowInfo",
    "UIElementInfo",
    # Utils
    "show_notification",
    "get_screenshots_dir",
    "get_next_screenshot_number",
    "get_next_recording_number",
    "flip_y_coordinate",
    "generate_screenshot_path",
    "generate_recording_path",
    # Dependencies
    "REQUIRED_PACKAGES",
    "check_dependencies",
    "install_dependencies",
    "prompt_install",
    "handle_early_flags",
    "handle_import_error",
    "check_accessibility_permissions",
]

