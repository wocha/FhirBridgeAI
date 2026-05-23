"""Retired legacy verification script.

Direct broker publish outside the transactional outbox is forbidden in the
hardened runtime. This script remains only as an explicit blocked stub.
"""

from __future__ import annotations

import logging

LOGGER = logging.getLogger(__name__)
BLOCK_MESSAGE = (
    "Legacy verification path retired: verify_export.py is not approved for runtime use. "
    "Use runtime-safe integration tests and the outbox dispatcher instead. "
    "Reference: docs/adr/ADR-021-Legacy-Path-Retirement-Decision-Template.md"
)


def main() -> int:
    LOGGER.error(BLOCK_MESSAGE)
    raise SystemExit(BLOCK_MESSAGE)


if __name__ == "__main__":
    main()
