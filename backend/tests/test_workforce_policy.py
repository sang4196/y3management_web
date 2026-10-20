"""Exact policy codecs and safe no-JS form contract."""

from dataclasses import replace
from typing import Any
from uuid import uuid4

import pytest

from y3management.contracts import Rejected
from y3management.http import workforce_page
from y3management.workforce.public import RegisterTrainer
from y3management.workforce.validation import fingerprint, normalize


def command() -> RegisterTrainer:
    return RegisterTrainer(
        uuid4(), "가상 이름", "+82 (0) 123", uuid4(), 0, "0", "9" * 1024, "9999-12"
    )


def test_exact_and_canonical() -> None:
    c = command()
    assert normalize(c) == c
    assert fingerprint(c) == fingerprint(normalize(replace(c, name="  가상 이름  ")))
    assert fingerprint(c) != fingerprint(replace(c, base_salary_won="0"))
    assert (
        normalize(replace(c, base_salary_start_month="0001-01")).base_salary_start_month
        == "0001-01"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("fixed_amount_won", ""),
        ("fixed_amount_won", "1.1"),
        ("fixed_amount_won", "01"),
        ("fixed_amount_won", "1e3"),
        ("fixed_amount_won", "NaN"),
        ("fixed_amount_won", "9" * 1025),
        ("rate_percent", True),
        ("rate_percent", 101),
        ("phone", "  "),
        ("name", "a\x00"),
        ("name", "\ud800"),
        ("base_salary_start_month", "0000-01"),
        ("base_salary_start_month", "2026-13"),
    ],
)
def test_reject_without_coercion(field: str, value: Any) -> None:
    with pytest.raises(Rejected):
        normalize(replace(command(), **{field: value}))


def test_form_no_get_fallback() -> None:
    page = workforce_page()
    assert 'method="post" action="/api/v1/admin/trainers"' in page
    assert '<fieldset id="fields" disabled>' in page
    assert '<button id="submit" disabled>' in page


@pytest.mark.parametrize("size,status", [(8192, 200), (8193, 413)])
def test_body_limit_actual_asgi_chunks(size: int, status: int) -> None:
    """Feed separate receive messages, no Content-Length (not TestClient coalescing)."""
    import asyncio

    from starlette.types import Message, Receive, Scope, Send

    from y3management.http import BodyLimit

    sent: list[Message] = []
    chunks = [b" " * 3000, b" " * 3000, b" " * (size - 6000)]
    consumed = 0

    async def receive() -> Message:
        nonlocal consumed
        value = chunks[consumed]
        consumed += 1
        return {"type": "http.request", "body": value, "more_body": consumed < 3}

    async def send(message: Message) -> None:
        sent.append(message)

    async def inner(scope: Scope, receive: Receive, send: Send) -> None:
        message = await receive()
        assert len(message["body"]) == 8192
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    asyncio.run(
        BodyLimit(inner)(
            {"type": "http", "path": "/api/v1/admin/trainers", "headers": []}, receive, send
        )
    )
    assert consumed == 3 and sent[0]["status"] == status
