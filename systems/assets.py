"""Asset loading and management system with online texture support"""
import pygame
import os
import requests
from pathlib import Path
from typing import Dict, Optional
import hashlib

class AssetManager:
    """Manages loading and caching of game assets"""
    
    def __init__(self, cache_dir: str = "assets/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Asset caches
        self.images: Dict[str, pygame.Surface] = {}
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        
        # Online asset sources
        self.texture_sources = {
            "opengameart": "https://opengameart.org/sites/default/files/",
            "kenney": "https://www.kenney.nl/assets/",
            "itch": "https://img.itch.zone/aW1hZ2UvNDI4ODcvMjA0Mzk0LnBuZw==/original/",
        }
        
        # Predefined good textures (these are known to work and look good)
        self.recommended_textures = {
            "space_background": {
                "url": "https://opengameart.org/sites/default/files/space-background-1.png",
                "local_name": "space_bg.png"
            },
            "planet_rocky": {
                "url": "https://opengameart.org/sites/default/files/planet-1.png", 
                "local_name": "planet_rocky.png"
            },
            "particle_glow": {
                "url": "https://opengameart.org/sites/default/files/particle.png",
                "local_name": "particle.png"
            }
        }
    
    def download_asset(self, url: str, local_path: Path) -> bool:
        """Download an asset from a URL"""
        try:
            print(f"Downloading asset from {url}...")
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'ParticleTycoon/1.0 (Game Asset Loader)'
            })
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Successfully downloaded to {local_path}")
            return True
            
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return False
    
    def get_image(self, name: str, fallback_color: tuple = (128, 128, 128), size: tuple = (64, 64)) -> pygame.Surface:
        """Get an image, downloading if necessary, with fallback to generated texture"""
        if name in self.images:
            return self.images[name]
        
        # Try to load from local cache first
        local_path = self.cache_dir / f"{name}.png"
        if local_path.exists():
            try:
                surface = pygame.image.load(str(local_path)).convert_alpha()
                self.images[name] = surface
                return surface
            except Exception as e:
                print(f"Failed to load cached image {local_path}: {e}")
        
        # Try to download from recommended textures
        if name in self.recommended_textures:
            texture_info = self.recommended_textures[name]
            download_path = self.cache_dir / texture_info["local_name"]
            
            if self.download_asset(texture_info["url"], download_path):
                try:
                    surface = pygame.image.load(str(download_path)).convert_alpha()
                    self.images[name] = surface
                    return surface
                except Exception as e:
                    print(f"Failed to load downloaded image: {e}")
        
        # Fallback: generate a simple texture
        print(f"Generating fallback texture for {name}")
        surface = self.generate_texture(name, fallback_color, size)
        self.images[name] = surface
        return surface
    
    def generate_texture(self, name: str, color: tuple, size: tuple) -> pygame.Surface:
        """Generate a procedural texture as fallback"""
        surface = pygame.Surface(size, pygame.SRCALPHA)
        
        if "planet" in name.lower():
            # Generate a planet-like texture
            self.generate_planet_texture(surface, color)
        elif "particle" in name.lower():
            # Generate a glowing particle texture
            self.generate_particle_texture(surface, color)
        elif "space" in name.lower() or "background" in name.lower():
            # Generate a space background
            self.generate_space_texture(surface, size)
        else:
            # Simple solid color with border
            surface.fill(color)
            pygame.draw.rect(surface, (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50)), surface.get_rect(), 2)
        
        return surface
    
    def generate_planet_texture(self, surface: pygame.Surface, color: tuple):
        """Generate a planet-like texture"""
        size = surface.get_size()
        center = (size[0] // 2, size[1] // 2)
        radius = min(size[0], size[1]) // 2 - 2
        
        # Base circle
        pygame.draw.circle(surface, color, center, radius)
        
        # Add some shading
        darker = (max(0, color[0] - 40), max(0, color[1] - 40), max(0, color[2] - 40))
        pygame.draw.circle(surface, darker, (center[0] + radius//4, center[1] + radius//4), radius//2)
        
        # Add highlight
        lighter = (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40))
        pygame.draw.circle(surface, lighter, (center[0] - radius//3, center[1] - radius//3), radius//4)
    
    def generate_particle_texture(self, surface: pygame.Surface, color: tuple):
        """Generate a glowing particle texture"""
        size = surface.get_size()
        center = (size[0] // 2, size[1] // 2)
        radius = min(size[0], size[1]) // 2
        
        # Create glow effect with multiple circles
        for i in range(radius, 0, -2):
            alpha = int(255 * (radius - i) / radius * 0.8)
            glow_color = (*color, alpha)
            glow_surface = pygame.Surface((i*2, i*2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, glow_color, (i, i), i)
            surface.blit(glow_surface, (center[0] - i, center[1] - i), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def generate_space_texture(self, surface: pygame.Surface, size: tuple):
        """Generate a space background with stars"""
        # Fill with dark space color
        surface.fill((5, 5, 15))
        
        # Add stars
        import random
        random.seed(42)  # Consistent star pattern
        for _ in range(size[0] * size[1] // 1000):  # Density based on size
            x = random.randint(0, size[0] - 1)
            y = random.randint(0, size[1] - 1)
            brightness = random.randint(100, 255)
            star_size = random.choice([1, 1, 1, 2])  # Mostly small stars
            color = (brightness, brightness, brightness)
            pygame.draw.circle(surface, color, (x, y), star_size)
    
    def load_music_files(self, music_dir: str = "music") -> list:
        """Load available music files"""
        music_path = Path(music_dir)
        if not music_path.exists():
            music_path.mkdir(exist_ok=True)
            
        music_files = []
        supported_formats = ['.mp3', '.ogg', '.wav']
        
        for ext in supported_formats:
            music_files.extend(list(music_path.glob(f"*{ext}")))
        
        return [str(f) for f in music_files]
    
    def get_asset_info(self) -> dict:
        """Get information about loaded assets"""
        return {
            "images_loaded": len(self.images),
            "sounds_loaded": len(self.sounds),
            "cache_dir": str(self.cache_dir),
            "cache_size": sum(f.stat().st_size for f in self.cache_dir.rglob('*') if f.is_file())
        }

# Global asset manager instance
asset_manager = AssetManager()
