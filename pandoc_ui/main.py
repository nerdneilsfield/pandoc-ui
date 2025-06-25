"""
Main entry point for pandoc-ui GUI application.
"""

import argparse
import logging
import os
import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from pandoc_ui.gui.ui_components import MainWindowUI


def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


class PandocUIMainWindow(QMainWindow):
    """Main application window inheriting from QMainWindow."""

    def __init__(self, parent=None):
        """Initialize main window."""
        super().__init__(parent)

        # Initialize UI components
        self.ui_handler = MainWindowUI(self)

    def closeEvent(self, event):
        """Handle window close event."""
        if self.ui_handler.handleWindowClose():
            event.accept()
        else:
            event.ignore()


def main():
    """Main application entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Pandoc UI - Graphical interface for document conversion")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with console output")
    parser.add_argument("--version", action="version", version="Pandoc UI 0.1.0")
    args = parser.parse_args()
    
    # Windows console allocation for debugging
    if args.debug and sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.AllocConsole()
            # Redirect stdout and stderr to console
            sys.stdout = open('CONOUT$', 'w')
            sys.stderr = open('CONOUT$', 'w')
            print("🐛 Debug console allocated")
        except Exception as e:
            pass  # Ignore console allocation errors
    
    # Setup logging
    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
    else:
        setup_logging()
    
    logger = logging.getLogger(__name__)
    
    if args.debug:
        logger.debug("Debug mode enabled")
        logger.debug(f"Platform: {sys.platform}")
        logger.debug(f"Python version: {sys.version}")
        logger.debug(f"Command line args: {sys.argv}")

    # Force Qt platform plugin for WSL compatibility
    if not os.environ.get("QT_QPA_PLATFORM"):
        # Check for WSL environment
        is_wsl = (
            os.environ.get("WSL_DISTRO_NAME")
            or os.environ.get("WSL_INTEROP")
            or "microsoft" in os.uname().release.lower()
            if hasattr(os, "uname")
            else False
        )
        if is_wsl:
            os.environ["QT_QPA_PLATFORM"] = "xcb"
            logger.info("WSL detected, setting Qt platform to xcb")

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Pandoc UI")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("pandoc-ui")

    # High DPI scaling is enabled by default in Qt 6
    # The AA_EnableHighDpiScaling and AA_UseHighDpiPixmaps attributes are deprecated in Qt 6
    logger.info("High DPI scaling enabled by default in Qt 6")

    try:
        # Create and show main window
        logger.info("Starting Pandoc UI application...")
        main_window = PandocUIMainWindow()
        main_window.show()

        logger.info("Application window displayed")

        # Run application event loop
        exit_code = app.exec()
        logger.info(f"Application exiting with code: {exit_code}")

        return exit_code

    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
