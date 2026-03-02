"""
KRITIS Dashboard for FhirBridgeAI Dispatcher.
Shows an overview of the OCR-to-FHIR extraction progress.
Connected via Read-Only access to the SQLite database via SQLAlchemy.

Run: streamlit run dashboard/app.py
"""

import os
import sys

import pandas as pd
import streamlit as st
from sqlalchemy import func

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from fhirbridge.core.database import Job, get_engine, get_session_factory
except ImportError:
    st.error("Kann das database-Module nicht importieren. Stelle sicher, dass src/ im PYTHONPATH ist.")
    st.stop()


# KRITIS-friendly Setup: Disable all external dependencies/tracking
st.set_page_config(
    page_title="FhirBridgeAI - Dispatcher Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Unterbinde externe Requests für saubere Offline-Ausführung (Best Effort Layouting)
st.markdown("""
    <style>
    /* Force local minimalist styling */
    .stApp {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏥 FhirBridgeAI - Dispatcher Monitor")
st.markdown("KRITIS Sicheres Monitoring für die LLM-gesteuerte OCR-zu-FHIR Pipeline.")

DB_PATH = "data/dispatcher.db"

@st.cache_resource
def get_db_session_factory():
    if not os.path.exists(DB_PATH):
        return None
    engine = get_engine(DB_PATH)
    return get_session_factory(engine)


session_factory = get_db_session_factory()

if session_factory is None:
    st.warning(f"Datenbank nicht gefunden: `{DB_PATH}`. Der Dispatcher muss einmal gelaufen sein, bevor das Dashboard startet.")
    st.stop()


# ---------------------------------------------------------------------------
# Database Queries (Read-Only)
# ---------------------------------------------------------------------------

try:
    with session_factory() as session:
        total_jobs = session.query(func.count(Job.id)).scalar()
        pending_jobs = session.query(func.count(Job.id)).filter(Job.status == "PENDING").scalar()
        ocr_jobs = session.query(func.count(Job.id)).filter(Job.status == "OCR_PROCESSING").scalar()
        llm_jobs = session.query(func.count(Job.id)).filter(Job.status == "LLM_EXTRACTION").scalar()
        done_jobs = session.query(func.count(Job.id)).filter(Job.status == "FHIR_GENERATED").scalar()
        error_jobs = session.query(func.count(Job.id)).filter(Job.status == "ERROR").scalar()


        # KPIs rendering
        st.subheader("System Status")
        kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

        with kpi1:
            st.metric(label="Total Files", value=total_jobs)
        with kpi2:
            st.metric(label="Pending ⏳", value=pending_jobs)
        with kpi3:
            st.metric(label="OCR 👁️", value=ocr_jobs)
        with kpi4:
            st.metric(label="LLM 🧠", value=llm_jobs)
        with kpi5:
            st.metric(label="Success ✅", value=done_jobs)
        with kpi6:
            st.metric(label="Errors ❌", value=error_jobs)

        st.divider()

        # ---------------------------------------------------------------------------
        # Progress Graph (Throughput)
        # ---------------------------------------------------------------------------
        st.subheader("Processing Throughput (Last 24h)")

        # Query jobs grouped by hour and status
        # SQLite native date formatting
        throughput_query = session.query(
            func.strftime('%Y-%m-%d %H:00', Job.updated_at).label('hour'),
            Job.status,
            func.count(Job.id).label('count')
        ).group_by('hour', Job.status).all()

        if throughput_query:
            df_throughput = pd.DataFrame(throughput_query, columns=['hour', 'status', 'count'])
            # Pivot table for stacked bar chart effect
            df_pivot = df_throughput.pivot(index='hour', columns='status', values='count').fillna(0)

            # Map colors for statuses if they exist in the pivot columns
            color_map = []
            status_colors = {
                'FHIR_GENERATED': '#00b050',    # Green
                'ERROR': '#c00000',             # Red
                'LLM_EXTRACTION': '#0078d4',    # Blue
                'OCR_PROCESSING': '#ffc000',    # Yellow
                'PENDING': '#808080'            # Gray
            }

            # Render native Streamlit bar chart
            st.bar_chart(df_pivot, use_container_width=True, height=300)
        else:
            st.info("⏳ Keine historischen Daten für den zeitlichen Verlauf gefunden.")

        st.divider()

        # ---------------------------------------------------------------------------
        # Audit Log View
        # ---------------------------------------------------------------------------
        st.subheader("Audit Log & Job Pipeline")

        # Get all jobs, ordering by most recent first
        all_jobs = session.query(Job).order_by(Job.updated_at.desc()).all()

        if all_jobs:
            # Convert to Pandas DataFrame for Streamlit Table
            df = pd.DataFrame([{
                "ID": j.id,
                "File": os.path.basename(j.filepath),
                "Status": j.status,
                "Created": j.created_at.strftime("%H:%M:%S") if j.created_at else "",
                "Updated": j.updated_at.strftime("%H:%M:%S") if j.updated_at else ""
            } for j in all_jobs])

            # Color specific to status
            def style_status(val):
                color = 'black'
                if val == 'FHIR_GENERATED': color = 'green'
                elif val == 'ERROR': color = 'red'
                elif val == 'LLM_EXTRACTION': color = 'blue'
                elif val == 'OCR_PROCESSING': color = 'orange'
                elif val == 'PENDING': color = 'gray'
                return f'color: {color}; font-weight: bold'

            styled_df = df.style.map(style_status, subset=['Status'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.info("Keine Jobs in der Pipeline.")

        st.divider()

        # ---------------------------------------------------------------------------
        # Inspektor View
        # ---------------------------------------------------------------------------
        st.subheader("Job Inspektor (Auditability)")
        st.markdown("Vergleiche den rohen, vom Tesseract erzeugten Text, mit den strukturierten FHIR-Daten des LLMs.")

        if total_jobs > 0:
            selected_id = st.selectbox("Job ID wählen:", [f"Job #{j.id} - {os.path.basename(j.filepath)}" for j in all_jobs])

            if selected_id:
                # Extract the numeric ID from the dropdown text "Job #<ID> - ..."
                job_id = int(selected_id.split(' ')[1].replace('#', ''))
                job = session.query(Job).filter(Job.id == job_id).first()

                if job:
                    st.markdown(f"**Datei:** `{job.filepath}` | **Status:** `{job.status}`")

                    c1, c2 = st.columns(2)

                    with c1:
                        st.markdown("### 📄 Input (Arztbrief / Raw OCR)")
                        if job.ocr_text:
                            st.text_area("Extrahierter Text", job.ocr_text, height=600, disabled=True, label_visibility="collapsed")
                        elif job.status == "OCR_PROCESSING":
                            st.info("👁️ Bildverarbeitung (OCR) läuft aktuell. Bitte warten...")
                        elif job.status == "PENDING":
                            st.info("⏳ Dokument wartet auf Verarbeitung in der Queue.")
                        else:
                            st.error("Text konnte nicht aus der Datenbank gelesen werden.")

                    with c2:
                        st.markdown("### 🏥 Output (ISiK FHIR/JSON)")
                        if job.status == "FHIR_GENERATED" and job.fhir_json:
                            try:
                                import json
                                parsed_json = json.loads(job.fhir_json)
                                st.json(parsed_json, expanded=True)
                            except Exception as e:
                                st.error(f"Konnte Output nicht parsen: {e}")
                        elif job.status == "ERROR":
                            st.error(f"❌ Abbruch mit Fehler:\n\n{job.error_trace}")
                        elif job.status == "LLM_EXTRACTION":
                            st.warning("🧠 Mistral-NeMo extrahiert gerade die klinischen Daten aus dem Text. Bitte warten...")
                        elif job.status in ["PENDING", "OCR_PROCESSING"]:
                            st.info("⏳ Warte auf Abschluss der OCR-Phase, bevor das LLM gestartet wird.")
except Exception as e:
    st.error(f"Fehler beim Lesezugriff auf die Datenbank: {e}")
