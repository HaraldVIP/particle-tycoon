"""
Background graphics, including the parallax starfield and tiled backgrounds.
"""
import pygame
import random
import math
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from systems.camera import Camera

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

    def draw(self, screen, camera: 'Camera'):
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

    def draw(self, screen, camera: 'Camera'):
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
