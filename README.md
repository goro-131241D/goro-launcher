# Goro-Launcher

**Goro-Launcher** is a resident launcher that offers hotkey operations and hierarchical menus. It displays an icon in the task tray, allowing you to efficiently launch applications and files. The settings can be easily configured using a YAML file, enabling flexible customization.

## Main Features

- **Resident Launcher**: Goro-Launcher stays in the task tray, allowing you to open the launcher menu at any time.
- **Hotkey Invocation**: You can quickly bring up the launcher using keyboard hotkeys.
- **KeyMap Functionality**: Based on the configured KeyMap, you can instantly open related menus by pressing the corresponding key.
- **Hierarchical Menu**: The menu has a hierarchical structure, allowing you to manage items in an organized way.
- **YAML Configuration**: Menus, hotkeys, and KeyMaps are all configured using human-readable YAML files.

## Installation

Here is how to set up **Goro-Launcher** to start automatically on Windows boot.

### Creating the Executable

1. Use `pyinstaller` to create `goro-launcher.exe` from `goro-launcher.py`.
2. Create a folder and place the following files inside:
   - `goro-launcher.exe`
   - `icon.png`
   - `menu.yaml`
3. Create a shortcut for `goro-launcher.exe` (Right-click > Send to > Desktop (create shortcut)).
4. Move the shortcut created on the desktop to the following folder:
   `"C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"`

After this, **goro-launcher.exe** will automatically start upon boot.

### Running `goro-launcher.py` using Python

In this case, the console window will briefly appear during startup.

1. Install Python.
2. Create a folder and set up a Python virtual environment (`venv`).
3. In the folder, run:python -m pip install -r freeze.txt
This will install the necessary libraries.
4. Create a shortcut for `goro-launcher-run.bat`.
5. Copy the created shortcut to the startup folder.

This will launch **goro-launcher.py** within the activated virtual environment.

## Usage

1. **Task Tray Icon**: Once **Goro-Launcher** is started, an icon will appear in the task tray.
2. **Hotkey Invocation**: Press the configured hotkey to display the menu. The default hotkey is "Ctrl+Alt+N."
3. **Opening Menus with KeyMap**: By pressing the keys defined in the KeyMap, the corresponding menu will automatically open.
Each menu item displays the associated key, and pressing the key will expand the menu.
4. **Menu Hierarchy**: The menu is hierarchically organized, allowing quick access to the necessary functions and applications.

## Configuration File (YAML)

### `menu.yaml` Configuration Options:

- **hot_key**: Manages the hotkey settings.
- **key_map**: Sets the Key Map to associate keys with menus.
- **menu**: Manages the structure and display order of the menu items.

### `menu.yaml` Sample

A sample is provided. The sample file includes instructions on how to register applications, bookmarks for websites, and folders. It also explains how to prepare scripts for applications that require specific conditions for startup.

### System Requirements

The following environment has been tested:

- Windows 10
- Python 3.11.9

### In Case of Issues

Since **Goro-Launcher** operates on `hwnd`, some security software might flag it as an issue. In that case, please configure exceptions in your security software.

### License

GPL v3.0

### Links

Website: [https://goro-bizaid.com](https://goro-bizaid.com)  
X (formerly Twitter): [https://x.com/Goro_bizaid](https://x.com/Goro_bizaid)
