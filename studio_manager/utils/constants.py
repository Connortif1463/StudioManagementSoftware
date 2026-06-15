from pathlib import Path

# DAW mapping
DAW_MAP = {
    "P": "Pro Tools",
    "A": "Ableton",
    "L": "Logic"
}

# DAW executable paths (update these for your system)
DAW_PATHS = {
    "P": {
        "name": "Pro Tools",
        "mac": "/Applications/Pro Tools.app",
        "win": r"C:\Program Files\Avid\Pro Tools\ProTools.exe",
        "folder": "protools",
        "ext": ".ptx"
    },
    "A": {
        "name": "Ableton",
        "mac": "/Applications/Ableton Live 11 Suite.app",
        "win": r"C:\ProgramData\Ableton\Live 11 Suite\Program\Ableton Live 11 Suite.exe",
        "folder": "ableton",
        "ext": ".als"
    },
    "L": {
        "name": "Logic",
        "mac": "/Applications/Logic Pro X.app",
        "win": None,
        "folder": "logic",
        "ext": ".logicx"
    }
}

# Project subfolders
PROJECT_SUBFOLDERS = ["production", "mix", "master"]

# Subfolder descriptions
SUBFOLDER_PURPOSES = {
    "production": "Production files, raw recordings, stems, and session files for the production phase.",
    "mix": "Mixing session files, mix bounces, and automation data.",
    "master": "Mastering files, final exports, and mastering session data."
}

# Menu options
MENU_OPTIONS = {
    "1": "Create New Project",
    "2": "Open Existing Project",
    "3": "View File Tree",
    "4": "View Tasks & Statistics",
    "q": "Quit"
}

# File size units
SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB']