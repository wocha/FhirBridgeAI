"""
KRITIS Observability Dashboard for FhirBridgeAI.

CQRS Read-Only dashboard with RBAC (viewer/auditor) providing:
- Pipeline Overview with KPIs and throughput charts
- RabbitMQ queue health monitoring
- Failed job quarantine inspector
- Job-level audit trail (OCR Input vs FHIR Output)

Air-gapped: No external CDN, no Google Fonts, no tracking.
Run: streamlit run dashboard/app.py
"""

import json
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from fhirbridge.core.database import Job, JobStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. Page Config & KRITIS Air-Gap Styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="FhirBridgeAI – Observability",
    page_icon="🏥",
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

# ---------------------------------------------------------------------------
# 2. RBAC Authentication
# ---------------------------------------------------------------------------
CREDENTIALS: dict[str, Any] = {
    "usernames": {
        "viewer": {
            "email": "viewer@fhirbridge.local",
            "name": "Viewer",
            "password": "viewer123",
            "role": "viewer",
        },
        "auditor": {
            "email": "auditor@fhirbridge.local",
            "name": "Auditor",
            "password": "auditor123",
            "role": "auditor",
        },
    }
}

# Hash passwords in-place on first run (idempotent – skips already-hashed)
stauth.Hasher.hash_passwords(CREDENTIALS)

COOKIE_CONFIG: dict[str, Any] = {
    "expiry_days": 1,
    "key": "kritis_dashboard_signature",
    "name": "kritis_dashboard_session",
}

authenticator = stauth.Authenticate(
    credentials=CREDENTIALS,
    cookie_name=COOKIE_CONFIG["name"],
    cookie_key=COOKIE_CONFIG["key"],
    cookie_expiry_days=COOKIE_CONFIG["expiry_days"],
)

# Sidebar login
try:
    authenticator.login(location="sidebar")
except Exception as e:
    st.sidebar.error(f"Login error: {e}")

auth_status = st.session_state.get("authentication_status")

if auth_status is False:
    st.sidebar.error("❌ Ungültige Anmeldedaten.")
    st.stop()
elif auth_status is None:
    st.sidebar.warning("🔒 Bitte anmelden, um das Dashboard zu nutzen.")
    st.stop()

# --- Authenticated from here ---
current_username: str = st.session_state.get("username", "")
current_role: str = CREDENTIALS["usernames"].get(current_username, {}).get("role", "viewer")

st.sidebar.success(f"Angemeldet als **{current_username}** ({current_role})")
authenticator.logout("Logout", "sidebar")

# ---------------------------------------------------------------------------
# 3. Navigation (Sidebar)
# ---------------------------------------------------------------------------
page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Pipeline Overview",
        "📨 Message Queues",
        "🔴 Quarantine / Failed Jobs",
        "🔍 Job Inspector",
    ],
)

if st.sidebar.button("🔄 Daten aktualisieren"):
    st.cache_data.clear()

# ---------------------------------------------------------------------------
# 4. Data Layer – Postgres (Read-Only, Cached)
# ---------------------------------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL", "")


@st.cache_resource
def get_readonly_session_factory() -> sessionmaker:  # type: ignore[type-arg]
    """Create a read-only SQLAlchemy session factory from DATABASE_URL."""
    if not DATABASE_URL:
        return None  # type: ignore[return-value]
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


session_factory = get_readonly_session_factory()
if session_factory is None:
    st.error("❌ DATABASE_URL ist nicht gesetzt. Dashboard kann nicht starten.")
    st.stop()


@st.cache_data(ttl=10)
def fetch_job_kpis() -> dict[str, int]:
    """Fetch aggregated job counts per status."""
    with session_factory() as session:
        rows = session.query(Job.status, func.count(Job.id)).group_by(Job.status).all()
    counts: dict[str, int] = {s.value: 0 for s in JobStatus}
    for status, count in rows:
        counts[status if isinstance(status, str) else status.value] = count
    return counts


@st.cache_data(ttl=10)
def fetch_throughput_24h() -> pd.DataFrame:
    """Fetch hourly job throughput for the last 24 hours (Postgres date_trunc)."""
    cutoff = datetime.now(tz=UTC) - timedelta(hours=24)
    with session_factory() as session:
        rows = (
            session.query(
                func.date_trunc("hour", Job.updated_at).label("hour"),
                Job.status,
                func.count(Job.id).label("count"),
            )
            .filter(Job.updated_at >= cutoff)
            .group_by("hour", Job.status)
            .order_by("hour")
            .all()
        )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["hour", "status", "count"])
    df["status"] = df["status"].apply(lambda s: s.value if hasattr(s, "value") else s)
    return df


@st.cache_data(ttl=10)
def fetch_failed_jobs() -> list[dict[str, Any]]:
    """Fetch jobs with FAILED or EXPORT_FAILED status."""
    with session_factory() as session:
        jobs = (
            session.query(Job)
            .filter(Job.status.in_([JobStatus.FAILED, JobStatus.EXPORT_FAILED]))
            .order_by(Job.updated_at.desc())
            .all()
        )
        return [
            {
                "id": j.id,
                "filepath": j.filepath,
                "status": j.status.value if hasattr(j.status, "value") else j.status,
                "error_trace": j.error_trace or "",
                "updated_at": str(j.updated_at) if j.updated_at else "",
            }
            for j in jobs
        ]


@st.cache_data(ttl=10)
def fetch_all_jobs_summary() -> list[dict[str, Any]]:
    """Fetch all jobs (summary) for the Job Inspector dropdown."""
    with session_factory() as session:
        jobs = session.query(Job).order_by(Job.updated_at.desc()).all()
        return [
            {
                "id": j.id,
                "filepath": j.filepath,
                "status": j.status.value if hasattr(j.status, "value") else j.status,
            }
            for j in jobs
        ]


@st.cache_data(ttl=10)
def fetch_job_detail(job_id: int) -> dict[str, Any] | None:
    """Fetch full detail for a single job."""
    with session_factory() as session:
        j = session.query(Job).filter(Job.id == job_id).first()
        if not j:
            return None
        return {
            "id": j.id,
            "filepath": j.filepath,
            "status": j.status.value if hasattr(j.status, "value") else j.status,
            "ocr_text": j.ocr_text or "",
            "fhir_json": j.fhir_json or "",
            "error_trace": j.error_trace or "",
            "created_at": str(j.created_at) if j.created_at else "",
            "updated_at": str(j.updated_at) if j.updated_at else "",
        }


# ---------------------------------------------------------------------------
# 5. Data Layer – RabbitMQ Management API
# ---------------------------------------------------------------------------
RABBITMQ_MANAGEMENT_URL = os.environ.get("RABBITMQ_MANAGEMENT_URL", "")
RABBITMQ_USER = os.environ.get("RABBITMQ_DEFAULT_USER", "guest")
RABBITMQ_PASS = os.environ.get("RABBITMQ_DEFAULT_PASS", "guest")


@st.cache_data(ttl=10)
def fetch_queue_metrics() -> tuple[list[dict[str, Any]], bool]:
    """
    Fetch queue metrics from RabbitMQ Management API.
    Returns (queue_list, success_flag).
    """
    if not RABBITMQ_MANAGEMENT_URL:
        return [], False
    try:
        resp = httpx.get(
            f"{RABBITMQ_MANAGEMENT_URL}/api/queues",
            auth=(RABBITMQ_USER, RABBITMQ_PASS),
            timeout=5.0,
        )
        resp.raise_for_status()
        queues = resp.json()
        return [
            {
                "name": q.get("name", "unknown"),
                "messages_ready": q.get("messages_ready", 0),
                "messages_unacked": q.get("messages_unacknowledged", 0),
                "consumers": q.get("consumers", 0),
                "is_dlq": "dlx" in q.get("name", "").lower() or "dead" in q.get("name", "").lower(),
            }
            for q in queues
        ], True
    except Exception as exc:
        logger.warning("RabbitMQ Management API unreachable: %s", exc)
        return [], False


# ---------------------------------------------------------------------------
# 6. Page Rendering
# ---------------------------------------------------------------------------


