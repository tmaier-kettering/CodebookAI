"""
Apple-inspired modern theme for tkinter/ttk applications.
Provides colors, fonts, and styling consistent with Apple's design language.
"""

import tkinter as tk
from tkinter import ttk
import platform


class AppleTheme:
    """Apple-inspired color scheme and styling constants."""
    
    # Apple-inspired color palette
    COLORS = {
        # System colors
        'system_blue': '#007AFF',
        'system_green': '#34C759', 
        'system_indigo': '#5856D6',
        'system_orange': '#FF9500',
        'system_pink': '#FF2D92',
        'system_purple': '#AF52DE',
        'system_red': '#FF3B30',
        'system_teal': '#30B0C7',
        'system_yellow': '#FFCC00',
        
        # Gray colors (light mode)
        'system_gray': '#8E8E93',
        'system_gray2': '#AEAEB2', 
        'system_gray3': '#C7C7CC',
        'system_gray4': '#D1D1D6',
        'system_gray5': '#E5E5EA',
        'system_gray6': '#F2F2F7',
        
        # Background colors
        'primary_background': '#FFFFFF',
        'secondary_background': '#F2F2F7',
        'tertiary_background': '#FFFFFF',
        'grouped_background': '#F2F2F7',
        
        # Label colors
        'label': '#000000',
        'secondary_label': '#3C3C43',
        'tertiary_label': '#3C3C43',
        'quaternary_label': '#3C3C43',
        
        # Fill colors
        'quaternary_system_fill': '#F2F2F7',
        'tertiary_system_fill': '#E5E5EA',
        'secondary_system_fill': '#D1D1D6',
        'system_fill': '#C7C7CC',
        
        # Separator colors
        'separator': '#C6C6C8',
        'opaque_separator': '#C6C6C8',
        
        # Link color
        'link': '#007AFF',
        
        # Special colors for our app
        'accent': '#007AFF',  # System blue
        'destructive': '#FF3B30',  # System red
        'success': '#34C759',  # System green
        'warning': '#FF9500',  # System orange
    }
    
    # Typography
    FONTS = {
        'system': '.AppleSystemUIFont' if platform.system() == 'Darwin' else 'Segoe UI',
        'system_size': 13,
        'title_size': 20,
        'headline_size': 17,
        'body_size': 17,
        'callout_size': 16,
        'subhead_size': 15,
        'footnote_size': 13,
        'caption_size': 12,
    }
    
    # Spacing and dimensions (Apple uses 8pt grid system)
    SPACING = {
        'xs': 4,   # 0.5 * 8
        'sm': 8,   # 1 * 8
        'md': 16,  # 2 * 8
        'lg': 24,  # 3 * 8
        'xl': 32,  # 4 * 8
        'xxl': 48, # 6 * 8
    }
    
    # Border radius (Apple uses subtle rounded corners)
    BORDER_RADIUS = {
        'sm': 4,
        'md': 8,
        'lg': 12,
        'xl': 16,
    }

    @classmethod
    def apply_theme(cls, root: tk.Tk) -> ttk.Style:
        """Apply Apple-inspired theme to the application."""
        style = ttk.Style()
        
        # Configure the overall theme based on available themes
        available_themes = style.theme_names()
        if 'aqua' in available_themes:  # macOS
            style.theme_use('aqua')
        elif 'vista' in available_themes:  # Windows Vista/7/8/10/11
            style.theme_use('vista') 
        elif 'clam' in available_themes:  # Modern alternative
            style.theme_use('clam')
        else:
            style.theme_use('default')
        
        # Configure root window
        root.configure(bg=cls.COLORS['grouped_background'])
        
        # Frame styles
        style.configure('Card.TFrame',
                       background=cls.COLORS['primary_background'],
                       relief='flat',
                       borderwidth=1)
        
        style.configure('Sidebar.TFrame',
                       background=cls.COLORS['secondary_background'],
                       relief='flat')
        
        # Label styles  
        style.configure('Title.TLabel',
                       background=cls.COLORS['primary_background'],
                       foreground=cls.COLORS['label'],
                       font=(cls.FONTS['system'], cls.FONTS['title_size'], 'bold'))
        
        style.configure('Headline.TLabel',
                       background=cls.COLORS['primary_background'],
                       foreground=cls.COLORS['label'],
                       font=(cls.FONTS['system'], cls.FONTS['headline_size'], 'bold'))
        
        style.configure('Body.TLabel',
                       background=cls.COLORS['primary_background'],
                       foreground=cls.COLORS['label'],
                       font=(cls.FONTS['system'], cls.FONTS['body_size']))
        
        style.configure('Secondary.TLabel',
                       background=cls.COLORS['primary_background'],
                       foreground=cls.COLORS['secondary_label'],
                       font=(cls.FONTS['system'], cls.FONTS['body_size']))
        
        # Button styles with improved padding and modern appearance
        style.configure('Accent.TButton',
                       background=cls.COLORS['accent'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=(cls.FONTS['system'], cls.FONTS['body_size'], 'bold'),
                       padding=(16, 8))  # Better padding
        
        style.map('Accent.TButton',
                 background=[('active', cls._darken_color(cls.COLORS['accent'])),
                           ('pressed', cls._darken_color(cls.COLORS['accent'], 0.2))],
                 relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        
        style.configure('Secondary.TButton',
                       background=cls.COLORS['quaternary_system_fill'],
                       foreground=cls.COLORS['label'],
                       borderwidth=0,
                       focuscolor='none',
                       font=(cls.FONTS['system'], cls.FONTS['body_size']),
                       padding=(16, 8))  # Better padding
        
        style.map('Secondary.TButton',
                 background=[('active', cls.COLORS['tertiary_system_fill']),
                           ('pressed', cls.COLORS['secondary_system_fill'])],
                 relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        
        style.configure('Destructive.TButton',
                       background=cls.COLORS['destructive'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=(cls.FONTS['system'], cls.FONTS['body_size'], 'bold'),
                       padding=(16, 8))  # Better padding
        
        style.map('Destructive.TButton',
                 background=[('active', cls._darken_color(cls.COLORS['destructive'])),
                           ('pressed', cls._darken_color(cls.COLORS['destructive'], 0.2))],
                 relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        
        # Icon button style (for toolbar buttons) - more Apple-like
        style.configure('Icon.TButton',
                       background=cls.COLORS['primary_background'],
                       foreground=cls.COLORS['accent'],
                       borderwidth=1,
                       bordercolor=cls.COLORS['separator'],
                       focuscolor='none',
                       font=(cls.FONTS['system'], 18),  # Larger icons
                       width=4,
                       padding=(12, 8))  # Better padding
        
        style.map('Icon.TButton',
                 background=[('active', cls.COLORS['quaternary_system_fill']),
                           ('pressed', cls.COLORS['tertiary_system_fill'])],
                 bordercolor=[('active', cls.COLORS['accent']),
                            ('pressed', cls.COLORS['accent'])],
                 relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        
        # Entry styles with rounded appearance
        style.configure('TEntry',
                       fieldbackground=cls.COLORS['primary_background'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=cls.COLORS['separator'],
                       focuscolor=cls.COLORS['accent'],
                       font=(cls.FONTS['system'], cls.FONTS['body_size']),
                       padding=(12, 8))  # Better internal padding
        
        style.map('TEntry',
                 bordercolor=[('focus', cls.COLORS['accent'])],
                 lightcolor=[('focus', cls.COLORS['accent'])],
                 darkcolor=[('focus', cls.COLORS['accent'])])
        
        # Combobox styles with Apple-like appearance
        style.configure('TCombobox',
                       fieldbackground=cls.COLORS['primary_background'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=cls.COLORS['separator'],
                       focuscolor=cls.COLORS['accent'],
                       font=(cls.FONTS['system'], cls.FONTS['body_size']),
                       padding=(12, 8),  # Better internal padding
                       arrowcolor=cls.COLORS['secondary_label'])
        
        style.map('TCombobox',
                 bordercolor=[('focus', cls.COLORS['accent'])],
                 arrowcolor=[('active', cls.COLORS['accent'])])
        
        # Notebook (tabs) styles
        style.configure('TNotebook',
                       background=cls.COLORS['primary_background'],
                       borderwidth=0,
                       tabmargins=[0, 0, 0, 0])
        
        style.configure('TNotebook.Tab',
                       background=cls.COLORS['quaternary_system_fill'],
                       foreground=cls.COLORS['secondary_label'],
                       borderwidth=0,
                       focuscolor='none',
                       font=(cls.FONTS['system'], cls.FONTS['body_size']),
                       padding=[16, 8])
        
        style.map('TNotebook.Tab',
                 background=[('selected', cls.COLORS['primary_background']),
                           ('active', cls.COLORS['tertiary_system_fill'])],
                 foreground=[('selected', cls.COLORS['label'])])
        
        # Treeview styles with alternating row colors (Apple-like)
        style.configure('Treeview',
                       background=AppleTheme.COLORS['primary_background'],
                       foreground=AppleTheme.COLORS['label'],
                       fieldbackground=AppleTheme.COLORS['primary_background'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=AppleTheme.COLORS['separator'],
                       font=(AppleTheme.FONTS['system'], AppleTheme.FONTS['body_size']),
                       rowheight=32)  # Increase row height for better spacing
        
        style.map('Treeview',
                 background=[('selected', AppleTheme.COLORS['accent']),
                           ('focus', AppleTheme.COLORS['accent'])],
                 foreground=[('selected', 'white'),
                           ('focus', 'white')])
        
        # Configure alternating row colors
        style.configure('Treeview',
                       background=AppleTheme.COLORS['primary_background'])
        
        style.configure('Treeview.Heading',
                       background=AppleTheme.COLORS['secondary_background'],
                       foreground=AppleTheme.COLORS['secondary_label'],
                       borderwidth=0,
                       relief='flat',
                       font=(AppleTheme.FONTS['system'], AppleTheme.FONTS['footnote_size'], 'bold'),
                       padding=(12, 8))  # Add padding to headers
        
        # Scrollbar styles
        style.configure('TScrollbar',
                       background=cls.COLORS['quaternary_system_fill'],
                       borderwidth=0,
                       arrowcolor=cls.COLORS['secondary_label'],
                       troughcolor=cls.COLORS['secondary_background'])
        
        return style
    
    @staticmethod
    def _darken_color(hex_color: str, factor: float = 0.1) -> str:
        """Darken a hex color by the given factor."""
        # Remove the '#' if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Darken each component
        darkened = tuple(max(0, min(255, int(c * (1 - factor)))) for c in rgb)
        
        # Convert back to hex
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"

    @classmethod
    def get_font(cls, style: str = 'body', weight: str = 'normal') -> tuple:
        """Get a font tuple for the given style and weight."""
        size = cls.FONTS.get(f'{style}_size', cls.FONTS['body_size'])
        return (cls.FONTS['system'], size, weight)