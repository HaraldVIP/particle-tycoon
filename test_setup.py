#!/usr/bin/env python3
"""Test script to verify the modular setup works correctly"""

def test_imports():
    """Test that all our new modules can be imported"""
    print("🧪 Testing module imports...")
    
    try:
        from config.constants import SCREEN_WIDTH, PARTICLE_COLORS
        print("✅ config.constants imported successfully")
        
        from systems.audio import generate_tick_sound
        print("✅ systems.audio imported successfully")
        
        from systems.assets import asset_manager
        print("✅ systems.assets imported successfully")
        
        from ui.effects import MoneyPopup, LightRay
        print("✅ ui.effects imported successfully")
        
        print("\n🎉 All modules imported successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_asset_manager():
    """Test the asset manager functionality"""
    print("\n🖼️ Testing asset manager...")
    
    try:
        from systems.assets import asset_manager
        
        # Test generating a fallback texture
        test_surface = asset_manager.get_image("test_planet", (100, 50, 200), (64, 64))
        print(f"✅ Generated fallback texture: {test_surface.get_size()}")
        
        # Test asset info
        info = asset_manager.get_asset_info()
        print(f"✅ Asset info: {info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Asset manager error: {e}")
        return False

def test_audio_system():
    """Test the audio system"""
    print("\n🔊 Testing audio system...")
    
    try:
        from systems.audio import generate_tick_sound, generate_planet_name
        
        # Test sound generation (don't play it)
        sound = generate_tick_sound()
        print(f"✅ Generated tick sound: {type(sound)}")
        
        # Test planet name generation
        name = generate_planet_name()
        print(f"✅ Generated planet name: {name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Audio system error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Particle Tycoon - Modular Setup Test")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    if test_imports():
        tests_passed += 1
        
    if test_asset_manager():
        tests_passed += 1
        
    if test_audio_system():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All systems working! Ready to run the game.")
        print("\nNext steps:")
        print("1. Run: python main.py (uses original game)")
        print("2. Install Git and set up GitHub backup")
        print("3. Continue refactoring when ready")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")
        print("You can still run the original game with: python particle_tycoon.py")

if __name__ == "__main__":
    main()
