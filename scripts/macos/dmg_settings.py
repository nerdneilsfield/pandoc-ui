# DMG build settings for pandoc-ui
# Configuration for dmgbuild tool

import os

# Get paths - since __file__ is not available in exec context, use a different approach
# The working directory should be the project root when this is executed
_project_root = os.getcwd()
_dist_dir = os.path.join(_project_root, "dist")

# Application info
app_name = "Pandoc UI"
app_bundle = f"{app_name}.app"

# Files to include in DMG - check both dist/ and dist/macos/ locations
app_bundle_path = os.path.join(_dist_dir, app_bundle)
if not os.path.exists(app_bundle_path):
    # Try the macos subdirectory
    app_bundle_path = os.path.join(_dist_dir, "macos", app_bundle)

files = [app_bundle_path]

# Create Applications symlink for easy installation
symlinks = {
    'Applications': '/Applications'
}

# Volume settings
volume_name = app_name
badge_icon = os.path.join(_project_root, "resources", "icons", "app.icns")
if not os.path.exists(badge_icon):
    badge_icon = None

# Window appearance
background_path = os.path.join(_project_root, "scripts", "macos", "background.png")
background = background_path if os.path.exists(background_path) else None
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