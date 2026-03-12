# pages/students.py

import tkinter as tk
from tkinter import messagebox
from core.theme import *
from core import database as db
from components.widgets import (AppButton, Divider, FormField, FormDropdown,
                                  Modal, make_tree)


class StudentsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._search_var = tk.StringVar()
        self._search_var.trace("w", lambda *a: self._populate())

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=PAD_PAGE, pady=(PAD_PAGE, 4))
        tk.Label(hdr, text="Students", bg=BG, fg=TEXT, font=FONT_H1).pack(side="left")
        AppButton(hdr, "Admit Student", lambda: AdmitStudentModal(self, self.app),
                  color=ACCENT, icon="🎓").pack(side="right")
        Divider(self, pady=6)

        # Search bar
        sf = tk.Frame(self, bg=BG)
        sf.pack(fill="x", padx=PAD_PAGE, pady=(0, 10))
        tk.Label(sf, text="🔍", bg=BG, fg=SUBTEXT, font=("Segoe UI", 12)).pack(side="left")
        tk.Entry(sf, textvariable=self._search_var, bg=CARD, fg=TEXT, font=FONT_BODY,
                 relief="flat", bd=0, insertbackground=TEXT, width=36,
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT2).pack(side="left", padx=8, ipady=6)
        tk.Label(sf, text="Search by name, roll, course...", bg=BG, fg=DIM,
                 font=FONT_SMALL).pack(side="left")

        # Table
        cols = ("Name", "Roll No", "Course", "Year", "Hostel", "Room",
                "Phone", "Guardian", "Joined")
        widths = [160, 90, 120, 50, 120, 70, 110, 140, 90]
        self._tree_wrap, self._tv = make_tree(self, cols, widths, height=18)
        self._tree_wrap.pack(fill="both", expand=True, padx=PAD_PAGE)

        # Actions
        bf = tk.Frame(self, bg=BG)
        bf.pack(fill="x", padx=PAD_PAGE, pady=8)
        AppButton(bf, "View Profile", lambda: self._profile(), ACCENT2, small=True).pack(side="left", padx=4)
        AppButton(bf, "Edit",         lambda: self._edit(),    ACCENT4, small=True).pack(side="left", padx=4)
        AppButton(bf, "Vacate",       lambda: self._vacate(),  ACCENT3, small=True).pack(side="left", padx=4)
        AppButton(bf, "Delete",       lambda: self._delete(),  DANGER,  small=True).pack(side="left", padx=4)

        self._populate()

    def _populate(self):
        tv = self._tv
        for row in tv.get_children():
            tv.delete(row)
        data = self.app.data
        q = self._search_var.get().lower()

        for s in sorted(data["students"], key=lambda x: x["name"]):
            if q and not any(q in str(s.get(k,"")).lower()
                             for k in ("name","roll","course","email")):
                continue
            hostel = db.get_hostel(data, s.get("hostel_id",""))
            room   = db.get_room(data, s.get("room_id",""))
            tv.insert("", "end", iid=s["id"],
                      values=(s["name"], s["roll"], s.get("course",""),
                               s.get("year",""), hostel["name"] if hostel else "—",
                               room["number"] if room else "—",
                               s.get("phone",""), s.get("guardian",""),
                               s.get("join_date","")))

    def _selected(self):
        sel = self._tv.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a student."); return None
        return db.get_student(self.app.data, sel[0])

    def _profile(self):
        s = self._selected()
        if s: StudentProfileModal(self, self.app, s)

    def _edit(self):
        s = self._selected()
        if s: EditStudentModal(self, self.app, s)

    def _vacate(self):
        s = self._selected()
        if not s: return
        if messagebox.askyesno("Vacate Room", f"Vacate {s['name']} from their room?"):
            # Free up room
            room = db.get_room(self.app.data, s.get("room_id",""))
            if room:
                occ = db.room_occupancy(self.app.data, room["id"])
                if occ <= 1:
                    room["status"] = "available"
            s["room_id"]   = None
            s["hostel_id"] = None
            db.save(self.app.data)
            self._populate()

    def _delete(self):
        s = self._selected()
        if not s: return
        if messagebox.askyesno("Delete Student", f"Delete record for {s['name']}?"):
            self.app.data["students"] = [st for st in self.app.data["students"] if st["id"] != s["id"]]
            db.save(self.app.data)
            self._populate()


