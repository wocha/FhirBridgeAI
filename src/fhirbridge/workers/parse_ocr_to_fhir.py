"""Retired legacy entrypoint.

This path is intentionally blocked. See ADR-021 for the retirement decision
and the hardened replacement path via the transactional worker runtime.
"""

from __future__ import annotations

import logging

LOGGER = logging.getLogger(__name__)
BLOCK_MESSAGE = (
    "Legacy path retired: parse_ocr_to_fhir.py is not approved for runtime use. "
    "Use the async worker pipeline with transactional outbox and claim-check storage instead. "
    "Reference: docs/adr/ADR-021-Legacy-Path-Retirement-Decision-Template.md"
)


def main() -> int:
    LOGGER.error(BLOCK_MESSAGE)
    raise SystemExit(BLOCK_MESSAGE)


if __name__ == "__main__":
    main()
