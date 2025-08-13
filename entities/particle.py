"""
Particle class - handles particle physics, rendering, and behavior
"""
import pygame
import random
import math
from typing import List, TYPE_CHECKING
from collections import deque

# Import constants
from config.constants import PARTICLE_COLORS, WORLD_LIMIT

from systems.audio import generate_explosion_sound

# Avoid circular imports
if TYPE_CHECKING:
    from entities.planet import Planet
    from entities.wall import Wall

# Try to import gfxdraw for better performance
try:
    import pygame.gfxdraw
    HAS_GFXDRAW = True
except ImportError:
    HAS_GFXDRAW = False


class Particle:
    def __init__(self, x: float, y: float, z: float = None, bouncing: bool = False, from_spawner: bool = False):
        self.x = x
        self.y = y
        self.z = z if z is not None else random.uniform(0.3, 1.0)  # Depth for parallax
        # Random initial velocity
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.8, 2.2)  # Slower average speed
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.radius = 5  # Bigger particles
        self.mass = 1
        self.alive = True
        self.bouncing = bouncing
        self.from_spawner = from_spawner  # Track if spawned from user-placed spawner
        
        # Visual properties
        if bouncing:
            self.color = random.choice([(255, 150, 255), (255, 255, 150), (150, 255, 255)])
        else:
            self.color = random.choice(PARTICLE_COLORS)
        self.trail = deque(maxlen=8)  # Shorter, cleaner trails
        self.trail.append((x, y, self.z))
        
        # Enhanced glow effect
        self.glow_radius = 12
        
        # Lifetime
        self.lifetime = 20.0  # seconds
        self.age = 0.0
        self.exploding = False
        self.explosion_timer = 0.0
        self.explosion_particles = []  # For animated explosion
        self.fading = False
        self.fade_timer = 0.0
        
        # Pending clones for collection tracking
        self._pending_clones = []

    def update(self, dt: float, planets: List['Planet'], gravity_distance: float = 500.0, 
               air_resistance_intensity: float = 0.5, camera=None, sfx_volume: float = 0.5, 
               walls: List['Wall'] = None):
        """Update particle physics and behavior"""
        if not self.alive:
            return

        # Handle explosion state
        if self.exploding:
            self.explosion_timer += dt
            for p in self.explosion_particles:
                p['x'] += p['vx'] * dt * 60
                p['y'] += p['vy'] * dt * 60
                p['alpha'] -= dt * 300
                p['radius'] = max(0.5, p['radius'] - dt * 8)
                if p['alpha'] <= 0:
                    p['alpha'] = 0
            
            if self.explosion_timer > 1.0:
                self.alive = False
            return

        # Handle fading state
        if self.fading:
            self.fade_timer += dt
            if self.fade_timer >= 1.0:
                self.alive = False
                return

        # Age the particle
        self.age += dt
        if self.age > self.lifetime:
            self._start_fading()
            return

        # Apply gravity from planets
        total_fx = 0
        total_fy = 0
        
        for planet in planets:
            dx = planet.x - self.x
            dy = planet.y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Only apply gravity within the specified distance
            if distance < gravity_distance and distance > planet.radius + self.radius:
                # Gravity force calculation
                force = (planet.mass * self.mass) / (distance * distance) * 0.1
                
                # Normalize direction
                if distance > 0:
                    fx = (dx / distance) * force
                    fy = (dy / distance) * force
                    total_fx += fx
                    total_fy += fy

        # Apply forces to velocity
        self.vx += total_fx * dt
        self.vy += total_fy * dt

        # Apply air resistance in planet atmosphere zones
        for planet in planets:
            dx = planet.x - self.x
            dy = planet.y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Air resistance within 3x planet radius
            if distance < planet.radius * 3:
                air_factor = 1.0 - (distance / (planet.radius * 3))
                resistance = air_resistance_intensity * air_factor
                self.vx *= (1.0 - resistance * dt)
                self.vy *= (1.0 - resistance * dt)

        # Update position
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60

        # Add to trail
        self.trail.append((self.x, self.y, self.z))

        # Wall collisions
        if walls:
            for wall in walls:
                if wall.check_collision(self.x, self.y, self.radius):
                    # Simple bounce
                    self.vx *= -0.8
                    self.vy *= -0.8
                    # Move particle out of wall
                    self.x += self.vx * dt * 10
                    self.y += self.vy * dt * 10

        # Check for planet collection
        for planet in planets:
            dx = planet.x - self.x
            dy = planet.y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < planet.radius + self.radius:
                self._clone_particle(planet)
                self._start_explosion(sfx_volume)
                return

        # Boundary check - despawn if too far out
        if (abs(self.x) > WORLD_LIMIT or abs(self.y) > WORLD_LIMIT):
            self.alive = False

    def _start_fading(self):
        """Start the fading animation"""
        self.fading = True
        self.fade_timer = 0.0

    def _start_explosion(self, sfx_volume: float = 0.5):
        """Start explosion animation when collected"""
        self.exploding = True
        self.explosion_timer = 0.0
        
        try:
            sound = generate_explosion_sound()
            sound.set_volume(sfx_volume)
            sound.play()
        except Exception as e:
            print(f"Error playing explosion sound: {e}")

        # Create explosion particles
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 120)
            self.explosion_particles.append({
                'x': self.x,
                'y': self.y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'color': self.color,
                'alpha': 255,
                'radius': random.uniform(2, 4)
            })

    def _clone_particle(self, planet):
        """Create a clone for money generation tracking"""
        clone_data = {
            'planet': planet,
            'value': 1,  # Base value
            'position': (self.x, self.y)
        }
        self._pending_clones.append(clone_data)

    def get_alpha(self, camera=None):
        """Get particle alpha based on state and camera"""
        # In map mode, particles are completely invisible
        if camera and camera.is_map_mode():
            return 0
        
        # Fading particles
        if self.fading:
            return int(255 * (self.fade_timer / 1.0))
        
        # Fade in for first 0.3s
        if self.age < 0.3:
            return max(50, int(255 * (self.age / 0.3)))
        return 255

    def draw(self, screen, camera, planets=None):
        """Render the particle with Level of Detail (LOD) for performance."""
        if not self.alive:
            return

        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # Aggressive culling
        margin = 100 # Increased margin to avoid pop-in
        if not (-margin < screen_x < camera.screen_width + margin and -margin < screen_y < camera.screen_height + margin):
            return

        alpha = self.get_alpha(camera)
        if alpha == 0:
            return

        scaled_radius = max(1, int(self.radius * camera.zoom))

        # Explosion effect
        if self.exploding:
            for p in self.explosion_particles:
                px, py = camera.world_to_screen(p['x'], p['y'])
                color = (*p['color'][:3], min(255, int(p['alpha'])))
                pygame.draw.circle(screen, color[:3], (int(px), int(py)), max(1, int(p['radius'] * camera.zoom)))
            return

        # LOD-based rendering
        zoom_level = camera.zoom
        
        # LOD 1: High detail (zoomed in)
        if zoom_level > 0.8:
            # Full aura and trail
            self.draw_aura(screen, screen_x, screen_y, scaled_radius, alpha)
            self.draw_trail(screen, camera, scaled_radius, alpha)
            self.draw_core(screen, screen_x, screen_y, scaled_radius, alpha)
        # LOD 2: Medium detail
        elif zoom_level > 0.4:
            # Simple trail, no aura
            self.draw_trail(screen, camera, scaled_radius, alpha, simple=True)
            self.draw_core(screen, screen_x, screen_y, scaled_radius, alpha)
        # LOD 3: Low detail (zoomed out)
        else:
            # Just the core particle
            self.draw_core(screen, screen_x, screen_y, scaled_radius, alpha, simple=True)

    def draw_core(self, screen, x, y, radius, alpha, simple=False):
        main_color = (*self.color, alpha)
        pygame.draw.circle(screen, main_color[:3], (int(x), int(y)), radius)
        if simple or radius <= 1:
            return
        
        center_color = tuple(min(255, c + 80) for c in self.color)
        center_radius = max(1, int(radius * 0.6))
        pygame.draw.circle(screen, center_color, (int(x), int(y)), center_radius)

    def draw_aura(self, screen, x, y, radius, alpha):
        if radius <= 2: return
        for layer in range(2):
            aura_size = int(self.glow_radius * (1.5 - layer * 0.3) * camera.zoom)
            if aura_size > radius + 2:
                aura_alpha = max(5, int(alpha * (0.15 - layer * 0.08)))
                glow_surf = pygame.Surface((aura_size * 2, aura_size * 2), pygame.SRCALPHA)
                glow_color = (*self.color, max(8, int(aura_alpha)))
                pygame.draw.circle(glow_surf, glow_color, (aura_size, aura_size), aura_size)
                screen.blit(glow_surf, (int(x - aura_size), int(y - aura_size)))

    def draw_trail(self, screen, camera, radius, alpha, simple=False):
        if len(self.trail) < 2: return

        points = list(self.trail)
        if simple:
            # Draw a simple line for the trail
            start_pos = camera.world_to_screen(points[0][0], points[0][1])
            end_pos = camera.world_to_screen(points[-1][0], points[-1][1])
            trail_color = (*self.color, int(alpha * 0.5))
            pygame.draw.line(screen, trail_color[:3], start_pos, end_pos, max(1, int(radius * 0.8)))
        else:
            # Draw detailed trail
            for i in range(len(points) - 1):
                tx, ty, _ = points[i]
                trail_screen_x, trail_screen_y = camera.world_to_screen(tx, ty)
                
                base_trail_alpha = alpha * (i + 1) / len(points) * 0.8
                trail_alpha = int(base_trail_alpha)

                if trail_alpha > 8:
                    trail_size = max(1, int(radius * 0.8 * (i + 1) / len(points)))
                    trail_color = (*self.color, trail_alpha)
                    pygame.draw.circle(screen, trail_color[:3], (int(trail_screen_x), int(trail_screen_y)), trail_size)
