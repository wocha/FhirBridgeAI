from __future__ import annotations

import asyncio

from fhirbridge.core.outbox_dispatcher import run_dispatcher


if __name__ == "__main__":
    asyncio.run(run_dispatcher())
