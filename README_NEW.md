# Particle Tycoon - Modular Version

A physics-based tycoon game where you place planets to collect particles and earn money!

## 🚀 Quick Start

### Option 1: Run the original (while we refactor)
```bash
python particle_tycoon.py
```

### Option 2: Run the new modular version (coming soon)
```bash
python main.py
```

## 📁 Project Structure

```
particle_tycoon/
├── main.py                    # 🎯 Simple entry point - run this!
├── particle_tycoon.py         # 💾 Original game (backup/fallback)
├── requirements.txt           # 📦 Enhanced dependencies with asset libraries
├── .gitignore                # 🚫 Git ignore patterns
├── 
├── config/                   # ⚙️ Game configuration
│   ├── constants.py          # 🎨 Colors, sizes, costs
│   └── settings.py           # 🔧 Game settings (coming soon)
├── 
├── entities/                 # 🎮 Game objects
│   ├── particle.py           # ✨ Particle physics
│   ├── planet.py             # 🪐 Planets and dwarf planets
│   ├── emitter.py            # 🌟 Particle spawning
│   ├── spawner.py            # 📍 Additional spawn points
│   └── wall.py               # 🧱 Collision walls
├── 
├── systems/                  # 🔧 Game systems
│   ├── audio.py              # 🔊 Sound generation
│   ├── assets.py             # 🖼️ Asset loading with online textures
│   ├── camera.py             # 📷 Camera controls
│   └── physics.py            # ⚡ Physics utilities
├── 
├── ui/                       # 🖥️ User interface
│   ├── components.py         # 🎛️ Sliders, selectors
│   ├── effects.py            # ✨ Money popups, light rays
│   └── hud.py                # 📊 Game UI
├── 
├── graphics/                 # 🎨 Rendering
│   ├── background.py         # 🌌 Starfield, backgrounds
│   └── rendering.py          # 🖌️ Render utilities
├── 
├── core/                     # 🧠 Core game logic
│   └── game.py               # 🎮 Main game class
└── 
└── assets/                   # 🎭 Game assets
    ├── cache/                # 📁 Downloaded textures cache
    ├── music/                # 🎵 Background music
    └── Backround.png         # 🖼️ Original background
```

## 🛠️ Setup Instructions

### 1. Install Dependencies
```bash
# Install enhanced requirements
pip install -r requirements.txt

# Or with full Python path:
C:\Python313\python.exe -m pip install -r requirements.txt
```

### 2. Set up Git (for backups to GitHub)

#### Install Git:
1. Download from: https://git-scm.com/download/windows
2. Install with default settings
3. Restart your terminal/PowerShell

#### Initialize repository:
```bash
git init
git add .
git commit -m "Initial commit - modular particle tycoon"
```

#### Connect to GitHub:
1. Create a new repository on GitHub.com
2. Copy the repository URL
3. Run:
```bash
git remote add origin https://github.com/YOUR_USERNAME/particle-tycoon.git
git branch -M main
git push -u origin main
```

### 3. Enhanced Features

#### 🖼️ Online Textures
The game now automatically downloads better textures from:
- OpenGameArt.org
- Kenney.nl asset packs
- Other open-source game asset sites

If download fails, it generates procedural textures as fallback.

#### 🎨 Asset Management
```python
from systems.assets import asset_manager

# Load enhanced planet texture
planet_texture = asset_manager.get_image("planet_rocky")

# Load space background
space_bg = asset_manager.get_image("space_background", size=(1920, 1080))
```

## 🎮 How to Play

1. **Objective**: Collect particles by placing planets that attract them with gravity
2. **Controls**: 
   - Left Click & Drag: Move camera
   - Mouse Wheel: Zoom in/out
   - Buy Planet: Click green button, then click to place
   - ESC: Cancel placement or deselect
3. **Upgrades**: Spend money to buy more planets and increase particle spawn rate

## 🔧 Development

### Adding New Features
1. Create new modules in appropriate packages
2. Import what you need from other modules
3. Keep the original `particle_tycoon.py` as reference
4. Test frequently with `python main.py`

### Asset Sources
The game uses these online asset libraries:
- **OpenGameArt**: Free game assets
- **Kenney.nl**: High-quality game assets
- **Procedural Generation**: Fallback textures

### Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes
4. Commit: `git commit -m "Add feature"`
5. Push: `git push origin feature-name`
6. Create a Pull Request

## 🐛 Troubleshooting

### "Git not found"
Install Git from https://git-scm.com/download/windows

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Download failed"
The game will use procedural textures instead. Check your internet connection.

### Performance Issues
The modular structure might be slightly slower during development. The original `particle_tycoon.py` is kept for performance comparison.

## 📝 License

This project is open source. Feel free to modify and distribute!

---
*Made with ❤️ using Python and Pygame*
