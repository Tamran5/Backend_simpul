# app/utils/helpers.py

from datetime import date, datetime, timezone

MONTHS_ID = [
    '', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
    'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des',
]


def format_date_display(d: date) -> str:
    """date → '14 Jun 2026'"""
    return f"{d.day} {MONTHS_ID[d.month]} {d.year}"


def date_to_epoch(d: date) -> int:
    """date → Unix timestamp (awal hari, UTC)"""
    dt = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    return int(dt.timestamp())


def to_initials(name: str) -> str:
    """'Rizky Aditya' → 'RA' | 'Rizky' → 'R'"""
    if not name:
        return '?'
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    return name[0].upper()


def allowed_file(filename: str, allowed: set) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed