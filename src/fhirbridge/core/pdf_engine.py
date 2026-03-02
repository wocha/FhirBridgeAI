import hashlib
import json
import os
import random
import tempfile
import uuid
from pathlib import Path
from typing import Any

import barcode
import cv2
import fitz  # PyMuPDF
import numpy as np
import qrcode
from barcode.writer import ImageWriter
from faker import Faker
from PIL import Image, ImageFilter
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from fhirbridge.models.kdl_document import (
    DischargeBrief,
    ImagingReport,
    LabResults,
    NursingWardDoc,
    Prescription,
    RendererType,
    WorkIncapacityCertificate,
)

STYLES = getSampleStyleSheet()
STYLES.add(
    ParagraphStyle(name="MedicalHeader", fontName="Helvetica-Bold", fontSize=14, spaceAfter=10)
)
STYLES.add(
    ParagraphStyle(name="MedicalSubHeader", fontName="Helvetica-Bold", fontSize=11, spaceAfter=5)
)
STYLES.add(
    ParagraphStyle(name="MedicalBody", fontName="Helvetica", fontSize=10, spaceAfter=8, leading=14)
)
STYLES.add(
    ParagraphStyle(name="NursingNote", fontName="Courier", fontSize=9, spaceAfter=3, leading=11)
)
STYLES.add(
    ParagraphStyle(name="KDLTag", fontName="Helvetica-Oblique", fontSize=7, textColor=colors.grey)
)

CATALOG_PATH = Path(__file__).parent.parent / "assets" / "hospital_catalog.json"


def get_institution_mapping(synthea_name: str) -> dict:
    default_inst = {
        "name": "Wocharienklinikum",
        "header_type": "standard",
        "color": HexColor("#003366"),
    }

    if not CATALOG_PATH.exists():
        return default_inst

    try:
        with open(CATALOG_PATH, encoding="utf-8") as f:
            catalog = json.load(f)
    except Exception:
        return default_inst

    mapping = catalog.get(synthea_name)
    if not mapping:
        mapping = catalog.get("default")

    if not mapping:
        return default_inst

    return {
        "name": mapping.get("name", default_inst["name"]),
        "header_type": mapping.get("header_type", default_inst["header_type"]),
        "color": HexColor(mapping.get("color_hex", "#003366")),
    }


