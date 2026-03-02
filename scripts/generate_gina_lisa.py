import datetime
import os
import random
import uuid
from io import BytesIO
from pathlib import Path

import barcode
import cv2
import fitz  # PyMuPDF

# For graphs and barcodes
import matplotlib.pyplot as plt
import numpy as np
import pydicom
import pydicom.uid
import qrcode
import requests
from barcode.writer import ImageWriter
from PIL import Image, ImageFilter
from pydicom.dataset import Dataset, FileDataset
from reportlab.lib import colors

# Imports for structural PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as RLImage,
)
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral-nemo"

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

# --- KDL Registry ---
KDL_REGISTRY = {
    "AD010103": "Entlassungsbericht intern",
    "AD010111": "Ambulanzbrief",
    "AU050102": "Überweisungsschein",
    "OP150103": "OP-Bericht",
    "PT080102": "Histologiebefund",
    "DG020103": "CT-Befund",
    "DG020110": "Röntgenbefund",
    "VL160105": "Pflegebericht",
    "VL160106": "Pflegekurve",
    "TH130107": "Medikamentenplan intern/extern",
    "LB120103": "Laborbefund intern",
    "TH060103": "Physiotherapieprotokoll",
}

INSTITUTIONS = [
    {
        "name": "Klinikum Mitte - Universitätsmedizin",
        "header_type": "standard",
        "color": colors.darkblue,
    },
    {
        "name": "Zentrum für Radiologie & Nuklearmedizin Dr. Stein",
        "header_type": "modern",
        "color": colors.darkred,
    },
    {
        "name": "Gemeinschaftspraxis für Innere Medizin & Onkologie",
        "header_type": "classic",
        "color": colors.black,
    },
    {"name": "Pathologisches Institut Nord", "header_type": "minimal", "color": colors.darkgreen},
    {"name": "Reha-Zentrum Parkaue", "header_type": "standard", "color": colors.darkslategrey},
]

# --- ANTI-HALLUCINATION ENGINE ---


def generate_llm_text(prompt, context="", target_date_str=""):
    """
    Generates text with strict date enforcement.
    """
    enforced_prompt = (
        f"System: Du bist ein medizinischer Dokumentations-Assistent. "
        f"Schreibe fachlich korrekte Texte für deutsche Krankenhausakten.\n"
        f"HEUTIGES DATUM: {target_date_str}. Erstelle den Text so, als wäre HEUTE dieser Tag.\n"
        f"Kontext: {context}\n"
        f"Aufgabe: {prompt}\n\n"
        f"Antworte NUR mit dem klinischen Text."
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": enforced_prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 800},
                },
                timeout=300,
            )
            if response.status_code == 200:
                return response.json()["response"].strip()
            else:
                print(
                    f"  [!] Ollama returned status {response.status_code}. Retry {attempt+1}/{max_retries}"
                )
        except Exception as e:
            print(f"  [!] LLM Attempt {attempt+1} Error: {e}")

    return f"Klinischer Bericht vom {target_date_str}. Die Dokumentation erfolgt nach Standardvorgabe aufgrund technischer Verzögerung."


# --- Helpers ---


