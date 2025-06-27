# DMG build settings for pandoc-ui
# Configuration for dmgbuild tool

import os

# Get the directory containing this file
_settings_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_settings_dir))

# Application info
app_name = "Pandoc UI"
app_bundle = f"{app_name}.app"

# Files to include in DMG
files = [os.path.join(_project_root, "dist", app_bundle)]

# Create Applications symlink for easy installation
symlinks = {
    'Applications': '/Applications'
}

# Volume settings
volume_name = app_name
badge_icon = os.path.join(_project_root, "resources", "icons", "app.icns")

# Window appearance
background = os.path.join(_settings_dir, "background.png")
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
sidebar_width = 180

# Window geometry: ((x, y), (width, height))
window_rect = ((100, 100), (640, 400))

# Icon positions: {filename: (x, y)}
icon_locations = {
    app_bundle: (160, 200),
    'Applications': (480, 200)
}

# Icon view settings
default_view = 'icon-view'
icon_size = 128
text_size = 16

# Layout
arrange_by = None
grid_offset = (0, 0)
grid_spacing = 100
scroll_position = (0, 0)
label_pos = 'bottom'  # or 'right'

# License (optional)
# license_file = os.path.join(_project_root, "LICENSE")

# Format
format = 'UDZO'  # Compressed
compression_level = 9

# Additional options
include_icon_view_settings = 'auto'
include_list_view_settings = 'auto'