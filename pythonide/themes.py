"""Colour themes. Every colour the IDE uses comes from here.

To add a theme, copy one of the dictionaries below, change the colours and
add it to THEMES. "bold_code" makes all code bold (easier to read on a
projector), "min_font" is the smallest code text size the theme uses and
"text_boost" makes the error help and Variables panel text bigger.
"""

LIGHT = {
    "label": "Light",
    "bold_code": False,
    "min_font": 0,
    "text_boost": 0,
    # editor
    "bg": "#ffffff", "fg": "#1e1e1e", "cursor": "#000000",
    "gutter_bg": "#f0f0f0", "gutter_fg": "#8a8a8a", "gutter_mark_fg": "#000000",
    "current_line": "#f5f9ff", "select": "#cce4ff",
    "keyword": "#0000cc", "builtin": "#8a2be2", "string": "#067d17",
    "comment": "#8c8c8c", "number": "#c45200", "defname": "#0b6e99",
    "step_line": "#fff3a0", "error_line": "#ffd6d6", "error_line_fg": "#b00000",
    # window
    "toolbar": "#e8eef5", "panel": "#ffffff", "header": "#dfe6ee", "header_active": "#cfd8e3",
    "sash": "#c9d3df", "text": "#1e1e1e", "muted": "#666666", "status_bg": "#f3f3f3",
    "button": "#ffffff", "button_active": "#dde7f3", "button_disabled": "#aab4bf",
    "entry": "#ffffff", "entry_disabled": "#eeeeee", "input_wait": "#fff59d",
    "run": "#2e7d32", "stop": "#c62828", "step": "#1565c0",
    # output
    "out_bg": "#fbfbfb", "out_fg": "#1e1e1e", "stderr": "#b00000", "typed": "#1565c0",
    "info": "#777777", "err_title": "#b00000", "err_text": "#3a3a3a", "hint": "#1b5e20",
    "tech": "#888888",
    # variables
    "changed": "#c8f7c5", "heading": "#1565c0",
}

DARK = dict(LIGHT, **{
    "label": "Dark",
    "bg": "#1e1e1e", "fg": "#d4d4d4", "cursor": "#ffffff",
    "gutter_bg": "#1e1e1e", "gutter_fg": "#858585", "gutter_mark_fg": "#ffffff",
    "current_line": "#2a2d2e", "select": "#264f78",
    "keyword": "#569cd6", "builtin": "#c586c0", "string": "#ce9178",
    "comment": "#6a9955", "number": "#b5cea8", "defname": "#dcdcaa",
    "step_line": "#5e5000", "error_line": "#5c1e1e", "error_line_fg": "#ff8a80",
    "toolbar": "#333333", "panel": "#252526", "header": "#2d2d30", "header_active": "#3e3e42",
    "sash": "#3c3c3c", "text": "#e0e0e0", "muted": "#a0a0a0", "status_bg": "#007acc",
    "button": "#3c3c3c", "button_active": "#505050", "button_disabled": "#4d545b",
    "entry": "#3c3c3c", "entry_disabled": "#2b2b2b", "input_wait": "#6b5d00",
    "out_bg": "#1b1b1b", "out_fg": "#d4d4d4", "stderr": "#f48771", "typed": "#4fc1ff",
    "info": "#8a8a8a", "err_title": "#ff6b6b", "err_text": "#dddddd", "hint": "#89d185",
    "tech": "#8a8a8a",
    "changed": "#2e5e2e", "heading": "#4fc1ff",
})

# High contrast for projectors: pure black, bold text on white and strong
# colours, because projectors wash out pale colours and thin lines.
PROJECTOR = dict(LIGHT, **{
    "label": "Projector (high contrast)",
    "bold_code": True,
    "min_font": 18,
    "text_boost": 3,
    "bg": "#ffffff", "fg": "#000000",
    "gutter_bg": "#e6e6e6", "gutter_fg": "#333333",
    "current_line": "#eaf2ff", "select": "#99c9ff",
    "keyword": "#0000c8", "builtin": "#7000a8", "string": "#006000",
    "comment": "#505050", "number": "#b03c00", "defname": "#00489a",
    "step_line": "#ffe033", "error_line": "#ffb0b0", "error_line_fg": "#a00000",
    "toolbar": "#d5dfeb", "header": "#c4d3e6", "header_active": "#b0c4dc",
    "sash": "#8fa3ba", "text": "#000000", "muted": "#333333", "status_bg": "#e0e0e0",
    "button_disabled": "#9aa5b1", "input_wait": "#ffeb3b",
    "out_bg": "#ffffff", "out_fg": "#000000", "stderr": "#a00000", "typed": "#0030c0",
    "info": "#444444", "err_title": "#b00000", "err_text": "#000000", "hint": "#005000",
    "tech": "#444444",
    "changed": "#90e090",
})

THEMES = {"light": LIGHT, "dark": DARK, "projector": PROJECTOR}
DEFAULT = "light"


def get(name):
    return THEMES.get(name, THEMES[DEFAULT])
