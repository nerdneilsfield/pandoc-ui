"""
Pytest configuration and fixtures for pandoc-ui tests.
"""

import os
import pytest
from PySide6.QtWidgets import QApplication


def pytest_configure(config):
    """Configure pytest for GUI testing."""
    # Set headless mode for all GUI tests
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'


@pytest.fixture(scope="session")
def qapp_session():
    """Session-scoped QApplication fixture."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app here as it may be used by other tests


@pytest.fixture
def qapp(qapp_session):
    """Test-scoped QApplication fixture."""
    yield qapp_session
    # Process any pending events after each test
    qapp_session.processEvents()