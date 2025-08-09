"""
Main Game class with all functionality from the original game
"""
import pygame
import random
import math
import os
from typing import List

# Import from our modular structure
from entities.particle import Particle
from entities.planet import Planet, DwarfPlanet
from systems.camera import Camera
from systems.audio import generate_tick_sound, generate_spawn_sound
from ui.components import Slider, MusicSelector
from ui.effects import MoneyPopup, LightRay
from config.constants import *


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
        
    def draw(self, screen, camera, gravity_distance: float = None, air_resistance_intensity: float = None):
        sx1, sy1 = camera.world_to_screen(self.x1, self.y1)
        sx2, sy2 = camera.world_to_screen(self.x2, self.y2)
        pygame.draw.line(screen, (100, 100, 255), (sx1, sy1), (sx2, sy2), max(2, int(3 * camera.zoom)))


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
    
    def draw(self, screen, camera, planets=None):
        for particle in self.particles:
            particle.draw(screen, camera, planets)


class ParticleSpawner:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.spawn_rate = 5  # particles per second
        self.spawn_timer = 0
        self.particles: List[Particle] = []
        
    def update(self, dt: float, planets: List[Planet], sfx_volume: float = 0.5, camera=None, gravity_distance: float = 500.0, air_resistance_intensity: float = 0.5, walls: List[Wall] = None):
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
    
    def draw(self, screen, camera, planets=None):
        # Draw the spawner itself
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        pygame.draw.circle(screen, (255, 255, 0), (int(screen_x), int(screen_y)), max(3, int(8 * camera.zoom)))
        pygame.draw.circle(screen, (255, 255, 255), (int(screen_x), int(screen_y)), max(3, int(8 * camera.zoom)), 2)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(screen, camera, planets)


