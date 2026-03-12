# components/sidebar.py  —  Left navigation sidebar

import tkinter as tk
from core.theme import *

NAV_ITEMS = [
    ("dashboard",   "⬛",  "Dashboard"),
    ("hostels",     "🏠",  "Hostels"),
    ("rooms",       "🚪",  "Rooms"),
    ("students",    "🎓",  "Students"),
    ("fees",        "💰",  "Fee Management"),
    ("complaints",  "📢",  "Complaints"),
    ("visitors",    "👥",  "Visitors"),
    ("notices",     "📋",  "Notices"),
    ("reports",     "📊",  "Reports"),
]


class Sidebar(tk.Frame):
    def __init__(self, parent, on_navigate):
        super().__init__(parent, bg=PANEL, width=220)
        self.pack_propagate(False)
        self.on_navigate = on_navigate
        self._active = None
        self._btns = {}
        self._build()

    def _build(self):
        # ── Logo ──
        logo = tk.Frame(self, bg=PANEL)
        logo.pack(fill="x", pady=(24, 8), padx=16)

        circle = tk.Canvas(logo, width=46, height=46, bg=PANEL,
                            highlightthickness=0)
        circle.pack(side="left")
        circle.create_oval(2, 2, 44, 44, fill=ACCENT, outline="")
        circle.create_text(23, 23, text="H", fill=TEXT,
                           font=("Segoe UI", 20, "bold"))

        tk.Label(logo, text="HostelPro", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 15, "bold")).pack(side="left", padx=10)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=16, pady=8)

        tk.Label(self, text="MAIN MENU", bg=PANEL, fg=DIM,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=20, pady=(4, 2))

        # ── Nav buttons ──
        for key, icon, label in NAV_ITEMS:
            btn = _NavButton(self, icon, label,
                             command=lambda k=key: self.navigate(k))
            btn.pack(fill="x", padx=8, pady=1)
            self._btns[key] = btn

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=16, pady=12)

        # ── Footer ──
        tk.Label(self, text="HostelPro  v1.0",
                 bg=PANEL, fg=DIM, font=FONT_SMALL).pack(side="bottom", pady=10)

    def navigate(self, key):
        if self._active:
            self._btns[self._active].set_active(False)
        self._active = key
        self._btns[key].set_active(True)
        self.on_navigate(key)


class _NavButton(tk.Frame):
    def __init__(self, parent, icon, label, command):
        super().__init__(parent, bg=PANEL, cursor="hand2")
        self.command = command
        self.active = False

        self.indicator = tk.Frame(self, bg=PANEL, width=3)
        self.indicator.pack(side="left", fill="y")

        inner = tk.Frame(self, bg=PANEL, pady=9, padx=10)
        inner.pack(side="left", fill="both", expand=True)

        self.icon_lbl = tk.Label(inner, text=icon, bg=PANEL, fg=SUBTEXT,
                                  font=("Segoe UI", 13))
        self.icon_lbl.pack(side="left")
        self.txt_lbl = tk.Label(inner, text=label, bg=PANEL, fg=SUBTEXT,
                                 font=("Segoe UI", 11))
        self.txt_lbl.pack(side="left", padx=10)

        for w in (self, inner, self.icon_lbl, self.txt_lbl):
            w.bind("<Button-1>", lambda e: command())
            w.bind("<Enter>",    self._on_enter)
            w.bind("<Leave>",    self._on_leave)

    def set_active(self, active: bool):
        self.active = active
        fg  = TEXT   if active else SUBTEXT
        bg  = HOVER  if active else PANEL
        ind = ACCENT if active else PANEL
        self.indicator.config(bg=ind)
        for w in (self, self.icon_lbl, self.txt_lbl):
            w.config(bg=bg)
        self.txt_lbl.config(fg=fg, font=("Segoe UI", 11, "bold" if active else "normal"))
        self.icon_lbl.config(fg=ACCENT if active else SUBTEXT)

    def _on_enter(self, e):
        if not self.active:
            for w in (self, self.icon_lbl, self.txt_lbl):
                w.config(bg=HOVER)

    def _on_leave(self, e):
        if not self.active:
            for w in (self, self.icon_lbl, self.txt_lbl):
                w.config(bg=PANEL)