class StudentProfileModal(Modal):
    def __init__(self, parent, app, student):
        super().__init__(parent, "Student Profile", 520, 500)
        self.app = app
        s = student
        data = app.data
        b = self.body
        hostel = db.get_hostel(data, s.get("hostel_id",""))
        room   = db.get_room(data, s.get("room_id",""))
        fees   = db.fees_for_student(data, s["id"])

        # Avatar
        av_frame = tk.Frame(b, bg=BG)
        av_frame.pack(fill="x", pady=(0, 12))
        cv = tk.Canvas(av_frame, width=60, height=60, bg=ACCENT4, highlightthickness=0)
        cv.pack(side="left")
        cv.create_text(30, 30, text=s["name"][0], fill=TEXT, font=("Segoe UI", 28, "bold"))
        info_f = tk.Frame(av_frame, bg=BG)
        info_f.pack(side="left", padx=14)
        tk.Label(info_f, text=s["name"], bg=BG, fg=TEXT, font=FONT_H2).pack(anchor="w")
        tk.Label(info_f, text=f"{s['roll']}  •  {s.get('course','')}", bg=BG, fg=SUBTEXT,
                 font=FONT_BODY).pack(anchor="w")

        Divider(b, pady=8)

        fields = [
            ("🏠 Hostel",       hostel["name"] if hostel else "—"),
            ("🚪 Room",         room["number"] if room else "—"),
            ("📅 Year",         str(s.get("year","—"))),
            ("📞 Phone",        s.get("phone","—")),
            ("✉️ Email",        s.get("email","—")),
            ("👤 Guardian",     s.get("guardian","—")),
            ("📞 Guardian Ph.", s.get("guardian_phone","—")),
            ("📅 Date of Birth",s.get("dob","—")),
            ("📅 Join Date",    s.get("join_date","—")),
            ("💰 Fee Records",  f"{len(fees)} record(s)"),
        ]
        grid = tk.Frame(b, bg=BG)
        grid.pack(fill="x")
        for i, (lbl, val) in enumerate(fields):
            tk.Label(grid, text=lbl, bg=BG, fg=SUBTEXT, font=FONT_SMALL,
                     width=18, anchor="w").grid(row=i, column=0, sticky="w", pady=3)
            tk.Label(grid, text=val, bg=BG, fg=TEXT, font=FONT_BODY,
                     anchor="w").grid(row=i, column=1, sticky="w", pady=3, padx=10)

        self.add_footer_btn("Close", self.destroy, CARD2)


