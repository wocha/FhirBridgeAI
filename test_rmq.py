"""Retired legacy RabbitMQ demo. Not approved for runtime use."""

from __future__ import annotations

try:
    import pytest
except ModuleNotFoundError:
    pytest = None

SKIP_REASON = "Retired legacy RabbitMQ demo; use hardened outbox dispatcher tests instead."
pytestmark = pytest.mark.skip(reason=SKIP_REASON) if pytest else ()


def test_retired_rabbitmq_demo_is_disabled() -> None:
    assert True


def main() -> None:
    raise SystemExit(
        "Retired legacy helper: test_rmq.py is not approved for runtime use. "
        "Use the hardened outbox dispatcher and authenticated runtime workers instead."
    )


if __name__ == "__main__":
    main()
