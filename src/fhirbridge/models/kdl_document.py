from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RendererType(StrEnum):
    DIN5008 = "DIN5008"
    TABULAR = "TABULAR"
    KBV_FORM = "KBV_FORM"


class KdlDocumentBase(BaseModel):
    """
    Base definition of a KDL Document for synthetic generation.
    """

    model_config = ConfigDict(extra="forbid")

    renderer_type: RendererType = Field(
        default=RendererType.DIN5008, description="The renderer to use for the PDF"
    )
    kdl_code: str = Field(..., description="The KDL Code (e.g., AD010103)")
    kdl_name: str = Field(..., description="The name of the KDL document type")
    patient_id: str = Field(..., description="Simulated Patient ID")
    patient_name: str = Field(..., description="Full Name of the patient")
    fall_id: str = Field(..., description="The Case/Encounter ID")
    document_date: str = Field(..., description="Date of the document in DD.MM.YYYY format")


class DischargeBrief(KdlDocumentBase):
    """
    KDL: AD010103 (Entlassungsbericht intern) or AD010111 (Ambulanzbrief)
    """

    title: str = Field(..., description="Title of the discharge brief, e.g. 'ENTLASSUNGSBERICHT'")
    content_paragraphs: list[str] = Field(
        ..., description="The clinical text paragraphs of the discharge brief."
    )


class NursingLogEntry(BaseModel):
    timestamp: str = Field(
        ..., description="Time of the shift or entry, e.g. 'Frühschicht' or '08:00'"
    )
    pflegekraft_kuerzel: str = Field(
        ..., description="Kürzel der Pflegekraft, z.B. 'Schwester S.M.'"
    )
    note: str = Field(..., description="The nursing note text")


class NursingWardDoc(KdlDocumentBase):
    """
    KDL: VL160105 (Fieberkurve / Pflegebericht)
    """

    renderer_type: RendererType = Field(
        default=RendererType.TABULAR, description="The renderer to use for the PDF"
    )
    title: str = Field("PFLEGEBERICHT", description="Title of the nursing log")
    entries: list[NursingLogEntry] = Field(..., description="Entries in the nursing log")


class SurgeryReport(KdlDocumentBase):
    """
    KDL: OP150103 (OP-Bericht)
    """

    renderer_type: RendererType = Field(
        default=RendererType.DIN5008, description="The renderer to use for the PDF"
    )
    title: str = Field(..., description="Title of the surgical report, e.g. 'OPERATIONSBERICHT'")
    content_paragraphs: list[str] = Field(..., description="The surgical text paragraphs.")
    surgeons: list[str] = Field(..., description="List of surgeons involved in the operation.")


class ImagingReport(KdlDocumentBase):
    """
    KDL: DG020103 (CT-Befund), DG020110 (Röntgenbefund), PT080102 (Histologiebefund)
    """

    renderer_type: RendererType = Field(
        default=RendererType.DIN5008, description="The renderer to use for the PDF"
    )
    title: str = Field(
        ..., description="Title of the report, e.g. 'MAMMOGRAPHIE' or 'RÖNTGEN THORAX'"
    )
    findings: list[str] = Field(..., description="The detailed diagnostic findings paragraphs.")
    conclusion: str = Field(..., description="The final conclusion or summary of the findings.")


class LabParameter(BaseModel):
    name: str = Field(..., description="Name of the parameter, e.g. 'Leukozyten'")
    value: str = Field(..., description="Value with unit, e.g. '12.5 G/l'")
    reference_range: str = Field(..., description="Reference normal range, e.g. '4-10'")


class LabResults(KdlDocumentBase):
    """
    KDL: LB120103 (Laborbefund intern)
    """

    renderer_type: RendererType = Field(
        default=RendererType.TABULAR, description="The renderer to use for the PDF"
    )
    title: str = Field("LABORBEFUND", description="Title of the lab report")
    parameters: list[LabParameter] = Field(..., description="List of measured lab parameters")


class Prescription(KdlDocumentBase):
    """
    Muster 16 (Rezept)
    """

    renderer_type: RendererType = Field(
        default=RendererType.KBV_FORM, description="The renderer to use for the PDF"
    )
    medications: list[str] = Field(..., description="List of prescribed medications and dosages")


class WorkIncapacityCertificate(KdlDocumentBase):
    """
    Muster 1 (Arbeitsunfähigkeitsbescheinigung)
    """

    renderer_type: RendererType = Field(
        default=RendererType.KBV_FORM, description="The renderer to use for the PDF"
    )
    start_date: str = Field(..., description="Start date of work incapacity")
    end_date: str = Field(..., description="End date of work incapacity")
    icd_code: str = Field(..., description="Primary ICD code")


# Union type for dynamic handling
DocumentContent = (
    DischargeBrief
    | NursingWardDoc
    | SurgeryReport
    | ImagingReport
    | LabResults
    | Prescription
    | WorkIncapacityCertificate
)
