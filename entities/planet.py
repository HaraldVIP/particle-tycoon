"""
Planet and DwarfPlanet classes - handles planet physics, rendering, and behavior
"""
import pygame
import random
import math
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
    pass


class DwarfPlanet:
    """A smaller, cheaper version of Planet with reduced capabilities"""
    def __init__(self, x: float, y: float, radius: float = 20):
        self.x = x
        self.y = y
        self.radius = radius
        self.mass = radius * 0.8  # Lighter than regular planets
        self.gravity_distance = 300  # Shorter gravity reach
        
        # Visual properties - simpler than regular planets
        self.planet_type = random.choice(PLANET_TYPES)
        self.color = self.planet_type["color"]
        
        # Hover effect
        self.wobble_timer = 0
        
        # Collection stats
        self.particles_collected = 0
        self.money_generated = 0.0

    def update(self, dt, is_hovered=False):
        """Update dwarf planet state"""
        # Hover wobble effect
        if is_hovered:
            self.wobble_timer += dt * 8  # Faster wobble for dwarf planets
            if self.wobble_timer > 2 * math.pi:
                self.wobble_timer -= 2 * math.pi
        else:
            self.wobble_timer = 0

    def draw(self, screen, camera, gravity_distance: float = None, air_resistance_intensity: float = None):
        """Draw the dwarf planet (simplified)"""
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        if camera.is_map_mode():
            # In map mode, draw a simple small circle
            map_radius = max(2, int(self.radius * 0.5)) # Smaller and fixed size
            pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), map_radius)
            return

        # Convert world position to screen position with wobble
        wobble_x = math.sin(self.wobble_timer) * 1.5 if self.wobble_timer > 0 else 0
        wobble_y = math.cos(self.wobble_timer * 1.2) * 1.5 if self.wobble_timer > 0 else 0
        screen_x += wobble_x
        screen_y += wobble_y
        
        # Scale with zoom and hover effect
        hover_scale = 1.1 if self.wobble_timer > 0 else 1.0
        scaled_radius = max(2, int(self.radius * camera.zoom * hover_scale))
        
        # Only draw if visible
        margin = scaled_radius + 20
        if (screen_x < -margin or screen_x > camera.screen_width + margin or 
            screen_y < -margin or screen_y > camera.screen_height + margin):
            return
        
        # Draw simple planet (no atmosphere for dwarf planets)
        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), scaled_radius)
        
        # Add simple spots if the type has them
        if self.planet_type["spots"] and scaled_radius > 4:
            spot_color = tuple(max(0, c - 30) for c in self.color)
            for _ in range(2):  # Fewer spots than regular planets
                spot_angle = random.uniform(0, 2 * math.pi)
                spot_distance = random.uniform(0.2, 0.6) * scaled_radius
                spot_x = int(screen_x + math.cos(spot_angle) * spot_distance)
                spot_y = int(screen_y + math.sin(spot_angle) * spot_distance)
                spot_radius = max(1, scaled_radius // 6)
                pygame.draw.circle(screen, spot_color, (spot_x, spot_y), spot_radius)
        
        # Simple outline
        outline_color = tuple(max(0, c - 50) for c in self.color)
        pygame.draw.circle(screen, outline_color, (int(screen_x), int(screen_y)), scaled_radius, 2)

    def draw_preview(self, screen, x, y, size=16):
        """Draw a small preview of the dwarf planet for the UI"""
        # Draw base (simpler than Planet)
        pygame.draw.circle(screen, self.color, (x, y), size)
        
        # Simple outline
        outline_color = tuple(max(0, c - 50) for c in self.color)
        pygame.draw.circle(screen, outline_color, (x, y), size, 1)


class Planet:
    def __init__(self, x: float, y: float, radius: float = 48):  # 4x bigger than original
        self.x = x
        self.y = y
        self.radius = radius
        self.mass = radius * 2.0  # Mass affects gravity
        self.gravity_distance = 500  # How far gravity reaches
        
        # Visual properties
        self.planet_type = random.choice(PLANET_TYPES)
        self.color = self.planet_type["color"]
        self.has_rings = self.planet_type["rings"]
        self.has_spots = self.planet_type["spots"]
        
        # Generate consistent spots for this planet
        self.spots = []
        if self.has_spots:
            num_spots = random.randint(3, 7)
            for _ in range(num_spots):
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(0.2, 0.8)
                size = random.uniform(0.1, 0.25)
                self.spots.append((angle, distance, size))
        
        # Ring properties
        if self.has_rings:
            self.ring_inner_radius = 1.3
            self.ring_outer_radius = 1.8
            self.ring_color = tuple(max(0, c - 40) for c in self.color)
        
        # Hover effect
        self.wobble_timer = 0
        
        # Collection tracking
        self.particles_collected = 0
        self.money_generated = 0.0
        
        # Performance optimization
        self._cached_spots = None
        self._cached_radius = None

    def update(self, dt, is_hovered=False):
        """Update planet state"""
        # Hover wobble effect
        if is_hovered:
            self.wobble_timer += dt * 5  # Wobble speed
            if self.wobble_timer > 2 * math.pi:
                self.wobble_timer -= 2 * math.pi
        else:
            self.wobble_timer = 0

    def draw(self, screen, camera, gravity_distance: float = None, air_resistance_intensity: float = None):
        """Render the planet with optimized performance"""
        # Convert world position to screen position with wobble effect
        wobble_x = math.sin(self.wobble_timer) * 2 if self.wobble_timer > 0 else 0
        wobble_y = math.cos(self.wobble_timer * 1.3) * 2 if self.wobble_timer > 0 else 0
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        screen_x += wobble_x
        screen_y += wobble_y
        
        # Scale radius with zoom and hover effect
        hover_scale = 1.15 if self.wobble_timer > 0 else 1.0
        
        if camera.is_map_mode():
            # In map mode, draw a simple larger circle
            map_radius = max(4, int(self.radius * 0.7)) # Larger and fixed size
            pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), map_radius)
            return
        else:
            # Normal mode - scale with camera zoom
            scaled_radius = max(2, int(self.radius * camera.zoom * hover_scale))
            air_radius = max(4, int(self.radius * 3 * camera.zoom * hover_scale))
        
        # Only draw if planet is visible on screen
        margin = air_radius + 50
        if (screen_x < -margin or screen_x > camera.screen_width + margin or 
            screen_y < -margin or screen_y > camera.screen_height + margin):
            return
        
        # Draw atmospheric area - OPTIMIZED FOR PERFORMANCE
        if camera.zoom > 0.4 and camera.zoom < 3.0 and air_radius > 4 and air_radius < 200:
            # Use direct drawing instead of creating surfaces for better performance
            for i in range(3):
                atmo_radius = air_radius - (i * air_radius // 4)
                if atmo_radius > 2:
                    alpha = max(5, 15 - (i * 5))  # Decreasing alpha: 15, 10, 5
                    # Use pygame.gfxdraw for better alpha blending performance
                    if HAS_GFXDRAW:
                        pygame.gfxdraw.filled_circle(screen, int(screen_x), int(screen_y), atmo_radius, (100, 150, 255, alpha))
                    else:
                        # Fallback to regular circle if gfxdraw not available
                        atmo_surf = pygame.Surface((atmo_radius * 2, atmo_radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(atmo_surf, (100, 150, 255, alpha), (atmo_radius, atmo_radius), atmo_radius)
                        screen.blit(atmo_surf, (screen_x - atmo_radius, screen_y - atmo_radius))

        # Debug rings for gravity and air resistance ranges - disable when heavily zoomed in
        if camera.zoom > 0.15 and camera.zoom < 4.0:
            # Gravity max distance ring
            grav_r = max(1, int(self.gravity_distance * camera.zoom))
            if grav_r > 3:  # Only draw if large enough to be visible
                grav_surf = pygame.Surface((grav_r * 2 + 4, grav_r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(grav_surf, (0, 255, 0, 80), (grav_r + 2, grav_r + 2), grav_r, 2)
                screen.blit(grav_surf, (screen_x - grav_r - 2, screen_y - grav_r - 2))
                
                # Gravity fade zone outer ring (+200)
                outer_r = max(grav_r + int(200 * camera.zoom), grav_r + 1)
                if outer_r > grav_r + 2:  # Only draw if significantly larger
                    outer_surf = pygame.Surface((outer_r * 2 + 4, outer_r * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(outer_surf, (0, 255, 0, 40), (outer_r + 2, outer_r + 2), outer_r, 1)
                    screen.blit(outer_surf, (screen_x - outer_r - 2, screen_y - outer_r - 2))
            
            # Air resistance ring (same radius as gravity range in this model)
            air_r = max(1, int(self.gravity_distance * camera.zoom))
            if air_r > 3:
                air_surf = pygame.Surface((air_r * 2 + 4, air_r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(air_surf, (255, 100, 100, 60), (air_r + 2, air_r + 2), air_r, 1)
                screen.blit(air_surf, (screen_x - air_r - 2, screen_y - air_r - 2))

        # Draw rings behind planet if it has them
        if self.has_rings and scaled_radius > 6:
            ring_inner = int(scaled_radius * self.ring_inner_radius)
            ring_outer = int(scaled_radius * self.ring_outer_radius)
            ring_surf = pygame.Surface((ring_outer * 2, ring_outer * 2), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (*self.ring_color, 120), (ring_outer, ring_outer), ring_outer)
            pygame.draw.circle(ring_surf, (0, 0, 0, 0), (ring_outer, ring_outer), ring_inner)
            screen.blit(ring_surf, (screen_x - ring_outer, screen_y - ring_outer))

        # Draw planet base
        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), scaled_radius)
        
        # Draw spots if planet has them
        if self.has_spots and scaled_radius > 4:
            spot_color = tuple(max(0, c - 30) for c in self.color)
            for angle, distance, size in self.spots:
                spot_distance = distance * scaled_radius
                spot_x = int(screen_x + math.cos(angle) * spot_distance)
                spot_y = int(screen_y + math.sin(angle) * spot_distance)
                spot_radius = max(1, int(size * scaled_radius))
                pygame.draw.circle(screen, spot_color, (spot_x, spot_y), spot_radius)
        
        # Draw rings in front of planet if it has them
        if self.has_rings and scaled_radius > 6:
            ring_inner = int(scaled_radius * self.ring_inner_radius)
            ring_outer = int(scaled_radius * self.ring_outer_radius)
            # Draw thin ring outline
            pygame.draw.circle(screen, self.ring_color, (int(screen_x), int(screen_y)), ring_outer, 2)
            pygame.draw.circle(screen, self.ring_color, (int(screen_x), int(screen_y)), ring_inner, 1)
        
        # Draw planet outline
        outline_color = tuple(max(0, c - 50) for c in self.color)
        pygame.draw.circle(screen, outline_color, (int(screen_x), int(screen_y)), scaled_radius, 2)

    def draw_preview(self, screen, x, y, size=20):
        """Draw a small preview of the planet for the UI"""
        # Draw base
        pygame.draw.circle(screen, self.color, (x, y), size)
        
        # Draw rings if planet has them
        if self.has_rings:
            ring_inner = int(size * 1.3)
            ring_outer = int(size * 1.8)
            pygame.draw.circle(screen, self.ring_color, (x, y), ring_outer, 1)
            pygame.draw.circle(screen, self.ring_color, (x, y), ring_inner, 1)
        
        # Draw spots if planet has them
        if self.has_spots:
            spot_color = tuple(max(0, c - 30) for c in self.color)
            for angle, distance, spot_size in self.spots[:3]:  # Only first 3 spots in preview
                spot_distance = distance * size * 0.8
                spot_x = int(x + math.cos(angle) * spot_distance)
                spot_y = int(y + math.sin(angle) * spot_distance)
                spot_radius = max(1, int(spot_size * size * 0.5))
                pygame.draw.circle(screen, spot_color, (spot_x, spot_y), spot_radius)
        
        # Draw outline
        outline_color = tuple(max(0, c - 50) for c in self.color)
        pygame.draw.circle(screen, outline_color, (x, y), size, 1)
