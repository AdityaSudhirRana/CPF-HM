# pages/complaints.py

import tkinter as tk
from tkinter import messagebox
from datetime import date
from core.theme import *
from core import database as db
from components.widgets import (AppButton, Divider, Badge, FormField,
                                  FormDropdown, Modal, make_tree)


class ComplaintsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        data = self.app.data

        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=PAD_PAGE, pady=(PAD_PAGE, 4))
        tk.Label(hdr, text="Complaints & Maintenance", bg=BG, fg=TEXT, font=FONT_H1).pack(side="left")
        AppButton(hdr, "New Complaint", lambda: AddComplaintModal(self, self.app),
                  color=ACCENT, icon="📢").pack(side="right")
        Divider(self, pady=6)

        # Stats row
        sf = tk.Frame(self, bg=BG)
        sf.pack(fill="x", padx=PAD_PAGE, pady=6)
        comps = data["complaints"]
        for lbl, val, color in [
            ("Total",    len(comps), ACCENT2),
            ("Pending",  sum(1 for c in comps if c.get("status")=="pending"),  ACCENT3),
            ("Resolved", sum(1 for c in comps if c.get("status")=="resolved"), ACCENT),
        ]:
            card = tk.Frame(sf, bg=CARD, padx=18, pady=10)
            card.pack(side="left", padx=6)
            tk.Label(card, text=str(val), bg=CARD, fg=color,
                     font=("Segoe UI", 22, "bold")).pack()
            tk.Label(card, text=lbl, bg=CARD, fg=SUBTEXT, font=FONT_SMALL).pack()

        cols = ("Title", "Student", "Hostel", "Category", "Date", "Priority", "Status", "Resolution")
        widths = [160, 130, 110, 100, 90, 80, 90, 200]
        self._tree_wrap, self._tv = make_tree(self, cols, widths, height=16)
        self._tree_wrap.pack(fill="both", expand=True, padx=PAD_PAGE)

        bf = tk.Frame(self, bg=BG)
        bf.pack(fill="x", padx=PAD_PAGE, pady=8)
        AppButton(bf, "Mark Resolved", lambda: self._resolve(), ACCENT, small=True).pack(side="left", padx=4)
        AppButton(bf, "Delete",        lambda: self._delete(),  DANGER, small=True).pack(side="left", padx=4)

        self._populate()

    def _populate(self):
        tv = self._tv
        for row in tv.get_children():
            tv.delete(row)
        data = self.app.data
        for c in sorted(data["complaints"], key=lambda x: x.get("date",""), reverse=True):
            student = db.get_student(data, c.get("student_id",""))
            hostel  = db.get_hostel(data, c.get("hostel_id",""))
            tv.insert("", "end", iid=c["id"],
                      values=(c.get("title",""),
                               student["name"] if student else c.get("student_name","—"),
                               hostel["name"] if hostel else "—",
                               c.get("category",""),
                               c.get("date",""),
                               c.get("priority","").capitalize(),
                               c.get("status","").capitalize(),
                               c.get("resolution","")))

    def _resolve(self):
        sel = self._tv.selection()
        if not sel: messagebox.showwarning("Select","Select a complaint."); return
        cid = sel[0]
        c = next((x for x in self.app.data["complaints"] if x["id"] == cid), None)
        if c:
            c["status"] = "resolved"
            c["resolved_date"] = date.today().isoformat()
            db.save(self.app.data)
            self._populate()

    def _delete(self):
        sel = self._tv.selection()
        if not sel: return
        cid = sel[0]
        if messagebox.askyesno("Delete","Delete this complaint?"):
            self.app.data["complaints"] = [c for c in self.app.data["complaints"] if c["id"] != cid]
            db.save(self.app.data)
            self._populate()


class AddComplaintModal(Modal):
    def __init__(self, parent, app):
        super().__init__(parent, "New Complaint", 520, 460)
        self.app = app
        self._build()

    def _build(self):
        data = self.app.data
        b = self.body
        stu_labels = [f"{s['name']}  ({s['roll']})" for s in data["students"]]
        self._stu_map = {f"{s['name']}  ({s['roll']})": s for s in data["students"]}

        self.f_student   = FormDropdown(b, "Student", stu_labels or ["—"])
        self.f_student.pack(fill="x", pady=4)

        grid = tk.Frame(b, bg=BG)
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1)

        self.f_title    = FormField(grid, "Title *", required=True)
        self.f_title.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
        cats = ["Maintenance","Cleanliness","Security","Noise","Food","Internet","Other"]
        self.f_cat      = FormDropdown(grid, "Category", cats)
        self.f_cat.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        self.f_priority = FormDropdown(grid, "Priority", ["low","medium","high"])
        self.f_priority.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        self.f_hostel   = FormDropdown(grid, "Hostel", [h["name"] for h in data["hostels"]])
        self.f_hostel.grid(row=2, column=0, sticky="ew", padx=4, pady=4)

        tk.Label(b, text="Description", bg=BG, fg=SUBTEXT, font=FONT_SMALL).pack(anchor="w", pady=(8,2))
        self.f_desc = tk.Text(b, height=4, bg=CARD2, fg=TEXT, font=FONT_BODY,
                               relief="flat", bd=0, insertbackground=TEXT,
                               highlightthickness=1, highlightbackground=BORDER)
        self.f_desc.pack(fill="x")

        self.add_footer_btn("Cancel", self.destroy, CARD2)
        self.add_footer_btn("Submit", self._save, ACCENT)

    def _save(self):
        title = self.f_title.get()
        if not title: messagebox.showerror("Required","Title is required."); return
        stu = self._stu_map.get(self.f_student.get())
        hostel = next((h for h in self.app.data["hostels"] if h["name"] == self.f_hostel.get()), None)
        c = {
            "id":          db.new_id("C"),
            "title":       title,
            "student_id":  stu["id"] if stu else "",
            "student_name":stu["name"] if stu else "",
            "hostel_id":   hostel["id"] if hostel else "",
            "category":    self.f_cat.get(),
            "priority":    self.f_priority.get(),
            "description": self.f_desc.get("1.0","end-1c"),
            "date":        date.today().isoformat(),
            "status":      "pending",
            "resolution":  "",
        }
        self.app.data["complaints"].append(c)
        db.save(self.app.data)
        self.destroy()
        self.master.refresh()
