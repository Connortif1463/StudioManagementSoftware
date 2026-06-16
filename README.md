# Studio Management System

A comprehensive project management system for music studios, designed to track songs, albums, sessions, and project stages from production to mastering.

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

## Install from GitHub

```bash
git clone https://github.com/yourusername/StudioManagementSoftware.git
cd StudioManagementSoftware

pip install -r requirements.txt

python3 run.py
```

### Dependencies

```pip install
rich>=13.0.0
```

### Starting the Application

```bash
python3 run.py
```

### Project Files Structure

```
artists/
└── Artist Name/
    └── Project Name/
        ├── production/
        │   └── project_production_session.als
        ├── mix/
        │   └── project_mix_session.ptx
        ├── master/
        │   └── project_master_session.ptx
        ├── finished/
        │   └── final_master.wav
        └── .project_tracker.json   # Project metadata
```

## DAW Templates

Place your DAW template files in the `templates/` folder:

- `templates/ableton templates/ableton template.als`
- `templates/protools templates/protools template.ptx`
- `templates/logic templates/logic template.logicx`

When creating a new project, the template will be copied to the appropriate stage folder.
