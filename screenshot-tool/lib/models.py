"""
Data models for the screenshot tool.
"""

from typing import Tuple, NamedTuple


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