class BasePdfRenderer:
    """Base strategy for PDF rendering."""

    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir

    def render(
        self, doc_obj: Any, output_path: str, inst: dict[str, Any], include_qr: bool = True
    ) -> None:
        raise NotImplementedError("Subclasses must implement render()")

    def add_patient_barcode_safe(self, canvas: Any, fall_id: str) -> None:
        canvas.saveState()
        EAN = barcode.get_barcode_class("code128")
        ean = EAN(fall_id, writer=ImageWriter())
        temp_file = str(self.temp_dir / f"temp_barcode_{uuid.uuid4().hex[:6]}")
        temp_png = f"{temp_file}.png"
        ean.save(temp_file)
        canvas.drawImage(temp_png, A4[0] - 55 * mm, A4[1] - 30 * mm, width=35 * mm, height=12 * mm)
        canvas.restoreState()

    def add_doc_qrcode_safe(self, canvas: Any, inst_name: str, kdl_code: str, fall_id: str) -> None:
        canvas.saveState()
        qr_data = json.dumps({"inst": inst_name, "kdl": kdl_code, "fall": fall_id})
        qr = qrcode.QRCode(box_size=3, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        temp_file = str(self.temp_dir / f"temp_qr_{uuid.uuid4().hex[:6]}.png")
        img.save(temp_file, format="PNG")
        canvas.drawImage(temp_file, A4[0] - 30 * mm, 10 * mm, width=15 * mm, height=15 * mm)
        canvas.restoreState()


class Din5008Renderer(BasePdfRenderer):
    """Renderer for classic DIN 5008 business letters (like Arztbriefe)."""

    def draw_dynamic_header(
        self, canvas: Any, doc: Any, inst: dict[str, Any], doc_obj: Any, include_qr: bool = True
    ) -> None:
        canvas.saveState()

        h = int(hashlib.md5(str(getattr(doc_obj, "fall_id", "1")).encode()).hexdigest(), 16)

        # Seed Faker deterministically so the same fall_id always gets the same doctor
        fake = Faker("de_DE")
        Faker.seed(h)

        # Add realistic medical prefixes
        prefix = fake.random_element(
            elements=("Dr. med.", "Prof. Dr. med.", "Dr. med.", "PD Dr. med.")
        )
        doc_name = f"{prefix} {fake.first_name()} {fake.last_name()}"
        doc_address = fake.street_address()
        doc_city = f"{fake.postcode()} {fake.city()}"

        # 1. Header & Sender Block (Absender)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.setFillColor(inst["color"])
        sender_text = f"{inst['name']} - Klinik für Allgemeine Innere Medizin"
        canvas.drawString(20 * mm, A4[1] - 15 * mm, sender_text)

        canvas.setStrokeColor(inst["color"])
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, A4[1] - 17 * mm, A4[0] - 20 * mm, A4[1] - 17 * mm)

        # 2. Recipient Address Block (Empfänger) & Rücksendeangabe
        address_y = A4[1] - 50 * mm

        # Rücksendeangabe (Fensterbrief)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.black)
        sender_line = "Wocharienklinikum | Musterstraße 10 | 12345 Wocharien"
        canvas.drawString(20 * mm, address_y + 5 * mm, sender_line)
        sender_line_width = canvas.stringWidth(sender_line, "Helvetica", 7)
        canvas.setLineWidth(0.3)
        canvas.line(20 * mm, address_y + 4 * mm, 20 * mm + sender_line_width, address_y + 4 * mm)

        canvas.setFont("Helvetica", 10)
        canvas.drawString(20 * mm, address_y, "Herrn / Frau Kollegin / Kollegen")
        canvas.drawString(20 * mm, address_y - 5 * mm, doc_name)
        canvas.drawString(20 * mm, address_y - 10 * mm, doc_address)
        canvas.drawString(20 * mm, address_y - 15 * mm, doc_city)

        # 3. Date & Location (Ort und Datum)
        # Positioned closer to the Betrifft-zeile (which starts at topMargin)
        date_y = A4[1] - 105 * mm
        # Use first word of hospital name as city fallback
        city = inst["name"].split(" ")[0] if inst["name"] else "Klinik"
        city = city.replace("Klinikum", "Stadt").replace("Wocharienklinikum", "Wocharien")
        canvas.drawRightString(
            A4[0] - 20 * mm,
            date_y,
            f"{city}, den {getattr(doc_obj, 'document_date', '01.01.1970')}",
        )

        # Footer
        page_num = doc.page
        canvas.setFont("Helvetica", 6)
        canvas.setFillColor(colors.black)

        if page_num == 1:
            # Full 3-column clinic footer
            footer_y = 25 * mm
            # Col 1: Kontakt & Bank
            canvas.drawString(20 * mm, footer_y, f"{inst['name']} • Telefon 05555 123 0")
            canvas.drawString(20 * mm, footer_y - 3 * mm, "Internet: www.klinikum-beispiel.de")
            canvas.drawString(20 * mm, footer_y - 6 * mm, "USt-IdNr. DE 1234567890")
            canvas.drawString(
                20 * mm, footer_y - 9 * mm, "Bankverbindung: Sparkasse Musterstadt • BLZ 000 000 00"
            )

            # Col 2: Gesellschaft
            canvas.drawString(90 * mm, footer_y, f"{inst['name']} • Gesellschaft für Gesundheit")
            canvas.drawString(90 * mm, footer_y - 3 * mm, "Vorstand: Dr. Frieda Baum")

        # Footer Metadata (all pages)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.grey)
        patient_name = getattr(doc_obj, "patient_name", "Patient")
        fall_id = getattr(doc_obj, "fall_id", "UNK")
        doc_date = getattr(doc_obj, "document_date", "01.01.1970")
        canvas.drawString(
            20 * mm, 10 * mm, f"Arztbrief für {patient_name} | Fall: {fall_id} | Datum: {doc_date}"
        )
        canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, f"Seite {page_num}")

        canvas.restoreState()

        self.add_patient_barcode_safe(canvas, getattr(doc_obj, "fall_id", "FALL-ID"))
        if include_qr:
            self.add_doc_qrcode_safe(
                canvas,
                inst["name"],
                getattr(doc_obj, "kdl_code", "UNK"),
                getattr(doc_obj, "fall_id", "UNK"),
            )

    def render(
        self, doc_obj: Any, output_path: str, inst: dict[str, Any], include_qr: bool = True
    ) -> None:
        # Erhöhter Top-Margin (115mm) für DIN-lang Falzbereich und harmonischeren Abstand
        doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=115 * mm, bottomMargin=25 * mm)
        story = []

        patient_name = getattr(doc_obj, "patient_name", "Unbekannter Patient")
        fall_id = getattr(doc_obj, "fall_id", "FALL-UNK")

        subject_text = f"<b>Betrifft:</b> {patient_name} (Fall-ID: {fall_id})"
        story.append(Paragraph(subject_text, STYLES["MedicalBody"]))
        story.append(Spacer(1, 10 * mm))

        if isinstance(doc_obj, (DischargeBrief, ImagingReport)):
            for p in doc_obj.content_paragraphs:  # type: ignore[union-attr]
                story.append(Paragraph(p.replace("\n", "<br/>"), STYLES["MedicalBody"]))

        elif isinstance(doc_obj, NursingWardDoc):
            for entry in doc_obj.entries:
                story.append(
                    Paragraph(f"<b>{entry.timestamp}:</b> {entry.note}", STYLES["NursingNote"])
                )

        doc.build(
            story,
            onFirstPage=lambda c, d: self.draw_dynamic_header(c, d, inst, doc_obj, include_qr),
            onLaterPages=lambda c, d: self.draw_dynamic_header(c, d, inst, doc_obj, include_qr),
        )


