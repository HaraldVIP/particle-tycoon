"""Game constants and configuration values"""
import pygame

# Initialize Pygame for display info
pygame.init()

# Get system resolution
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
FPS = 60

# Planet visual types
PLANET_TYPES = [
    {"name": "Rocky", "color": (139, 69, 19), "rings": False, "spots": True},
    {"name": "Gas Giant", "color": (255, 140, 0), "rings": True, "spots": False},
    {"name": "Ice World", "color": (173, 216, 230), "rings": False, "spots": False},
    {"name": "Desert", "color": (238, 203, 173), "rings": False, "spots": True},
    {"name": "Ocean", "color": (0, 105, 148), "rings": False, "spots": False},
    {"name": "Volcanic", "color": (178, 34, 34), "rings": False, "spots": True},
    {"name": "Forest", "color": (34, 139, 34), "rings": False, "spots": False},
    {"name": "Crystal", "color": (147, 0, 211), "rings": True, "spots": False},
]

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (100, 149, 237)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)

# World simulation limit (for despawn bounds)
WORLD_LIMIT = 100000  # Very large world boundary to avoid premature despawn

# Map boundary for visual border - match particle spawn area
MAP_BOUNDARY = 40000  # Visible red border boundary (matches particle spawn area)

# Particle colors
PARTICLE_COLORS = [
    (255, 100, 100),  # Light red
    (100, 255, 100),  # Light green
    (100, 100, 255),  # Light blue
    (255, 255, 100),  # Light yellow
    (255, 100, 255),  # Light magenta
    (100, 255, 255),  # Light cyan
    (255, 150, 100),  # Orange
    (150, 100, 255),  # Purple
]

# Game costs and settings
PLANET_BASE_COST = 40
DWARF_PLANET_COST = 15
SPAWNER_COST = 200
SPAWN_RATE_COST = 100
WALL_COST_PER_UNIT = 0.5

# Default game settings
DEFAULT_SFX_VOLUME = 0.5
DEFAULT_MUSIC_VOLUME = 1.0
DEFAULT_GRAVITY_DISTANCE = 1000.0
DEFAULT_AIR_RESISTANCE = 0.1
