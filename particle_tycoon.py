"""
This file is deprecated and will be removed in a future version.
Please run main.py instead.
"""

import sys
import os
import pygame

# Add the root directory to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from core.game import Game
except ImportError as e:
    print("Error: Could not import the main game from core.game.")
    print("Please ensure that the new modular structure is intact.")
    print(f"Import Error: {e}")
    pygame.quit()
    sys.exit(1)

if __name__ == "__main__":
    print("="*80)
    print("WARNING: You are running particle_tycoon.py, which is deprecated.")
    print("Running the new modular game from main.py instead...")
    print("="*80)

    # Initialize Pygame and run the new game from core.game
    try:
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        game = Game()
        game.run()
    except Exception as e:
        print(f"An error occurred while running the game: {e}")
        pygame.quit()
        sys.exit(1)
    finally:
        pygame.quit()
        sys.exit(0)
