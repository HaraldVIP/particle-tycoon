"""
Wall class - provides a collidable line segment for particles to bounce off.
"""
import pygame
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from systems.camera import Camera

class Wall:
    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.length = math.sqrt((x2-x1)**2 + (y2-y1)**2)

    def check_collision(self, px: float, py: float, radius: float) -> bool:
        # Simple point-to-line distance check
        A = py - self.y1
        B = self.x1 - px
        C = px * self.y1 - self.x1 * py
        distance = abs(A * self.x2 + B * self.y2 + C) / math.sqrt(A*A + B*B) if A*A + B*B > 0 else float('inf')
        return distance < radius

    def draw(self, screen, camera: 'Camera', gravity_distance: float = None, air_resistance_intensity: float = None):
        sx1, sy1 = camera.world_to_screen(self.x1, self.y1)
        sx2, sy2 = camera.world_to_screen(self.x2, self.y2)
        pygame.draw.line(screen, (100, 100, 255), (sx1, sy1), (sx2, sy2), max(2, int(3 * camera.zoom)))
