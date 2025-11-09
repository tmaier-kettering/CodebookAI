#!/usr/bin/env python3
"""
Smoke test for CustomTkinter migration.
Tests basic UI functionality without requiring API keys or full setup.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    try:
        import customtkinter as ctk
        print("  ✓ customtkinter imported")
        
        from ui.theme_config import initialize_theme, get_title_font
        print("  ✓ theme_config imported")
        
        from ui.dialogs import show_info, show_error, ask_open_filename
        print("  ✓ dialogs imported")
        
        from ui.tooltip import ToolTip
        print("  ✓ tooltip imported")
        
        from ui.ui_utils import center_window
        print("  ✓ ui_utils imported")
        
        from ui.progress_ui import ProgressController
        print("  ✓ progress_ui imported")
        
        print("✅ All imports successful\n")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}\n")
        return False


def test_theme_init():
    """Test theme initialization."""
    print("Testing theme initialization...")
    try:
        from ui.theme_config import initialize_theme, DEFAULT_THEME_MODE
        initialize_theme()
        print(f"  ✓ Theme initialized with mode: {DEFAULT_THEME_MODE}")
        print("✅ Theme initialization successful\n")
        return True
    except Exception as e:
        print(f"❌ Theme initialization failed: {e}\n")
        return False


def test_basic_window():
    """Test creating a basic CTk window."""
    print("Testing basic window creation...")
    try:
        import customtkinter as ctk
        from ui.theme_config import initialize_theme
        
        # Initialize theme
        initialize_theme()
        
        # Create window
        root = ctk.CTk()
        root.title("Smoke Test")
        root.geometry("400x300")
        
        # Add some widgets
        label = ctk.CTkLabel(root, text="CustomTkinter Smoke Test")
        label.pack(pady=20)
        
        button = ctk.CTkButton(root, text="Close", command=root.destroy)
        button.pack(pady=10)
        
        print("  ✓ Window created successfully")
        print("  ✓ Widgets created and packed")
        
        # Close immediately for automated testing
        root.after(100, root.destroy)
        root.mainloop()
        
        print("✅ Basic window test successful\n")
        return True
    except Exception as e:
        print(f"❌ Window creation failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_tooltip():
    """Test tooltip functionality."""
    print("Testing tooltip...")
    try:
        import customtkinter as ctk
        from ui.tooltip import ToolTip
        from ui.theme_config import initialize_theme
        
        initialize_theme()
        root = ctk.CTk()
        
        button = ctk.CTkButton(root, text="Hover me")
        button.pack(pady=20)
        
        tooltip = ToolTip(button, "This is a tooltip")
        
        print("  ✓ Tooltip created successfully")
        
        root.after(100, root.destroy)
        root.mainloop()
        
        print("✅ Tooltip test successful\n")
        return True
    except Exception as e:
        print(f"❌ Tooltip test failed: {e}\n")
        return False


def test_progress_window():
    """Test progress window."""
    print("Testing progress window...")
    try:
        import customtkinter as ctk
        from ui.progress_ui import ProgressController
        from ui.theme_config import initialize_theme
        
        initialize_theme()
        root = ctk.CTk()
        root.withdraw()  # Hide root
        
        # Create progress window
        progress = ProgressController.open(root, total_count=10, title="Test Progress")
        
        # Update a few times
        for i in range(1, 6):
            progress.update(i, f"Processing item {i}")
        
        progress.close()
        
        print("  ✓ Progress window created and updated")
        
        root.destroy()
        
        print("✅ Progress window test successful\n")
        return True
    except Exception as e:
        print(f"❌ Progress window test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("CustomTkinter Migration Smoke Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Theme Init", test_theme_init),
        ("Basic Window", test_basic_window),
        ("Tooltip", test_tooltip),
        ("Progress Window", test_progress_window),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}\n")
            results.append((name, False))
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All smoke tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
