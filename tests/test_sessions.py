"""Сборка сбоев, без настоящего settings.json."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from crashpeek.log import parse_payload
from crashpeek.sessions import Event, build_sessions, clip_sessions, format_code, parse_iso, row_kind
from crashpeek.settings import load_days, save_days

TZ = timezone(timedelta(hours=5))


def at(day: int, hour: int, minute: int) -> datetime:
    return datetime(2026, 10, day, hour, minute, tzinfo=TZ)


class ParseTests(unittest.TestCase):
    def test_code_and_payload(self) -> None:
        self.assertEqual(format_code("c0000409"), "0xC0000409")
        with self.assertRaises(Exception):
            parse_payload("ERR отказано в доступе")
        rows = parse_payload('[{"t":"2026-10-26T22:01:51+05:00","id":1000,"src":"crash","p":[]}]')
        self.assertEqual(rows[0]["src"], "crash")
        when = parse_iso("2026-10-26T22:01:51.3599642+05:00")
        self.assertIsNotNone(when)
        self.assertEqual(when.year, 2026)
        self.assertEqual(when.minute, 1)


class SessionTests(unittest.TestCase):
    def test_crash_and_hang_newest_first(self) -> None:
        crash = Event(
            at(26, 22, 1),
            1000,
            "crash",
            (
                "llama-server.exe",
                "0.0.0.0",
                "6ad0f842",
                "ucrtbase.dll",
                "10.0.19041.3636",
                "81cf5d89",
                "c0000409",
                "000000000007286e",
                "47d8",
                "",
                r"D:\llama\b11669\llama-server.exe",
            ),
        )
        hang = Event(
            at(11, 15, 18),
            1002,
            "hang",
            (
                "RobloxPlayerBeta.exe",
                "2.724.0.735",
                "",
                "",
                "",
                r"D:\XboxGames\Roblox\Content\RobloxPlayerBeta.exe",
            ),
        )
        rows = build_sessions([hang, crash])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].app, "llama-server.exe")
        self.assertEqual(row_kind(rows[0]), "сбой")
        self.assertEqual(rows[0].module, "ucrtbase.dll")
        self.assertEqual(rows[0].code, "0xC0000409")
        self.assertEqual(rows[1].kind, "зависание")
        self.assertEqual(rows[1].app, "RobloxPlayerBeta.exe")

    def test_clip_drops_old(self) -> None:
        now = at(28, 20, 0)
        old = Event(at(1, 10, 0), 1000, "crash", ("old.exe",) + ("",) * 10)
        fresh = Event(at(26, 22, 1), 1000, "crash", ("new.exe",) + ("",) * 10)
        shown = clip_sessions(build_sessions([old, fresh]), 14, now)
        self.assertEqual(len(shown), 1)
        self.assertEqual(shown[0].app, "new.exe")

    def test_hang_not_eaten_as_crash(self) -> None:
        hang = Event(at(26, 12, 0), 1002, "crash", ("game.exe", "1", "", "", "", r"C:\game.exe"))
        rows = build_sessions([hang])
        self.assertEqual(rows[0].kind, "зависание")
        self.assertEqual(rows[0].path, r"C:\game.exe")

    def test_clip_naive_now(self) -> None:
        now = datetime(2026, 10, 28, 20, 0, 0)
        item = Event(at(26, 22, 1), 1000, "crash", ("new.exe",) + ("",) * 10)
        shown = clip_sessions(build_sessions([item]), 14, now)
        self.assertEqual(len(shown), 1)


class SettingsTests(unittest.TestCase):
    def test_roundtrip_in_temp(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            save_days(30, root)
            self.assertEqual(load_days(root), 30)
            save_days(3, root)
            self.assertEqual(load_days(root), 14)


if __name__ == "__main__":
    unittest.main()
