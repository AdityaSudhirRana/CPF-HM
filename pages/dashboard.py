# pages/dashboard.py

import tkinter as tk
from datetime import date
from core.theme import *
from core import database as db
from components.widgets import StatCard, Divider, Badge, PageHeader


class DashboardPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        data = self.app.data
        today = date.today().isoformat()

        # ── Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=PAD_PAGE, pady=(PAD_PAGE, 4))
        tk.Label(hdr, text="Dashboard", bg=BG, fg=TEXT, font=FONT_H1).pack(side="left")
        tk.Label(hdr, text=date.today().strftime("  %A, %d %B %Y"),
                 bg=BG, fg=SUBTEXT, font=FONT_BODY).pack(side="left", anchor="s", pady=5)
        Divider(self, pady=6)

        # ── Stat Cards ───────────────────────────────────────────────────────
        sf = tk.Frame(self, bg=BG)
        sf.pack(fill="x", padx=PAD_PAGE, pady=8)
        for i in range(5):
            sf.columnconfigure(i, weight=1)

        rooms = data["rooms"]
        students = data["students"]
        fees = data["fees"]
        complaints = data["complaints"]

        total_rooms  = len(rooms)
        avail_rooms  = sum(1 for r in rooms if r["status"] == "available")
        occup_rooms  = sum(1 for r in rooms if r["status"] == "occupied")
        maint_rooms  = sum(1 for r in rooms if r["status"] == "maintenance")
        total_stud   = len(students)
        pending_fees = sum(1 for f in fees if f.get("status") == "unpaid")
        open_comp    = sum(1 for c in complaints if c.get("status") == "pending")

        cards_data = [
            ("🏠", "Total Rooms",    total_rooms,  ACCENT2),
            ("✅", "Available",      avail_rooms,  ACCENT),
            ("🔴", "Occupied",       occup_rooms,  ACCENT4),
            ("🎓", "Students",       total_stud,   ACCENT2),
            ("⚠️", "Open Issues",    open_comp,    ACCENT3),
        ]
        for col, (icon, lbl, val, color) in enumerate(cards_data):
            c = StatCard(sf, icon, lbl, val, color)
            c.grid(row=0, column=col, sticky="ew", padx=6)

        # ── Two column layout ────────────────────────────────────────────────
        cols = tk.Frame(self, bg=BG)
        cols.pack(fill="both", expand=True, padx=PAD_PAGE, pady=8)
        cols.columnconfigure(0, weight=3)
        cols.columnconfigure(1, weight=2)

        # Left – Recent students
        left = tk.Frame(cols, bg=CARD, padx=PAD_CARD, pady=PAD_CARD)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(left, text="Recently Admitted Students", bg=CARD, fg=TEXT,
                 font=FONT_H3).pack(anchor="w")
        Divider(left, pady=6)

        headers = ["Name", "Roll No", "Room", "Hostel", "Joined"]
        hrow = tk.Frame(left, bg=PANEL)
        hrow.pack(fill="x", pady=(0, 4))
        widths = [22, 12, 8, 14, 12]
        for h, w in zip(headers, widths):
            tk.Label(hrow, text=h, bg=PANEL, fg=SUBTEXT, font=FONT_SMALL,
                     width=w, anchor="w").pack(side="left", padx=4, pady=4)

        recent = sorted(students, key=lambda s: s.get("join_date",""), reverse=True)[:7]
        for s in recent:
            room = db.get_room(data, s.get("room_id",""))
            hostel = db.get_hostel(data, s.get("hostel_id",""))
            row_f = tk.Frame(left, bg=CARD)
            row_f.pack(fill="x")
            tk.Frame(left, bg=BORDER, height=1).pack(fill="x")
            vals = [s["name"], s["roll"],
                    room["number"] if room else "—",
                    hostel["name"][:14] if hostel else "—",
                    s.get("join_date","—")]
            for v, w in zip(vals, widths):
                tk.Label(row_f, text=str(v)[:w], bg=CARD, fg=TEXT,
                         font=FONT_BODY, width=w, anchor="w").pack(side="left", padx=4, pady=6)

        # Right – Hostel occupancy + notices
        right = tk.Frame(cols, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")

        occ_f = tk.Frame(right, bg=CARD, padx=PAD_CARD, pady=PAD_CARD)
        occ_f.pack(fill="x", pady=(0, 8))
        tk.Label(occ_f, text="Hostel Occupancy", bg=CARD, fg=TEXT, font=FONT_H3).pack(anchor="w")
        Divider(occ_f, pady=6)

        for h in data["hostels"]:
            h_rooms = db.rooms_for_hostel(data, h["id"])
            cap = sum(r["capacity"] for r in h_rooms)
            occ = sum(db.room_occupancy(data, r["id"]) for r in h_rooms)
            pct = int((occ / cap * 100)) if cap else 0

            row_f = tk.Frame(occ_f, bg=CARD)
            row_f.pack(fill="x", pady=4)
            tk.Label(row_f, text=h["name"][:18], bg=CARD, fg=TEXT,
                     font=FONT_BODY, width=18, anchor="w").pack(side="left")
            bar_bg = tk.Frame(row_f, bg=CARD2, height=12, width=100)
            bar_bg.pack(side="left", padx=8)
            bar_bg.pack_propagate(False)
            fill_color = DANGER if pct > 85 else (ACCENT3 if pct > 60 else ACCENT)
            tk.Frame(bar_bg, bg=fill_color, height=12,
                     width=int(pct)).place(x=0, y=0)
            tk.Label(row_f, text=f"{occ}/{cap}", bg=CARD, fg=SUBTEXT,
                     font=FONT_SMALL).pack(side="right")

        notices_f = tk.Frame(right, bg=CARD, padx=PAD_CARD, pady=PAD_CARD)
        notices_f.pack(fill="both", expand=True)
        tk.Label(notices_f, text="Latest Notices", bg=CARD, fg=TEXT, font=FONT_H3).pack(anchor="w")
        Divider(notices_f, pady=6)

        for n in sorted(data["notices"], key=lambda x: x.get("date",""), reverse=True)[:4]:
            nf = tk.Frame(notices_f, bg=CARD2, padx=10, pady=8)
            nf.pack(fill="x", pady=4)
            top = tk.Frame(nf, bg=CARD2)
            top.pack(fill="x")
            tk.Label(top, text=n["title"], bg=CARD2, fg=TEXT,
                     font=("Segoe UI", 10, "bold")).pack(side="left")
            Badge(top, n.get("priority","low")).pack(side="right")
            tk.Label(nf, text=n.get("date",""), bg=CARD2, fg=DIM,
                     font=FONT_SMALL).pack(anchor="w")
