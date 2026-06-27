# HyDE Wallpaper Manager 🖼️✨

A lightweight, zero-dependency web interface to manage and change wallpapers for the **HyDE** (Hyprland Desktop Environment) active theme. 

Built entirely with Python's native libraries (`http.server`) and vanilla HTML/CSS/JavaScript, requiring **zero package installations**!

---

## Features

* **🔍 Active Theme Auto-Detection:** Automatically detects the current theme from your HyDE configuration files (`wallbash.conf` or `config.toml`).
* **🌟 Active Wallpaper Indicator:** Reads the `wall.set` symlink to visually highlight which wallpaper is currently active.
* **⚡ One-Click Apply:** Applies wallpapers instantly using the official `hyde-shell` tool in the background.
* **📤 Drag & Drop Upload:** Add new wallpapers directly to the current theme's folder by dragging and dropping them into the web view.
* **🗑️ Easy Deletion:** Clean up unwanted wallpapers directly from the web interface.
* **🚀 Zero Dependencies:** Runs out-of-the-box on any Linux distribution with Python 3 and HyDE.

---

## Getting Started

### Prerequisites
Make sure you have **HyDE** installed and configured on your system.

### Running the App
1. Clone this repository (or copy the files) to your system.
2. Make the launcher script executable:
   ```bash
   chmod +x launch.sh
   ```
3. Run the script:
   ```bash
   ./launch.sh
   ```
4. The server will start on port `5050` and automatically open your default browser to `http://localhost:5050`.

---

## File Structure

* `app.py`: Standard Python HTTP server handling API requests for theme statuses, wallpaper listing, uploading, applying, and deleting.
* `index.html`: Sleek modern GUI structure.
* `style.css`: Clean, dark glassmorphic theme styling matching the Hyprland aesthetic.
* `script.js`: Frontend logic for drag-and-drop, API communications, and rendering.
* `launch.sh`: Port checker and execution script.
