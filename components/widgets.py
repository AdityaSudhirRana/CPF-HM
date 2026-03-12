# components/widgets.py  —  Reusable UI primitives

import tkinter as tk
from tkinter import ttk
from core.theme import *


# ── Button ─────────────────────────────────────────────────────────────────────
class AppButton(tk.Button):
    def __init__(self, parent, text, command, color=ACCENT, fg=TEXT,
                 width=None, icon="", small=False, **kw):
        font = FONT_SMALL if small else ("Segoe UI", 10, "bold")
        padx, pady = (10, 5) if small else (16, 8)
        label = f"{icon}  {text}" if icon else text
        super().__init__(parent, text=label, command=command,
                         bg=color, fg=fg, font=font,
                         relief="flat", bd=0, cursor="hand2",
                         padx=padx, pady=pady,
                         activebackground=_lighten(color),
                         activeforeground=fg, **kw)
        if width:
            self.config(width=width)
        self.color = color
        self.bind("<Enter>", lambda e: self.config(bg=_lighten(color)))
        self.bind("<Leave>", lambda e: self.config(bg=color))


def _lighten(hex_color):
    try:
        r = min(255, int(hex_color[1:3], 16) + 25)
        g = min(255, int(hex_color[3:5], 16) + 25)
        b = min(255, int(hex_color[5:7], 16) + 25)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color


# ── Section Header ─────────────────────────────────────────────────────────────
class PageHeader(tk.Frame):
    def __init__(self, parent, title, subtitle=""):
        super().__init__(parent, bg=BG)
        tk.Label(self, text=title, bg=BG, fg=TEXT, font=FONT_H1).pack(side="left", anchor="s")
        if subtitle:
            tk.Label(self, text=f"  {subtitle}", bg=BG, fg=SUBTEXT, font=FONT_BODY).pack(side="left", anchor="s", pady=4)

    def add_action(self, text, command, color=ACCENT, icon=""):
        AppButton(self, text, command, color=color, icon=icon).pack(side="right", padx=4)


# ── Divider ────────────────────────────────────────────────────────────────────
class Divider(tk.Frame):
    def __init__(self, parent, pady=8, color=BORDER):
        super().__init__(parent, bg=color, height=1)
        self.pack(fill="x", pady=pady)


# ── Stat Card ──────────────────────────────────────────────────────────────────
class StatCard(tk.Frame):
    def __init__(self, parent, icon, label, value, color=ACCENT, **kw):
        super().__init__(parent, bg=CARD, padx=PAD_CARD, pady=14, **kw)
        top = tk.Frame(self, bg=CARD)
        top.pack(fill="x")
        tk.Label(top, text=icon, bg=CARD, fg=color, font=("Segoe UI", 24)).pack(side="left")
        self._val_lbl = tk.Label(top, text=str(value), bg=CARD, fg=color, font=FONT_NUM)
        self._val_lbl.pack(side="right")
        tk.Label(self, text=label, bg=CARD, fg=SUBTEXT, font=FONT_SMALL).pack(anchor="w")

    def set_value(self, v):
        self._val_lbl.config(text=str(v))


# ── Badge ──────────────────────────────────────────────────────────────────────
STATUS_COLORS = {
    "available":   (ACCENT,   TAG_GREEN),
    "occupied":    (ACCENT2,  TAG_BLUE),
    "maintenance": (ACCENT3,  TAG_AMBER),
    "pending":     (ACCENT3,  TAG_AMBER),
    "resolved":    (ACCENT,   TAG_GREEN),
    "paid":        (ACCENT,   TAG_GREEN),
    "unpaid":      (DANGER,   TAG_RED),
    "partial":     (ACCENT3,  TAG_AMBER),
    "high":        (DANGER,   TAG_RED),
    "medium":      (ACCENT3,  TAG_AMBER),
    "low":         (ACCENT,   TAG_GREEN),
    "boys":        (ACCENT2,  TAG_BLUE),
    "girls":       (ACCENT4,  TAG_PURPLE),
}

