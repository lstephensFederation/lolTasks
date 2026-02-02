# lolTasks

A powerful terminal-based weekly task management application built with Python and curses.

## Features

- **Weekly Task Management**: Organize tasks by week with a clean, intuitive interface
- **Advanced Text Editing**: Full-featured line editor with undo/redo, word navigation, and standard shortcuts
- **Cross-Platform**: Works on macOS, Linux, and Windows (with appropriate terminal)
- **Persistent Storage**: JSON-based data storage in your home directory
- **Vim-Style Shortcuts**: Familiar key bindings for power users

## Installation

### From PyPI (Recommended)
```bash
pip install lolTasks
```

### From Source
```bash
git clone https://github.com/lstephensFederation/lolTasks.git
cd lolTasks
pip install .
```

## Usage

### Basic Usage
```bash
lolTasks
# or
task
```

### Command Line Options
```bash
lolTasks --help  # Show help and key bindings
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
- `Esc`: Exit edit mode

### Global Actions
- `Ctrl + U`: Undo last action
- `Ctrl + R`: Redo last undone action
- `n`: Move task to next week
- `p`: Move task to previous week
- `q`: Quit application

### Text Editing (when in edit mode)
- `Esc + U`: Undo last change (vim-style)
- `Esc + R`: Redo last undone change
- `Option + Left` (macOS): Skip to previous word
- `Option + Right` (macOS): Skip to next word
- `Ctrl + A`: Move to start of line
- `Ctrl + E`: Move to end of line
- `Left/Right`: Move cursor
- `Home/End`: Move to start/end of line
- `Backspace/Delete`: Delete characters
- `Enter/Esc`: Save and exit edit mode

## Data Storage

Tasks are stored in `~/.lolTasks/weekly_tasks.json`. The application automatically creates this directory and file on first run.

## Requirements

- Python 3.6+
- A terminal that supports curses (most modern terminals)

## Development

### Setup Development Environment
```bash
git clone https://github.com/lstephensFederation/lolTasks.git
cd lolTasks
pip install -e .
```

### Running Tests
```bash
# No tests implemented yet
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Changelog

### Version 1.0.0
- Initial release
- Complete task management functionality
- Advanced text editing features
- Cross-platform compatibility
- Comprehensive documentation

## Support

For issues, questions, or contributions, please visit:
https://github.com/lstephensFederation/lolTasks