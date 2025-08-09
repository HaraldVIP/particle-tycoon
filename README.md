# Particle Tycoon Game

A physics-based tycoon game where you place planets to collect particles and earn money!

## How to Play

1. **Objective**: Collect particles by placing planets that attract them with gravity
2. **Particle Emitter**: The red circle in the center spawns particles continuously
3. **Planets**: Blue circles that attract particles with realistic gravity physics
4. **Money**: Earn $1 for each particle that hits a planet
5. **Upgrades**: Spend money to buy more planets and increase particle spawn rate

## Controls

- **Buy Planet**: Click the green "Buy Planet" button, then click anywhere to place a planet
- **Select Planet**: Click on any placed planet to select it (yellow highlight appears)
- **Upgrade Gravity**: Select a planet, then click "Upgrade Gravity" to increase its gravitational pull
- **Upgrade Spawn Rate**: Click the "Upgrade Spawn" button to increase particles per second
- **Test Money**: Click the yellow "Test +$100" button for quick money (testing purposes)
- **Volume Control**: Drag the volume slider to adjust audio levels
- **ESC**: Cancel planet placement or deselect planets

## Game Mechanics

- **Gravity Physics**: Particles are attracted to planets based on realistic gravity simulation
- **Planet Placement**: Planets cannot be placed too close to the emitter or other planets
- **Progressive Costs**: Planet and upgrade costs increase as you buy more
- **Real-time Stats**: Track your money, particles collected, and active particles

## Installation & Running

1. Install dependencies:
   ```bash
   # If pip is in PATH:
   pip install -r requirements.txt
   
   # If you need to use full Python path (like on your system):
   C:\Python313\python.exe -m pip install -r requirements.txt
   ```

2. Run the game:
   ```bash
   # If python is in PATH:
   python particle_tycoon.py
   
   # If you need to use full Python path:
   C:\Python313\python.exe particle_tycoon.py
   ```

## Requirements

- Python 3.7+ (tested with Python 3.13)
- pygame 2.6.0+
- numpy 1.24.3+

## Game Features

- ✅ Realistic gravity physics simulation
- ✅ Particle emitter with configurable spawn rate and sound effects
- ✅ Planet placement system with collision detection
- ✅ Money system based on particle collection
- ✅ Progressive upgrade system
- ✅ Real-time game statistics
- ✅ Intuitive UI and controls
- ✅ Visual feedback for planet placement

### Enhanced Features
- 🔊 **Dynamic Audio System**: 
  - Particle spawn sounds with random pitches (200-800 Hz)
  - Procedural ambient background music
  - Volume slider for audio control
- 🌟 **Particle Visual Effects**: 
  - Colorful particles with 8 different random colors
  - Glowing aura effects around each particle
  - Trailing effects that fade over time
- 🌍 **Planetary System**: 
  - Smaller, more strategic planet placement (radius 20 vs 30)
  - **Gravity Upgrades**: Click planets to select and upgrade their gravity strength
  - Visual indicators for upgraded planets (color changes, level display)
  - Air resistance zones around planets (3x planet radius)
  - Resistance decreases with distance from planet
- 🎮 **Improved Gameplay**:
  - **Test Button**: Quick +$100 money for testing features
  - Planet selection system with visual highlighting
  - Progressive upgrade costs for balanced gameplay
  - Reduced planet costs (40 vs 50) for smaller planets
- ⚡ **Pure Physics**: Particles only slow down from gravity and air resistance

Enjoy building your particle collection empire!
