# pages/notices.py

import tkinter as tk
from tkinter import messagebox
from datetime import date
from core.theme import *
from core import database as db
from components.widgets import AppButton, Divider, Badge, FormField, FormDropdown, Modal


class NoticesPage(tk.Frame):
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
        tk.Label(hdr, text="Notice Board", bg=BG, fg=TEXT, font=FONT_H1).pack(side="left")
        AppButton(hdr, "Post Notice", lambda: PostNoticeModal(self, self.app),
                  color=ACCENT, icon="📋").pack(side="right")
        Divider(self, pady=6)

        scroll_canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=scroll_canvas.yview)
        inner = tk.Frame(scroll_canvas, bg=BG)
        inner.bind("<Configure>",
                   lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))
        scroll_canvas.create_window((0, 0), window=inner, anchor="nw")
        scroll_canvas.configure(yscrollcommand=sb.set)
        scroll_canvas.pack(side="left", fill="both", expand=True, padx=PAD_PAGE)
        sb.pack(side="right", fill="y")

        for n in sorted(data["notices"], key=lambda x: x.get("date",""), reverse=True):
            self._notice_card(inner, n)

    def _notice_card(self, parent, n):
        data = self.app.data
        hostel = db.get_hostel(data, n.get("hostel_id","")) if n.get("hostel_id") != "ALL" else None
        hostel_name = hostel["name"] if hostel else "All Hostels"

        prio_colors = {"high": DANGER, "medium": ACCENT3, "low": ACCENT}
        prio = n.get("priority","low")
        border_color = prio_colors.get(prio, ACCENT)

        card = tk.Frame(parent, bg=CARD, pady=0)
        card.pack(fill="x", pady=6)

        # Left accent bar
        tk.Frame(card, bg=border_color, width=4).pack(side="left", fill="y")

        body = tk.Frame(card, bg=CARD, padx=16, pady=14)
        body.pack(side="left", fill="both", expand=True)

        top = tk.Frame(body, bg=CARD)
        top.pack(fill="x")
        tk.Label(top, text=n["title"], bg=CARD, fg=TEXT, font=FONT_H3).pack(side="left")
        right = tk.Frame(top, bg=CARD)
        right.pack(side="right")
        Badge(right, prio).pack(side="right", padx=4)
        tk.Label(right, text=n.get("date",""), bg=CARD, fg=DIM, font=FONT_SMALL).pack(side="right", padx=8)

        tk.Label(body, text=f"📌 {hostel_name}", bg=CARD, fg=ACCENT2, font=FONT_SMALL).pack(anchor="w", pady=2)
        tk.Label(body, text=n.get("content",""), bg=CARD, fg=SUBTEXT, font=FONT_BODY,
                 wraplength=700, justify="left").pack(anchor="w", pady=4)

        btn_row = tk.Frame(body, bg=CARD)
        btn_row.pack(anchor="e")
        AppButton(btn_row, "Delete", lambda nid=n["id"]: self._delete(nid), DANGER, small=True).pack()

    def _delete(self, nid):
        if messagebox.askyesno("Delete Notice", "Delete this notice?"):
            self.app.data["notices"] = [n for n in self.app.data["notices"] if n["id"] != nid]
            db.save(self.app.data)
            self.refresh()


class PostNoticeModal(Modal):
    def __init__(self, parent, app):
        super().__init__(parent, "Post New Notice", 520, 400)
        self.app = app
        self._build()

    def _build(self):
        data = self.app.data
        b = self.body
        hostel_options = ["All Hostels"] + [h["name"] for h in data["hostels"]]
        self._hostel_map = {"All Hostels": "ALL", **{h["name"]: h["id"] for h in data["hostels"]}}

        self.f_title    = FormField(b, "Title *", required=True)
        self.f_title.pack(fill="x", pady=5)

        grid = tk.Frame(b, bg=BG)
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1)
        self.f_hostel   = FormDropdown(grid, "For Hostel", hostel_options)
        self.f_hostel.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        self.f_priority = FormDropdown(grid, "Priority", ["low","medium","high"])
        self.f_priority.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        tk.Label(b, text="Content *", bg=BG, fg=SUBTEXT, font=FONT_SMALL).pack(anchor="w", pady=(10,2))
        self.f_content = tk.Text(b, height=5, bg=CARD2, fg=TEXT, font=FONT_BODY,
                                  relief="flat", bd=0, insertbackground=TEXT,
                                  highlightthickness=1, highlightbackground=BORDER)
        self.f_content.pack(fill="x")

        self.add_footer_btn("Cancel", self.destroy, CARD2)
        self.add_footer_btn("Post Notice", self._save, ACCENT)

    def _save(self):
        title = self.f_title.get()
        content = self.f_content.get("1.0","end-1c").strip()
        if not title or not content:
            messagebox.showerror("Required","Title and content are required."); return
        n = {
            "id":        db.new_id("N"),
            "title":     title,
            "content":   content,
            "hostel_id": self._hostel_map.get(self.f_hostel.get(), "ALL"),
            "priority":  self.f_priority.get(),
            "date":      date.today().isoformat(),
        }
        self.app.data["notices"].append(n)
        db.save(self.app.data)
        self.destroy()
        self.master.refresh()
