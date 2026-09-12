"""Reusable server-side validators (mirrors static/js/validation.js).

Usage:
    errors = validate(form, {
        "full_name": [("required",), ("alpha",)],
        "national_id": [("required",), ("numeric",)],
        "email": [("required",), ("email",)],
        "dob": [("required",), ("date_not_future",)],
    })
    if errors: raise ValidationError(errors)
"""

import re
from datetime import date, datetime

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ALPHA_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]*$")   # letters, spaces, . ' -
_NUMERIC_RE = re.compile(r"^[0-9]+$")
_BEDNUM_RE = re.compile(r"^[A-Za-z]{2,4}-\d{2,3}$")  # e.g. ER-01, ICU-12
_CNIC_RE = re.compile(r"^\d{13}$")                   # exactly 13 digits


class ValidationError(Exception):
    """Carries a list of human-readable field errors."""

    def __init__(self, errors):
        self.errors = errors if isinstance(errors, list) else [errors]
        super().__init__("; ".join(self.errors))


_LABELS = {
    "full_name": "Name", "fname": "First name", "lname": "Last name",
    "national_id": "CNIC", "phone": "Phone", "email": "Email",
    "dob": "Date of birth", "bed_number": "Bed number", "license_no": "License No",
}


def _label(field):
    return _LABELS.get(field, field.replace("_", " ").title())


def _check(rule, value):
    """Return an error fragment for a single rule, or None if valid."""
    v = (value or "").strip()
    name = rule[0]
    if name == "required":
        return "is required" if v == "" else None
    if v == "":
        return None  # other rules pass on empty (use 'required' to forbid empty)
    if name == "alpha":
        return "must contain letters only" if not _ALPHA_RE.match(v) else None
    if name == "numeric":
        return "must contain digits only" if not _NUMERIC_RE.match(v) else None
    if name == "cnic":
        return "must be exactly 13 digits" if not _CNIC_RE.match(v) else None
    if name == "email":
        return "must be a valid email address" if not _EMAIL_RE.match(v) else None
    if name == "bed_number":
        return "must look like 'ER-01'" if not _BEDNUM_RE.match(v) else None
    if name == "min_len":
        return f"must be at least {rule[1]} characters" if len(v) < rule[1] else None
    if name == "max_len":
        return f"must be at most {rule[1]} characters" if len(v) > rule[1] else None
    if name == "positive_int":
        return ("must be a positive whole number"
                if not (_NUMERIC_RE.match(v) and int(v) > 0) else None)
    if name == "non_negative":
        return ("cannot be negative"
                if not (_NUMERIC_RE.match(v) and int(v) >= 0) else None)
    if name == "date_not_future":
        try:
            d = datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            return "must be a valid date (YYYY-MM-DD)"
        return "cannot be in the future" if d > date.today() else None
    if name == "date":
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            return "must be a valid date (YYYY-MM-DD)"
        return None
    return None


def validate(data, rules):
    """Run `rules` against `data` (a dict-like). Return a list of error strings."""
    errors = []
    for field, field_rules in rules.items():
        value = data.get(field) if hasattr(data, "get") else data[field]
        for rule in field_rules:
            frag = _check(rule, value)
            if frag:
                errors.append(f"{_label(field)} {frag}.")
                break  # one error per field
    return errors
