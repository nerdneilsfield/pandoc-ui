"""
Main entry point for pandoc-ui GUI application.
"""

import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt

from .gui.ui_components import MainWindowUI


def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
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
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Pandoc UI")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("pandoc-ui")
    
    # Enable high DPI scaling
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
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