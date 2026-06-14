import logging

from wisdom_digest.logging_utils import configure_logging, mask_email


def test_mask_email_preserves_domain_and_masks_local_part():
    assert mask_email("person@example.com") == "p***n@example.com"


def test_mask_email_handles_short_or_invalid_values():
    assert mask_email("ab@example.com") == "***@example.com"
    assert mask_email("invalid") == "***"


def test_configure_logging_suppresses_http_client_info_logs():
    configure_logging("INFO")

    assert logging.getLogger("httpx").getEffectiveLevel() == logging.WARNING
    assert logging.getLogger("httpcore").getEffectiveLevel() == logging.WARNING
