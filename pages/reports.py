# pages/reports.py

import tkinter as tk
import csv
from tkinter import filedialog, messagebox
from datetime import date
from core.theme import *
from core import database as db
from components.widgets import AppButton, Divider, StatCard


class ReportsPage(tk.Frame):
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
        tk.Label(hdr, text="Reports & Analytics", bg=BG, fg=TEXT, font=FONT_H1).pack(side="left")
        Divider(self, pady=6)

        scroll = tk.Canvas(self, bg=BG, highlightthickness=0)
        inner = tk.Frame(scroll, bg=BG)
        inner.bind("<Configure>",
                   lambda e: scroll.configure(scrollregion=scroll.bbox("all")))
        scroll.create_window((0, 0), window=inner, anchor="nw")
        scroll.pack(fill="both", expand=True, padx=PAD_PAGE, pady=4)

        # ── Overall stats ──────────────────────────────────────────────────
        self._section(inner, "Overall Summary")
        sf = tk.Frame(inner, bg=BG)
        sf.pack(fill="x", pady=8)
        sf.columnconfigure((0,1,2,3,4), weight=1)

        rooms = data["rooms"]
        students = data["students"]
        fees_list = data["fees"]
        total_capacity = sum(r["capacity"] for r in rooms)
        total_occ = sum(db.room_occupancy(data, r["id"]) for r in rooms)
        total_collected = sum(f.get("amount",0) for f in fees_list if f.get("status")=="paid")
        total_pending   = sum(f.get("amount",0) for f in fees_list if f.get("status")=="unpaid")
        occ_pct = int(total_occ / total_capacity * 100) if total_capacity else 0

        for col, (icon, lbl, val, color) in enumerate([
            ("🏠", "Total Capacity",  total_capacity,    ACCENT2),
            ("👥", "Occupancy",       f"{total_occ} ({occ_pct}%)", ACCENT4),
            ("🎓", "Students",        len(students),     ACCENT),
            ("💰", "Fees Collected",  f"₹{total_collected:,}", ACCENT),
            ("⏳", "Fees Pending",    f"₹{total_pending:,}",   DANGER),
        ]):
            StatCard(sf, icon, lbl, val, color).grid(row=0, column=col, sticky="ew", padx=6)

        # ── Hostel breakdown ───────────────────────────────────────────────
        self._section(inner, "Hostel-wise Breakdown")
        htable = tk.Frame(inner, bg=CARD, padx=16, pady=14)
        htable.pack(fill="x", pady=8)
        headers = ["Hostel", "Type", "Rooms", "Capacity", "Occupied", "Available", "Occupancy %"]
        for col, h in enumerate(headers):
            tk.Label(htable, text=h, bg=PANEL, fg=SUBTEXT, font=FONT_SMALL,
                     width=14, anchor="w", padx=4, pady=4).grid(row=0, column=col, sticky="ew", padx=1)
        for row_i, h in enumerate(data["hostels"], 1):
            h_rooms = db.rooms_for_hostel(data, h["id"])
            cap   = sum(r["capacity"] for r in h_rooms)
            occ   = sum(db.room_occupancy(data, r["id"]) for r in h_rooms)
            avail = sum(1 for r in h_rooms if r["status"]=="available")
            pct   = int(occ/cap*100) if cap else 0
            vals  = [h["name"], h.get("type",""), len(h_rooms), cap, occ, avail, f"{pct}%"]
            bg = CARD if row_i%2==0 else CARD2
            for col, val in enumerate(vals):
                tk.Label(htable, text=str(val), bg=bg, fg=TEXT, font=FONT_BODY,
                         width=14, anchor="w", padx=4, pady=6).grid(row=row_i, column=col, sticky="ew", padx=1)

        # ── Room type breakdown ────────────────────────────────────────────
        self._section(inner, "Room Type Distribution")
        rt_frame = tk.Frame(inner, bg=BG)
        rt_frame.pack(fill="x", pady=8)
        rt_counts = {}
        for r in data["rooms"]:
            t = r.get("type","Unknown")
            rt_counts[t] = rt_counts.get(t, 0) + 1
        colors = [ACCENT, ACCENT2, ACCENT4, ACCENT3, DANGER]
        for i, (rtype, count) in enumerate(sorted(rt_counts.items(), key=lambda x: -x[1])):
            card = tk.Frame(rt_frame, bg=CARD, padx=16, pady=12)
            card.pack(side="left", padx=6)
            color = colors[i % len(colors)]
            tk.Label(card, text=str(count), bg=CARD, fg=color,
                     font=("Segoe UI", 22, "bold")).pack()
            tk.Label(card, text=rtype, bg=CARD, fg=SUBTEXT, font=FONT_SMALL).pack()

        # ── Fee summary by month ───────────────────────────────────────────
        self._section(inner, "Fee Collection by Month")
        fee_by_month = {}
        for f in fees_list:
            m = f.get("month","Unknown")
            if m not in fee_by_month:
                fee_by_month[m] = {"paid": 0, "unpaid": 0}
            if f.get("status") == "paid":
                fee_by_month[m]["paid"] += f.get("amount", 0)
            else:
                fee_by_month[m]["unpaid"] += f.get("amount", 0)

        if fee_by_month:
            fee_table = tk.Frame(inner, bg=CARD, padx=16, pady=14)
            fee_table.pack(fill="x", pady=8)
            for col, h in enumerate(["Month", "Collected", "Pending", "Total"]):
                tk.Label(fee_table, text=h, bg=PANEL, fg=SUBTEXT, font=FONT_SMALL,
                         width=18, anchor="w", padx=6, pady=4).grid(row=0, column=col, sticky="ew", padx=1)
            for ri, (month, vals) in enumerate(sorted(fee_by_month.items()), 1):
                bg = CARD if ri%2==0 else CARD2
                total = vals["paid"] + vals["unpaid"]
                for ci, val in enumerate([month, f"₹{vals['paid']:,}",
                                           f"₹{vals['unpaid']:,}", f"₹{total:,}"]):
                    tk.Label(fee_table, text=val, bg=bg, fg=TEXT, font=FONT_BODY,
                             width=18, anchor="w", padx=6, pady=6).grid(row=ri, column=ci, sticky="ew", padx=1)
        else:
            tk.Label(inner, text="No fee data yet.", bg=BG, fg=SUBTEXT, font=FONT_BODY).pack(anchor="w")

        # ── Export buttons ─────────────────────────────────────────────────
        self._section(inner, "Export Data")
        exp_frame = tk.Frame(inner, bg=BG)
        exp_frame.pack(fill="x", pady=8)
        AppButton(exp_frame, "Export Students CSV",    lambda: self._export("students"),    ACCENT2).pack(side="left", padx=6)
        AppButton(exp_frame, "Export Fee Report CSV",  lambda: self._export("fees"),        ACCENT4).pack(side="left", padx=6)
        AppButton(exp_frame, "Export Complaints CSV",  lambda: self._export("complaints"),  ACCENT3).pack(side="left", padx=6)

    def _section(self, parent, title):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", pady=(12, 0))
        tk.Label(f, text=title, bg=BG, fg=TEXT, font=FONT_H3).pack(side="left")
        Divider(f)

    def _export(self, kind):
        data = self.app.data
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV","*.csv")])
        if not path: return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if kind == "students":
                w.writerow(["Name","Roll","Course","Year","Hostel","Room","Phone","Email","Join Date"])
                for s in data["students"]:
                    hostel = db.get_hostel(data, s.get("hostel_id",""))
                    room   = db.get_room(data, s.get("room_id",""))
                    w.writerow([s["name"], s["roll"], s.get("course",""), s.get("year",""),
                                hostel["name"] if hostel else "", room["number"] if room else "",
                                s.get("phone",""), s.get("email",""), s.get("join_date","")])
            elif kind == "fees":
                w.writerow(["Student","Roll","Month","Amount","Status","Due Date","Paid Date","Remarks"])
                for fee in data["fees"]:
                    stu = db.get_student(data, fee.get("student_id",""))
                    w.writerow([stu["name"] if stu else "", stu["roll"] if stu else "",
                                fee.get("month",""), fee.get("amount",""), fee.get("status",""),
                                fee.get("due_date",""), fee.get("paid_date",""), fee.get("remarks","")])
            elif kind == "complaints":
                w.writerow(["Title","Student","Hostel","Category","Priority","Status","Date","Resolution"])
                for c in data["complaints"]:
                    stu = db.get_student(data, c.get("student_id",""))
                    hostel = db.get_hostel(data, c.get("hostel_id",""))
                    w.writerow([c.get("title",""), stu["name"] if stu else c.get("student_name",""),
                                hostel["name"] if hostel else "", c.get("category",""),
                                c.get("priority",""), c.get("status",""),
                                c.get("date",""), c.get("resolution","")])
        messagebox.showinfo("Exported", f"Saved to:\n{path}")