class TabularRenderer(BasePdfRenderer):
    """Renderer for tabular data like LabResults without full DIN5008 formatting."""

    def draw_tabular_header(
        self, canvas: Any, doc: Any, inst: dict[str, Any], doc_obj: Any, include_qr: bool = True
    ) -> None:
        canvas.saveState()

        # Simple Header
        canvas.setFont("Helvetica-Bold", 14)
        canvas.setFillColor(inst["color"])
        canvas.drawString(20 * mm, A4[1] - 20 * mm, f"{inst['name']} - Laborbefund")

        canvas.setStrokeColor(inst["color"])
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, A4[1] - 22 * mm, A4[0] - 20 * mm, A4[1] - 22 * mm)

        # Meta Data
        canvas.setFont("Helvetica", 10)
        canvas.setFillColor(colors.black)
        patient_name = getattr(doc_obj, "patient_name", "Patient")
        fall_id = getattr(doc_obj, "fall_id", "UNK")
        doc_date = getattr(doc_obj, "document_date", "01.01.1970")

        canvas.drawString(20 * mm, A4[1] - 30 * mm, f"Patient: {patient_name}")
        canvas.drawString(20 * mm, A4[1] - 35 * mm, f"Fall-ID: {fall_id}")
        canvas.drawString(20 * mm, A4[1] - 40 * mm, f"Datum: {doc_date}")

        # Footer
        page_num = doc.page
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, f"Seite {page_num}")

        canvas.restoreState()

        self.add_patient_barcode_safe(canvas, getattr(doc_obj, "fall_id", "UNK"))
        if include_qr:
            self.add_doc_qrcode_safe(
                canvas,
                inst["name"],
                getattr(doc_obj, "kdl_code", "UNK"),
                getattr(doc_obj, "fall_id", "UNK"),
            )

    def render(
        self, doc_obj: Any, output_path: str, inst: dict[str, Any], include_qr: bool = True
    ) -> None:
        # Smaller top margin since header is more compact
        doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=50 * mm, bottomMargin=25 * mm)
        story = []

        if isinstance(doc_obj, LabResults):
            data = [["Parameter", "Wert", "Norm"]]
            for param in doc_obj.parameters:
                data.append([param.name, param.value, param.reference_range])

            t = Table(data, colWidths=[60 * mm, 40 * mm, 40 * mm], hAlign="LEFT")
            t.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ]
                )
            )
            story.append(t)

        doc.build(
            story,
            onFirstPage=lambda c, d: self.draw_tabular_header(c, d, inst, doc_obj, include_qr),
            onLaterPages=lambda c, d: self.draw_tabular_header(c, d, inst, doc_obj, include_qr),
        )


class KbvFormRenderer(BasePdfRenderer):
    """Renderer for standard KBV Forms (e.g., Rezept, AU). Absolute coordinates."""

    def render(
        self, doc_obj: Any, output_path: str, inst: dict[str, Any], include_qr: bool = True
    ) -> None:
        # Für KBV Formulare rendern wir einfachen Text an bestimmten
        # Koordinaten für den Proof of Concept.
        from reportlab.pdfgen import canvas as pdf_canvas

        c = pdf_canvas.Canvas(output_path, pagesize=A4)
        c.setFont("Helvetica-Bold", 14)

        if isinstance(doc_obj, Prescription):
            c.drawString(20 * mm, A4[1] - 30 * mm, "Muster 16 - Kassenrezept")
            c.setFont("Helvetica", 11)
            c.drawString(
                20 * mm, A4[1] - 40 * mm, f"Patient: {getattr(doc_obj, 'patient_name', 'UNK')}"
            )
            c.drawString(20 * mm, A4[1] - 45 * mm, "Geb. Datum: 01.01.1980")  # Placeholder

            c.setFont("Helvetica-Bold", 10)
            c.drawString(20 * mm, A4[1] - 60 * mm, "Verordnete Medikamente:")
            c.setFont("Helvetica", 10)
            y = A4[1] - 65 * mm
            for med in getattr(doc_obj, "medications", []):
                c.drawString(25 * mm, y, f"- {med}")
                y -= 10 * mm

        elif isinstance(doc_obj, WorkIncapacityCertificate):
            c.drawString(20 * mm, A4[1] - 30 * mm, "Muster 1 - Arbeitsunfähigkeitsbescheinigung")
            c.setFont("Helvetica", 11)
            c.drawString(
                20 * mm, A4[1] - 40 * mm, f"Patient: {getattr(doc_obj, 'patient_name', 'UNK')}"
            )
            c.drawString(
                20 * mm,
                A4[1] - 55 * mm,
                f"Arbeitsunfähig von: {getattr(doc_obj, 'start_date', 'UNK')}",
            )
            c.drawString(
                20 * mm,
                A4[1] - 60 * mm,
                f"Voraussichtlich bis: {getattr(doc_obj, 'end_date', 'UNK')}",
            )
            c.drawString(
                20 * mm, A4[1] - 75 * mm, f"Diagnose (ICD): {getattr(doc_obj, 'icd_code', 'UNK')}"
            )

        self.add_patient_barcode_safe(c, getattr(doc_obj, "fall_id", "UNK"))
        if include_qr:
            self.add_doc_qrcode_safe(
                c,
                inst["name"],
                getattr(doc_obj, "kdl_code", "UNK"),
                getattr(doc_obj, "fall_id", "UNK"),
            )

        c.save()


