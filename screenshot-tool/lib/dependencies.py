"""
Dependency management for the screenshot tool.

Handles checking, installing, and importing PyObjC dependencies.
"""

import sys
import subprocess
from typing import List, Optional

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
    """Install required dependencies using pip.
    
    Args:
        quiet: If True, suppress output
        
    Returns:
        True if installation succeeded
    """
    if not quiet:
        print("Installing required dependencies...")
        print(f"Packages: {', '.join(REQUIRED_PACKAGES)}")
        print()
    
    try:
        python_exe = sys.executable
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
    """Prompt user to install dependencies.
    
    Returns:
        True if user chose to install and installation succeeded
    """
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


def check_installed_packages() -> bool:
    """Check and print the status of all required packages.
    
    Returns:
        True if all packages are OK
    """
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
    
    return all("OK" in status for _, status in packages_status)


def handle_import_error(import_error: Exception):
    """Handle PyObjC import failure.
    
    Determines if packages are installed but can't be loaded (sandbox issue)
    or if they need to be installed.
    
    Args:
        import_error: The ImportError that occurred
    """
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
        print(f"Import error: {import_error}")
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


def handle_early_flags():
    """Handle --install and --check-installed flags before importing PyObjC.
    
    This should be called early in the main script, before trying to import
    PyObjC modules.
    
    Returns:
        True if a flag was handled (and script should exit), False otherwise
    """
    if "--install" in sys.argv:
        success = install_dependencies()
        sys.exit(0 if success else 1)
    
    if "--check-installed" in sys.argv:
        all_ok = check_installed_packages()
        sys.exit(0 if all_ok else 1)
    
    return False


def check_accessibility_permissions() -> bool:
    """Check if the app has accessibility permissions for event monitoring.
    
    If permissions are missing, prints instructions and attempts to open
    System Preferences.
    
    Returns:
        True if permissions are granted
    """
    # Import here since this is only called after PyObjC is confirmed available
    from Quartz import CGPreflightListenEventAccess, CGRequestListenEventAccess
    import os
    
    try:
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


