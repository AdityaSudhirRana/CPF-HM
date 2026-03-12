# pages/fees.py

import tkinter as tk
from tkinter import messagebox
from datetime import date
from core.theme import *
from core import database as db
from components.widgets import (AppButton, Divider, Badge, FormField,
                                  FormDropdown, Modal, make_tree, StatCard)


class FeesPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._filter_status = tk.StringVar(value="All")
        self._filter_status.trace("w", lambda *a: self._populate())

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        data = self.app.data

        # Header
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=PAD_PAGE, pady=(PAD_PAGE, 4))
        tk.Label(hdr, text="Fee Management", bg=BG, fg=TEXT, font=FONT_H1).pack(side="left")
        AppButton(hdr, "Add Fee Record", lambda: AddFeeModal(self, self.app),
                  color=ACCENT, icon="💰").pack(side="right")
        Divider(self, pady=6)

        # Summary cards
        sf = tk.Frame(self, bg=BG)
        sf.pack(fill="x", padx=PAD_PAGE, pady=8)
        sf.columnconfigure((0, 1, 2, 3), weight=1)

        fees = data["fees"]
        total_collected = sum(f.get("amount", 0) for f in fees if f.get("status") == "paid")
        total_pending   = sum(f.get("amount", 0) for f in fees if f.get("status") == "unpaid")
        count_paid      = sum(1 for f in fees if f.get("status") == "paid")
        count_unpaid    = sum(1 for f in fees if f.get("status") == "unpaid")

        cards = [
            ("💰", "Collected",      f"₹{total_collected:,}", ACCENT),
            ("⏳", "Pending",        f"₹{total_pending:,}",   DANGER),
            ("✅", "Paid Records",   count_paid,               ACCENT),
            ("❌", "Unpaid Records", count_unpaid,             ACCENT3),
        ]
        for col, (icon, lbl, val, color) in enumerate(cards):
            StatCard(sf, icon, lbl, val, color).grid(row=0, column=col, sticky="ew", padx=6)

        # Filters
        flt = tk.Frame(self, bg=BG)
        flt.pack(fill="x", padx=PAD_PAGE, pady=(8, 4))
        tk.Label(flt, text="Filter:", bg=BG, fg=SUBTEXT, font=FONT_SMALL).pack(side="left")
        for s in ["All", "paid", "unpaid", "partial"]:
            tk.Radiobutton(flt, text=s.capitalize(), variable=self._filter_status, value=s,
                           bg=BG, fg=TEXT, selectcolor=CARD2, activebackground=BG,
                           font=FONT_SMALL).pack(side="left", padx=6)

        # Table
        cols = ("Student Name", "Roll", "Month", "Amount", "Due Date", "Paid Date", "Status", "Remarks")
        widths = [160, 90, 80, 90, 100, 100, 90, 180]
        self._tree_wrap, self._tv = make_tree(self, cols, widths, height=14)
        self._tree_wrap.pack(fill="both", expand=True, padx=PAD_PAGE)

        # Actions
        bf = tk.Frame(self, bg=BG)
        bf.pack(fill="x", padx=PAD_PAGE, pady=8)
        AppButton(bf, "Mark as Paid", lambda: self._mark_paid(), ACCENT, small=True).pack(side="left", padx=4)
        AppButton(bf, "Edit Record",  lambda: self._edit(),      ACCENT2, small=True).pack(side="left", padx=4)
        AppButton(bf, "Delete",       lambda: self._delete(),    DANGER,  small=True).pack(side="left", padx=4)

        self._populate()

    def _populate(self):
        tv = self._tv
        for row in tv.get_children():
            tv.delete(row)
        data = self.app.data
        st_filter = self._filter_status.get()

        for f in sorted(data["fees"], key=lambda x: x.get("due_date",""), reverse=True):
            if st_filter != "All" and f.get("status","") != st_filter:
                continue
            student = db.get_student(data, f.get("student_id",""))
            tv.insert("", "end", iid=f["id"],
                      values=(student["name"] if student else "—",
                               student["roll"] if student else "—",
                               f.get("month",""),
                               f"₹{f.get('amount',0):,}",
                               f.get("due_date",""),
                               f.get("paid_date","—"),
                               f.get("status","").capitalize(),
                               f.get("remarks","")))

    def _selected_fee(self):
        sel = self._tv.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a fee record."); return None
        fid = sel[0]
        return next((f for f in self.app.data["fees"] if f["id"] == fid), None)

    def _mark_paid(self):
        fee = self._selected_fee()
        if not fee: return
        fee["status"]    = "paid"
        fee["paid_date"] = date.today().isoformat()
        db.save(self.app.data)
        self._populate()

    def _edit(self):
        fee = self._selected_fee()
        if fee: EditFeeModal(self, self.app, fee)

    def _delete(self):
        fee = self._selected_fee()
        if not fee: return
        if messagebox.askyesno("Delete", "Delete this fee record?"):
            self.app.data["fees"] = [f for f in self.app.data["fees"] if f["id"] != fee["id"]]
            db.save(self.app.data)
            self._populate()


