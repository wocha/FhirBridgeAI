"""Retired blocked prototype. Not approved for runtime use or scaffolding."""

from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "Retired prototype: this scenario dispatcher predates the hardened ingestion boundary "
        "and transactional outbox flow. Use the authenticated ingestion API and canonical "
        "runtime workers instead."
    )


if __name__ == "__main__":
    main()
