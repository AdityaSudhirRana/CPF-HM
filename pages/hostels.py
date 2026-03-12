# pages/hostels.py

import tkinter as tk
from tkinter import messagebox
from core.theme import *
from core import database as db
from components.widgets import (AppButton, PageHeader, Divider, Badge,
                                  FormField, FormDropdown, Modal, make_tree)


class HostelsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        data = self.app.data

        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=PAD_PAGE, pady=(PAD_PAGE, 4))
        tk.Label(hdr, text="Hostel Blocks", bg=BG, fg=TEXT, font=FONT_H1).pack(side="left")
        AppButton(hdr, "Add Hostel", lambda: AddHostelModal(self, self.app),
                  color=ACCENT, icon="🏠").pack(side="right")
        Divider(self, pady=6)

        cards_frame = tk.Frame(self, bg=BG)
        cards_frame.pack(fill="both", expand=True, padx=PAD_PAGE, pady=8)
        cards_frame.columnconfigure((0, 1, 2), weight=1)

        for col, h in enumerate(data["hostels"]):
            self._hostel_card(cards_frame, h, col)

    def _hostel_card(self, parent, h, col):
        data = self.app.data
        rooms = db.rooms_for_hostel(data, h["id"])
        cap   = sum(r["capacity"] for r in rooms)
        occ   = sum(db.room_occupancy(data, r["id"]) for r in rooms)
        avail = sum(1 for r in rooms if r["status"] == "available")
        maint = sum(1 for r in rooms if r["status"] == "maintenance")

        card = tk.Frame(parent, bg=CARD, padx=PAD_CARD, pady=PAD_CARD)
        card.grid(row=0, column=col, sticky="nsew", padx=8)

        # Header
        top = tk.Frame(card, bg=CARD)
        top.pack(fill="x")
        tk.Label(top, text="🏠", bg=CARD, fg=ACCENT2,
                 font=("Segoe UI", 30)).pack(side="left")
        right_top = tk.Frame(top, bg=CARD)
        right_top.pack(side="left", padx=12)
        tk.Label(right_top, text=h["name"], bg=CARD, fg=TEXT, font=FONT_H2).pack(anchor="w")
        Badge(right_top, h.get("type","Boys")).pack(anchor="w", pady=2)

        Divider(card, pady=8)

        info = [
            ("🏢 Floors",     str(h.get("floors", "—"))),
            ("👤 Warden",     h.get("warden", "—")),
            ("📞 Contact",    h.get("contact", "—")),
        ]
        for lbl, val in info:
            row = tk.Frame(card, bg=CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=lbl, bg=CARD, fg=SUBTEXT, font=FONT_SMALL,
                     width=14, anchor="w").pack(side="left")
            tk.Label(row, text=val, bg=CARD, fg=TEXT, font=FONT_BODY).pack(side="left")

        Divider(card, pady=8)

        # Occupancy bar
        tk.Label(card, text="Occupancy", bg=CARD, fg=SUBTEXT, font=FONT_SMALL).pack(anchor="w")
        pct = int((occ / cap * 100)) if cap else 0
        bar_bg = tk.Frame(card, bg=CARD2, height=10)
        bar_bg.pack(fill="x", pady=4)
        fill_color = DANGER if pct > 85 else (ACCENT3 if pct > 65 else ACCENT)
        tk.Frame(bar_bg, bg=fill_color, height=10).place(relwidth=pct/100, relheight=1)

        stat_row = tk.Frame(card, bg=CARD)
        stat_row.pack(fill="x", pady=4)
        for lbl, val, color in [("Occupied", occ, ACCENT2),
                                  ("Available", avail, ACCENT),
                                  ("Maintenance", maint, ACCENT3)]:
            sf = tk.Frame(stat_row, bg=CARD2, padx=10, pady=6)
            sf.pack(side="left", padx=3, fill="x", expand=True)
            tk.Label(sf, text=str(val), bg=CARD2, fg=color,
                     font=("Segoe UI", 16, "bold")).pack()
            tk.Label(sf, text=lbl, bg=CARD2, fg=SUBTEXT, font=FONT_SMALL).pack()

        # Actions
        btn_row = tk.Frame(card, bg=CARD)
        btn_row.pack(fill="x", pady=(10, 0))
        AppButton(btn_row, "Edit", lambda hh=h: EditHostelModal(self, self.app, hh),
                  color=ACCENT2, small=True).pack(side="left", padx=2)
        AppButton(btn_row, "Delete", lambda hh=h: self._delete(hh),
                  color=DANGER, small=True).pack(side="left", padx=2)

    def _delete(self, h):
        if messagebox.askyesno("Delete Hostel",
                                f"Delete '{h['name']}'? This will remove all rooms and student allocations."):
            d = self.app.data
            room_ids = [r["id"] for r in d["rooms"] if r["hostel_id"] == h["id"]]
            d["rooms"] = [r for r in d["rooms"] if r["hostel_id"] != h["id"]]
            d["students"] = [s for s in d["students"] if s["hostel_id"] != h["id"]]
            d["hostels"] = [hh for hh in d["hostels"] if hh["id"] != h["id"]]
            db.save(d)
            self.refresh()