def draw_dynamic_header(canvas, doc, inst, kdl_code, date_str, fall_id):
    canvas.saveState()
    canvas.setStrokeColor(inst["color"])
    canvas.setLineWidth(0.5)

    if inst["header_type"] == "standard":
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(20 * mm, A4[1] - 15 * mm, inst["name"])
        canvas.line(20 * mm, A4[1] - 17 * mm, A4[0] - 20 * mm, A4[1] - 17 * mm)
    elif inst["header_type"] == "modern":
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawCentredString(A4[0] / 2, A4[1] - 20 * mm, inst["name"])
        canvas.setFillColor(inst["color"])
        canvas.rect(20 * mm, A4[1] - 25 * mm, A4[0] - 40 * mm, 1 * mm, fill=1)
    elif inst["header_type"] == "classic":
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawRightString(A4[0] - 20 * mm, A4[1] - 15 * mm, inst["name"])
    elif inst["header_type"] == "minimal":
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(20 * mm, A4[1] - 12 * mm, inst["name"])

    kdl_name = KDL_REGISTRY.get(kdl_code, "Unbekannt")
    canvas.setFont("Helvetica-Oblique", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(
        20 * mm, 10 * mm, f"KDL: {kdl_code} - {kdl_name} | Fall-ID: {fall_id} | Datum: {date_str}"
    )

    canvas.restoreState()
    add_patient_barcode_safe(canvas, doc)
    add_doc_qrcode_safe(canvas, doc)


def add_patient_barcode_safe(canvas, doc):
    canvas.saveState()
    patient_id = "G123456789"
    EAN = barcode.get_barcode_class("code128")
    ean = EAN(patient_id, writer=ImageWriter())
    temp_file = f"temp_barcode_{uuid.uuid4().hex[:6]}"
    ean.save(temp_file)
    canvas.drawImage(f"{temp_file}.png", 20 * mm, A4[1] - 30 * mm, width=35 * mm, height=12 * mm)
    canvas.restoreState()
    if os.path.exists(f"{temp_file}.png"):
        os.remove(f"{temp_file}.png")


def add_doc_qrcode_safe(canvas, doc):
    canvas.saveState()
    doc_id = f"DOC-{uuid.uuid4().hex[:8]}"
    qr = qrcode.QRCode(box_size=3, border=1)
    qr.add_data(doc_id)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    temp_file = f"temp_qr_{uuid.uuid4().hex[:6]}.png"
    img.save(temp_file, format="PNG")
    canvas.drawImage(temp_file, A4[0] - 35 * mm, 10 * mm, width=15 * mm, height=15 * mm)
    canvas.restoreState()
    if os.path.exists(temp_file):
        os.remove(temp_file)


# --- Specialized Generators ---


def generate_discharge_brief(output_path, patient_name, date_str, inst, fall_id, scenario_context):
    prompt = f"Schreibe einen DIN-konformen Entlassungsbericht für {patient_name}. Kontext: {scenario_context}. Erwähne Diagnosen, Verlauf und Medikation."
    content = generate_llm_text(
        prompt, context=f"Arztbrief Fall {fall_id}", target_date_str=date_str
    )
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=40 * mm)
    story = [Paragraph("ENTLASSUNGSBERICHT", STYLES["MedicalHeader"]), Spacer(1, 5 * mm)]
    for p in content.split("\n\n"):
        story.append(Paragraph(p.replace("\n", "<br/>"), STYLES["MedicalBody"]))
    doc.build(
        story,
        onFirstPage=lambda c, d: draw_dynamic_header(c, d, inst, "AD010103", date_str, fall_id),
    )


def generate_outpatient_letter(
    output_path, patient_name, date_str, inst, fall_id, scenario_context
):
    prompt = f"Schreibe einen Ambulanzbrief für {patient_name}. Kontext: {scenario_context}. Erwähne kurz den Status Quo und die nächsten Schritte."
    content = generate_llm_text(
        prompt, context=f"Ambulanzbrief Fall {fall_id}", target_date_str=date_str
    )
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=40 * mm)
    story = [Paragraph("AMBULANZBRIEF", STYLES["MedicalHeader"]), Spacer(1, 5 * mm)]
    for p in content.split("\n\n"):
        story.append(Paragraph(p.replace("\n", "<br/>"), STYLES["MedicalBody"]))
    doc.build(
        story,
        onFirstPage=lambda c, d: draw_dynamic_header(c, d, inst, "AD010111", date_str, fall_id),
    )


def generate_imaging_report(
    output_path, title, date_str, inst, fall_id, kdl_code, scenario_context
):
    prompt = f"Schreibe einen Befundbericht für {title}. Kontext: {scenario_context}. Nutze medizinische Fachbegriffe."
    content = generate_llm_text(
        prompt, context=f"Befund für Fall {fall_id}", target_date_str=date_str
    )
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=40 * mm)
    story = [Paragraph(title, STYLES["MedicalHeader"]), Spacer(1, 5 * mm)]
    for p in content.split("\n\n"):
        story.append(Paragraph(p, STYLES["MedicalBody"]))
    doc.build(
        story, onFirstPage=lambda c, d: draw_dynamic_header(c, d, inst, kdl_code, date_str, fall_id)
    )


