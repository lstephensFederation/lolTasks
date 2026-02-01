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
    """Safer line editor with cursor movement + vim-style start support"""
    curses.curs_set(1)
    stdscr.keypad(True)
    s = list(initial)
    pos = 0 if start_at_beginning else len(s)

    _, max_x = stdscr.getmaxyx()
    display_width = max_x - base_x - 2  # margin

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
        elif key == '\x1b':  # Escape key
            break
        elif key in ('KEY_LEFT', 'KEY_BACKSPACE', '\x7f', '\b'):
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
            if pos < len(s):
                del s[pos]
        elif len(key) == 1 and 32 <= ord(key) <= 126:
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
    print("  q         Quit")
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
        help_txt = f"↑↓/kj:Move{'/Reorder'+mode} | r:Reorder | ←→:Week | Tab/S-Tab:State | I:Edit@start | a:Add{hint} | ⏎:Edit (title if none selected) | d:Del | n/p:Shift | q:Quit"
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

        # Normal mode commands
        if key.lower() == 'q':
            save_data(data)
            break
        elif key.lower() == 'r':
            reorder_mode = not reorder_mode
        elif key == '\t' and 0 <= selected < len(active['tasks']):
            active['tasks'][selected]['state'] = STATE_CYCLE_FORWARD[active['tasks'][selected]['state']]
            save_data(data)
        elif key == '\x1b[Z' and 0 <= selected < len(active['tasks']):
            active['tasks'][selected]['state'] = STATE_CYCLE_BACKWARD[active['tasks'][selected]['state']]
            save_data(data)
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
            edit_mode = True
            force_start = False
        elif key == '\n' and selected is not None:
            edit_mode = True
            force_start = False
        elif key.lower() == 'd' and 0 <= selected < len(active['tasks']):
            del active['tasks'][selected]
            selected = max(-1, selected - 1)
            save_data(data)
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

if __name__ == '__main__':
    curses.wrapper(main)
