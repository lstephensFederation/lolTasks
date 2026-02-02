#!/usr/bin/env python3
import curses
import datetime
import json
import os
import sys
from datetime import timedelta

DATA_DIR = os.path.expanduser('~/.lolTasks')
DATA_FILE = os.path.join(DATA_DIR, 'weekly_tasks.json')

STATES = ['TO-DO', 'PENDING', 'COMPLETED']
STATE_CYCLE_FORWARD = {s: STATES[(i + 1) % 3] for i, s in enumerate(STATES)}
STATE_CYCLE_BACKWARD = {s: STATES[(i - 1) % 3] for i, s in enumerate(STATES)}

# Display symbols (fixed visual width = 4 chars including spaces/brackets)
STATE_SYMBOLS = {
    'TO-DO':     '[ ] ',
    'PENDING':   '[~] ',
    'COMPLETED': '[x] ',
}

# For consistent offset calculation during editing (always 4 chars)
PREFIX_WIDTH = 4

COLORS = {'TO-DO': 1, 'PENDING': 2, 'COMPLETED': 3}

def get_week_key(date):
    y, w, _ = date.isocalendar()
    return f"{y}-W{w:02d}"

def week_to_date(year, week):
    d = datetime.date(year, 1, 4)
    d -= timedelta(days=d.isocalendar()[2] - 1)
    return d + timedelta(weeks=week - 1)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_input(stdscr, base_y, base_x, initial='', start_at_beginning=False):
    """Safer line editor with cursor movement + vim-style start support + undo/redo + word navigation"""
    curses.curs_set(1)
    stdscr.keypad(True)
    s = list(initial)
    pos = 0 if start_at_beginning else len(s)

    # Undo/redo history
    history = [''.join(s)]
    history_pos = 0

    _, max_x = stdscr.getmaxyx()
    display_width = max_x - base_x - 2  # margin

    def save_state():
        nonlocal history, history_pos
        current = ''.join(s)
        # Remove any history after current position
        history = history[:history_pos + 1]
        history.append(current)
        history_pos = len(history) - 1
        # Limit history to 50 entries
        if len(history) > 50:
            history.pop(0)
            history_pos -= 1

    def undo():
        nonlocal s, pos, history_pos
        if history_pos > 0:
            history_pos -= 1
            s = list(history[history_pos])
            pos = min(pos, len(s))

    def redo():
        nonlocal s, pos, history_pos
        if history_pos < len(history) - 1:
            history_pos += 1
            s = list(history[history_pos])
            pos = min(pos, len(s))

    def skip_word_left():
        nonlocal pos
        # Skip whitespace
        while pos > 0 and s[pos - 1].isspace():
            pos -= 1
        # Skip word
        while pos > 0 and not s[pos - 1].isspace():
            pos -= 1

    def skip_word_right():
        nonlocal pos
        # Skip word
        while pos < len(s) and not s[pos].isspace():
            pos += 1
        # Skip whitespace
        while pos < len(s) and s[pos].isspace():
            pos += 1

    while True:
        start = max(0, pos - display_width + 5)
        visible = s[start:start + display_width]
        visible_str = ''.join(visible)

        try:
            stdscr.move(base_y, base_x)
            stdscr.clrtoeol()
            stdscr.addstr(base_y, base_x, visible_str)
        except curses.error:
            pass  # Skip if can't draw
        try:
            cursor_x = base_x + (pos - start)
            stdscr.move(base_y, cursor_x)
        except curses.error:
            pass
        stdscr.refresh()

        key = stdscr.getkey()

        if key == '\n':
            break
        elif key == '\x01':  # Ctrl+A - jump to start of line
            pos = 0
        elif key == '\x05':  # Ctrl+E - jump to end of line
            pos = len(s)
        elif key == '\x1b':  # Escape key or start of escape sequence
            # Check for escape sequences
            stdscr.nodelay(True)
            try:
                next_key = stdscr.getkey()
                if next_key == 'u':  # Esc + U = undo (vim-style)
                    undo()
                elif next_key == 'r':  # Esc + R = redo (vim-style)
                    redo()
                elif next_key == 'b':  # Option + Left on macOS (\x1bb)
                    skip_word_left()
                elif next_key == 'f':  # Option + Right on macOS (\x1bf)
                    skip_word_right()
                elif next_key == '[':  # CSI sequences
                    seq = stdscr.getkey()
                    if seq == 'D':  # Left arrow
                        pos = max(0, pos - 1)
                    elif seq == 'C':  # Right arrow
                        pos = min(len(s), pos + 1)
                    elif seq == '1':  # \x1b[1~ (Home) or \x1b[1;9D (Option+Left)
                        next_char = stdscr.getkey()
                        if next_char == '~':  # \x1b[1~ - Home
                            pos = 0
                        elif next_char == ';':  # \x1b[1;9D - Option+Left
                            modifier = stdscr.getkey()
                            direction = stdscr.getkey()
                            if modifier == '9' and direction == 'D':
                                skip_word_left()
                    elif seq == '4':  # \x1b[4~ (End)
                        next_char = stdscr.getkey()
                        if next_char == '~':
                            pos = len(s)
                    elif seq == '7':  # \x1b[7~ (Home on some terminals)
                        next_char = stdscr.getkey()
                        if next_char == '~':
                            pos = 0
                    elif seq == '8':  # \x1b[8~ (End on some terminals)
                        next_char = stdscr.getkey()
                        if next_char == '~':
                            pos = len(s)
                    else:
                        # Unknown CSI sequence
                        pass
                else:
                    # Single escape - exit edit mode
                    break
            except curses.error:
                # Timeout or no more keys - treat as single escape
                break
            finally:
                stdscr.nodelay(False)
        elif key in ('KEY_LEFT', 'KEY_BACKSPACE', '\x7f', '\b'):
            save_state()
            if pos > 0:
                pos -= 1
                if key in ('\x7f', '\b'):
                    del s[pos]
        elif key == 'KEY_RIGHT':
            if pos < len(s):
                pos += 1
        elif key == 'KEY_HOME':
            pos = 0
        elif key == 'KEY_END':
            pos = len(s)
        elif key == 'KEY_DC':
            save_state()
            if pos < len(s):
                del s[pos]
        elif len(key) == 1 and 32 <= ord(key) <= 126:
            save_state()
            s.insert(pos, key)
            pos += 1

    curses.curs_set(0)
    return ''.join(s)