def generate_lab_results(output_path, date_str, inst, fall_id, hba1c=False, status="sick"):
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=40 * mm)
    data = [["Parameter", "Wert", "Norm"]]
    if hba1c:
        val = (
            round(random.uniform(7.0, 9.5), 1)
            if status == "sick"
            else round(random.uniform(5.5, 6.5), 1)
        )
        data.append(["HbA1c", f"{val} %", "4.0 - 6.0"])

    leuko = round(random.uniform(11, 15), 1) if status == "sick" else round(random.uniform(5, 8), 1)
    crp = random.randint(50, 150) if status == "sick" else random.randint(1, 5)
    data.append(["Leukozyten", f"{leuko} G/l", "4.0 - 10.0"])
    data.append(["CRP", f"{crp} mg/l", "< 5.0"])

    t = Table(data, colWidths=[40 * mm, 30 * mm, 30 * mm])
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ]
        )
    )
    doc.build(
        [Paragraph("LABORBEFUND", STYLES["MedicalHeader"]), t],
        onFirstPage=lambda c, d: draw_dynamic_header(c, d, inst, "LB120103", date_str, fall_id),
    )


def generate_medication_plan(output_path, date_str, inst, fall_id, meds):
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=40 * mm)
    data = [["Medikament", "Dosierung", "Hinweise"]]
    for m in meds:
        data.append(m)

    t = Table(data, colWidths=[60 * mm, 40 * mm, 60 * mm])
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )

    story = [
        Paragraph("BUNDESEINHEITLICHER MEDIKATIONSPLAN", STYLES["MedicalHeader"]),
        Spacer(1, 5 * mm),
        t,
    ]
    doc.build(
        story,
        onFirstPage=lambda c, d: draw_dynamic_header(c, d, inst, "TH130107", date_str, fall_id),
    )


def generate_nursing_curve(
    output_path, date_str, inst, fall_id, data_points, title="VITALWERTE / KURVE"
):
    # Generate Plot
    plt.figure(figsize=(6, 3))
    times = [p[0] for p in data_points]
    values = [p[1] for p in data_points]
    plt.plot(times, values, marker="o", linestyle="-", color="blue")
    plt.title(title)
    plt.grid(True, linestyle="--", alpha=0.6)

    imgdata = BytesIO()
    plt.savefig(imgdata, format="png", dpi=100)
    plt.close()

    temp_img = f"temp_plot_{uuid.uuid4().hex[:6]}.png"
    with open(temp_img, "wb") as f:
        f.write(imgdata.getvalue())

    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=40 * mm)
    story = [
        Paragraph("STATIONSKURVE", STYLES["MedicalHeader"]),
        Spacer(1, 10 * mm),
        RLImage(temp_img, width=160 * mm, height=80 * mm),
        Spacer(1, 10 * mm),
        Paragraph("Dokumentation der Vitalparameter und Messwerte.", STYLES["MedicalBody"]),
    ]
    doc.build(
        story,
        onFirstPage=lambda c, d: draw_dynamic_header(c, d, inst, "VL160106", date_str, fall_id),
    )
    if os.path.exists(temp_img):
        os.remove(temp_img)


def generate_physio_protocol(output_path, date_str, inst, fall_id, sessions):
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=40 * mm)
    story = [
        Paragraph("PHYSIOTHERAPEUTISCHES PROTOKOLL", STYLES["MedicalHeader"]),
        Spacer(1, 5 * mm),
    ]

    for s in sessions:
        story.append(Paragraph(f"<b>Datum: {s['date']}</b>", STYLES["MedicalSubHeader"]))
        story.append(Paragraph(s["activity"], STYLES["MedicalBody"]))
        story.append(Spacer(1, 3 * mm))
    doc.build(
        story,
        onFirstPage=lambda c, d: draw_dynamic_header(c, d, inst, "TH060103", date_str, fall_id),
    )


def generate_nursing_log(output_path, date_str, inst, fall_id, day_context):
    prompt = f"Schreibe kurze Pflegebucheinträge für einen Patienten. Kontext: {day_context}."
    content = generate_llm_text(prompt, context=f"Pflege Fall {fall_id}", target_date_str=date_str)
    doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=40 * mm)
    story = [Paragraph("PFLEGEBERICHT", STYLES["MedicalHeader"]), Spacer(1, 5 * mm)]
    for line in content.split("\n"):
        if line.strip():
            story.append(Paragraph(line, STYLES["NursingNote"]))
    doc.build(
        story,
        onFirstPage=lambda c, d: draw_dynamic_header(c, d, inst, "VL160105", date_str, fall_id),
    )


