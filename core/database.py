# core/database.py  —  JSON-backed persistence layer

import json, os, uuid
from datetime import date, datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "hostel.json")

# ── Default seed data ──────────────────────────────────────────────────────────
_DEFAULTS = {
    "hostels": [
        {"id": "H1", "name": "Sunrise Block",  "type": "Boys",   "floors": 4, "warden": "Mr. Ramesh Kumar",   "contact": "9876543210"},
        {"id": "H2", "name": "Lotus Block",    "type": "Girls",  "floors": 3, "warden": "Ms. Priya Sharma",   "contact": "9876543211"},
        {"id": "H3", "name": "Everest Block",  "type": "Boys",   "floors": 5, "warden": "Mr. Suresh Patel",   "contact": "9876543212"},
    ],
    "rooms": [
        # H1 – Sunrise
        {"id":"R101","hostel_id":"H1","number":"101","floor":1,"type":"Single","capacity":1,"status":"occupied","amenities":["AC","WiFi","Attached Bathroom"],"rent":6000},
        {"id":"R102","hostel_id":"H1","number":"102","floor":1,"type":"Double","capacity":2,"status":"available","amenities":["WiFi","Common Bathroom"],"rent":4500},
        {"id":"R103","hostel_id":"H1","number":"103","floor":1,"type":"Triple","capacity":3,"status":"occupied","amenities":["Fan","Common Bathroom"],"rent":3200},
        {"id":"R201","hostel_id":"H1","number":"201","floor":2,"type":"Double","capacity":2,"status":"maintenance","amenities":["AC","WiFi"],"rent":5000},
        {"id":"R202","hostel_id":"H1","number":"202","floor":2,"type":"Single","capacity":1,"status":"available","amenities":["AC","WiFi","Attached Bathroom"],"rent":6000},
        # H2 – Lotus
        {"id":"R301","hostel_id":"H2","number":"301","floor":1,"type":"Single","capacity":1,"status":"available","amenities":["AC","WiFi","Attached Bathroom"],"rent":6500},
        {"id":"R302","hostel_id":"H2","number":"302","floor":1,"type":"Double","capacity":2,"status":"occupied","amenities":["Fan","WiFi"],"rent":4000},
        {"id":"R303","hostel_id":"H2","number":"303","floor":2,"type":"Triple","capacity":3,"status":"available","amenities":["AC","WiFi","Common Bathroom"],"rent":3800},
        # H3 – Everest
        {"id":"R401","hostel_id":"H3","number":"401","floor":1,"type":"Double","capacity":2,"status":"occupied","amenities":["AC","WiFi"],"rent":5200},
        {"id":"R402","hostel_id":"H3","number":"402","floor":1,"type":"Single","capacity":1,"status":"available","amenities":["Fan","WiFi"],"rent":4800},
        {"id":"R403","hostel_id":"H3","number":"403","floor":2,"type":"Triple","capacity":3,"status":"occupied","amenities":["AC","WiFi","Attached Bathroom"],"rent":3500},
    ],
    "students": [
        {"id":"S001","name":"Arjun Mehta",    "roll":"21CS001","course":"B.Tech CSE","year":2,"hostel_id":"H1","room_id":"R101","phone":"9111111111","email":"arjun@college.edu","guardian":"Rajesh Mehta","guardian_phone":"9222222222","join_date":"2024-07-15","dob":"2003-05-10"},
        {"id":"S002","name":"Vikram Singh",   "roll":"21ME002","course":"B.Tech ME", "year":2,"hostel_id":"H1","room_id":"R103","phone":"9111111112","email":"vikram@college.edu","guardian":"Suresh Singh","guardian_phone":"9222222223","join_date":"2024-07-16","dob":"2003-08-22"},
        {"id":"S003","name":"Priya Nair",     "roll":"22EC001","course":"B.Tech ECE","year":1,"hostel_id":"H2","room_id":"R302","phone":"9111111113","email":"priya@college.edu","guardian":"Mohan Nair","guardian_phone":"9222222224","join_date":"2024-07-18","dob":"2004-03-14"},
        {"id":"S004","name":"Rohit Sharma",   "roll":"21CS010","course":"B.Tech CSE","year":2,"hostel_id":"H3","room_id":"R401","phone":"9111111114","email":"rohit@college.edu","guardian":"Anil Sharma","guardian_phone":"9222222225","join_date":"2024-07-15","dob":"2003-11-05"},
        {"id":"S005","name":"Sneha Patel",    "roll":"22ME005","course":"B.Tech ME", "year":1,"hostel_id":"H2","room_id":"R302","phone":"9111111115","email":"sneha@college.edu","guardian":"Girish Patel","guardian_phone":"9222222226","join_date":"2024-07-19","dob":"2004-06-30"},
    ],
    "fees": [],
    "complaints": [],
    "visitors": [],
    "notices": [
        {"id":"N001","title":"Hostel Inauguration","content":"All hostels are now open for AY 2024-25. Welcome students!","date":"2024-07-01","priority":"high","hostel_id":"ALL"},
        {"id":"N002","title":"Water Supply Maintenance","content":"Water supply will be interrupted on 15th from 10AM–2PM.","date":"2024-07-10","priority":"medium","hostel_id":"H1"},
    ],
}


def _ensure_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def load() -> dict:
    _ensure_dir()
    if os.path.exists(DB_PATH):
        with open(DB_PATH) as f:
            return json.load(f)
    save(_DEFAULTS)
    return _DEFAULTS


def save(data: dict):
    _ensure_dir()
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)


def new_id(prefix=""):
    return prefix + str(uuid.uuid4())[:8].upper()


# ── Query helpers ──────────────────────────────────────────────────────────────
def get_hostel(data, hid):
    return next((h for h in data["hostels"] if h["id"] == hid), None)

def get_room(data, rid):
    return next((r for r in data["rooms"] if r["id"] == rid), None)

def get_student(data, sid):
    return next((s for s in data["students"] if s["id"] == sid), None)

def rooms_for_hostel(data, hid):
    return [r for r in data["rooms"] if r["hostel_id"] == hid]

def students_in_room(data, rid):
    return [s for s in data["students"] if s["room_id"] == rid]

def room_occupancy(data, rid):
    return len(students_in_room(data, rid))

def fees_for_student(data, sid):
    return [f for f in data["fees"] if f["student_id"] == sid]

def complaints_for_hostel(data, hid):
    if hid == "ALL":
        return data["complaints"]
    return [c for c in data["complaints"] if c.get("hostel_id") == hid]

def today():
    return date.today().isoformat()