class MedicalPdfEngine:
    """
    Engine to orchestrate rendering of Pydantic KDL documents into DIN-A4 PDFs.
    Uses tempfile.TemporaryDirectory to ensure safe artifact handling and the
    Strategy pattern to render correctly based on document RendererType.
    """

    def __init__(self, temp_dir: str | None = None) -> None:
        self._temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self._temp_dir_obj.name)

        # Instantiate strategies
        self.renderers = {
            RendererType.DIN5008: Din5008Renderer(self.temp_dir),
            RendererType.TABULAR: TabularRenderer(self.temp_dir),
            RendererType.KBV_FORM: KbvFormRenderer(self.temp_dir),
        }

    def cleanup(self) -> None:
        """Removes temporary image files (barcodes/QR) generated during the process."""
        if hasattr(self, "_temp_dir_obj") and self._temp_dir_obj:
            try:
                self._temp_dir_obj.cleanup()
            except Exception as e:
                print(f"Warning: Could not clean up TemporaryDirectory - {e}")
            self._temp_dir_obj = None  # type: ignore[assignment]

    def __del__(self) -> None:
        self.cleanup()

    def render_clean_pdf(
        self,
        doc_obj: Any,
        output_path: str,
        synthea_hospital_name: str | None = None,
        include_qr: bool = True,
    ) -> None:
        """
        Builds the clean PDF. Acts as a Factory method delegating to the appropriate
        strategy based on the `renderer_type`.
        """
        inst = get_institution_mapping(str(synthea_hospital_name or ""))

        # Get Renderer Type, fallback to DIN5008
        renderer_type = getattr(doc_obj, "renderer_type", RendererType.DIN5008)
        renderer = self.renderers.get(renderer_type, self.renderers[RendererType.DIN5008])

        renderer.render(doc_obj, output_path, inst, include_qr)

    def apply_hardware_degradation(self, image: Any) -> Any:
        img_array = np.array(image)
        h, w, c = img_array.shape
        # Streaks
        for _ in range(random.randint(1, 4)):
            x = random.randint(0, w - 1)
            w_s = random.randint(1, 2)
            img_array[:, x : x + w_s, :] = (img_array[:, x : x + w_s, :] * 0.7 + 160 * 0.3).astype(
                np.uint8
            )

        image = Image.fromarray(img_array).convert("L")
        image = image.filter(ImageFilter.GaussianBlur(0.7))

        img_array = np.array(image)
        noise = np.random.normal(0, 10, img_array.shape).astype(np.uint8)
        image = Image.fromarray(cv2.add(img_array, noise)).convert("RGB")

        # Slight rotation misalignment
        image = image.rotate(
            random.uniform(-1.2, 1.2),
            resample=Image.Resampling.BICUBIC,
            expand=True,
            fillcolor=(255, 255, 255),
        )
        return image

    def degrade_pdf_to_scan(
        self, clean_pdf: str, dirty_pdf: str, remove_clean: bool = True
    ) -> None:
        try:
            pdf_doc = fitz.open(clean_pdf)
            images = []
            for page in pdf_doc:
                pix = page.get_pixmap(dpi=150)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                images.append(self.apply_hardware_degradation(img))
            pdf_doc.close()

            if images:
                images[0].save(
                    dirty_pdf, save_all=True, append_images=images[1:], resolution=150.0, quality=75
                )

            if remove_clean and os.path.exists(clean_pdf):
                os.remove(clean_pdf)
        except Exception as e:
            print(f"Scan Error: {e}")
