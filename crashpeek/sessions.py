"""Сборка записей: сбой приложения или зависание."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

_FRAC = re.compile(r"(\.\d{6})\d+")

CRASH_ID = 1000
HANG_ID = 1002


@dataclass
class Event:
    when: datetime
    id: int
    src: str
    props: tuple[str, ...]


@dataclass
class Crash:
    when: datetime
    kind: str
    app: str
    version: str
    module: str
    code: str
    path: str


def clean_text(text: str) -> str:
    return "".join(ch for ch in text if unicodedata.category(ch) != "Cf").strip()


def exe_name(text: str) -> str:
    name = Path(clean_text(text).replace("/", "\\")).name
    return name or clean_text(text)


def format_code(text: str) -> str:
    raw = clean_text(text).lower().replace("0x", "")
    if not raw:
        return ""
    try:
        value = int(raw, 16)
    except ValueError:
        return clean_text(text)
    return f"0x{value:08X}"


def parse_iso(text: str) -> datetime | None:
    raw = clean_text(str(text)).replace("Z", "+00:00")
    if not raw:
        return None
    raw = _FRAC.sub(r"\1", raw)
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _stamp(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def _is_hang(item: Event) -> bool:
    if item.src == "hang" or item.id == HANG_ID:
        return True
    return False


def _is_crash(item: Event) -> bool:
    return item.src == "crash" or item.id == CRASH_ID


def build_sessions(events: list[Event]) -> list[Crash]:
    rows: list[Crash] = []
    for item in events:
        if _is_hang(item):
            app = exe_name(item.props[0]) if item.props else ""
            version = clean_text(item.props[1]) if len(item.props) > 1 else ""
            path = clean_text(item.props[5]) if len(item.props) > 5 else ""
            rows.append(
                Crash(
                    when=item.when,
                    kind="зависание",
                    app=app or "журнал не записал",
                    version=version,
                    module="",
                    code="",
                    path=path,
                )
            )
            continue
        if not _is_crash(item):
            continue
        app = exe_name(item.props[0]) if item.props else ""
        version = clean_text(item.props[1]) if len(item.props) > 1 else ""
        module = exe_name(item.props[3]) if len(item.props) > 3 else ""
        code = format_code(item.props[6]) if len(item.props) > 6 else ""
        path = clean_text(item.props[10]) if len(item.props) > 10 else ""
        rows.append(
            Crash(
                when=item.when,
                kind="сбой",
                app=app or "журнал не записал",
                version=version,
                module=module,
                code=code,
                path=path,
            )
        )
    rows.sort(key=lambda item: _stamp(item.when), reverse=True)
    return rows


def clip_sessions(rows: list[Crash], days: int, now: datetime) -> list[Crash]:
    cutoff = _stamp(now) - timedelta(days=days)
    visible = [item for item in rows if _stamp(item.when) >= cutoff]
    visible.sort(key=lambda item: _stamp(item.when), reverse=True)
    return visible


def row_kind(item: Crash) -> str:
    return item.kind


_MONTHS = "янв фев мар апр май июн июл авг сен окт ноя дек".split()


def format_when(moment: datetime) -> str:
    local = moment.astimezone() if moment.tzinfo else moment
    return f"{local.day} {_MONTHS[local.month - 1]}, {local:%H:%M}"
