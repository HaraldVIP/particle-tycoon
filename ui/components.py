"""
UI components like sliders, buttons, and selectors
"""
import pygame
import os
from typing import List
from config.constants import *


class Slider:
    def __init__(self, x: int, y: int, width: int, height: int, min_val: float = 0.0, max_val: float = 1.0, start_val: float = 0.5):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = start_val
        self.dragging = False
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_value(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_value(event.pos[0])
    
    def update_value(self, mouse_x: int):
        relative_x = mouse_x - self.rect.x
        relative_x = max(0, min(self.rect.width, relative_x))
        ratio = relative_x / self.rect.width
        self.value = self.min_val + ratio * (self.max_val - self.min_val)
    
    def draw(self, screen):
        # Draw track
        pygame.draw.rect(screen, GRAY, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        # Draw handle
        handle_x = self.rect.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        handle_rect = pygame.Rect(handle_x - 5, self.rect.y - 2, 10, self.rect.height + 4)
        pygame.draw.rect(screen, LIGHT_GRAY, handle_rect)
        pygame.draw.rect(screen, WHITE, handle_rect, 1)


class MusicSelector:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.display_rect = pygame.Rect(x, y, width, height - 30)
        self.up_button = pygame.Rect(x + width - 25, y, 20, 15)
        self.down_button = pygame.Rect(x + width - 25, y + 15, 20, 15)
        
        # Music tracks
        self.music_files = []
        music_dir = "music"
        if os.path.exists(music_dir):
            for file in os.listdir(music_dir):
                if file.endswith(('.mp3', '.wav', '.ogg')):
                    self.music_files.append(file)
        
        if not self.music_files:
            self.music_files = ["No music files found"]
        
        self.selected_index = 0
        self.playing_index = -1  # Track which song is playing
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.up_button.collidepoint(event.pos) and len(self.music_files) > 1:
                self.selected_index = (self.selected_index - 1) % len(self.music_files)
                return True  # Indicate selection changed
            elif self.down_button.collidepoint(event.pos) and len(self.music_files) > 1:
                self.selected_index = (self.selected_index + 1) % len(self.music_files)
                return True  # Indicate selection changed
        return False
    
    def get_selected_file(self):
        if self.music_files and self.music_files[0] != "No music files found":
            return os.path.join("music", self.music_files[self.selected_index])
        return None
    
    def set_playing(self, index: int):
        self.playing_index = index
    
    def draw(self, screen):
        font = pygame.font.Font(None, 24)
        
        # Draw background
        pygame.draw.rect(screen, DARK_GRAY, self.display_rect)
        pygame.draw.rect(screen, WHITE, self.display_rect, 1)
        
        # Draw up/down buttons
        pygame.draw.rect(screen, GRAY, self.up_button)
        pygame.draw.rect(screen, WHITE, self.up_button, 1)
        pygame.draw.rect(screen, GRAY, self.down_button)
        pygame.draw.rect(screen, WHITE, self.down_button, 1)
        
        # Draw arrows
        up_center = (self.up_button.centerx, self.up_button.centery)
        down_center = (self.down_button.centerx, self.down_button.centery)
        
        # Up arrow
        pygame.draw.polygon(screen, WHITE, [
            (up_center[0], up_center[1] - 5),
            (up_center[0] - 5, up_center[1] + 3),
            (up_center[0] + 5, up_center[1] + 3)
        ])
        
        # Down arrow  
        pygame.draw.polygon(screen, WHITE, [
            (down_center[0], down_center[1] + 5),
            (down_center[0] - 5, down_center[1] - 3),
            (down_center[0] + 5, down_center[1] - 3)
        ])
        
        # Draw current track name (truncated if too long)
        if self.music_files:
            track_name = self.music_files[self.selected_index]
            if track_name.endswith(('.mp3', '.wav', '.ogg')):
                track_name = track_name[:-4]  # Remove extension
            
            # Truncate long names
            if len(track_name) > 15:
                track_name = track_name[:12] + "..."
            
            name_text = font.render(track_name, True, WHITE)
            name_rect = name_text.get_rect()
            name_rect.centery = self.display_rect.centery
            name_rect.x = self.display_rect.x + 5
            
            # Highlight if this is the currently playing track
            if self.selected_index == self.playing_index:
                pygame.draw.rect(screen, YELLOW, self.display_rect, 2)
            screen.blit(name_text, name_rect)
