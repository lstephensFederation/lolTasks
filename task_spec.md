# Weekly Tasks Application Specification

## Overview

The Weekly Tasks application is a terminal-based task management tool built with Python and the curses library. It provides a text-based user interface for managing weekly tasks with different completion states, allowing users to organize and track their tasks across multiple weeks.

## Features

### Core Functionality
- **Weekly Task Management**: Organize tasks by ISO week (YYYY-WW format)
- **Task States**: Three-state system (TO-DO, PENDING, COMPLETED) with visual indicators
- **Multi-Week Navigation**: View and navigate between previous, current, and next weeks
- **Task Operations**: Add, edit, delete, and reorder tasks
- **State Cycling**: Change task states forward and backward
- **Task Movement**: Move tasks between weeks

### User Interface
- **Terminal-Based**: Uses curses for full-screen text interface
- **Color Coding**: Different colors for each task state (Red=TO-DO, Blue=PENDING, Green=COMPLETED)
- **Responsive Layout**: Adapts to terminal size with scrollable task lists
- **Word Wrapping**: Long task descriptions wrap properly for selected items
- **Visual Indicators**: Checkboxes and symbols for task states

## Data Model

### Storage
- **Location**: `~/.lolTasks/weekly_tasks.json`
- **Format**: JSON file with week-based structure

### Structure
```json
{
  "2026-W05": {
    "title": "Week of February 3-9, 2026",
    "tasks": [
      {
        "text": "Complete project documentation",
        "state": "TO-DO"
      },
      {
        "text": "Review code changes",
        "state": "PENDING"
      }
    ]
  }
}
```

### Task States
- **TO-DO**: `[ ] ` - Red color, initial state
- **PENDING**: `[~] ` - Blue color, in-progress state
- **COMPLETED**: `[x] ` - Green color, finished state

## User Interface Layout

```
Previous Week (YYYY-WW – Title)
─────────────────────────────────
[ ] Task 1
[~] Task 2
[x] Task 3

Current Week (YYYY-WW – Title)
═════════════════════════════════
[ ] Selected task (highlighted)
[~] Task 2
[x] Task 3
    ... more

Next Week (YYYY-WW – Title)
─────────────────────────────────
[ ] Task 1
[~] Task 2

↑↓/kj:Move/Reorder | r:Reorder | ←→:Week | Tab/S-Tab:State | I:Edit@start | a:Add | ⏎:Edit | d:Del | n/p:Shift | q:Quit
```

## Key Bindings

### Navigation
- `↑/↓` or `k/j`: Move selection up/down
- `←/→` or `h/l`: Navigate to previous/next week
- `Tab`: Cycle task state forward (TO-DO → PENDING → COMPLETED)
- `Shift+Tab`: Cycle task state backward

### Task Management
- `a`: Add new task after selected item
- `Enter`: Edit selected task (or week title if none selected)
- `I`: Edit task at beginning of line (vim-style)
- `d`: Delete selected task
- `r`: Toggle reorder mode for moving tasks up/down
- `Esc`: Exit edit mode (same as Enter - saves changes)

### Task Movement
- `n`: Move task to next week
- `p`: Move task to previous week

### General
- `q`: Quit application

## File Structure

```
~/.lolTasks/
├── task.py              # Main application script
├── weekly_tasks.json    # Task data storage
├── weekly_tasks.json.backup  # Backup file
└── __pycache__/         # Python bytecode cache
```

## Dependencies

### Required Python Modules
- `curses`: Terminal user interface (built-in on Unix systems)
- `datetime`: Date and time handling (built-in)
- `json`: JSON data serialization (built-in)
- `os`: Operating system interface (built-in)
- `sys`: System-specific parameters (built-in)

### System Requirements
- Unix-like operating system (Linux, macOS)
- Python 3.x
- Terminal with curses support

## Installation and Usage

### Installation
1. Download `task.py` to a directory in PATH
2. Make executable: `chmod +x task.py`
3. Run: `./task.py`

### First Run
- Application creates `~/.lolTasks/` directory automatically
- Initializes with current week data
- Shows help with `--help` or `-h` flag

## Technical Implementation

### Architecture
- **Single File Application**: All code in `task.py`
- **Event-Driven UI**: Main loop processes keyboard input
- **In-Memory Data**: Loads/saves JSON data on operations
- **State Management**: Tracks UI state (selection, modes, scroll)

### Key Functions
- `main()`: Application entry point with curses wrapper
- `get_input()`: Safe line editing with cursor movement
- `draw_week_tasks()`: Render tasks with wrapping and selection
- `load_data()`/`save_data()`: JSON persistence
- `get_week_key()`: ISO week calculation
- `week_to_date()`: Convert week to date

### Error Handling
- Graceful handling of terminal resize
- Safe file operations with directory creation
- Input validation for task operations
- Fallback for drawing operations that exceed screen bounds

## Future Enhancements

Potential features for future versions:
- Task categories/tags
- Due dates within weeks
- Search functionality
- Export to different formats
- Synchronization with external services
- Customizable color schemes
- Keyboard shortcut customization</content>
<parameter name="filePath">/Users/lstephens/.lolTasks/task_spec.md