class AdmitStudentModal(Modal):
    def __init__(self, parent, app):
        super().__init__(parent, "Admit New Student", 600, 620)
        self.app = app
        self._build()

    def _build(self):
        data = self.app.data
        b = self.body

        # Hostel & Room selectors
        avail_rooms = [r for r in data["rooms"] if r["status"] == "available"]
        hostel_names = list({db.get_hostel(data, r["hostel_id"])["name"]
                              for r in avail_rooms
                              if db.get_hostel(data, r["hostel_id"])})

        self._room_map = {
            f"{db.get_hostel(data, r['hostel_id'])['name']} — Room {r['number']} (cap {r['capacity']})": r
            for r in avail_rooms if db.get_hostel(data, r["hostel_id"])
        }
        room_labels = list(self._room_map.keys())

        grid = tk.Frame(b, bg=BG)
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1)

        self.f_name     = FormField(grid, "Full Name *", required=True)
        self.f_name.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        self.f_roll     = FormField(grid, "Roll Number *", required=True)
        self.f_roll.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        self.f_course   = FormField(grid, "Course", "B.Tech CSE")
        self.f_course.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        self.f_year     = FormDropdown(grid, "Year", ["1","2","3","4"], "1")
        self.f_year.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        self.f_room     = FormDropdown(grid, "Assign Room *", room_labels if room_labels else ["No rooms available"])
        self.f_room.grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
        self.f_phone    = FormField(grid, "Phone")
        self.f_phone.grid(row=3, column=0, sticky="ew", padx=4, pady=4)
        self.f_email    = FormField(grid, "Email")
        self.f_email.grid(row=3, column=1, sticky="ew", padx=4, pady=4)
        self.f_dob      = FormField(grid, "Date of Birth (YYYY-MM-DD)")
        self.f_dob.grid(row=4, column=0, sticky="ew", padx=4, pady=4)
        self.f_guardian = FormField(grid, "Guardian Name")
        self.f_guardian.grid(row=4, column=1, sticky="ew", padx=4, pady=4)
        self.f_gphone   = FormField(grid, "Guardian Phone")
        self.f_gphone.grid(row=5, column=0, sticky="ew", padx=4, pady=4)

        self.add_footer_btn("Cancel", self.destroy, CARD2)
        self.add_footer_btn("Admit Student", self._save, ACCENT)

    def _save(self):
        name = self.f_name.get()
        roll = self.f_roll.get()
        room_label = self.f_room.get()
        if not name or not roll:
            messagebox.showerror("Required", "Name and Roll Number are required."); return
        room = self._room_map.get(room_label)
        if not room:
            messagebox.showerror("No Room", "Please select a valid room."); return

        # Check capacity
        occ = db.room_occupancy(self.app.data, room["id"])
        if occ >= room["capacity"]:
            messagebox.showerror("Full", "Selected room is at full capacity."); return

        from core.database import today
        student = {
            "id":             db.new_id("S"),
            "name":           name,
            "roll":           roll,
            "course":         self.f_course.get(),
            "year":           self.f_year.get(),
            "hostel_id":      room["hostel_id"],
            "room_id":        room["id"],
            "phone":          self.f_phone.get(),
            "email":          self.f_email.get(),
            "dob":            self.f_dob.get(),
            "guardian":       self.f_guardian.get(),
            "guardian_phone": self.f_gphone.get(),
            "join_date":      today(),
        }
        self.app.data["students"].append(student)

        # Update room status
        new_occ = occ + 1
        if new_occ >= room["capacity"]:
            room["status"] = "occupied"

        db.save(self.app.data)
        messagebox.showinfo("Success", f"{name} admitted successfully!")
        self.destroy()
        self.master.refresh()


class EditStudentModal(Modal):
    def __init__(self, parent, app, student):
        super().__init__(parent, f"Edit — {student['name']}", 520, 480)
        self.app = app
        self.student = student
        self._build()

    def _build(self):
        s = self.student
        b = self.body
        grid = tk.Frame(b, bg=BG)
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1)

        self.f_name     = FormField(grid, "Full Name", s["name"])
        self.f_name.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        self.f_course   = FormField(grid, "Course", s.get("course",""))
        self.f_course.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        self.f_year     = FormDropdown(grid, "Year", ["1","2","3","4"], str(s.get("year","1")))
        self.f_year.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        self.f_phone    = FormField(grid, "Phone", s.get("phone",""))
        self.f_phone.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        self.f_email    = FormField(grid, "Email", s.get("email",""))
        self.f_email.grid(row=2, column=0, sticky="ew", padx=4, pady=4)
        self.f_dob      = FormField(grid, "DOB", s.get("dob",""))
        self.f_dob.grid(row=2, column=1, sticky="ew", padx=4, pady=4)
        self.f_guardian = FormField(grid, "Guardian", s.get("guardian",""))
        self.f_guardian.grid(row=3, column=0, sticky="ew", padx=4, pady=4)
        self.f_gphone   = FormField(grid, "Guardian Phone", s.get("guardian_phone",""))
        self.f_gphone.grid(row=3, column=1, sticky="ew", padx=4, pady=4)

        self.add_footer_btn("Cancel", self.destroy, CARD2)
        self.add_footer_btn("Update", self._save, ACCENT)

    def _save(self):
        s = self.student
        s["name"]           = self.f_name.get()
        s["course"]         = self.f_course.get()
        s["year"]           = self.f_year.get()
        s["phone"]          = self.f_phone.get()
        s["email"]          = self.f_email.get()
        s["dob"]            = self.f_dob.get()
        s["guardian"]       = self.f_guardian.get()
        s["guardian_phone"] = self.f_gphone.get()
        db.save(self.app.data)
        self.destroy()
        self.master.refresh()
