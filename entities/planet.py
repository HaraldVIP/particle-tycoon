"""
Planet and DwarfPlanet classes - handles planet physics, rendering, and behavior
"""
import pygame
import random
import math
import itertools
from typing import TYPE_CHECKING

# Import constants
from config.constants import PLANET_TYPES

# Try to import gfxdraw for better performance
try:
    import pygame.gfxdraw
    HAS_GFXDRAW = True
except ImportError:
    HAS_GFXDRAW = False

# Avoid circular imports
if TYPE_CHECKING:
    from systems.camera import Camera

# Spacey planet names
SPACEY_NAMES = [
    "Nebulon", "Quasar", "Andromeda", "Pulsara", "Galaxion", "Stellara", "Cosmica", "Astrolis", "Vortexia", "Nova Prime", "Celestia", "Orbitron", "Zenith", "Eclipse", "Cometia", "Lunaris", "Solara", "Meteorix", "Auroria", "Spectra"
]
planet_name_counter = itertools.count(1)

def generate_planet_name():
    base = random.choice(SPACEY_NAMES)
    num = next(planet_name_counter)
    return f"{base}-{num}"


class DwarfPlanet:
    """A smaller, cheaper version of Planet with reduced capabilities"""
    def __init__(self, x: float, y: float, radius: float = 18):
        self.x = x
        self.y = y
        self.radius = radius
        self.base_mass = radius * 1.5
        self.gravity_level = 1
        self.mass = self.base_mass * self.gravity_level
        self.particles_collected = 0
        self.upgrade_cost = 30
        self.name = generate_planet_name()
        
        self.gravity_distance = 150
        self.air_resistance_intensity = 0.3
        self.has_clone_orbit = False

        self.planet_type = {"name": "Dwarf", "color": (139, 90, 43), "rings": False, "spots": False}
        self.color = self.planet_type["color"]
        
        self.wobble_timer = 0
        self.counter_bounce_timer = 0
        self.counter_bounce_scale = 1.0

    def collect_particle(self):
        self.particles_collected += 1
        growth_factor = 1.001
        self.radius *= growth_factor
        self.mass *= 1.0005
        self.counter_bounce_timer = 0.3
        self.counter_bounce_scale = 1.3

    def upgrade_gravity(self):
        if self.gravity_level < 3:
            self.gravity_level += 1
            self.mass = self.base_mass * self.gravity_level
            self.upgrade_cost = int(self.upgrade_cost * 1.8)

    def update(self, dt, is_hovered=False):
        if self.counter_bounce_timer > 0:
            self.counter_bounce_timer -= dt
            progress = 1.0 - (self.counter_bounce_timer / 0.3)
            if progress < 0.5:
                self.counter_bounce_scale = 1.0 + (progress * 2) * 0.3
            else:
                self.counter_bounce_scale = 1.3 - ((progress - 0.5) * 2) * 0.3
            if self.counter_bounce_timer <= 0:
                self.counter_bounce_scale = 1.0

        if is_hovered:
            self.wobble_timer += dt * 6
        else:
            self.wobble_timer = 0

    def draw(self, screen, camera: 'Camera', gravity_distance: float = None, air_resistance_intensity: float = None):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        if camera.is_map_mode():
            map_radius = max(2, int(self.radius * 0.5))
            pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), map_radius)
            return

        wobble_x = math.sin(self.wobble_timer) * 1 if self.wobble_timer > 0 else 0
        wobble_y = math.cos(self.wobble_timer * 1.3) * 1 if self.wobble_timer > 0 else 0
        screen_x += wobble_x
        screen_y += wobble_y
        
        hover_scale = 1.1 if self.wobble_timer > 0 else 1.0
        scaled_radius = max(2, int(self.radius * camera.zoom * hover_scale))
        
        margin = scaled_radius + 20
        if not (-margin < screen_x < camera.screen_width + margin and -margin < screen_y < camera.screen_height + margin):
            return
        
        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), scaled_radius)
        if self.wobble_timer > 0:
            pygame.draw.circle(screen, (200, 200, 200), (int(screen_x), int(screen_y)), scaled_radius, 2)
        pygame.draw.circle(screen, (0,0,0), (int(screen_x), int(screen_y)), scaled_radius, 1)