def render_pipeline_overview() -> None:
    """Page 1: Pipeline Overview – KPIs, Progress Bar, Throughput Chart."""
    st.header("📊 Pipeline Overview")

    try:
        kpis = fetch_job_kpis()
    except Exception as e:
        st.error(f"Fehler beim Laden der KPIs: {e}")
        return

    total = sum(kpis.values())
    pending = kpis.get(JobStatus.PENDING.value, 0)
    processing = (
        kpis.get(JobStatus.OCR_PROCESSING.value, 0)
        + kpis.get(JobStatus.LLM_EXTRACTION.value, 0)
        + kpis.get(JobStatus.EXPORTING.value, 0)
    )
    success = kpis.get(JobStatus.FHIR_GENERATED.value, 0) + kpis.get(JobStatus.EXPORTED.value, 0)
    failed = kpis.get(JobStatus.FAILED.value, 0)
    export_failed = kpis.get(JobStatus.EXPORT_FAILED.value, 0)

    # KPI Metrics
    cols = st.columns(6)
    cols[0].metric("Total Jobs", total)
    cols[1].metric("Pending ⏳", pending)
    cols[2].metric("Processing ⚙️", processing)
    cols[3].metric("Success ✅", success)
    cols[4].metric("Failed ❌", failed)
    cols[5].metric("Export Failed ⚠️", export_failed)

    # Progress Bar
    st.subheader("Pipeline Fortschritt")
    progress_ratio = success / total if total > 0 else 0.0
    st.progress(min(progress_ratio, 1.0))
    st.caption(f"{success} von {total} Jobs erfolgreich abgeschlossen ({progress_ratio:.0%})")

    st.divider()

    # Throughput Chart (last 24h)
    st.subheader("Throughput (letzte 24h)")
    try:
        df = fetch_throughput_24h()
    except Exception as e:
        st.error(f"Fehler beim Laden der Throughput-Daten: {e}")
        return

    if df.empty:
        st.info("⏳ Keine Throughput-Daten für die letzten 24 Stunden vorhanden.")
    else:
        df_pivot = df.pivot_table(
            index="hour", columns="status", values="count", aggfunc="sum"
        ).fillna(0)
        st.bar_chart(df_pivot, use_container_width=True, height=350)


def render_message_queues() -> None:
    """Page 2: Message Queues – RabbitMQ queue health."""
    st.header("📨 Message Queues")

    queues, ok = fetch_queue_metrics()

    if not ok:
        st.warning(
            "⚠️ RabbitMQ Management API nicht erreichbar. "
            "Queue-Metriken sind aktuell nicht verfügbar."
        )
        return

    if not queues:
        st.info("Keine Queues gefunden.")
        return

    # Separate normal queues from DLQs
    normal_queues = [q for q in queues if not q["is_dlq"]]
    dlq_queues = [q for q in queues if q["is_dlq"]]

    # Normal Queues
    st.subheader("Active Queues")
    if normal_queues:
        df_normal = pd.DataFrame(normal_queues)[
            ["name", "messages_ready", "messages_unacked", "consumers"]
        ]
        df_normal.columns = ["Queue", "Messages Ready", "Messages Unacked", "Consumers"]
        st.dataframe(df_normal, use_container_width=True, hide_index=True)
    else:
        st.info("Keine aktiven Queues.")

    st.divider()

    # Dead-Letter Queues
    st.subheader("🔴 Dead-Letter Queues (DLQ)")
    if dlq_queues:
        total_dlq_messages = sum(q["messages_ready"] for q in dlq_queues)
        if total_dlq_messages > 0:
            st.error(
                f"🚨 ALARM: {total_dlq_messages} Nachrichten in Dead-Letter Queues! "
                "Sofortige Untersuchung erforderlich."
            )
        else:
            st.success("✅ Keine Nachrichten in Dead-Letter Queues.")

        df_dlq = pd.DataFrame(dlq_queues)[
            ["name", "messages_ready", "messages_unacked", "consumers"]
        ]
        df_dlq.columns = ["DLQ Name", "Messages Ready", "Messages Unacked", "Consumers"]
        st.dataframe(df_dlq, use_container_width=True, hide_index=True)
    else:
        st.info("Keine Dead-Letter Queues konfiguriert.")