class Badge(tk.Label):
    def __init__(self, parent, text, **kw):
        key = text.lower()
        fg, bg = STATUS_COLORS.get(key, (TEXT, CARD2))
        super().__init__(parent, text=f"  {text.capitalize()}  ",
                         bg=bg, fg=fg, font=FONT_BADGE,
                         relief="flat", padx=2, pady=2, **kw)


# ── Scrollable Frame ───────────────────────────────────────────────────────────
class ScrollFrame(tk.Frame):
    def __init__(self, parent, bg=BG, **kw):
        super().__init__(parent, bg=bg, **kw)
        canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = tk.Frame(canvas, bg=bg)
        self.inner.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))


# ── Styled Treeview ────────────────────────────────────────────────────────────
def make_tree(parent, columns, col_widths=None, height=14, style_name="App"):
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(f"{style_name}.Treeview",
                    background=CARD, foreground=TEXT,
                    fieldbackground=CARD, borderwidth=0,
                    rowheight=30, font=FONT_BODY)
    style.configure(f"{style_name}.Treeview.Heading",
                    background=PANEL, foreground=SUBTEXT,
                    font=("Segoe UI", 9, "bold"), relief="flat")
    style.map(f"{style_name}.Treeview",
              background=[("selected", ACCENT2)],
              foreground=[("selected", TEXT)])

    wrap = tk.Frame(parent, bg=CARD)
    tv = ttk.Treeview(wrap, columns=columns, show="headings",
                      style=f"{style_name}.Treeview", height=height)
    sb = ttk.Scrollbar(wrap, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sb.set)
    tv.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    for i, col in enumerate(columns):
        w = col_widths[i] if col_widths else 120
        tv.heading(col, text=col)
        tv.column(col, width=w, anchor="w", minwidth=60)
    return wrap, tv


# ── Form Field ─────────────────────────────────────────────────────────────────
class FormField(tk.Frame):
    def __init__(self, parent, label, default="", required=False, width=30):
        super().__init__(parent, bg=CARD)
        lbl = f"{label} {'*' if required else ''}"
        tk.Label(self, text=lbl, bg=CARD, fg=SUBTEXT, font=FONT_SMALL,
                 anchor="w").pack(fill="x")
        self.var = tk.StringVar(value=str(default))
        self.entry = tk.Entry(self, textvariable=self.var, bg=CARD2, fg=TEXT,
                              font=FONT_BODY, relief="flat", bd=0,
                              insertbackground=TEXT, width=width,
                              highlightthickness=1,
                              highlightbackground=BORDER,
                              highlightcolor=ACCENT2)
        self.entry.pack(fill="x", ipady=6, pady=(2, 0))

    def get(self): return self.var.get().strip()
    def set(self, v): self.var.set(str(v))


class FormDropdown(tk.Frame):
    def __init__(self, parent, label, values, default="", width=28):
        super().__init__(parent, bg=CARD)
        tk.Label(self, text=label, bg=CARD, fg=SUBTEXT, font=FONT_SMALL,
                 anchor="w").pack(fill="x")
        self.var = tk.StringVar(value=default or (values[0] if values else ""))
        style = ttk.Style()
        style.configure("F.TCombobox", fieldbackground=CARD2, background=CARD2,
                        foreground=TEXT, selectbackground=ACCENT2)
        self.combo = ttk.Combobox(self, textvariable=self.var, values=values,
                                  state="readonly", font=FONT_BODY, width=width)
        self.combo.pack(fill="x", ipady=4, pady=(2, 0))

    def get(self): return self.var.get().strip()
    def set(self, v): self.var.set(str(v))


# ── Modal dialog base ──────────────────────────────────────────────────────────
class Modal(tk.Toplevel):
    def __init__(self, parent, title, width=560, height=500):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        # Title bar
        tk.Label(self, text=title, bg=PANEL, fg=TEXT, font=FONT_H2,
                 pady=14).pack(fill="x")
        Divider(self, pady=0)
        # Scrollable body
        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True, padx=20, pady=14)
        # Footer
        self.footer = tk.Frame(self, bg=PANEL, pady=10)
        self.footer.pack(fill="x", side="bottom")

    def add_footer_btn(self, text, cmd, color=ACCENT):
        AppButton(self.footer, text, cmd, color=color).pack(side="right", padx=10)