class StarField:
    def __init__(self, num_stars=300, width=80000, height=80000, min_depth=0.3, max_depth=1.0):
        self.stars = []
        for _ in range(num_stars):
            self.stars.append({
                'x': random.uniform(-width//2, width//2),
                'y': random.uniform(-height//2, height//2),
                'size': random.uniform(0.5, 2.0),
                'depth': random.uniform(min_depth, max_depth),
                'color': random.choice([(255, 255, 255), (255, 255, 200), (200, 200, 255), (255, 200, 200)]),
                'base_brightness': random.randint(100, 255),
                'twinkle_speed': random.uniform(0.5, 2.0),
                'twinkle_phase': random.uniform(0, 2 * math.pi)
            })

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
                    for layer in range(3):
                        layer_size = size + layer * 2
                        layer_alpha = max(20, brightness // (layer + 1))
                        glow_surf = pygame.Surface((layer_size * 2, layer_size * 2), pygame.SRCALPHA)
                        glow_color = (*color, layer_alpha)
                        pygame.draw.circle(glow_surf, glow_color, (layer_size, layer_size), layer_size)
                        screen.blit(glow_surf, (px - layer_size, py - layer_size))
                
                # Main star
                pygame.draw.circle(screen, color, (int(px), int(py)), size)


# Background functionality removed as requested


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
        self.spawner_cost = SPAWNER_COST
        self.dwarf_planet_cost = DWARF_PLANET_COST
        self.selected_planet = None
        self.hovered_planet = None  # Track which planet is being hovered
        self.planet_cost = PLANET_BASE_COST
        self.wall_cost_per_unit = WALL_COST_PER_UNIT
        self.spawn_rate_cost = SPAWN_RATE_COST
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Settings menu
        self.show_settings = False
        self.sfx_volume = DEFAULT_SFX_VOLUME
        self.music_volume = DEFAULT_MUSIC_VOLUME
        self.sfx_slider = Slider(250, 180, 150, 20, 0.0, 1.0, self.sfx_volume)
        self.music_slider = Slider(250, 230, 150, 20, 0.0, 1.0, self.music_volume)
        
        # Gravity settings
        self.gravity_distance = DEFAULT_GRAVITY_DISTANCE
        self.gravity_slider = Slider(250, 380, 150, 20, 100.0, 1000.0, self.gravity_distance)
        
        # Air resistance settings
        self.air_resistance_intensity = DEFAULT_AIR_RESISTANCE
        self.air_resistance_slider = Slider(250, 430, 150, 20, 0.0, 1.0, self.air_resistance_intensity)
        
        # Music system
        self.music_selector = MusicSelector(250, 280, 200, 50)
        self.current_music = None
        
        # UI Effects
        self.money_popups: List[MoneyPopup] = []
        self.light_rays: List[LightRay] = []
        
        # Load and play music
        self.load_music()

    def load_music(self):
        """Load and start playing background music"""
        music_file = self.music_selector.get_selected_file()
        if music_file and music_file != self.current_music:
            try:
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1)  # Loop indefinitely
                self.current_music = music_file
                self.music_selector.set_playing(self.music_selector.selected_index)
            except Exception as e:
                print(f"Failed to load music {music_file}: {e}")

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
                
                if self.music_selector.handle_event(event):
                    self.load_music()  # Reload music if selection changed
                
                # Update volumes and settings
                if self.sfx_slider.value != self.sfx_volume:
                    self.sfx_volume = self.sfx_slider.value
                
                if self.music_slider.value != self.music_volume:
                    self.music_volume = self.music_slider.value
                    pygame.mixer.music.set_volume(self.music_volume)
                
                if self.gravity_slider.value != self.gravity_distance:
                    self.gravity_distance = self.gravity_slider.value
                
                if self.air_resistance_slider.value != self.air_resistance_intensity:
                    self.air_resistance_intensity = self.air_resistance_slider.value
                
                # Settings menu key handling
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.show_settings = False
                
                continue  # Skip other event handling when in settings
            
            # Camera events
            self.camera.handle_event(event)
            
            # Key events
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Cancel any placement mode
                    self.placing_planet = False
                    self.placing_wall = False
                    self.placing_spawner = False
                    self.placing_dwarf_planet = False
                    self.selected_planet = None
                elif event.key == pygame.K_s:
                    self.show_settings = not self.show_settings
                elif event.key == pygame.K_F11:
                    self.toggle_fullscreen()
            
            # Mouse events
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_x, mouse_y = event.pos
                    world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)
                    
                    # Check UI button clicks first
                    if self.handle_ui_click(mouse_x, mouse_y):
                        continue
                    
                    # Handle placement modes
                    if self.placing_planet and self.money >= self.planet_cost:
                        self.planets.append(Planet(world_x, world_y))
                        self.money -= self.planet_cost
                        self.placing_planet = False
                        
                        # Play purchase sound
                        try:
                            tick_sound = generate_tick_sound()
                            tick_sound.set_volume(self.sfx_volume)
                            tick_sound.play()
                        except:
                            pass
                    
                    elif self.placing_dwarf_planet and self.money >= self.dwarf_planet_cost:
                        self.planets.append(DwarfPlanet(world_x, world_y))
                        self.money -= self.dwarf_planet_cost
                        self.placing_dwarf_planet = False
                        
                        # Play purchase sound
                        try:
                            tick_sound = generate_tick_sound()
                            tick_sound.set_volume(self.sfx_volume)
                            tick_sound.play()
                        except:
                            pass
                    
                    elif self.placing_spawner and self.money >= self.spawner_cost:
                        self.spawners.append(ParticleSpawner(world_x, world_y))
                        self.money -= self.spawner_cost
                        self.placing_spawner = False
                        
                        # Play purchase sound
                        try:
                            tick_sound = generate_tick_sound()
                            tick_sound.set_volume(self.sfx_volume)
                            tick_sound.play()
                        except:
                            pass
                    
                    elif self.placing_wall:
                        if self.wall_start_pos is None:
                            self.wall_start_pos = (world_x, world_y)
                        else:
                            wall_length = math.sqrt((world_x - self.wall_start_pos[0])**2 + (world_y - self.wall_start_pos[1])**2)
                            wall_cost = wall_length * self.wall_cost_per_unit
                            if self.money >= wall_cost:
                                self.walls.append(Wall(self.wall_start_pos[0], self.wall_start_pos[1], world_x, world_y))
                                self.money -= wall_cost
                                self.placing_wall = False
                                self.wall_start_pos = None
                                
                                # Play purchase sound
                                try:
                                    tick_sound = generate_tick_sound()
                                    tick_sound.set_volume(self.sfx_volume)
                                    tick_sound.play()
                                except:
                                    pass
                    
                    else:
                        # Select planet
                        self.selected_planet = None
                        for planet in self.planets:
                            dx = planet.x - world_x
                            dy = planet.y - world_y
                            distance = math.sqrt(dx*dx + dy*dy)
                            if distance < planet.radius + 10:  # 10 pixel tolerance
                                self.selected_planet = planet
                                break
        
        return True

    def handle_ui_click(self, mouse_x: int, mouse_y: int) -> bool:
        """Handle UI button clicks. Returns True if a UI element was clicked."""
        # Buy Planet button
        if 50 <= mouse_x <= 200 and 50 <= mouse_y <= 90:
            if self.money >= self.planet_cost:
                self.placing_planet = True
                self.placing_dwarf_planet = False
                self.placing_spawner = False
                self.placing_wall = False
            return True
        
        # Buy Dwarf Planet button
        if 50 <= mouse_x <= 200 and 100 <= mouse_y <= 140:
            if self.money >= self.dwarf_planet_cost:
                self.placing_dwarf_planet = True
                self.placing_planet = False
                self.placing_spawner = False
                self.placing_wall = False
            return True
        
        # Buy Spawner button
        if 50 <= mouse_x <= 200 and 150 <= mouse_y <= 190:
            if self.money >= self.spawner_cost:
                self.placing_spawner = True
                self.placing_planet = False
                self.placing_dwarf_planet = False
                self.placing_wall = False
            return True
        
        # Buy Wall button
        if 50 <= mouse_x <= 200 and 200 <= mouse_y <= 240:
            self.placing_wall = True
            self.placing_planet = False
            self.placing_dwarf_planet = False
            self.placing_spawner = False
            self.wall_start_pos = None
            return True
        
        # Increase spawn rate button
        if 50 <= mouse_x <= 200 and 250 <= mouse_y <= 290:
            if self.money >= self.spawn_rate_cost:
                self.emitter.spawn_rate += 10
                self.money -= self.spawn_rate_cost
                self.spawn_rate_cost = int(self.spawn_rate_cost * 1.5)  # Increase cost
                
                # Play purchase sound
                try:
                    tick_sound = generate_tick_sound()
                    tick_sound.set_volume(self.sfx_volume)
                    tick_sound.play()
                except:
                    pass
            return True
        
        return False

    def update(self, dt):
        # Update particle emitter
        self.emitter.update(dt, self.planets, self.sfx_volume, self.camera, self.gravity_distance, self.air_resistance_intensity, self.walls)
        
        # Update spawners
        for spawner in self.spawners:
            spawner.update(dt, self.planets, self.sfx_volume, self.camera, self.gravity_distance, self.air_resistance_intensity, self.walls)
        
        # Update planets and check for hover
        mouse_pos = pygame.mouse.get_pos()
        world_mouse_x, world_mouse_y = self.camera.screen_to_world(mouse_pos[0], mouse_pos[1])
        self.hovered_planet = None
        
        for planet in self.planets:
            # Check if mouse is hovering over this planet
            dx = planet.x - world_mouse_x
            dy = planet.y - world_mouse_y
            distance = math.sqrt(dx*dx + dy*dy)
            is_hovered = distance < planet.radius + 10
            
            if is_hovered:
                self.hovered_planet = planet
            
            planet.update(dt, is_hovered)
        
        # Collect money from particles that were collected
        money_earned = 0
        for particle in self.emitter.particles:
            if hasattr(particle, '_pending_clones') and particle._pending_clones:
                for clone_data in particle._pending_clones:
                    money_earned += clone_data['value']
                    # Create money popup and light rays
                    self.money_popups.append(MoneyPopup(clone_data['position'][0], clone_data['position'][1], clone_data['value']))
                    # Create light rays in multiple directions
                    for i in range(8):
                        angle = (i / 8) * 2 * math.pi
                        self.light_rays.append(LightRay(clone_data['position'][0], clone_data['position'][1], angle))
                particle._pending_clones.clear()
        
        # Check spawner particles too
        for spawner in self.spawners:
            for particle in spawner.particles:
                if hasattr(particle, '_pending_clones') and particle._pending_clones:
                    for clone_data in particle._pending_clones:
                        money_earned += clone_data['value']
                        # Create money popup and light rays
                        self.money_popups.append(MoneyPopup(clone_data['position'][0], clone_data['position'][1], clone_data['value']))
                        # Create light rays in multiple directions
                        for i in range(8):
                            angle = (i / 8) * 2 * math.pi
                            self.light_rays.append(LightRay(clone_data['position'][0], clone_data['position'][1], angle))
                    particle._pending_clones.clear()
        
        if money_earned > 0:
            self.money += money_earned
        
        # Update UI effects
        self.money_popups = [popup for popup in self.money_popups if popup.update(dt)]
        self.light_rays = [ray for ray in self.light_rays if ray.update(dt)]

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        else:
            # Use windowed mode with reasonable size
            windowed_width = min(1600, SCREEN_WIDTH - 200)
            windowed_height = min(1000, SCREEN_HEIGHT - 300)
            self.screen = pygame.display.set_mode((windowed_width, windowed_height))
            # Update camera screen dimensions for windowed mode
            self.camera.screen_width = windowed_width
            self.camera.screen_height = windowed_height

    def draw(self):
        # Clear screen
        self.screen.fill(BLACK)
        
        # Draw starfield
        self.starfield.draw(self.screen, self.camera)
        
        # Draw particle emitter
        self.emitter.draw(self.screen, self.camera, self.planets)
        
        # Draw spawners
        for spawner in self.spawners:
            spawner.draw(self.screen, self.camera, self.planets)
        
        # Draw walls
        for wall in self.walls:
            wall.draw(self.screen, self.camera, self.gravity_distance, self.air_resistance_intensity)
        
        # Draw planets
        for planet in self.planets:
            planet.draw(self.screen, self.camera, self.gravity_distance, self.air_resistance_intensity)
        
        # Draw UI effects
        for popup in self.money_popups:
            popup.draw(self.screen, self.camera, self.small_font)
        
        for ray in self.light_rays:
            ray.draw(self.screen, self.camera)
        
        # Draw UI
        self.draw_ui()
        
        # Draw settings menu if open
        if self.show_settings:
            self.draw_settings()
        
        pygame.display.flip()

    def draw_ui(self):
        # Money display
        money_text = self.font.render(f"Money: ${self.money:.0f}", True, WHITE)
        self.screen.blit(money_text, (10, 10))
        
        # Particle count
        total_particles = len(self.emitter.particles)
        for spawner in self.spawners:
            total_particles += len(spawner.particles)
        particle_text = self.small_font.render(f"Particles: {total_particles}", True, WHITE)
        self.screen.blit(particle_text, (10, 50))
        
        # Spawn rate
        spawn_text = self.small_font.render(f"Spawn Rate: {self.emitter.spawn_rate}/s", True, WHITE)
        self.screen.blit(spawn_text, (10, 70))
        
        # Controls
        controls = [
            "Left-drag: Move camera",
            "Scroll: Zoom",
            "S: Settings",
            "F11: Fullscreen",
            "ESC: Cancel"
        ]
        for i, control in enumerate(controls):
            control_text = self.small_font.render(control, True, LIGHT_GRAY)
            self.screen.blit(control_text, (10, 100 + i * 20))
        
        # Buy buttons
        buttons = [
            (f"Buy Planet (${self.planet_cost})", self.money >= self.planet_cost, self.placing_planet),
            (f"Buy Dwarf Planet (${self.dwarf_planet_cost})", self.money >= self.dwarf_planet_cost, self.placing_dwarf_planet),
            (f"Buy Spawner (${self.spawner_cost})", self.money >= self.spawner_cost, self.placing_spawner),
            ("Buy Wall", True, self.placing_wall),
            (f"Upgrade Spawn Rate (${self.spawn_rate_cost})", self.money >= self.spawn_rate_cost, False)
        ]
        
        for i, (text, affordable, active) in enumerate(buttons):
            y = 250 + i * 50
            color = GREEN if affordable else RED
            if active:
                color = YELLOW
            
            button_rect = pygame.Rect(50, y, 200, 40)
            pygame.draw.rect(self.screen, color, button_rect)
            pygame.draw.rect(self.screen, WHITE, button_rect, 2)
            
            button_text = self.small_font.render(text, True, BLACK)
            text_rect = button_text.get_rect(center=button_rect.center)
            self.screen.blit(button_text, text_rect)

    def draw_settings(self):
        # Settings background
        settings_rect = pygame.Rect(200, 100, 400, 380)
        pygame.draw.rect(self.screen, DARK_GRAY, settings_rect)
        pygame.draw.rect(self.screen, WHITE, settings_rect, 2)
        
        # Settings title
        title_text = self.font.render("Settings (ESC to close)", True, WHITE)
        self.screen.blit(title_text, (220, 120))
        
        # SFX Volume
        sfx_text = self.small_font.render(f"SFX Volume: {self.sfx_volume:.2f}", True, WHITE)
        self.screen.blit(sfx_text, (220, 160))
        self.sfx_slider.draw(self.screen)
        
        # Music Volume
        music_text = self.small_font.render(f"Music Volume: {self.music_volume:.2f}", True, WHITE)
        self.screen.blit(music_text, (220, 210))
        self.music_slider.draw(self.screen)
        
        # Music Selection
        music_label = self.small_font.render("Music Track:", True, WHITE)
        self.screen.blit(music_label, (220, 260))
        self.music_selector.draw(self.screen)
        
        # Gravity Distance
        gravity_text = self.small_font.render(f"Gravity Range: {self.gravity_distance:.0f}", True, WHITE)
        self.screen.blit(gravity_text, (220, 360))
        self.gravity_slider.draw(self.screen)
        
        # Air Resistance
        air_text = self.small_font.render(f"Air Resistance: {self.air_resistance_intensity:.2f}", True, WHITE)
        self.screen.blit(air_text, (220, 410))
        self.air_resistance_slider.draw(self.screen)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            
            running = self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()