class Planet:
    def __init__(self, x: float, y: float, radius: float = 48):
        self.x = x
        self.y = y
        self.radius = radius
        self.base_mass = radius * 2
        self.gravity_level = 1
        self.mass = self.base_mass * self.gravity_level
        self.particles_collected = 0
        self.upgrade_cost = 75
        self.name = generate_planet_name()

        self.base_gravity_distance = 500.0
        self.gravity_distance = self.base_gravity_distance
        self.base_air_resistance_intensity = 0.5
        self.air_resistance_intensity = self.base_air_resistance_intensity

        self.has_clone_orbit = False
        self.clone_orbit_radius = self.radius * 4
        self.clone_orbit_cost = 150
        
        self.planet_type = random.choice(PLANET_TYPES)
        self.color = self.planet_type["color"]
        self.has_rings = self.planet_type["rings"]
        self.has_spots = self.planet_type["spots"]
        self.spots = []
        if self.has_spots:
            for _ in range(random.randint(2, 5)):
                self.spots.append((random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8)))
        
        self.counter_bounce_timer = 0
        self.counter_bounce_scale = 1.0
        self.shimmer_timer = 0
        self.shimmer_intensity = 0
        self.wobble_timer = 0

    def collect_particle(self):
        self.particles_collected += 1
        self.radius *= 1.002
        self.mass *= 1.001
        self.gravity_distance *= 1.001
        self.air_resistance_intensity *= 1.001
        self.clone_orbit_radius = self.radius * 4
        self.counter_bounce_timer = 0.5
        self.counter_bounce_scale = 1.5
        self.shimmer_timer = 0.3
        self.shimmer_intensity = 1.0
        return 1 # Return value of particle

    def upgrade_gravity(self):
        self.gravity_level += 1
        self.mass = self.base_mass * (1 + (self.gravity_level - 1) * 0.5)
        self.gravity_distance = self.base_gravity_distance * (1 + (self.gravity_level - 1) * 0.3)
        self.air_resistance_intensity = self.base_air_resistance_intensity * (1 + (self.gravity_level - 1) * 0.4)
        self.upgrade_cost = int(self.upgrade_cost * 1.3)
        if self.gravity_level > 1:
            intensity = min(255, 100 + (self.gravity_level - 1) * 20)
            self.color = (intensity, 149, 237)

    def upgrade_clone_orbit(self):
        self.has_clone_orbit = True
        self.clone_orbit_cost = int(self.clone_orbit_cost * 1.5)

    def update(self, dt, is_hovered=False):
        if self.counter_bounce_timer > 0:
            self.counter_bounce_timer -= dt
            progress = 1.0 - (self.counter_bounce_timer / 0.5)
            self.counter_bounce_scale = 1.0 + (progress * 2) * 0.5 if progress < 0.5 else 1.5 - ((progress - 0.5) * 2) * 0.5
            if self.counter_bounce_timer <= 0: self.counter_bounce_scale = 1.0

        if self.shimmer_timer > 0:
            self.shimmer_timer -= dt
            self.shimmer_intensity = self.shimmer_timer / 0.3
            if self.shimmer_timer <= 0: self.shimmer_intensity = 0

        if is_hovered:
            self.wobble_timer += dt * 8
        else:
            self.wobble_timer = 0

    def draw(self, screen, camera: 'Camera', gravity_distance: float = None, air_resistance_intensity: float = None):
        wobble_x = math.sin(self.wobble_timer) * 2 if self.wobble_timer > 0 else 0
        wobble_y = math.cos(self.wobble_timer * 1.3) * 2 if self.wobble_timer > 0 else 0
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        screen_x += wobble_x
        screen_y += wobble_y
        
        hover_scale = 1.15 if self.wobble_timer > 0 else 1.0
        
        if camera.is_map_mode():
            map_radius = max(4, int(self.radius * 0.7))
            pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), map_radius)
            return

        scaled_radius = max(2, int(self.radius * camera.zoom * hover_scale))
        air_radius = max(4, int(self.radius * 3 * camera.zoom * hover_scale))
        
        margin = air_radius + 50
        if not (-margin < screen_x < camera.screen_width + margin and -margin < screen_y < camera.screen_height + margin):
            return
        
        # Optimization: Don't draw complex effects when zoomed out
        if camera.zoom > 0.3:
            if self.has_rings:
                ring_radius1 = int(scaled_radius * 1.4)
                ring_radius2 = int(scaled_radius * 1.6)
                ring_color = tuple(c // 2 for c in self.color)
                pygame.draw.circle(screen, ring_color, (screen_x, screen_y), ring_radius2, max(1, int(3 * camera.zoom)))
                pygame.draw.circle(screen, ring_color, (screen_x, screen_y), ring_radius1, max(1, int(2 * camera.zoom)))

        pygame.draw.circle(screen, self.color, (screen_x, screen_y), scaled_radius)

        if camera.zoom > 0.5 and self.has_spots:
            spot_color = tuple(max(0, c - 40) for c in self.color)
            for spot_x_ratio, spot_y_ratio in self.spots:
                spot_x = screen_x + int(spot_x_ratio * scaled_radius * 0.7)
                spot_y = screen_y + int(spot_y_ratio * scaled_radius * 0.7)
                spot_radius = max(1, int(scaled_radius * 0.15))
                pygame.draw.circle(screen, spot_color, (spot_x, spot_y), spot_radius)
        
        outline_color = (255,255,255) if self.shimmer_intensity > 0 else (0,0,0)
        pygame.draw.circle(screen, outline_color, (screen_x, screen_y), scaled_radius, max(1, int(2 * camera.zoom)))

        if camera.zoom > 0.2:
            font_size = max(12, int(20 * camera.zoom))
            font = pygame.font.Font(None, font_size)
            text = font.render(str(self.particles_collected), True, WHITE)
            text_rect = text.get_rect(center=(screen_x, screen_y - int(3 * camera.zoom)))
            screen.blit(text, text_rect)
            if self.gravity_level > 1:
                level_font = pygame.font.Font(None, max(10, int(16 * camera.zoom)))
                level_text = level_font.render(f"G{self.gravity_level}", True, YELLOW)
                level_rect = level_text.get_rect(center=(screen_x, screen_y + int(8 * camera.zoom)))
                screen.blit(level_text, level_rect)
