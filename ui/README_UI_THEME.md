# CodebookAI Modern UI Theme

This document describes the Apple-inspired modern UI theme implemented for CodebookAI.

## Overview

The UI has been completely modernized with an Apple-inspired design system that follows Human Interface Guidelines while maintaining all existing functionality.

## Key Features

### 🎨 Apple Design Language
- **System Colors**: Complete implementation of Apple's system color palette
- **Typography**: Apple system fonts with proper hierarchy (Title, Headline, Body, etc.)
- **Spacing**: Consistent 8pt grid system for all layouts
- **Visual Hierarchy**: Clean, card-based layouts with proper emphasis

### 🖼️ Modern Components

#### Buttons
- **Accent Button**: Primary blue button for main actions
- **Secondary Button**: Gray button for secondary actions  
- **Icon Button**: Toolbar-style buttons with hover effects
- **Destructive Button**: Red button for destructive actions

#### Layout
- **Card Frames**: Clean white containers with subtle shadows
- **Grouped Background**: Light gray background for visual separation
- **Proper Padding**: Consistent spacing using the 8pt grid system

#### Form Elements
- **Enhanced Entries**: Better padding and focus styling
- **Modern Comboboxes**: Improved dropdown styling
- **Table Views**: Better headers, row spacing, and selection

## Usage

### Applying the Theme

```python
from ui.apple_theme import AppleTheme

# Apply theme to any tkinter window
style = AppleTheme.apply_theme(root)
root.configure(bg=AppleTheme.COLORS['grouped_background'])
```

### Using Styled Components

```python
# Buttons
ttk.Button(parent, text="Save", style="Accent.TButton")
ttk.Button(parent, text="Cancel", style="Secondary.TButton") 
ttk.Button(parent, text="⚙️", style="Icon.TButton")

# Labels
ttk.Label(parent, text="Title", style="Title.TLabel")
ttk.Label(parent, text="Body text", style="Body.TLabel")

# Frames
ttk.Frame(parent, style="Card.TFrame")
```

### Color System

```python
# Access colors
AppleTheme.COLORS['accent']           # System blue
AppleTheme.COLORS['primary_background'] # White
AppleTheme.COLORS['secondary_background'] # Light gray
AppleTheme.COLORS['destructive']      # System red
AppleTheme.COLORS['success']          # System green
```

### Typography

```python
# Get fonts
font = AppleTheme.get_font('title', 'bold')      # (font_name, size, weight)
font = AppleTheme.get_font('body')               # Regular body font
```

### Spacing

```python
# Use consistent spacing
padding = AppleTheme.SPACING['md']     # 16px
padding = AppleTheme.SPACING['lg']     # 24px
```

## File Structure

- `apple_theme.py` - Main theme implementation
- `main_window.py` - Updated main window with modern styling
- `settings_window.py` - Updated settings dialog with theme

## Design Principles

1. **Consistency**: All components follow the same visual language
2. **Hierarchy**: Clear information hierarchy through typography and spacing
3. **Accessibility**: High contrast ratios and proper touch targets
4. **Native Feel**: Feels like a native Mac/Windows application
5. **Professional**: Clean, sophisticated appearance suitable for business use

## Benefits

- **Modern Appearance**: Professional, contemporary look
- **Better UX**: Improved visual hierarchy and usability
- **Maintainable**: Clean separation of styling from logic
- **Extensible**: Easy to add new styles or adjust existing ones
- **Cross-Platform**: Works consistently across different operating systems