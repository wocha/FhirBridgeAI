"""Retired legacy helper. Not approved for runtime use."""

from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "Retired legacy helper: enqueue_test_jobs.py is not approved for runtime use. "
        "Use the authenticated ingestion API and transactional outbox path instead."
    )


if __name__ == "__main__":
    main()
