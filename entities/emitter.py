"""
ParticleEmitter class - responsible for spawning and managing particles in the main simulation area.
"""
import pygame
import random
import math
from typing import List, TYPE_CHECKING

from entities.particle import Particle
from systems.audio import generate_spawn_sound

if TYPE_CHECKING:
    from entities.planet import Planet
    from entities.wall import Wall
    from systems.camera import Camera

class ParticleEmitter:
    def __init__(self, world_width=80000, world_height=80000):
        self.world_width = world_width
        self.world_height = world_height
        self.spawn_rate = 90  # particles per second
        self.spawn_timer = 0
        self.particles: List[Particle] = []
        self.sound_timer = 0  # To limit sound frequency

    def update(self, dt: float, planets: List['Planet'], sfx_volume: float = 0.5, camera: 'Camera' = None, gravity_distance: float = 500.0, air_resistance_intensity: float = 0.5, walls: List['Wall'] = None):
        self.spawn_timer += dt
        self.sound_timer += dt
        spawn_interval = 1.0 / self.spawn_rate
        particles_spawned = 0
        while self.spawn_timer >= spawn_interval:
            self.spawn_timer -= spawn_interval
            px = random.uniform(-self.world_width//2, self.world_width//2)
            py = random.uniform(-self.world_height//2, self.world_height//2)
            pz = random.uniform(0.3, 1.0)
            self.particles.append(Particle(px, py, pz, from_spawner=False))  # Main emitter particles fade in
            particles_spawned += 1
        # Play spawn sound for the first spawned particle (if any)
        if particles_spawned > 0 and self.sound_timer >= 0.05:
            try:
                p = self.particles[-1]
                spawn_sound = generate_spawn_sound()
                if camera:
                    dx = p.x - camera.x
                    dy = p.y - camera.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    if distance < 5000:  # Only play if reasonably close
                        volume = max(0.05, min(sfx_volume, sfx_volume * (5000 - distance) / 5000))
                        spawn_sound.set_volume(volume)
                        spawn_sound.play()
                self.sound_timer = 0
            except:
                pass  # Ignore sound errors

        # Update all particles
        for particle in self.particles[:]:  # Use slice copy for safe removal
            particle.update(dt, planets, gravity_distance, air_resistance_intensity, camera, sfx_volume, walls)
            if not particle.alive:
                self.particles.remove(particle)

    def draw(self, screen, camera: 'Camera', planets: List['Planet'] = None):
        for particle in self.particles:
            particle.draw(screen, camera, planets)
