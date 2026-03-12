# pages/rooms.py

import tkinter as tk
from tkinter import messagebox
from core.theme import *
from core import database as db
from components.widgets import (AppButton, Divider, Badge, FormField,
                                  FormDropdown, Modal, make_tree)

AMENITIES_LIST = ["AC", "WiFi", "Fan", "Attached Bathroom", "Common Bathroom",
                   "Hot Water", "TV", "Study Table", "Wardrobe"]

ROOM_TYPES = ["Single", "Double", "Triple", "Dormitory"]
STATUSES   = ["available", "occupied", "maintenance"]


class RoomsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._filter_hostel = tk.StringVar(value="All")
        self._filter_status = tk.StringVar(value="All")
        self._filter_hostel.trace("w", lambda *a: self._populate())
        self._filter_status.trace("w", lambda *a: self._populate())

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        data = self.app.data

        # ── Header ──
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=PAD_PAGE, pady=(PAD_PAGE, 4))
        tk.Label(hdr, text="Room Management", bg=BG, fg=TEXT, font=FONT_H1).pack(side="left")
        AppButton(hdr, "Add Room", lambda: AddRoomModal(self, self.app),
                  color=ACCENT, icon="🚪").pack(side="right")
        Divider(self, pady=6)

        # ── Filters ──
        flt = tk.Frame(self, bg=BG)
        flt.pack(fill="x", padx=PAD_PAGE, pady=(0, 10))
        tk.Label(flt, text="Hostel:", bg=BG, fg=SUBTEXT, font=FONT_SMALL).pack(side="left")
        hostel_names = ["All"] + [h["name"] for h in data["hostels"]]
        self._hostel_map = {"All": None, **{h["name"]: h["id"] for h in data["hostels"]}}
        for name in hostel_names:
            rb = tk.Radiobutton(flt, text=name, variable=self._filter_hostel, value=name,
                                bg=BG, fg=TEXT, selectcolor=CARD2, activebackground=BG,
                                activeforeground=TEXT, font=FONT_SMALL)
            rb.pack(side="left", padx=4)

        tk.Label(flt, text="  Status:", bg=BG, fg=SUBTEXT, font=FONT_SMALL).pack(side="left", padx=(16, 0))
        for s in ["All", "available", "occupied", "maintenance"]:
            rb = tk.Radiobutton(flt, text=s.capitalize(), variable=self._filter_status, value=s,
                                bg=BG, fg=TEXT, selectcolor=CARD2, activebackground=BG,
                                activeforeground=TEXT, font=FONT_SMALL)
            rb.pack(side="left", padx=4)

        # ── Table ──
        cols = ("Room No", "Hostel", "Floor", "Type", "Capacity", "Occupied", "Status",
                "Rent/mo", "Amenities")
        widths = [80, 130, 60, 80, 80, 80, 100, 80, 200]
        self._tree_wrap, self._tv = make_tree(self, cols, widths, height=18)
        self._tree_wrap.pack(fill="both", expand=True, padx=PAD_PAGE)

        # ── Action row ──
        bf = tk.Frame(self, bg=BG)
        bf.pack(fill="x", padx=PAD_PAGE, pady=8)
        AppButton(bf, "Edit Room",   lambda: self._edit(),   ACCENT2, small=True).pack(side="left", padx=4)
        AppButton(bf, "Delete Room", lambda: self._delete(), DANGER,  small=True).pack(side="left", padx=4)
        AppButton(bf, "View Occupants", lambda: self._view_occupants(), ACCENT4, small=True).pack(side="left", padx=4)

        self._populate()

    def _populate(self):
        tv = self._tv
        for row in tv.get_children():
            tv.delete(row)
        data = self.app.data
        hid_filter = self._hostel_map.get(self._filter_hostel.get())
        st_filter  = self._filter_status.get()

        for r in data["rooms"]:
            if hid_filter and r["hostel_id"] != hid_filter:
                continue
            if st_filter != "All" and r["status"] != st_filter:
                continue
            hostel = db.get_hostel(data, r["hostel_id"])
            occ    = db.room_occupancy(data, r["id"])
            tv.insert("", "end", iid=r["id"],
                      values=(r["number"],
                               hostel["name"] if hostel else "—",
                               r.get("floor","—"),
                               r.get("type","—"),
                               r["capacity"],
                               occ,
                               r["status"].capitalize(),
                               f"₹{r.get('rent',0):,}",
                               ", ".join(r.get("amenities",[]))))

    def _edit(self):
        sel = self._tv.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a room."); return
        room = db.get_room(self.app.data, sel[0])
        EditRoomModal(self, self.app, room)

    def _delete(self):
        sel = self._tv.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a room."); return
        room = db.get_room(self.app.data, sel[0])
        if db.room_occupancy(self.app.data, room["id"]) > 0:
            messagebox.showerror("Occupied", "Cannot delete an occupied room."); return
        if messagebox.askyesno("Delete", f"Delete room {room['number']}?"):
            self.app.data["rooms"] = [r for r in self.app.data["rooms"] if r["id"] != room["id"]]
            db.save(self.app.data)
            self._populate()

    def _view_occupants(self):
        sel = self._tv.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a room."); return
        room = db.get_room(self.app.data, sel[0])
        students = db.students_in_room(self.app.data, room["id"])
        win = tk.Toplevel(self)
        win.title(f"Room {room['number']} — Occupants")
        win.geometry("500x300")
        win.configure(bg=CARD)
        win.grab_set()
        tk.Label(win, text=f"Room {room['number']} Occupants  ({len(students)}/{room['capacity']})",
                 bg=CARD, fg=TEXT, font=FONT_H3, pady=12).pack(fill="x")
        Divider(win, pady=0)
        if not students:
            tk.Label(win, text="No students in this room.", bg=CARD, fg=SUBTEXT,
                     font=FONT_BODY, pady=20).pack()
        for s in students:
            row = tk.Frame(win, bg=CARD2, pady=8, padx=14)
            row.pack(fill="x", padx=12, pady=4)
            tk.Label(row, text=f"👤 {s['name']}", bg=CARD2, fg=TEXT, font=FONT_BODY).pack(side="left")
            tk.Label(row, text=s["roll"], bg=CARD2, fg=SUBTEXT, font=FONT_SMALL).pack(side="right")
            tk.Label(row, text=s.get("course",""), bg=CARD2, fg=DIM,
                     font=FONT_SMALL).pack(side="right", padx=12)


