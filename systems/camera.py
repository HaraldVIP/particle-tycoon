"""
Camera system for handling view transformations, zooming, and panning
"""
import pygame
from typing import Tuple


class Camera:
    def __init__(self, screen_width: int, screen_height: int):
        self.x = 0
        self.y = 0  # Camera offset Y
        self.zoom = 1.0  # Zoom level (1.0 = normal, >1.0 = zoomed in, <1.0 = zoomed out)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.dragging = False
        self.last_mouse_pos = (0, 0)
        
        # Zoom limits - allow much more zoom out for bigger map
        self.min_zoom = 0.05
        self.max_zoom = 10.0  # Allow high zoom for detailed viewing
    
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
