# pages/visitors.py

import tkinter as tk
from tkinter import messagebox
from datetime import date, datetime
from core.theme import *
from core import database as db
from components.widgets import (AppButton, Divider, FormField, FormDropdown,
                                  Modal, make_tree)


class VisitorsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=PAD_PAGE, pady=(PAD_PAGE, 4))
        tk.Label(hdr, text="Visitor Log", bg=BG, fg=TEXT, font=FONT_H1).pack(side="left")
        AppButton(hdr, "Log Visitor", lambda: LogVisitorModal(self, self.app),
                  color=ACCENT, icon="👥").pack(side="right")
        Divider(self, pady=6)

        cols = ("Visitor Name", "Phone", "Visiting Student", "Hostel",
                "Purpose", "Check-In", "Check-Out", "Date")
        widths = [150, 110, 140, 120, 120, 80, 80, 90]
        self._tree_wrap, self._tv = make_tree(self, cols, widths, height=20)
        self._tree_wrap.pack(fill="both", expand=True, padx=PAD_PAGE)

        bf = tk.Frame(self, bg=BG)
        bf.pack(fill="x", padx=PAD_PAGE, pady=8)
        AppButton(bf, "Mark Check-Out", lambda: self._checkout(), ACCENT2, small=True).pack(side="left", padx=4)
        AppButton(bf, "Delete Entry",   lambda: self._delete(),   DANGER,  small=True).pack(side="left", padx=4)

        self._populate()

    def _populate(self):
        tv = self._tv
        for row in tv.get_children():
            tv.delete(row)
        data = self.app.data
        for v in sorted(data["visitors"], key=lambda x: x.get("date",""), reverse=True):
            student = db.get_student(data, v.get("student_id",""))
            hostel  = db.get_hostel(data, v.get("hostel_id",""))
            tv.insert("", "end", iid=v["id"],
                      values=(v.get("visitor_name",""),
                               v.get("visitor_phone",""),
                               student["name"] if student else v.get("student_name","—"),
                               hostel["name"] if hostel else "—",
                               v.get("purpose",""),
                               v.get("check_in",""),
                               v.get("check_out","—"),
                               v.get("date","")))

    def _checkout(self):
        sel = self._tv.selection()
        if not sel: return
        vid = sel[0]
        v = next((x for x in self.app.data["visitors"] if x["id"] == vid), None)
        if v:
            v["check_out"] = datetime.now().strftime("%H:%M")
            db.save(self.app.data)
            self._populate()

    def _delete(self):
        sel = self._tv.selection()
        if not sel: return
        if messagebox.askyesno("Delete","Delete this visitor entry?"):
            self.app.data["visitors"] = [v for v in self.app.data["visitors"] if v["id"] != sel[0]]
            db.save(self.app.data)
            self._populate()


class LogVisitorModal(Modal):
    def __init__(self, parent, app):
        super().__init__(parent, "Log New Visitor", 500, 440)
        self.app = app
        self._build()

    def _build(self):
        data = self.app.data
        b = self.body
        stu_labels = [f"{s['name']}  ({s['roll']})" for s in data["students"]]
        self._stu_map = {f"{s['name']}  ({s['roll']})": s for s in data["students"]}

        grid = tk.Frame(b, bg=BG)
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1)

        self.f_vname   = FormField(grid, "Visitor Name *", required=True)
        self.f_vname.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        self.f_vphone  = FormField(grid, "Visitor Phone")
        self.f_vphone.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        self.f_student = FormDropdown(grid, "Visiting Student *", stu_labels or ["—"])
        self.f_student.grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
        purposes = ["Family Visit","Academic","Personal","Delivery","Other"]
        self.f_purpose = FormDropdown(grid, "Purpose", purposes)
        self.f_purpose.grid(row=2, column=0, sticky="ew", padx=4, pady=4)
        self.f_checkin = FormField(grid, "Check-In Time", datetime.now().strftime("%H:%M"))
        self.f_checkin.grid(row=2, column=1, sticky="ew", padx=4, pady=4)
        self.f_id_proof= FormField(grid, "ID Proof Type")
        self.f_id_proof.grid(row=3, column=0, sticky="ew", padx=4, pady=4)
        self.f_id_num  = FormField(grid, "ID Number")
        self.f_id_num.grid(row=3, column=1, sticky="ew", padx=4, pady=4)

        self.add_footer_btn("Cancel", self.destroy, CARD2)
        self.add_footer_btn("Log Entry", self._save, ACCENT)

    def _save(self):
        vname = self.f_vname.get()
        if not vname: messagebox.showerror("Required","Visitor name is required."); return
        stu = self._stu_map.get(self.f_student.get())
        entry = {
            "id":            db.new_id("V"),
            "visitor_name":  vname,
            "visitor_phone": self.f_vphone.get(),
            "student_id":    stu["id"] if stu else "",
            "student_name":  stu["name"] if stu else "",
            "hostel_id":     stu["hostel_id"] if stu else "",
            "purpose":       self.f_purpose.get(),
            "check_in":      self.f_checkin.get(),
            "check_out":     "",
            "id_proof":      self.f_id_proof.get(),
            "id_number":     self.f_id_num.get(),
            "date":          date.today().isoformat(),
        }
        self.app.data["visitors"].append(entry)
        db.save(self.app.data)
        self.destroy()
        self.master.refresh()
