#!/usr/bin/env python3
# main.py  —  Entry point for Hostel Management System

import tkinter as tk
import sys, os

# Make sure imports resolve from project root
sys.path.insert(0, os.path.dirname(__file__))

from core import database as db
from core.theme import *
from components.sidebar import Sidebar

# ── Page imports ──────────────────────────────────────────────────────────────
from pages.dashboard  import DashboardPage
from pages.hostels    import HostelsPage
from pages.rooms      import RoomsPage
from pages.students   import StudentsPage
from pages.fees       import FeesPage
from pages.complaints import ComplaintsPage
from pages.visitors   import VisitorsPage
from pages.notices    import NoticesPage
from pages.reports    import ReportsPage


PAGE_MAP = {
    "dashboard":   DashboardPage,
    "hostels":     HostelsPage,
    "rooms":       RoomsPage,
    "students":    StudentsPage,
    "fees":        FeesPage,
    "complaints":  ComplaintsPage,
    "visitors":    VisitorsPage,
    "notices":     NoticesPage,
    "reports":     ReportsPage,
}


class HostelApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HostelPro — College Hostel Management System")
        self.geometry("1320x800")
        self.minsize(1100, 680)
        self.configure(bg=BG)

        # ── Try to set a nice window icon ──
        try:
            self.iconbitmap("")
        except Exception:
            pass

        # ── Load data ──────────────────────────────────────────────────────
        self.data = db.load()

        # ── Layout ─────────────────────────────────────────────────────────
        self._sidebar = Sidebar(self, on_navigate=self._navigate)
        self._sidebar.pack(side="left", fill="y")

        # Top bar (breadcrumb)
        self._topbar = tk.Frame(self, bg=PANEL, height=42)
        self._topbar.pack(side="top", fill="x")
        self._topbar.pack_propagate(False)
        self._page_label = tk.Label(self._topbar, text="Dashboard",
                                     bg=PANEL, fg=SUBTEXT, font=FONT_SMALL,
                                     padx=20)
        self._page_label.pack(side="left", pady=10)
        tk.Label(self._topbar, text="HostelPro  •  College Hostel Management",
                 bg=PANEL, fg=DIM, font=FONT_SMALL).pack(side="right", padx=20)

        # Content area
        self._content = tk.Frame(self, bg=BG)
        self._content.pack(side="left", fill="both", expand=True)

        # ── Instantiate all pages ──────────────────────────────────────────
        self._pages: dict[str, tk.Frame] = {}
        for key, cls in PAGE_MAP.items():
            page = cls(self._content, self)
            self._pages[key] = page
            page.place(relwidth=1, relheight=1)

        # ── Start on dashboard ─────────────────────────────────────────────
        self._navigate("dashboard")

    def _navigate(self, key: str):
        page = self._pages.get(key)
        if page:
            page.refresh()
            page.lift()
        label = key.replace("_", " ").title()
        self._page_label.config(text=f"  /  {label}")
        # Re-trigger sidebar highlight (already handled in sidebar itself)

    def reload_data(self):
        """Call this if any page modifies and saves data externally."""
        self.data = db.load()


if __name__ == "__main__":
    app = HostelApp()
    app.mainloop()
