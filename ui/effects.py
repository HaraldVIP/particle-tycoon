"""UI effects like money popups and light rays"""
import pygame
import math

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
            
        # Convert world position to screen position
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # Calculate end point of the ray
        end_x = screen_x + math.cos(self.angle) * self.length
        end_y = screen_y + math.sin(self.angle) * self.length
        
        # Calculate color with intensity
        alpha = int(255 * self.intensity)
        color = (255, 255, 200, alpha)  # Bright yellow-white
        
        # Create a surface with per-pixel alpha for the line
        temp_surface = pygame.Surface((abs(int(end_x - screen_x)) + 4, abs(int(end_y - screen_y)) + 4), pygame.SRCALPHA)
        
        # Draw the light ray as a thick line with glow effect
        start_pos = (2, 2) if end_x >= screen_x and end_y >= screen_y else (abs(int(end_x - screen_x)) + 2, abs(int(end_y - screen_y)) + 2)
        end_pos = (abs(int(end_x - screen_x)) + 2, abs(int(end_y - screen_y)) + 2) if end_x >= screen_x and end_y >= screen_y else (2, 2)
        
        # Draw multiple lines for glow effect
        for thickness in range(3, 0, -1):
            line_alpha = int(alpha * (0.3 + 0.7 * (4 - thickness) / 3))
            line_color = (255, 255, 200, line_alpha)
            if thickness == 1:
                # Core line
                pygame.draw.line(temp_surface, line_color[:3], start_pos, end_pos, thickness)
            else:
                # Glow layers
                pygame.draw.line(temp_surface, (255, 255, 200, line_alpha // 2), start_pos, end_pos, thickness)
        
        # Blit to screen at correct position
        blit_x = min(screen_x, end_x) - 2
        blit_y = min(screen_y, end_y) - 2
        screen.blit(temp_surface, (blit_x, blit_y), special_flags=pygame.BLEND_ALPHA_SDL2)
