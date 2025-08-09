#!/usr/bin/env python3
"""
Particle Tycoon - Main Entry Point

A physics-based tycoon game where you place planets to collect particles and earn money!

Usage:
    python main.py

Controls:
    - Left Click & Drag: Move camera
    - Mouse Wheel: Zoom in/out
    - Buy Planet: Click green button, then click to place
    - ESC: Cancel placement or deselect
"""

if __name__ == "__main__":
    # Use the complete modular Game class
    try:
        print("Starting Particle Tycoon (Complete Modular Version)...")
        
        # Initialize Pygame
        import pygame
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # Import and run the complete game
        from core.game import Game
        
        game = Game()
        game.run()
        
        print("Game closed successfully!")
        
    except KeyboardInterrupt:
        print("\nGame closed by user")
    except Exception as e:
        print(f"Error starting game: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to close...")
