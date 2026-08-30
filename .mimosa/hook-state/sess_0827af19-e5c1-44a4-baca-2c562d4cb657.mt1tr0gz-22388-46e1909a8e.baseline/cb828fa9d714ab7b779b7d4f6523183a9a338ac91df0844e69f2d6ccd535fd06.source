"""AppConfig.from_env — mode fail-closed clamp, the live gate (M5), .env loading,
and the Fugu key. (from_env previously had zero test coverage — a review finding.)"""

import pytest

pytestmark = pytest.mark.l1

from nbb_cp.app.config import AppConfig
from nbb_cp.kernel.domain import Mode


class TestFromEnv:
    def test_defaults_when_empty(self):
        cfg = AppConfig.from_env({})
        assert cfg.mode is Mode.SHADOW
        assert cfg.global_cap_cents == 3000
        assert cfg.fugu_api_key is None

    def test_unknown_mode_fails_closed_to_shadow(self):
        assert AppConfig.from_env({"NBB_MODE": "production"}).mode is Mode.SHADOW

    def test_live_clamped_to_shadow_without_override(self):
        # SPEC §6: live is unreachable until the Phase-6 gate.
        assert AppConfig.from_env({"NBB_MODE": "live"}).mode is Mode.SHADOW

    def test_live_allowed_with_explicit_override(self):
        cfg = AppConfig.from_env({"NBB_MODE": "live", "NBB_ALLOW_LIVE": "1"})
        assert cfg.mode is Mode.LIVE

    def test_fugu_key_read_from_env(self):
        assert AppConfig.from_env({"FUGU_API_KEY": "secret-xyz"}).fugu_api_key == "secret-xyz"

    def test_cap_override(self):
        assert AppConfig.from_env({"NBB_GLOBAL_CAP_CENTS": "5000"}).global_cap_cents == 5000


class TestDotenv:
    def test_dotenv_fills_config_when_env_is_none(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text(
            "FUGU_API_KEY=fromfile\nNBB_GLOBAL_CAP_CENTS=7000\n", encoding="utf-8"
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("FUGU_API_KEY", raising=False)
        monkeypatch.delenv("NBB_GLOBAL_CAP_CENTS", raising=False)
        cfg = AppConfig.from_env()  # env=None -> reads .env in cwd
        assert cfg.fugu_api_key == "fromfile"
        assert cfg.global_cap_cents == 7000

    def test_real_env_overrides_dotenv(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text("FUGU_API_KEY=fromfile\n", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("FUGU_API_KEY", "fromenv")
        assert AppConfig.from_env().fugu_api_key == "fromenv"

    def test_comments_and_quotes_handled(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text('# comment\nFUGU_API_KEY="quoted-val"\n\n', encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("FUGU_API_KEY", raising=False)
        assert AppConfig.from_env().fugu_api_key == "quoted-val"

    def test_no_dotenv_no_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)  # no .env present
        monkeypatch.delenv("FUGU_API_KEY", raising=False)
        assert AppConfig.from_env().fugu_api_key is None

    def test_dotenv_with_utf8_bom_still_loads_first_key(self, tmp_path, monkeypatch):
        # PowerShell/Notepad write a UTF-8 BOM by default; without utf-8-sig the first
        # key parses as "﻿FUGU_API_KEY" and is silently dropped.
        (tmp_path / ".env").write_text("FUGU_API_KEY=bomkey\n", encoding="utf-8-sig")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("FUGU_API_KEY", raising=False)
        assert AppConfig.from_env().fugu_api_key == "bomkey"
