"""
Enterprise KRITIS Dashboard for Autonomous Dispatcher Monitoring.

Air-gapped Streamlit application that provides read-only transparency into
the SQLite Job Queue. This dashboard never mutates the database to prevent
locking the active workers.
"""

import logging
import os
import sys

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

# Import our schema from the dispatcher skill
# Allows parsing DB enums and models securely
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "building-autonomous-dispatchers", "scripts")))
try:
    from schema_reference import Job, JobStatus
except ImportError:
    st.error("Failed to import Job schema from building-autonomous-dispatchers.")
    st.stop()

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kritis_dashboard")

# --- Streamlit Page Configuration ---------------------------------------------
# strict air-gap compliance: no external fonts or SVGs loaded
st.set_page_config(
    page_title="Phase 4: Autonomous Dispatcher",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to hide the Streamlit main menu (hamburger) and deploy button
# which usually ping external services.
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# --- Authentication Configuration -----------------------------------------------
# In a real production KRITIS deployment, these comes from a DB or OIDC claim mapping.
CREDENTIALS = {
    "usernames": {
        "viewer": {
            "name": "Viewer",
            "password": "$2b$12$eFWS5NFtQacFt.ewdBAQzu9rT/.fYETiRcy4VDGBCSEawj88PouTK", # pre-hashed 'viewer'
            "role": "viewer"
        },
        "auditor": {
            "name": "Auditor",
            "password": "$2b$12$37oop.xmAAMJiJvgqso.BOT4X25DM3OY/JdcwwSpawDF.F7UoSWX.", # pre-hashed 'auditor'
            "role": "auditor"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials=CREDENTIALS,
    cookie_name="kritis_dashboard_session",
    cookie_key="kritis_dashboard_signature",
    cookie_expiry_days=1,
)

# --- Database Setup -----------------------------------------------------------
DB_PATH = os.getenv("DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "dispatcher.db")))
st.sidebar.caption(f"DB Reference: {DB_PATH}")

# Caching the DB connection ensures Streamlit doesn't recreate it on every slider drag
@st.cache_resource
def get_db_session() -> sessionmaker:
    """Provides a read-only session factory to the database.
    Crucial: check_same_thread=False allows Streamlit threads to query DB (for SQLite).
    """
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        engine = create_engine(DATABASE_URL)
        return sessionmaker(autocommit=False, autoflush=False, bind=engine)

    if not os.path.exists(DB_PATH):
        logger.warning(f"Database missing at {DB_PATH}")
        return None

    engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={'check_same_thread': False})
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

SessionLocal = get_db_session()

# --- Data Fetching Functions --------------------------------------------------

@st.cache_data(ttl=5) # Refresh metrics roughly every 5 seconds
def fetch_job_metrics() -> dict:
    """Safe, read-only aggregation of queue metrics."""
    if not SessionLocal:
        return {"total": 0, "pending": 0, "processing": 0, "done": 0, "error": 0}

    try:
        with SessionLocal() as session:
            # Getting counts by status
            stmt = select(Job.status, func.count(Job.id)).group_by(Job.status)
            results = session.execute(stmt).all()

            # Map results to dict
            status_counts = {status.name: count for status, count in results}

            total = sum(status_counts.values())

            pending = status_counts.get(JobStatus.PENDING.name, 0)

            # Active processing states
            processing = (
                status_counts.get(JobStatus.OCR_PROCESSING.name, 0) +
                status_counts.get(JobStatus.LLM_EXTRACTION.name, 0)
            )

            done = status_counts.get(JobStatus.FHIR_GENERATED.name, 0)

            error = (
                status_counts.get(JobStatus.ERROR.name, 0) +
                status_counts.get(JobStatus.FAILED_PERMANENTLY.name, 0)
            )

            return {
                "total": total,
                "pending": pending,
                "processing": processing,
                "done": done,
                "error": error
            }

    except Exception as e:
        logger.error(f"Error reading metrics: {e}")
        return {"total": 0, "pending": 0, "processing": 0, "done": 0, "error": 0}

@st.cache_data(ttl=5)
def fetch_recent_jobs(limit: int = 50, status_filter: str = "ALL") -> pd.DataFrame:
    """Fetches recent jobs as a Pandas DataFrame for the Audi Log view."""
    if not SessionLocal:
        return pd.DataFrame()

    try:
        with SessionLocal() as session:
            query = select(Job)

            if status_filter != "ALL":
                # Convert string back to Enum for filtering
                filter_enum = getattr(JobStatus, status_filter, None)
                if filter_enum:
                    query = query.where(Job.status == filter_enum)

            query = query.order_by(Job.updated_at.desc()).limit(limit)

            jobs = session.execute(query).scalars().all()

            # Convert to list of dicts for Pandas
            data = []
            for j in jobs:
                data.append({
                    "id": j.id,
                    "file_path": j.file_path,
                    "status": j.status.name,
                    "retry_count": j.retry_count,
                    "locked_by": j.lock_id,
                    "updated_at": j.updated_at,
                    "error_message": j.error_message
                })
            return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error fetching job table: {e}")
        return pd.DataFrame()


# --- UI Layout ----------------------------------------------------------------

def render_dashboard():
    """Renders the high-level metrics view."""
    st.title("Queue Dispatcher Overview")
    st.markdown("KRITIS-compliant, air-gapped monitoring of the background extraction pipeline.")

    if not SessionLocal:
        st.error(f"Database not found at {DB_PATH}. Ensure the Dispatcher Worker has started processing.")
        return

    metrics = fetch_job_metrics()

    # Render KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Jobs", metrics["total"])
    with col2:
        st.metric("Pending 📥", metrics["pending"])
    with col3:
        st.metric("Processing ⚙️", metrics["processing"])
    with col4:
        st.metric("Completed ✅", metrics["done"])
    with col5:
        st.metric("Errors ❌", metrics["error"])

    st.divider()

    # Progress Bar overall completion
    if metrics["total"] > 0:
        completion_rate = metrics["done"] / metrics["total"]
        st.subheader("Batch Progress")
        st.progress(completion_rate, text=f"{metrics['done']} out of {metrics['total']} files completed.")
    else:
        st.info("No jobs found in the queue. Enqueue some HL7/PDF files.")


def render_audit_log():
    """Renders the detailed Audit Log table."""
    st.title("Audit Log & Traceability")
    st.markdown("Detailed view of job execution states. Click on a row to expand error traces.")

    col1, col2 = st.columns([1, 3])
    with col1:
        # We construct the dynamic list of statuses from the Enum
        statuses = ["ALL"] + [s.name for s in JobStatus]
        status_filter = st.selectbox("Filter Status", statuses)

    with col2:
        limit = st.slider("Max Rows", min_value=10, max_value=500, value=50)

    st.divider()

    df = fetch_recent_jobs(limit=limit, status_filter=status_filter)

    if df.empty:
        st.warning("No jobs match the current filter.")
    else:
        # Use st.dataframe for an interactive table
        st.dataframe(
            df[["status", "file_path", "retry_count", "locked_by", "updated_at"]],
            use_container_width=True,
            hide_index=True
        )

        # Display specific error traces below the table to satisfy auditability
        error_df = df[df['error_message'].notnull()]

        current_username = st.session_state.get('username')
        current_role = CREDENTIALS["usernames"].get(current_username, {}).get("role", "viewer")

        if not error_df.empty:
            if current_role == 'auditor':
                st.subheader("Recent Error Traces")
                for _, row in error_df.head(10).iterrows():
                    with st.expander(f"Error in {os.path.basename(row['file_path'])} (Job: {row['id']})", expanded=False):
                        st.code(row['error_message'], language="text")
            else:
                st.info("🔒 Detailed error traces and payloads require 'auditor' role.")


# --- Main Application Routing -------------------------------------------------

def main():
    try:
        authenticator.login()
    except Exception as e:
        st.error(e)

    if st.session_state.get("authentication_status"):
        st.sidebar.title("Navigation")

        current_username = st.session_state.get('username')
        current_role = CREDENTIALS["usernames"].get(current_username, {}).get("role", "viewer")
        st.sidebar.markdown(f"**Logged in as:** `{current_username}` (Role: `{current_role}`)")
        authenticator.logout("Logout", "sidebar")
        st.sidebar.divider()

        page = st.sidebar.radio("Go to", ["Dashboard", "Audit Log"])

        if page == "Dashboard":
            render_dashboard()
        elif page == "Audit Log":
            render_audit_log()

        st.sidebar.divider()

        # Manual Refresh button (cache expires implicitly, but this is nice for UX)
        if st.sidebar.button("↻ Refresh Dashboard"):
            st.cache_data.clear()
            st.rerun()
    elif st.session_state.get("authentication_status") is False:
        st.error('Username/password is incorrect')
    elif st.session_state.get("authentication_status") is None:
        st.warning('Please enter your username and password')

if __name__ == "__main__":
    main()
