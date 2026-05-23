from __future__ import annotations

import asyncio

from fhirbridge.core.auth import ExternalUserClaims
from fhirbridge.core.database import Job, ReadModelState
from fhirbridge.ingestion import api
from tests.runtime_fakes import RuntimeStore, fake_database_bundle, fake_fetch_read_model_state_async


def test_dashboard_read_model_endpoint_returns_materialized_versions(monkeypatch) -> None:
    store = RuntimeStore()
    job = Job(
        document_id="doc-dashboard",
        filepath="doc-dashboard.txt",
        tenant_scope="tenant-a",
        actor_id="actor-a",
        status="FHIR_GENERATED",
        aggregate_version=4,
        required_read_version=4,
    )
    projection = ReadModelState(
        projection_name="dashboard",
        job_id=1,
        required_version=4,
        visible_version=3,
        status="FHIR_GENERATED",
    )
    store.add(job)
    projection.job_id = int(job.id)
    store.add(projection)

    monkeypatch.setattr(api, "_get_database", lambda: fake_database_bundle(store))
    monkeypatch.setattr(api, "fetch_read_model_state_async", fake_fetch_read_model_state_async)

    user = ExternalUserClaims(sub="doctor-1", tenant_scope="tenant-a", roles=["PHYSICIAN"])
    response = asyncio.run(api.get_dashboard_read_model(job_id=int(job.id), document_id=None, user=user))

    assert response.job_id == int(job.id)
    assert response.required_version == 4
    assert response.visible_version == 3