def generate_dicom(output_path, patient_name, patient_id, date_str, study_description):
    """
    Generates a mock DICOM file with basic metadata and a simple noise/gradient image.
    """
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = pydicom.uid.SecondaryCaptureImageStorage
    file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    file_meta.ImplementationClassUID = pydicom.uid.generate_uid()

    ds = FileDataset(output_path, {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.PatientName = patient_name
    ds.PatientID = patient_id
    ds.ContentDate = date_str.replace(".", "")
    ds.ContentTime = "120000"
    ds.Modality = "CR"
    ds.StudyDescription = study_description
    ds.SeriesDescription = "Static Capture"
    ds.StudyInstanceUID = pydicom.uid.generate_uid()
    ds.SeriesInstanceUID = pydicom.uid.generate_uid()
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID

    # Create a dummy image
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelRepresentation = 0
    ds.HighBit = 15
    ds.BitsStored = 16
    ds.BitsAllocated = 16
    ds.Columns = 512
    ds.Rows = 512
    pixel_data = np.random.randint(0, 2**16 - 1, (512, 512), dtype=np.uint16)
    ds.PixelData = pixel_data.tobytes()

    ds.save_as(output_path)
    return ds.StudyInstanceUID


# --- Degradation ---


def apply_hardware_degradation(image):
    img_array = np.array(image)
    h, w, c = img_array.shape
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
    image = image.rotate(
        random.uniform(-1.2, 1.2), resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255)
    )
    return image


def degrade_pdf_to_scan(clean_pdf, dirty_pdf):
    try:
        doc = fitz.open(clean_pdf)
        images = []
        for page in doc:
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(apply_hardware_degradation(img))
        doc.close()
        if images:
            images[0].save(
                dirty_pdf, save_all=True, append_images=images[1:], resolution=150.0, quality=75
            )
        os.remove(clean_pdf)
    except Exception as e:
        print(f"Scan Error: {e}")


# --- ORCHESTRATOR ---


def main():
    base_dir = Path("data/inbound")
    p_name = "Gina Lisa"
    p_id = "G123456789"
    print(f"\n--- Generating {p_name} ({p_id}) ---")

    # 2002: Birth
    print("-> 2002: Birth")
    f_id = "FALL_2002_BIRTH"
    f_dir = base_dir / p_id / f_id
    f_dir.mkdir(parents=True, exist_ok=True)
    generate_discharge_brief(
        "temp.pdf",
        p_name,
        "14.11.2002",
        INSTITUTIONS[0],
        f_id,
        "Spontangeburt, Apgar 9/10/10. Gesundes Neugeborenes.",
    )
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_AD010103_GEBURT.pdf"))

    # 2006: Diabetes Diagnosis
    print("-> 2006: Diabetes Diagnosis")
    f_id = "FALL_2006_DIABETES"
    f_dir = base_dir / p_id / f_id
    f_dir.mkdir(parents=True, exist_ok=True)
    start_date = datetime.date(2006, 1, 10)
    for day in range(5):
        ds = (start_date + datetime.timedelta(days=day)).strftime("%d.%m.%Y")
        generate_nursing_log(
            "temp.pdf", ds, INSTITUTIONS[0], f_id, "Insulin-Einstellung, Schulung der Eltern."
        )
        degrade_pdf_to_scan("temp.pdf", str(f_dir / f"KDL_VL160105_PFLEGE_D{day}.pdf"))
    generate_lab_results("temp.pdf", "15.01.2006", INSTITUTIONS[0], f_id, hba1c=True, status="sick")
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_LB120103_LAB.pdf"))

    # NEW: Medication Plan
    meds = [
        ["Actrapid", "10-12-10", "S.C. vor Mahlzeit"],
        ["Protaphane", "0-0-20", "S.C. zur Nacht"],
    ]
    generate_medication_plan("temp.pdf", "15.01.2006", INSTITUTIONS[0], f_id, meds)
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_TH130107_MEDPLAN.pdf"))

    # NEW: Nursing Curve (Blood Sugar)
    bs_data = [("08:00", 240), ("12:00", 180), ("18:00", 210), ("22:00", 150)]
    generate_nursing_curve(
        "temp.pdf", "15.01.2006", INSTITUTIONS[0], f_id, bs_data, title="Blutzuckerspiegel (mg/dl)"
    )
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_VL160106_KURVE.pdf"))

    # NEW: Physio/Education Protocol
    sessions = [
        {"date": "12.01.2006", "activity": "Schulung der Injektionstechnik."},
        {"date": "14.01.2006", "activity": "Ernährungsberatung BE-Berechnung."},
    ]
    generate_physio_protocol("temp.pdf", "15.01.2006", INSTITUTIONS[0], f_id, sessions)
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_TH060103_BERATUNG.pdf"))

    generate_discharge_brief(
        "temp.pdf",
        p_name,
        "15.01.2006",
        INSTITUTIONS[0],
        f_id,
        "Neudiagnose Diabetes Mellitus Typ 1. Einstellung auf ICT.",
    )
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_AD010103_BRIEF.pdf"))

    # 2007-2026: Diabetes Follow-up
    for year in range(2007, 2027):
        if year in [2012, 2020]:
            continue  # Specialized years
        print(f"-> {year}: Diabetes Checkup")
        f_id = f"FALL_{year}_DIAB_KONTROLLE"
        f_dir = base_dir / p_id / f_id
        f_dir.mkdir(parents=True, exist_ok=True)
        ds = f"15.03.{year}"
        generate_outpatient_letter(
            "temp.pdf",
            p_name,
            ds,
            INSTITUTIONS[2],
            f_id,
            f"Regelmäßige Diabetes-Kontrolle {year}. HbA1c stabil.",
        )
        degrade_pdf_to_scan("temp.pdf", str(f_dir / f"KDL_AD010111_CHECK_{year}.pdf"))

    # 2012: Appendectomy (Expanded Full Stack)
    print("-> 2012: Appendectomy (Full Record)")
    f_id = "FALL_2012_APPENDIX"
    f_dir = base_dir / p_id / f_id
    f_dir.mkdir(parents=True, exist_ok=True)

    # Pre-OP Lab
    generate_lab_results(
        "temp.pdf", "04.07.2012", INSTITUTIONS[0], f_id, hba1c=False, status="sick"
    )
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_LB120103_LAB_PRE.pdf"))

    # OP Report
    generate_imaging_report(
        "temp.pdf",
        "OP-BERICHT",
        "05.07.2012",
        INSTITUTIONS[0],
        f_id,
        "OP150103",
        "Laparoskopische Appendektomie bei akuter Appendizitis.",
    )
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_OP150103_OP.pdf"))

    # Post-OP Ward stay (4 days)
    for day in range(4):
        ds = (datetime.date(2012, 7, 5) + datetime.timedelta(days=day)).strftime("%d.%m.%Y")
        generate_nursing_log(
            "temp.pdf", ds, INSTITUTIONS[0], f_id, f"Post-OP Tag {day}. Wundkontrolle, Kostaufbau."
        )
        degrade_pdf_to_scan("temp.pdf", str(f_dir / f"KDL_VL160105_PFLEGE_D{day}.pdf"))

    # Post-OP Lab (Control)
    generate_lab_results(
        "temp.pdf", "07.07.2012", INSTITUTIONS[0], f_id, hba1c=False, status="normal"
    )
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_LB120103_LAB_POST.pdf"))

    # Medication Plan at discharge
    meds = [
        ["Ibuprofen 400", "1-1-1", "Z.n. Appendektomie. Bedarf!"],
        ["Pantoprazol 20", "1-0-0", "Magenschutz"],
    ]
    generate_medication_plan("temp.pdf", "08.07.2012", INSTITUTIONS[0], f_id, meds)
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_TH130107_MEDPLAN.pdf"))

    # Discharge Brief
    generate_discharge_brief(
        "temp.pdf",
        p_name,
        "08.07.2012",
        INSTITUTIONS[0],
        f_id,
        "Akute Appendizitis, unkomplizierter postoperativer Verlauf. Entlassung in die Häuslichkeit.",
    )
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_AD010103_BRIEF.pdf"))

    # 2020: Hip Fracture
    print("-> 2020: Hip Fracture (inc. DICOM)")
    f_id = "FALL_2020_HIP_FX"
    f_dir = base_dir / p_id / f_id
    f_dir.mkdir(parents=True, exist_ok=True)
    d_dir = f_dir / "DICOM"
    d_dir.mkdir(exist_ok=True)

    generate_outpatient_letter(
        "temp.pdf",
        p_name,
        "20.09.2020",
        INSTITUTIONS[0],
        f_id,
        "Notaufnahme nach Sturz beim Reiten. V.a. Schenkelhalsfraktur.",
    )
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_AD010111_NOTAUFNAHME.pdf"))

    # Pre-OP DICOM & Report
    study_uid = generate_dicom(
        str(d_dir / f"STUDY_{uuid.uuid4().hex[:6]}.dcm"),
        p_name,
        p_id,
        "20.09.2020",
        "Röntgen Becken/Hüfte",
    )
    pacs_id = f"PACS-{uuid.uuid4().hex[:8].upper()}"
    generate_imaging_report(
        "temp.pdf",
        "RÖNTGEN BECKEN/HÜFTE",
        "20.09.2020",
        INSTITUTIONS[1],
        f_id,
        "DG020110",
        f"Mediale Schenkelhalsfraktur rechts, verschoben. PACS-Link: {pacs_id}, StudyUID: {study_uid}",
    )
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_DG020110_XRAY.pdf"))

    generate_imaging_report(
        "temp.pdf",
        "OP-BERICHT",
        "21.09.2020",
        INSTITUTIONS[0],
        f_id,
        "OP150103",
        "ORIF Schenkelhalsfraktur mittels DHS (Dynamische Hüftschraube).",
    )
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_OP150103_OP.pdf"))

    # Post-OP DICOM (Control)
    study_uid_post = generate_dicom(
        str(d_dir / f"STUDY_{uuid.uuid4().hex[:6]}.dcm"),
        p_name,
        p_id,
        "25.09.2020",
        "Röntgen Kontrolle post-OP",
    )
    generate_imaging_report(
        "temp.pdf",
        "RÖNTGEN KONTROLLE",
        "25.09.2020",
        INSTITUTIONS[1],
        f_id,
        "DG020110",
        f"Lagekontrolle DHS re. Achsgerechte Stellung. PACS-ID: {pacs_id}, StudyUID: {study_uid_post}",
    )
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_DG020110_CONTROL.pdf"))

    # NEW: Medication Plan
    meds = [
        ["Clexane 40mg", "0-0-1", "S.C. Thromboseprophylaxe"],
        ["Metamizol 500", "1-1-1-1", "Bedarf bei Schmerz"],
    ]
    generate_medication_plan("temp.pdf", "28.09.2020", INSTITUTIONS[0], f_id, meds)
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_TH130107_MEDPLAN.pdf"))

    # NEW: Nursing Curve (Vital Signs/Pain)
    pain_data = [("Tag 1", 8), ("Tag 3", 5), ("Tag 5", 3), ("Tag 7", 2)]
    generate_nursing_curve(
        "temp.pdf", "28.09.2020", INSTITUTIONS[0], f_id, pain_data, title="Schmerzskala (VAS)"
    )
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_VL160106_KURVE.pdf"))

    # NEW: Physio Protocol
    sessions = [
        {"date": "23.09.2020", "activity": "Erste Mobilisation Bettkante."},
        {"date": "25.09.2020", "activity": "Gehtraining mit Unterarmgehstützen."},
    ]
    generate_physio_protocol("temp.pdf", "28.09.2020", INSTITUTIONS[0], f_id, sessions)
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_TH060103_PHYSIO.pdf"))

    generate_discharge_brief(
        "temp.pdf",
        p_name,
        "28.09.2020",
        INSTITUTIONS[0],
        f_id,
        "Operative Versorgung einer Schenkelhalsfraktur. Mobilisation unter Teilbelastung.",
    )
    degrade_pdf_to_scan("temp.pdf", str(f_dir / "KDL_AD010103_BRIEF.pdf"))

    print("\nGeneration complete.")


if __name__ == "__main__":
    main()