class AddHostelModal(Modal):
    def __init__(self, parent, app):
        super().__init__(parent, "Add New Hostel", 480, 400)
        self.app = app
        self._build()

    def _build(self):
        b = self.body
        self.f_name    = FormField(b, "Hostel Name", required=True)
        self.f_type    = FormDropdown(b, "Type", ["Boys", "Girls", "Co-ed"])
        self.f_floors  = FormField(b, "Number of Floors", "3")
        self.f_warden  = FormField(b, "Warden Name")
        self.f_contact = FormField(b, "Contact Number")
        for f in (self.f_name, self.f_type, self.f_floors, self.f_warden, self.f_contact):
            f.pack(fill="x", pady=5)
        self.add_footer_btn("Cancel", self.destroy, CARD2)
        self.add_footer_btn("Save Hostel", self._save, ACCENT)

    def _save(self):
        name = self.f_name.get()
        if not name:
            messagebox.showerror("Required", "Hostel name is required."); return
        hostel = {
            "id":      db.new_id("H"),
            "name":    name,
            "type":    self.f_type.get(),
            "floors":  self.f_floors.get(),
            "warden":  self.f_warden.get(),
            "contact": self.f_contact.get(),
        }
        self.app.data["hostels"].append(hostel)
        db.save(self.app.data)
        self.destroy()
        self.master.refresh()


class EditHostelModal(Modal):
    def __init__(self, parent, app, hostel):
        super().__init__(parent, f"Edit — {hostel['name']}", 480, 400)
        self.app = app
        self.hostel = hostel
        self._build()

    def _build(self):
        h = self.hostel
        b = self.body
        self.f_name    = FormField(b, "Hostel Name", h["name"], required=True)
        self.f_type    = FormDropdown(b, "Type", ["Boys","Girls","Co-ed"], h.get("type","Boys"))
        self.f_floors  = FormField(b, "Floors", h.get("floors",""))
        self.f_warden  = FormField(b, "Warden", h.get("warden",""))
        self.f_contact = FormField(b, "Contact", h.get("contact",""))
        for f in (self.f_name, self.f_type, self.f_floors, self.f_warden, self.f_contact):
            f.pack(fill="x", pady=5)
        self.add_footer_btn("Cancel", self.destroy, CARD2)
        self.add_footer_btn("Update", self._save, ACCENT)

    def _save(self):
        h = self.hostel
        h["name"]    = self.f_name.get()
        h["type"]    = self.f_type.get()
        h["floors"]  = self.f_floors.get()
        h["warden"]  = self.f_warden.get()
        h["contact"] = self.f_contact.get()
        db.save(self.app.data)
        self.destroy()
        self.master.refresh()
