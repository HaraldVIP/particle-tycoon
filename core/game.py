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
from entities.wall import Wall
from entities.emitter import ParticleEmitter
from entities.spawner import ParticleSpawner
from systems.camera import Camera
from systems.audio import generate_tick_sound, generate_spawn_sound, generate_catch_sound
from ui.components import Slider, MusicSelector
from ui.effects import MoneyPopup, LightRay
from graphics.background import StarField, TiledBackground
from config.constants import *


class Game:
    def __init__(self):
        self.fullscreen = False
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Particle Tycoon - Left Click & Drag to Move, Scroll to Zoom")
        self.clock = pygame.time.Clock()
        
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.starfield = StarField()
        self.tiled_background = TiledBackground()
        
        self.money = 100
        self.display_money = 100.0
        self.money_animation_speed = 5.0
        self.planets: List[Planet] = []
        self.walls: List[Wall] = []
        self.emitter = ParticleEmitter()
        
        self.placing_planet = False
        self.placing_wall = False
        self.placing_spawner = False
        self.placing_dwarf_planet = False
        self.wall_start_pos = None
        self.spawners = []
        self.spawner_cost = SPAWNER_COST
        self.dwarf_planet_cost = DWARF_PLANET_COST
        self.selected_planet = None
        self.hovered_planet = None
        self.planet_cost = PLANET_BASE_COST
        self.wall_cost_per_unit = WALL_COST_PER_UNIT
        self.spawn_rate_cost = SPAWN_RATE_COST
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.show_settings = False
        self.sfx_volume = DEFAULT_SFX_VOLUME
        self.music_volume = DEFAULT_MUSIC_VOLUME
        self.sfx_slider = Slider(250, 180, 150, 20, 0.0, 1.0, self.sfx_volume)
        self.music_slider = Slider(250, 230, 150, 20, 0.0, 1.0, self.music_volume)
        self.gravity_slider = Slider(250, 380, 150, 20, 100.0, 1000.0, DEFAULT_GRAVITY_DISTANCE)
        self.air_resistance_slider = Slider(250, 430, 150, 20, 0.0, 1.0, DEFAULT_AIR_RESISTANCE)
        self.music_selector = MusicSelector(250, 280, 200, 50)
        self.current_music = None
        
        self.money_popups: List[MoneyPopup] = []
        self.light_rays: List[LightRay] = []
        
        self.selected_tool = -1 # -1 for no tool
        self.hotbar_tools = [
            {"name": "Planet", "key": pygame.K_1},
            {"name": "Dwarf", "key": pygame.K_2},
            {"name": "Spawner", "key": pygame.K_3},
            {"name": "Wall", "key": pygame.K_4},
        ]

        self.show_tutorial = True
        self.tutorial_completed = False
        self.show_stats = True

        self.load_music()

    def load_music(self):
        music_file = self.music_selector.get_selected_file()
        if music_file and music_file != self.current_music:
            try:
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1)
                self.current_music = music_file
                self.music_selector.set_playing(self.music_selector.selected_index)
            except Exception as e:
                print(f"Failed to load music {music_file}: {e}")

    def select_tool(self, tool_index: int):
        self.selected_tool = tool_index
        self.placing_planet = tool_index == 0
        self.placing_dwarf_planet = tool_index == 1
        self.placing_spawner = tool_index == 2
        self.placing_wall = tool_index == 3
        self.wall_start_pos = None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if self.show_tutorial:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.show_tutorial = False
                    self.tutorial_completed = True
                continue

            if self.show_settings:
                # Handle settings UI events
                continue
            
            self.camera.handle_event(event)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.placing_planet = self.placing_wall = self.placing_spawner = self.placing_dwarf_planet = False
                    self.selected_planet = None
                    self.selected_tool = -1
                elif event.key == pygame.K_s: self.show_settings = not self.show_settings
                elif event.key == pygame.K_F11: self.toggle_fullscreen()
                else:
                    for i, tool in enumerate(self.hotbar_tools):
                        if event.key == tool["key"]:
                            self.select_tool(i)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = event.pos
                if self.handle_ui_click(mouse_x, mouse_y): continue

                world_x, world_y = self.camera.screen_to_world(mouse_x, mouse_y)

                if self.placing_planet and self.money >= self.planet_cost:
                    self.planets.append(Planet(world_x, world_y))
                    self.money -= self.planet_cost
                elif self.placing_dwarf_planet and self.money >= self.dwarf_planet_cost:
                    self.planets.append(DwarfPlanet(world_x, world_y))
                    self.money -= self.dwarf_planet_cost
                elif self.placing_spawner and self.money >= self.spawner_cost:
                    self.spawners.append(ParticleSpawner(world_x, world_y))
                    self.money -= self.spawner_cost
                elif self.placing_wall:
                    if self.wall_start_pos is None:
                        self.wall_start_pos = (world_x, world_y)
                    else:
                        self.walls.append(Wall(self.wall_start_pos[0], self.wall_start_pos[1], world_x, world_y))
                        self.wall_start_pos = None
                else:
                    self.selected_planet = None
                    for planet in self.planets:
                        if math.hypot(planet.x - world_x, planet.y - world_y) < planet.radius + 10:
                            self.selected_planet = planet
                            break
        return True

    def handle_ui_click(self, mouse_x: int, mouse_y: int) -> bool:
        hotbar_y = self.screen.get_height() - 70
        for i, tool in enumerate(self.hotbar_tools):
            hotbar_x = self.screen.get_width() // 2 - (len(self.hotbar_tools) * 60) // 2 + i * 60
            if hotbar_x <= mouse_x <= hotbar_x + 50 and hotbar_y <= mouse_y <= hotbar_y + 50:
                self.select_tool(i)
                return True

        if 10 <= mouse_x <= 110 and self.screen.get_height() - 50 <= mouse_y <= self.screen.get_height() - 10:
            self.show_stats = not self.show_stats
            return True
        return False

    def update(self, dt):
        self.emitter.update(dt, self.planets, self.sfx_volume, self.camera, self.gravity_slider.value, self.air_resistance_slider.value, self.walls)
        for spawner in self.spawners:
            spawner.update(dt, self.planets, self.sfx_volume, self.camera, self.gravity_slider.value, self.air_resistance_slider.value, self.walls)
        
        mouse_pos = pygame.mouse.get_pos()
        world_mouse_x, world_mouse_y = self.camera.screen_to_world(mouse_pos[0], mouse_pos[1])
        self.hovered_planet = None
        for planet in self.planets:
            if math.hypot(planet.x - world_mouse_x, planet.y - world_mouse_y) < planet.radius + 10:
                self.hovered_planet = planet
            planet.update(dt, self.hovered_planet == planet)

        all_particles = self.emitter.particles + [p for s in self.spawners for p in s.particles]
        for p in all_particles:
            if not p.alive: continue
            for planet in self.planets:
                if math.hypot(p.x - planet.x, p.y - planet.y) < planet.radius + p.radius:
                    self.money += planet.collect_particle()
                    p.alive = False
                    try:
                        sound = generate_catch_sound()
                        sound.set_volume(self.sfx_volume * 0.5)
                        sound.play()
                    except Exception as e:
                        print(f"Error playing catch sound: {e}")
                    break

        money_diff = self.money - self.display_money
        self.display_money += money_diff * self.money_animation_speed * dt

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        mode = pygame.FULLSCREEN if self.fullscreen else 0
        self.screen = pygame.display.set_mode((self.screen.get_width(), self.screen.get_height()), mode)

    def draw(self):
        self.screen.fill(BLACK)
        self.tiled_background.draw(self.screen, self.camera)
        self.starfield.draw(self.screen, self.camera)
        
        for entity in sorted(self.walls + self.planets + self.spawners, key=lambda e: e.y):
            entity.draw(self.screen, self.camera)

        self.emitter.draw(self.screen, self.camera, self.planets)
        for spawner in self.spawners:
            spawner.draw(self.screen, self.camera, self.planets)
        
        self.draw_ui()
        if self.show_settings: self.draw_settings()
        if self.show_tutorial: self.draw_tutorial()
        pygame.display.flip()

    def draw_hotbar(self):
        hotbar_y = self.screen.get_height() - 70
        n_tools = len(self.hotbar_tools)
        for i, tool in enumerate(self.hotbar_tools):
            hotbar_x = self.screen.get_width() // 2 - (n_tools * 60) // 2 + i * 60
            rect = pygame.Rect(hotbar_x, hotbar_y, 50, 50)
            is_selected = self.selected_tool == i
            color = YELLOW if is_selected else WHITE
            pygame.draw.rect(self.screen, color, rect, 2)
            tool_text = self.small_font.render(tool["name"], True, color)
            self.screen.blit(tool_text, tool_text.get_rect(center=rect.center))
            key_text = self.small_font.render(pygame.key.name(tool["key"]), True, color)
            self.screen.blit(key_text, (rect.x + 5, rect.y + 35))

    def draw_ui(self):
        money_text = self.font.render(f"Money: ${self.display_money:.0f}", True, WHITE)
        self.screen.blit(money_text, (10, 10))
        
        if self.camera.is_map_mode():
            map_text = self.font.render("Map Mode", True, YELLOW)
            text_rect = map_text.get_rect(center=(self.camera.screen_width // 2, self.camera.screen_height - 30))
            self.screen.blit(map_text, text_rect)

        self.draw_hotbar()
        
        stats_btn_rect = pygame.Rect(10, self.screen.get_height() - 50, 100, 40)
        stats_btn_color = GREEN if self.show_stats else GRAY
        pygame.draw.rect(self.screen, stats_btn_color, stats_btn_rect)
        stats_text = self.small_font.render("Stats", True, BLACK)
        self.screen.blit(stats_text, stats_text.get_rect(center=stats_btn_rect.center))

        if self.show_stats:
            stats_y = self.screen.get_height() - 200
            stats = [
                f"Particles: {len(self.emitter.particles) + sum(len(s.particles) for s in self.spawners)}",
                f"Planets: {len(self.planets)}",
                f"Zoom: {self.camera.zoom:.2f}x",
                f"FPS: {self.clock.get_fps():.1f}"
            ]
            for i, stat in enumerate(stats):
                stat_text = self.small_font.render(stat, True, WHITE)
                self.screen.blit(stat_text, (10, stats_y + i * 20))

    def draw_settings(self):
        settings_rect = pygame.Rect(200, 100, 400, 380)
        pygame.draw.rect(self.screen, DARK_GRAY, settings_rect)
        pygame.draw.rect(self.screen, WHITE, settings_rect, 2)
        
        title_text = self.font.render("Settings (ESC to close)", True, WHITE)
        self.screen.blit(title_text, (220, 120))
        
        labels = ["SFX Volume", "Music Volume", "Music Track", "Gravity Range", "Air Resistance"]
        sliders = [self.sfx_slider, self.music_slider, self.music_selector, self.gravity_slider, self.air_resistance_slider]
        for i, (label, slider) in enumerate(zip(labels, sliders)):
            text = self.small_font.render(f"{label}: {slider.value:.2f}" if isinstance(slider, Slider) else label, True, WHITE)
            self.screen.blit(text, (220, 160 + i * 50))
            slider.x = 250
            slider.y = 180 + i * 50
            slider.draw(self.screen)

    def draw_tutorial(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0,0))

        panel_w, panel_h = 600, 400
        panel_x = self.screen.get_width() // 2 - panel_w // 2
        panel_y = self.screen.get_height() // 2 - panel_h // 2
        pygame.draw.rect(self.screen, (20, 20, 40), (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_w, panel_h), 3)

        title = self.font.render("Welcome to Particle Tycoon!", True, YELLOW)
        self.screen.blit(title, (panel_x + 20, panel_y + 20))

        lines = [
            "• Use keys 1-4 to select a tool from the hotbar.",
            "• Click to place planets, spawners, or walls.",
            "• Scroll to zoom, left-click and drag to pan.",
            "• Collect particles with planets to earn money.",
            "• Click a planet to select it and see upgrade options.",
            "• Press 'S' to open settings.",
            "Click anywhere to dismiss."
        ]
        for i, line in enumerate(lines):
            text = self.small_font.render(line, True, WHITE)
            self.screen.blit(text, (panel_x + 30, panel_y + 80 + i * 30))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            if not self.handle_events(): break
            self.update(dt)
            self.draw()
        pygame.quit()