def show_help():
    print("Weekly Tasks App - task")
    print("Keys:")
    print("  ↑↓/kj     Move selection / Reorder (when in reorder mode)")
    print("  r         Toggle reorder mode")
    print("  ←→/hl     Prev/Next week")
    print("  Tab       Cycle state forward")
    print("  Shift+Tab Cycle state backward")
    print("  I         Edit current item at start of line (vim-style I)")
    print("  a         Add new task after selected")
    print("  Enter     Edit selected item (cursor at end)")
    print("  d         Delete selected task")
    print("  n / p     Shift task next / prev week")
    print("  Ctrl+U     Undo last action")
    print("  Ctrl+R     Redo last undone action")
    print("  q         Quit")
    print()
    print("In edit mode:")
    print("  Esc       Exit edit mode")
    print("  Esc+u     Undo (vim-style)")
    print("  Esc+r     Redo (vim-style)")
    print("  Option+←→ Word navigation")
    print("  Ctrl+A/E  Line navigation (start/end)")
    print("  Arrow keys Cursor movement")
    sys.exit(0)

def main(stdscr):
    if len(sys.argv) > 1 and sys.argv[1] in ('--help', '-h'):
        show_help()

    curses.curs_set(0)
    stdscr.keypad(True)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)

    today = datetime.date.today()
    current_week = get_week_key(today)

    active_week = current_week
    selected = -1
    edit_mode = False
    reorder_mode = False
    scroll_offset = 0
    force_start = False

    # Global undo/redo history
    undo_history = []
    undo_pos = -1
    MAX_UNDO = 20

    # Save initial state
    initial_data = load_data()
    undo_history.append(json.dumps(initial_data))
    undo_pos = 0

    def save_undo_state():
        nonlocal undo_history, undo_pos
        # Save current in-memory data, not from disk
        current_data = data.copy()
        # Remove any history after current position
        undo_history = undo_history[:undo_pos + 1]
        undo_history.append(json.dumps(current_data))
        undo_pos = len(undo_history) - 1
        # Limit history
        if len(undo_history) > MAX_UNDO:
            undo_history.pop(0)
            undo_pos -= 1

    def undo():
        nonlocal undo_history, undo_pos, selected, active, prev, nxt, data
        if undo_pos > 0:
            undo_pos -= 1
            restored_data = json.loads(undo_history[undo_pos])
            save_data(restored_data)
            # Reload data immediately
            data = load_data()
            active = data[active_week]
            nxt = data[next_week]
            prev = data[prev_week]
            # Adjust selected index
            selected = max(-1, min(selected, len(active['tasks']) - 1))
            return True
        return False

    def redo():
        nonlocal undo_history, undo_pos, selected, active, prev, nxt, data
        if undo_pos < len(undo_history) - 1:
            undo_pos += 1
            restored_data = json.loads(undo_history[undo_pos])
            save_data(restored_data)
            # Reload data immediately
            data = load_data()
            active = data[active_week]
            nxt = data[next_week]
            prev = data[prev_week]
            # Adjust selected index
            selected = max(-1, min(selected, len(active['tasks']) - 1))
            return True
        return False

    while True:
        data = load_data()

        if active_week not in data:
            data[active_week] = {'title': 'Editable Title here for the week', 'tasks': []}
            save_data(data)

        stdscr.clear()
        maxy, maxx = stdscr.getmaxyx()

        y, w_part = active_week.split('-W')
        y = int(y)
        w = int(w_part)
        active_date = week_to_date(y, w)
        prev_date = active_date - timedelta(weeks=1)
        next_date = active_date + timedelta(weeks=1)
        prev_week = get_week_key(prev_date)
        next_week = get_week_key(next_date)

        for wk in [prev_week, active_week, next_week]:
            if wk not in data:
                data[wk] = {'title': 'Week title', 'tasks': []}
                save_data(data)

        prev = data[prev_week]
        active = data[active_week]
        nxt = data[next_week]

        selected = max(-1, min(selected, len(active['tasks']) - 1))

        # Layout positions - ensure active title is always visible
        title_y = 0
        prev_start_y = 2
        prev_end_y = 6  # Previous week: title at 0, sep at 1, tasks at 2-5 (max 4 tasks)
        active_title_y = prev_end_y + 1  # Title at line 7
        active_start_y = active_title_y + 2  # Tasks start at line 9
        next_start_y = maxy - 12 if maxy > 35 else active_start_y + 12

        # Adjust scroll_offset to make selected visible
        if selected >= 0:
            visible_rows = next_start_y - active_start_y - 1
            if selected < scroll_offset:
                scroll_offset = selected
            elif selected > scroll_offset + visible_rows - 1:
                scroll_offset = selected - (visible_rows - 1)
            scroll_offset = max(0, scroll_offset)

        # Titles & separators
        def draw_title(y, week_key, text, attr=curses.A_NORMAL):
            if y >= maxy: return  # Skip if beyond screen
            label = f"{week_key} – {text}"
            if len(label) > maxx - 6:
                label = label[:maxx-9] + "..."
            stdscr.addstr(y, 2, label, attr)

        draw_title(title_y, prev_week, prev['title'], curses.A_DIM)
        if title_y + 1 < maxy:
            stdscr.addstr(title_y + 1, 0, "─" * (maxx - 2), curses.A_DIM)

        draw_title(active_title_y, active_week, active['title'], curses.A_BOLD)
        if active_title_y + 1 < maxy:
            stdscr.addstr(active_title_y + 1, 0, "═" * (maxx - 2), curses.A_BOLD)

        draw_title(next_start_y - 2, next_week, nxt['title'], curses.A_DIM)
        if next_start_y - 1 < maxy:
            stdscr.addstr(next_start_y - 1, 0, "─" * (maxx - 2), curses.A_DIM)

        # Improved tasks drawing with word-wrap for selected
        def draw_week_tasks(base_y, week_data, is_active, sel_idx=-1, max_tasks=8, scroll_offset=0, max_y=None):
            if max_y is None:
                max_y = maxy
            max_y = min(max_y, maxy - 2)  # Leave room for help bar at maxy-1
            tasks = week_data['tasks']
            y = base_y
            wrap_width = maxx - 16  # margin for prefix + indent

            start_idx = scroll_offset if is_active else 0
            end_idx = len(tasks)
            if max_tasks is not None:
                end_idx = min(end_idx, start_idx + max_tasks)

            idx = start_idx
            while idx < end_idx and y < max_y:
                t = tasks[idx]
                prefix = STATE_SYMBOLS[t['state']]           # always 4 chars
                text = t['text']
                attr = curses.color_pair(COLORS.get(t['state'], 1))
                if is_active and idx == sel_idx:
                    attr |= curses.A_REVERSE
                if not is_active:
                    attr |= curses.A_DIM

                full = prefix + text
                if is_active and idx == sel_idx and len(full) > wrap_width:
                    lines = []
                    rem = full
                    while rem:
                        if len(rem) <= wrap_width:
                            lines.append(rem)
                            break
                        split = rem.rfind(' ', 0, wrap_width)
                        if split == -1:
                            split = wrap_width
                        lines.append(rem[:split])
                        rem = rem[split:].lstrip()
                        if rem:
                            rem = ' ' * PREFIX_WIDTH + rem
                    for line in lines:
                        if y >= max_y: break
                        try:
                            stdscr.addstr(y, 2, line, attr)
                        except curses.error:
                            pass
                        y += 1
                else:
                    if len(full) > wrap_width + 5:
                        full = full[:wrap_width - 3] + "..."
                    if y < max_y:
                        try:
                            stdscr.addstr(y, 2, full, attr)
                        except curses.error:
                            pass
                    y += 1

                idx += 1

            if idx < len(tasks) and y < max_y:
                stdscr.addstr(y, 2, "... more", curses.A_DIM)

        draw_week_tasks(prev_start_y, prev, False, max_tasks=4, max_y=active_title_y - 1)
        draw_week_tasks(active_start_y, active, True, selected, max_tasks=None, scroll_offset=scroll_offset, max_y=next_start_y - 2)
        draw_week_tasks(next_start_y, nxt, False, max_tasks=8, max_y=maxy - 1)

        # Help bar
        mode = " [REORDER]" if reorder_mode else ""
        hint = " (after selected)" if 0 <= selected < len(active['tasks']) else " (at end)"
        help_txt = f"↑↓/kj:Move{'/Reorder'+mode} | r:Reorder | ←→:Week | Tab/S-Tab:State | I:Edit@start | a:Add{hint} | ⏎:Edit | d:Del | n/p:Shift | Ctrl+U:Undo | Ctrl+R:Redo | q:Quit"
        if maxy - 1 < maxy:
            stdscr.addstr(maxy - 1, 0, help_txt[:maxx - 1], curses.A_DIM)

        stdscr.refresh()

        if edit_mode:
            if selected == -1:
                offset = len(f"{active_week} – ")
                new_title = get_input(stdscr, active_title_y, 2 + offset,
                                      active['title'], start_at_beginning=force_start)
                active['title'] = new_title
            else:
                t = active['tasks'][selected]
                offset = PREFIX_WIDTH                               # ← Fixed!
                edit_y = active_start_y + (selected - scroll_offset)
                new_text = get_input(stdscr, edit_y, 2 + offset,
                                     t['text'], start_at_beginning=force_start)
                t['text'] = new_text
            save_data(data)
            edit_mode = False
            force_start = False
            continue

        key = stdscr.getkey()
        force_start = False

        # Handle control key sequences
        if key == '\x15':  # Ctrl+U = undo
            if undo():
                continue
        elif key == '\x12':  # Ctrl+R = redo
            if redo():
                continue

        # Normal mode commands
        if key.lower() == 'q':
            save_data(data)
            break
        elif key.lower() == 'r':
            reorder_mode = not reorder_mode
        elif key == '\t' and 0 <= selected < len(active['tasks']):
            active['tasks'][selected]['state'] = STATE_CYCLE_FORWARD[active['tasks'][selected]['state']]
            save_data(data)
            save_undo_state()
        elif key == '\x1b[Z' and 0 <= selected < len(active['tasks']):
            active['tasks'][selected]['state'] = STATE_CYCLE_BACKWARD[active['tasks'][selected]['state']]
            save_data(data)
            save_undo_state()
        elif key == 'I':  # Shift+I - edit at start
            if selected == -1 or 0 <= selected < len(active['tasks']):
                edit_mode = True
                force_start = True
        elif key in ('KEY_UP', 'k'):
            tasks = active['tasks']
            if reorder_mode:
                if selected > 0:
                    tasks[selected-1], tasks[selected] = tasks[selected], tasks[selected-1]
                    selected -= 1
                    save_data(data)
                    save_undo_state()
            else:
                if selected > 0:
                    selected -= 1
                elif selected == -1 and tasks:
                    selected = len(tasks) - 1
        elif key in ('KEY_DOWN', 'j'):
            tasks = active['tasks']
            if reorder_mode:
                if selected < len(tasks) - 1:
                    tasks[selected+1], tasks[selected] = tasks[selected], tasks[selected+1]
                    selected += 1
                    save_data(data)
                    save_undo_state()
            else:
                if selected == -1 and tasks:
                    selected = 0
                elif selected < len(tasks) - 1:
                    selected += 1
                elif selected == len(tasks) - 1:
                    selected = -1
        elif key in ('KEY_LEFT', 'h'):
            active_week = prev_week
            selected = -1
            scroll_offset = 0
        elif key in ('KEY_RIGHT', 'l'):
            active_week = next_week
            selected = -1
            scroll_offset = 0
        elif key.lower() == 'a':
            tasks = active['tasks']
            new_task = {'text': 'New task', 'state': 'TO-DO'}
            if selected == -1 or selected >= len(tasks):
                tasks.append(new_task)
                selected = len(tasks) - 1
            else:
                pos = selected + 1
                tasks.insert(pos, new_task)
                selected = pos
            save_data(data)
            save_undo_state()
            edit_mode = True
            force_start = False
        elif key == '\n' and selected is not None:
            edit_mode = True
            force_start = False
        elif key.lower() == 'd' and 0 <= selected < len(active['tasks']):
            del active['tasks'][selected]
            selected = max(-1, selected - 1)
            save_data(data)
            save_undo_state()
        elif key.lower() in ('n', 'p') and 0 <= selected < len(active['tasks']):
            tasks = active['tasks']
            task = tasks.pop(selected)
            delta = 1 if key.lower() == 'n' else -1
            target_date = active_date + timedelta(weeks=delta)
            target_week = get_week_key(target_date)
            if target_week not in data:
                data[target_week] = {'title': 'Week title', 'tasks': []}
            data[target_week]['tasks'].append(task)
            selected = max(-1, min(selected, len(tasks) - 1))
            save_data(data)
            save_undo_state()

if __name__ == '__main__':
    curses.wrapper(main)
