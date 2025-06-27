# DMG Background Image Instructions

## Creating a Custom Background Image

To create a professional-looking DMG, you can add a custom background image:

### Image Requirements
- **Size**: 640x400 pixels (matches DMG window size)
- **Format**: PNG with transparency support
- **Content**: Should guide users to drag the app to Applications

### Suggested Design Elements
1. **App Icon**: Place the app icon on the left side
2. **Arrow**: Draw an arrow pointing from app to Applications folder
3. **Text**: "Drag Pandoc UI to Applications to install"
4. **Background**: Subtle gradient or solid color
5. **Branding**: Optional logo or project branding

### Creating the Image

#### Option 1: Using GIMP (Free)
1. Create new image: 640x400 pixels
2. Add background gradient or color
3. Import app icon (128x128 pixels)
4. Add Applications folder icon
5. Draw arrow with text
6. Export as PNG with transparency

#### Option 2: Using Figma/Canva (Online)
1. Create 640x400 canvas
2. Use design templates for DMG backgrounds
3. Customize with app icon and branding
4. Export as PNG

#### Option 3: Use Template
Create a simple background with text instructions:
- White/light background
- "Drag to Applications to Install" text
- Simple arrow graphic

### File Location
Save the background image as:
```
scripts/macos/background.png
```

### Alternative: No Background
The build script will work without a background image. The DMG will use the default Finder appearance with proper icon positioning.

## Testing the DMG Appearance

After creating the background:
1. Build the DMG using the build script
2. Mount the DMG and check the layout
3. Adjust icon positions in `dmg_settings.py` if needed
4. Rebuild until satisfied with the appearance

## Icon Positions

Current positions in `dmg_settings.py`:
- App icon: (160, 200)
- Applications link: (480, 200)

Adjust these coordinates to match your background design.