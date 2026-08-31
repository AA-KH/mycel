"""
Invite Code Management Module - Invite code validation and login records
"""

import json
import csv
import time
from datetime import datetime

from .config import INVITE_CODES_FILE, LOGIN_RECORDS_FILE


def load_invite_codes():
    """Load invite code data"""
    if INVITE_CODES_FILE.exists():
        with open(INVITE_CODES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"codes": [], "login_records": []}


def save_invite_codes(data):
    """Save invite code data"""
    with open(INVITE_CODES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def verify_invite_code(code: str) -> bool:
    """Verify if the invite code is valid"""
    data = load_invite_codes()
    return code.upper() in [c.upper() for c in data.get("codes", [])]


def init_login_csv():
    """Initialize login record CSV file (if not exists)"""
    if not LOGIN_RECORDS_FILE.exists():
        with open(LOGIN_RECORDS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'InviteCode', 'LoginDate', 'LoginTime', 'Timestamp'])
        print(f"[Init] Created login record file: {LOGIN_RECORDS_FILE}")


def get_next_record_id():
    """Get the next record ID"""
    if not LOGIN_RECORDS_FILE.exists():
        return 1

    with open(LOGIN_RECORDS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        if len(rows) <= 1:  # Only header or empty file
            return 1
        return len(rows)  # ID = row count (excluding header)


def record_login(code: str):
    """Record login info to CSV file"""
    # Ensure CSV file exists
    init_login_csv()

    now = datetime.now()
    record_id = get_next_record_id()

    login_record = {
        "id": record_id,
        "invite_code": code.upper(),
        "login_date": now.strftime("%Y-%m-%d"),
        "login_time": now.strftime("%H:%M:%S"),
        "timestamp": int(time.time())
    }

    # Write to CSV
    with open(LOGIN_RECORDS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            login_record["id"],
            login_record["invite_code"],
            login_record["login_date"],
            login_record["login_time"],
            login_record["timestamp"]
        ])

    # Also save to JSON for backward compatibility
    data = load_invite_codes()
    data["login_records"].append({
        "invite_code": login_record["invite_code"],
        "login_time": now.isoformat(),
        "timestamp": login_record["timestamp"]
    })
    save_invite_codes(data)

    print(f"[Login Record] #{record_id} Invite Code: {code}, Date: {login_record['login_date']}, Time: {login_record['login_time']}")


def get_login_records_from_csv():
    """Read login records from CSV file"""
    if not LOGIN_RECORDS_FILE.exists():
        return []

    records = []
    with open(LOGIN_RECORDS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records
