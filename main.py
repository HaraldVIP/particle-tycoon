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
    # Import the original game file for now
    # This allows easy startup while we refactor
    import particle_tycoon
    
    # In the future, this will be:
    # from core.game import Game
    # game = Game()
    # game.run()
