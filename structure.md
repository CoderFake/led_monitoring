led_engine/
    ├── main.py                      # Main entry point
    ├── requirements.txt             # Dependencies
    ├── config/
    │   ├── __init__.py
    │   ├── settings.py             # Engine configuration
    │   └── theme.py                # Theme for the monitor UI
    ├── src/
    │   ├── __init__.py
    │   ├── core/                   # Engine core
    │   │   ├── __init__.py
    │   │   ├── animation_engine.py # LED Animation Playback Engine
    │   │   ├── scene_manager.py    # Scene management
    │   │   ├── led_output.py       # LED output via OSC
    │   │   └── osc_handler.py      # Handles OSC message input
    │   ├── models/                 # Data models
    │   │   ├── __init__.py
    │   │   ├── scene.py           # Scene model
    │   │   ├── effect.py          # Effect model
    │   │   └── segment.py         # Segment model
    │   ├── monitor/               # Monitor UI (view-only)
    │   │   ├── __init__.py
    │   │   ├── monitor_window.py  # Monitor window
    │   │   ├── components/        # Monitor components
    │   │   │   ├── __init__.py
    │   │   │   ├── status_display.py    # Status display
    │   │   │   ├── log_viewer.py        # Log viewer
    │   │   │   └── stats_panel.py       # Statistics panel
    │   │   └── styles/            # Monitor styles
    │   │       ├── __init__.py
    │   │       └── theme_manager.py     # Theme manager
    │   ├── utils/                 # Utilities
    │   │   ├── __init__.py
    │   │   ├── logger.py          # Logging system
    │   │   ├── file_handler.py    # File handler
    │   │   └── performance.py     # Performance monitoring
    │   └── data/                  # Data files
    │       ├── scenes/            # Scene JSON files
    │       │   ├── scene_01.json
    │       │   ├── scene_02.json
    │       │   └── multiple_scenes.json
    │       └── logs/              # Log files
    ├── tests/                     # Unit tests,  API tests
    │   
    └── docs/                      # Documentation
        ├── README.md
        ├── OSC_SPEC.md
        └── MONITORING.md
