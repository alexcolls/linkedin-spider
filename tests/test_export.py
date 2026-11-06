"""Tests for exports, URL files and other files holding sensitive data."""

import csv
import json
import pickle
import stat
import sys
from pathlib import Path

import pytest

from linkedin_spider.models import Profile
from linkedin_spider.utils.export import Exporter, load_urls, save_urls
from linkedin_spider.utils.session import SessionManager
from linkedin_spider.utils.vpn import VPNManager

URL = "https://www.linkedin.com/in/x"
FORMULA = '=HYPERLINK("http://evil.example","click")'


def mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


@pytest.fixture
def exporter(tmp_path):
    return Exporter(tmp_path / "out")


class TestFormulaInjection:
    @pytest.mark.parametrize("payload", [FORMULA, "+1+1", "-1+1", "@SUM(A1)"])
    def test_csv_neutralizes_formulas(self, exporter, payload):
        path = exporter.export([Profile(url=URL, name=payload)], format="csv")

        with open(path, newline="", encoding="utf-8") as f:
            assert next(csv.DictReader(f))["name"] == "'" + payload

    def test_excel_never_writes_a_formula(self, exporter):
        openpyxl = pytest.importorskip("openpyxl")

        path = exporter.export([Profile(url=URL, name=FORMULA)], format="excel")

        cell = openpyxl.load_workbook(path).active["B2"]
        assert cell.data_type == "s"
        assert cell.value == "'" + FORMULA

    def test_json_keeps_the_original_text(self, exporter):
        path = exporter.export([Profile(url=URL, name=FORMULA)], format="json")

        assert json.loads(path.read_text(encoding="utf-8"))[0]["name"] == FORMULA

    def test_ordinary_text_is_untouched(self, exporter):
        path = exporter.export([Profile(url=URL, name="Ana García")], format="csv")

        with open(path, newline="", encoding="utf-8") as f:
            assert next(csv.DictReader(f))["name"] == "Ana García"


class TestExporter:
    @pytest.mark.parametrize("format", ["csv", "json", "excel"])
    def test_exports_are_owner_only(self, exporter, format):
        pytest.importorskip("openpyxl")

        path = exporter.export([Profile(url=URL, name="X")], format=format)

        assert mode(path) == 0o600

    def test_json_round_trip(self, exporter, sample_profiles):
        path = exporter.export(sample_profiles, format="json")

        loaded = [Profile.from_dict(d) for d in json.loads(path.read_text("utf-8"))]
        assert loaded == sample_profiles

    def test_nothing_to_export(self, exporter):
        assert exporter.export([], format="csv") is None

    def test_constructing_creates_nothing(self, tmp_path):
        Exporter(tmp_path / "out")

        assert not (tmp_path / "out").exists()

    def test_unknown_format_is_rejected(self, exporter):
        with pytest.raises(ValueError):
            exporter.check_format("pdf")

    def test_missing_openpyxl_is_caught_up_front(self, exporter, monkeypatch):
        monkeypatch.setitem(sys.modules, "openpyxl", None)

        with pytest.raises(ImportError):
            exporter.check_format("excel")


class TestUrlFiles:
    def test_load_cleans_and_filters(self, tmp_path):
        path = tmp_path / "urls.txt"
        path.write_text(
            "https://es.linkedin.com/in/a/\n"
            "\n"
            "https://www.linkedin.com/in/a?trk=x\n"
            "https://evil.example/in/b\n"
            "https://www.linkedin.com/in/c\n"
        )

        assert load_urls(path) == [
            "https://www.linkedin.com/in/a",
            "https://www.linkedin.com/in/c",
        ]

    def test_save_merges_instead_of_overwriting(self, tmp_path):
        path = tmp_path / "data" / "urls.txt"

        assert save_urls(path, ["https://www.linkedin.com/in/a"]) == 1
        assert save_urls(path, ["https://www.linkedin.com/in/b"]) == 2

        assert load_urls(path) == [
            "https://www.linkedin.com/in/a",
            "https://www.linkedin.com/in/b",
        ]


class TestCookieFiles:
    COOKIES = [{"name": "li_at", "value": "secret"}]

    def test_round_trip_is_json_and_owner_only(self, tmp_path):
        manager = SessionManager(tmp_path / "cookies.json")

        assert manager.save_cookies(self.COOKIES)

        assert json.loads(manager.cookie_path.read_text()) == self.COOKIES
        assert mode(manager.cookie_path) == 0o600
        assert manager.load_cookies() == self.COOKIES

    def test_pickle_file_is_never_executed(self, tmp_path):
        marker = tmp_path / "executed"

        class Payload:
            def __reduce__(self):
                return (Path.touch, (marker,))

        path = tmp_path / "cookies.pkl"
        path.write_bytes(pickle.dumps(Payload()))

        assert SessionManager(path).load_cookies() == []
        assert not marker.exists()

    def test_k8s_secret_is_owner_only(self, tmp_path):
        path = tmp_path / "k8s" / "linkedin-cookies-secret.yaml"

        assert SessionManager().create_k8s_secret_yaml(self.COOKIES, path)

        assert mode(path) == 0o600


class TestVpnCommands:
    @pytest.fixture
    def calls(self, monkeypatch):
        recorded = []

        class Result:
            returncode = 1
            stdout = stderr = ""

        def fake_run(*args, **kwargs):
            recorded.append((args, kwargs))
            return Result()

        monkeypatch.setattr("subprocess.run", fake_run)
        return recorded

    def test_connect_doesnt_use_a_shell(self, calls):
        VPNManager(command="vpn connect; touch /tmp/pwned", enabled=True).connect()

        (args, kwargs) = calls[0]
        assert args[0] == ["vpn", "connect;", "touch", "/tmp/pwned"]
        assert not kwargs.get("shell")

    def test_disconnect_doesnt_kill_other_tunnels(self, calls):
        VPNManager(command="vpn", enabled=True).disconnect()

        assert calls
        for args, kwargs in calls:
            assert "killall" not in args[0]
            assert not kwargs.get("shell")
