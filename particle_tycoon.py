import pygame
import random
import math
import numpy as np
import os
import time
from typing import List, Tuple
from collections import deque
import pygame.sndarray
import itertools

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

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

# Generate tick sound for money increases
def generate_tick_sound():
    """Generate a short tick sound for money increases"""
    sample_rate = 22050
    duration = 0.1  # Short tick sound
    
    # Generate a quick beep
    frames = int(duration * sample_rate)
    arr = np.zeros((frames, 2))
    
    # Create a quick tick with frequency sweep
    for i in range(frames):
        # Quick frequency sweep from 800Hz to 1200Hz
        freq = 800 + (400 * i / frames)
        wave = 0.3 * np.sin(2 * np.pi * freq * i / sample_rate)
        # Apply quick fade envelope
        envelope = max(0, 1 - (i / frames) ** 0.5)
        arr[i] = [wave * envelope, wave * envelope]
    
    arr = (arr * 32767).astype(np.int16)
    sound = pygame.sndarray.make_sound(arr)
    return sound

def generate_spawn_sound():
    """Generate a simple spawn sound with random pitch"""
    frequency = random.randint(200, 800)  # Random frequency
    duration = 0.1  # Short duration
    sample_rate = 22050
    frames = int(duration * sample_rate)
    
    # Generate a simple sine wave
    arr = np.zeros((frames, 2))
    for i in range(frames):
        wave = np.sin(2 * np.pi * frequency * i / sample_rate)
        # Add some fade out to avoid clicks
        fade = 1.0 - (i / frames) ** 2
        arr[i] = [wave * fade * 0.1, wave * fade * 0.1]  # Low volume
    
    # Convert to pygame sound
    sound_array = (arr * 32767).astype(np.int16)
    sound = pygame.sndarray.make_sound(sound_array)
    return sound

