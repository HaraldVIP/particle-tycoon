"""
ParticleSpawner class - a placeable entity that spawns particles at a fixed location.
"""
import pygame
import random
from typing import List, TYPE_CHECKING

from entities.particle import Particle

if TYPE_CHECKING:
    from entities.planet import Planet
    from entities.wall import Wall
    from systems.camera import Camera

class ParticleSpawner:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.spawn_rate = 5  # particles per second
        self.spawn_timer = 0
        self.particles: List[Particle] = []

    def update(self, dt: float, planets: List['Planet'], sfx_volume: float = 0.5, camera: 'Camera' = None, gravity_distance: float = 500.0, air_resistance_intensity: float = 0.5, walls: List['Wall'] = None):
        self.spawn_timer += dt
        spawn_interval = 1.0 / self.spawn_rate
        while self.spawn_timer >= spawn_interval:
            self.spawn_timer -= spawn_interval
            # Spawn near the spawner
            px = self.x + random.uniform(-50, 50)
            py = self.y + random.uniform(-50, 50)
            pz = random.uniform(0.3, 1.0)
            self.particles.append(Particle(px, py, pz, from_spawner=True))  # Spawner particles don't fade in

        # Update all particles
        for particle in self.particles[:]:  # Use slice copy for safe removal
            particle.update(dt, planets, gravity_distance, air_resistance_intensity, camera, sfx_volume, walls)
            if not particle.alive:
                self.particles.remove(particle)

    def draw(self, screen, camera: 'Camera', planets: List['Planet'] = None):
        # Draw the spawner itself
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        pygame.draw.circle(screen, (255, 255, 0), (int(screen_x), int(screen_y)), max(3, int(8 * camera.zoom)))
        pygame.draw.circle(screen, (255, 255, 255), (int(screen_x), int(screen_y)), max(3, int(8 * camera.zoom)), 2)

        # Draw particles
        for particle in self.particles:
            particle.draw(screen, camera, planets)
