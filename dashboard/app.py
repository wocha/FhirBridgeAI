"""
KRITIS observability dashboard for FhirBridgeAI.

Security model:
- Dashboard is reachable only behind oauth2-proxy.
- Identity is accepted only from trusted proxy headers.
- Queue status is read from Prometheus (not RabbitMQ Management API).
"""

import logging
import os
from typing import Any
from urllib.parse import urlparse

import httpx
import pandas as pd
import streamlit as st

from fhirbridge.core.read_models import (
    bind_materialized_read_model,
    evaluate_materialized_version_gate,
)

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="FhirBridgeAI Observability",
    page_icon="H",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .stApp { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    </style>
    """,
    unsafe_allow_html=True,
)

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
PROMETHEUS_TIMEOUT = float(os.getenv("PROMETHEUS_TIMEOUT_SECONDS", "5"))
REQUIRED_PROXY_HEADER = os.getenv("DASHBOARD_REQUIRED_PROXY_HEADER", "X-Auth-Request-User")
DASHBOARD_API_BASE_URL = os.getenv("DASHBOARD_API_BASE_URL", "")
DASHBOARD_API_CA_BUNDLE_PATH = os.getenv("DASHBOARD_API_CA_BUNDLE_PATH", "")
DASHBOARD_API_TIMEOUT = float(os.getenv("DASHBOARD_API_TIMEOUT_SECONDS", "5"))


def _require_https_api_base_url() -> str:
    base_url = DASHBOARD_API_BASE_URL.strip()
    if not base_url:
        raise RuntimeError("DASHBOARD_API_BASE_URL is required")
    parsed = urlparse(base_url)
    if parsed.scheme.lower() != "https":
        raise RuntimeError("DASHBOARD_API_BASE_URL must use https://")
    if not parsed.netloc:
        raise RuntimeError("DASHBOARD_API_BASE_URL must include a host")
    return base_url.rstrip("/")


def _require_api_ca_bundle_path() -> str:
    bundle_path = DASHBOARD_API_CA_BUNDLE_PATH.strip()
    if not bundle_path:
        raise RuntimeError("DASHBOARD_API_CA_BUNDLE_PATH is required for dashboard API TLS")
    if not os.path.isfile(bundle_path):
        raise RuntimeError("DASHBOARD_API_CA_BUNDLE_PATH must point to an existing CA bundle")
    return bundle_path


API_BASE_URL = _require_https_api_base_url()
API_CA_BUNDLE_PATH = _require_api_ca_bundle_path()


def _read_headers() -> dict[str, str]:
    try:
        headers = st.context.headers
        return dict(headers.items())
    except AttributeError:
        try:
            from streamlit.web.server.websocket_headers import _get_websocket_headers

            return _get_websocket_headers() or {}
        except Exception:
            return {}


def _header_value(headers: dict[str, str], key: str) -> str:
    for candidate in (key, key.lower()):
        if candidate in headers and headers[candidate]:
            return str(headers[candidate]).strip()
    return ""


def _derive_identity(headers: dict[str, str]) -> tuple[str, str]:
    proxy_user = _header_value(headers, REQUIRED_PROXY_HEADER)
    if not proxy_user:
        raise PermissionError(
            f"Required trusted proxy header '{REQUIRED_PROXY_HEADER}' is missing."
        )

    forwarded_user = _header_value(headers, "X-Forwarded-User")
    if forwarded_user and forwarded_user != proxy_user:
        raise PermissionError(
            "Header mismatch between trusted proxy identity and forwarded user."
        )

    roles_raw = _header_value(headers, "X-Auth-Request-Groups") or _header_value(
        headers, "X-Forwarded-Groups"
    )
    role = "auditor" if "auditor" in roles_raw.lower() else "viewer"
    return proxy_user, role


@st.cache_data(ttl=10)
def _prom_query(query: str) -> list[dict[str, Any]]:
    response = httpx.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": query},
        timeout=PROMETHEUS_TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "success":
        raise RuntimeError(f"Prometheus query failed: {payload}")
    return payload.get("data", {}).get("result", [])


def _as_float(result_item: dict[str, Any]) -> float:
    value = result_item.get("value", [0, "0"])  # [timestamp, value]
    try:
        return float(value[1])
    except (IndexError, ValueError, TypeError):
        return 0.0


@st.cache_data(ttl=10)
def fetch_queue_metrics() -> list[dict[str, Any]]:
    ready_rows = _prom_query("rabbitmq_queue_messages_ready")
    unacked_rows = _prom_query("rabbitmq_queue_messages_unacked")
    consumer_rows = _prom_query("rabbitmq_queue_consumers")

    queue_map: dict[str, dict[str, Any]] = {}

    def ensure_queue(name: str) -> dict[str, Any]:
        if name not in queue_map:
            queue_map[name] = {
                "queue": name,
                "messages_ready": 0,
                "messages_unacked": 0,
                "consumers": 0,
                "is_dlq": "dlx" in name.lower() or "dead" in name.lower(),
            }
        return queue_map[name]

    for row in ready_rows:
        queue_name = row.get("metric", {}).get("queue", "unknown")
        ensure_queue(queue_name)["messages_ready"] = int(_as_float(row))

    for row in unacked_rows:
        queue_name = row.get("metric", {}).get("queue", "unknown")
        ensure_queue(queue_name)["messages_unacked"] = int(_as_float(row))

    for row in consumer_rows:
        queue_name = row.get("metric", {}).get("queue", "unknown")
        ensure_queue(queue_name)["consumers"] = int(_as_float(row))

    return sorted(queue_map.values(), key=lambda entry: entry["queue"])


def render_pipeline_overview(queue_rows: list[dict[str, Any]]) -> None:
    st.header("Pipeline Overview")

    total_queues = len(queue_rows)
    total_ready = sum(int(row["messages_ready"]) for row in queue_rows)
    total_unacked = sum(int(row["messages_unacked"]) for row in queue_rows)
    total_consumers = sum(int(row["consumers"]) for row in queue_rows)
    total_dlq_messages = sum(
        int(row["messages_ready"]) for row in queue_rows if bool(row.get("is_dlq"))
    )

    cols = st.columns(5)
    cols[0].metric("Queues", total_queues)
    cols[1].metric("Messages Ready", total_ready)
    cols[2].metric("Messages Unacked", total_unacked)
    cols[3].metric("Consumers", total_consumers)
    cols[4].metric("DLQ Messages", total_dlq_messages)

    if total_dlq_messages > 0:
        st.error(
            f"Alert: {total_dlq_messages} message(s) are currently in dead-letter queues."
        )
    else:
        st.success("No dead-letter queue backlog detected.")


def render_message_queues(queue_rows: list[dict[str, Any]]) -> None:
    st.header("Message Queues")

    if not queue_rows:
        st.info("No queue metrics returned by Prometheus.")
        return

    df = pd.DataFrame(queue_rows)
    df = df[["queue", "messages_ready", "messages_unacked", "consumers", "is_dlq"]]
    df.columns = ["Queue", "Messages Ready", "Messages Unacked", "Consumers", "DLQ"]

    st.dataframe(df, use_container_width=True, hide_index=True)


def render_security_posture(username: str, role: str) -> None:
    st.header("Security Posture")
    st.markdown("**Enforced controls in this dashboard runtime:**")
    st.markdown("- Identity accepted only from trusted oauth2-proxy headers.")
    st.markdown("- Queue state sourced from Prometheus, not RabbitMQ admin API.")
    st.markdown("- Read-model policy sourced from the backend read-model endpoint, not URL parameters.")
    st.markdown(f"- Active principal: `{username}` (`{role}`).")


def _forward_bearer_token(headers: dict[str, str]) -> str:
    direct_authorization = _header_value(headers, "Authorization")
    if direct_authorization.lower().startswith("bearer "):
        return direct_authorization

    for candidate in ("X-Forwarded-Access-Token", "X-Auth-Request-Access-Token"):
        token = _header_value(headers, candidate)
        if token:
            return token if token.lower().startswith("bearer ") else f"Bearer {token}"
    return ""


@st.cache_data(ttl=5, show_spinner=False)
def fetch_dashboard_read_model_state(
    *,
    bearer_token: str,
    job_id: int | None,
    document_id: str | None,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if job_id is not None:
        params["job_id"] = job_id
    if document_id:
        params["document_id"] = document_id

    response = httpx.get(
        f"{API_BASE_URL}/api/v1/read-models/dashboard",
        params=params,
        headers={"Authorization": bearer_token},
        timeout=DASHBOARD_API_TIMEOUT,
        verify=API_CA_BUNDLE_PATH,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=5, show_spinner=False)
def fetch_manual_review_state(*, bearer_token: str, job_id: int) -> dict[str, Any]:
    response = httpx.get(
        f"{API_BASE_URL}/api/v1/manual-review/{job_id}",
        headers={"Authorization": bearer_token},
        timeout=DASHBOARD_API_TIMEOUT,
        verify=API_CA_BUNDLE_PATH,
    )
    response.raise_for_status()
    return response.json()


def submit_manual_review_decision(*, bearer_token: str, job_id: int, decision: str, notes: str) -> dict[str, Any]:
    response = httpx.post(
        f"{API_BASE_URL}/api/v1/manual-review/{job_id}/decision",
        headers={"Authorization": bearer_token},
        json={"decision": decision, "notes": notes or None},
        timeout=DASHBOARD_API_TIMEOUT,
        verify=API_CA_BUNDLE_PATH,
    )
    response.raise_for_status()
    return response.json()


def render_read_model_gate(headers: dict[str, str]) -> None:
    st.header("Read Model Gate")

    job_id_raw = st.query_params.get("job_id")
    document_id = st.query_params.get("document_id")
    requested_raw = st.query_params.get("required_version")

    if job_id_raw is None and document_id is None:
        st.info(
            "Pass `job_id` or `document_id` and optionally `required_version` to evaluate "
            "the materialized dashboard read model."
        )
        return

    try:
        job_id = int(job_id_raw) if job_id_raw is not None else None
    except ValueError:
        st.error("`job_id` must be an integer.")
        return

    requested_version: int | None = None
    if requested_raw is not None:
        try:
            requested_version = int(requested_raw)
        except ValueError:
            st.error("`required_version` must be an integer when provided.")
            return

    bearer_token = _forward_bearer_token(headers)
    if not bearer_token:
        st.error("Clinical read-model policy cannot be evaluated because no access token reached the dashboard.")
        return

    try:
        state = bind_materialized_read_model(
            fetch_dashboard_read_model_state(
                bearer_token=bearer_token,
                job_id=job_id,
                document_id=document_id,
            )
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            st.warning("No materialized dashboard projection exists yet for this document.")
            return
        st.error(f"Read-model endpoint rejected the request: {exc}")
        return
    except Exception as exc:
        logger.warning("Read-model lookup failed: %s", exc)
        st.error(f"Unable to query the materialized read model: {exc}")
        return

    gate = evaluate_materialized_version_gate(
        actual_required_version=state.required_version,
        visible_version=state.visible_version,
        requested_version=requested_version,
    )
    st.metric("Requested Version", requested_version if requested_version is not None else state.required_version)
    st.metric("Materialized Required", gate.actual_required_version)
    st.metric("Visible Version", gate.visible_version)
    if gate.allowed:
        st.success(gate.message)
        st.caption(f"Clinical view unlocked for job {state.job_id} ({state.document_id}).")
    else:
        st.error(gate.message)
        st.caption(
            "Clinical content remains hidden until the backend projection reaches the required version."
        )


def render_manual_review(headers: dict[str, str], role: str) -> None:
    st.header("Manual Review")

    if role != "auditor":
        st.error("Manual review controls are limited to auditor sessions behind oauth2-proxy.")
        return

    job_id_raw = st.query_params.get("job_id")
    if job_id_raw is None:
        st.info("Pass `job_id` to open a backend-mediated manual review case.")
        return

    try:
        job_id = int(job_id_raw)
    except ValueError:
        st.error("`job_id` must be an integer.")
        return

    bearer_token = _forward_bearer_token(headers)
    if not bearer_token:
        st.error("Manual review cannot run because no access token reached the dashboard.")
        return

    try:
        review = fetch_manual_review_state(bearer_token=bearer_token, job_id=job_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            st.warning("No manual review case exists yet for this job.")
            return
        if exc.response.status_code == 403:
            st.error("The backend rejected this review request due to RBAC policy.")
            return
        st.error(f"Manual review endpoint rejected the request: {exc}")
        return
    except Exception as exc:
        logger.warning("Manual review lookup failed: %s", exc)
        st.error(f"Unable to query the manual review endpoint: {exc}")
        return

    meta_cols = st.columns(4)
    meta_cols[0].metric("Job", review["job_id"])
    meta_cols[1].metric("Review Status", review["review_status"])
    meta_cols[2].metric("Job Status", review["job_status"])
    meta_cols[3].metric("Visible Version", review["visible_version"])

    st.caption(
        f"Source: `{review['source_kind']}` | File: `{review['submitted_filename']}` | "
        f"Evidence SHA-256: `{review.get('evidence_sha256') or 'n/a'}`"
    )
    st.info(
        f"Qdrant remains advisory-only here: {review['qdrant_reason']} "
        f"({review['qdrant_blocking_adr'] or 'no blocking ADR'})."
    )

    if review.get("pseudonymized_preview"):
        st.subheader("Pseudonymized Preview")
        st.text_area(
            "Review Source",
            review["pseudonymized_preview"],
            height=240,
            disabled=True,
        )

    if review.get("extracted_bundle_json"):
        st.subheader("Extracted Bundle")
        st.code(review["extracted_bundle_json"], language="json")

    decision = st.selectbox(
        "Decision",
        options=[("approve", "Approve export"), ("reject", "Reject to quarantine")],
        format_func=lambda option: option[1],
    )
    notes = st.text_area("Review Notes", max_chars=2000, placeholder="Why are you approving or rejecting this case?")

    if st.button("Submit Review Decision", type="primary"):
        try:
            result = submit_manual_review_decision(
                bearer_token=bearer_token,
                job_id=job_id,
                decision=decision[0],
                notes=notes,
            )
            st.cache_data.clear()
            st.success(result["message"])
        except httpx.HTTPStatusError as exc:
            st.error(f"Manual review submission failed: {exc}")
        except Exception as exc:
            logger.warning("Manual review submission failed: %s", exc)
            st.error(f"Unable to submit the manual review decision: {exc}")


headers = _read_headers()
try:
    current_user, current_role = _derive_identity(headers)
except PermissionError as exc:
    st.error(f"Access denied: {exc}")
    st.stop()

st.sidebar.success(f"Authenticated as {current_user} ({current_role})")

page = st.sidebar.radio(
    "Navigation",
    [
        "Pipeline Overview",
        "Message Queues",
        "Security Posture",
        "Read Model Gate",
        "Manual Review",
    ],
)

if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()

st.title("FhirBridgeAI Observability Dashboard")
st.caption("Zero-trust dashboard path with Prometheus-backed queue observability.")

queue_metrics: list[dict[str, Any]] = []
try:
    queue_metrics = fetch_queue_metrics()
except Exception as exc:
    logger.warning("Prometheus queue metrics unavailable: %s", exc)
    st.warning(f"Prometheus metrics are currently unavailable: {exc}")

if page == "Pipeline Overview":
    render_pipeline_overview(queue_metrics)
elif page == "Message Queues":
    render_message_queues(queue_metrics)
elif page == "Read Model Gate":
    render_read_model_gate(headers)
elif page == "Manual Review":
    render_manual_review(headers, current_role)
else:
    render_security_posture(current_user, current_role)
