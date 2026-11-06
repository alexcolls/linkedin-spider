"""Tests for configuration loading."""

import pytest

from linkedin_spider.utils.config import Config


@pytest.fixture
def config_file(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(
        "logging:\n"
        "  level: WARNING\n"
        "  file: custom/x.log\n"
        "  console: false\n"
        "export:\n"
        "  data_dir: custom_data\n"
        "  default_format: json\n"
    )
    return path


def test_yaml_settings_are_honoured(config_file):
    config = Config(config_file)

    assert config.log_level == "WARNING"
    assert config.log_file == "custom/x.log"
    assert config.console_logging is False
    assert config.data_dir.name == "custom_data"
    assert config.default_export_format == "json"


def test_defaults_without_yaml(tmp_path):
    config = Config(tmp_path / "missing.yaml")

    assert config.log_level == "INFO"
    assert config.log_file == "logs/linkedin-spider.log"
    assert config.console_logging is True
    assert config.data_dir.name == "data"
    assert config.default_export_format == "csv"


def test_documented_env_vars_override_yaml(config_file, monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    monkeypatch.setenv("LOG_FILE", "env.log")
    monkeypatch.setenv("DATA_DIR", "env_data")
    monkeypatch.setenv("DEFAULT_EXPORT_FORMAT", "excel")

    config = Config(config_file)

    assert config.log_level == "ERROR"
    assert config.log_file == "env.log"
    assert config.data_dir.name == "env_data"
    assert config.default_export_format == "excel"


def test_generic_env_vars_are_ignored(config_file, monkeypatch):
    monkeypatch.setenv("LEVEL", "DEBUG")
    monkeypatch.setenv("FILE", "/etc/passwd")
    monkeypatch.setenv("CONSOLE", "true")
    monkeypatch.setenv("COMMAND", "rm -rf /")
    monkeypatch.setenv("ENABLED", "true")

    config = Config(config_file)

    assert config.log_level == "WARNING"
    assert config.log_file == "custom/x.log"
    assert config.console_logging is False
    assert config.vpn_command == "protonvpn-cli c -r"
    assert config.vpn_enabled is False


@pytest.mark.parametrize("password", ["0123456", "true", "12.5"])
def test_password_stays_exactly_as_written(tmp_path, monkeypatch, password):
    monkeypatch.setenv("LINKEDIN_PASSWORD", password)

    assert Config(tmp_path / "missing.yaml").linkedin_password == password