class AddRoomModal(Modal):
    def __init__(self, parent, app):
        super().__init__(parent, "Add New Room", 520, 560)
        self.app = app
        self._build()

    def _build(self):
        b = self.body
        data = self.app.data
        hostel_names = [h["name"] for h in data["hostels"]]
        self._hostel_map = {h["name"]: h["id"] for h in data["hostels"]}

        grid = tk.Frame(b, bg=BG)
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1)

        self.f_hostel   = FormDropdown(grid, "Hostel *", hostel_names)
        self.f_hostel.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        self.f_number   = FormField(grid, "Room Number *", required=True)
        self.f_number.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        self.f_floor    = FormField(grid, "Floor", "1")
        self.f_floor.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        self.f_type     = FormDropdown(grid, "Room Type", ROOM_TYPES)
        self.f_type.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        self.f_capacity = FormField(grid, "Capacity", "2")
        self.f_capacity.grid(row=2, column=0, sticky="ew", padx=4, pady=4)
        self.f_rent     = FormField(grid, "Monthly Rent (₹)", "4000")
        self.f_rent.grid(row=2, column=1, sticky="ew", padx=4, pady=4)
        self.f_status   = FormDropdown(grid, "Status", STATUSES, "available")
        self.f_status.grid(row=3, column=0, sticky="ew", padx=4, pady=4)

        # Amenities checkboxes
        tk.Label(b, text="Amenities", bg=BG, fg=SUBTEXT, font=FONT_SMALL).pack(anchor="w", pady=(10, 4))
        am_frame = tk.Frame(b, bg=BG)
        am_frame.pack(fill="x")
        self._am_vars = {}
        for i, am in enumerate(AMENITIES_LIST):
            var = tk.BooleanVar()
            self._am_vars[am] = var
            tk.Checkbutton(am_frame, text=am, variable=var, bg=BG, fg=TEXT,
                           selectcolor=CARD2, activebackground=BG, activeforeground=TEXT,
                           font=FONT_SMALL).grid(row=i//3, column=i%3, sticky="w", padx=4)

        self.add_footer_btn("Cancel", self.destroy, CARD2)
        self.add_footer_btn("Save Room", self._save, ACCENT)

    def _save(self):
        num = self.f_number.get()
        if not num:
            messagebox.showerror("Required", "Room number is required."); return
        try:
            cap  = int(self.f_capacity.get())
            rent = int(self.f_rent.get())
        except ValueError:
            messagebox.showerror("Invalid", "Capacity and rent must be numbers."); return

        room = {
            "id":         db.new_id("R"),
            "hostel_id":  self._hostel_map[self.f_hostel.get()],
            "number":     num,
            "floor":      self.f_floor.get(),
            "type":       self.f_type.get(),
            "capacity":   cap,
            "status":     self.f_status.get(),
            "rent":       rent,
            "amenities":  [k for k, v in self._am_vars.items() if v.get()],
        }
        self.app.data["rooms"].append(room)
        db.save(self.app.data)
        self.destroy()
        self.master.refresh()


class EditRoomModal(Modal):
    def __init__(self, parent, app, room):
        super().__init__(parent, f"Edit Room {room['number']}", 500, 400)
        self.app  = app
        self.room = room
        self._build()

    def _build(self):
        r = self.room
        b = self.body
        grid = tk.Frame(b, bg=BG)
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1)

        self.f_floor  = FormField(grid, "Floor", r.get("floor",""))
        self.f_floor.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        self.f_type   = FormDropdown(grid, "Type", ROOM_TYPES, r.get("type","Double"))
        self.f_type.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        self.f_rent   = FormField(grid, "Rent (₹)", r.get("rent",""))
        self.f_rent.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        self.f_status = FormDropdown(grid, "Status", STATUSES, r["status"])
        self.f_status.grid(row=1, column=1, sticky="ew", padx=4, pady=4)

        tk.Label(b, text="Amenities", bg=BG, fg=SUBTEXT, font=FONT_SMALL).pack(anchor="w", pady=(12, 4))
        am_frame = tk.Frame(b, bg=BG)
        am_frame.pack(fill="x")
        self._am_vars = {}
        for i, am in enumerate(AMENITIES_LIST):
            var = tk.BooleanVar(value=(am in r.get("amenities",[])))
            self._am_vars[am] = var
            tk.Checkbutton(am_frame, text=am, variable=var, bg=BG, fg=TEXT,
                           selectcolor=CARD2, activebackground=BG, activeforeground=TEXT,
                           font=FONT_SMALL).grid(row=i//3, column=i%3, sticky="w", padx=4)

        self.add_footer_btn("Cancel", self.destroy, CARD2)
        self.add_footer_btn("Update", self._save, ACCENT)

    def _save(self):
        r = self.room
        try:
            r["rent"]      = int(self.f_rent.get())
        except ValueError:
            pass
        r["floor"]     = self.f_floor.get()
        r["type"]      = self.f_type.get()
        r["status"]    = self.f_status.get()
        r["amenities"] = [k for k, v in self._am_vars.items() if v.get()]
        db.save(self.app.data)
        self.destroy()
        self.master.refresh()
