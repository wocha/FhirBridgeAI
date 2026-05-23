import asyncio
import tempfile
import traceback
from pathlib import Path

import httpx
from opentelemetry import trace, propagate
from opentelemetry.sdk.trace import TracerProvider

from fhirbridge.models.kdl_document import DischargeBrief, RendererType
from fhirbridge.core.pdf_engine import MedicalPdfEngine

# 1. Setup OpenTelemetry Tracer
provider = TracerProvider()
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("e2e-trigger-script")

API_URL = "http://localhost/ingest/pdf"

async def generate_and_upload_pdf():
    # 2. Nutze die bestehende Logik aus pdf_engine.py zur PDF Generierung (KDL Modellierung)
    doc = DischargeBrief(
        renderer_type=RendererType.DIN5008,
        kdl_code="AD010103",
        kdl_name="Entlassungsbericht intern",
        patient_id="PAT-E2E-001",
        patient_name="Erika E2E-Mustermann",
        fall_id="FALL-E2E-001",
        document_date="12.03.2026",
        title="ENTLASSUNGSBERICHT",
        content_paragraphs=[
            "Die automatisierte End-to-End Verarbeitung wurde erfolgreich initiiert.",
            "Dies ist ein generiertes PDF, das das System unter Hochlastbedingungen testen soll."
        ]
    )

    pdf_engine = MedicalPdfEngine()
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf_path = tmp.name

    try:
        # Generate the safe PDF
        pdf_engine.render_clean_pdf(doc, pdf_path, synthea_hospital_name="General Hospital")
        
        # 3. Simulate a clean API Client with Async (aiohttp/httpx)
        with tracer.start_as_current_span("trigger_e2e_ingest") as span:
            headers = {}
            # 4. Inject initial OpenTelemetry-Trace-Context
            propagate.inject(headers)
            
            span.set_attribute("http.url", API_URL)
            span.set_attribute("http.method", "POST")
            
            print(f"[*] Generiertes KDL-Dokument ({doc.kdl_code}) wird hochgeladen...")
            print(f"[*] API-Gateway: {API_URL}")
            print(f"[*] Trace Context Headers: {headers}")

            async with httpx.AsyncClient(follow_redirects=True, verify=False) as client:
                with open(pdf_path, "rb") as f:
                    # 'files' dictionary defines multipart form-data.
                    files = {"file": ("e2e_test_report.pdf", f, "application/pdf")}
                    
                    # 5. Fire-and-Forget. Script terminats immediately after 200/202.
                    response = await client.post(API_URL, files=files, headers=headers, timeout=10.0)
                    
            if response.status_code in (200, 202):
                print(f"[+] Erfolgreich! HTTP {response.status_code} - Document Accepted.")
                print("[+] Skript terminiert erfolgreich (Fire-and-Forget). Kein Polling!")
            else:
                print(f"[-] Fehler: Unerwarteter HTTP Status {response.status_code}")
                print(response.text)
                response.raise_for_status()
                
    except Exception as e:
        print(f"[!] Kritischer Fehler in der Ausführung: {e}")
        # Gib den reinen Stacktrace aus
        traceback.print_exc()
        raise
    finally:
        # Cleanup temp file
        Path(pdf_path).unlink(missing_ok=True)
        pdf_engine.cleanup()

if __name__ == "__main__":
    asyncio.run(generate_and_upload_pdf())
