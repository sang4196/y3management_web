"""Exact input codecs; limits describe representation, not business wage caps."""

import hashlib
import json
import re
import unicodedata
from dataclasses import replace
from datetime import date
from uuid import UUID

from y3management.contracts import Rejected
from y3management.workforce.public import RegisterTrainer


def label(value: str, limit: int) -> str:
    if (
        not isinstance(value, str)
        or len(value) > limit
        or any(unicodedata.category(c) in {"Cc", "Cs"} for c in value)
        or not value.strip()
    ):
        raise Rejected(422, "invalid_request")
    return value.strip()


def money(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"(?:0|[1-9][0-9]{0,1023})", value) is None:
        raise Rejected(422, "invalid_request")
    return value


def month(value: str) -> date:
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{4}-(?:0[1-9]|1[0-2])", value) is None:
        raise Rejected(422, "invalid_request")
    try:
        return date(int(value[:4]), int(value[5:]), 1)
    except ValueError:
        raise Rejected(422, "invalid_request") from None


def normalize(c: RegisterTrainer) -> RegisterTrainer:
    if (
        type(c.rate_percent) is not int
        or not 0 <= c.rate_percent <= 100
        or not isinstance(c.operation_id, UUID)
        or not isinstance(c.home_branch_id, UUID)
    ):
        raise Rejected(422, "invalid_request")
    month(c.base_salary_start_month)
    return replace(
        c,
        name=label(c.name, 200),
        phone=label(c.phone, 128),
        fixed_amount_won=money(c.fixed_amount_won),
        base_salary_won=money(c.base_salary_won),
    )


def fingerprint(c: RegisterTrainer) -> bytes:
    payload = [
        1,
        c.name,
        c.phone,
        str(c.home_branch_id),
        c.rate_percent,
        c.fixed_amount_won,
        c.base_salary_won,
        c.base_salary_start_month,
    ]
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    ).digest()
