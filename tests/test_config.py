from unittest.mock import patch

from wisdom_digest.config import load_settings, parse_bool


def test_config_defaults_are_safe():
    clear_env = {
        "DEFAULT_TIMEZONE": "",
        "DRY_RUN": "",
        "WRITE_DRY_RUN_LOGS": "",
        "DIGEST_SLOT": "",
        "LOG_LEVEL": "",
    }

    with patch.dict("os.environ", clear_env, clear=True):
        settings = load_settings()

    assert settings.default_timezone == "Pacific/Auckland"
    assert settings.dry_run is True
    assert settings.write_dry_run_logs is False
    assert settings.digest_slot is None
    assert settings.log_level == "INFO"


def test_parse_bool_accepts_common_values():
    assert parse_bool("true") is True
    assert parse_bool("1") is True
    assert parse_bool("false") is False
    assert parse_bool("0") is False