def generate_catch_sound():
    # Simple chime
    sample_rate = 22050
    duration = 0.12
    frames = int(duration * sample_rate)
    arr = np.zeros((frames, 2))
    freq = random.choice([880, 1046, 1318])
    for i in range(frames):
        wave = np.sin(2 * np.pi * freq * i / sample_rate)
        arr[i] = [wave * 0.2, wave * 0.2]
    sound_array = (arr * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(sound_array)

def generate_explosion_sound():
    # Simple noise burst
    sample_rate = 22050
    duration = 0.18
    frames = int(duration * sample_rate)
    arr = np.random.uniform(-1, 1, (frames, 2)) * np.linspace(1, 0, frames)[:, None] * 0.3
    sound_array = (arr * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(sound_array)

# Spacey planet names
SPACEY_NAMES = [
    "Nebulon", "Quasar", "Andromeda", "Pulsara", "Galaxion", "Stellara", "Cosmica", "Astrolis", "Vortexia", "Nova Prime", "Celestia", "Orbitron", "Zenith", "Eclipse", "Cometia", "Lunaris", "Solara", "Meteorix", "Auroria", "Spectra"
]
planet_name_counter = itertools.count(1)

def generate_planet_name():
    base = random.choice(SPACEY_NAMES)
    num = next(planet_name_counter)
    return f"{base} {num}"

class MoneyPopup:
    """Animated money increase popup with tilt and color effects"""
    def __init__(self, x: float, y: float, amount: int):
        self.x = x
        self.y = y
        self.start_y = y
        self.amount = amount
        self.timer = 0
        self.duration = 1.5
        self.tilt_angle = 0
        self.max_tilt = 15  # degrees
        self.color = [0, 255, 0]  # Start green
        self.target_color = [255, 255, 255]  # End white
        self.font_size = 24
        
    def update(self, dt: float) -> bool:
        """Update the money popup. Returns False when it should be removed."""
        self.timer += dt
        
        # Move upward
        self.y = self.start_y - (self.timer * 50)  # Move up 50 pixels per second
        
        # Tilt animation - tilt up initially, then straighten
        if self.timer < 0.3:  # Tilt phase
            self.tilt_angle = (self.timer / 0.3) * self.max_tilt
        else:  # Straighten phase
            remaining_tilt_time = min(0.7, self.duration - self.timer)
            self.tilt_angle = self.max_tilt * (remaining_tilt_time / 0.7)
            
        # Color transition from green to white
        progress = min(1.0, self.timer / self.duration)
        for i in range(3):
            self.color[i] = int(self.color[i] + (self.target_color[i] - self.color[i]) * progress * 2)
            
        return self.timer < self.duration
        
    def draw(self, screen, camera, font):
        """Draw the money popup"""
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # Create text surface
        text = font.render(f"+${self.amount}", True, tuple(self.color))
        
        # Apply tilt by rotating the text
        if abs(self.tilt_angle) > 0.1:
            # Rotate text surface
            rotated_text = pygame.transform.rotate(text, self.tilt_angle)
            text_rect = rotated_text.get_rect(center=(screen_x, screen_y))
            screen.blit(rotated_text, text_rect)
        else:
            text_rect = text.get_rect(center=(screen_x, screen_y))
            screen.blit(text, text_rect)

class LightRay:
    """Light ray effect that emanates from particle collision points"""
    def __init__(self, x: float, y: float, angle: float):
        self.x = x
        self.y = y
        self.angle = angle
        self.length = 0
        self.max_length = 25  # Even smaller light rays - less tall
        self.timer = 0
        self.duration = 0.5  # Faster effect - half the time
        self.intensity = 1.0
        
    def update(self, dt: float) -> bool:
        """Update the light ray. Returns False when it should be removed."""
        self.timer += dt
        
        # Grow quickly, then fade
        if self.timer < 0.1:  # Faster growth phase
            self.length = (self.timer / 0.1) * self.max_length
            self.intensity = 1.0
        else:  # Fade phase
            fade_progress = (self.timer - 0.1) / (self.duration - 0.1)
            self.intensity = max(0, 1.0 - fade_progress)
            
        return self.timer < self.duration
        
    def draw(self, screen, camera):
        """Draw the light ray"""
        if self.intensity <= 0:
            return
            
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # Calculate end point
        end_x = self.x + math.cos(self.angle) * self.length
        end_y = self.y + math.sin(self.angle) * self.length
        screen_end_x, screen_end_y = camera.world_to_screen(end_x, end_y)
        
        # Draw smaller, more subtle light rays
        alpha = int(255 * self.intensity)
        for i in range(3):  # Fewer layers for smaller effect
            width = max(1, 3 - i)  # Thinner lines
            line_alpha = max(10, alpha // (i + 1))
            
            # Create color with alpha
            color = (255, 255, 200, line_alpha)  # Bright yellow-white
            
            # Draw line (pygame doesn't support alpha directly, so we approximate)
            if i == 0:  # Brightest core
                pygame.draw.line(screen, (255, 255, 255), 
                               (screen_x, screen_y), (screen_end_x, screen_end_y), width)
            else:  # Outer glow layers
                fade_color = (255 - i * 50, 255 - i * 50, 200 - i * 40)
                pygame.draw.line(screen, fade_color,
                               (screen_x, screen_y), (screen_end_x, screen_end_y), width)

class Wall:
    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        # Normalize wall vector
        if self.length > 0:
            self.nx = (y2-y1) / self.length  # Normal vector
            self.ny = -(x2-x1) / self.length
        else:
            self.nx = self.ny = 0
    
    def check_collision(self, px, py, radius):
        # Check if particle collides with wall segment
        dx = px - self.x1
        dy = py - self.y1
        wall_dx = self.x2 - self.x1
        wall_dy = self.y2 - self.y1
        if self.length == 0:
            return False, 0, 0
        t = max(0, min(1, (dx*wall_dx + dy*wall_dy) / (self.length**2)))
        closest_x = self.x1 + t * wall_dx
        closest_y = self.y1 + t * wall_dy
        dist = math.sqrt((px - closest_x)**2 + (py - closest_y)**2)
        if dist < radius:
            return True, self.nx, self.ny
        return False, 0, 0
    
    def draw(self, screen, camera, gravity_distance: float = None, air_resistance_intensity: float = None):
        sx1, sy1 = camera.world_to_screen(self.x1, self.y1)
        sx2, sy2 = camera.world_to_screen(self.x2, self.y2)
        pygame.draw.line(screen, (100, 100, 255), (sx1, sy1), (sx2, sy2), max(2, int(3 * camera.zoom)))

class Camera:
    def __init__(self, screen_width: int, screen_height: int):
        self.x = 0  # Camera offset X
        self.y = 0  # Camera offset Y
        self.zoom = 1.0  # Zoom level (1.0 = normal, >1.0 = zoomed in, <1.0 = zoomed out)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.dragging = False
        self.last_mouse_pos = (0, 0)
        
        # Zoom limits - allow much more zoom out for bigger map
        self.min_zoom = 0.05
        self.max_zoom = 5.0
    
    def is_map_mode(self) -> bool:
        """Check if camera is in map mode (when zoomed almost completely out)"""
        # Map mode activates when zoom is very close to minimum (very zoomed out)
        # Activate when zoom is 0.1 or less (even closer to min_zoom of 0.05)
        return self.zoom <= 0.1
    
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates"""
        screen_x = (world_x - self.x) * self.zoom + self.screen_width // 2
        screen_y = (world_y - self.y) * self.zoom + self.screen_height // 2
        return int(screen_x), int(screen_y)
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates"""
        world_x = (screen_x - self.screen_width // 2) / self.zoom + self.x
        world_y = (screen_y - self.screen_height // 2) / self.zoom + self.y
        return world_x, world_y
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click for dragging
                self.dragging = True
                self.last_mouse_pos = event.pos
            elif event.button == 4:  # Mouse wheel up
                self.zoom_at_point(event.pos, 1.1)
            elif event.button == 5:  # Mouse wheel down
                self.zoom_at_point(event.pos, 0.9)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left click release
                self.dragging = False
        
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            dx = event.pos[0] - self.last_mouse_pos[0]
            dy = event.pos[1] - self.last_mouse_pos[1]
            
            # Move camera (opposite direction of mouse movement)
            self.x -= dx / self.zoom
            self.y -= dy / self.zoom
            
            self.last_mouse_pos = event.pos
    
    def zoom_at_point(self, screen_pos: Tuple[int, int], zoom_factor: float):
        """Zoom in/out at a specific screen point"""
        # Convert screen point to world coordinates before zoom
        world_x, world_y = self.screen_to_world(screen_pos[0], screen_pos[1])
        
        # Apply zoom
        new_zoom = self.zoom * zoom_factor
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
        
        if new_zoom != self.zoom:
            self.zoom = new_zoom
            
            # Adjust camera position to keep the zoom point stationary
            new_world_x, new_world_y = self.screen_to_world(screen_pos[0], screen_pos[1])
            self.x += new_world_x - world_x
            self.y += new_world_y - world_y

class Slider:
    def __init__(self, x: int, y: int, width: int, height: int, min_val: float = 0.0, max_val: float = 1.0, start_val: float = 0.5):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = start_val
        self.dragging = False
        
        # Calculate knob position
        knob_x = x + (start_val - min_val) / (max_val - min_val) * width - 5
        self.knob_rect = pygame.Rect(knob_x, y - 2, 10, height + 4)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.knob_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # Calculate new position
            new_x = max(self.rect.x, min(event.pos[0], self.rect.x + self.rect.width))
            self.knob_rect.x = new_x - 5
            
            # Calculate new value
            ratio = (new_x - self.rect.x) / self.rect.width
            self.value = self.min_val + ratio * (self.max_val - self.min_val)
            
    def draw(self, screen):
        # Update rect position
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Update knob position based on current value and position
        knob_x = self.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.width - 5
        self.knob_rect.x = knob_x
        self.knob_rect.y = self.y - 2
        
        # Draw slider track
        pygame.draw.rect(screen, DARK_GRAY, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        # Draw knob
        pygame.draw.rect(screen, LIGHT_GRAY, self.knob_rect)
        pygame.draw.rect(screen, WHITE, self.knob_rect, 1)

class MusicSelector:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.music_files = self.load_music_files()
        self.selected_index = 0 if self.music_files else -1
        self.current_music = None
        self.music_channel = None
        self.font = pygame.font.Font(None, 20)
        self.playing_index = -1  # Track which index is currently playing
        # Button areas
        self.prev_button = pygame.Rect(x, y, 30, height)
        self.next_button = pygame.Rect(x + width - 30, y, 30, height)
        self.display_rect = pygame.Rect(x + 35, y, width - 110, height)
        self.play_button = pygame.Rect(x + width - 70, y, 40, height)
    
    def load_music_files(self):
        """Load all music files from the music folder"""
        music_files = ["None"]  # Always include "None" option
        music_folder = "music"
        
        if os.path.exists(music_folder):
            supported_formats = ['.wav', '.ogg', '.mp3']
            for file in os.listdir(music_folder):
                if any(file.lower().endswith(fmt) for fmt in supported_formats):
                    music_files.append(file)
        
        return music_files
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.prev_button.collidepoint(event.pos):
                self.select_previous()
            elif self.next_button.collidepoint(event.pos):
                self.select_next()
            elif self.play_button.collidepoint(event.pos):
                self.play_selected()
    
    def select_previous(self):
        if self.music_files:
            self.selected_index = (self.selected_index - 1) % len(self.music_files)
    
    def select_next(self):
        if self.music_files:
            self.selected_index = (self.selected_index + 1) % len(self.music_files)
    def play_selected(self):
        if not self.music_files or self.selected_index >= len(self.music_files):
            return
        selected_file = self.music_files[self.selected_index]
        if selected_file == "None":
            if self.music_channel:
                self.music_channel.stop()
            self.current_music = None
            self.playing_index = -1
        else:
            try:
                music_path = os.path.join("music", selected_file)
                self.current_music = pygame.mixer.Sound(music_path)
                if not self.music_channel:
                    self.music_channel = pygame.mixer.Channel(1)
                self.music_channel.stop()
                self.music_channel.play(self.current_music, loops=-1)
                self.playing_index = self.selected_index
            except Exception as e:
                print(f"Failed to load music {selected_file}: {e}")
                self.current_music = None
                self.playing_index = -1
    
    def play_music(self, volume: float):
        """Play the current music at specified volume"""
        if self.current_music and self.music_channel and pygame.mixer.get_init():
            if not self.music_channel.get_busy():
                self.music_channel.play(self.current_music, loops=-1)
            self.music_channel.set_volume(volume)
    
    def stop_music(self):
        """Stop the current music"""
        if self.music_channel:
            self.music_channel.stop()
    
    def draw(self, screen):
        # Update all positions
        self.rect.x = self.x
        self.rect.y = self.y
        self.prev_button = pygame.Rect(self.x, self.y, 30, self.height)
        self.next_button = pygame.Rect(self.x + self.width - 30, self.y, 30, self.height)
        self.display_rect = pygame.Rect(self.x + 35, self.y, self.width - 110, self.height)
        self.play_button = pygame.Rect(self.x + self.width - 70, self.y, 40, self.height)
        
        # Draw background
        pygame.draw.rect(screen, DARK_GRAY, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        # Draw previous button
        pygame.draw.rect(screen, GRAY, self.prev_button)
        pygame.draw.rect(screen, WHITE, self.prev_button, 1)
        prev_text = self.font.render("<", True, WHITE)
        prev_rect = prev_text.get_rect(center=self.prev_button.center)
        screen.blit(prev_text, prev_rect)
        # Draw next button
        pygame.draw.rect(screen, GRAY, self.next_button)
        pygame.draw.rect(screen, WHITE, self.next_button, 1)
        next_text = self.font.render(">", True, WHITE)
        next_rect = next_text.get_rect(center=self.next_button.center)
        screen.blit(next_text, next_rect)
        # Draw play button
        pygame.draw.rect(screen, GREEN if self.selected_index != self.playing_index else YELLOW, self.play_button)
        pygame.draw.rect(screen, WHITE, self.play_button, 1)
        play_text = self.font.render("Play", True, BLACK if self.selected_index != self.playing_index else RED)
        play_rect = play_text.get_rect(center=self.play_button.center)
        screen.blit(play_text, play_rect)
        # Draw current selection
        if self.music_files and self.selected_index < len(self.music_files):
            current_name = self.music_files[self.selected_index]
            if current_name != "None":
                display_name = os.path.splitext(current_name)[0].replace("_", " ").title()
            else:
                display_name = "None"
            if len(display_name) > 15:
                display_name = display_name[:12] + "..."
            name_text = self.font.render(display_name, True, WHITE)
            name_rect = name_text.get_rect(center=self.display_rect.center)
            # Highlight if this is the currently playing track
            if self.selected_index == self.playing_index:
                pygame.draw.rect(screen, YELLOW, self.display_rect, 2)
            screen.blit(name_text, name_rect)

class Particle:
    def __init__(self, x: float, y: float, z: float = None, bouncing: bool = False):
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
    
    def update(self, dt: float, planets: List['Planet'], gravity_distance: float = 500.0, air_resistance_intensity: float = 0.5, camera=None, sfx_volume: float = 0.5, walls: List['Wall'] = None):
        if not self.alive:
            return
        
        # Check if particle is being affected by gravity (will be determined in the gravity loop below)
        affected_by_gravity = False
            
        if self.age >= self.lifetime and not self.exploding and not self.fading:
            # Always fade out on timeout (no explosions on timeout)
            self.fading = True
            self.fade_timer = 1.0  # Fade over 1 second
        if self.exploding:
            self.explosion_timer -= dt
            # Animate explosion particles
            for p in self.explosion_particles:
                p['x'] += p['vx'] * dt * 20
                p['y'] += p['vy'] * dt * 20
                p['alpha'] = max(0, p['alpha'] - 600 * dt)
            if self.explosion_timer <= 0:
                self.alive = False
            return
        
        if self.fading:
            self.fade_timer -= dt
            if self.fade_timer <= 0:
                self.alive = False
            # Do NOT return; keep moving while fading
        
        # Store current position in trail
        self.trail.append((self.x, self.y, self.z))
        
        # Apply forces from all planets
        for planet in planets:
            dx = planet.x - self.x
            dy = planet.y - self.y
            distance = math.sqrt(dx**2 + dy**2)
            
            # Check collision with clone orbit zone (before planet collision)
            if (planet.has_clone_orbit and not hasattr(self, '_cloned_from_planet') and 
                abs(distance - planet.clone_orbit_radius) <= 3):  # Small tolerance for crossing the orbit
                # Clone this particle
                self._clone_particle(planet)
                # Mark this particle as cloned to prevent re-cloning
                self._cloned_from_planet = planet
            
            # Check collision with planet (more robust detection)
            collision_distance = planet.radius + self.radius + 2  # Add small buffer
            if distance < collision_distance:
                if not self.fading:
                    # Only explode on planet collision, not during fade
                    self.exploding = True
                    self.explosion_timer = 0.2  # Short explosion for collision
                    # Generate small explosion for collision
                    self.explosion_particles = []
                    for _ in range(6):  # Fewer particles for collision
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(1, 3)
                        color = random.choice([
                            (255, 255, 100), (255, 200, 50), self.color
                        ])
                        self.explosion_particles.append({
                            'x': self.x,
                            'y': self.y,
                            'z': self.z,
                            'vx': math.cos(angle) * speed,
                            'vy': math.sin(angle) * speed,
                            'color': color,
                            'radius': random.randint(1, 3),
                            'alpha': 255
                        })
                # Mark dead regardless
                self.alive = False
                # Always ensure particle collection is triggered and get collision data
                collision_data = planet.collect_particle(camera, sfx_volume, self.x, self.y)
                
                # Create light ray effect if we have collision data and game reference
                if collision_data and hasattr(camera, '_game_ref'):
                    surface_x, surface_y, angle = collision_data
                    # Create multiple light rays in different directions
                    for i in range(3):  # 3 rays for a nice effect
                        ray_angle = angle + (i - 1) * 0.3  # Spread rays slightly
                        light_ray = LightRay(surface_x, surface_y, ray_angle)
                        camera._game_ref.light_rays.append(light_ray)
                return
            
            # Apply gravitational force with adjustable range
            if distance > 0:
                # Adjustable gravity with extended range
                gravity_strength = 2.0  # Base gravity strength
                max_gravity_distance = planet.gravity_distance  # Use planet's individual gravity distance
                
                # Gradual gravity falloff - always apply some force, but fade smoothly
                # Use modified inverse law with gradual distance falloff
                base_force = planet.mass / (distance**1.5) * gravity_strength
                
                # Gradual distance falloff instead of hard cutoff
                if distance < max_gravity_distance:
                    distance_factor = 1.0  # Full strength
                else:
                    # Gradually fade out over the next 200 units
                    fade_distance = 200
                    distance_factor = max(0, 1.0 - (distance - max_gravity_distance) / fade_distance)
                
                # Apply distance factor to force
                force = base_force * distance_factor
                
                if force > 0:  # Only apply if there's any force left
                    force_x = (dx / distance) * force
                    force_y = (dy / distance) * force
                    
                    self.vx += force_x
                    self.vy += force_y
                    
                    # Mark that this particle is being affected by gravity
                    affected_by_gravity = True
                
                # Apply air resistance over same gradual distance as gravity
                max_air_distance = max_gravity_distance  # Same distance as gravity
                if distance < max_air_distance + 200:  # Include fade zone
                    # Calculate air resistance strength based on distance
                    if distance < max_air_distance:
                        air_strength = 1.0 - (distance / max_air_distance)  # Full strength to zero
                    else:
                        # Gradual fade in the extra 200 units
                        fade_distance = 200
                        air_strength = max(0, 1.0 - (distance - max_air_distance) / fade_distance)
                        air_strength = air_strength * 0.5  # Weaker in fade zone
                    
                    # Apply air resistance with adjustable intensity
                    base_resistance = 0.015 * planet.air_resistance_intensity  # Use planet's individual air resistance
                    air_resistance = base_resistance * air_strength
                    
                    # Apply resistance opposite to velocity
                    speed = math.sqrt(self.vx**2 + self.vy**2)
                    if speed > 0:
                        resistance_x = -(self.vx / speed) * air_resistance * speed
                        resistance_y = -(self.vy / speed) * air_resistance * speed
                        
                        self.vx += resistance_x
                        self.vy += resistance_y
        
        # Age the particle only if it's NOT being affected by gravity
        if not affected_by_gravity:
            self.age += dt
        
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Check collision with walls
        if walls:
            for wall in walls:
                collision, nx, ny = wall.check_collision(self.x, self.y, self.radius)
                if collision:
                    # Bounce off wall
                    # Calculate dot product of velocity with wall normal
                    dot_product = self.vx * nx + self.vy * ny
                    
                    # Reflect velocity
                    self.vx -= 2 * dot_product * nx
                    self.vy -= 2 * dot_product * ny
                    
                    # Apply some energy loss
                    self.vx *= 0.8
                    self.vy *= 0.8
                    
                    # Move particle slightly away from wall to prevent sticking
                    self.x += nx * (self.radius + 1)
                    self.y += ny * (self.radius + 1)
                    break
        
        # Remove particles that go extremely far away from the world center
        # Use a very large boundary so fading particles keep moving visibly
        boundary = WORLD_LIMIT
        if (self.x < -boundary or self.x > boundary or 
            self.y < -boundary or self.y > boundary):
            self.alive = False
    
    def _clone_particle(self, planet):
        """Clone this particle and add velocity spread"""
        # Calculate the orthogonal direction to current velocity
        velocity_magnitude = math.sqrt(self.vx**2 + self.vy**2)
        if velocity_magnitude == 0:
            return  # Can't spread zero velocity
        
        # Normalize velocity vector
        vx_norm = self.vx / velocity_magnitude
        vy_norm = self.vy / velocity_magnitude
        
        # Orthogonal vector (perpendicular to velocity)
        ortho_x = -vy_norm  # Rotate 90 degrees
        ortho_y = vx_norm
        
        # Spread amount (adjust this to control how much particles spread)
        spread_strength = velocity_magnitude * 0.3  # 30% of current velocity
        
        # Modify this particle's velocity (spread in one direction)
        self.vx += ortho_x * spread_strength
        self.vy += ortho_y * spread_strength
        
        # Create clone particle data (will be added by emitter)
        clone_data = {
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'vx': self.vx - 2 * ortho_x * spread_strength,  # Opposite direction
            'vy': self.vy - 2 * ortho_y * spread_strength,
            'color': self.color,
            'radius': self.radius,
            'mass': self.mass,
            'age': self.age,
            'lifetime': self.lifetime
        }
        
        # Store clone data for the emitter to process
        if not hasattr(self, '_pending_clones'):
            self._pending_clones = []
        self._pending_clones.append(clone_data)
    
    def get_alpha(self, camera=None):
        # In map mode, particles are completely invisible (0% opacity)
        if camera and camera.is_map_mode():
            return 0
        
        # Fading particles
        if self.fading:
            return int(255 * (self.fade_timer / 1.0))
        
        # Fade in for first 0.3s (faster fade-in for better visibility)
        if self.age < 0.3:
            return max(50, int(255 * (self.age / 0.3)))  # Ensure minimum visibility
        return 255
    
    def draw(self, screen, camera, planets=None):
        if not self.alive:
            return
        
        # Simple world-to-screen conversion (no parallax)
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        margin = 50
        if (screen_x < -margin or screen_x > camera.screen_width + margin or 
            screen_y < -margin or screen_y > camera.screen_height + margin):
            return
        
        # Better scaling - ensure particles are visible when zoomed out
        raw_scaled_radius = self.radius * camera.zoom
        if raw_scaled_radius < 0.5:
            scaled_radius = 3  # Minimum 3 pixels when extremely zoomed out for better visibility
        elif raw_scaled_radius < 1.5:
            scaled_radius = 3  # Still 3 pixels for small sizes to ensure visibility
        else:
            scaled_radius = max(2, int(raw_scaled_radius))  # Ensure minimum 2 pixels
        
        alpha = self.get_alpha(camera)
        if alpha == 0:  # Skip drawing completely if invisible
            return
        
        # Explosion effect - simplified for performance
        if self.exploding:
            for p in self.explosion_particles:
                px, py = camera.world_to_screen(p['x'], p['y'])
                if 0 <= px < camera.screen_width and 0 <= py < camera.screen_height:
                    color = (*p['color'][:3], min(255, int(p['alpha'])))
                    pygame.draw.circle(screen, color[:3], (int(px), int(py)), max(1, p['radius']))
            return
        
        # Enhanced multi-layer aura effect with distance falloff - improved visibility
        if camera.zoom > 0.2 and scaled_radius > 1:  # Show aura at more zoom levels
            # Create multiple glow layers for satisfying aura
            aura_layers = [
                (scaled_radius * 2.5, alpha * 0.2),  # Outer glow - more visible
                (scaled_radius * 2.0, alpha * 0.3),  # Mid glow
                (scaled_radius * 1.5, alpha * 0.5),  # Inner glow - brighter
            ]
            
            for aura_radius, aura_alpha in aura_layers:
                if aura_alpha > 3:  # Lower threshold for visibility
                    aura_size = max(2, int(aura_radius))
                    # Create glow surface with proper alpha
                    glow_surf = pygame.Surface((aura_size * 2, aura_size * 2), pygame.SRCALPHA)
                    glow_color = (*self.color, max(8, int(aura_alpha)))  # Higher minimum alpha
                    pygame.draw.circle(glow_surf, glow_color, (aura_size, aura_size), aura_size)
                    screen.blit(glow_surf, (int(screen_x - aura_size), int(screen_y - aura_size)))
        
        # Simplified, cleaner trail rendering
        if len(self.trail) > 2 and camera.zoom > 0.4:
            trail_points = list(self.trail)[-6:]  # Only use last 6 points for clean trails
            
            for i in range(len(trail_points) - 1):
                tx, ty, tz = trail_points[i]
                trail_screen_x, trail_screen_y = camera.world_to_screen(tx, ty)
                
                # Check if trail point is on screen
                if (-20 <= trail_screen_x <= camera.screen_width + 20 and 
                    -20 <= trail_screen_y <= camera.screen_height + 20):
                    
                    # Smooth fade from back to front
                    trail_alpha = int(alpha * (i + 1) / len(trail_points) * 0.6)
                    if trail_alpha > 8:
                        trail_size = max(1, int(scaled_radius * 0.7 * (i + 1) / len(trail_points)))
                        trail_color = (*self.color, trail_alpha)
                        pygame.draw.circle(screen, trail_color[:3], (int(trail_screen_x), int(trail_screen_y)), trail_size)
        
        # Draw main particle with enhanced appearance
        main_color = (*self.color, alpha)
        pygame.draw.circle(screen, main_color[:3], (int(screen_x), int(screen_y)), scaled_radius)
        
        # Add bright center with gradient effect
        if scaled_radius > 1:
            # Bright inner core
            center_color = tuple(min(255, c + 80) for c in self.color)
            center_radius = max(1, int(scaled_radius * 0.6))
            pygame.draw.circle(screen, center_color, (int(screen_x), int(screen_y)), center_radius)
            
            # Very bright center point
            if scaled_radius > 2:
                core_color = tuple(min(255, c + 120) for c in self.color)
                core_radius = max(1, int(scaled_radius * 0.3))
                pygame.draw.circle(screen, core_color, (int(screen_x), int(screen_y)), core_radius)

class DwarfPlanet:
    """A smaller, cheaper version of Planet with reduced capabilities"""
    def __init__(self, x: float, y: float, radius: float = 18):  # Much smaller than regular planets (48)
        self.x = x
        self.y = y
        self.radius = radius
        self.base_mass = radius * 1.5  # Less mass than regular planets
        self.gravity_level = 1
        self.mass = self.base_mass * self.gravity_level
        self.particles_collected = 0
        self.upgrade_cost = 30  # Cheaper upgrades
        self.name = generate_planet_name()  # Add name attribute like regular planets
        
        # Weaker gravity and air resistance
        self.gravity_distance = 150  # Shorter range than regular planets (300)
        self.base_air_resistance_intensity = 0.3  # Weaker air resistance
        self.air_resistance_intensity = self.base_air_resistance_intensity
        
        # No clone orbit capability for dwarf planets
        self.has_clone_orbit = False
        self.clone_orbit_radius = 0
        self.clone_orbit_cost = 999999  # Effectively disabled
        
        # Visual properties - smaller and more basic
        self.planet_type = {"name": "Dwarf", "color": (139, 90, 43), "has_rings": False, "has_spots": False}  # Brown dwarf
        self.color = self.planet_type["color"]
        self.has_rings = False
        self.has_spots = False
        self.spots = []
        
        # Animation properties
        self.counter_bounce_timer = 0
        self.counter_bounce_scale = 1.0
        self.shimmer_timer = 0
        self.shimmer_intensity = 0
        self.wobble_timer = 0
        
    def collect_particle(self, camera=None, sfx_volume=0.5, px=None, py=None):
        self.particles_collected += 1
        
        # Automatic growth and gravity increase every particle hit (smaller effect for dwarf planets)
        growth_factor = 1.001  # Grow by 0.1% each hit (half of regular planets)
        gravity_factor = 1.0005  # Increase gravity by 0.05% each hit (half of regular planets)
        
        # Grow dwarf planet size
        self.radius *= growth_factor
        
        # Increase gravity properties
        self.mass *= gravity_factor
        
        # Smaller bounce effect
        self.counter_bounce_timer = 0.3  # Shorter bounce
        self.counter_bounce_scale = 1.0
        
        # Return collision data for light ray effect
        collision_data = None
        if px is not None and py is not None:
            # Calculate collision point on planet surface
            dx = px - self.x
            dy = py - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            if distance > 0:
                # Normalize and scale to planet surface
                surface_x = self.x + (dx / distance) * self.radius
                surface_y = self.y + (dy / distance) * self.radius
                # Calculate angle pointing outward from planet center
                angle = math.atan2(dy, dx)
                collision_data = (surface_x, surface_y, angle)
                
        return collision_data
        
    def upgrade_gravity(self):
        """Upgrade gravity (limited for dwarf planets)"""
        if self.gravity_level < 3:  # Max level 3 instead of 5
            self.gravity_level += 1
            self.mass = self.base_mass * self.gravity_level
            self.upgrade_cost = int(self.upgrade_cost * 1.8)  # Faster cost increase
            
    def upgrade_clone_orbit(self):
        """Dwarf planets cannot have clone orbits"""
        pass  # Do nothing
    
    def get_visual_radius(self, camera, hover_scale=1.0):
        """Get the visual radius of the dwarf planet based on camera mode"""
        if camera.is_map_mode():
            map_mode_scale = 0.5
            return self.radius * map_mode_scale * hover_scale
        else:
            return self.radius * camera.zoom * hover_scale
    
    def update(self, dt, is_hovered=False):
        """Update dwarf planet animations (simplified)"""
        if self.counter_bounce_timer > 0:
            self.counter_bounce_timer -= dt
            progress = 1.0 - (self.counter_bounce_timer / 0.3)  # Shorter duration
            if progress < 0.5:
                self.counter_bounce_scale = 1.0 + (progress * 2) * 0.3  # Smaller bounce
            else:
                self.counter_bounce_scale = 1.3 - ((progress - 0.5) * 2) * 0.3
            
            if self.counter_bounce_timer <= 0:
                self.counter_bounce_scale = 1.0
        
        # Simple wobble when hovered
        if is_hovered:
            self.wobble_timer += dt * 6  # Slower wobble
        else:
            self.wobble_timer = 0
    
    def draw(self, screen, camera, gravity_distance: float = None, air_resistance_intensity: float = None):
        """Draw the dwarf planet (simplified)"""
        # Basic position with small wobble
        wobble_x = math.sin(self.wobble_timer) * 1 if self.wobble_timer > 0 else 0
        wobble_y = math.cos(self.wobble_timer * 1.3) * 1 if self.wobble_timer > 0 else 0
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        screen_x += wobble_x
        screen_y += wobble_y
        
        hover_scale = 1.1 if self.wobble_timer > 0 else 1.0  # Smaller hover effect
        
        if camera.is_map_mode():
            map_mode_scale = 0.5
            scaled_radius = max(3, int(self.radius * map_mode_scale * hover_scale))
        else:
            scaled_radius = max(2, int(self.radius * camera.zoom * hover_scale))
        
        # Only draw if visible
        margin = scaled_radius + 20
        if (screen_x < -margin or screen_x > camera.screen_width + margin or 
            screen_y < -margin or screen_y > camera.screen_height + margin):
            return
        
        # Simple planet drawing - no fancy effects
        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), scaled_radius)
        
        # Simple highlight if hovered
        if self.wobble_timer > 0:
            pygame.draw.circle(screen, (200, 200, 200), (int(screen_x), int(screen_y)), scaled_radius, 2)
        
        # Simple outline
        pygame.draw.circle(screen, WHITE, (int(screen_x), int(screen_y)), scaled_radius, 1)
    
    def draw_preview(self, screen, x, y, size):
        """Draw a small preview of the dwarf planet for the UI"""
        # Draw base (simpler than Planet)
        pygame.draw.circle(screen, self.color, (x, y), size)
        
        # Draw simple outline
        pygame.draw.circle(screen, WHITE, (x, y), size, 1)

class Planet:
    def __init__(self, x: float, y: float, radius: float = 48):  # 4x bigger than original (12 * 4 = 48)
        self.x = x
        self.y = y
        self.radius = radius
        self.base_mass = radius * 2
        self.gravity_level = 1  # Upgrade level
        self.mass = self.base_mass * self.gravity_level  # Mass affected by upgrades
        self.particles_collected = 0
        self.upgrade_cost = 75  # Cost to upgrade gravity
        self.name = generate_planet_name()
        
        # Per-planet gravity and air resistance properties
        self.base_gravity_distance = 500.0  # Base gravity distance
        self.gravity_distance = self.base_gravity_distance
        self.base_air_resistance_intensity = 0.5  # Base air resistance
        self.air_resistance_intensity = self.base_air_resistance_intensity
        
        # Clone orbit zone properties
        self.has_clone_orbit = False
        self.clone_orbit_radius = self.radius * 4  # Default clone orbit distance
        self.clone_orbit_cost = 150  # Cost to add clone orbit
        
        # Visual properties
        self.planet_type = random.choice(PLANET_TYPES)
        self.color = self.planet_type["color"]
        self.has_rings = self.planet_type["rings"]
        self.has_spots = self.planet_type["spots"]
        if self.has_spots:
            self.spots = [(random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8)) for _ in range(random.randint(2, 5))]
        
        # Animation properties
        self.counter_bounce_timer = 0
        self.counter_bounce_scale = 1.0
        self.shimmer_timer = 0
        self.shimmer_intensity = 0
        self.wobble_timer = 0  # For hover wobble effect
        
    def collect_particle(self, camera=None, sfx_volume=0.5, px=None, py=None):
        self.particles_collected += 1
        
        # Automatic growth and gravity increase every particle hit
        growth_factor = 1.002  # Grow by 0.2% each hit
        gravity_factor = 1.001  # Increase gravity by 0.1% each hit
        
        # Grow planet size
        self.radius *= growth_factor
        
        # Increase gravity properties
        self.mass *= gravity_factor
        self.gravity_distance *= gravity_factor
        self.air_resistance_intensity *= gravity_factor
        
        # Update clone orbit radius to match planet growth
        self.clone_orbit_radius = self.radius * 4
        
        # Trigger bounce animation
        self.counter_bounce_timer = 0.5  # Animation duration
        self.counter_bounce_scale = 1.5  # Scale up
        # Trigger shimmer effect
        self.shimmer_timer = 0.3  # Shimmer duration
        self.shimmer_intensity = 1.0  # Full intensity
        
        # Return collision data for light ray effect
        collision_data = None
        if px is not None and py is not None:
            # Calculate collision point on planet surface
            dx = px - self.x
            dy = py - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            if distance > 0:
                # Normalize and scale to planet surface
                surface_x = self.x + (dx / distance) * self.radius
                surface_y = self.y + (dy / distance) * self.radius
                # Calculate angle pointing outward from planet center
                angle = math.atan2(dy, dx)
                collision_data = (surface_x, surface_y, angle)
        
        # Play catch sound
        if camera and px is not None and py is not None:
            dx = px - camera.x
            dy = py - camera.y
            distance = math.sqrt(dx*dx + dy*dy)
            base_volume = max(0.05, 1.0 / (distance / 400 + 1))
            final_volume = base_volume * sfx_volume
            try:
                sound = generate_catch_sound()
                sound.set_volume(min(0.5, final_volume))
                sound.play()
            except pygame.error:
                pass
                
        return collision_data  # Sound system not available or failed
    
    def upgrade_gravity(self):
        """Upgrade the planet's gravity strength, distance, and air resistance"""
        self.gravity_level += 1
        
        # Increase mass (gravity strength)
        self.mass = self.base_mass * (1 + (self.gravity_level - 1) * 0.5)  # 50% increase per level
        
        # Increase gravity distance
        self.gravity_distance = self.base_gravity_distance * (1 + (self.gravity_level - 1) * 0.3)  # 30% increase per level
        
        # Increase air resistance intensity
        self.air_resistance_intensity = self.base_air_resistance_intensity * (1 + (self.gravity_level - 1) * 0.4)  # 40% increase per level
        
        self.upgrade_cost = int(self.upgrade_cost * 1.3)  # Cost increases by 30%
        
        # Visual indication of upgraded planet
        if self.gravity_level > 1:
            # Stronger planets get a different color
            intensity = min(255, 100 + (self.gravity_level - 1) * 20)
            self.color = (intensity, 149, 237)
    
    def upgrade_clone_orbit(self):
        """Add clone orbit zone to the planet"""
        self.has_clone_orbit = True
        # Increase cost for potential future upgrades
        self.clone_orbit_cost = int(self.clone_orbit_cost * 1.5)
    
    def get_visual_radius(self, camera, hover_scale=1.0):
        """Get the visual radius of the planet based on camera mode"""
        if camera.is_map_mode():
            # In map mode, planets are 0.5x size (smaller for overview)
            map_mode_scale = 0.5  # Make planets half size in map mode
            return self.radius * map_mode_scale * hover_scale
        else:
            # Normal mode - scale with camera zoom
            return self.radius * camera.zoom * hover_scale
    
    def update(self, dt, is_hovered=False):
        """Update planet animations"""
        if self.counter_bounce_timer > 0:
            self.counter_bounce_timer -= dt
            # Bounce animation: scale up then down
            progress = 1.0 - (self.counter_bounce_timer / 0.5)
            if progress < 0.5:
                # Scale up phase
                self.counter_bounce_scale = 1.0 + (progress * 2) * 0.5
            else:
                # Scale down phase
                self.counter_bounce_scale = 1.5 - ((progress - 0.5) * 2) * 0.5
            
            if self.counter_bounce_timer <= 0:
                self.counter_bounce_scale = 1.0
        
        # Shimmer animation
        if self.shimmer_timer > 0:
            self.shimmer_timer -= dt
            # Fade out shimmer
            self.shimmer_intensity = self.shimmer_timer / 0.3
            
            if self.shimmer_timer <= 0:
                self.shimmer_intensity = 0
        
        # Wobble animation when hovered
        if is_hovered:
            self.wobble_timer += dt * 8  # Speed of wobble
        else:
            self.wobble_timer = 0
        
    def draw(self, screen, camera, gravity_distance: float = None, air_resistance_intensity: float = None):
        # Convert world position to screen position with wobble effect
        wobble_x = math.sin(self.wobble_timer) * 2 if self.wobble_timer > 0 else 0
        wobble_y = math.cos(self.wobble_timer * 1.3) * 2 if self.wobble_timer > 0 else 0
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        screen_x += wobble_x
        screen_y += wobble_y
        
        # Scale radius with zoom and hover effect
        hover_scale = 1.15 if self.wobble_timer > 0 else 1.0  # 15% bigger when hovered
        
        if camera.is_map_mode():
            # In map mode, planets are 0.5x size (smaller for overview)
            map_mode_scale = 0.5  # Make planets half size in map mode
            scaled_radius = max(4, int(self.radius * map_mode_scale * hover_scale))
            air_radius = max(6, int(self.radius * 3 * map_mode_scale * hover_scale))
        else:
            # Normal mode - scale with camera zoom
            scaled_radius = max(2, int(self.radius * camera.zoom * hover_scale))
            air_radius = max(4, int(self.radius * 3 * camera.zoom * hover_scale))
        
        # Only draw if planet is visible on screen
        margin = air_radius + 50
        if (screen_x < -margin or screen_x > camera.screen_width + margin or 
            screen_y < -margin or screen_y > camera.screen_height + margin):
            return
        
        # Draw atmospheric area (air resistance zone) - only at moderate zoom levels
        if camera.zoom > 0.4 and camera.zoom < 4.0 and air_radius > 4:
            # Create surface only when needed, with optimized size
            atmo_surf = pygame.Surface((air_radius * 2, air_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(atmo_surf, (100, 150, 255, 15), (air_radius, air_radius), air_radius)
            screen.blit(atmo_surf, (screen_x - air_radius, screen_y - air_radius))

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
            if air_r > 3:  # Only draw if large enough to be visible
                air_surf = pygame.Surface((air_r * 2 + 4, air_r * 2 + 4), pygame.SRCALPHA)
                # Color intensity reflects planet's air resistance value
                air_alpha = int(50 + 150 * min(1.0, max(0.0, self.air_resistance_intensity)))
                pygame.draw.circle(air_surf, (100, 150, 255, air_alpha), (air_r + 2, air_r + 2), air_r, 1)
                screen.blit(air_surf, (screen_x - air_r - 2, screen_y - air_r - 2))
            
            # Clone orbit ring - bright purple/magenta ring
            if self.has_clone_orbit:
                clone_r = max(1, int(self.clone_orbit_radius * camera.zoom))
                if clone_r > 2:  # Only draw if large enough to be visible
                    clone_surf = pygame.Surface((clone_r * 2 + 4, clone_r * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(clone_surf, (255, 0, 255, 180), (clone_r + 2, clone_r + 2), clone_r, max(1, int(2 * camera.zoom)))
                    screen.blit(clone_surf, (screen_x - clone_r - 2, screen_y - clone_r - 2))

        # DEBUG visualization rings: gravity and air resistance ranges are handled above
        
        # Draw planet base
        pygame.draw.circle(screen, self.color, (screen_x, screen_y), scaled_radius)
        
        # Draw spots if planet has them
        if self.has_spots and camera.zoom > 0.3:
            spot_color = tuple(max(0, c - 40) for c in self.color)
            for spot_x, spot_y in self.spots:
                spot_screen_x = screen_x + int(spot_x * scaled_radius * 0.7)
                spot_screen_y = screen_y + int(spot_y * scaled_radius * 0.7)
                spot_radius = max(1, int(scaled_radius * 0.15))
                pygame.draw.circle(screen, spot_color, (spot_screen_x, spot_screen_y), spot_radius)
        
        # Draw rings if planet has them
        if self.has_rings and camera.zoom > 0.2:
            ring_radius1 = int(scaled_radius * 1.4)
            ring_radius2 = int(scaled_radius * 1.6)
            ring_color = tuple(c // 2 for c in self.color)
            pygame.draw.circle(screen, ring_color, (screen_x, screen_y), ring_radius2, max(1, int(3 * camera.zoom)))
            pygame.draw.circle(screen, ring_color, (screen_x, screen_y), ring_radius1, max(1, int(2 * camera.zoom)))
        
        # Draw planet outline
        outline_color = WHITE
        if self.shimmer_intensity > 0:
            # Add shimmer effect - bright white outline
            shimmer_alpha = int(255 * self.shimmer_intensity)
            outline_color = (255, 255, 255)
            # Draw additional shimmer glow
            shimmer_surf = pygame.Surface((scaled_radius*4, scaled_radius*4), pygame.SRCALPHA)
            shimmer_color = (*outline_color, shimmer_alpha // 2)
            pygame.draw.circle(shimmer_surf, shimmer_color, (scaled_radius*2, scaled_radius*2), scaled_radius*2)
            screen.blit(shimmer_surf, (screen_x - scaled_radius*2, screen_y - scaled_radius*2))
        
        pygame.draw.circle(screen, outline_color, (screen_x, screen_y), scaled_radius, max(1, int(2 * camera.zoom)))
        
        # Draw collection count and gravity level (always visible in map mode, otherwise when zoomed in enough)
        if camera.is_map_mode() or camera.zoom > 0.2:
            if camera.is_map_mode():
                # Fixed font sizes for map mode
                font_size = 16
                small_font_size = 12
            else:
                # Zoom-based font sizes for normal mode
                font_size = max(12, int(20 * camera.zoom))
                small_font_size = max(10, int(16 * camera.zoom))
            
            font = pygame.font.Font(None, font_size)
            small_font = pygame.font.Font(None, small_font_size)
            
            # Particles collected (with bounce animation)
            bounce_font_size = int(font_size * self.counter_bounce_scale)
            bounce_font = pygame.font.Font(None, bounce_font_size)
            text = bounce_font.render(str(self.particles_collected), True, WHITE)
            text_rect = text.get_rect(center=(screen_x, screen_y - int(3 * camera.zoom)))
            screen.blit(text, text_rect)
            
            # Gravity level indicator
            if self.gravity_level > 1:
                level_text = small_font.render(f"G{self.gravity_level}", True, YELLOW)
                level_rect = level_text.get_rect(center=(screen_x, screen_y + int(8 * camera.zoom)))
                screen.blit(level_text, level_rect)
    
    def draw_preview(self, screen, x, y, size):
        """Draw a small preview of the planet for the UI"""
        # Draw base
        pygame.draw.circle(screen, self.color, (x, y), size)
        
        # Draw spots
        if self.has_spots:
            spot_color = tuple(max(0, c - 40) for c in self.color)
            for spot_x, spot_y in self.spots[:3]:  # Only show first 3 spots
                spot_screen_x = x + int(spot_x * size * 0.7)
                spot_screen_y = y + int(spot_y * size * 0.7)
                spot_radius = max(1, int(size * 0.15))
                pygame.draw.circle(screen, spot_color, (spot_screen_x, spot_screen_y), spot_radius)
        
        # Draw rings
        if self.has_rings:
            ring_radius1 = int(size * 1.4)
            ring_radius2 = int(size * 1.6)
            ring_color = tuple(c // 2 for c in self.color)
            pygame.draw.circle(screen, ring_color, (x, y), ring_radius2, 2)
            pygame.draw.circle(screen, ring_color, (x, y), ring_radius1, 1)
        
        # Draw outline with shimmer
        outline_color = WHITE
        if self.shimmer_intensity > 0:
            # Add shimmer effect to preview
            shimmer_alpha = int(255 * self.shimmer_intensity)
            outline_color = (255, 255, 255)
            # Draw shimmer glow around preview
            shimmer_surf = pygame.Surface((size*4, size*4), pygame.SRCALPHA)
            shimmer_color = (*outline_color, shimmer_alpha // 3)
            pygame.draw.circle(shimmer_surf, shimmer_color, (size*2, size*2), size*2)
            screen.blit(shimmer_surf, (x - size*2, y - size*2))
        
        pygame.draw.circle(screen, outline_color, (x, y), size, 1)

class ParticleEmitter:
    def __init__(self, world_width=80000, world_height=80000):
        self.world_width = world_width
        self.world_height = world_height
        self.spawn_rate = 90  # particles per second
        self.spawn_timer = 0
        self.particles: List[Particle] = []
        self.sound_timer = 0  # To limit sound frequency
        
    def update(self, dt: float, planets: List[Planet], sfx_volume: float = 0.5, camera=None, gravity_distance: float = 500.0, air_resistance_intensity: float = 0.5, walls: List[Wall] = None):
        self.spawn_timer += dt
        self.sound_timer += dt
        spawn_interval = 1.0 / self.spawn_rate
        particles_spawned = 0
        while self.spawn_timer >= spawn_interval:
            self.spawn_timer -= spawn_interval
            px = random.uniform(-self.world_width//2, self.world_width//2)
            py = random.uniform(-self.world_height//2, self.world_height//2)
            pz = random.uniform(0.3, 1.0)
            self.particles.append(Particle(px, py, pz))
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
                    base_volume = max(0.05, 1.0 / (distance / 400 + 1))
                else:
                    base_volume = 0.1
                final_volume = base_volume * sfx_volume
                spawn_sound.set_volume(min(0.5, final_volume))
                spawn_sound.play()
                self.sound_timer = 0
            except pygame.error:
                pass  # Sound system not available or failed
        for particle in self.particles[:]:
            # Process pending clones from this particle
            if hasattr(particle, '_pending_clones') and particle._pending_clones:
                for clone_data in particle._pending_clones:
                    # Create new cloned particle
                    cloned_particle = Particle(clone_data['x'], clone_data['y'], clone_data['z'])
                    cloned_particle.vx = clone_data['vx']
                    cloned_particle.vy = clone_data['vy']
                    cloned_particle.color = clone_data['color']
                    cloned_particle.radius = clone_data['radius']
                    cloned_particle.mass = clone_data['mass']
                    cloned_particle.age = clone_data['age']
                    cloned_particle.lifetime = clone_data['lifetime']
                    # Mark as cloned to prevent re-cloning
                    cloned_particle._cloned_from_planet = True
                    self.particles.append(cloned_particle)
                # Clear pending clones
                particle._pending_clones = []
            
            # Check for explosion
            if particle.exploding and not hasattr(particle, '_explosion_sound_played'):
                if camera:
                    dx = particle.x - camera.x
                    dy = particle.y - camera.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    if distance < 400:
                        base_volume = max(0.05, 1.0 / (distance / 400 + 1))
                    else:
                        base_volume = 0.0
                else:
                    base_volume = 0.1
                final_volume = base_volume * sfx_volume
                try:
                    if final_volume > 0.01:
                        sound = generate_explosion_sound()
                        sound.set_volume(min(0.5, final_volume))
                        sound.play()
                except pygame.error:
                    pass  # Sound system not available or failed
                particle._explosion_sound_played = True
            # Collision detection is handled in particle.update() method
            particle.update(dt, planets, gravity_distance, air_resistance_intensity, camera, sfx_volume, walls)
            if not particle.alive:
                self.particles.remove(particle)
    
    def draw(self, screen, camera, planets=None):
        # Draw all particles - removed aggressive culling that was causing particles to disappear
        for particle in self.particles:
            particle.draw(screen, camera, planets)

class ParticleSpawner:
    """A placeable particle spawner that creates particles at a specific location"""
    def __init__(self, x: float, y: float, spawn_rate: int = 20):
        self.x = x
        self.y = y
        self.spawn_rate = spawn_rate  # particles per second
        self.spawn_timer = 0
        self.particles: List[Particle] = []
        self.radius = 15  # Visual radius
        
    def update(self, dt: float, planets: List[Planet], walls: List[Wall] = None):
        """Update spawner and spawn particles"""
        self.spawn_timer += dt
        spawn_interval = 1.0 / self.spawn_rate
        
        while self.spawn_timer >= spawn_interval:
            self.spawn_timer -= spawn_interval
            # Spawn particle near the spawner location
            offset = 20
            px = self.x + random.uniform(-offset, offset)
            py = self.y + random.uniform(-offset, offset)
            pz = random.uniform(0.3, 1.0)
            self.particles.append(Particle(px, py, pz))
        
        # Update particles
        for particle in self.particles[:]:
            particle.update(dt, planets, 500.0, 0.5, None, 0.5, walls)
            if not particle.alive:
                self.particles.remove(particle)
    
    def draw(self, screen, camera):
        """Draw the spawner"""
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # Always draw particles first, even if spawner is offscreen
        for particle in self.particles:
            particle.draw(screen, camera)
        
        # Only draw spawner visual if it's visible on screen
        margin = 50
        if (screen_x < -margin or screen_x > camera.screen_width + margin or 
            screen_y < -margin or screen_y > camera.screen_height + margin):
            return
        
        # Draw spawner as a pulsing yellow circle
        pulse = math.sin(pygame.time.get_ticks() * 0.005) * 0.3 + 0.7  # Pulse between 0.4 and 1.0
        scaled_radius = max(3, int(self.radius * camera.zoom * pulse))
        color = (int(255 * pulse), int(255 * pulse), 0)  # Yellow with pulsing intensity
        
        pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), scaled_radius)
        pygame.draw.circle(screen, WHITE, (int(screen_x), int(screen_y)), scaled_radius, 2)

class StarField:
    def __init__(self, num_stars=300, width=80000, height=80000, min_depth=0.3, max_depth=1.0):
        self.stars = []
        for _ in range(num_stars):
            x = random.uniform(-width//2, width//2)
            y = random.uniform(-height//2, height//2)
            depth = random.uniform(min_depth, max_depth)
            base_brightness = random.randint(180, 255)
            size = random.randint(25, 50)  # Much bigger minimum star size (was 10-30, now 25-50)
            # Only white stars for clean parallax effect
            color = (base_brightness, base_brightness, base_brightness)
            twinkle_speed = random.uniform(0.5, 2.0)
            self.stars.append({'x': x, 'y': y, 'depth': depth, 'base_brightness': base_brightness, 'size': size, 'color': color, 'twinkle_speed': twinkle_speed, 'twinkle_phase': random.uniform(0, 2 * math.pi)})
    def draw(self, screen, camera):
        t = pygame.time.get_ticks() / 1000.0
        for star in self.stars:
            px = (star['x'] - camera.x * star['depth']) * camera.zoom + camera.screen_width // 2
            py = (star['y'] - camera.y * star['depth']) * camera.zoom + camera.screen_height // 2
            size = max(1, int(star['size'] * camera.zoom * (1.2 - star['depth'])))
            
            # Enhanced twinkle
            twinkle = 0.5 + 0.5 * math.sin(t * star['twinkle_speed'] + star['twinkle_phase'])
            brightness = int(star['base_brightness'] * (0.7 + 0.3 * twinkle))
            color = tuple(min(255, int(c * (0.7 + 0.3 * twinkle))) for c in star['color'])
            
            # Enhanced star rendering with lens flares
            if 0 <= px < camera.screen_width and 0 <= py < camera.screen_height:
                # Multiple glow layers for depth
                if size > 1:
                    for glow_size, alpha in [(size*8, 15), (size*6, 25), (size*4, 40)]:
                        glow_surf = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
                        glow_color = (*color, alpha)
                        pygame.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
                        screen.blit(glow_surf, (int(px) - glow_size, int(py) - glow_size))
                
                # Lens flare effects (cross pattern) for larger stars
                if size >= 2:
                    flare_length = size * 4
                    flare_color = (*color, 80)
                    # Horizontal flare
                    pygame.draw.line(screen, flare_color, 
                                   (int(px) - flare_length, int(py)), (int(px) + flare_length, int(py)), 1)
                    # Vertical flare
                    pygame.draw.line(screen, flare_color, 
                                   (int(px), int(py) - flare_length), (int(px), int(py) + flare_length), 1)
                    
                    # Diagonal flares for brighter stars
                    if size >= 3:
                        diag_len = int(flare_length * 0.7)
                        pygame.draw.line(screen, (*color, 60), 
                                       (int(px) - diag_len, int(py) - diag_len), (int(px) + diag_len, int(py) + diag_len), 1)
                        pygame.draw.line(screen, (*color, 60), 
                                       (int(px) - diag_len, int(py) + diag_len), (int(px) + diag_len, int(py) - diag_len), 1)
                
                # Main star (bright core)
                pygame.draw.circle(screen, color, (int(px), int(py)), size)
                if size > 1:
                    # Bright center
                    center_color = tuple(min(255, int(c * 1.3)) for c in color)
                    pygame.draw.circle(screen, center_color, (int(px), int(py)), max(1, size//2))

class TiledBackground:
    def __init__(self, image_path: str = "Backround.png"):
        self.image_path = image_path
        self.background_image = None
        self.scale = 7.0  # Default scale
        self.load_image()
    
    def load_image(self):
        """Load the background image"""
        try:
            # Load image and ensure it has proper format for transparency
            original_image = pygame.image.load(self.image_path)
            self.background_image = original_image.convert()  # Convert without alpha first
            print(f"Loaded background image: {self.image_path} (size: {self.background_image.get_size()})")
        except pygame.error as e:
            print(f"Could not load background image {self.image_path}: {e}")
            self.background_image = None
    
    def set_scale(self, scale: float):
        """Set the scale of the background tiles"""
        self.scale = max(3.0, min(10.0, scale))  # Clamp between 3.0 and 10.0
    
    def draw(self, screen, camera):
        """Draw the tiled background with performance optimizations"""
        if self.background_image is None:
            return
        
        # Skip background rendering when zoomed in extremely far to improve performance
        if camera.zoom > 5.0:
            return
        
        # Get the original image size
        orig_width = self.background_image.get_width()
        orig_height = self.background_image.get_height()
        
        # Calculate world space tile size (fixed size in world coordinates, only affected by scale setting)
        world_tile_width = orig_width * self.scale
        world_tile_height = orig_height * self.scale
        
        if world_tile_width <= 0 or world_tile_height <= 0:
            return
        
        # Calculate world space coverage needed (what area of the world is visible)
        world_left = camera.x - (camera.screen_width / (2 * camera.zoom))
        world_right = camera.x + (camera.screen_width / (2 * camera.zoom))
        world_top = camera.y - (camera.screen_height / (2 * camera.zoom))
        world_bottom = camera.y + (camera.screen_height / (2 * camera.zoom))
        
        # Calculate starting tile indices (which tiles we need to draw)
        start_tile_x = int(world_left // world_tile_width) - 1
        end_tile_x = int(world_right // world_tile_width) + 2
        start_tile_y = int(world_top // world_tile_height) - 1
        end_tile_y = int(world_bottom // world_tile_height) + 2
        
        # Limit the number of tiles to prevent performance issues when zoomed out very far
        max_tiles_per_axis = 10
        if (end_tile_x - start_tile_x) > max_tiles_per_axis:
            center_x = (start_tile_x + end_tile_x) // 2
            start_tile_x = center_x - max_tiles_per_axis // 2
            end_tile_x = center_x + max_tiles_per_axis // 2
        if (end_tile_y - start_tile_y) > max_tiles_per_axis:
            center_y = (start_tile_y + end_tile_y) // 2
            start_tile_y = center_y - max_tiles_per_axis // 2
            end_tile_y = center_y + max_tiles_per_axis // 2
        
        # Draw tiles
        for tile_x in range(start_tile_x, end_tile_x):
            for tile_y in range(start_tile_y, end_tile_y):
                # Calculate world position of this tile
                world_x = tile_x * world_tile_width
                world_y = tile_y * world_tile_height
                
                # Convert to screen coordinates
                screen_x, screen_y = camera.world_to_screen(world_x, world_y)
                
                # Calculate screen tile size (world tile size * camera zoom)
                screen_tile_width = int(world_tile_width * camera.zoom)
                screen_tile_height = int(world_tile_height * camera.zoom)
                
                # Skip very small tiles for performance
                if screen_tile_width < 4 or screen_tile_height < 4:
                    continue
                
                # Only draw if tile is visible on screen
                if (screen_x + screen_tile_width >= 0 and screen_x < camera.screen_width and
                    screen_y + screen_tile_height >= 0 and screen_y < camera.screen_height):
                    
                    if screen_tile_width > 0 and screen_tile_height > 0:
                        # Scale the image to screen size
                        screen_scaled_image = pygame.transform.scale(self.background_image, (screen_tile_width, screen_tile_height))
                        # Keep background at consistent 50% opacity - simple approach
                        screen_scaled_image.set_alpha(128)  # 50% transparency
                        screen.blit(screen_scaled_image, (screen_x, screen_y))

class Game:
    def __init__(self):
        self.fullscreen = False
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Particle Tycoon - Left Click & Drag to Move, Scroll to Zoom")
        self.clock = pygame.time.Clock()
        
        # Camera system
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Star field
        self.starfield = StarField()
        
        # Tiled background
        self.tiled_background = TiledBackground()
        
        # Game state
        self.money = 100
        self.planets: List[Planet] = []
        self.walls: List[Wall] = []
        self.emitter = ParticleEmitter()  # No longer at (0,0)
        
        # UI state
        self.placing_planet = False
        self.placing_wall = False
        self.placing_spawner = False
        self.placing_dwarf_planet = False
        self.wall_start_pos = None
        self.spawners = []  # List of additional particle spawners
        self.spawner_cost = 200  # Cost to place a spawner
        self.dwarf_planet_cost = 15  # Cheaper dwarf planets
        self.selected_planet = None
        self.hovered_planet = None  # Track which planet is being hovered
        self.planet_cost = 40
        self.wall_cost_per_unit = 0.5  # Cost per distance unit for walls
        self.spawn_rate_cost = 100
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Settings menu
        self.show_settings = False
        self.sfx_volume = 0.5
        self.music_volume = 1.0  # Maximum volume for much louder music
        self.sfx_slider = Slider(250, 180, 150, 20, 0.0, 1.0, self.sfx_volume)
        self.music_slider = Slider(250, 230, 150, 20, 0.0, 1.0, self.music_volume)
        
        # Gravity settings
        self.gravity_distance = 1000.0  # Maximum gravity distance - default to 1000
        self.gravity_slider = Slider(250, 380, 150, 20, 100.0, 1000.0, self.gravity_distance)
        
        # Air resistance settings
        self.air_resistance_intensity = 0.1  # 0.0 to 1.0 scale - default to 0.1
        self.air_resistance_slider = Slider(250, 420, 150, 20, 0.0, 1.0, self.air_resistance_intensity)
        
        # Star visibility setting
        self.show_stars = True  # Show white stars by default
        
        # Background settings
        self.background_scale = 7.0  # Default background scale
        self.background_slider = Slider(250, 460, 150, 20, 3.0, 10.0, self.background_scale)
        self.music_selector = MusicSelector(250, 280, 200, 30)
        # Play a random song on launch (excluding "None")
        if len(self.music_selector.music_files) > 1:  # More than just "None"
            # Get all music files except "None" (index 0)
            music_indices = list(range(1, len(self.music_selector.music_files)))
            if music_indices:
                random_index = random.choice(music_indices)
                self.music_selector.selected_index = random_index
                self.music_selector.play_selected()
        else:
            # No music files available, keep "None" selected
            self.music_selector.play_selected()
        
        # Game stats
        self.total_particles_collected = 0
        
        # Money animation
        self.display_money = 0.0  # Smoothly animated money display
        self.money_animation_speed = 5.0  # Speed of money counter animation
        self.last_money_amount = 0  # Track last money amount for tick sounds
        
        # Visual effects
        self.light_rays = []  # List of active light rays
        self.money_popups = []  # List of active money popups
        
        # Money tracking for graph
        self.money_history = []  # List of (time, money) tuples
        self.money_history_timer = 0
        self.show_money_graph = False
        
        # UI toggles
        self.show_stats = True
        self.show_tutorial = True  # Show tutorial on first boot
        
        # Tutorial
        self.tutorial_completed = False
        self.planet_menu_visible = True
        
        # Placement feedback
        self.placement_error_message = ""
        self.placement_error_timer = 0.0
        
        # Hotbar system
        self.selected_tool = 0  # 0=none, 1=planets, 2=walls
        self.hotbar_tools = [
            {"name": "None", "key": "ESC", "color": GRAY},
            {"name": "Planet", "key": "1", "color": GREEN},
            {"name": "Wall", "key": "2", "color": BLUE},
            {"name": "Spawner", "key": "3", "color": YELLOW},
            {"name": "Dwarf", "key": "4", "color": (150, 100, 50)},  # Brown color for dwarf planets
        ]
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Handle settings menu first
            if self.show_settings:
                self.sfx_slider.handle_event(event)
                self.music_slider.handle_event(event)
                self.gravity_slider.handle_event(event)
                self.air_resistance_slider.handle_event(event)
                self.background_slider.handle_event(event)
                self.music_selector.handle_event(event)
                
                # Update volumes and settings
                if self.sfx_slider.value != self.sfx_volume:
                    self.sfx_volume = self.sfx_slider.value
                
                if self.music_slider.value != self.music_volume:
                    self.music_volume = self.music_slider.value
                
                if self.gravity_slider.value != self.gravity_distance:
                    self.gravity_distance = self.gravity_slider.value
                
                if self.air_resistance_slider.value != self.air_resistance_intensity:
                    self.air_resistance_intensity = self.air_resistance_slider.value
                
                if self.background_slider.value != self.background_scale:
                    self.background_scale = self.background_slider.value
                    self.tiled_background.set_scale(self.background_scale)
            
            # Handle camera controls only if not clicking on UI elements
            ui_clicked = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                # Check if clicking on any UI element
                hotbar_clicked = self.is_click_on_hotbar(mouse_x, mouse_y)
                if (self.is_click_on_settings_button(mouse_x, mouse_y) or
                    hotbar_clicked >= 0 or
                    (not self.show_settings and (
                        self.is_click_on_stats_button(mouse_x, mouse_y) or
                        self.is_click_on_upgrade_gravity_button(mouse_x, mouse_y) or
                        self.is_click_on_clone_orbit_button(mouse_x, mouse_y)
                    )) or
                    (self.show_settings and (
                        200 <= mouse_x <= 700 and 100 <= mouse_y <= 500  # Settings panel area
                    ))):
                    ui_clicked = True
            
            # Only handle camera if not clicking UI
            if not ui_clicked:
                self.camera.handle_event(event)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    
                    # Check tutorial dismissal
                    if self.show_tutorial:
                        panel_h = 400
                        panel_y = SCREEN_HEIGHT // 2 - panel_h // 2
                        ok_y = panel_y + panel_h - 80
                        if SCREEN_WIDTH // 2 - 50 <= mouse_x <= SCREEN_WIDTH // 2 + 50 and ok_y <= mouse_y <= ok_y + 40:  # OK button
                            self.show_tutorial = False
                            self.tutorial_completed = True
                        return True  # Don't process other clicks during tutorial
                    
                    # Check hotbar clicks first (highest priority)
                    if not self.show_settings:
                        hotbar_tool = self.is_click_on_hotbar(mouse_x, mouse_y)
                        if hotbar_tool >= 0:
                            self.select_tool(hotbar_tool)
                            return True  # Don't process other clicks
                    
                    # Check settings button
                    if self.is_click_on_settings_button(mouse_x, mouse_y):
                        self.show_settings = not self.show_settings
                    
                    # Check stats toggle button
                    elif self.is_click_on_stats_button(mouse_x, mouse_y):
                        self.show_stats = not self.show_stats
                    
                    # Check placement first (before UI buttons)
                    elif self.placing_planet:
                        # Convert screen coordinates to world coordinates
                        world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
                        # Place planet if not too close to emitter or other planets AND we have enough money
                        can_place = self.can_place_planet(world_x, world_y)
                        has_money = self.money >= self.planet_cost
                        if can_place and has_money:
                            self.planets.append(Planet(world_x, world_y))
                            self.money -= self.planet_cost
                            self.planet_cost = int(self.planet_cost * 1.15)  # Slower cost increase
                            self.placing_planet = False
                        elif self.money < self.planet_cost:
                            # Show error message if not enough money
                            self.placement_error_message = "Not enough money!"
                            self.placement_error_timer = 3.0
                    
                    elif self.placing_wall:
                        # Convert screen coordinates to world coordinates
                        world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
                        
                        if self.wall_start_pos is None:
                            # First click - set start position
                            self.wall_start_pos = (world_x, world_y)
                        else:
                            # Second click - place wall if we can afford it
                            wall_cost = self.get_wall_cost(self.wall_start_pos, (world_x, world_y))
                            if wall_cost > 0 and self.money >= wall_cost:
                                self.walls.append(Wall(self.wall_start_pos[0], self.wall_start_pos[1], world_x, world_y))
                                self.money -= wall_cost
                                self.placing_wall = False
                                self.wall_start_pos = None
                            else:
                                # Show appropriate error message
                                if wall_cost == 0:
                                    self.placement_error_message = "Wall too short! Minimum 10 units."
                                    self.placement_error_timer = 3.0
                                elif self.money < wall_cost:
                                    self.placement_error_message = "Not enough money!"
                                    self.placement_error_timer = 3.0
                                # Reset wall placement
                                self.wall_start_pos = None
                    
                    elif self.placing_spawner:
                        # Convert screen coordinates to world coordinates
                        world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
                        # Place spawner if we have enough money
                        if self.money >= self.spawner_cost:
                            self.spawners.append(ParticleSpawner(world_x, world_y))
                            self.money -= self.spawner_cost
                            self.spawner_cost = int(self.spawner_cost * 1.25)  # Increase cost for next spawner
                            self.placing_spawner = False
                        else:
                            # Show error message if not enough money
                            self.placement_error_message = "Not enough money!"
                            self.placement_error_timer = 3.0
                    
                    elif self.placing_dwarf_planet:
                        # Convert screen coordinates to world coordinates
                        world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
                        # Place dwarf planet if we have enough money and valid placement
                        if self.can_place_planet(world_x, world_y) and self.money >= self.dwarf_planet_cost:
                            self.planets.append(DwarfPlanet(world_x, world_y))
                            self.money -= self.dwarf_planet_cost
                            self.dwarf_planet_cost = int(self.dwarf_planet_cost * 1.2)  # Slower cost increase than regular planets
                            self.placing_dwarf_planet = False
                        elif self.money < self.dwarf_planet_cost:
                            # Show error message if not enough money
                            self.placement_error_message = "Not enough money!"
                            self.placement_error_timer = 3.0

                    # Hotbar clicks are now handled at the top for higher priority
                    
                    # If settings menu is open, handle settings-specific clicks
                    elif self.show_settings:
                        # Calculate panel positions for new layout
                        panel_width = 800
                        panel_height = 600
                        panel_x = (SCREEN_WIDTH - panel_width) // 2
                        panel_y = (SCREEN_HEIGHT - panel_height) // 2
                        col1_x = panel_x + 30
                        col2_x = panel_x + 400
                        col2_y = panel_y + 60
                        button_y = panel_y + panel_height - 100
                        button_spacing = 140
                        
                        # Check for test money button
                        if col1_x <= mouse_x <= col1_x + 120 and button_y <= mouse_y <= button_y + 35:
                            self.money += 100
                        
                        # Check for tutorial button
                        elif col1_x + button_spacing <= mouse_x <= col1_x + button_spacing + 120 and button_y <= mouse_y <= button_y + 35:
                            self.show_tutorial = True
                        
                        # Check for star visibility toggle button
                        elif col2_x <= mouse_x <= col2_x + 180 and col2_y + 190 <= mouse_y <= col2_y + 225:
                            self.show_stars = not self.show_stars
                        
                        # Check for fullscreen toggle button
                        elif col2_x <= mouse_x <= col2_x + 180 and col2_y + 235 <= mouse_y <= col2_y + 270:
                            self.toggle_fullscreen()
                        
                        # Check for windowed mode button (only in fullscreen)
                        elif self.fullscreen and col2_x <= mouse_x <= col2_x + 180 and col2_y + 280 <= mouse_y <= col2_y + 315:
                            self.toggle_fullscreen()
                        
                        # Check for quit button
                        elif col1_x + button_spacing * 3 <= mouse_x <= col1_x + button_spacing * 3 + 120 and button_y <= mouse_y <= button_y + 35:
                            return False  # Exit game loop
                    
                    # Check if clicking on remaining UI buttons
                    if self.is_click_on_stats_button(mouse_x, mouse_y):
                        self.show_stats = not self.show_stats
                    
                    elif self.is_click_on_upgrade_gravity_button(mouse_x, mouse_y):
                        if self.selected_planet and self.money >= self.selected_planet.upgrade_cost:
                            self.money -= self.selected_planet.upgrade_cost
                            self.selected_planet.upgrade_gravity()
                    
                    elif self.is_click_on_clone_orbit_button(mouse_x, mouse_y):
                        if (self.selected_planet and not self.selected_planet.has_clone_orbit and 
                            self.money >= self.selected_planet.clone_orbit_cost):
                            self.money -= self.selected_planet.clone_orbit_cost
                            self.selected_planet.upgrade_clone_orbit()
                    
                    elif self.is_click_on_upgrade_spawn_button(mouse_x, mouse_y):
                        if self.money >= self.spawn_rate_cost:
                            self.money -= self.spawn_rate_cost
                            self.emitter.spawn_rate += 5  # Increase spawn rate by 5 particles per second
                            self.spawn_rate_cost = int(self.spawn_rate_cost * 1.4)  # Increase cost by 40%
                    
                    else:
                        # Check if clicking on a planet (using visual size)
                        world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
                        clicked_planet = None
                        for planet in self.planets:
                            distance = math.sqrt((world_x - planet.x)**2 + (world_y - planet.y)**2)
                            hover_scale = 1.15 if planet == self.hovered_planet else 1.0
                            visual_radius = planet.get_visual_radius(self.camera, hover_scale)
                            if distance <= visual_radius:
                                clicked_planet = planet
                                break
                        
                        if clicked_planet:
                            if self.camera.is_map_mode():
                                # In map mode, clicking a planet zooms into it
                                self.zoom_to_planet(clicked_planet)
                            else:
                                # In normal mode, clicking a planet selects it for upgrades
                                self.selected_planet = clicked_planet
                        else:
                            self.selected_planet = None
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # First priority: close settings menu if open
                    if self.show_settings:
                        self.show_settings = False
                    else:
                        # Then cancel placement modes and selections
                        self.placing_planet = False
                        self.placing_wall = False
                        self.placing_spawner = False
                        self.placing_dwarf_planet = False
                        self.wall_start_pos = None
                        self.selected_planet = None
                        self.selected_tool = 0  # Reset to no tool
                elif event.key == pygame.K_f:
                    self.toggle_fullscreen()
                # Hotbar hotkeys
                elif event.key == pygame.K_1:
                    self.select_tool(1)  # Planets
                elif event.key == pygame.K_2:
                    self.select_tool(2)  # Walls
                elif event.key == pygame.K_3:
                    self.select_tool(3)  # Future tool
                elif event.key == pygame.K_4:
                    self.select_tool(4)  # Future tool
        
        return True
    
    def draw_map_boundary(self):
        """Draw red border around the map boundary"""
        # Define boundary coordinates
        boundary = MAP_BOUNDARY
        
        # Convert world boundary corners to screen coordinates
        top_left_x, top_left_y = self.camera.world_to_screen(-boundary, -boundary)
        top_right_x, top_right_y = self.camera.world_to_screen(boundary, -boundary)
        bottom_left_x, bottom_left_y = self.camera.world_to_screen(-boundary, boundary)
        bottom_right_x, bottom_right_y = self.camera.world_to_screen(boundary, boundary)
        
        # Draw the four border lines
        border_color = RED
        border_width = 3 if self.camera.is_map_mode() else max(1, int(2 * self.camera.zoom))
        
        # Top border
        pygame.draw.line(self.screen, border_color, (top_left_x, top_left_y), (top_right_x, top_right_y), border_width)
        # Bottom border
        pygame.draw.line(self.screen, border_color, (bottom_left_x, bottom_left_y), (bottom_right_x, bottom_right_y), border_width)
        # Left border
        pygame.draw.line(self.screen, border_color, (top_left_x, top_left_y), (bottom_left_x, bottom_left_y), border_width)
        # Right border
        pygame.draw.line(self.screen, border_color, (top_right_x, top_right_y), (bottom_right_x, bottom_right_y), border_width)
    
    def select_tool(self, tool_id: int):
        """Select a tool from the hotbar"""
        self.selected_tool = tool_id
        
        # Reset placement states
        self.placing_planet = False
        self.placing_wall = False
        self.placing_spawner = False
        self.placing_dwarf_planet = False
        self.wall_start_pos = None
        self.selected_planet = None
        
        # Set appropriate placement state based on tool
        if tool_id == 1:  # Planets
            self.placing_planet = True  # Allow placement mode even without money, check money on actual placement
        elif tool_id == 2:  # Walls
            self.placing_wall = True
        elif tool_id == 3:  # Spawners
            self.placing_spawner = True
        elif tool_id == 4:  # Dwarf Planets
            self.placing_dwarf_planet = True
    
    def can_place_planet(self, x: float, y: float) -> bool:
        # Reset error message
        self.placement_error_message = ""
        self.placement_error_timer = 0.0
        
        # Check distance from other planets - reduced minimum distance for smaller planets
        min_distance = 50  # Reduced from previous calculation for smaller planets
        for planet in self.planets:
            planet_dist = math.sqrt((x - planet.x)**2 + (y - planet.y)**2)
            if planet_dist < min_distance:
                self.placement_error_message = "Too close to another planet!"
                self.placement_error_timer = 3.0  # Show message for 3 seconds
                return False
        
        # No world boundary restrictions - can place anywhere!
        return True
    
    def is_click_on_buy_planet_button(self, x: int, y: int) -> bool:
        return 20 <= x <= 180 and 20 <= y <= 60
    
    def is_click_on_upgrade_spawn_button(self, x: int, y: int) -> bool:
        return 20 <= x <= 230 and 70 <= y <= 110
    
    def is_click_on_test_money_button(self, x: int, y: int) -> bool:
        return 20 <= x <= 120 and 120 <= y <= 160
    
    def is_click_on_upgrade_gravity_button(self, x: int, y: int) -> bool:
        return 20 <= x <= 200 and 170 <= y <= 210
    
    def is_click_on_clone_orbit_button(self, x: int, y: int) -> bool:
        return 20 <= x <= 200 and 220 <= y <= 260
    
    def is_click_on_settings_button(self, x: int, y: int) -> bool:
        return SCREEN_WIDTH - 120 <= x <= SCREEN_WIDTH - 20 and 60 <= y <= 100
    
    def is_click_on_stats_button(self, x: int, y: int) -> bool:
        return 20 <= x <= 120 and SCREEN_HEIGHT - 50 <= y <= SCREEN_HEIGHT - 10
    
    def is_click_on_buy_wall_button(self, x: int, y: int) -> bool:
        return 200 <= x <= 340 and 20 <= y <= 60
    
    def is_click_on_hotbar(self, x: int, y: int) -> int:
        """Check if click is on hotbar, return tool index or -1 if not on hotbar"""
        hotbar_width = len(self.hotbar_tools) * 60 + (len(self.hotbar_tools) - 1) * 10
        hotbar_x = SCREEN_WIDTH // 2 - hotbar_width // 2
        hotbar_y = SCREEN_HEIGHT - 120
        
        for i in range(len(self.hotbar_tools)):
            slot_x = hotbar_x + i * 70
            slot_y = hotbar_y
            slot_size = 60
            
            if slot_x <= x <= slot_x + slot_size and slot_y <= y <= slot_y + slot_size:
                return i
        
        return -1
    
    def get_wall_cost(self, start_pos, end_pos):
        """Calculate the cost of a wall based on its length"""
        if start_pos is None or end_pos is None:
            return 0
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = math.sqrt(dx*dx + dy*dy)
        cost = length * self.wall_cost_per_unit
        # Minimum cost of 1 for any wall, but require minimum length of 10 units
        return max(1, int(cost)) if length >= 10 else 0
    
    def update_hover_state(self):
        """Update which planet is being hovered over"""
        if self.show_settings:  # Don't update hover when settings are open
            self.hovered_planet = None
            return
            
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
        
        self.hovered_planet = None
        for planet in self.planets:
            distance = math.sqrt((world_x - planet.x)**2 + (world_y - planet.y)**2)
            visual_radius = planet.get_visual_radius(self.camera)
            if distance <= visual_radius:
                self.hovered_planet = planet
                break
    
    def zoom_to_planet(self, planet):
        """Zoom the camera to focus on a planet"""
        # Center camera on planet
        self.camera.x = planet.x
        self.camera.y = planet.y
        
        # Set zoom level to show planet nicely (adjust as needed)
        target_zoom = 2.0  # Good zoom level to see planet details
        self.camera.zoom = min(target_zoom, self.camera.max_zoom)
        
        # Select the planet for upgrade UI
        self.selected_planet = planet
    
    def update(self, dt: float):
        # Add game reference to camera for light ray effects
        self.camera._game_ref = self
        
        self.emitter.update(dt, self.planets, self.sfx_volume, self.camera, self.gravity_distance, self.air_resistance_intensity, self.walls)
        
        # Update spawners
        for spawner in self.spawners:
            spawner.update(dt, self.planets, self.walls)
        
        self.music_selector.play_music(self.music_volume)
        
        # Update planet animations
        for planet in self.planets:
            is_hovered = (planet == self.hovered_planet)
            planet.update(dt, is_hovered)
        new_particles_collected = sum(planet.particles_collected for planet in self.planets)
        particles_this_frame = new_particles_collected - self.total_particles_collected
        self.money += particles_this_frame
        self.total_particles_collected = new_particles_collected
        
        # Handle money increases - play tick sounds and create money popups
        money_increase = self.money - self.last_money_amount
        if money_increase > 0:
            # Play tick sound for each money increase
            for _ in range(min(money_increase, 10)):  # Limit to 10 sounds max to avoid spam
                try:
                    tick_sound = generate_tick_sound()
                    tick_sound.set_volume(min(0.3, self.sfx_volume * 0.6))  # Quieter than other sounds
                    tick_sound.play()
                except pygame.error:
                    pass
            
            # Create money popup at a random planet that collected particles
            collecting_planets = [p for p in self.planets if p.particles_collected > 0]
            if collecting_planets:
                popup_planet = random.choice(collecting_planets)
                popup = MoneyPopup(popup_planet.x, popup_planet.y - popup_planet.radius - 20, money_increase)
                self.money_popups.append(popup)
        
        self.last_money_amount = self.money
        
        # Animate money display
        money_diff = self.money - self.display_money
        if abs(money_diff) > 0.1:
            self.display_money += money_diff * self.money_animation_speed * dt
        else:
            self.display_money = self.money
            
        # Update visual effects
        # Update light rays
        self.light_rays = [ray for ray in self.light_rays if ray.update(dt)]
        
        # Update money popups
        self.money_popups = [popup for popup in self.money_popups if popup.update(dt)]
        
        # Update hover state
        self.update_hover_state()
        
        # Update placement error timer
        if self.placement_error_timer > 0:
            self.placement_error_timer -= dt
        
        # Track money history for graph (every 2 seconds)
        self.money_history_timer += dt
        if self.money_history_timer >= 2.0:
            self.money_history_timer = 0
            current_time = pygame.time.get_ticks() / 1000.0
            self.money_history.append((current_time, self.money))
            # Keep only last 100 data points
            if len(self.money_history) > 100:
                self.money_history.pop(0)
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Background removed per user request
        # self.tiled_background.draw(self.screen, self.camera)
        
        # Draw parallax stars (if enabled)
        if self.show_stars:
            self.starfield.draw(self.screen, self.camera)
        
        # Draw red map boundary border
        self.draw_map_boundary()
        
        # Draw walls
        for wall in self.walls:
            wall.draw(self.screen, self.camera)
        
        # Draw emitter and particles
        self.emitter.draw(self.screen, self.camera, self.planets)
        
        # Draw spawners
        for spawner in self.spawners:
            spawner.draw(self.screen, self.camera)
        
        # Draw planets
        for planet in self.planets:
            planet.draw(self.screen, self.camera, self.gravity_distance, self.air_resistance_intensity)
            
            # Highlight selected planet
            if planet == self.selected_planet:
                screen_x, screen_y = self.camera.world_to_screen(planet.x, planet.y)
                highlight_radius = max(5, int((planet.radius + 5) * self.camera.zoom))
                pygame.draw.circle(self.screen, YELLOW, (screen_x, screen_y), highlight_radius, max(2, int(3 * self.camera.zoom)))
        
        # Draw UI first
        self.draw_ui()
        
        # Draw placement preview on top of UI for maximum visibility
        if self.placing_planet:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
            can_place = self.can_place_planet(world_x, world_y)
            has_money = self.money >= self.planet_cost
            color = GREEN if (can_place and has_money) else RED
            preview_radius = max(25, int(35 * self.camera.zoom))  # Even bigger preview
            
            # Draw multiple circles for maximum visibility
            pygame.draw.circle(self.screen, color, (mouse_x, mouse_y), preview_radius, 6)  # Outer thick outline
            pygame.draw.circle(self.screen, color, (mouse_x, mouse_y), max(8, preview_radius//2), 4)  # Middle circle
            pygame.draw.circle(self.screen, color, (mouse_x, mouse_y), max(4, preview_radius//4), 2)  # Inner circle
            
            # Add text label above cursor
            status_text = "PLANET" + (" ✓" if (can_place and has_money) else " ✗")
            text_surface = self.small_font.render(status_text, True, color)
            self.screen.blit(text_surface, (mouse_x - 30, mouse_y - 40))
        
        elif self.placing_wall:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
            
            if self.wall_start_pos is not None:
                # Draw preview line from start position to mouse
                start_screen_x, start_screen_y = self.camera.world_to_screen(self.wall_start_pos[0], self.wall_start_pos[1])
                
                # Calculate cost for preview
                wall_cost = self.get_wall_cost(self.wall_start_pos, (world_x, world_y))
                color = GREEN if self.money >= wall_cost and wall_cost > 0 else RED
                
                # Draw preview line
                pygame.draw.line(self.screen, color, (start_screen_x, start_screen_y), (mouse_x, mouse_y), 5)  # Thicker line
                
                # Draw cost text near mouse
                cost_text = self.small_font.render(f"${wall_cost}", True, color)
                self.screen.blit(cost_text, (mouse_x + 10, mouse_y - 20))
            else:
                # Draw start point indicator
                pygame.draw.circle(self.screen, BLUE, (mouse_x, mouse_y), 8, 3)  # Bigger indicator
        
        elif self.placing_spawner:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            color = GREEN if self.money >= self.spawner_cost else RED
            preview_radius = max(20, int(25 * self.camera.zoom))  # Even bigger spawner preview
            
            # Draw multiple circles for maximum visibility
            pygame.draw.circle(self.screen, color, (mouse_x, mouse_y), preview_radius, 6)  # Outer thick outline
            pygame.draw.circle(self.screen, color, (mouse_x, mouse_y), max(6, preview_radius//2), 4)  # Middle circle
            pygame.draw.circle(self.screen, color, (mouse_x, mouse_y), max(3, preview_radius//4), 2)  # Inner circle
            
            # Add text label above cursor
            status_text = "SPAWNER" + (" ✓" if self.money >= self.spawner_cost else " ✗")
            text_surface = self.small_font.render(status_text, True, color)
            self.screen.blit(text_surface, (mouse_x - 35, mouse_y - 40))
        
        elif self.placing_dwarf_planet:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
            can_place = self.can_place_planet(world_x, world_y)
            has_money = self.money >= self.dwarf_planet_cost
            color = GREEN if (can_place and has_money) else RED
            preview_radius = max(18, int(26 * self.camera.zoom))  # Even bigger dwarf planet preview
            
            # Draw multiple circles for maximum visibility
            pygame.draw.circle(self.screen, color, (mouse_x, mouse_y), preview_radius, 6)  # Outer thick outline
            pygame.draw.circle(self.screen, color, (mouse_x, mouse_y), max(6, preview_radius//2), 4)  # Middle circle
            pygame.draw.circle(self.screen, color, (mouse_x, mouse_y), max(3, preview_radius//4), 2)  # Inner circle
            
            # Add text label above cursor
            status_text = "DWARF" + (" ✓" if (can_place and has_money) else " ✗")
            text_surface = self.small_font.render(status_text, True, color)
            self.screen.blit(text_surface, (mouse_x - 25, mouse_y - 40))
        
        pygame.display.flip()
    
    def draw_ui(self):
        # Money display (with smooth animation)
        money_text = self.font.render(f"Money: ${int(self.display_money)}", True, WHITE)
        self.screen.blit(money_text, (SCREEN_WIDTH - 200, 20))
        
        # Map mode indicator
        if self.camera.is_map_mode():
            # Draw map mode indicator
            indicator_x = SCREEN_WIDTH - 250
            indicator_y = 60
            pygame.draw.circle(self.screen, (0, 255, 0), (indicator_x, indicator_y), 8)
            pygame.draw.circle(self.screen, WHITE, (indicator_x, indicator_y), 8, 2)
            map_text = self.small_font.render("MAP MODE", True, (0, 255, 0))
            self.screen.blit(map_text, (indicator_x + 15, indicator_y - 8))
        
        # Settings button
        pygame.draw.rect(self.screen, DARK_GRAY, (SCREEN_WIDTH - 120, 60, 100, 40))
        pygame.draw.rect(self.screen, WHITE, (SCREEN_WIDTH - 120, 60, 100, 40), 2)
        settings_text = self.small_font.render("Settings", True, WHITE)
        self.screen.blit(settings_text, (SCREEN_WIDTH - 110, 72))
        
        # Settings menu
        if self.show_settings:
            # Semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            
            # Larger settings panel to prevent crowding
            panel_width = 800
            panel_height = 600
            panel_x = (SCREEN_WIDTH - panel_width) // 2
            panel_y = (SCREEN_HEIGHT - panel_height) // 2
            panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
            pygame.draw.rect(self.screen, DARK_GRAY, panel_rect)
            pygame.draw.rect(self.screen, WHITE, panel_rect, 3)
            
            # Settings title
            title_text = self.font.render("Settings", True, WHITE)
            self.screen.blit(title_text, (panel_x + 20, panel_y + 15))
            
            # Left Column - Audio Controls
            col1_x = panel_x + 30
            col1_y = panel_y + 60
            
            audio_title = self.small_font.render("Audio Controls", True, YELLOW)
            self.screen.blit(audio_title, (col1_x, col1_y))
            
            # SFX Volume
            sfx_label = self.small_font.render("SFX Volume:", True, WHITE)
            self.screen.blit(sfx_label, (col1_x, col1_y + 40))
            # Update slider position
            self.sfx_slider.x = col1_x
            self.sfx_slider.y = col1_y + 60
            self.sfx_slider.draw(self.screen)
            
            # Music Volume
            music_label = self.small_font.render("Music Volume:", True, WHITE)
            self.screen.blit(music_label, (col1_x, col1_y + 100))
            # Update slider position
            self.music_slider.x = col1_x
            self.music_slider.y = col1_y + 120
            self.music_slider.draw(self.screen)
            
            # Music Selection
            music_select_label = self.small_font.render("Background Music:", True, WHITE)
            self.screen.blit(music_select_label, (col1_x, col1_y + 160))
            # Update music selector position
            self.music_selector.x = col1_x
            self.music_selector.y = col1_y + 180
            self.music_selector.draw(self.screen)
            
            # Right Column - Game Controls
            col2_x = panel_x + 400
            col2_y = panel_y + 60
            
            game_title = self.small_font.render("Game Controls", True, YELLOW)
            self.screen.blit(game_title, (col2_x, col2_y))
            
            # Gravity Distance
            gravity_label = self.small_font.render(f"Gravity Distance: {int(self.gravity_distance)}", True, WHITE)
            self.screen.blit(gravity_label, (col2_x, col2_y + 40))
            # Update gravity slider position
            self.gravity_slider.x = col2_x
            self.gravity_slider.y = col2_y + 60
            self.gravity_slider.draw(self.screen)
            
            # Air Resistance Intensity
            air_label = self.small_font.render(f"Air Resistance: {self.air_resistance_intensity:.1f}", True, WHITE)
            self.screen.blit(air_label, (col2_x, col2_y + 100))
            # Update air resistance slider position
            self.air_resistance_slider.x = col2_x
            self.air_resistance_slider.y = col2_y + 120
            self.air_resistance_slider.draw(self.screen)
            
            # Background Scale
            bg_label = self.small_font.render(f"Background Scale: {self.background_scale:.1f}", True, WHITE)
            self.screen.blit(bg_label, (col2_x, col2_y + 140))
            # Update background slider position
            self.background_slider.x = col2_x
            self.background_slider.y = col2_y + 160
            self.background_slider.draw(self.screen)
            
            # Star visibility toggle button
            star_label = "Hide Stars" if self.show_stars else "Show Stars"
            star_color = GREEN if self.show_stars else GRAY
            pygame.draw.rect(self.screen, star_color, (col2_x, col2_y + 190, 180, 35))
            pygame.draw.rect(self.screen, WHITE, (col2_x, col2_y + 190, 180, 35), 2)
            star_text = self.small_font.render(star_label, True, BLACK if self.show_stars else WHITE)
            self.screen.blit(star_text, (col2_x + 10, col2_y + 200))
            
            # Fullscreen toggle button
            fs_label = "Go Windowed" if self.fullscreen else "Go Fullscreen"
            pygame.draw.rect(self.screen, LIGHT_GRAY, (col2_x, col2_y + 235, 180, 35))
            pygame.draw.rect(self.screen, WHITE, (col2_x, col2_y + 235, 180, 35), 2)
            fs_text = self.small_font.render(fs_label + " (F)", True, BLACK)
            self.screen.blit(fs_text, (col2_x + 10, col2_y + 245))
            
            # Windowed mode button (only show in fullscreen)
            if self.fullscreen:
                pygame.draw.rect(self.screen, LIGHT_GRAY, (col2_x, col2_y + 280, 180, 35))
                pygame.draw.rect(self.screen, WHITE, (col2_x, col2_y + 280, 180, 35), 2)
                windowed_text = self.small_font.render("Windowed Mode", True, BLACK)
                self.screen.blit(windowed_text, (col2_x + 10, col2_y + 290))
            
            # Bottom Row - Action Buttons
            button_y = panel_y + panel_height - 100
            button_spacing = 140
            
            # Test money button
            pygame.draw.rect(self.screen, YELLOW, (col1_x, button_y, 120, 35))
            pygame.draw.rect(self.screen, WHITE, (col1_x, button_y, 120, 35), 2)
            test_text = self.small_font.render("Test +$100", True, BLACK)
            self.screen.blit(test_text, (col1_x + 10, button_y + 8))
            
            # Tutorial button
            pygame.draw.rect(self.screen, BLUE, (col1_x + button_spacing, button_y, 120, 35))
            pygame.draw.rect(self.screen, WHITE, (col1_x + button_spacing, button_y, 120, 35), 2)
            tutorial_text = self.small_font.render("Show Tutorial", True, WHITE)
            self.screen.blit(tutorial_text, (col1_x + button_spacing + 5, button_y + 8))
            
            # Money Graph button
            graph_color = GREEN if self.show_money_graph else GRAY
            pygame.draw.rect(self.screen, graph_color, (col1_x + button_spacing * 2, button_y, 120, 35))
            pygame.draw.rect(self.screen, WHITE, (col1_x + button_spacing * 2, button_y, 120, 35), 2)
            graph_text = self.small_font.render("Money Graph", True, WHITE)
            self.screen.blit(graph_text, (col1_x + button_spacing * 2 + 5, button_y + 8))
            
            # Quit button
            pygame.draw.rect(self.screen, (200, 50, 50), (col1_x + button_spacing * 3, button_y, 120, 35))
            pygame.draw.rect(self.screen, WHITE, (col1_x + button_spacing * 3, button_y, 120, 35), 2)
            quit_text = self.small_font.render("Quit Game", True, WHITE)
            self.screen.blit(quit_text, (col1_x + button_spacing * 3 + 15, button_y + 8))
            
            # Close instruction
            close_text = self.small_font.render("Click Settings again to close", True, YELLOW)
            close_rect = close_text.get_rect(center=(panel_x + panel_width//2, panel_y + panel_height - 25))
            self.screen.blit(close_text, close_rect)
        
        else:
            # Game UI (only show when settings is closed)
            # Spawn rate upgrade button
            spawn_color = GREEN if self.money >= self.spawn_rate_cost else GRAY
            pygame.draw.rect(self.screen, spawn_color, (20, 70, 210, 40))
            pygame.draw.rect(self.screen, WHITE, (20, 70, 210, 40), 2)
            spawn_text = self.small_font.render(f"Upgrade Spawn Rate (${self.spawn_rate_cost})", True, WHITE)
            self.screen.blit(spawn_text, (25, 82))
            
            # Stats toggle button
            stats_color = GREEN if self.show_stats else GRAY
            pygame.draw.rect(self.screen, stats_color, (20, SCREEN_HEIGHT - 50, 100, 40))
            pygame.draw.rect(self.screen, WHITE, (20, SCREEN_HEIGHT - 50, 100, 40), 2)
            stats_text = self.small_font.render("Stats", True, WHITE)
            self.screen.blit(stats_text, (45, SCREEN_HEIGHT - 38))
            
            # Upgrade gravity button (only show if planet is selected)
            if self.selected_planet:
                gravity_color = GREEN if self.money >= self.selected_planet.upgrade_cost else GRAY
                pygame.draw.rect(self.screen, gravity_color, (20, 170, 180, 40))
                pygame.draw.rect(self.screen, WHITE, (20, 170, 180, 40), 2)
                gravity_text = self.small_font.render(f"Upgrade Gravity (${self.selected_planet.upgrade_cost})", True, WHITE)
                self.screen.blit(gravity_text, (25, 182))
                
                # Clone orbit upgrade button (only show if planet doesn't have clone orbit yet)
                if not self.selected_planet.has_clone_orbit:
                    clone_color = GREEN if self.money >= self.selected_planet.clone_orbit_cost else GRAY
                    pygame.draw.rect(self.screen, clone_color, (20, 220, 180, 40))
                    pygame.draw.rect(self.screen, WHITE, (20, 220, 180, 40), 2)
                    clone_text = self.small_font.render(f"Add Clone Orbit (${self.selected_planet.clone_orbit_cost})", True, WHITE)
                    self.screen.blit(clone_text, (25, 232))
                
                # Selected planet info
                planet_info_y = 270 if not self.selected_planet.has_clone_orbit else 220
                info_text = self.small_font.render(f"Selected: Level {self.selected_planet.gravity_level} Planet", True, YELLOW)
                self.screen.blit(info_text, (20, planet_info_y))
                
                # Show clone orbit status
                if self.selected_planet.has_clone_orbit:
                    clone_info = self.small_font.render("Clone Orbit: ACTIVE", True, (255, 0, 255))
                    self.screen.blit(clone_info, (20, planet_info_y + 20))
            
            # Stats (only show if toggled on)
            if self.show_stats:
                stats_y = 250
                stats = [
                    f"Particles/sec: {self.emitter.spawn_rate}",
                    f"Total Collected: {self.total_particles_collected}",
                    f"Planets: {len(self.planets)}",
                    f"Active Particles: {len(self.emitter.particles)}",
                    f"Zoom: {self.camera.zoom:.2f}x"
                ]
                
                for i, stat in enumerate(stats):
                    stat_text = self.small_font.render(stat, True, WHITE)
                    self.screen.blit(stat_text, (20, stats_y + i * 20))
            
            # Only show essential placement instructions
            if self.placing_planet:
                instruction_text = self.small_font.render("Click to place planet (ESC to cancel)", True, YELLOW)
                self.screen.blit(instruction_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 30))
            elif self.placing_wall:
                if self.wall_start_pos is None:
                    instruction_text = self.small_font.render("Click to set wall start point (ESC to cancel)", True, YELLOW)
                else:
                    instruction_text = self.small_font.render("Click to set wall end point (ESC to cancel)", True, YELLOW)
                self.screen.blit(instruction_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 30))
            elif self.placing_spawner:
                instruction_text = self.small_font.render("Click to place particle spawner (ESC to cancel)", True, YELLOW)
                self.screen.blit(instruction_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 30))
            elif self.placing_dwarf_planet:
                instruction_text = self.small_font.render("Click to place dwarf planet (ESC to cancel)", True, YELLOW)
                self.screen.blit(instruction_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 30))
            
            # Show placement error message
            if self.placement_error_timer > 0 and self.placement_error_message:
                error_text = self.small_font.render(self.placement_error_message, True, RED)
                self.screen.blit(error_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 60))
            
            # Draw hotbar
            self.draw_hotbar()
        
        # Draw planet menu on the right
        if self.planet_menu_visible:
            menu_x = SCREEN_WIDTH - 300
            menu_y = 120
            menu_w = 280
            menu_h = 60 * max(1, len(self.planets)) + 40
            pygame.draw.rect(self.screen, (30, 30, 60), (menu_x, menu_y, menu_w, menu_h))
            pygame.draw.rect(self.screen, WHITE, (menu_x, menu_y, menu_w, menu_h), 2)
            title = self.small_font.render("Your Planets", True, YELLOW)
            self.screen.blit(title, (menu_x + 10, menu_y + 10))
            for i, planet in enumerate(self.planets):
                y = menu_y + 40 + i * 60
                color = GREEN if planet == self.selected_planet else WHITE
                
                # Draw planet preview
                planet.draw_preview(self.screen, menu_x + 30, y + 15, 12)
                
                # Draw planet info
                name_text = self.small_font.render(planet.name, True, color)
                self.screen.blit(name_text, (menu_x + 55, y))
                type_text = self.small_font.render(f"({planet.planet_type['name']})", True, GRAY)
                self.screen.blit(type_text, (menu_x + 55, y + 15))
                count_text = self.small_font.render(f"$ {planet.particles_collected}", True, color)
                self.screen.blit(count_text, (menu_x + 180, y + 8))
        
        # Tutorial screen
        if self.show_tutorial:
            # Semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            # Tutorial panel
            panel_w, panel_h = 600, 400
            panel_x = SCREEN_WIDTH // 2 - panel_w // 2
            panel_y = SCREEN_HEIGHT // 2 - panel_h // 2
            pygame.draw.rect(self.screen, (20, 20, 40), (panel_x, panel_y, panel_w, panel_h))
            pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_w, panel_h), 3)
            
            # Tutorial title
            title = self.font.render("Welcome to Particle Tycoon!", True, YELLOW)
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, panel_y + 40))
            self.screen.blit(title, title_rect)
            
            # Tutorial text
            tutorial_lines = [
                "• Left-click and drag to move around the space",
                "• Scroll wheel to zoom in and out",
                "• Buy planets to collect particles and earn money",
                "• Click on planets to select and upgrade them",
                "• Use the Stats button to toggle information display",
                "• Access Settings for audio controls and fullscreen (F key)",
                "",
                "Build your particle collection empire!"
            ]
            
            for i, line in enumerate(tutorial_lines):
                text = self.small_font.render(line, True, WHITE)
                self.screen.blit(text, (panel_x + 40, panel_y + 100 + i * 30))
            
            # OK button
            ok_button = pygame.Rect(SCREEN_WIDTH // 2 - 50, panel_y + panel_h - 80, 100, 40)
            pygame.draw.rect(self.screen, GREEN, ok_button)
            pygame.draw.rect(self.screen, WHITE, ok_button, 2)
            ok_text = self.small_font.render("OK", True, BLACK)
            ok_rect = ok_text.get_rect(center=ok_button.center)
            self.screen.blit(ok_text, ok_rect)
    
    def draw_hotbar(self):
        """Draw the hotbar at the bottom center of the screen"""
        hotbar_width = len(self.hotbar_tools) * 60 + (len(self.hotbar_tools) - 1) * 10
        hotbar_x = SCREEN_WIDTH // 2 - hotbar_width // 2
        hotbar_y = SCREEN_HEIGHT - 120
        
        for i, tool in enumerate(self.hotbar_tools):
            slot_x = hotbar_x + i * 70
            slot_y = hotbar_y
            slot_size = 60
            
            # Determine slot appearance
            if i == self.selected_tool:
                # Selected slot - bright border
                border_color = YELLOW
                bg_color = tool["color"]
                text_color = WHITE
            elif (i == 1 and self.money < self.planet_cost) or (i > 2):  # Planet unaffordable or future tools
                # Disabled slot - dark appearance
                border_color = DARK_GRAY
                bg_color = DARK_GRAY
                text_color = GRAY
            else:
                # Available slot - normal appearance
                border_color = WHITE
                bg_color = tool["color"]
                text_color = WHITE
            
            # Draw slot background
            pygame.draw.rect(self.screen, bg_color, (slot_x, slot_y, slot_size, slot_size))
            pygame.draw.rect(self.screen, border_color, (slot_x, slot_y, slot_size, slot_size), 3)
            
            # Draw tool name
            name_text = self.small_font.render(tool["name"], True, text_color)
            name_rect = name_text.get_rect(center=(slot_x + slot_size//2, slot_y + slot_size//2 - 10))
            self.screen.blit(name_text, name_rect)
            
            # Draw hotkey
            key_text = self.small_font.render(tool["key"], True, text_color)
            key_rect = key_text.get_rect(center=(slot_x + slot_size//2, slot_y + slot_size//2 + 10))
            self.screen.blit(key_text, key_rect)
            
            # Draw cost for planet tool
            if i == 1:  # Planet tool
                cost_text = self.small_font.render(f"${self.planet_cost}", True, text_color)
                cost_rect = cost_text.get_rect(center=(slot_x + slot_size//2, slot_y + slot_size + 15))
                self.screen.blit(cost_text, cost_rect)
    
    def draw(self):
        """Main draw method that renders everything"""
        # Clear screen
        self.screen.fill(BLACK)
        
        # Draw white parallax stars (always enabled)
        self.starfield.draw(self.screen, self.camera)
        
        # Draw map boundary
        if hasattr(self, 'draw_map_boundary'):
            self.draw_map_boundary()
        
        # Draw walls
        for wall in self.walls:
            wall.draw(self.screen, self.camera, self.gravity_distance, self.air_resistance_intensity)
        
        # Draw planets
        for planet in self.planets:
            planet.draw(self.screen, self.camera, self.gravity_distance, self.air_resistance_intensity)
        
        # Draw spawners
        for spawner in self.spawners:
            spawner.draw(self.screen, self.camera)
        
        # Draw emitter
        self.emitter.draw(self.screen, self.camera)
        
        # Draw light rays
        for light_ray in self.light_rays:
            light_ray.draw(self.screen, self.camera)
        
        # Draw money popups
        for money_popup in self.money_popups:
            money_popup.draw(self.screen, self.camera, self.font)
        
        # Draw UI elements
        if hasattr(self, 'draw_ui'):
            self.draw_ui()
        
        # Draw placement previews
        if hasattr(self, 'draw_placement_previews'):
            self.draw_placement_previews()
        
        # Draw settings menu
        if self.show_settings and hasattr(self, 'draw_settings_menu'):
            self.draw_settings_menu()
        
        # Draw tutorial
        if hasattr(self, 'show_tutorial') and self.show_tutorial and hasattr(self, 'draw_tutorial'):
            self.draw_tutorial()
        
        # Draw stats menu
        if hasattr(self, 'show_stats') and self.show_stats and hasattr(self, 'draw_stats_menu'):
            self.draw_stats_menu()
        
        # Draw money graph
        if self.show_money_graph and hasattr(self, 'draw_money_graph'):
            self.draw_money_graph()
        
        # Draw hotbar
        if hasattr(self, 'draw_hotbar'):
            self.draw_hotbar()
        
        # Update display
        pygame.display.flip()
    
    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
            # Update camera screen size for fullscreen
            self.camera.screen_width = SCREEN_WIDTH
            self.camera.screen_height = SCREEN_HEIGHT
        else:
            # Make windowed mode much smaller so user can grab title bar and move window
            windowed_width = min(1400, SCREEN_WIDTH - 400)
            windowed_height = min(1000, SCREEN_HEIGHT - 300)
            self.screen = pygame.display.set_mode((windowed_width, windowed_height))
            # Update camera screen dimensions for windowed mode
            self.camera.screen_width = windowed_width
            self.camera.screen_height = windowed_height
    
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            
            running = self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
