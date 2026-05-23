"""Retired blocked prototype. Not approved for runtime use or scaffolding."""

from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "Retired prototype: use the hardened outbox dispatcher and canonical async workers "
        "under src/fhirbridge instead of this standalone message-consumer stub."
    )


if __name__ == "__main__":
    main()
