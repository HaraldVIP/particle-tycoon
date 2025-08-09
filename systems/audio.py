"""Audio system for generating and playing sounds"""
import pygame
import numpy as np
import random

# Initialize Pygame mixer
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

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
    
    arr = (arr * 32767).astype(np.int16)
    sound = pygame.sndarray.make_sound(arr)
    return sound

def generate_catch_sound():
    """Generate a simple chime sound for particle collection"""
    # Simple chime
    frequency = random.randint(400, 1200)  # Random frequency for variety
    duration = 0.15  # Short duration
    sample_rate = 22050
    frames = int(duration * sample_rate)
    
    # Generate a simple sine wave with harmonics
    arr = np.zeros((frames, 2))
    for i in range(frames):
        # Main tone
        wave = np.sin(2 * np.pi * frequency * i / sample_rate)
        # Add harmonic for richness
        wave += 0.3 * np.sin(2 * np.pi * frequency * 2 * i / sample_rate)
        # Add some fade out to avoid clicks
        fade = 1.0 - (i / frames) ** 1.5
        arr[i] = [wave * fade * 0.08, wave * fade * 0.08]  # Low volume
    
    arr = (arr * 32767).astype(np.int16)
    sound = pygame.sndarray.make_sound(arr)
    return sound

def generate_explosion_sound():
    """Generate a simple noise burst for explosions"""
    # Simple noise burst
    duration = 0.3
    sample_rate = 22050
    frames = int(duration * sample_rate)
    
    # Generate noise
    arr = np.zeros((frames, 2))
    for i in range(frames):
        # White noise with some filtering
        noise = random.uniform(-1, 1)
        # Apply envelope - quick attack, slow decay
        if i < frames * 0.1:  # Attack phase
            envelope = i / (frames * 0.1)
        else:  # Decay phase
            envelope = 1.0 - ((i - frames * 0.1) / (frames * 0.9)) ** 0.5
        
        arr[i] = [noise * envelope * 0.15, noise * envelope * 0.15]  # Low volume
    
    arr = (arr * 32767).astype(np.int16)
    sound = pygame.sndarray.make_sound(arr)
    return sound

def generate_planet_name():
    """Generate a random planet name"""
    prefixes = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Theta", "Nova", "Stellar", "Cosmic"]
    suffixes = ["Prime", "Major", "Minor", "Core", "Edge", "Central", "Outer", "Inner", "Deep", "Far"]
    return f"{random.choice(prefixes)} {random.choice(suffixes)}"