class AddFeeModal(Modal):
    def __init__(self, parent, app):
        super().__init__(parent, "Add Fee Record", 500, 440)
        self.app = app
        self._build()

    def _build(self):
        data = self.app.data
        b = self.body
        stu_names = [f"{s['name']}  ({s['roll']})" for s in data["students"]]
        self._stu_map = {f"{s['name']}  ({s['roll']})": s for s in data["students"]}

        self.f_student = FormDropdown(b, "Student *", stu_names if stu_names else ["No students"])
        self.f_student.pack(fill="x", pady=5)

        grid = tk.Frame(b, bg=BG)
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1)

        months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]
        self.f_month    = FormDropdown(grid, "Month", months)
        self.f_month.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        self.f_amount   = FormField(grid, "Amount (₹) *", "5000")
        self.f_amount.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        self.f_due      = FormField(grid, "Due Date (YYYY-MM-DD)", date.today().isoformat())
        self.f_due.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        self.f_status   = FormDropdown(grid, "Status", ["unpaid","paid","partial"], "unpaid")
        self.f_status.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        self.f_remarks  = FormField(b, "Remarks")
        self.f_remarks.pack(fill="x", pady=5)

        self.add_footer_btn("Cancel", self.destroy, CARD2)
        self.add_footer_btn("Save Record", self._save, ACCENT)

    def _save(self):
        stu_label = self.f_student.get()
        student   = self._stu_map.get(stu_label)
        if not student:
            messagebox.showerror("Required", "Select a valid student."); return
        try:
            amount = int(self.f_amount.get())
        except ValueError:
            messagebox.showerror("Invalid", "Amount must be a number."); return

        fee = {
            "id":         db.new_id("F"),
            "student_id": student["id"],
            "month":      self.f_month.get(),
            "amount":     amount,
            "due_date":   self.f_due.get(),
            "paid_date":  date.today().isoformat() if self.f_status.get() == "paid" else "",
            "status":     self.f_status.get(),
            "remarks":    self.f_remarks.get(),
        }
        self.app.data["fees"].append(fee)
        db.save(self.app.data)
        self.destroy()
        self.master.refresh()


class EditFeeModal(Modal):
    def __init__(self, parent, app, fee):
        super().__init__(parent, "Edit Fee Record", 480, 360)
        self.app = app
        self.fee = fee
        self._build()

    def _build(self):
        f = self.fee
        b = self.body
        grid = tk.Frame(b, bg=BG)
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1)

        self.f_amount   = FormField(grid, "Amount (₹)", str(f.get("amount","")))
        self.f_amount.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        self.f_status   = FormDropdown(grid, "Status", ["unpaid","paid","partial"], f.get("status","unpaid"))
        self.f_status.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        self.f_due      = FormField(grid, "Due Date", f.get("due_date",""))
        self.f_due.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        self.f_paid     = FormField(grid, "Paid Date", f.get("paid_date",""))
        self.f_paid.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        self.f_remarks  = FormField(b, "Remarks", f.get("remarks",""))
        self.f_remarks.pack(fill="x", pady=5)

        self.add_footer_btn("Cancel", self.destroy, CARD2)
        self.add_footer_btn("Update", self._save, ACCENT)

    def _save(self):
        f = self.fee
        try:
            f["amount"] = int(self.f_amount.get())
        except ValueError:
            pass
        f["status"]    = self.f_status.get()
        f["due_date"]  = self.f_due.get()
        f["paid_date"] = self.f_paid.get()
        f["remarks"]   = self.f_remarks.get()
        db.save(self.app.data)
        self.destroy()
        self.master.refresh()