def render_quarantine(role: str) -> None:
    """Page 3: Quarantine / Failed Jobs – Error Inspector."""
    st.header("🔴 Quarantine / Failed Jobs")

    try:
        failed_jobs = fetch_failed_jobs()
    except Exception as e:
        st.error(f"Fehler beim Laden der fehlgeschlagenen Jobs: {e}")
        return

    if not failed_jobs:
        st.success("✅ Keine fehlgeschlagenen Jobs. Alle Systeme arbeiten normal.")
        return

    st.warning(f"⚠️ {len(failed_jobs)} Job(s) im Quarantäne-Status.")

    for job in failed_jobs:
        with st.expander(
            f"Job #{job['id']} — {os.path.basename(job['filepath'])} "
            f"[{job['status']}] — {job['updated_at']}"
        ):
            st.markdown(f"**Job ID:** `{job['id']}`")
            st.markdown(f"**Dateipfad:** `{job['filepath']}`")
            st.markdown(f"**Status:** `{job['status']}`")
            st.markdown(f"**Letzte Aktualisierung:** `{job['updated_at']}`")

            st.divider()

            if role == "auditor":
                st.markdown("**Error Trace:**")
                if job["error_trace"]:
                    st.code(job["error_trace"], language="text")
                else:
                    st.info("Kein Error Trace vorhanden.")
            else:
                st.info("🔒 Error Traces sind nur für die Rolle **auditor** sichtbar.")


def render_job_inspector(role: str) -> None:
    """Page 4: Job Inspector – OCR Input vs FHIR Output (auditor only)."""
    st.header("🔍 Job Inspector")

    if role != "auditor":
        st.warning(
            "🔒 Zugriff eingeschränkt: Der Job Inspector ist nur für "
            "Benutzer mit der Rolle **auditor** verfügbar."
        )
        return

    try:
        all_jobs = fetch_all_jobs_summary()
    except Exception as e:
        st.error(f"Fehler beim Laden der Job-Liste: {e}")
        return

    if not all_jobs:
        st.info("Keine Jobs in der Pipeline.")
        return

    # Dropdown to select a job
    job_options = {
        f"Job #{j['id']} — {os.path.basename(j['filepath'])} [{j['status']}]": j["id"]
        for j in all_jobs
    }
    selected_label = st.selectbox("Job auswählen:", list(job_options.keys()))

    if not selected_label:
        return

    selected_id = job_options[selected_label]

    try:
        detail = fetch_job_detail(selected_id)
    except Exception as e:
        st.error(f"Fehler beim Laden des Jobs: {e}")
        return

    if not detail:
        st.error("Job nicht gefunden.")
        return

    st.markdown(
        f"**Datei:** `{detail['filepath']}` | **Status:** `{detail['status']}` | "
        f"**Erstellt:** `{detail['created_at']}` | **Aktualisiert:** `{detail['updated_at']}`"
    )

    if detail["error_trace"]:
        with st.expander("⚠️ Error Trace"):
            st.code(detail["error_trace"], language="text")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📄 Input (Raw OCR Text)")
        if detail["ocr_text"]:
            st.text_area(
                "OCR Output",
                detail["ocr_text"],
                height=600,
                disabled=True,
                label_visibility="collapsed",
            )
        else:
            st.info("Kein OCR-Text vorhanden (Job noch in Verarbeitung oder fehlgeschlagen).")

    with col_right:
        st.subheader("🏥 Output (FHIR JSON)")
        if detail["fhir_json"]:
            try:
                parsed = json.loads(detail["fhir_json"])
                st.json(parsed, expanded=True)
            except json.JSONDecodeError:
                st.code(detail["fhir_json"], language="json")
        else:
            st.info("Kein FHIR-Output vorhanden (Job noch in Verarbeitung oder fehlgeschlagen).")


# ---------------------------------------------------------------------------
# 7. Main Router
# ---------------------------------------------------------------------------
st.title("🏥 FhirBridgeAI – Observability Dashboard")
st.caption("KRITIS-konformes Monitoring für die LLM-gesteuerte OCR-zu-FHIR Pipeline.")

if page == "📊 Pipeline Overview":
    render_pipeline_overview()
elif page == "📨 Message Queues":
    render_message_queues()
elif page == "🔴 Quarantine / Failed Jobs":
    render_quarantine(current_role)
elif page == "🔍 Job Inspector":
    render_job_inspector(current_role)
