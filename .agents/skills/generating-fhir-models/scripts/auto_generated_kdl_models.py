"""
Auto-Generated Pydantic Models for KDL Documents.
Generated via Mistral Overnight Factory.
"""

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    kdl_name: str
    patient_id: str
    document_date: str


# ------------------------------------------------------------
# KDL: AB060103 - Laborbefund intern
# Standard: Abrechnungsstandard gemäß InEK/DRG-Vorgaben und §301 SGB V Datensatz
# ------------------------------------------------------------

from pydantic import BaseModel


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class LaborwertZeile(BaseModel):
    wert: float = Field(description="Laborwert")
    einheit: str = Field(description="Einheit des Laborwerts")
    referenzbereich_min: float = Field(description="Unterer Referenzbereich")
    referenzbereich_max: float = Field(description="Oberer Referenzbereich")


class Laborbefundintern(KdlDocumentBase):
    kdl_code: str = "AB060103"
    patient_id: str = Field(description="Patienten-ID")
    laborwerte: list[LaborwertZeile] = Field(description="Laborwerte des Patienten")


# ------------------------------------------------------------
# KDL: AB060104 - Konsilbericht intern
# Standard: Abrechnungsstandard gemäß InEK/DRG-Vorgaben und §301 SGB V Datensatz
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    document_type: str
    sender_institution_id: str
    recipient_institution_id: str
    creation_time: datetime
    sender_healthcare_provider_id: str
    recipient_healthcare_provider_id: str
    patient_id: str


class Konsilberichtintern(KdlDocumentBase):
    kdl_code: str = Field(default="AB060104", description="KDL-Code für Konsilbericht intern")
    document_type: str = Field(
        default="Konsilbericht intern", description="Art des medizinischen Dokuments"
    )
    sender_institution_id: str
    recipient_institution_id: str
    creation_time: datetime
    sender_healthcare_provider_id: str
    recipient_healthcare_provider_id: str
    patient_id: str

    # Weitere relevante Felder können hier definiert werden, z.B. für Tabellenzeilen in Laborwerten


# ------------------------------------------------------------
# KDL: AD010101 - Ärztliche Stellungnahme
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------


from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        allow_population_by_field_name = True


class ArztlicheStellungnahme(KdlDocumentBase):
    dokument_id: str = Field(description="ID des Dokuments")
    dokument_typ: str = Field(description="Typ des Dokuments", const="AD010101")
    patient_information: dict = Field(description="Informationen zum Patienten")
    diagnose: list[str] = Field(description="Diagnosen")
    befund: str = Field(description="Befunde")
    therapie_empfehlung: str = Field(description="Therapieempfehlungen")


# ------------------------------------------------------------
# KDL: AD010102 - Krankheitserreger, unerwünschte Ereig
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class KrankheitserregerUnerwuenschteEreig(KdlDocumentBase):
    dokumenttyp: str = Field(description="Dokumenttyp (AD010102)")
    erstellungszeitpunkt: datetime = Field(description="Erstellungszeitpunkt")
    patient_id: UUID = Field(description="Patient ID")
    krankenhaus_id: UUID = Field(description="Krankenhaus ID")
    behandelnder_arzt: str = Field(description="Behandelnder Arzt")
    diagnose: str = Field(description="Diagnose")
    laborwerte: list[Laborwert] = Field(default_factory=list, description="Laborwerte")


class Laborwert(BaseModel):
    parameter: str = Field(description="Laborparameter")
    wert: float = Field(description="Wert des Parameters")
    einheit: str = Field(description="Einheit des Parameters")


# ------------------------------------------------------------
# KDL: AD010103 - Entlassungsbericht intern
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    version: int = 1


class Entlassungsberichtintern(KdlDocumentBase):
    kdl_code: str = "AD010103"
    version: int = 1

    patient: dict = Field(description="Patientendaten")
    diagnose: list = Field(description="Diagnosen")
    komplikationen: list = Field(description="Komplikationen")
    laborwerte: list[dict] = Field(description="Laborwerte")
    medikamente: list[dict] = Field(description="Verordnete Medikamente")
    entlassungsdatum: str = Field(description="Entlassungsdatum")
    behandelnder_arzt: dict = Field(description="Behandelnder Arzt")


# ------------------------------------------------------------
# KDL: AD010104 - schriftliche Einwilligung, die stationäre Behandlung vorzeitig gegen ärztlichen Rat abzubrechen. Entlassungsbericht extern
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_type: str = Field(description="Art des medizinischen Dokuments")


class RechenEntlassungsberichtExtern(KdlDocumentBase):
    einwilligung_text: str = Field(description="Text der schriftlichen Einwilligung")
    abrechen_grund: str = Field(
        description="Grund für den vorzeitigen Abbruch der stationären Behandlung"
    )
    entlassungsdatum: str = Field(description="Entlassungsdatum des Patienten")
    behandelnder_arzt: str = Field(description="Name des behandelnden Arztes")


# ------------------------------------------------------------
# KDL: AD010105 - individuelle Kostenerstellung der erbrachten Leistungen an den jeweiligen Kostenträger. Reha-Bericht
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_type: str = Field(description="Art des medizinischen Dokuments")


class EiligenKostenträgerRehaBericht(KdlDocumentBase):
    kdl_code: str = "AD010105"
    document_type: str = "Individuelle Kostenerstellung der erbrachten Leistungen an den jeweiligen Kostenträger (Reha-Bericht)"
    patient_id: str = Field(description="Patienten-ID")
    insurance_provider: str = Field(description="Kostenträger")
    treatment_period_start: date = Field(description="Anfang des Behandlungszeitraums")
    treatment_period_end: date = Field(description="Ende des Behandlungszeitraums")
    treatments: list[treatment] = Field(description="Erbrachte Leistungen")


class treatment(BaseModel):
    service_code: str = Field(description="Leistungs-ID")
    service_description: str = Field(description="Beschreibung der Leistung")
    quantity: int = Field(description="Anzahl der erbrachten Leistungen")
    unit_price: float = Field(description="Einheitlicher Preis für die Leistung")


# ------------------------------------------------------------
# KDL: AD010106 - Konsilbericht extern
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    header: dict
    body: dict


class Konsilberichtextern(KdlDocumentBase):
    header: dict = Field(description="Kopfzeile des Dokuments")
    body: dict = Field(
        description="Hauptteil des Dokuments",
        default={
            "header": {
                "sender": {"name": "", "address": ""},
                "receiver": {"name": "", "address": ""},
            },
            "content": {
                "patient_info": {"first_name": "", "last_name": "", "date_of_birth": "", "sex": ""},
                "consultation_reason": "",
                "findings": "",
                "diagnosis": "",
                "treatment": "",
                "recommendations": "",
                "labor_results": {"table": [{"parameter": "", "value": "", "unit": ""}]},
            },
        },
    )


# ------------------------------------------------------------
# KDL: AD010107 - Verlegungsbericht intern
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Verlegungsberichtintern(KdlDocumentBase):
    dokument_id: str = Field(description="Dokument-ID")
    dok_type: str = Field(description="Dokument-Typ")
    dok_zeitpunkt: datetime = Field(description="Dokument-Zeitpunkt")
    patient: dict = Field(description="Patienten-Daten")
    einweisender_arzt: dict = Field(description="Einweisender Arzt")
    verlegungsgrund: str = Field(description="Verlegungsgrund")
    verlegungsziel: dict = Field(description="Verlegungsziel")
    laborwerte: list[dict] = Field(description="Laborwerte (optional)")
    diagnose: str = Field(description="Diagnose")
    behandlungsplan: str = Field(description="Behandlungsplan")


# ------------------------------------------------------------
# KDL: AD010108 - Pflegevisite Vorläufiger Arztbericht
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class PflegevisiteVorläufigerArztbericht(KdlDocumentBase):
    kdl_code: str = "AD010108"
    document_type: str = "Pflegevisite Vorläufiger Arztbericht"

    patient_id: str = Field(description="Patientenkennzeichen")
    patient_name: str = Field(description="Name des Patienten")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    sex: str = Field(description="Geschlecht des Patienten")

    attending_physician: str = Field(description="Arzt, der die Pflegevisite durchgeführt hat")
    visit_date: str = Field(description="Datum der Pflegevisite")
    diagnosis: str = Field(description="Diagnose")

    laboratory_results: list[dict[str, str]] = Field(
        default_factory=list, description="Laborbefunde"
    )


# ------------------------------------------------------------
# KDL: AD010109 - Ärztlicher Befundbericht
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ArztlicherBefundbericht(KdlDocumentBase):
    dokumenttyp: str = Field(description="Art des Dokuments (z.B. AD010109)")
    patient_id: str = Field(description="Patientenkennung")
    patient_name: str = Field(description="Name des Patienten")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    doctor_id: str = Field(description="Identifikationsnummer des Arztes")
    doctor_name: str = Field(description="Name des Arztes")
    report_text: str = Field(description="Textualer Befundbericht")
    diagnosis: list[str] = Field(description="Diagnosen")
    treatment: list[str] = Field(description="Behandlungen")


# ------------------------------------------------------------
# KDL: AD010110 - Ärztlicher Verlaufsbericht
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ArztlicherVerlaufsbericht(KdlDocumentBase):
    dokument_id: str = Field(description="ID des Dokuments")
    dokument_typ: str = Field(description="Typ des Dokuments", const="AD010110")
    patient_id: str = Field(description="ID des Patienten")
    patient_name: str = Field(description="Name des Patienten")
    ArztlicherVerlaufsbericht_Erstellungsdatum: datetime = Field(description="Datum der Erstellung")
    ArztlicherVerlaufsbericht_Autor: str = Field(description="Autor des Dokuments")
    ArztlicherVerlaufsbericht_Text: str = Field(description="Text des Dokuments")


# ------------------------------------------------------------
# KDL: AD010111 - Ambulanzbrief
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    sender: dict = Field(description="Absender des Dokuments")
    recipient: list[dict] = Field(description="Empfänger des Dokuments")


class Ambulanzbrief(KdlDocumentBase):
    kdl_code: str = "AD010111"
    patient: dict = Field(description="Patientendaten")
    diagnosis: str = Field(description="Diagnose")
    treatment: str = Field(description="Behandlung")
    medications: list[str] = Field(description="Verordnete Medikamente")
    laboratory_results: list[dict] = Field(description="Laborergebnisse")


# ------------------------------------------------------------
# KDL: AD010112 - (Krebsfrüherkennung ZervixKarzinom) und 40 (Krebsfrüherkennung Männer) Kurzarztbrief
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class RvixKarzinomUnd40Kurzarztbrief(KdlDocumentBase):
    dokumenttyp: str = Field(default="AD010112", const="AD010112")
    patient: Patient = Field(description="Patientendaten")
    untersuchung: KrebsfrueherkennungUntersuchung = Field(description="Untersuchungsdaten")
    befund: KrebsfrueherkennungBefund = Field(description="Befund")
    anamnese: str = Field(description="Anamnese")
    labor: list[Laborwert] = Field(default_factory=list, description="Laborwerte")
    diagnose: str = Field(description="Diagnose")
    therapieempfehlung: str = Field(description="Therapieempfehlung")


class KrebsfrueherkennungUntersuchung(BaseModel):
    art: KrebsfrueherkennungArt = Field(description="Art der Untersuchung")
    durchgefuehrt_am: datetime = Field(
        description="Datum, an dem die Untersuchung durchgeführt wurde"
    )
    durchgefuhrender_arzt: Arzt = Field(description="Arzt, der die Untersuchung durchgeführt hat")


class KrebsfrueherkennungBefund(BaseModel):
    zervixkarzinom: bool = Field(description="Vorhandensein von Zervixkarzinom")
    mannertumoren: bool = Field(description="Vorhandensein von Tumoren beim Mann")


# ------------------------------------------------------------
# KDL: AD010113 - Nachschaubericht
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class Nachschaubericht(KdlDocumentBase):
    kdl_code: str = "AD010113"
    document_type: str = "Nachschaubericht"

    patient_id: str = Field(description="Patientenkennung")
    doctor_id: str = Field(description="Arztkennung")
    report_date: str = Field(description="Berichtsdatum")

    findings: list[str] = Field(description="Befunde")
    diagnoses: list[str] = Field(description="Diagnosen")


# ------------------------------------------------------------
# KDL: AD010199 - Die Notation der Resteklassen endet immer auf *99. Damit steht die Restklasse immer an letzter Position der Unterklasse und es ist problemlos möglich, weitere spezifische Dokumentenklassen einer Unterklasse hinzuzufügen. Notation Bezeichnung Dokumentenklasse
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class IonBezeichnungDokumentenklasse(KdlDocumentBase):
    notation: str = Field(description="Die Notation der Resteklassen endet immer auf *99.")
    Bezeichnung: str = Field(description="Bezeichnung der Dokumentenklasse")
    Dokumentenklasse: str = Field(description="Dokumentenklasse")


# ------------------------------------------------------------
# KDL: AD020101 - buch Arbeitsunfähigkeitsbescheinigung
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class BuchArbeitsunfaehigkeitsbescheinigung(KdlDocumentBase):
    kdl_code: str = "AD020101"
    patient: dict = Field(description="Patientendaten")
    arbeitsunfaehigkeit: dict = Field(description="Arbeitsunfähigkeitsdauer und Gründe")
    diagnose: list = Field(description="Diagnosen")


# ------------------------------------------------------------
# KDL: AD020102 - Anga
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        allow_population_by_field_name = True
        validate_assignment = True


class Anga(KdlDocumentBase):
    dokument_id: str = Field(description="Dokument-ID")
    dok_type: str = Field(description="Dokument-Typ")
    dok_vers: str = Field(description="Dokument-Version")
    patient: dict = Field(description="Patienteninformationen")
    header: dict = Field(description="Kopfzeile")
    body: dict = Field(description="Hauptteil")
    signature: dict = Field(description="Signatur")


# ------------------------------------------------------------
# KDL: AD020103 - Todesbescheinigung
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Todesbescheinigung(KdlDocumentBase):
    dokumenttyp: str = Field(default="AD020103", description="KDL-Code für Todesbescheinigung")
    patient: Patient = Field(description="Patientendaten")
    erstellender_arzt: Arzt = Field(description="Erstellender Arzt")
    todestag: date = Field(description="Todestag")
    ursache_des_todes: str = Field(description="Ursache des Todes")
    laborwerte: list[Laborwert] = Field(default=[], description="Laborwerte")
    weitere_befunde: str = Field(default="", description="Weitere Befunde")


class Patient(BaseModel):
    name: str
    geburtsdatum: date
    geschlecht: str


class Arzt(BaseModel):
    name: str
    fachrichtung: str


class Laborwert(BaseModel):
    parameter: str
    wert: float
    einheit: str


# ------------------------------------------------------------
# KDL: AD020104 - Ärztliche Bescheinigung
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    document_type: str
    sender: dict
    recipient: list[dict]
    creation_time: datetime
    signature: Signature


class ArztlicheBescheinigung(KdlDocumentBase):
    kdl_code: str = Field(default="AD020104", const=True)
    patient: Patient
    diagnosis: Diagnosis
    medical_justification: MedicalJustification
    issuing_physician: IssuingPhysician
    validity_period: ValidityPeriod


class Patient(BaseModel):
    first_name: str
    last_name: str
    birth_date: date
    street: str
    house_number: str
    postal_code: str
    city: str


class Diagnosis(BaseModel):
    diagnosis_text: str
    icd_codes: list[str]


class MedicalJustification(BaseModel):
    justification_text: str


class IssuingPhysician(BaseModel):
    first_name: str
    last_name: str
    medical_practice: MedicalPractice


class MedicalPractice(BaseModel):
    street: str
    house_number: str
    postal_code: str
    city: str


class ValidityPeriod(BaseModel):
    start_date: date
    end_date: date


# ------------------------------------------------------------
# KDL: AD020105 - Befund des aktuellen Zustands in der Notaufnahme (inkl. Triage). Notfall-/ Vertretungsschein
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class TriageNotfallVertretungsschein(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")
    diagnosis: str = Field(description="Diagnose")
    treatment: str = Field(description="Behandlung")
    discharge_summary: str = Field(description="Entlassungsbrief")
    follow_up_instructions: str = Field(description="Nachsorgeanweisungen")
    notfall_vertretungsschein: bool = Field(description="Notfall-/Vertretungsschein")


# ------------------------------------------------------------
# KDL: AD020106 - Sachauflistung zu Gegenständen, die bei Aufnahme mit in die Einrichtung gebracht wurden. Wiedereingliederungsplan
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class WurdenWiedereingliederungsplan(KdlDocumentBase):
    dokument_id: str = Field(description="Dokument-ID")
    patient_id: str = Field(description="Patient-ID")
    einrichtungs_id: str = Field(description="Einrichtungs-ID")
    aufnahme_datum: str = Field(description="Aufnahmedatum")
    entlassungs_datum: str = Field(description="Entlassungsdatum")
    sachauflistung: list[dict[str, str]] = Field(
        description="Sachauflistung zu Gegenständen, die bei Aufnahme mit in die Einrichtung gebracht wurden."
    )
    wiedereingliederungsplan: dict[str, str] = Field(description="Wiedereingliederungsplan")


# ------------------------------------------------------------
# KDL: AD020107 - nisse über die Messung der Funktionalität des Gehörs. Aufenthaltsbescheinigung
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class GehörsAufenthaltsbescheinigung(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    birth_date: str = Field(description="Geburtsdatum")
    measurement_date: str = Field(description="Messungsdatum")
    left_ear_frequency1: float = Field(description="Linkes Ohr Frequenz 1")
    left_ear_frequency2: float = Field(description="Linkes Ohr Frequenz 2")
    right_ear_frequency1: float = Field(description="Rechtes Ohr Frequenz 1")
    right_ear_frequency2: float = Field(description="Rechtes Ohr Frequenz 2")


# ------------------------------------------------------------
# KDL: AD020108 - Geburtsanzeige
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Geburtsanzeige(KdlDocumentBase):
    kdl_code: str = "AD020108"
    patient: Patient = Field(description="Patientendaten")
    geburtsdatum: datetime = Field(description="Geburtsdatum des Kindes")
    geschlecht: Geschlecht = Field(description="Geschlecht des Kindes")
    mutterliche_krankengeschichte: str = Field(description="Mutterliche Krankengeschichte")
    vaterliche_krankengeschichte: str = Field(description="Vaterliche Krankengeschichte")
    geburtsverlauf: Geburtsverlauf = Field(description="Verlauf der Geburt")
    neonatologie: Neonatologie = Field(description="Neonatologische Befunde und Maßnahmen")


class Patient(BaseModel):
    name: str
    geburtsdatum: datetime
    adresse: Adresse


class Adresse(BaseModel):
    strasse: str
    plz: str
    ort: str


class Geburtsverlauf(BaseModel):
    wehenbeginn: datetime = Field(description="Zeitpunkt des Wehenbeginns")
    geburt: Geburt = Field(description="Verlauf der Geburt")


class Geburt(BaseModel):
    geburtsart: Geburtsart
    geburtsdauer: timedelta = Field(description="Dauer der Geburt in Minuten")
    newborn_status: NewbornStatus = Field(description="Neugeborenenstatus")


class Neonatologie(BaseModel):
    apgar_werte: ApgarWerte = Field(description="APGAR-Werte")
    laborwerte: list[Laborwert] = Field(description="Laborwerte des Neugeborenen")


class ApgarWerte(BaseModel):
    eine_minute: int
    fünf_minuten: int
    zehn_minuten: int


class Laborwert(BaseModel):
    parameter: str
    wert: float
    einheit: str


# ------------------------------------------------------------
# KDL: AD020199 - Sonstiger Arztbericht
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class SonstigerArztbericht(KdlDocumentBase):
    kdl_code: str = "AD020199"
    document_type: str = "Sonstiger Arztbericht"

    patient_id: str = Field(description="Patienten-ID")
    doctor_id: str = Field(description="Arzt-ID")
    report_date: str = Field(description="Berichtsdatum")
    diagnosis: str = Field(description="Diagnose")


# ------------------------------------------------------------
# KDL: AD020201 - operative Visite Anatomische Skizze
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class OperativeVisiteAnatomischeSkizze(KdlDocumentBase):
    dokument_id: UUID = Field(description="Identifikationsnummer des Dokuments")
    dokument_typ: Literal["AD020201"] = Field(
        description="KDL-Code für operative Visite Anatomische Skizze"
    )
    patient_id: UUID = Field(description="Identifikationsnummer des Patienten")
    erstellungszeitpunkt: datetime = Field(
        description="Datum und Uhrzeit der Erstellung des Dokuments"
    )
    erstellender_arzt: str = Field(description="Name des erstellenden Arztes", max_length=255)
    anatomische_befunde: list[str] = Field(description="Anatomische Befunde in Form von Textzeilen")
    skizzenbild: bytes | None = Field(description="Skizzenbild als Byte-Array (optional)")
    operationstechniker: str | None = Field(
        description="Name des Operationstechnikers (optional)", max_length=255
    )
    anzahl_skizzenbilder: int = Field(description="Anzahl der Skizzenbilder im Dokument")
    skizzenbild_dateiname: str | None = Field(
        description="Dateiname des Skizzenbilds (optional)", max_length=255
    )


# ------------------------------------------------------------
# KDL: AD020202 - Blutgruppenausweis
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------


from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Blutgruppenausweis(KdlDocumentBase):
    dokument_id: str = Field(description="Dokument-ID")
    patient: dict = Field(description="Patienteninformationen")
    ausstellungsdatum: str = Field(description="Ausstellungsdatum im Format TT.MM.JJJJ")
    rhesusfaktor: str = Field(description="Rhesus-Faktor (positiv oder negativ)")
    blutgruppe: str = Field(description="Blutgruppe")
    laborwerte: list[dict] = Field(description="Laborwerte")

    class Config:
        extra = "forbid"


# ------------------------------------------------------------
# KDL: AD020203 - ben des Sozialdienstes zu empfohlenen Maßnahmen. Beinhaltet auch Notizen des Gesprächsverlaufes und festgelegte Vereinbarungen. Bericht Gesundheitsuntersuchung
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class BerichtGesundheitsuntersuchung(KdlDocumentBase):
    patient: dict = Field(description="Patientendaten")
    anamnese: str = Field(description="Anamnese")
    diagnose: str = Field(description="Diagnose")
    empfohlene_massnahmen: list = Field(description="Empfohlene Maßnahmen")
    gespraechsverlauf: str = Field(description="Gesprächsverlauf")
    vereinbarungen: dict = Field(description="Festgelegte Vereinbarungen")
    laborwerte: dict = Field(description="Laborwerte")


# ------------------------------------------------------------
# KDL: AD020204 - Krankenbeförderung) Krebsfrüherkennung
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code")
    sender: dict = Field(description="Absender des Dokuments")
    recipient: list = Field(description="Empfänger des Dokuments")


class KrebsfrüherkennungTabelle(BaseModel):
    tabellen_name: str = Field(description="Name der Tabelle")
    tabellen_inhalt: list = Field(description="Inhalt der Tabelle")


class KrankenbeförderungKrebsfrüherkennung(KdlDocumentBase):
    kdl_code: str = "AD020204"
    sender: dict
    recipient: list
    patient: dict = Field(description="Patientendaten")
    diagnosis: str = Field(description="Diagnose")
    treatment: str = Field(description="Behandlung")
    lab_results: KrebsfrüherkennungTabelle = Field(description="Laborergebnisse")


# ------------------------------------------------------------
# KDL: AD020205 - ben zur Meldung von Krebserkrankungen an das Krebsregister. Messblatt
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    version: str
    sender: dict
    receiver: dict
    creation_time: datetime
    signature: dict


class benzurMeldungvonKrebserkrankungenandasKrebsregister(Messblatt(KdlDocumentBase)):
    kdl_code = Field("AD020205", const=True)
    patient: dict = Field(description="Patientendaten")
    disease: dict = Field(description="Erkrankungsdaten")
    treatment: dict = Field(description="Behandlungsdaten")
    follow_up: dict = Field(description="Nachsorgedaten")


# ------------------------------------------------------------
# KDL: AD020206 - ben zum Umfang einer Behandlung und die damit verbundenen Rechte und Pflichten zwischen Einrichtung und Patient. Belastungserprobung
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Belastungserprobung(KdlDocumentBase):
    dokument_typ: str = Field(description="Dokumenttyp (z.B. AD020206)")
    patient_id: str = Field(description="Patientenkennung")
    einrichtung_id: str = Field(description="Einrichtungskennung")
    behandlungsumfang: str = Field(description="Umfang der Behandlung")
    rechte_pflichten_einrichtung: str = Field(description="Rechte und Pflichten der Einrichtung")
    rechte_pflichten_patient: str = Field(description="Rechte und Pflichten des Patienten")


# ------------------------------------------------------------
# KDL: AD020207 - Ärztlicher Fragebogen
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    creation_date: datetime = Field(description="Erstellungsdatum des Dokuments")


class LaborwertZeile(BaseModel):
    parameter: str = Field(description="Laborparameter")
    wert: float = Field(description="Messwert des Parameters")
    einheit: str = Field(description="Einheit des Messwerts")


class ArztlicherFragebogen(KdlDocumentBase):
    kdl_code: str = "AD020207"
    patient_id: uuid.UUID = Field(description="Patienten-ID")
    frage_1: str = Field(description="Antwort auf Frage 1")
    frage_2: str = Field(description="Antwort auf Frage 2")
    laborwerte: list[LaborwertZeile] = Field(
        default_factory=list, description="Laborwerte des Patienten"
    )


# ------------------------------------------------------------
# KDL: AD020208 - Befund extern
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    document_id: str = Field(description="Dokument-ID")
    document_type: str = Field(description="Dokumenttyp")


class Befundextern(KdlDocumentBase):
    document_type: str = "AD020208"
    patient_id: str = Field(description="Patient-ID")
    sender_practice_id: str = Field(description="Absender-Praxis-ID")
    recipient_practice_id: str = Field(description="Empfänger-Praxis-ID")
    creation_time: datetime = Field(description="Erstellungsdatum und -zeit")
    diagnosis: list[str] = Field(description="Diagnosen")
    findings: list[str] = Field(description="Befunde")
    recommendations: list[str] = Field(description="Empfehlungen")


# ------------------------------------------------------------
# KDL: AD020299 - Sonstige Bescheinigung
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------


from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class SonstigeBescheinigung(KdlDocumentBase):
    dokument_id: str = Field(description="Dokument-ID")
    dok_type: str = Field(description="Dokument-Typ")
    sender_institution_id: str = Field(description="Sender-Institution-ID")
    recipient_institution_id: str = Field(description="Empfänger-Institution-ID")
    creation_time: int = Field(description="Erstellungszeitpunkt")
    signature: str = Field(description="Signatur")

    patient: dict = Field(description="Patientendaten")
    diagnosis: dict = Field(description="Diagnosen")
    treatment: dict = Field(description="Behandlungen")
    findings_list: list[dict] = Field(default_factory=list, description="Befunde")


# ------------------------------------------------------------
# KDL: AD060101 - relevanten Daten zu einer angeforderten Blutkonserve. Konsilanforderung
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class NBlutkonserveKonsilanforderung(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum")
    blood_product_code: str = Field(description="Blutprodukt-Code")
    blood_group: str = Field(description="Blutgruppe")
    required_amount: float = Field(description="Erforderliche Menge")
    requested_by: str = Field(description="Angefragt von")


# ------------------------------------------------------------
# KDL: AD060103 - vor Aufnahme einer Psychotherapie) Konsilbericht intern
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class VorAufnahmeeinerPsychotherapieKonsilberichtintern(KdlDocumentBase):
    kdl_code: str = "AD060103"
    document_type: str = "vor Aufnahme einer Psychotherapie Konsilbericht intern"

    patient_id: str = Field(description="Patientenkennnummer")
    patient_name: str = Field(description="Name des Patienten")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    sex: str = Field(description="Geschlecht des Patienten")

    diagnosis: str = Field(description="Diagnose")
    treatment_plan: str = Field(description="Behandlungsplan")


# ------------------------------------------------------------
# KDL: AD060104 - Anforderung/Anmeldung einer Befundung durch einen Facharzt aus einem weiteren Leistungsbereich. Konsilbericht extern
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"
        allow_population_by_field_name = True


class UngFacharztKonsilberichtextern(KdlDocumentBase):
    art: str
    kdl_code: str
    sender: dict
    recipient: list[dict]
    subject: str
    text: str
    attachments: list[str]


# ------------------------------------------------------------
# KDL: AD060105 - Visitenprotokoll
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------


from pydantic import BaseModel, Field


class Visitenprotokoll(KdlDocumentBase):
    dokumenttyp: str = Field(default="AD060105", description="KDL-Code für Visitenprotokoll")
    patient: Patient = Field(description="Patientendaten")
    behandelnder_arzt: Arzt = Field(description="Behandelnder Arzt")
    mitarbeitende_ärzte: list[Arzt] = Field(default=[], description="Mitwirkende Ärzte")
    visite_datum: datetime = Field(description="Datum der Visite")
    diagnose: str = Field(description="Diagnose")
    laborwerte: list[Laborwert] = Field(default=[], description="Laborwerte")
    medikamente: list[Medikament] = Field(default=[], description="Verschriebene Medikamente")


class Patient(BaseModel):
    name: str
    geburtsdatum: datetime
    geschlecht: str


class Arzt(BaseModel):
    name: str
    fachrichtung: str


class Laborwert(BaseModel):
    parameter: str
    wert: float
    einheit: str


# ------------------------------------------------------------
# KDL: AD060107 - Teambesprechungsprotokoll
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Teambesprechungsprotokoll(KdlDocumentBase):
    dokumenttyp: str = Field(description="Dokumenttyp (AD060107)")
    version: str = Field(description="Version des Dokuments")
    autor: str = Field(description="Autor des Dokuments")
    erstellungsdatum: str = Field(description="Erstellungsdatum des Dokuments")
    betroffener_patient: dict = Field(description="Betroffener Patient")
    beschwerdebeschreibung: str = Field(description="Beschwerdebeschreibung")
    diagnose: str = Field(description="Diagnose")
    behandlungsplan: str = Field(description="Behandlungsplan")


# ------------------------------------------------------------
# KDL: AD060108 - persönliche und organisatorische Anga
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class PersönlicheundorganisatorischeAnga(KdlDocumentBase):
    patienten_id: str = Field(description="Patienten-ID")
    name_vorname: str = Field(description="Name und Vorname des Patienten")
    geburtsdatum: str = Field(description="Geburtstag des Patienten im Format TT.MM.JJJJ")
    geschlecht: str = Field(description="Geschlecht des Patienten (männlich, weiblich oder divers)")
    adresse_strasse: str = Field(description="Straße und Hausnummer des Patienten")
    adresse_plz_ort: str = Field(description="Postleitzahl und Ort des Patienten")
    kontakt_tel: str = Field(description="Telefonnummer des Patienten")
    kontakt_email: str = Field(description="E-Mail-Adresse des Patienten", nullable=True)
    versichertennummer: str = Field(description="Versicherungsnummer des Patienten")
    kassenart: str = Field(description="Art der Krankenkasse des Patienten")
    krankenhaus_id: str = Field(
        description="ID des Krankenhauses, in dem der Patient behandelt wird"
    )
    einweisender_arzt: str = Field(
        description="Name und Vorname des einweisenden Arztes", nullable=True
    )
    aufnahme_datum: str = Field(description="Aufnahmedatum im Format TT.MM.JJJJ")
    entlassungs_datum: str = Field(
        description="Entlassungsdatum im Format TT.MM.JJJJ", nullable=True
    )


# ------------------------------------------------------------
# KDL: AD060199 - Sonstige ärztliche Befunderhebung
# Standard: DIN 5008 Geschäftsbriefnorm, KBV/gematik eArztbrief-Richtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class SonstigeärztlicheBefunderhebung(KdlDocumentBase):
    kdl_code: str = Field(default="AD060199", const=True)
    header: Header
    body: Body


class Header(BaseModel):
    sender: Sender
    recipient: Recipient
    creation_time: datetime
    document_type: str = Field(default="Sonstige ärztliche Befunderhebung")


class Sender(BaseModel):
    name: str
    address: Address


class Recipient(BaseModel):
    name: str
    address: Address


class Address(BaseModel):
    street: str
    postal_code: str
    city: str
    country: str = Field(default="DE")


class Body(BaseModel):
    findings: list[Finding]


class Finding(BaseModel):
    type: str
    description: str
    date: datetime


# ------------------------------------------------------------
# KDL: AM010101 - von Blut oder Blutbestandteilen an den Empfänger. Bogen abrechnungsrelevanter Diagnosen/ Prozeduren
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class SrelevanterDiagnosenProzeduren(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    sender_institution_id: str = Field(description="Absender-Instituions-ID")
    receiver_institution_id: str = Field(description="Empfänger-Institutions-ID")
    diagnosis_procedure_code: str = Field(description="Diagnose/Prozedur-Code (AM010101)")
    diagnosis_procedure_description: str = Field(description="Beschreibung der Diagnose/Prozedur")
    date_of_service: str = Field(description="Datum des Leistungsereignisses")
    billing_amount: float = Field(description="Rechnungsbetrag")


# ------------------------------------------------------------
# KDL: AM010102 - tologie G-AEP Kriterien
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------


from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    version: int = Field(description="Version des medizinischen Dokuments")


class TologieGAEPKriterien(KdlDocumentBase):
    kdl_code: str = "AM010102"
    version: int = 1
    patient_id: str = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    sex: str = Field(description="Geschlecht des Patienten")
    diagnosis: list[str] = Field(description="Diagnosen des Patienten")
    treatment: list[str] = Field(description="Behandlungen des Patienten")


# ------------------------------------------------------------
# KDL: AM010103 - Kostenübernahmeverlängerung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Kostenuebernahmeverlaengerung(KdlDocumentBase):
    kdl_code: str = Field(default="AM010103", const=True)
    patient: Patient = Field(description="Patientendaten")
    versicherer: Versicherer = Field(description="Versichererdaten")
    behandelnder_arzt: Arzt = Field(description="Behandelnder Arzt")
    diagnose: Diagnose = Field(description="Diagnose")
    kostenuebernahmezeitraum: KostenuebernahmeZeitraum = Field(
        description="Kostenübernahmezeitraum"
    )
    verlaengerungsgrund: str = Field(description="Verlängerunggrund")
    unterschriften: list[Unterschrift] = Field(default=[])


# ------------------------------------------------------------
# KDL: AM010104 - Medizinischen Dienst), Muster 86 (Weiterleitungsbogen für angeforderte Befunde an den MDK) Schriftverkehr MDK Kasse
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code")


class AndenMDKSchriftverkehrMDKKasse(KdlDocumentBase):
    versichertenr_id: str = Field(description="Versichertennummer")
    name_versicherter: str = Field(description="Name des Versicherten")
    geburtsdatum_versicherter: str = Field(description="Geburtsdatum des Versicherten")
    kassenart: str = Field(description="Kassenart")
    kassenzeichen: str = Field(description="Kassenzeichen")
    anrede_kasse: str = Field(description="Anrede der Kasse")
    name_kasse: str = Field(description="Name der Kasse")
    adresse_kasse: str = Field(description="Adresse der Kasse")
    befund_anfordern_fuer: str = Field(description="Befund anfordern für")
    art_befund: str = Field(description="Art des Befundes")
    laborwerte: list[dict] = Field(default=[], description="Laborwerte")


# ------------------------------------------------------------
# KDL: AM010105 - aufga
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    version: str = Field(description="Version des KDL-Dokuments")
    type: str = Field(description="Typ des KDL-Dokuments")


class Aufga(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    gender: str = Field(description="Geschlecht des Patienten")
    diagnosis: str = Field(description="Diagnose")
    treatment: str = Field(description="Behandlung")


# ------------------------------------------------------------
# KDL: AM010106 - ben zur Art und Dauer der durchgeführten Wiederbelebungsmaßnahme. Rechnung ambulante/ stationäre Behandlung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class GambulantestationäreBehandlung(KdlDocumentBase):
    art_der_wiederbelebungsmaßnahme: str = Field(description="Art der Wiederbelebungsmaßnahme")
    dauer_der_wiederbelebungsmaßnahme: int = Field(
        description="Dauer der Wiederbelebungsmaßnahme in Minuten"
    )
    ambulante_behandlung: bool = Field(description="Flag für ambulante Behandlung")
    stationäre_behandlung: bool = Field(description="Flag für stationäre Behandlung")
    rechnungsbetrag: float = Field(description="Rechnungsbetrag")


# ------------------------------------------------------------
# KDL: AM010107 - Ergebnis einer Begutachtung durch den Medizinischen Dienst der Krankenkassen. MDK Prüfauftrag
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        allow_population_by_field_name = True


class MDKPruefauftrag(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    pruefauftrag_id: str = Field(description="ID des Prüfauftrags")
    begutachtungsdatum: datetime = Field(description="Datum der Begutachtung")
    begutachter: str = Field(description="Name des Begutachters")
    versichertenummer: str = Field(description="Versicherungsnummer des Versicherten")
    krankenkasse: str = Field(description="Krankenkasse")
    diagnose: list[str] = Field(description="Diagnosen")
    laborwerte: list[Dict[str, Any]] = Field(description="Laborwerte")


# ------------------------------------------------------------
# KDL: AM010108 - MDK Gutachten
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_id: str = Field(description="Dokument-ID")


class MDKGutachten(KdlDocumentBase):
    gutachter_name: str = Field(description="Name des Gutachters")
    gutachter_berufstitel: str = Field(description="Berufstitel des Gutachters")
    patient_name: str = Field(description="Name des Patienten")
    patient_gender: str = Field(description="Geschlecht des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    patient_insurance_number: str = Field(description="Versicherungsnummer des Patienten")
    diagnosis: str = Field(description="Diagnose")
    findings: list[str] = Field(description="Befunde")
    recommendations: list[str] = Field(description="Empfehlungen")


# ------------------------------------------------------------
# KDL: AM010199 - Sonstige Fallbesprechung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    document_type: str
    sender: dict
    recipient: dict
    creation_time: datetime
    signature: Signature


class SonstigeFallbesprechung(KdlDocumentBase):
    kdl_code = "AM010199"
    document_type = "Sonstige Fallbesprechung"

    fallnummer: str = Field(description="Fallnummer des Patienten")
    patient_name: str = Field(description="Name des Patienten")
    birth_date: date = Field(description="Geburtsdatum des Patienten")
    sex: str = Field(description="Geschlecht des Patienten", enum=["m", "w"])
    insurance_company: str = Field(description="Krankenkasse des Patienten")

    fallbesprechung_text: str = Field(description="Text der Fallbesprechung")

    responsible_doctor: dict = Field(description="Verantwortlicher Arzt")
    attending_doctors: list[dict] = Field(description="Anwesende Ärzte")

    signature: Signature = Field(description="Unterschrift des verantwortlichen Arztes")


# ------------------------------------------------------------
# KDL: AM010201 - Anfrage für eine gezielte professionelle Behandlung psychischer Störungen. Antrag auf Rehabilitation
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    version: int = 1


class AntragAufRehabilitation(KdlDocumentBase):
    kdl_code: str = "AM010201"
    version: int = 1

    patient: dict = Field(description="Patientendaten")
    behandelnder_arzt: dict = Field(description="Behandelnder Arzt")
    diagnose: list = Field(description="Diagnosen")
    zielsetzung: str = Field(description="Zielsetzung der Rehabilitation")
    voraussichtliche_dauer: int = Field(
        description="Voraussichtliche Dauer der Rehabilitation (in Tagen)"
    )
    leistungsbedarf: dict = Field(description="Leistungsbedarf")


# ------------------------------------------------------------
# KDL: AM010202 - Rezept, Psychologische Therapieanordnung, Verordnung von Krankenhausbehandlung, Postoperative Verordnung, Bestrahlungsverordnung Antrag auf Betreuung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_type: str = Field(description="Art des medizinischen Dokuments")


class GsverordnungAntragaufBetreuung(KdlDocumentBase):
    kdl_code: str = "AM010202"
    document_type: str = "Rezept, Psychologische Therapieanordnung, Verordnung von Krankenhausbehandlung, Postoperative Verordnung, Bestrahlungsverordnung Antrag auf Betreuung"

    patient: dict = Field(description="Patientendaten")
    doctor: dict = Field(description="Arztinformationen")
    diagnosis: str = Field(description="Diagnose")
    medication: list = Field(description="Verordnete Medikamente")
    duration: int = Field(description="Dauer der Verordnung in Tagen")


# ------------------------------------------------------------
# KDL: AM010203 - Anfrage auf eine gesetzliche Vormundschaft durch das Gericht. Antrag auf gesetzliche Unterbringung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class RagaufgesetzlicheUnterbringung(KdlDocumentBase):
    antragsteller: str = Field(description="Name und Vorname des Antragstellers")
    geburtsdatum_antragsteller: str = Field(description="Geburtsdatum des Antragstellers")
    wohnort_antragsteller: str = Field(description="Wohnort des Antragstellers")
    unterbringungsgrund: str = Field(description="Grund für die Unterbringung")
    unterbringungsdauer: int = Field(description="Dauer der beantragten Unterbringung in Monaten")


# ------------------------------------------------------------
# KDL: AM010204 - Verlängerungsantrag
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Verlängerungsantrag(KdlDocumentBase):
    dokumenttyp: str = Field(default="AM010204", description="KDL-Code für Verlängerungsantrag")
    patient_id: UUID = Field(description="Patienten-ID")
    versichertenrrn: str = Field(description="Versicherten-RRN")
    name_patient: str = Field(description="Name des Patienten")
    geburtsdatum: date = Field(description="Geburtstag des Patienten")
    adresse_patient: str = Field(description="Adresse des Patienten")
    krankenkasse: str = Field(description="Krankenkasse")
    arzt_id: UUID = Field(description="ID des Arztes")
    arzt_name: str = Field(description="Name des Arztes")
    diagnose: str = Field(description="Diagnose")
    beginn_behandlung: date = Field(description="Beginn der Behandlung")
    ende_behandlung: date | None = Field(
        default=None, description="Ende der Behandlung (optional)"
    )
    beihilfe_anspruch: bool = Field(description="Beihilfe-Anspruch")
    kostenuebernahme: str = Field(description="Kostenübernahme durch die Krankenkasse")


# ------------------------------------------------------------
# KDL: AM010205 - Antrag auf Psychotherapie
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class AntragaufPsychotherapie(KdlDocumentBase):
    antragsteller_name: str = Field(description="Name des Antragstellers")
    antragsteller_geburtsdatum: str = Field(
        description="Geburtstag des Antragstellers (TT.MM.JJJJ)"
    )
    antragsteller_gender: str = Field(
        description="Geschlecht des Antragstellers ('männlich', 'weiblich' oder 'divers')"
    )
    antragsteller_strasse: str = Field(description="Straße und Hausnummer des Antragstellers")
    antragsteller_plz: str = Field(description="Postleitzahl des Antragstellers")
    antragsteller_ort: str = Field(description="Ort des Antragstellers")
    antragsteller_email: str = Field(description="E-Mail-Adresse des Antragstellers")
    psychotherapeut_name: str = Field(description="Name des Psychotherapeuten")
    psychotherapeut_strasse: str = Field(description="Straße und Hausnummer des Psychotherapeuten")
    psychotherapeut_plz: str = Field(description="Postleitzahl des Psychotherapeuten")
    psychotherapeut_ort: str = Field(description="Ort des Psychotherapeuten")
    diagnose: str = Field(description="Diagnose")


# ------------------------------------------------------------
# KDL: AM010206 - Leistungen, welche durch die Pflegeversicherung übernommen werden sollen. Bsp.: Pflegegeld, Pflegehilfsmittel. Antrag auf Pflegeeinstufung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        allow_population_by_field_name = True


class IttelAntragAufPflegeeinstufung(KdlDocumentBase):
    antragsteller: str = Field(description="Name des Antragstellers")
    geburtsdatum_antragsteller: str = Field(
        description="Geburtstag des Antragstellers im Format TT.MM.JJJJ"
    )
    versichertenrrn: str = Field(description="Versicherter Rentenversicherungsnummer")
    pflegebeduerftigkeit: bool = Field(description="Pflegebedürftigkeit")
    pflegestufe: int = Field(description="Pflegestufe")
    leistungen: list[dict] = Field(
        description="Leistungen, welche durch die Pflegeversicherung übernommen werden sollen"
    )

    class Config:
        schema_extra = {
            "example": {
                "antragsteller": "Max Mustermann",
                "geburtsdatum_antragsteller": "01.01.1980",
                "versichertenrrn": "1234567890",
                "pflegebeduerftigkeit": True,
                "pflegestufe": 2,
                "leistungen": [
                    {"leistung": "Pflegegeld", "betrag": 200},
                    {"leistung": "Pflegehilfsmittel", "betrag": 150},
                ],
            }
        }


# ------------------------------------------------------------
# KDL: AM010207 - Kostenübernahmeantrag
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Kostenuebernahmeantrag(KdlDocumentBase):
    kdl_code: str = Field(default="AM010207", const=True)
    patient: Patient = Field(description="Patientendaten")
    versicherer: Versicherer = Field(description="Versichererdaten")
    leistungserbringer: Leistungserbringer = Field(description="Leistungserbringerdaten")
    diagnose: str = Field(description="Diagnose")
    Leistungen: list[Leistung] = Field(description="Leistungen")
    kostenuebernahme: bool = Field(description="Kostenübernahme gewünscht")


# ------------------------------------------------------------
# KDL: AM010208 - Antrag zur Inanspruchnahme einer begrenzten oder vollstationären Pflege einer pflegebedürftigen Person. Antrag auf Leistungen der Pflegeversicherung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code")


class PflegebeduerftigePerson(BaseModel):
    name: str = Field(description="Name der pflegebedürftigen Person")
    geburtsdatum: str = Field(description="Geburtstag der pflegebedürftigen Person")
    adresse: str = Field(description="Adresse der pflegebedürftigen Person")


class AntragAufLeistungen(BaseModel):
    pflegebeduerftige_person: PflegebeduerftigePerson = Field(description="Pflegebedürftige Person")
    antragsteller: str = Field(description="Name des Antragstellers")
    versicherungsnummer: str = Field(description="Versicherungsnummer der pflegebedürftigen Person")
    art_der_pflege: str = Field(description="Art der Pflege (begrenzt oder vollstationär)")
    beginn_datum: str = Field(description="Beginn des Leistungszeitraums")
    ende_datum: str = Field(description="Ende des Leistungszeitraums")


class EistungenderPflegeversicherung(KdlDocumentBase):
    kdl_code: str = Field(
        default="AM010208",
        description="KDL-Code für den Antrag zur Inanspruchnahme einer begrenzten oder vollstationären Pflege",
    )
    antrag_auf_leistenungen: AntragAufLeistungen = Field(
        description="Antrag auf Leistungen der Pflegeversicherung"
    )


# ------------------------------------------------------------
# KDL: AM010209 - Anfrage bei Gericht auf Unterbringung in eine geschlossene Einrichtung durch einen Arzt, wenn eine Eigenund Fremdgefährdung besteht. Antrag auf Kurzzeitpflege
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class BestehtAntragaufKurzzeitpflege(KdlDocumentBase):
    patient: dict = Field(description="Patientendaten")
    antragsteller: str = Field(description="Antragsteller")
    grund_für_unterbringung: str = Field(description="Grund für die Unterbringung")
    eigen_und_fremd_gefährdung: bool = Field(description="Besteht eine Eigen- und Fremdgefährdung")
    kurzzeitpflege_benötigt: bool = Field(description="Ist Kurzzeitpflege erforderlich")


# ------------------------------------------------------------
# KDL: AM010299 - Sonstige Abrechnungsdokumentation
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class SonstigeAbrechnungsdokumentation(KdlDocumentBase):
    kdl_code: str = "AM010299"
    document_type: str = "Sonstige Abrechnungsdokumentation"

    patient_id: str = Field(description="Patienten-ID")
    provider_id: str = Field(description="Leistungserbringer-ID")
    service_date: date = Field(description="Leistungsdatum")
    service_code: str = Field(description="Leistungsnummer")
    quantity: float = Field(description="Menge/Anzahl der Leistung")
    unit_price: float = Field(description="Einheitlicher Preis pro Menge/Anzahl")


# ------------------------------------------------------------
# KDL: AM010301 - Aufklärungsbogen klassiert. Bisherige Erfahrungen
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class BisherigeErfahrungen(KdlDocumentBase):
    patient_id: int = Field(description="ID des Patienten")
    aufklaerungsbogen_datum: datetime = Field(description="Datum des Aufklärungsbogens")
    krankengeschichte: str = Field(description="Krankengeschichte des Patienten")
    vorerkrankungen: list[str] = Field(description="Vorerkrankungen des Patienten")
    aktuelle_medikation: list[str] = Field(description="Aktuelle Medikation des Patienten")
    allergien: list[str] = Field(description="Allergien des Patienten")


# ------------------------------------------------------------
# KDL: AM010302 - gen zur Kontrolle des Blutzuckers über einen bestimmten Zeitraum. Diagnostischer Aufklärungsbogen
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_type: str = Field(description="Art des medizinischen Dokuments")


class DiagnostischerAufklaerungsbogen(KdlDocumentBase):
    kdl_code: str = "AM010302"
    document_type: str = "Diagnostischer Aufklärungsbogen"

    patient_id: str = Field(description="Patienten-ID")
    doctor_id: str = Field(description="Arzt-ID")

    blutzuckerwerte: list[dict[str, str]] = Field(
        default_factory=list, description="Tabelle mit Blutzuckerwerten"
    )

    class Config:
        orm_mode = True


# ------------------------------------------------------------
# KDL: AM010303 - Operationsaufklärungsbogen
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Operationsaufklärungsbogen(KdlDocumentBase):
    kdl_code: str = Field(default="AM010303", const=True)
    patient_id: UUID
    birth_date: date
    surgeon: str
    diagnosis: str
    operation_procedure: str
    risks_informed: bool = Field(description="Patient wurde über Risiken aufgeklärt")
    consent_given: bool = Field(description="Einwilligung des Patienten liegt vor")


# ------------------------------------------------------------
# KDL: AM010304 - Anweisung, die Akte/Daten des Mandanten zu löschen (Art. 17 DSGVO). Aufklärungsbogen Therapie
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class DSGVOAufklärungsbogenTherapie(KdlDocumentBase):
    patient_id: int = Field(..., description="Patienten-ID")
    mandant_id: int = Field(..., description="Mandanten-ID")
    aufklärung_erfolgt: bool = Field(..., description="Aufklärung erfolgte")
    einwilligung_in_löschung: bool = Field(..., description="Einwilligung in Löschung")


# ------------------------------------------------------------
# KDL: AM010399 - Sonstiger Antrag
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    version: int


class SonstigerAntrag(KdlDocumentBase):
    kdl_code: str = Field(default="AM010399", const=True)
    version: int = Field(default=1, const=True)

    anlagestatus: str = Field(description="Status der Anlage")
    antragsteller: dict = Field(description="Antragstellerdaten")
    versicherungsstatus: str = Field(description="Versicherungsstatus des Antragstellers")
    beihilfeberechtigt: bool = Field(description="Beihilfeberechtigung des Antragstellers")
    leistung_beschreibung: str = Field(description="Beschreibung der beantragten Leistung")
    leistung_dauer: int = Field(description="Dauer der beantragten Leistung in Tagen")
    leistungsbeginn: datetime.date = Field(description="Beginndatum der beantragten Leistung")
    leistungsende: datetime.date = Field(description="Enddatum der beantragten Leistung")


# ------------------------------------------------------------
# KDL: AM030101 - Bericht bzw. eine Zusammenfassung eines Patientenfalls bezüglich der nachstationären Betreuung oder weiteren Behandlung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    creation_date: datetime = Field(description="Erstellungsdatum des medizinischen Dokuments")


class BerichtbzwZusammenfassungPatientenfalls(KdlDocumentBase):
    patient_id: UUID = Field(description="ID des Patienten")
    report_text: str = Field(description="Berichtstext bzw. Zusammenfassung des Patientenfalls")
    further_treatment_required: bool = Field(description="Benötigt der Patient weitere Behandlung?")
    aftercare_required: bool = Field(description="Benötigt der Patient nachstationäre Betreuung?")


# ------------------------------------------------------------
# KDL: AM030102 - ben über Voraussetzungen, den Ablauf oder erforderliche bildgebende Diagnostiken. Erfolgte Durchführungen werden gekennzeichnet. Checkliste Entlassung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class NnzeichnetChecklisteEntlassung(KdlDocumentBase):
    voraussetzungen: dict = Field(
        description="Befunde und Diagnosen, die für die stationäre Behandlung relevant sind."
    )
    ablauffolge: str = Field(
        description="Ablauf der Behandlung einschließlich der erfolgten Durchführungen von bildgebenden Diagnostiken."
    )
    entlassungsplan: str = Field(
        description="Checkliste zur Entlassung mit den erforderlichen Maßnahmen und Verordnungen."
    )


# ------------------------------------------------------------
# KDL: AM030103 - Entlassungsplan
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    version: int = Field(description="Version des KDL-Standards")


class Entlassungsplan(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    discharge_date: str = Field(description="Entlassungsdatum")
    treating_physician: str = Field(description="Behandelnder Arzt")
    reason_for_admission: str = Field(description="Grund für die Aufnahme")
    diagnosis: str = Field(description="Diagnose")
    treatment_course: str = Field(description="Verlauf der Behandlung")
    discharge_instructions: str = Field(description="Entlassungsinstruktion")


# ------------------------------------------------------------
# KDL: AM030104 - Patientenlaufzettel
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class Patientenlaufzettel(KdlDocumentBase):
    kdl_code: str = "AM030104"
    document_type: str = "Patientenlaufzettel"

    patient_id: str = Field(description="ID des Patienten")
    last_name: str = Field(description="Nachname des Patienten")
    first_name: str = Field(description="Vorname des Patienten")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    street: str = Field(description="Straße und Hausnummer des Patienten")
    postal_code: str = Field(description="Postleitzahl des Patienten")
    city: str = Field(description="Stadt des Patienten")
    phone_number: str = Field(description="Telefonnummer des Patienten")
    email_address: str | None = Field(description="E-Mail-Adresse des Patienten", default=None)
    insurance_company: str = Field(description="Krankenkasse des Patienten")
    insurance_number: str = Field(description="Versicherungsnummer des Patienten")
    attending_physician: str = Field(description="Behandelnder Arzt")
    referral_reason: str = Field(description="Grund der Überweisung")


# ------------------------------------------------------------
# KDL: AM030199 - Anspruchsberechtigung) Sonstige Checkliste Administration
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class NstigeChecklisteAdministration(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    birth_date: date = Field(description="Geburtsdatum des Patienten")
    admin_checklist_items: list[Dict[str, Any]] = Field(
        description="Liste der administrativen Checklisten-Items"
    )

    class Config:
        orm_mode = True


# ------------------------------------------------------------
# KDL: AM050101 - Datenschutzerklärung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------


from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    version: int


class Datenschutzerklärung(KdlDocumentBase):
    kdl_code = Field(default="AM050101", const=True)
    version: int = Field(default=1, ge=1, le=2)

    einwilligung_erlaubt: bool = Field(description="Erklärung zur Einwilligung")
    daten_nutzung: str = Field(description="Zweck der Datennutzung")
    daten_speicherung: str = Field(description="Dauer der Datenspeicherung")
    daten_weitergabe: list[str] = Field(description="Empfänger von Daten")
    daten_sicherheit: str = Field(description="Maßnahmen zur Datensicherheit")
    kontakt_möglichkeit: str = Field(description="Kontaktmöglichkeit für Betroffene")


# ------------------------------------------------------------
# KDL: AM050104 - Einschätzung eines Patienten durch den Sozialdienst. Einverständniserklärung Abrechnung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class VerständniserklärungAbrechnung(KdlDocumentBase):
    patient_id: str = Field(description="ID des Patienten")
    patient_name: str = Field(description="Name des Patienten")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    social_service_evaluation: str = Field(description="Einschätzung durch den Sozialdienst")
    consent_for_billing: bool = Field(description="Einverständnis zur Abrechnung")


# ------------------------------------------------------------
# KDL: AM050105 - schriftliche Erlaubnis, sensible Daten zu Abrechnungszwecken an Dritte weiterzugeben. Einverständniserklärung Behandlung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class RstaendniserklaerungBehandlung(KdlDocumentBase):
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    patient_address: str = Field(description="Adresse des Patienten")
    doctor_name: str = Field(description="Name des Arztes")
    doctor_practice: str = Field(description="Praxisklinik des Arztes")
    treatment_type: str = Field(description="Art der Behandlung")
    permission_start_date: str = Field(description="Beginn der Erlaubnis")
    permission_end_date: str = Field(description="Ende der Erlaubnis")


# ------------------------------------------------------------
# KDL: AM050106 - zur Teilnahme an einer Studie. Einwilligung und Datenschutzerklärung Entlassungsmanagement
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class ErklärungEntlassungsmanagement(KdlDocumentBase):
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    study_title: str = Field(description="Titel der Studie")
    consent_given: bool = Field(
        description="Entscheidung des Patienten zur Teilnahme an der Studie"
    )
    data_protection_declaration_accepted: bool = Field(
        description="Akzeptanz der Datenschutzerklärung durch den Patienten"
    )


# ------------------------------------------------------------
# KDL: AM050107 - Gutachten, Schriftverkehr MDK Arzt Schweigepflichtentbindung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    document_type: str


class KArztSchweigepflichtentbindung(KdlDocumentBase):
    kdl_code = "AM050107"
    document_type = "Gutachten, Schriftverkehr MDK Arzt Schweigepflichtentbindung"

    patient_id: str = Field(description="Patienten-ID")
    patient_name: str = Field(description="Name des Patienten")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    insurance_company: str = Field(description="Krankenkasse")
    insured_person_id: str = Field(description="Versicherten-Identifikationsnummer")

    doctor_info: dict = Field(description="Informationen zum Arzt")
    medical_history: str = Field(description="Medical history of the patient")
    diagnosis: str = Field(description="Diagnosis")
    treatment: str = Field(description="Treatment")
    recommendations: str = Field(description="Recommendations")


# ------------------------------------------------------------
# KDL: AM050108 - nisse einer Untersuchung bei der Körperhöhlen und Hohlorgane von innen bildlich dargestellt und ausgewertet werden. Entlassung gegen ärztlichen
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ErdenEntlassunggegenärztlichen(KdlDocumentBase):
    patient_id: int = Field(..., description="Patienten-ID")
    patient_name: str = Field(..., description="Name des Patienten")
    birth_date: date = Field(..., description="Geburtsdatum des Patienten")
    doctor_id: int = Field(..., description="ID des untersuchenden Arztes")
    examination_date: date = Field(..., description="Datum der Untersuchung")
    findings: str = Field(..., description="Befunde der Untersuchung")
    diagnosis: str = Field(..., description="Diagnose")
    discharge_reason: str = Field(..., description="Entlassungsgrund")


# ------------------------------------------------------------
# KDL: AM050109 - stationäre Aufenthalt stattgefunden hat. Aufforderung zur Herausgabe der medizinischen Dokumentation
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class EdermedizinischenDokumentation(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    patient_name: str = Field(description="Name des Patienten")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    insurance_company: str = Field(description="Krankenkasse")
    hospital_stay_start_date: str = Field(description="Anfangsdatum des stationären Aufenthalts")
    hospital_stay_end_date: str = Field(description="Enddatum des stationären Aufenthalts")
    reason_for_hospitalization: str = Field(description="Grund für die Krankenhausbehandlung")


# ------------------------------------------------------------
# KDL: AM050110 - Mandanten herauszuge
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Mandantenherauszuge(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    patient_name: str = Field(description="Patientennamen")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")
    insurance_company: str = Field(description="Krankenkasse")
    insurance_number: str = Field(description="Versicherungsnummer")
    doctor_id: str = Field(description="Arzt-ID")
    doctor_name: str = Field(description="Arztname")
    medical_practice_address: str = Field(description="Adresse der medizinischen Einrichtung")
    medical_practice_phone: str = Field(description="Telefonnummer der medizinischen Einrichtung")


# ------------------------------------------------------------
# KDL: AM050199 - Notfallambulanz Sonstige Einwilligung/ Erklärung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_type: str = Field(description="Art des medizinischen Dokuments")


class NotfallambulanzSonstigeEinwilligungErklärung(KdlDocumentBase):
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    patient_address: str = Field(description="Adresse des Patienten")
    emergency_contact: str = Field(description="Notfallkontakt des Patienten")
    declaration_text: str = Field(description="Text der Einwilligung/Erklärung")


# ------------------------------------------------------------
# KDL: AM160101 - dann sinnvoll, wenn anhand dieser die verwendete Klasse leichter nachvollziehbar sein soll. Beispiel 2 »Interpretation KDL-Kode« In einer digitalen Patientenakte sind folgende KDL-Kodes verschlüsselt
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------


from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class InterpretationKDLKode(KdlDocumentBase):
    kdl_code: str = Field(description="Verschlüsselter KDL-Code")
    interpretation: str = Field(description="Interpretation des KDL-Kodes")


# ------------------------------------------------------------
# KDL: AM160102 - nisse einer Nachsorgeuntersuchung nach dem Einsetzen eines Defibrillators auf seine Funktion. Impfausweis
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class NachsorgeuntersuchungDefibrillator(Impfausweis(KdlDocumentBase)):
    patient_id: int = Field(description="Patienten-ID")
    defibrillator_type: str = Field(description="Typ des Defibrillators")
    implantation_date: date = Field(description="Datum der Implantation")
    last_checkup_date: date = Field(description="Datum der letzten Nachsorgeuntersuchung")
    next_checkup_date: date = Field(
        description="Datum der nächsten geplanten Nachsorgeuntersuchung"
    )
    defibrillator_function: str = Field(description="Funktion des Defibrillators")


# ------------------------------------------------------------
# KDL: AM160103 - läufige Fassung des Entlassungsberichtes. Vorsorgevollmacht
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class UngsberichtesVorsorgevollmacht(KdlDocumentBase):
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    patient_address: str = Field(description="Adresse des Patienten")
    power_of_attorney_holder: str = Field(description="Inhaber der Vorsorgevollmacht")
    power_of_attorney_scope: str = Field(description="Umfang der Vorsorgevollmacht")


# ------------------------------------------------------------
# KDL: AM160104 - Nachweis über Terminvereinbarungen, durchgeführte Diagnostiken, Behandlungen o.ä. während des Aufenthaltes. Patientenverfügung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class EhandlungenPatientenverfuegung(KdlDocumentBase):
    patient_id: str = Field(description="ID des Patienten")
    patient_name: str = Field(description="Name des Patienten")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    insurance_provider: str = Field(description="Krankenkasse des Patienten")
    admission_date: str = Field(description="Einweisungsdatum")
    discharge_date: str = Field(description="Entlassungsdatum")
    treatments: list[dict] = Field(default_factory=list, description="Durchgeführte Behandlungen")
    diagnostics: list[dict] = Field(default_factory=list, description="Durchgeführte Diagnostiken")
    appointments: list[dict] = Field(default_factory=list, description="Terminvereinbarungen")
    patient_consent: str = Field(description="Patientenverfuegung")


# ------------------------------------------------------------
# KDL: AM160105 - ben zu zusätzlich gewählten Leistungen, während einer Behandlung, zwischen Einrichtung und Patient. Wertgegenständeverwaltung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        allow_population_by_field_name = True


class IentWertgegenstaendeverwaltung(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code für das medizinische Dokument")
    einrichtung: str = Field(description="Name der Einrichtung")
    patient: str = Field(description="Name des Patienten")
    behandlungszeitraum_von: datetime = Field(description="Behandlungszeitraum von")
    behandlungszeitraum_bis: datetime = Field(description="Behandlungszeitraum bis")
    gewaehlte_leistungen: list[str] = Field(
        description="Gewählte Leistungen während der Behandlung"
    )
    wertgegenstaende: list[Dict[str, str]] = Field(
        description="Wertgegenstände während der Behandlung"
    )


# ------------------------------------------------------------
# KDL: AM160106 - Nachweis über den aktuellen Verbleib sowie den Aktenlauf. Allergiepass
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class BsowiedenAktenlaufAllergiepass(KdlDocumentBase):
    patient_name: str = Field(description="Patient's name")
    patient_birthdate: str = Field(description="Patient's birth date")
    allergies: list[str] = Field(description="List of allergies")
    current_location: str = Field(description="Current location of the patient")
    medical_history: str = Field(description="Medical history")


# ------------------------------------------------------------
# KDL: AM160107 - Herzschrittmacherausweis
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class Herzschrittmacherausweis(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    last_name: str = Field(description="Nachname des Patienten")
    first_name: str = Field(description="Vorname des Patienten")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    address: str = Field(description="Adresse des Patienten")
    city: str = Field(description="Stadt des Patienten")
    zip_code: str = Field(description="PLZ des Patienten")
    phone_number: str = Field(description="Telefonnummer des Patienten")
    doctor_id: str = Field(description="ID des Arztes")
    doctor_last_name: str = Field(description="Nachname des Arztes")
    doctor_first_name: str = Field(description="Vorname des Arztes")
    device_type: str = Field(description="Typ des Herzschrittmachers")
    device_manufacturer: str = Field(description="Hersteller des Herzschrittmachers")
    device_serial_number: str = Field(description="Seriennummer des Herzschrittmachers")
    implantation_date: str = Field(description="Implantationsdatum des Herzschrittmachers")
    battery_life_expectancy: int = Field(
        description="Geschätzte Lebensdauer der Batterie in Monaten"
    )


# ------------------------------------------------------------
# KDL: AM160108 - ben, in dem alle relevanten Daten zum Schwangerschaftsverlauf erfasst werden. Nachlassprotokoll
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_type: str = Field(description="Art des medizinischen Dokuments")


class Schwangerschaftsverlauf(BaseModel):
    schwangerschaftswoche: int = Field(description="Schwangerschaftswoche")
    muttermundstatus: str = Field(description="Muttermundstatus")
    kindslage: str = Field(description="Kindslage")
    herzton: str = Field(description="Herztöne")


class Laborwert(BaseModel):
    parameter: str = Field(description="Laborparameter")
    wert: float = Field(description="Wert des Laborparameters")
    einheit: str = Field(description="Einheit des Laborparameters")


class Nachlassprotokoll(KdlDocumentBase):
    kdl_code: str = "AM160108"
    document_type: str = "Nachlassprotokoll"

    schwangerschaftsverlauf: Schwangerschaftsverlauf = Field(description="Schwangerschaftsverlauf")
    laborwerte: list[Laborwert] = Field(default_factory=list, description="Laborwerte")

    erstellungsdatum: datetime = Field(description="Erstellungsdatum des Nachlassprotokolls")


# ------------------------------------------------------------
# KDL: AM160109 - Untersuchung, bei der Schnittbilder von Knochen und Weichteilen im menschlichen Körper, mit Hilfe von Magnetfeldern, bildlich dargestellt und ausgewertet werden. Mutterpass (Kopie)
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class SgewertetWerdenMutterpassKopie(KdlDocumentBase):
    untersuchungsdatum: str = Field(description="Datum der Untersuchung")
    untersuchender_arzt: str = Field(description="Name des untersuchenden Arztes")
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")


# ------------------------------------------------------------
# KDL: AM160110 - Augeninnendruck Ausweiskopie
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class AugeninnendruckAusweiskopie(KdlDocumentBase):
    kdl_code: str = Field(default="AM160110", const=True)
    patient_id: UUID
    issue_date: date
    doctor_id: UUID
    eye_pressure_left: float
    eye_pressure_right: float
    measurement_date: date


# ------------------------------------------------------------
# KDL: AM160111 - ben zu durchgeführten Impfungen mit Angaben zur Charge. ImplantatAusweis
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ImpfstoffCharge(BaseModel):
    impfstoff: str = Field(description="Impfstoff")
    charge: str = Field(description="Charge")


class ImplantatAusweis(KdlDocumentBase):
    impfungen: list[tuple[str, ImpfstoffCharge]] = Field(
        description="Durchgeführte Impfungen mit Angaben zur Charge"
    )


# ------------------------------------------------------------
# KDL: AM160112 - Anweisung einer Bestrahlungstherapie zur Behandlung. Betreuerausweis
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class Betreuerausweis(KdlDocumentBase):
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    treating_physician: str = Field(description="Behandelnder Physiker")
    radiation_dose: float = Field(description="Strahlendosis in Gy")
    treatment_fractionation: str = Field(description="Fraktionierung der Bestrahlungstherapie")
    total_treatment_time: int = Field(description="Gesamtbehandlungsdauer in Minuten")


# ------------------------------------------------------------
# KDL: AM160199 - ben, die nicht in einer spezifischeren KDL dieser Unterklasse abgebildet werden können. Sonstiges patienteneigenes Dokument
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_type: str = Field(description="Art des medizinischen Dokuments")


class SonstigesPatienteneigenesDokument(KdlDocumentBase):
    kdl_code: str = "AM160199"
    document_type: str = "Sonstiges patienteneigenes Dokument"

    content: str = Field(description="Inhalt des medizinischen Dokuments")


# ------------------------------------------------------------
# KDL: AM160201 - Belehrung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class Belehrung(KdlDocumentBase):
    kdl_code: str = "AM160201"
    patient_id: int = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    sex: str = Field(description="Geschlecht des Patienten")
    insured_person_id: str = Field(description="Versichertenkarte-Identifikationsnummer")
    insurance_company: str = Field(description="Krankenkasse")
    family_name: str = Field(description="Familienname des Patienten")
    given_names: str = Field(description="Vorname(n) des Patienten")
    street: str = Field(description="Straße und Hausnummer")
    postal_code: str = Field(description="Postleitzahl")
    city: str = Field(description="Ort")


# ------------------------------------------------------------
# KDL: AM160202 - Informationsblatt
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    version: int = Field(description="Version des Dokuments")


class Informationsblatt(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    sex: str = Field(description="Geschlecht des Patienten ('männlich' oder 'weiblich')")
    disease_description: str = Field(description="Beschreibung der Erkrankung")
    treatment_plan: str = Field(description="Behandlungsplan")


# ------------------------------------------------------------
# KDL: AM160203 - Hinweise, die für eine Behandlung oder stationären Aufenthalt notwendig sind. Informationsblatt Entlassungsmanagement
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    document_type: str
    version: str


class IonsblattEntlassungsmanagement(KdlDocumentBase):
    kdl_code: str = Field(
        default="AM160203", description="KDL-Code für das Informationsblatt Entlassungsmanagement"
    )
    document_type: str = Field(
        default="Hinweise zur Behandlung und Entlassung",
        description="Typ des medizinischen Dokuments",
    )
    version: str = Field(default="1.0", description="Version des medizinischen Dokuments")

    patient_id: int = Field(description="Identifikationsnummer des Patienten")
    patient_name: str = Field(description="Name des Patienten")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    treating_physician: str = Field(description="Behandelnder Arzt")
    discharge_date: str = Field(description="Entlassungsdatum")

    Hinweise: list[dict[str, str]] = Field(
        default=[], description="Tabelle mit Hinweisen für die Behandlung und Entlassung"
    )


# ------------------------------------------------------------
# KDL: AM160299 - Sonstiges Patienteninformationsblatt
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    version: int


class SonstigesPatienteninformationsblatt(KdlDocumentBase):
    kdl_code = "AM160299"
    version: int = Field(..., description="Version des Patienteninformationsblatts")
    patient_name: str = Field(..., description="Name des Patienten")
    birth_date: str = Field(..., description="Geburtsdatum des Patienten")
    address: str = Field(..., description="Adresse des Patienten")
    phone_number: str = Field(..., description="Telefonnummer des Patienten")
    email_address: str | None = Field(None, description="E-Mail-Adresse des Patienten")
    insurance_company: str = Field(..., description="Krankenkasse des Patienten")
    insurance_number: str = Field(..., description="Versicherungsnummer des Patienten")
    doctor_name: str = Field(..., description="Name des behandelnden Arztes")
    doctor_address: str = Field(..., description="Adresse des behandelnden Arztes")
    additional_information: str | None = Field(None, description="Zusätzliche Informationen")


# ------------------------------------------------------------
# KDL: AM160301 - Beispiel 1 »Anwendung der Resteklassen« Der Leistungserbringer erstellt für seine Einrichtung ein neues Formular für die »Poststationäre Verordnung einer alternativen Behandlungsmethode«
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class AlternativenBehandlungsmethode(KdlDocumentBase):
    patient_id: int = Field(..., description="Patient ID")
    patient_name: str = Field(..., description="Patient Name")
    birth_date: str = Field(..., description="Birth Date")
    sex: str = Field(..., description="Sex")
    diagnosis: str = Field(..., description="Diagnosis")
    alternative_treatment_method: str = Field(..., description="Alternative Treatment Method")
    reason_for_alternative_treatment: str = Field(
        ..., description="Reason for Alternative Treatment"
    )


# ------------------------------------------------------------
# KDL: AM160302 - Heil-/Hilfsmittelverordnung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_type: str = Field(description="Typ des medizinischen Dokuments")


class HeilHilfsmittelverordnung(KdlDocumentBase):
    kdl_code: str = "AM160302"
    document_type: str = "Heil-/Hilfsmittelverordnung"

    verordnender_arzt: str = Field(description="Verordnender Arzt")
    patient: str = Field(description="Patient")
    hilfsmittel: list[dict] = Field(description="Liste der verordneten Hilfsmittel")

    class Config:
        orm_mode = True


# ------------------------------------------------------------
# KDL: AM160303 - Stellungnahme Verordnung häusliche Krankenpflege
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------


from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    version: int = Field(description="Version des medizinischen Dokuments")


class StellungnahmeVerordnungHauslicheKrankenpflege(KdlDocumentBase):
    kdl_code: str = "AM160303"
    version: int = 1

    patient: dict = Field(description="Patientendaten")
    verordnender_arzt: dict = Field(description="Verordnender Arzt")
    verordnung_beginn: datetime = Field(description="Beginn der Verordnung")
    verordnung_dauer: int = Field(description="Dauer der Verordnung in Tagen")
    pflegebedarf: str = Field(description="Pflegebedarf des Patienten")
    pflegemaßnahmen: list[str] = Field(description="Pflegemaßnahmen, die erforderlich sind")
    diagnose: str = Field(description="Diagnose, die zur häuslichen Krankenpflege führt")


# ------------------------------------------------------------
# KDL: AM160399 - Krankentransportschein
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    version: str = Field(description="Version des medizinischen Dokuments")


class Krankentransportschein(KdlDocumentBase):
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    transport_reason: str = Field(description="Grund für den Krankentransport")
    destination_hospital: str = Field(description="Zielkrankenhaus")
    transporting_organization: str = Field(description="Transportierende Organisation")


# ------------------------------------------------------------
# KDL: AM170101 - Spirometrie Dokumentationsbogen Meldepflicht
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")
    document_type: str = Field(description="Dokumenttyp")


class SpirometrieDokumentationsbogenMeldepflicht(KdlDocumentBase):
    kdl_code: str = "AM170101"
    document_type: str = "Spirometrie Dokumentationsbogen Meldepflicht"

    patient_id: str = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")
    height: float = Field(description="Größe in cm")
    weight: float = Field(description="Gewicht in kg")

    spiro_values: list[dict[str, float]] = Field(
        default_factory=list, description="Spirometrie-Werte (Zeichenname: Wert)"
    )

    diagnosis: str = Field(description="Diagnose")


# ------------------------------------------------------------
# KDL: AM170102 - Nachweis über die verabreichte Dosis der Hormone und die Anzahl der Zyklen. Hygienestandard
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class AnzahlderZyklenHygienestandard(KdlDocumentBase):
    patient_id: str = Field(description="Patientenkennung")
    doctor_id: str = Field(description="Arztkennung")
    date_of_issue: str = Field(description="Ausstellungsdatum")
    dose_of_hormones: float = Field(description="Verabreichte Hormondosis in mg")
    number_of_cycles: int = Field(description="Anzahl der Zyklen")


# ------------------------------------------------------------
# KDL: AM170103 - graphische Darstellung zur Geburtensituation und der Eröffnung des Muttermundes bei Entbindung. Patientenfragebogen
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class IEntbindungPatientenfragebogen(KdlDocumentBase):
    geburtsdatum: datetime = Field(description="Das Geburtsdatum des Patienten")
    muttername: str = Field(description="Der Name der Mutter")
    muttervorname: str = Field(description="Der Vorname der Mutter")
    muttergeburtsdatum: datetime = Field(description="Das Geburtsdatum der Mutter")
    mutteradresse: str = Field(description="Die Adresse der Mutter")
    mutterplz: str = Field(description="Die Postleitzahl der Mutter")
    mutterort: str = Field(description="Der Ort der Mutter")
    muttertelefon: str = Field(description="Die Telefonnummer der Mutter")
    vatername: str = Field(description="Der Name des Vaters")
    vatervorname: str = Field(description="Der Vorname des Vaters")
    vatergeburtsdatum: datetime = Field(description="Das Geburtsdatum des Vaters")
    vateradresse: str = Field(description="Die Adresse des Vaters")
    vatermutterplz: str = Field(description="Die Postleitzahl des Vaters")
    vatermutterort: str = Field(description="Der Ort des Vaters")
    vatermuttertelefon: str = Field(description="Die Telefonnummer des Vaters")
    geburtssituation: str = Field(description="Beschreibung der Geburtssituation")
    eroeffnung_muttermund: str = Field(
        description="Beschreibung der Öffnung des Muttermundes bei Entbindung"
    )


# ------------------------------------------------------------
# KDL: AM170104 - Maßnahmenplan, der die strukturierte und zielgerichtete Vorgehensweise von Pflegekräften bei der Versorgung beschreibt
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class FtenBeiDerVersorgungBeschreibt(KdlDocumentBase):
    patient_id: int = Field(description="Patienten-ID")
    patient_name: str = Field(description="Patientennamen")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    sex: str = Field(description="Geschlecht des Patienten")
    diagnosis: str = Field(description="Diagnose")
    treatment_plan: str = Field(description="Behandlungsplan")


# ------------------------------------------------------------
# KDL: AM170105 - tischer Punktion, Anmeldung zur Punktion Qualitätssicherungsbogen
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    document_type: str


class TischPunktionAnmeldungQualitaetsicherungBogen(KdlDocumentBase):
    kdl_code = "AM170105"
    document_type = "tischer Punktion, Anmeldung zur Punktion Qualitätssicherungsbogen"

    patient_id: str = Field(description="Patienten-ID")
    last_name: str = Field(description="Nachname des Patienten")
    first_name: str = Field(description="Vorname des Patienten")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    sex: str = Field(description="Geschlecht des Patienten ('männlich' oder 'weiblich')")
    address: str = Field(description="Adresse des Patienten")
    city: str = Field(description="Stadt des Patienten")
    postal_code: str = Field(description="Postleitzahl des Patienten")

    physician_id: str = Field(description="ID des behandelnden Arztes")
    physician_last_name: str = Field(description="Nachname des behandelnden Arztes")
    physician_first_name: str = Field(description="Vorname des behandelnden Arztes")
    physician_address: str = Field(description="Adresse des behandelnden Arztes")
    physician_city: str = Field(description="Stadt des behandelnden Arztes")
    physician_postal_code: str = Field(description="Postleitzahl des behandelnden Arztes")

    indication_for_puncture: str = Field(description="Indikation für die Punktion")
    puncture_site: str = Field(description="Punktionstelle")
    puncture_date: str = Field(description="Datum der Punktion")
    puncture_result: str = Field(description="Ergebnis der Punktion")


# ------------------------------------------------------------
# KDL: AM170199 - befund, Psychopathologischer Befund, Therapieplan Psy Sonstiges Qualitätssicherungsdokument
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code des Dokuments")


class GesQualitätssicherungsdokument(KdlDocumentBase):
    diagnose: str = Field(description="Psychopathologische Diagnose")
    therapieplan: str = Field(description="Therapieplan für psychische Störungen")
    sonstiges: str = Field(description="Sonstige Qualitätssicherungsinformationen")


# ------------------------------------------------------------
# KDL: AM190101 - Anforderung von Arzneimitteln an eine dafür zuständige Ausgabestelle. Anforderung Unterlagen
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class AbestelleAnforderungUnterlagen(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    medication_requests: list[dict[str, str]] = Field(
        description="Liste der angeforderten Arzneimittel"
    )
    responsible_output_location: str = Field(
        description="Verantwortliche Ausgabestelle für die Arzneimittel"
    )


# ------------------------------------------------------------
# KDL: AM190102 - Schriftverkehr Amtsgericht
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    document_type: str
    sender: dict
    recipient: list[dict]
    creation_date: datetime
    signature: Signature


class SchriftverkehrAmtsgericht(KdlDocumentBase):
    kdl_code: str = Field(default="AM190102", const=True)
    document_type: str = Field(default="Schriftverkehr Amtsgericht")
    sender: dict = Field(description="Absender des Schriftverkehrs")
    recipient: list[dict] = Field(description="Empfänger des Schriftverkehrs")
    creation_date: datetime = Field(description="Erstellungsdatum des Schriftverkehrs")
    signature: Signature = Field(description="Unterschrift für den Schriftverkehr")

    class Config:
        allow_population_by_field_name = True


# ------------------------------------------------------------
# KDL: AM190103 - Schriftverkehr MDK Arzt
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    sender: str = Field(description="Absender des medizinischen Dokuments")
    recipient: str = Field(description="Empfänger des medizinischen Dokuments")


class SchriftverkehrMDKArzt(KdlDocumentBase):
    kdl_code: str = "AM190103"
    anlass: str = Field(description="Anlass für den Schriftverkehr")
    betroffener_patient: str = Field(description="Betroffener Patient")
    medizinischer_hintergrund: str = Field(description="Medizinischer Hintergrund")
    beschwerden_symptome: str = Field(description="Beschwerden und Symptome")
    diagnose_therapie: str = Field(description="Diagnose und Therapie")
    laboruntersuchungen: list[dict[str, str]] = Field(
        default_factory=list, description="Laboruntersuchungen"
    )
    befund_bewertung: str = Field(description="Befund und Bewertung")


# ------------------------------------------------------------
# KDL: AM190104 - tliche Korrespondenz zwischen medizinischer Einrichtung und der deutschen Rentenversicherung. Schriftverkehr Krankenkasse
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class RungSchriftverkehrKrankenkasse(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    patient_name: str = Field(description="Patient Name")
    sender_einrichtung: str = Field(description="Sender Einrichtung")
    sender_adresse: str = Field(description="Sender Adresse")
    recipient_rentenversicherung: str = Field(description="Recipient Rentenversicherung")
    recipient_adresse: str = Field(description="Recipient Adresse")
    korrespondenz_typ: str = Field(description="Korrespondenz Typ")
    korrespondenz_text: str = Field(description="Korrespondenz Text")


# ------------------------------------------------------------
# KDL: AM190105 - Schriftverkehr Deutsche Rentenversicherung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class SchriftverkehrDeutscheRentenversicherung(KdlDocumentBase):
    anrede: str = Field(description="Anrede")
    name_vorname: str = Field(description="Name und Vorname")
    adresse: str = Field(description="Adresse")
    Geburtsdatum: str = Field(description="Geburtsdatum")
    rentenversicherungsnummer: str = Field(description="Rentenversicherungsnummer")
    schriftverkehrsart: str = Field(description="Art des Schriftverkehrs")
    betroffenerzeitraum_von: str = Field(description="Betroffener Zeitraum von")
    betroffenerzeitraum_bis: str = Field(description="Betroffener Zeitraum bis")
    anliegen: str = Field(description="Anliegen")


# ------------------------------------------------------------
# KDL: AM190106 - schriftliche Einwilligung um medizinische Daten, die der ärztlichen Schweigepflicht unterliegen, an Dritte weiterge
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ChtunterliegenanDritteweiterge(KdlDocumentBase):
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    patient_address: str = Field(description="Adresse des Patienten")
    doctor_name: str = Field(description="Name des Arztes")
    doctor_practice: str = Field(description="Praxisklinik des Arztes")
    data_recipient: str = Field(description="Empfänger der Daten")
    data_to_be_transferred: list[str] = Field(description="Übertragene medizinische Daten")
    consent_start_date: str = Field(description="Beginn der Einwilligung")
    consent_end_date: str = Field(description="Ende der Einwilligung")


# ------------------------------------------------------------
# KDL: AM190107 - Empfangsbestätigung
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Empfangsbestätigung(KdlDocumentBase):
    document_type: str = Field(default="AM190107", const="AM190107")
    sender: Sender = Field(description="Absender der Empfangsbestätigung")
    receiver: Receiver = Field(description="Empfänger der Empfangsbestätigung")
    document_date: datetime = Field(description="Datum des medizinischen Dokuments")
    document_time: time = Field(description="Uhrzeit des medizinischen Dokuments")
    document_id: UUID = Field(description="Identifikationsnummer des medizinischen Dokuments")
    sender_signature: Signature = Field(description="Unterschrift des Absenders")
    receiver_signature: Signature = Field(description="Unterschrift des Empfängers")


# ------------------------------------------------------------
# KDL: AM190108 - Handschriftliche Notiz
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    creation_time: datetime = Field(description="Erstellungszeitpunkt des Dokuments")


class HandschriftlicheNotiz(KdlDocumentBase):
    notiz_text: str = Field(description="Handschriftlicher Notiztext")
    autor: str = Field(description="Autor der handschriftlichen Notiz")


# ------------------------------------------------------------
# KDL: AM190109 - Bewegungsplan Lieferschein
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class BewegungsplanLieferschein(KdlDocumentBase):
    kdl_code: str = "AM190109"
    dokument_typ: str = "Bewegungsplan Lieferschein"
    patient: Patient = Field(description="Patientendaten")
    leistungserbringer: Leistungserbringer = Field(description="Leistungserbringerdaten")
    bewegt_am: date = Field(description="Datum der Bewegung")
    Bewegungsplan: list[BewegungsplanZeile] = Field(description="Tabelle mit Bewegungsplandetails")
    unterschrift_leistungserbringer: str = Field(description="Unterschrift des Leistungserbringers")


class Patient(BaseModel):
    name: str
    geburtsdatum: date


class Leistungserbringer(BaseModel):
    name: str
    adresse: str


class BewegungsplanZeile(BaseModel):
    art_der_bewegung: str
    dauer_minuten: int
    intensitaet: str


# ------------------------------------------------------------
# KDL: AM190110 - Schriftverkehr Amt/ Behörde/ Anwalt
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class SchriftverkehrAmtBehoerdeAnwalt(KdlDocumentBase):
    empfaenger: str = Field(description="Empfänger des Schriftverkehrs")
    absender: str = Field(description="Absender des Schriftverkehrs")
    betrifft: str = Field(description="Betreff des Schriftverkehrs")
    text: str = Field(description="Text des Schriftverkehrs")


# ------------------------------------------------------------
# KDL: AM190199 - ben, die nicht in einer spezifischeren KDL dieser Unterklasse abgebildet werden können. Sonstiger Schriftverkehr
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class BenDienlichSonstigerSchriftverkehr(KdlDocumentBase):
    dokumenttyp: str = Field(description="AM190199")
    empfaenger: str = Field(description="Empfänger des Dokuments")
    absender: str = Field(description="Absender des Dokuments")
    betrifft_patienten_id: str = Field(
        description="ID des Patienten, auf den sich das Dokument bezieht"
    )
    betrifft_patienten_name: str = Field(
        description="Name des Patienten, auf den sich das Dokument bezieht"
    )
    betrifft_patienten_geburtsdatum: str = Field(
        description="Geburtstag des Patienten, auf den sich das Dokument bezieht"
    )
    betrifft_patienten_strasse: str = Field(
        description="Straße des Patienten, auf den sich das Dokument bezieht"
    )
    betrifft_patienten_hausnummer: str = Field(
        description="Hausnummer des Patienten, auf den sich das Dokument bezieht"
    )
    betrifft_patienten_plz: str = Field(
        description="PLZ des Patienten, auf den sich das Dokument bezieht"
    )
    betrifft_patienten_ort: str = Field(
        description="Ort des Patienten, auf den sich das Dokument bezieht"
    )
    text: str = Field(description="Text des Dokuments")


# ------------------------------------------------------------
# KDL: AM190201 - Beratungsbogen Sozialer Dienst
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_type: str = Field(description="Art des medizinischen Dokuments")


class BeratungsbogenSozialerDienst(KdlDocumentBase):
    kdl_code: str = "AM190201"
    document_type: str = "Beratungsbogen Sozialer Dienst"

    patient_id: str = Field(description="Patienten-ID")
    patient_name: str = Field(description="Name des Patienten")
    birth_date: str = Field(description="Geburtsdatum des Patienten")

    social_service_contact: bool = Field(description="Kontakt zum sozialen Dienst gewünscht")
    contact_reason: str = Field(description="Grund für den Kontakt zum sozialen Dienst")

    care_level: str = Field(description="Pflegegrad nach SGB XI")
    care_need: str = Field(description="Pflegebedürftigkeit nach SGB XI")

    health_insurance: str = Field(description="Krankenkasse des Patienten")


# ------------------------------------------------------------
# KDL: AM190202 - Soziotherapeutischer Betreuungsplan
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    version: int


class SoziotherapeutischerBetreuungsplan(KdlDocumentBase):
    kdl_code = "AM190202"
    version: int = Field(..., description="Version des Betreuungsplans")
    patient: dict = Field(..., description="Patientendaten")
    betreuung: list = Field([], description="Betreuungsplan")
    diagnose: str = Field(..., description="Diagnose")
    behandlungsdauer: int = Field(..., description="Behandlungsdauer in Tagen")


# ------------------------------------------------------------
# KDL: AM190203 - ben über den notarztspezifischen Einsatz. Einschätzung Sozialdienst
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class benüberdennotarztspezifischenEinsatz(EinschätzungSozialdienst(KdlDocumentBase)):
    kdl_code: str = Field(
        default="AM190203", description="KDL-Code für den notarztspezifischen Einsatz"
    )
    patient_id: UUID = Field(description="ID des Patienten")
    social_service_evaluation: str = Field(description="Einschätzung des Sozialdiensts")


# ------------------------------------------------------------
# KDL: AM190204 - Überweisungsschein Abschlussbericht Sozialdienst
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class UeberweisungsscheinAbschlussberichtSozialdienst(KdlDocumentBase):
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    patient_insurance_number: str = Field(description="Versicherungsnummer des Patienten")
    referring_doctor: str = Field(description="Name des überweisenden Arztes")
    referral_date: str = Field(description="Datum der Überweisung")
    social_service_report: str = Field(description="Abschlussbericht Sozialdienst")


# ------------------------------------------------------------
# KDL: AM190299 - Sonstiger Aufklärungsbogen …
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class SonstigerAufklärungsbogen(KdlDocumentBase):
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    doctor_name: str = Field(description="Name des Arztes")
    date_of_creation: str = Field(description="Erstellungsdatum des Dokuments")
    consent_given: bool = Field(description="Entscheidung des Patienten zur Einwilligung")


# ------------------------------------------------------------
# KDL: AM220101 - (Behandlungsplan für Maßnahmen zur künstlichen Befruchtung) Behandlungsvertrag
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    document_type: str


class Behandlungsvertrag(KdlDocumentBase):
    kdl_code = "AM220101"
    document_type = "Behandlungsplan für Maßnahmen zur künstlichen Befruchtung"

    patient: dict = Field(description="Patientendaten")
    behandlungspartner: list[dict] = Field(description="Behandlungspartnerdaten")
    befruchtungsmethode: str = Field(description="Methode der künstlichen Befruchtung")
    voraussichtliches_datum_der_befruchtung: date = Field(
        description="Voraussichtliches Datum der Befruchtung"
    )
    behandlungsplan: list[dict] = Field(
        description="Behandlungsplan für Maßnahmen zur künstlichen Befruchtung"
    )


# ------------------------------------------------------------
# KDL: AM220102 - schriftliche Bevollmächtigung, bestimmte Interessen Dritter zu vertreten. Wahlleistungsvertrag
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class UvertretenWahlleistungsvertrag(KdlDocumentBase):
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    patient_address: str = Field(description="Adresse des Patienten")
    bevollmächtigter_name: str = Field(description="Name der Person, die bevollmächtigt wird")
    bevollmächtigter_relationship: str = Field(description="Beziehung zur bevollmächtigten Person")
    bevollmächtigung_text: str = Field(description="Text der schriftlichen Bevollmächtigung")
    wahlleistungen: list[str] = Field(description="Liste der gewählten Wahlleistungen")


# ------------------------------------------------------------
# KDL: AM220103 - verordnung), 8a (Verordnung von vergrößernden Sehhilfen), 13 (Heilmittelverordnung Physikalische Therapie), 14, 15 (VO einer Hörhilfe), 18 (VO Ergotherapie), 28 (VO Sozialdienst) Heimvertrag
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Verordnung8a(KdlDocumentBase):
    verordnung_id: str = Field(description="ID der Verordnung")
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    doctor_name: str = Field(description="Name des Arztes")
    doctor_signature: str = Field(description="Unterschrift des Arztes")
    prescription_date: str = Field(description="Datum der Verordnung")
    glasses_prescription: dict = Field(description="Verordnung für Sehhilfen")


class Heilmittelverordnung13(KdlDocumentBase):
    verordnung_id: str = Field(description="ID der Verordnung")
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    doctor_name: str = Field(description="Name des Arztes")
    doctor_signature: str = Field(description="Unterschrift des Arztes")
    prescription_date: str = Field(description="Datum der Verordnung")
    therapy_type: str = Field(description="Art der Physikalischen Therapie")


class VoHoerhilfe15(KdlDocumentBase):
    verordnung_id: str = Field(description="ID der Verordnung")
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    doctor_name: str = Field(description="Name des Arztes")
    doctor_signature: str = Field(description="Unterschrift des Arztes")
    prescription_date: str = Field(description="Datum der Verordnung")
    hoerhilfe_type: str = Field(description="Art der Hörhilfe")


class VoErgotherapie18(KdlDocumentBase):
    verordnung_id: str = Field(description="ID der Verordnung")
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    doctor_name: str = Field(description="Name des Arztes")
    doctor_signature: str = Field(description="Unterschrift des Arztes")
    prescription_date: str = Field(description="Datum der Verordnung")
    ergotherapie_type: str = Field(description="Art der Ergotherapie")


class VoSozialdienst28(KdlDocumentBase):
    verordnung_id: str = Field(description="ID der Verordnung")
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    doctor_name: str = Field(description="Name des Arztes")
    doctor_signature: str = Field(description="Unterschrift des Arztes")
    prescription_date: str = Field(description="Datum der Verordnung")
    sozialdienst_type: str = Field(description="Art des Sozialdienstes")


class Heimvertrag(KdlDocumentBase):
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    contract_date: str = Field(description="Datum des Heimvertrages")
    contract_details: dict = Field(description="Details zum Heimvertrag")


# ------------------------------------------------------------
# KDL: AM220199 - Sonstiges Dokument Sozialdienst
# Standard: Gesetzliche Vorgaben (SGB V, SGB XI, BGB), KBV Vordrucke (Muster-Formulare)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code des Dokuments")
    document_type: str = Field(description="Typ des Dokuments")


class SonstigesDokumentSozialdienst(KdlDocumentBase):
    kdl_code: str = "AM220199"
    document_type: str = "Sonstiges Dokument Sozialdienst"

    patient_id: int = Field(description="Patienten-ID")
    social_service_provider: str = Field(description="Sozialdienstleister")
    service_date: str = Field(description="Datum der Leistungserbringung")
    service_description: str = Field(description="Beschreibung der erbrachten Leistung")


# ------------------------------------------------------------
# KDL: AU010101 - gebundenen Indexierung verwendet werden. Um sicherzustellen, dass sich beispielsweise die Rechtschreibkorrektur der Klassenbezeichnung nicht negativ auswirkt, wenn diese bereits verwendet wurde, ist jeder KDL eine Notation vorangestellt. Diese Notation beschreibt den Deskriptor eineindeutig. Wird eine Dokumentenklasse deaktiviert, wird diese Notation auch nicht neu vergeben. Im Klassifikationssystem selbst entsteht eine Lücke. Wichtig ist, dass
# Standard: KBV-Standardformulare (Muster 2, 6, 7), G-BA Aufnahme-/Einweisungsrichtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code")
    description: str = Field(description="Beschreibung")


class GebundenenIndexierungverwendetwerden(KdlDocumentBase):
    pass


# ------------------------------------------------------------
# KDL: AU010102 - Anmeldung Aufnahme
# Standard: KBV-Standardformulare (Muster 2, 6, 7), G-BA Aufnahme-/Einweisungsrichtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class AnmeldungAufnahme(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")
    insurance_company: str = Field(description="Krankenkasse")
    admission_date: str = Field(description="Aufnahmedatum")
    discharge_date: str = Field(description="Entlassungsdatum")
    diagnosis: str = Field(description="Diagnose")
    treatment: str = Field(description="Behandlung")


# ------------------------------------------------------------
# KDL: AU010103 - ben über die Aufklärung der geplanten Therapie, inklusive anamnestischer Erhebungen. Aufnahmebogen
# Standard: KBV-Standardformulare (Muster 2, 6, 7), G-BA Aufnahme-/Einweisungsrichtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class TischerErhebungenAufnahmebogen(KdlDocumentBase):
    patient_name: str = Field(description="Name des Patienten")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    sex: str = Field(description="Geschlecht des Patienten")
    address: str = Field(description="Adresse des Patienten")
    insurance_company: str = Field(description="Krankenkasse des Patienten")
    anamnestic_findings: list[str] = Field(description="Anamnestische Befunde")
    planned_therapy: str = Field(description="Geplante Therapie")


# ------------------------------------------------------------
# KDL: AU010104 - Checkliste Aufnahme
# Standard: KBV-Standardformulare (Muster 2, 6, 7), G-BA Aufnahme-/Einweisungsrichtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_type: str = Field(description="Art des medizinischen Dokuments")


class ChecklisteAufnahme(KdlDocumentBase):
    kdl_code: str = "AU010104"
    document_type: str = "Checkliste Aufnahme"

    aufnahmegrund: str = Field(description="Grund der Aufnahme")
    diagnose: str = Field(description="Diagnose")
    laborwerte: list[Dict[str, Any]] = Field(default_factory=list, description="Laborwerte")


# ------------------------------------------------------------
# KDL: AU010105 - Stammblatt
# Standard: KBV-Standardformulare (Muster 2, 6, 7), G-BA Aufnahme-/Einweisungsrichtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Stammblatt(KdlDocumentBase):
    kdl_code: str = Field(default="AU010105", const=True)
    patient_id: UUID
    birth_date: date
    sex: Literal["m", "w"]
    family_name: str
    given_names: str
    street: str
    postal_code: str
    city: str
    phone_number: str | None = None
    email_address: EmailStr | None = None
    insurance_company: str
    insurance_policy_holder: str
    insurance_policy_number: str
    responsible_physician: str
    admission_date: date
    discharge_date: date | None = None
    diagnoses: list[str]
    allergies: list[str]
    medications: list[str]
    laboratory_results: list["LaborResult"]
    notes: str


class LaborResult(BaseModel):
    test_name: str
    result_value: float
    unit_of_measurement: str
    reference_range: str


# ------------------------------------------------------------
# KDL: AU010199 - Sonstiger Vertrag
# Standard: KBV-Standardformulare (Muster 2, 6, 7), G-BA Aufnahme-/Einweisungsrichtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class SonstigerVertrag(KdlDocumentBase):
    dokument_id: str = Field(description="Dokument-ID")
    version: int = Field(description="Version des Dokuments")
    erstellungszeitpunkt: datetime = Field(description="Erstellungszeitpunkt des Dokuments")
    autor_id: str = Field(description="ID des Autors")
    autor_name: str = Field(description="Name des Autors")
    vertragsbeginn: date = Field(description="Beginn des Vertrages")
    vertragsend: date = Field(description="Ende des Vertrages")
    vertragspartner_id: str = Field(description="ID des Vertragspartners")
    vertragspartner_name: str = Field(description="Name des Vertragspartners")


# ------------------------------------------------------------
# KDL: AU050101 - AD0201 = fortlaufende Nummer Abb. 12: Herleitung Notation für die Unterklassen der KDL-2021 2.5.3. DOKUMENTENKLASSEN DER KDL Mit der Version 2021 umfasst die KDL 381 Dokumentenklassen
# Standard: KBV-Standardformulare (Muster 2, 6, 7), G-BA Aufnahme-/Einweisungsrichtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class AD0201(KdlDocumentBase):
    dokumentenklasse_kennzeichen: str = Field(description="Kennung der Dokumentenklasse")
    fortlaufende_nummer: int = Field(
        description="Fortlaufende Nummer innerhalb der Dokumentenklasse"
    )
    patient_id: str = Field(description="Patient-ID")
    dokumententitel: str = Field(description="Titel des Dokuments")
    erstellungsdatum: str = Field(description="Erstellungsdatum des Dokuments")
    erstellender_arzt: str = Field(description="Name des erstellenden Arztes")


# ------------------------------------------------------------
# KDL: AU050102 - Überweisungsschein
# Standard: KBV-Standardformulare (Muster 2, 6, 7), G-BA Aufnahme-/Einweisungsrichtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code")


class Ueberweisungsschein(KdlDocumentBase):
    ueberweisender_arzt: str = Field(description="Überweisender Arzt")
    ueberweisungsgrund: str = Field(description="Übergreifendes ÜG")
    patient_name: str = Field(description="Patient Name")
    patient_birthdate: str = Field(description="Patient Geburtsdatum")
    patient_gender: str = Field(description="Patient Geschlecht")
    patient_street: str = Field(description="Patient Straße")
    patient_city: str = Field(description="Patient Stadt")
    patient_postal_code: str = Field(description="Patient PLZ")
    patient_phone_number: str = Field(description="Patient Telefonnummer")
    patient_email: str = Field(description="Patient E-Mail")
    ueberweisungsdatum: str = Field(description="Übergreifendes ÜD")
    ueberweisungsziel: str = Field(description="Übergreifendes ÜZ")


# ------------------------------------------------------------
# KDL: AU050104 - Verlegungsschein intern Verlegungsschein intern
# Standard: KBV-Standardformulare (Muster 2, 6, 7), G-BA Aufnahme-/Einweisungsrichtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class VerlegungsscheininternVerlegungsscheinintern(KdlDocumentBase):
    kdl_code: str = "AU050104"
    document_type: str = "Verlegungsschein intern"

    patient_id: str = Field(description="Patienten-ID")
    sender_institution: str = Field(description="Absendende Einrichtung")
    receiver_institution: str = Field(description="Empfangene Einrichtung")
    admission_date: datetime = Field(description="Einweisungsdatum")
    discharge_date: datetime = Field(description="Entlassungsdatum")
    diagnosis: str = Field(description="Diagnose")
    treatment: str = Field(description="Behandlung")


# ------------------------------------------------------------
# KDL: AU050199 - Meldung an Sozialdienst, Verlaufsdokumentation Sozialdienst Sonstiges Einweisungs-/ Überweisungsdokument
# Standard: KBV-Standardformulare (Muster 2, 6, 7), G-BA Aufnahme-/Einweisungsrichtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class SozialdienstEinweisungsdokument(KdlDocumentBase):
    einweisender_arzt: str = Field(description="Name des einweisenden Arztes")
    patient_name: str = Field(description="Name des Patienten")
    patient_gender: str = Field(description="Geschlecht des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    social_service_reason: str = Field(description="Grund für die Meldung an den Sozialdienst")
    additional_information: str = Field(description="Zusätzliche Informationen zum Patienten")


class VerlaufsdokumentationSozialdienstSonstigesEinweisungsUberweisungsdokument(
    SozialdienstEinweisungsdokument
):
    pass


# ------------------------------------------------------------
# KDL: AU190101 - Einsatzprotokoll
# Standard: KBV-Standardformulare (Muster 2, 6, 7), G-BA Aufnahme-/Einweisungsrichtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class Einsatzprotokoll(KdlDocumentBase):
    kdl_code: str = "AU190101"
    document_type: str = "Einsatzprotokoll"

    patient_id: str = Field(description="Patientenkennung")
    date_of_birth: str = Field(description="Geburtsdatum des Patienten")
    sex: str = Field(description="Geschlecht des Patienten")

    attending_physician: str = Field(description="Attestierender Arzt")
    diagnosis: str = Field(description="Diagnose")

    treatment: str = Field(description="Behandlung")


# ------------------------------------------------------------
# KDL: AU190102 - Notaufnahmebericht
# Standard: KBV-Standardformulare (Muster 2, 6, 7), G-BA Aufnahme-/Einweisungsrichtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class Notaufnahmebericht(KdlDocumentBase):
    kdl_code: str = "AU190102"
    document_type: str = "Notaufnahmebericht"

    patient: dict = Field(description="Patientendaten")
    anamnese: str = Field(description="Anamnese")
    diagnose: str = Field(description="Diagnose")
    laborwerte: list[dict] = Field(description="Laborwerte", default=[])


# ------------------------------------------------------------
# KDL: AU190103 - ärztlichen Bericht über die Behandlung in der Notaufnahme. Notaufnahmebogen
# Standard: KBV-Standardformulare (Muster 2, 6, 7), G-BA Aufnahme-/Einweisungsrichtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class Notaufnahmebogen(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")
    diagnosis: str = Field(description="Diagnose")
    treatment: str = Field(description="Behandlung")


# ------------------------------------------------------------
# KDL: AU190105 - ben zur Einschätzung des Harnverhalts
# Standard: KBV-Standardformulare (Muster 2, 6, 7), G-BA Aufnahme-/Einweisungsrichtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class BenzurEinschätzungdesHarnverhalts(KdlDocumentBase):
    patient_id: int = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    gender: str = Field(description="Geschlecht des Patienten")
    diagnosis: str = Field(description="Diagnose")
    treatment: str = Field(description="Behandlung")
    assessment: str = Field(description="Einschätzung des Harnverhalts")


# ------------------------------------------------------------
# KDL: AU190199 - tentypen, die nicht in einer spezifischeren KDL dieser Unterklasse abgebildet werden können, jedoch elektronisch direkt ausgetauscht wird. Sonstige Dokumentation Rettungsstelle
# Standard: KBV-Standardformulare (Muster 2, 6, 7), G-BA Aufnahme-/Einweisungsrichtlinie
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class TentypenSonstigeDokumentationRettungsstelle(KdlDocumentBase):
    dokumenttyp: str = Field(description="KDL-Code für den Dokumenttyp")
    version: int = Field(description="Version des Dokuments")
    erstellungszeitpunkt: datetime.datetime = Field(
        description="Zeitpunkt der Erstellung des Dokuments"
    )
    autor_id: UUID = Field(description="ID des Autors des Dokuments")
    autor_name: str = Field(description="Name des Autors des Dokuments")
    autor_berufstitel: str = Field(description="Berufstitel des Autors des Dokuments")
    autor_institution: str = Field(description="Institution des Autors des Dokuments")
    patient_id: UUID = Field(description="ID des Patienten")
    patient_name: str = Field(description="Name des Patienten")
    patient_geburtsdatum: date = Field(description="Geburtsdatum des Patienten")
    patient_gender: Literal["m", "w", "d"] = Field(description="Geschlecht des Patienten")
    tentypen: list[TentypenItem] = Field(description="Liste der Tentypen-Items")


class TentypenItem(BaseModel):
    typ: str = Field(description="Typ des Tentypens")
    wert: Union[str, int, float] = Field(description="Wert des Tentypens")


# ------------------------------------------------------------
# KDL: DG020101 - mische Abbildungen, die zur Befunderhebung dienen. Anforderung bildgebende Diagnostik
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ForderungBildgebendeDiagnostik(KdlDocumentBase):
    report_id: str = Field(description="Berichts-ID")
    patient_id: str = Field(description="Patient-ID")
    examination_date: datetime = Field(description="Untersuchungsdatum")
    modality: list[str] = Field(description="Modalitäten (z.B. CT, MR)")
    body_part_examined: str = Field(description="Untersuchter Körperteil")
    clinical_indication: str = Field(description="Klinischer Befund")
    findings: list[dict] = Field(description="Befunde", default_factory=list)
    impressions: str = Field(description="Eindrücke")
    recommendations: list[str] = Field(description="Empfehlungen")


# ------------------------------------------------------------
# KDL: DG020102 - Anforderung von Unterlagen, die für den aktuellen Behandlungsverlauf relevant sind. Angiographiebefund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class RelevantSindAngiographiebefund(KdlDocumentBase):
    dokument_typ: str = Field(description="Art des Dokuments")
    patient_id: str = Field(description="Patientenkennung")
    angefordertes_unterlagenformat: str = Field(description="Format der angeforderten Unterlagen")
    angeforderte_untersuchungen: list[str] = Field(
        description="Liste der angeforderten Untersuchungen"
    )
    angefordert_am: datetime = Field(
        description="Datum und Uhrzeit, zu denen die Unterlagen angefordert wurden"
    )
    ansprechpartner: str = Field(description="Ansprechpartner für Rückfragen")
    loinc_codes: list[str] = Field(description="LOINC-Codes der relevanten Befunde")


# ------------------------------------------------------------
# KDL: DG020103 - bungen für Klinische Studien. Diese sind inhaltlich unterschiedlich und abhängig von der Fragestellung der durchzuführenden Studie. CT-Befund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class DurchzuführendenStudieCTBefund(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    study_instance_uid: str = Field(description="UID der Studie")
    series_instance_uid: str = Field(description="UID der Serie")
    modality: str = Field(description="Modalität (z.B. CT)")
    body_part_examined: str = Field(description="Untersuchungsbereich")
    clinical_trial_id: str = Field(description="ID der klinischen Studie")
    loinc_code: str = Field(description="LOINC-Code für den Befund")
    diagnostic_impressions: str = Field(description="Diagnostische Schlüsse")
    findings: list[dict[str, str]] = Field(description="Befunde", default_factory=list)


# ------------------------------------------------------------
# KDL: DG020104 - Modul in der Praxissoftware niedergelassener Ärzte, um den eArztbrief direkt auszutauschen. Entspricht den Anforderungen der Telematikinfrastruktur. Echokardiographiebefund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class TrukturEchokardiographiebefund(KdlDocumentBase):
    report_id: str = Field(description="ID des Echokardiographieberichts")
    patient_id: str = Field(description="Patient-ID")
    report_date: datetime = Field(description="Datum des Echokardiographieberichts")
    physician_id: str = Field(description="ID des ausstellenden Arztes")
    loinc_code: str = Field(description="LOINC-Code für Echokardiographie")
    findings: list[str] = Field(description="Echokardiographische Befunde")


# ------------------------------------------------------------
# KDL: DG020105 - Nachweis für den Empfang von Dokumenten, Medikamenten, Hilfsmittel usw. Endoskopiebefund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class HilfsmitteluswEndoskopiebefund(KdlDocumentBase):
    nachweisnummer: str = Field(description="Nachweisnummer")
    patient_id: str = Field(description="Patient ID")
    dokumente: list[str] = Field(description="Empfangene Dokumente")
    medikamente: list[str] = Field(description="Empfangene Medikamente")
    hilfsmittel: list[str] = Field(description="Empfangene Hilfsmittel")
    endoskopiebefund: str = Field(description="Endoskopiebefund")


# ------------------------------------------------------------
# KDL: DG020106 - ben im Rahmen der Herstellung von Blut und Blutprodukten. Mindestinhalte sind: Datum, verantwortliche Person, Art des Blutes bzw. Blutproduktes. Herzkatheterprotokoll
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Herzkatheterprotokoll(KdlDocumentBase):
    datum: datetime = Field(description="Das Datum der Herstellung")
    verantwortliche_person: str = Field(
        description="Die verantwortliche Person für die Herstellung"
    )
    art_des_blutes_bzw_blutprodukts: str = Field(
        description="Die Art des Blutes bzw. Blutproduktes"
    )
    herzkatheter_protokoll: str = Field(description="Das Herzkatheterprotokoll")


# ------------------------------------------------------------
# KDL: DG020107 - ben über den Mehraufwand bei einer Infektion durch multiresistente Keime. MRT-Befund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class MultiresistenteKeime_MRTBefund(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code")
    diagnosis_date: datetime = Field(description="Diagnosedatum")
    patient_id: UUID = Field(description="Patienten-ID")
    report_text: str = Field(description="Berichtstext")
    mrt_findings: list[MRTFinding] = Field(description="MRT-Befunde")


class MRTFinding(BaseModel):
    finding_code: str = Field(description="LOINC-Code für den MRT-Befund")
    finding_description: str = Field(description="Beschreibung des MRT-Befundes")


# ------------------------------------------------------------
# KDL: DG020108 - Notfall wichtige Daten des Patienten – gespeichert auf der elektronischen Gesundheitskarte. OCT-Befund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ChenGesundheitskarte_OCTBefund(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")
    oct_report: dict = Field(description="OCT-Bericht")


# ------------------------------------------------------------
# KDL: DG020109 - PET-Befund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class PETBefund(KdlDocumentBase):
    kdl_code: str = "DG020109"
    document_type: str = "PET-Befund"

    patient_id: str = Field(description="Patientenkennung")
    examination_date: datetime = Field(description="Untersuchungsdatum")
    report_text: str = Field(description="Befundtext")

    # Laborwerte-Tabelle
    class LabValues(BaseModel):
        substance: str = Field(description="Substanz")
        value: float = Field(description="Wert")
        unit: str = Field(description="Einheit")

    lab_values: list[LabValues] = Field(default_factory=list, description="Laborwerte")


# ------------------------------------------------------------
# KDL: DG020110 - Ergeb
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ErgebnisZeile(BaseModel):
    loinc_code: str = Field(description="LOINC Code")
    name: str = Field(description="Name des Parameters")
    einheit: str = Field(description="Einheit des Parameters")
    wert: float | int = Field(description="Wert des Parameters")


class Ergebnis(KdlDocumentBase):
    dokument_id: uuid.UUID = Field(description="Dokument-ID")
    erstellungszeitpunkt: datetime.datetime = Field(description="Erstellungszeitpunkt")
    autor: str = Field(description="Autor des Dokuments")
    laborergebnisse: list[ErgebnisZeile] = Field(description="Laborergebnisse")


# ------------------------------------------------------------
# KDL: DG020111 - en zur Art und Dauer der zu verabreichenden Sondennahrung. Sonographiebefund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class SondennahrungSonographiebefund(KdlDocumentBase):
    art_der_sondennahrung: str = Field(description="Art der Sondennahrung")
    dauer_der_sondennahrung: int = Field(description="Dauer der Sondennahrung in Tagen")
    beginn_datum: str = Field(description="Beginn der Sondennahrung (YYYY-MM-DD)")


# ------------------------------------------------------------
# KDL: DG020112 - ben mit Therapiezielen, verordneten empfohlenen Maßnahmen usw., welche durch den Sozialen Dienst an die Krankenkasse weitergeleitet werden (KBV Muster 27). SPECT-Befund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class LenenMassnahmenUswKrankenkasse(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code")
    diagnose: str = Field(description="Diagnose")
    therapieziele: list[str] = Field(description="Therapieziele")
    empfohlene_maassenahmen: list[str] = Field(description="Empfohlene Maßnahmen")
    sozialer_dienst: str = Field(description="Sozialer Dienst")
    krankenkasse: str = Field(description="Krankenkasse")
    spect_befund: dict = Field(description="SPECT-Befund")


class SpectBefund(BaseModel):
    loinc_code: str = Field(description="LOINC-Code")
    beschreibung: str = Field(description="Beschreibung")
    ergebnis: float = Field(description="Ergebnis")


# ------------------------------------------------------------
# KDL: DG020113 - Szintigraphiebefund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Szintigraphiebefund(KdlDocumentBase):
    report_id: UUID = Field(description="Bericht-ID")
    patient_id: UUID = Field(description="Patient-ID")
    examination_date: datetime = Field(description="Untersuchungsdatum")
    physician: str = Field(description="Arzt/Ärztin")
    diagnosis: str = Field(description="Diagnose")
    findings: list[str] = Field(description="Befunde")


# ------------------------------------------------------------
# KDL: DG020114 - Mammographiebefund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class Mammographiebefund(KdlDocumentBase):
    kdl_code: str = "DG020114"
    document_type: str = "Mammographie Befund"

    class Config:
        schema_extra = {
            "example": {
                "kdl_code": "DG020114",
                "document_type": "Mammographie Befund",
                "patient_id": "1234567890",
                "examination_date": "2022-01-01",
                "radiologist": "Dr. Beispiel",
                "findings": [
                    {"location": "links", "description": "Kleiner Knoten"},
                    {"location": "rechts", "description": "Keine Auffälligkeiten"},
                ],
            }
        }

    patient_id: str = Field(description="Patienten-ID")
    examination_date: str = Field(description="Untersuchungsdatum im Format YYYY-MM-DD")
    radiologist: str = Field(description="Strahlender Arzt")
    findings: list[dict] = Field(description="Befunde")

    class Config:
        schema_extra = {
            "example": [
                {"location": "links", "description": "Kleiner Knoten"},
                {"location": "rechts", "description": "Keine Auffälligkeiten"},
            ]
        }


# ------------------------------------------------------------
# KDL: DG020115 - ben über erforderliche medizinische, organisatorische Maßnahmen zum Aufnahmezeitpunkt. Erfolgte Durchführungen werden gekennzeichnet. Checkliste bildgebende Diagnostik
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class HecklistebildgebendeDiagnostik(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    birth_date: date = Field(description="Geburtsdatum des Patienten")
    sex: Literal["m", "w"] = Field(description="Geschlecht des Patienten")
    medical_measures: list[str] = Field(description="Erforderliche medizinische Maßnahmen")
    organizational_measures: list[str] = Field(
        description="Erforderliche organisatorische Maßnahmen"
    )
    performed_procedures: list[str] = Field(description="Erfolgte Durchführungen")
    imaging_diagnostics_checklist: list[str] = Field(
        description="Checkliste bildgebende Diagnostik"
    )


# ------------------------------------------------------------
# KDL: DG020199 - Dialysevisite Sonstige Dokumentation bildgebende Diagnostik
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")
    document_type: str = Field(description="Dokumenttyp")


class MentationbildgebendeDiagnostik(KdlDocumentBase):
    kdl_code: str = "DG020199"
    document_type: str = "Dialysevisite Sonstige Dokumentation bildgebende Diagnostik"

    patient_id: str = Field(description="Patient ID")
    examination_date: datetime = Field(description="Examindatum")
    findings: list[str] = Field(description="Befunde")
    images: list[Dict[str, Any]] = Field(description="Bilddaten")


# ------------------------------------------------------------
# KDL: DG060101 - forderung von benötigten Blutkonserven bei einer Blutbank. Anforderung Funktionsdiagnostik
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class AnforderungFunktionsdiagnostik(KdlDocumentBase):
    loinc_code: str = Field(
        description="LOINC-Kodierung für die Anforderung von benötigten Blutkonserven bei einer Blutbank."
    )
    fachtitel: str = Field(description="Fachlicher Titel der Anforderung.")
    diagnose: str = Field(description="Diagnose, welche die Anforderung rechtfertigt.")
    laborwerte: list[Dict[str, Any]] = Field(
        default_factory=list, description="Tabelle mit Laborwerten."
    )
    laborwerte.append({"parameter": str, "einheit": str, "wert": float, "referenzbereich": str})


# ------------------------------------------------------------
# KDL: DG060102 - Audiometriebefund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Audiometriebefund(KdlDocumentBase):
    report_id: str = Field(description="Bericht-ID")
    patient_id: str = Field(description="Patient-ID")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")
    hearing_loss_side: str = Field(description="Hörverlust-Seite")
    audiometry_type: str = Field(description="Audiometrietyp")
    frequencies: list[float] = Field(description="Frequenzen")
    thresholds: list[int] = Field(description="Schwellenwerte")


# ------------------------------------------------------------
# KDL: DG060103 - standardisierte Anga
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class StandardisierteAnga(KdlDocumentBase):
    anamnese: str = Field(description="Anamnese des Patienten")
    diagnose: str = Field(description="Diagnose des Patienten")
    laborwerte: list[Dict[str, Any]] = Field(
        default_factory=list, description="Laborwerte des Patienten"
    )
    bildgebende_untersuchungen: list[str] = Field(
        description="Bildgebende Untersuchungen des Patienten"
    )
    medikamentöse_therapie: str = Field(description="Medikamentöse Therapie des Patienten")


# ------------------------------------------------------------
# KDL: DG060104 - Erklärung über die Unterbrechung des stationären Aufenthaltes über einen festgelegten Zeitraum. Blutdruckprotokoll
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class GtenZeitraumBlutdruckprotokoll(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    blood_pressure_values: list[dict] = Field(description="Blutdruckwerte", default=[])
    interruption_reason: str = Field(
        description="Grund für die Unterbrechung des stationären Aufenthaltes"
    )
    duration_of_interruption: int = Field(description="Dauer der Unterbrechung in Tagen")


# ------------------------------------------------------------
# KDL: DG060105 - CTG-Ausdruck
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class CTGAusdruck(KdlDocumentBase):
    kdl_code: str = Field(default="DG060105", const=True)
    patient_id: UUID
    report_date: datetime
    report_doctor: str
    examination_date: datetime
    examination_type: str
    findings: list[str]
    measurements: list[Dict[str, float]]
    impressions: str


# ------------------------------------------------------------
# KDL: DG060106 - Operierens, die nicht in einer spezifischeren KDL dieser Unterklasse abgebildet werden kann. Dokumentationsbogen Feststellung Hirntod
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class OperierensDokumentationsbogenFeststellungHirntod(KdlDocumentBase):
    dokumentationstitel: str = Field(description="Titel der Dokumentation")
    patient_id: str = Field(description="Patient ID")
    operateur: str = Field(description="Name des Operateurs")
    operation_datum: datetime = Field(description="Datum der Operation")
    hirntod_feststellungzeitpunkt: datetime = Field(description="Zeitpunkt der Hirntodfeststellung")
    hirntod_feststellungsmethode: str = Field(description="Methode der Hirntodfeststellung")
    klinische_untersuchung: bool = Field(description="Klinische Untersuchung durchgeführt?")
    laboruntersuchungen: list[Laborwert] = Field(default_factory=list, description="Laborwerte")


class Laborwert(BaseModel):
    loinc_code: str = Field(description="LOINC-Code des Laborwerts")
    wert: float = Field(description="Wert des Laborparameters")


# ------------------------------------------------------------
# KDL: DG060107 - Irreversibilitätsnachweis zur Feststellung des Hirnfunktionsausfalls. Dokumentationsbogen Herzschrittmacherkontrolle
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        schema_extra = {
            "title": "IrreversibilitätsnachweiszurFeststellungdesHirnfunktionsausfalls.DokumentationsbogenHerzschrittmacherkontrolle"
        }


class OgenHerzschrittmacherkontrolle(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    gender: str = Field(description="Geschlecht des Patienten")
    diagnosis: str = Field(description="Diagnose")
    examination_date: str = Field(description="Datum der Untersuchung")
    irreversibility_criteria_met: bool = Field(
        description="Ob die Kriterien für den Hirnfunktionsausfall erfüllt sind"
    )
    clinical_examination: dict = Field(description="Ergebnisse der klinischen Untersuchung")
    neurophysiological_examinations: list[dict] = Field(
        description="Ergebnisse der neurophysiologischen Untersuchungen"
    )


# ------------------------------------------------------------
# KDL: DG060108 - nisse einer Nachsorgeuntersuchung nach dem Einsetzen eines Herzschrittmacherimplantats. Dokumentationsbogen Lungenfunktionsprüfung
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Lungenfunktionspruefung(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    sex: str = Field(description="Geschlecht des Patienten")
    height: float = Field(description="Körpergröße des Patienten in cm")
    weight: float = Field(description="Körpergewicht des Patienten in kg")
    lungenfunktions_pruefung_datum: str = Field(description="Datum der Lungenfunktionsprüfung")
    spiro_volumen: float = Field(description="Spirometrie-Volumen in ml")
    spiro_flow: float = Field(description="Spirometrie-Flow in l/min")
    spiro_tidal_volume: float = Field(description="Tidal Volume in ml")
    spiro_respiratory_rate: float = Field(description="Respiratorische Rate in Atemzüge/min")


# ------------------------------------------------------------
# KDL: DG060109 - nisse einer ultraschallgestützten Untersuchung der Struktur und Funktion des Herzens, welche bildlich dargestellt und ausgewertet werden. EEGAuswertung
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class EEGAuswertung(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    birth_date: str = Field(description="Birth date of the patient")
    sex: str = Field(description="Sex of the patient")
    examination_date: str = Field(description="Date of the examination")
    report_text: str = Field(description="Textual report of the examination")
    findings: list[dict] = Field(default_factory=list, description="List of findings")
    EEG_data: dict = Field(description="EEG data")


# ------------------------------------------------------------
# KDL: DG060110 - Informationsaustausch per E-Mail – direkt elektronisch oder ausgedruckt in Papierkrankenakte - die nicht in einer spezifischeren KDL dieser Unterklasse abgebildet werden kann. EMG-Befund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class EabgebildetwerdenkannEMGBefund(KdlDocumentBase):
    emg_befund: str = Field(description="EMG-Befund")


# ------------------------------------------------------------
# KDL: DG060111 - EKGAuswertung
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class EKGAuswertung(KdlDocumentBase):
    kdl_code: str = "DG060111"
    report_id: UUID
    patient_id: UUID
    ausstellungsdatum: datetime
    auswertender_arzt: str
    laborwerte: list[Laborwerte]
    befund: str | None = Field(default="", description="Befundbeschreibung")


class Laborwerte(BaseModel):
    parameter: str
    loinc_code: str
    wert: float
    einheit: str
    referenzbereich: str


# ------------------------------------------------------------
# KDL: DG060112 - Manometriebefund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_id: str = Field(description="Dokument-ID")


class Manometriebefund(KdlDocumentBase):
    kdl_code: str = "DG060112"
    document_id: str = Field(description="ID des Manometriebefundes")
    patient_id: str = Field(description="Patient-ID")
    examination_date: str = Field(description="Datum der Untersuchung")
    symptoms: list[str] = Field(description="Symptome des Patienten")
    findings: dict[str, str] = Field(description="Manometrische Befunde")


# ------------------------------------------------------------
# KDL: DG060113 - Messungsprotokoll Augeninnendruck
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class MessungsprotokollAugeninnendruck(KdlDocumentBase):
    report_id: str = Field(description="Bericht-ID")
    patient_id: str = Field(description="Patient-ID")
    measurement_date: datetime = Field(description="Messungsdatum")
    left_eye_pressure: float = Field(description="Linkes Auge - Augeninnendruck in mmHg")
    right_eye_pressure: float = Field(description="Rechtes Auge - Augeninnendruck in mmHg")


# ------------------------------------------------------------
# KDL: DG060114 - Neurographiebefund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Neurographiebefund(KdlDocumentBase):
    kdl_code: str = "DG060114"
    report_type: str = "DiagnosticReport"

    class Befund(BaseModel):
        beschreibung: str = Field(description="Beschreibung des Befundes")
        auswertung: str = Field(description="Auswertung des Befundes")

    befunde: list[Befund] = Field(default_factory=list, description="Liste der Befunde")


# ------------------------------------------------------------
# KDL: DG060115 - Rhinometriebefund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------


from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Rhinometriebefund(KdlDocumentBase):
    report_id: str = Field(description="Bericht ID")
    patient_id: str = Field(description="Patient ID")
    examination_date: str = Field(description="Untersuchungsdatum")
    doctor_signature: str = Field(description="Arztunterschrift")
    diagnosis: list[str] = Field(default=[], description="Diagnosen")
    findings: list[str] = Field(default=[], description="Befunde")


# ------------------------------------------------------------
# KDL: DG060116 - Schlaflabordokumentationsbogen
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Schlaflabordokumentationsbogen(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")
    diagnosis: str = Field(description="Diagnose")
    symptoms: list[str] = Field(description="Symptome")
    sleep_study: dict[str, str] = Field(description="Schlafstudie")
    polysomnography: dict[str, str] = Field(description="Polysomnographie")
    treatment: str = Field(description="Therapie")
    follow_up: str = Field(description="Nachsorge")


# ------------------------------------------------------------
# KDL: DG060117 - Ergeb
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ErgebnisLaborparameter(BaseModel):
    parameter: str = Field(description="Laborparameter")
    einheit: str = Field(description="Einheit des Laborparameters")
    wert: float = Field(description="Wert des Laborparameters")


class ErgebnisDiagnose(BaseModel):
    diagnose: str = Field(description="Diagnose")
    code: str = Field(description="Code der Diagnose")


class ErgebnisMedikation(BaseModel):
    medikament: str = Field(description="Medikament")
    dosierung: str = Field(description="Dosierung des Medikaments")
    einnahme: str = Field(description="Einnahme des Medikaments")


class Ergebnis(ErgebnisLaborparameter, ErgebnisDiagnose, ErgebnisMedikation):
    patient_id: int = Field(description="Patient ID")
    dokument_id: int = Field(description="Dokument ID")
    erstellungsdatum: datetime = Field(description="Erstellungsdatum des Dokuments")


# ------------------------------------------------------------
# KDL: DG060118 - ben, ob die zur Entlassung notwendigen Dokumente/Gegenstände vollständig sind. Checkliste Funktionsdiagnostik
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Checkliste_funktionsdiagnostik(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code")
    diagnose: str = Field(description="Diagnose")
    laborwerte: list[Dict[str, Any]] = Field(default_factory=list, description="Laborwerte")
    bildgebende_verfahren: list[str] = Field(description="Bildgebende Verfahren")
    funktionelle_diagnostik: bool = Field(description="Funktionelle Diagnostik durchgeführt")
    entlassungsplan: str = Field(description="Entlassungsplan")


# ------------------------------------------------------------
# KDL: DG060119 - Ergometriebefund
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")
    document_type: str = Field(description="Document type")


class Ergometriebefund(KdlDocumentBase):
    ergometrie_art: str = Field(description="Art der Ergometrie")
    ergometrie_einheit: str = Field(description="Einheit der Ergometrie")
    ergometrie_dauer: float = Field(description="Dauer der Ergometrie in Minuten")
    ergometrie_max_puls: int = Field(description="Maximaler Puls während der Ergometrie")
    ergometrie_max_belastung: float = Field(
        description="Maximale Belastung während der Ergometrie in Watt"
    )
    ergometrie_steigung: str = Field(description="Steigung der Ergometrie")
    ergometrie_lage: str = Field(description="Lage des Patienten während der Ergometrie")
    ergometrie_bemerkungen: str = Field(description="Bemerkungen zur Ergometrie")


class Laborwert(BaseModel):
    loinc_code: str = Field(description="LOINC Code")
    wert: float = Field(description="Wert des Laborparameters")
    einheit: str = Field(description="Einheit des Laborparameters")


class ErgometriebefundLaborwerte(Ergometriebefund):
    laborwerte: list[Laborwert] = Field(
        default_factory=list, description="Laborparameter im Zusammenhang mit der Ergometrie"
    )


# ------------------------------------------------------------
# KDL: DG060120 - Schmerztherapie, Dialyse, Herzkatheter Kipptischuntersuchung
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ZkatheterKipptischuntersuchung(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code für das medizinische Dokument")
    diagnose: str = Field(description="Diagnose")
    laborwerte: list[Laborwert] = Field(default_factory=list, description="Laborwerte")
    befunde: list[str] = Field(default_factory=list, description="Befunde")


class Laborwert(BaseModel):
    parameter: str = Field(description="LOINC-Kodierung für den Laborparameter")
    wert: float = Field(description="Wert des Laborparameters")
    einheit: str = Field(description="Einheit des Laborparameters")


# ------------------------------------------------------------
# KDL: DG060121 - ben über die Aufwachphase nach einem Eingriff, Operation. Augenuntersuchung
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class Augenuntersuchung(KdlDocumentBase):
    augenuntersuchung_ergebnis: str = Field(description="Ergebnis der Augenuntersuchung")
    augenuntersuchung_bemerkungen: str = Field(description="Bemerkungen zur Augenuntersuchung")


# ------------------------------------------------------------
# KDL: DG060122 - festgelegte Leitlinie bezüglich der Durchführung von Hygienemaßnahmen zum Vermeiden von Gesundheitsschäden durch Erreger. ICD-Kontrolle
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ChädendurchErregerICDKontrolle(KdlDocumentBase):
    leitlinien_id: str = Field(description="ID der Leitlinie")
    erstellungsdatum: datetime = Field(description="Datum der Erstellung")
    autor: list[str] = Field(description="Autor/en der Leitlinie")
    zielgruppe: list[str] = Field(description="Zielgruppe der Leitlinie")
    icd_kontrolle: bool = Field(description="ICD-Kontrolle durchführen?")


# ------------------------------------------------------------
# KDL: DG060123 - Zahlenverbindungstest Zystometrie
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ZahlenverbindungstestZystometrie(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code für den Zahlenverbindungstest Zystometrie")
    loinc_code: str = Field(description="LOINC-Code für den Zahlenverbindungstest Zystometrie")
    diagnose: str = Field(
        description="Diagnose im Zusammenhang mit dem Zahlenverbindungstest Zystometrie"
    )
    laborwerte: list[Laborwert] = Field(
        default_factory=list,
        description="Laborwerte im Zusammenhang mit dem Zahlenverbindungstest Zystometrie",
    )


class Laborwert(BaseModel):
    parameter: str = Field(description="Parameter des Laborwerts")
    einheit: str = Field(description="Einheit des Laborwerts")
    wert: float = Field(description="Wert des Laborwerts")


# ------------------------------------------------------------
# KDL: DG060124 - befund intern/extern Uroflowmetrie
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class BefundInternExternUroflowmetrie(KdlDocumentBase):
    report_id: str = Field(description="Berichts-ID")
    patient_id: str = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")
    measurement_date: str = Field(description="Messungsdatum")
    voiding_time: float = Field(description="Entleerzeit in Sekunden")
    flow_rate_maximum: float = Field(description="Maximale Flussrate in ml/s")
    voided_volume: float = Field(description="Entleerte Menge in ml")
    residual_volume: float = Field(description="Restharnmenge in ml")


# ------------------------------------------------------------
# KDL: DG060199 - ben, die nicht in einer spezifischeren KDL dieser Unterklasse abgebildet werden können. Sonstige Dokumentation Funktionsdiagnostik
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class KumentationFunktionsdiagnostik(KdlDocumentBase):
    report_id: str = Field(description="Berichts-ID")
    patient_id: str = Field(description="Patient-ID")
    report_date: datetime = Field(description="Berichtsdatum")
    report_type: Literal["Sonstige Dokumentation Funktionsdiagnostik"] = Field(
        description="Berichtsart"
    )
    findings: list[str] = Field(description="Befunde")
    recommendations: list[str] = Field(description="Empfehlungen")


# ------------------------------------------------------------
# KDL: DG060201 - Schellong Test
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class SchellongTest(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code für den Schellong Test")
    loinc_code: str = Field(description="LOINC-Code für den Schellong Test")
    patient_id: str = Field(description="Patienten-ID")
    report_date: datetime = Field(description="Berichtsdatum")
    performer: dict = Field(description="Durchführender Arzt/Arzthelfer")
    result: dict = Field(description="Ergebnis des Schellong Tests")


# ------------------------------------------------------------
# KDL: DG060202 - nisse, wie gut der Körper eine festgelegte Menge Zucker verarbeiten kann. H2 Atemtest
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class R_verarbeiten_kann_H2_Atemtest(KdlDocumentBase):
    report_id: str = Field(description="Berichts-ID")
    patient_id: str = Field(description="Patient-ID")
    test_date: datetime = Field(description="Durchführungstermin des Tests")
    glucose_level: float = Field(description="Glukosekonzentration im Blut vor dem Test (mg/dL)")
    breath_samples: list[breath_sample] = Field(description="Atemproben")


class breath_sample(BaseModel):
    sample_time: datetime = Field(description="Entnahmezeitpunkt der Probe")
    carbon_dioxide_level: float = Field(description="Kohlendioxidkonzentration in der Probe (ppm)")


# ------------------------------------------------------------
# KDL: DG060203 - Allergietest
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Allergietest(KdlDocumentBase):
    kdl_code: str = Field(description="KDL Code für das medizinische Dokument")
    loinc_code: str = Field(description="LOINC Code für den Allergietest")
    patient_id: str = Field(description="Patientenkennung")
    test_date: datetime = Field(description="Datum des Allergietests")
    allergens: list[str] = Field(description="Getestete Allergene")
    results: list[dict] = Field(description="Ergebnisse des Allergietests")

    class Config:
        extra = "forbid"


# ------------------------------------------------------------
# KDL: DG060204 - Zahlenverbindungstest
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Zahlenverbindungstest(KdlDocumentBase):
    report_id: str = Field(description="Berichts-ID")
    patient_id: str = Field(description="Patient-ID")
    test_date: datetime = Field(description="Durchführungstermin des Tests")
    result: float = Field(description="Ergebnis des Tests")
    reference_range: str = Field(description="Referenzbereich für das Testergebnis")
    units: str = Field(description="Einheit des Testergebnisses")


# ------------------------------------------------------------
# KDL: DG060205 - BESCHREIBUNG DER DOKUMENTENKLASSEN 6-MinutenGehtest
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class BESCHREIBUNGDERDOKUMENTENKLASSEN6MinutenGehtest(KdlDocumentBase):
    dokument_kategorie: str = Field(description="Kategorie des Dokuments")
    dokument_typ: str = Field(description="Typ des Dokuments")
    patient_id: str = Field(description="Patient-ID")
    patient_geburtsdatum: str = Field(description="Geburtstag des Patienten")
    durchgefuehrte_untersuchung: str = Field(description="Durchgeführte Untersuchung")
    loinc_code: str = Field(description="LOINC-Code für die untersuchte Größe")
    einheit: str = Field(description="Einheit der untersuchten Größe")
    ergebnis_wert: float = Field(description="Ergebniswert der untersuchten Größe")
    referenzbereich: str = Field(description="Referenzbereich für den Ergebniswert")
    interpretationskommentar: str = Field(description="Interpretationskommentar zum Ergebniswert")


# ------------------------------------------------------------
# KDL: DG060299 - elektronischen Schriftverkehr, der nicht in einer spezifischeren KDL dieser Unterklasse abgebildet werden kann. Sonstiger Funktionstest
# Standard: Fachgesellschafts-Leitlinien (AWMF), ISiK DiagnosticReport Profil, LOINC-Kodierung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class RdenKannSonstigerFunktionstest(KdlDocumentBase):
    dokument_typ: str = Field(description="Typ des Dokuments")
    erstellungsdatum: datetime = Field(description="Erstellungsdatum des Dokuments")
    autor: str = Field(description="Autor des Dokuments")
    betroffener_patient: Patient = Field(description="Betroffener Patient")
    inhalt: str = Field(description="Inhalt des Dokuments")


# ------------------------------------------------------------
# KDL: ED010199 - ben, die nicht in einer spezifischeren KDL dieser Unterklasse abgebildet werden können. Sonstige Audiodokumentation
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Nen_SonstigeAudiodokumentation(KdlDocumentBase):
    dokumenttyp: str = Field(description="Typ des Dokuments")
    dok_id: str = Field(description="Identifikationsnummer des Dokuments")
    dok_erstellungszeitpunkt: datetime.datetime = Field(
        description="Zeitpunkt der Erstellung des Dokuments"
    )
    dok_ersteller: str = Field(description="Ersteller des Dokuments")
    dok_inhalt: str = Field(description="Inhalt des Dokuments")


# ------------------------------------------------------------
# KDL: ED020101 - digitale direkte Fotodokumentation – Schwerpunkt: Diagnostik Fotodokumentation Operation
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class StikFotodokumentationOperation(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    study_instance_uid: str = Field(description="Study Instance UID")
    series_instance_uid: str = Field(description="Series Instance UID")
    sop_instance_uid: str = Field(description="SOP Instance UID")
    modality: str = Field(description="Modality")
    photodocumentation_type: str = Field(description="Photodocumentation Type")
    photodocumentation_date_time: datetime = Field(description="Photodocumentation Date Time")
    photographer: str = Field(description="Photographer")
    image_quality: str = Field(description="Image Quality", enum=["100", "200", "300"])
    dicom_compliance: bool = Field(description="DICOM Compliance")
    isik_imaging_study_profile: bool = Field(description="ISiK Imaging Study Profile")


# ------------------------------------------------------------
# KDL: ED020102 - spezifischeren KDL dieser Unterklasse abgebildet werden kann. Bsp.: Anforderung Fotolabor, Dermatologische Fotografie Fotodokumentation Dermatologie
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class EFotodokumentationDermatologie(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code für die spezifische Unterklasse")
    bild_qualitaet: str = Field(description="Bildqualität nach DIN 6868")
    dicom_standard: str = Field(description="DICOM-Standard für medizinische Bildgebung")
    isik_profil: str = Field(description="ISiK ImagingStudy Profil")


# ------------------------------------------------------------
# KDL: ED020103 - digitale direkte Fotodokumentation – Schwerpunkt: Dermatologie Fotodokumentation Diagnostik
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class GieFotodokumentationDiagnostik(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    image_data: bytes = Field(description="Bilddaten im DICOM-Format")
    image_quality: str = Field(description="Bildqualität nach DIN 6868")
    diagnosis: str = Field(description="Diagnose")
    imaging_study_profile: str = Field(description="ISiK ImagingStudy Profil")


# ------------------------------------------------------------
# KDL: ED020104 - Wahlleistungsvertrag, Heimvertrag Videodokumentation Operation
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_type: str = Field(description="Art des medizinischen Dokuments")


class RagVideodokumentationOperation(KdlDocumentBase):
    kdl_code: str = "ED020104"
    document_type: str = "Wahlleistungsvertrag, Heimvertrag Videodokumentation Operation"
    patient_id: str = Field(description="Patienten-ID")
    operation_date: datetime = Field(description="Datum der Operation")
    surgeon: str = Field(description="Name des Operateurs")
    video_quality: VideoQuality = Field(description="Bildqualität des Videos nach DIN 6868")
    dicom_study_instance_uid: str = Field(description="DICOM-Studieninstanz-UUID")
    isik_imaging_study_profile: bool = Field(description="ISiK ImagingStudy Profil")


class VideoQuality(BaseModel):
    resolution: tuple[int, int] = Field(description="Auflösung des Videos in Pixel (Breite x Höhe)")
    frame_rate: float = Field(description="Bildwiederholrate des Videos in Bildern pro Sekunde")
    bit_depth: int = Field(description="Bit-Tiefe des Videos in Bit")


# ------------------------------------------------------------
# KDL: ED020199 - Foto-/Videodokumentation Sonstige
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class FotoVideodokumentationSonstige(KdlDocumentBase):
    kdl_code: str = "ED020199"
    document_type: str = "Foto-/Videodokumentation Sonstige"

    image_quality: str = Field(description="Bildqualität nach DIN 6868")
    dicom_compliance: bool = Field(description="DICOM-Standard für medizinische Bildgebung")
    isik_profile: bool = Field(description="ISiK ImagingStudy Profil")


# ------------------------------------------------------------
# KDL: ED110101 - bildgebende Diagnostik, Funktionstest, Ärztlicher Befundbericht Behandlungspfad
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Bildqualitaet(BaseModel):
    bildqualitaetsparameter: str = Field(description="Bildqualitätsparameter nach DIN 6868")
    bildqualitaetsbewertung: str = Field(description="Bewertung der Bildqualität")


class FunktionstestErgebnis(BaseModel):
    testname: str = Field(description="Name des Funktionstests")
    ergebnis: str = Field(description="Ergebnis des Funktionstests")


class BehandlungspfadSchritt(BaseModel):
    schrittbeschreibung: str = Field(description="Beschreibung des Schritts im Behandlungspfad")
    durchgefuehrt_am: datetime = Field(
        description="Datum und Uhrzeit, an dem der Schritt durchgeführt wurde"
    )


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code für das medizinische Dokument")
    erstellungsdatum: datetime = Field(description="Erstellungsdatum des medizinischen Dokuments")


class ErBefundberichtBehandlungspfad(KdlDocumentBase):
    bildqualitaet: Bildqualitaet = Field(description="Bildqualitätsparameter und Bewertung")
    funktionstests: list[FunktionstestErgebnis] = Field(description="Ergebnisse der Funktionstests")
    befund: str = Field(description="Ärztlicher Befundbericht")
    behandlungspfad: list[BehandlungspfadSchritt] = Field(description="Schritte im Behandlungspfad")


# ------------------------------------------------------------
# KDL: ED110102 - sungsschein Notfalldatenmanagement (NFDM)
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class SungsscheinNotfalldatenmanagement(KdlDocumentBase):
    kdl_code: str = Field(default="ED110102", const=True)
    patient_id: UUID
    birth_date: date
    first_name: str
    last_name: str
    address: str
    city: str
    postal_code: int
    phone_number: str
    emergency_contact_person: str
    emergency_contact_phone: str
    allergies: list[str]
    medications: list[str]
    illnesses: list[str]
    medical_conditions: list[str]
    blood_type: str
    rh_factor: str
    organ_donation_consent: bool
    image_studies: list[imaging_study] = Field(default_factory=list)


class imaging_study(BaseModel):
    study_id: UUID
    modality: str
    series: list[imaging_series] = Field(default_factory=list)


class imaging_series(BaseModel):
    series_id: UUID
    images: list[UUID]


# ------------------------------------------------------------
# KDL: ED110103 - (eMP) = bundeseinheitlicher Medikationsplan Medikationsplan elektronisch (eMP)
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class EMP(KdlDocumentBase):
    kdl_code: str = Field(description="KDL Code")
    title: str = Field(description="Titel des Dokuments")
    author: str = Field(description="Autor des Dokuments")
    creation_time: datetime = Field(description="Erstellungszeitpunkt des Dokuments")
    content: list[Union[str, "eMPTableRow"]] = Field(description="Inhalt des Dokuments")


class eMPTableRow(BaseModel):
    column1: str = Field(description="Spalte 1")
    column2: str = Field(description="Spalte 2")
    column3: str = Field(description="Spalte 3")


# ------------------------------------------------------------
# KDL: ED110104 - bescheinigung (papierbasiert) eArztbrief (bvitg)
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class BescheinigungPapierbasiertEArztbriefBvitg(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")
    medical_practice_id: str = Field(description="Medizinische Praxis ID")
    issuing_medical_practice_id: str = Field(description="Ausstellende medizinische Praxis ID")
    issue_date: str = Field(description="Ausstellungsdatum")
    diagnosis: list[str] = Field(description="Diagnosen")
    medication: list[str] = Field(description="Medikation")
    lab_results: list[Dict[str, Any]] = Field(description="Laborergebnisse")


# ------------------------------------------------------------
# KDL: ED110105 - gebnisse sowie die visuelle Darstellung der Aufzeichnung und Messung der elektrischen Ströme des Gehirns. eImpfpass
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ChenStrömedesGehirns_eImpfpass(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    birth_date: str = Field(description="Birth date of the patient")
    measurement_date: str = Field(description="Date of measurement")
    measurement_time: str = Field(description="Time of measurement")
    device_identifier: str = Field(description="Identifier of the device used for measurement")
    measurement_values: list[float] = Field(description="Measurement values of electrical currents")
    image_data: bytes = Field(description="Image data in DICOM format")


# ------------------------------------------------------------
# KDL: ED110106 - eZahnärztliches Bonusheft
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_id: str = Field(description="ID des Dokuments")


class EZahnärztlichesBonusheft(KdlDocumentBase):
    kdl_code: str = "ED110106"
    document_id: str
    patient_id: str = Field(description="Patienten-ID")
    dentist_id: str = Field(description="Zahnarzt-ID")
    creation_date: datetime = Field(description="Erstellungsdatum des Bonushefts")
    bonus_points: int = Field(description="Gesammelte Bonuspunkte")


# ------------------------------------------------------------
# KDL: ED110107 - eArbeitsunfähigkeitsbescheini-gung
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class EArbeitsunfähigkeitsbescheinigung(KdlDocumentBase):
    kdl_code: str = "ED110107"
    document_type: str = "eArbeitsunfähigkeitsbescheinigung"

    patient_id: str = Field(description="Patienten-ID")
    issue_date: datetime = Field(description="Ausstellungsdatum")
    doctor_id: str = Field(description="ID des ausstellenden Arztes")
    duration_of_illness: int = Field(description="Dauer der Arbeitsunfähigkeit in Tagen")
    reason_for_illness: str = Field(description="Grund für die Arbeitsunfähigkeit")

    class Config:
        orm_mode = True


# ------------------------------------------------------------
# KDL: ED110108 - eRezept
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ERezept(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code für das eRezept")
    arzt_id: str = Field(description="ID des ausstellenden Arztes")
    patient_id: str = Field(description="ID des Patienten")
    rezept_datum: datetime = Field(description="Datum des eRezepts")
    valid_from: datetime = Field(description="Gültig ab diesem Datum")
    valid_until: datetime = Field(description="Gültig bis zu diesem Datum")
    medication: list[Medication] = Field(
        default_factory=list, description="Liste der verordneten Medikamente"
    )


class Medication(BaseModel):
    name: str = Field(description="Name des Medikaments")
    dose: float = Field(description="Verordnete Dosis")
    unit: str = Field(description="Einheit der Dosis")


# ------------------------------------------------------------
# KDL: ED110109 - ben zur Vorbereitung einer Entlassung nach stationärem Aufenthalt. ePflegebericht
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class NäremAufenthalt_ePflegebericht(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    discharge_date: str = Field(description="Entlassungsdatum")
    care_unit: str = Field(description="Station/Abteilung, auf der der Patient behandelt wurde")
    medical_condition: str = Field(description="Hauptdiagnose")
    medication: list[str] = Field(description="Verordnete Medikamente")
    allergies: list[str] = Field(description="Allergien des Patienten")
    laboratory_results: list[Dict[str, Any]] = Field(description="Laborbefunde")
    imaging_studies: list["ImagingStudy"] = Field(description="Bildgebende Untersuchungen")


class ImagingStudy(BaseModel):
    study_id: str = Field(description="Studien-ID")
    modality: str = Field(description="Modus der Bildgebung (z.B. CT, MR)")
    body_part_examined: str = Field(description="Untersuchter Körperteil")
    series: list["Series"] = Field(description="Reihen von Bildern")


class Series(BaseModel):
    series_id: str = Field(description="Reihe-ID")
    images: list[Dict[str, Any]] = Field(description="Bilder in der Reihe")


# ------------------------------------------------------------
# KDL: ED110199 - Sonstige Dokumentation
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class SonstigeDokumentation(KdlDocumentBase):
    dokumentart: str = Field(description="Art des Dokuments")
    dok_id: str = Field(description="Identifikator des Dokuments")
    erstellungszeitpunkt: datetime.datetime = Field(
        description="Zeitpunkt der Erstellung des Dokuments"
    )
    autor: str = Field(description="Autor des Dokuments")
    beschreibung: str | None = Field(description="Beschreibung des Dokuments", default=None)
    bilddaten: list[Dict[str, Any]] = Field(
        description="Liste von Bilddaten im DICOM-Format", default=[]
    )


# ------------------------------------------------------------
# KDL: ED190101 - Informationsaustausch per E-Mail – direkt elektronisch oder ausgedruckt in Papierkrankenakte. Schwerpunkt: Arztauskunft ohne Befundergeb
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class NktArztauskunftohneBefundergeb(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    sender: str = Field(description="Sender des Informationsaustauschs")
    recipient: str = Field(description="Empfänger des Informationsaustauschs")
    subject: str = Field(description="Betreff des Informationsaustauschs")
    body: str = Field(description="Inhalt des Informationsaustauschs")
    image_study: dict = Field(
        description="Bildstudie nach DICOM-Standard und ISiK ImagingStudy Profil", default={}
    )


# ------------------------------------------------------------
# KDL: ED190102 - direkt elektronisch oder ausgedruckt in Papierkrankenakte. Schwerpunkt: Befundergeb
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Kenakte_SchwerpunktBefundergeb(KdlDocumentBase):
    bildqualitaet: str = Field(description="DIN 6868 Bildqualität")
    dicom_standard: str = Field(description="DICOM-Standard für med. Bildgebung")
    isik_profil: str = Field(description="ISiK ImagingStudy Profil")


# ------------------------------------------------------------
# KDL: ED190103 - EKG E-Mail Arztauskunft
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_id: str = Field(description="Dokument-ID")


class EKGEMailArztauskunft(KdlDocumentBase):
    kdl_code: str = "ED190103"
    document_id: str = Field(description="ID der EKG E-Mail Arztauskunft")
    patient_id: str = Field(description="Patient-ID")
    report_text: str = Field(description="Berichtstext zur EKG E-Mail Arztauskunft")
    images: list[Dict[str, Any]] = Field(
        description="Bilddaten im DICOM-Format entsprechend dem ISiK ImagingStudy Profil und DIN 6868 Bildqualität"
    )


# ------------------------------------------------------------
# KDL: ED190104 - Informationsaustausch per E-Mail – direkt elektronisch oder ausgedruckt in Papierkrankenakte. Schwerpunkt: Juristische Beweissicherung
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class UnktJuristischeBeweissicherung(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    sender: str = Field(description="Sender des Informationsaustauschs")
    recipient: str = Field(description="Empfänger des Informationsaustauschs")
    message_body: str = Field(description="Haupttext des E-Mails oder des ausgedruckten Dokuments")
    attachments: list[str] = Field(
        default=[], description="Anlagen im E-Mail oder ausgedruckte Dokumente"
    )
    timestamp: datetime = Field(description="Zeitstempel des Informationsaustauschs")


# ------------------------------------------------------------
# KDL: ED190105 - Informationsaustausch per Fax – direkt elektronisch oder ausgedruckt in Papierkrankenakte. Schwerpunkt: Arztauskunft ohne Befundergeb
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        allow_population_by_field_name = True


class NktArztauskunftohneBefundergeb(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    sender_facility_id: str = Field(description="Sender Facility ID")
    recipient_facility_id: str = Field(description="Recipient Facility ID")
    transmission_date_time: datetime = Field(description="Transmission Date Time")
    image_study: list[ImageStudy] = Field(description="List of Image Studies")


class ImageStudy(BaseModel):
    study_instance_uid: str = Field(description="Study Instance UID")
    series_instance_uid: str = Field(description="Series Instance UID")
    modality: str = Field(description="Modality")
    number_of_images: int = Field(description="Number of Images")
    image_quality: str = Field(description="Image Quality", enum=["DIN6868"])


# ------------------------------------------------------------
# KDL: ED190106 - Informationsaustausch per Fax – direkt elektronisch oder ausgedruckt in Papierkrankenakte. Inhaltlicher Schwerpunkt: Befundergeb
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class LtlicherSchwerpunktBefundergeb(KdlDocumentBase):
    bildqualitaet: str = Field(description="DIN 6868 Bildqualität")
    dicom_standard: str = Field(description="DICOM-Standard für med. Bildgebung")
    isik_profil: str = Field(description="ISiK ImagingStudy Profil")


# ------------------------------------------------------------
# KDL: ED190107 - Fax Arztauskunft
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class FaxArztauskunft(KdlDocumentBase):
    ausstellender_arzt: str = Field(description="Name des ausstellenden Arztes")
    patient_name: str = Field(description="Name des Patienten")
    patient_birth_date: str = Field(description="Geburtsdatum des Patienten")
    patient_id: str = Field(description="Patientenkennung")
    ausstellungsdatum: str = Field(description="Datum der Ausstellung")
    fax_nummer: str = Field(description="Fax-Nummer")
    bild_qualitaet: str = Field(description="Bildqualität nach DIN 6868")
    dicom_studien_id: str = Field(description="DICOM Studien-ID")
    isik_imaging_study_profil: bool = Field(description="ISiK ImagingStudy Profil")


# ------------------------------------------------------------
# KDL: ED190108 - Informationsaustausch per Fax – direkt elektronisch oder ausgedruckt in Papierkrankenakte. Schwerpunkt: Juristische Beweissicherung Fax Sonstige
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ScheBeweissicherungFaxSonstige(KdlDocumentBase):
    fax_id: str = Field(description="ID des Faxes")
    sender: str = Field(description="Absender des Faxes")
    receiver: str = Field(description="Empfänger des Faxes")
    send_time: datetime = Field(description="Zeitpunkt des Versands")
    image_quality: str = Field(description="Bildqualität nach DIN 6868")
    dicom_study_instance_uid: UUID = Field(description="DICOM-Standard für medizinische Bildgebung")
    isik_profile: bool = Field(description="ISiK ImagingStudy Profil")


# ------------------------------------------------------------
# KDL: ED190199 - version, Inhalationsplan Sonstiger elektronischer Schriftverkehr
# Standard: DIN 6868 Bildqualität, DICOM-Standard für med. Bildgebung, ISiK ImagingStudy Profil
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    version: str = Field(description="Dokumentversion")
    inhalePlan: dict = Field(description="Inhalationsplan")
    otherCommunication: list = Field(description="Sonstiger elektronischer Schriftverkehr")


class VersionInhaleOtherElectronic(BaseModel):
    class Config:
        title = "Version Inhale Other Electronic"

    version: str = Field(description="Dokumentversion nach DIN 6868")
    inhalePlan: dict = Field(description="Inhalationsplan nach ISiK ImagingStudy Profil")
    otherCommunication: list = Field(
        description="Sonstiger elektronischer Schriftverkehr nach DICOM-Standard für med. Bildgebung"
    )


class VersionInhaleOtherElectronic(KdlDocumentBase):
    pass


# ------------------------------------------------------------
# KDL: LB020101 - Blutgasanalyse
# Standard: ISiK Laborbefund Profil, LOINC-Kodierung, Referenzbereiche nach RiliBÄK
# ------------------------------------------------------------

from pydantic import BaseModel


class KdlDocumentBase(BaseModel):
    kdl_code: str
    document_type: str


class Blutgasanalyse(KdlDocumentBase):
    kdl_code = "LB020101"
    document_type = "Laborbefund"

    class Laborwert(BaseModel):
        loinc_code: str
        name: str
        unit: str
        value: float
        reference_range: str

    class Tabelle(BaseModel):
        header: list[str]
        rows: list[list[str]]

    laborwerte: list[Laborwert]
    tabelle: Tabelle | None = None


# ------------------------------------------------------------
# KDL: LB020102 - ben zur Blutgruppe und zum Rhesusfaktor. Blutkulturenbefund
# Standard: ISiK Laborbefund Profil, LOINC-Kodierung, Referenzbereiche nach RiliBÄK
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code")


class Blutkulturenbefund(KdlDocumentBase):
    blutgruppe: str = Field(description="Blutgruppe")
    rhesusfaktor: bool = Field(description="Rhesusfaktor")
    laborwerte: list[dict] = Field(default_factory=list, description="Laborwerte")
    referenzbereiche: dict = Field(description="Referenzbereiche nach RiliBÄK")

    class Config:
        orm_mode = True


# ------------------------------------------------------------
# KDL: LB020103 - ben zum Vertrag zwischen einer Einrichtung und einem Bewohner. Herstellungsund Prüfprotokoll von Blut und Blutprodukten
# Standard: ISiK Laborbefund Profil, LOINC-Kodierung, Referenzbereiche nach RiliBÄK
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class OtokollvonBlutundBlutprodukten(KdlDocumentBase):
    einrichtung: str = Field(description="Name der Einrichtung")
    Bewohner: str = Field(description="Name des Bewohners")
    herstellungsdatum: datetime = Field(description="Datum der Herstellung")
    pruefdatum: datetime = Field(description="Datum der Prüfung")
    laborbefunde: list[Laborbefund] = Field(default_factory=list, description="Laborbefunde")


class Laborbefund(BaseModel):
    loinc_code: str = Field(description="LOINC-Code des Laborparameters")
    bezeichnung: str = Field(description="Bezeichnung des Laborparameters")
    wert: float = Field(description="Messwert des Laborparameters")
    referenzbereich: str = Field(description="Referenzbereich nach RiliBÄK")


# ------------------------------------------------------------
# KDL: LB020104 - Nachweis über das Versenden eines Fax. Serologischer Befund
# Standard: ISiK Laborbefund Profil, LOINC-Kodierung, Referenzbereiche nach RiliBÄK
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class DeneinesFaxSerologischerBefund(KdlDocumentBase):
    loinc_code: str = Field(description="LOINC-Kodierung")
    result_status: str = Field(description="Ergebnisstatus")
    specimen_type: str = Field(description="Art der Probe")
    collection_date_time: datetime = Field(description="Entnahmezeitpunkt")
    result_date_time: datetime = Field(description="Ergebnisdatum")
    reference_range: dict = Field(description="Referenzbereiche nach RiliB├ĄK")


# ------------------------------------------------------------
# KDL: LB020199 - Sonstige Dokumentation Blut
# Standard: ISiK Laborbefund Profil, LOINC-Kodierung, Referenzbereiche nach RiliBÄK
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class SonstigeDokumentationBlut(KdlDocumentBase):
    kdl_code: str = "LB020199"
    loinc_codes: list[str] = Field(description="LOINC-Kodierung der Laborparameter")
    lab_results: list[LabResult] = Field(description="Laborbefunde")


class LabResult(BaseModel):
    parameter_name: str = Field(description="Name des Laborparameters")
    value: float = Field(description="Messwert des Parameters")
    reference_range: str = Field(description="Referenzbereich nach RiliBÄK")


# ------------------------------------------------------------
# KDL: LB120101 - ben zur Einschätzung einer Bewusstseinsund Hirnfunktionsstörung bei Erwachsenen nach Schädel-HirnTrauma. Glukosetoleranztestprotokoll
# Standard: ISiK Laborbefund Profil, LOINC-Kodierung, Referenzbereiche nach RiliBÄK
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class GlukoseWert(BaseModel):
    zeitpunkt: str = Field(description="Zeitpunkt der Messung")
    wert: float = Field(description="Glukosewert in mg/dl")


class Glukosetoleranztestprotokoll(KdlDocumentBase):
    patient_id: int = Field(description="Patienten-Identifikationsnummer")
    loinc_code: str = Field(description="LOINC-Kodierung für das medizinische Dokument")
    glukosewerte: list[GlukoseWert] = Field(description="Tabelle mit Glukosewerten")

    class Config:
        schema_extra = {
            "example": {
                "patient_id": 12345,
                "loinc_code": "LB120101",
                "glukosewerte": [
                    {"zeitpunkt": "08:00", "wert": 95.0},
                    {"zeitpunkt": "08:30", "wert": 105.0},
                ],
            }
        }


# ------------------------------------------------------------
# KDL: LB120102 - UNKNOWN
# Standard: ISiK Laborbefund Profil, LOINC-Kodierung, Referenzbereiche nach RiliBÄK
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class UNKNOWN(KdlDocumentBase):
    lb120102: str
    loinc_code: str
    result_value: float
    reference_range: str


# ------------------------------------------------------------
# KDL: LB120103 - Befundbogen
# Standard: ISiK Laborbefund Profil, LOINC-Kodierung, Referenzbereiche nach RiliBÄK
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Befundbogen(KdlDocumentBase):
    dokument_id: str = Field(description="ID des Dokuments")
    patient_id: str = Field(description="Patient-ID")
    befundzeitpunkt: datetime = Field(description="Zeitpunkt des Befundes")
    laborbefunde: list[Laborbefund] = Field(description="Laborbefunde")


class Laborbefund(BaseModel):
    loinc_code: str = Field(description="LOINC-Code für den Laborparameter")
    wert: float = Field(description="Messwert")
    referenzbereich: str = Field(description="Referenzbereich nach RiliBÄK")


# ------------------------------------------------------------
# KDL: LB120104 - Anforderung bzw. Anmeldung einer therapeutischen Behandlung. Anforderung Labor
# Standard: ISiK Laborbefund Profil, LOINC-Kodierung, Referenzbereiche nach RiliBÄK
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class AnforderungLabor(KdlDocumentBase):
    loinc_code: str = Field(description="LOINC-Kodierung")
    referenzbereich: str = Field(description="Referenzbereiche nach RiliBÄK")
    laborbefund_profil: str = Field(description="ISiK Laborbefund Profil")


class Laborwert(BaseModel):
    wert: float
    einheit: str


class AnforderungbzwAnmeldungeinertherapeutischenBehandlungAnforderungLabor(AnforderungLabor):
    laborwerte: list[Laborwert] = Field(default_factory=list)


# ------------------------------------------------------------
# KDL: LB120105 - Überweisungsschein Labor
# Standard: ISiK Laborbefund Profil, LOINC-Kodierung, Referenzbereiche nach RiliBÄK
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class UeberweisungsscheinLabor(KdlDocumentBase):
    kdl_code: str = "LB120105"
    patient_id: str = Field(description="Patienten-ID")
    doctor_id: str = Field(description="Arzt-ID")
    lab_values: list[LabValue] = Field(default_factory=list, description="Laborwerte")


class LabValue(BaseModel):
    loinc_code: str = Field(description="LOINC-Code des Laborwerts")
    value: float = Field(description="Messwert")
    reference_range: str = Field(description="Referenzbereich nach RiliBÄK")


# ------------------------------------------------------------
# KDL: LB120199 - dokumentation, PICCO Protokoll. Sonstiger Laborbefund
# Standard: ISiK Laborbefund Profil, LOINC-Kodierung, Referenzbereiche nach RiliBÄK
# ------------------------------------------------------------

from pydantic import BaseModel


class KdlDocumentBase(BaseModel):
    kdl_code: str


class SonstigerLaborbefund(KdlDocumentBase):
    loinc_code: str
    wert: float
    referenzbereich_min: float
    referenzbereich_max: float
    einheit: str
    bemerkungen: str = ""


# ------------------------------------------------------------
# KDL: LB130101 - nisse der Messung des Augeninnendrucks (Tonometrie) mittels Applationstonometer. Mikrobiologiebefund
# Standard: ISiK Laborbefund Profil, LOINC-Kodierung, Referenzbereiche nach RiliBÄK
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class STonometrieMikrobiologiebefund(KdlDocumentBase):
    loinc_code: str = Field(description="LOINC-Code für den Laborbefund")
    patient_id: str = Field(description="Patientenkennung")
    measurement_date: datetime = Field(description="Datum der Messung")
    tonometry_result: float = Field(description="Ergebnis der Tonometrie in mmHg")
    reference_range: str = Field(description="Referenzbereich nach RiliBÄK")

    class Config:
        schema_extra = {
            "example": {
                "loinc_code": "LB130101",
                "patient_id": "1234567890",
                "measurement_date": "2022-01-01T00:00:00Z",
                "tonometry_result": 15.5,
                "reference_range": "10-21 mmHg",
            }
        }


# ------------------------------------------------------------
# KDL: LB130102 - anforderung, Zytologieanforderung, Molekularpathologieanforderung Urinbefund
# Standard: ISiK Laborbefund Profil, LOINC-Kodierung, Referenzbereiche nach RiliBÄK
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class UrinbefundLaborwerte(BaseModel):
    parameter: str = Field(description="LOINC-Kodierung")
    einheit: str = Field(description="Einheit des Parameters")
    referenzbereich: str = Field(description="Referenzbereich nach RiliBÄK")
    wert: float = Field(description="Messwert")


class MolekularpathologieanforderungUrinbefund(KdlDocumentBase):
    kdl_code: str = Field(default="LB130102", const=True)
    laborwerte: list[UrinbefundLaborwerte] = Field(description="Tabelle mit Laborwerten")


# ------------------------------------------------------------
# KDL: LB220102 - tale direkte Videodokumentation – Schwerpunkt: Operation Virologiebefund
# Standard: ISiK Laborbefund Profil, LOINC-Kodierung, Referenzbereiche nach RiliBÄK
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class RpunktOperationVirologiebefund(KdlDocumentBase):
    dokumenttyp: str = Field(description="Typ des Dokuments")
    patient_id: str = Field(description="Patient-ID")
    loinc_code: str = Field(description="LOINC-Code für Virologiebefund")
    referenzbereich: dict = Field(description="Referenzbereich nach RiliBÄK")

    laborwerte: list[dict] = Field(
        default=[], description="Laborwerte mit LOINC-Kodierung und Referenzbereichen"
    )

    class Config:
        extra = "forbid"


# ------------------------------------------------------------
# KDL: OP010101 - geplanter Eingriff, Vitaldaten, Präoperative Visite Anästhesieprotokoll intraoperativ
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class Sthesieprotokollintraoperativ(KdlDocumentBase):
    einweisender_arzt: str = Field(description="Einweisender Arzt")
    geplanter_eingriff: dict = Field(description="Geplanter Eingriff")
    vitaldaten: list[dict] = Field(description="Vitaldaten")
    präoperative_visite: dict = Field(description="Präoperative Visite")
    anästhesieprotokoll_intraoperativ: dict = Field(description="Anästhesieprotokoll intraoperativ")


# ------------------------------------------------------------
# KDL: OP010102 - Aufwachraumprotokoll
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class Aufwachraumprotokoll(KdlDocumentBase):
    patient_id: int = Field(description="Patient ID")
    operation_date: str = Field(description="Operation Date")
    surgeon: str = Field(description="Surgeon")
    anasthetist: str = Field(description="Anesthetist")
    operation_time_start: str = Field(description="Operation Time Start")
    operation_time_end: str = Field(description="Operation Time End")
    awaking_room_arrival_time: str = Field(description="Awaking Room Arrival Time")
    awaking_room_departure_time: str = Field(description="Awaking Room Departure Time")
    pain_level_admission: int = Field(description="Pain Level at Admission")
    pain_level_discharge: int = Field(description="Pain Level at Discharge")


# ------------------------------------------------------------
# KDL: OP010103 - Checkliste Anästhesie
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class ChecklisteAnästhesie(KdlDocumentBase):
    anamnese: dict = Field(description="Anamnese")
    laborwerte: list[dict] = Field(description="Laborwerte", default=[])
    operation: dict = Field(description="Operation")
    postoperativ: dict = Field(description="Postoperativer Verlauf")


# ------------------------------------------------------------
# KDL: OP010199 - tungen (GOÄ), Einzahlungsquittung, Individual-Checkliste, Liquidation, Zahlungsaufforderung, Checkliste Abrechnung, Entlassungsschein Sonstige Anästhesiedokumentation
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class TongueDocument(KdlDocumentBase):
    tongue_goae: bool = Field(description="Tongue GOÄ")
    payment_receipt: bool = Field(description="Einzahlungsquittung")
    individual_checklist: bool = Field(description="Individual-Checkliste")
    liquidation: bool = Field(description="Liquidation")
    payment_request: bool = Field(description="Zahlungsaufforderung")
    billing_checklist: bool = Field(description="Checkliste Abrechnung")
    discharge_certificate_other_anesthesia: bool = Field(
        description="Entlassungsschein Sonstige Anästhesiedokumentation"
    )


# ------------------------------------------------------------
# KDL: OP150101 - Diagnosen und Leistungen während eines Krankenhausaufenthaltes, welche die Grundlage zur Abrechnung beim jeweiligen Kostenträger bilden. Chargendokumentation
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class GerbildenChargendokumentation(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code für das medizinische Dokument")
    diagnose: str = Field(description="Diagnose des Patienten")
    leistung: str = Field(description="Leistung während des Krankenhausaufenthaltes")
    abrechnung_kostentraeger: str = Field(description="Kostenträger für die Abrechnung")


# ------------------------------------------------------------
# KDL: OP150102 - OP-Anmeldungsbogen
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class OPAnmeldungsbogen(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    birth_date: date = Field(description="Geburtsdatum des Patienten")
    sex: Literal["male", "female"] = Field(description="Geschlecht des Patienten")
    surgeon: str = Field(description="Name des Operateurs")
    operation_date: date = Field(description="Datum der Operation")
    operation_type: str = Field(description="Art der Operation")
    anesthesia_type: str = Field(description="Art der Narkose")
    pre_operation_diagnosis: list[str] = Field(description="Voroperative Diagnosen")
    intra_operation_findings: list[str] = Field(description="Intraoperative Befunde")
    post_operation_diagnosis: list[str] = Field(description="Postoperative Diagnosen")


# ------------------------------------------------------------
# KDL: OP150103 - ben zur Anmeldung eines Patienten für einen operativen Eingriff. OP-Bericht
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code des Dokuments")


class NenoperativenEingriffOPBericht(KdlDocumentBase):
    anlass_operation: str = Field(description="Anlass der Operation")
    operativer_eingriff: str = Field(description="Operativer Eingriff")
    einweisender_arzt: str = Field(description="Einweisender Arzt")
    durchführende_ärzte: list[str] = Field(description="Durchführende Ärzte")
    anästhesieart: str = Field(description="Art der Anästhesie")
    komplikationen: list[str] = Field(description="Komplikationen während des Eingriffs")
    laborwerte: list[dict[str, str]] = Field(description="Laborwerte vor und nach dem Eingriff")


# ------------------------------------------------------------
# KDL: OP150104 - Zusammenfassung des Operationsverlaufes durch einen Arzt. OP-Bilddokumentation
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class OPBilddokumentation(KdlDocumentBase):
    operation_beschreibung: str = Field(description="Beschreibung der Operation")
    op_datum: datetime = Field(description="Datum der Operation")
    op_art: str = Field(description="Art der Operation")
    op_komplikationen: list[str] = Field(description="Komplikationen während der Operation")
    op_bilder: list[Dict[str, Any]] = Field(description="Liste von OP-Bilddokumentations-Einträgen")


class OPBilddokumentationEintrag(BaseModel):
    bild_id: UUID = Field(description="ID des Bildes")
    bild_datei: str = Field(description="Dateiname der Bilddatei")
    beschreibung: str | None = Field(description="Beschreibung des Bildes", default=None)


# ------------------------------------------------------------
# KDL: OP150105 - schließlich die bildliche Dokumentation, die während eines operativen Eingriffes entstanden ist. OP-Checkliste
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class IffesentstandenistOPCheckliste(KdlDocumentBase):
    operation_name: str = Field(description="Name der Operation")
    operation_date: datetime = Field(description="Datum der Operation")
    surgeon: str = Field(description="Name des Operateurs")
    anesthesia_type: str = Field(description="Art der Narkose")
    operation_duration: timedelta = Field(description="Dauer der Operation in Minuten")
    complications: list[str] = Field(
        default_factory=list, description="Komplikationen während der Operation"
    )
    check_list_items: list[dict] = Field(
        default_factory=list, description="OP-Checkliste mit allen Punkten"
    )


# ------------------------------------------------------------
# KDL: OP150106 - ben über die Aufklärung der geplanten Operation, inklusive anamnestischer Erhebungen. OP-Protokoll
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class EstischerErhebungenOPProtokoll(KdlDocumentBase):
    aufklärung_erfolgt: bool = Field(description="Aufklärung erfolgte")
    anamnese_erhebung: str = Field(description="Anamneseerhebung")
    operation_protokoll: str = Field(description="Operationprotokoll")


# ------------------------------------------------------------
# KDL: OP150107 - Postoperative Verordnung
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class PostoperativeVerordnung(KdlDocumentBase):
    kdl_code: str = "OP150107"
    operation: str = Field(description="Beschreibung der Operation")
    anamnese: str = Field(description="Anamnese des Patienten")
    laborwerte: list[dict[str, str]] = Field(description="Laborwerte des Patienten")
    medikamente: list[str] = Field(description="Verordnete Medikamente")
    verordnung_ende: datetime = Field(description="Datum und Uhrzeit der Verordnung")


# ------------------------------------------------------------
# KDL: OP150108 - liche Anga
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------


from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class LicheAnga(KdlDocumentBase):
    dokument_id: str = Field(description="Identifikationsnummer des Dokuments")
    patient_id: str = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    sex: str = Field(description="Geschlecht des Patienten")
    diagnosis: list[str] = Field(description="Diagnosen")
    operations: list[str] = Field(description="Durchgeführte Operationen")
    anesthesia_type: str = Field(description="Art der Narkose")
    operation_start_time: str = Field(description="Startzeitpunkt der Operation")
    operation_end_time: str = Field(description="Endzeitpunkt der Operation")
    surgeon: str = Field(description="Operierender Arzt")


# ------------------------------------------------------------
# KDL: OP150109 - Durchführung eines Blutreinigungsverfahrens. Dokumentation ambulantes Operieren
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel


class KdlDocumentBase(BaseModel):
    kdl_code: str


class KumentationambulantesOperieren(KdlDocumentBase):
    kdl_code = "OP150109"
    patient_id: int
    operation_date: date
    operator: str
    assistant: str | None = None
    blood_purification_method: str
    blood_volume_treated: float
    blood_pressure_before: float
    blood_pressure_after: float
    coagulation_time_before: float
    coagulation_time_after: float
    laboratory_findings: list[LaboratoryFinding]
    complications: str | None = None


class LaboratoryFinding(BaseModel):
    test_name: str
    result_value: float
    unit_of_measurement: str
    reference_range: str


# ------------------------------------------------------------
# KDL: OP150199 - Sonstige OPDokumentation
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    document_type: str


class SonstigeOPDokumentation(KdlDocumentBase):
    kdl_code = "OP150199"
    document_type = "Sonstige OPDokumentation"

    anamnese: str = Field(description="Anamnese")
    diagnose: str = Field(description="Diagnose")
    operativer_eingriff: str = Field(description="Operativer Eingriff")
    komplikationen: list[str] = Field(default_factory=list, description="Komplikationen")
    laborwerte: list["Laborwert"] = Field(default_factory=list, description="Laborwerte")


class Laborwert(BaseModel):
    parameter: str = Field(description="Parameter")
    wert: float | int = Field(description="Wert")
    einheit: str = Field(description="Einheit")


# ------------------------------------------------------------
# KDL: OP200101 - anzeige Transplantationsprotokoll
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class AnzeigeTransplantationsprotokoll(KdlDocumentBase):
    transplantations_protokoll_id: int = Field(description="ID des Transplantationsprotokolls")
    patient_id: int = Field(description="ID des Patienten")
    transplantations_datum: str = Field(description="Datum der Transplantation")
    donor_id: int = Field(description="ID des Spenders")
    transplantationsart: str = Field(description="Art der Transplantation")
    transplantiertes_organ: str = Field(description="Transplantiertes Organ")
    komplikationen: list[str] = Field(
        description="Komplikationen während und nach der Transplantation"
    )


# ------------------------------------------------------------
# KDL: OP200102 - graphie Spenderdokument
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class GraphieSpenderdokument(KdlDocumentBase):
    kdl_code: str = "OP200102"
    patient_id: str = Field(description="Patient ID")
    birth_date: str = Field(description="Birth Date")
    sex: str = Field(description="Sex")
    weight: float = Field(description="Weight in kg")
    height: float = Field(description="Height in cm")


# ------------------------------------------------------------
# KDL: OP200199 - aben, die nicht in einer spezifischeren KDL dieser Unterklasse abgebildet werden können. Sonstige Transplantationsdokumentation
# Standard: BQS/IQTIG Qualitätssicherung OP-Dokumentation, G-BA Mindestmengenregelung
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ETransplantationsdokumentation(KdlDocumentBase):
    dokumenttyp: str = Field(description="Typ des Dokuments")
    patient_id: int = Field(description="Patient ID")
    operation_datum: datetime = Field(description="Datum der Operation")
    transplantationsorgan: str = Field(description="Transplantiertes Organ")
    donator_informationen: dict = Field(description="Informationen ├╝ber den Donator")


# ------------------------------------------------------------
# KDL: PT080101 - Histologieanforderung
# Standard: TNM-Klassifikation (UICC), ICD-O-3 Morphologie, pathologische Befundstrukturen
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Histologieanforderung(KdlDocumentBase):
    kdl_code: str = Field(default="PT080101", const=True)
    tnm_klassifikation_uicc: str = Field(description="TNM-Klassifikation (UICC)")
    icd_o_3_morphologie: str = Field(description="ICD-O-3 Morphologie")
    pathologischer_befund: dict = Field(description="Pathologische Befundstrukturen")

    class Config:
        arbitrary_types_allowed = True


# ------------------------------------------------------------
# KDL: PT080102 - anforderung, Molekularpathologieanforderung Histologiebefund
# Standard: TNM-Klassifikation (UICC), ICD-O-3 Morphologie, pathologische Befundstrukturen
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class HistologieBefund(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code für Histologiebefund")
    tnm_klartext: str = Field(description="TNM-Klassifikation (UICC) in Klartext")
    icdo3_morphologie: str = Field(description="ICD-O-3 Morphologie")
    pathologische_befunde: list[dict[str, str]] = Field(
        description="Pathologische Befundstrukturen"
    )


class MolekularpathologieAnforderungHistologiebefund(HistologieBefund):
    pass


# ------------------------------------------------------------
# KDL: PT130101 - Molekularpathologieanforderung
# Standard: TNM-Klassifikation (UICC), ICD-O-3 Morphologie, pathologische Befundstrukturen
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Molekularpathologieanforderung(KdlDocumentBase):
    tnm_klarifikation: str = Field(description="TNM-Klassifikation (UICC)")
    icd_o_morphologie: str = Field(description="ICD-O-3 Morphologie")
    pathologischer_befund: dict = Field(description="Pathologische Befundstrukturen")

    class Config:
        extra = "forbid"


# ------------------------------------------------------------
# KDL: PT130102 - Anforderung Labor, Zytologieanforderung Molekularpathologiebefund
# Standard: TNM-Klassifikation (UICC), ICD-O-3 Morphologie, pathologische Befundstrukturen
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class AnforderungLaborZytologieMolekularpathologiebefund(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code")
    patient_id: str = Field(description="Patient ID")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")
    tumor_location: str = Field(description="Tumor-Lokalisation")
    tnm_classification: dict = Field(description="TNM-Klassifikation (UICC)")
    icd_o_3_morphology: str = Field(description="ICD-O-3 Morphologie")
    pathology_findings: list[dict] = Field(description="Pathologische Befundstrukturen")

    class Config:
        extra = "forbid"


# ------------------------------------------------------------
# KDL: PT260101 - nisse einer Untersuchung, bei der Druck und Volumen der Harnblase gemessen wird. Zytologieanforderung
# Standard: TNM-Klassifikation (UICC), ICD-O-3 Morphologie, pathologische Befundstrukturen
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class MessenwirdZytologieanforderung(KdlDocumentBase):
    blasen_volumen: float = Field(description="Blasenvolumen in ml")
    blasen_druck: float = Field(description="Blasendruck in cm H2O")
    zytologie_anforderung: bool = Field(description="Zytologische Untersuchung erforderlich")


# ------------------------------------------------------------
# KDL: PT260102 - Laboranforderung, Molekularpathologieanforderung Zytologiebefund
# Standard: TNM-Klassifikation (UICC), ICD-O-3 Morphologie, pathologische Befundstrukturen
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class OgieanforderungZytologiebefund(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    patient_id: str = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    sex: str = Field(description="Geschlecht des Patienten")
    tumor_location: str = Field(description="Tumor-Lokalisation")
    tnm_classification: dict = Field(description="TNM-Klassifikation (UICC)")
    icd_o_morphology: str = Field(description="ICD-O-3 Morphologie")
    pathology_findings: list = Field(description="Pathologische Befundstrukturen")

    class Config:
        schema_extra = {
            "example": {
                "kdl_code": "PT260102",
                "patient_id": "12345",
                "birth_date": "1980-01-01",
                "sex": "male",
                "tumor_location": "Brust",
                "tnm_classification": {"T": "1", "N": "0", "M": "0"},
                "icd_o_morphology": "8530/3",
                "pathology_findings": ["Befund 1", "Befund 2"],
            }
        }


# ------------------------------------------------------------
# KDL: SD070101 - gelegte Kriterien zur Feststellung der Notwendigkeit einer stationären Behandlung. Geburtenbericht
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class Geburtenbericht(KdlDocumentBase):
    geburtsdatum: str = Field(description="Geburtsdatum")
    geschlecht: str = Field(description="Geschlecht des Kindes")
    geburtsgewicht: float = Field(description="Geburtsgewicht in Gramm")
    length: float = Field(description="Länge des Kindes in Zentimeter")
    kopfumfang: float = Field(description="Kopfumfang in Zentimeter")
    apgar_wert: int = Field(description="APGAR-Wert nach 5 Minuten")
    stationaerer_aufenthalt: bool = Field(description="Notwendigkeit eines stationären Aufenthalts")


# ------------------------------------------------------------
# KDL: SD070103 - Geburtenbericht Geburtenverlaufskurve
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class GeburtenberichtGeburtenverlaufskurve(KdlDocumentBase):
    dokumenttyp: str = Field(description="Dokumenttyp")
    version: str = Field(description="Version des Dokumenttyps")
    patient_id: UUID = Field(description="Patient ID")
    geburtsdatum: date = Field(description="Geburtsdatum")
    mutterliche_komplikationen: list[str] = Field(description="Mutterliche Komplikationen")
    geburt: Geburtenverlaufskurve = Field(description="Geburtenverlaufskurve")


class Geburtenverlaufskurve(BaseModel):
    einleitung: str = Field(description="Einleitung der Geburt")
    wehen: list[Wehe] = Field(description="Verlauf der Wehen")
    geburt: Geburtsverlauf = Field(description="Verlauf der Geburt")
    neonatologie: Neonatologie = Field(description="Neonatologische Versorgung")


class Wehe(BaseModel):
    zeitpunkt: datetime = Field(description="Zeitpunkt der Wehe")
    dauer: float = Field(description="Dauer der Wehe in Minuten")
    starke: str = Field(description="Stärke der Wehe")


class Geburtsverlauf(BaseModel):
    geburtstag: date = Field(description="Geburtstag")
    geburtszeit: time = Field(description="Uhrzeit der Geburt")
    geburtsart: str = Field(description="Art der Geburt")
    kind: Kind = Field(description="Kindliche Daten")


class Neonatologie(BaseModel):
    apgar_wert: int = Field(description="APGAR-Wert")
    neonatologische_bemaessigung: str = Field(description="Neonatologische Bemaessigung")
    stationaerer_aufenthalt: bool = Field(description="Stationärer Aufenthalt")


class Kind(BaseModel):
    geschlecht: str = Field(description="Geschlecht des Kindes")
    gewicht: float = Field(description="Gewicht des Kindes in Gramm")
    length: float = Field(description="Länge des Kindes in Zentimeter")


# ------------------------------------------------------------
# KDL: SD070104 - Neugeborenenscreening
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Neugeborenenscreening(KdlDocumentBase):
    kdl_code: str = Field(default="SD070104", const=True)
    Screening_Datum: datetime = Field(description="Datum des Neugeborenenscreenings")
    Screening_Zeitpunkt: str = Field(
        description="Zeitpunkt des Neugeborenenscreenings (z.B. 'geboren', 'entlassen')"
    )
    Screening_Klinik: str = Field(
        description="Klinik, in der das Neugeborenenscreening durchgeführt wurde"
    )
    Screening_Personal: str = Field(
        description="Personal, das das Neugeborenenscreening durchgeführt hat"
    )

    Laborwerte: list[Laborwert] = Field(
        default_factory=list, description="Laborwerte des Neugeborenen"
    )


class Laborwert(BaseModel):
    Parameter: str = Field(
        description="Parameter, der gemessen wurde (z.B. 'Blutbild', 'Blutzucker')"
    )
    Ergebnis: float = Field(description="Ergebnis des Parameters")
    Einheit: str = Field(description="Einheit des Ergebnisses (z.B. 'mmol/L', 'g/dL')")


# ------------------------------------------------------------
# KDL: SD070105 - Asessment Partogramm
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class AsessmentPartogramm(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_id: str = Field(description="Identifikationsnummer des medizinischen Dokuments")
    patient_id: str = Field(description="Patientenkennung")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    sex: str = Field(description="Geschlecht des Patienten")
    assessment_data: dict = Field(description="Befunddaten")

    class Config:
        extra = "forbid"


# ------------------------------------------------------------
# KDL: SD070106 - nahmen zur Wiedereingliederung in das Erwerbsle
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    document_type: str
    creation_date: datetime
    author: str


class namentlicheAngaben(BaseModel):
    vorname: str = Field(description="Vorname")
    nachname: str = Field(description="Nachname")
    geburtsdatum: date = Field(description="Geburtstag")


class beruflicheSituation(BaseModel):
    zuletztBeraeuflicheTaeigkeit: str = Field(description="Letzte berufliche Tätigkeit")
    wiedereingliederungsmaerklich: bool = Field(description="Wiedereingliederung möglich?")


class gesundheitlicherZustand(BaseModel):
    diagnose: str = Field(description="Diagnose")
    beschwerden: str = Field(description="Beschwerden")
    behandlungsbedarf: bool = Field(description="Behandlungsbedarf vorhanden?")


class namentlicheAngaben(BaseModel):
    vorname: str = Field(description="Vorname")
    nachname: str = Field(description="Nachname")
    geburtsdatum: date = Field(description="Geburtstag")


class namentlicheAngaben(BaseModel):
    vorname: str = Field(description="Vorname")
    nachname: str = Field(description="Nachname")
    geburtsdatum: date = Field(description="Geburtstag")


class beruflicheSituation(BaseModel):
    zuletztBeraeuflicheTaeigkeit: str = Field(description="Letzte berufliche Tätigkeit")
    wiedereingliederungsmaerklich: bool = Field(description="Wiedereingliederung möglich?")


class gesundheitlicherZustand(BaseModel):
    diagnose: str = Field(description="Diagnose")
    beschwerden: str = Field(description="Beschwerden")
    behandlungsbedarf: bool = Field(description="Behandlungsbedarf vorhanden?")


class namentlicheAngaben(BaseModel):
    vorname: str = Field(description="Vorname")
    nachname: str = Field(description="Nachname")
    geburtsdatum: date = Field(description="Geburtstag")


class beruflicheSituation(BaseModel):
    zuletztBeraeuflicheTaeigkeit: str = Field(description="Letzte berufliche Tätigkeit")
    wiedereingliederungsmaerklich: bool = Field(description="Wiedereingliederung möglich?")


class gesundheitlicherZustand(BaseModel):
    diagnose: str = Field(description="Diagnose")
    beschwerden: str = Field(description="Beschwerden")
    behandlungsbedarf: bool = Field(description="Behandlungsbedarf vorhanden?")


class namentlicheAngaben(BaseModel):
    vorname: str = Field(description="Vorname")
    nachname: str = Field(description="Nachname")
    geburtsdatum: date = Field(description="Geburtstag")


class beruflicheSituation(BaseModel):
    zuletztBeraeuflicheTaeigkeit: str = Field(description="Letzte berufliche Tätigkeit")
    wiedereingliederungsmaerklich: bool = Field(description="Wiedereingliederung möglich?")


class gesundheitlicherZustand(BaseModel):
    diagnose: str = Field(description="Diagnose")
    beschwerden: str = Field(description="Beschwerden")
    behandlungsbedarf: bool = Field(description="Behandlungsbedarf vorhanden?")


# ------------------------------------------------------------
# KDL: SD070108 - befund
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Befund(KdlDocumentBase):
    dokument_id: str = Field(description="Identifikationsnummer des Dokuments")
    dokument_typ: str = Field(description="Typ des Dokuments (z.B. Befund)")
    erstellungszeitpunkt: datetime.datetime = Field(
        description="Zeitpunkt der Erstellung des Dokuments"
    )
    autor: dict = Field(description="Autor des Dokuments (Name und Berufsbezeichnung)")
    patient: dict = Field(description="Patientendaten (Name, Geburtsdatum, Geschlecht)")
    befund_text: str = Field(description="Freitextlicher Befund")
    laborwerte: list[dict] = Field(
        description="Laborwerte (Tabelle mit Spalten für Parameter und Ergebnis)"
    )


# ------------------------------------------------------------
# KDL: SD070109 - Geburtenbogen
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Geburtenbogen(KdlDocumentBase):
    dokument_id: str = Field(description="Identifikationsnummer des Geburtenbogens")
    geburtsdatum: date = Field(description="Das Geburtsdatum des Kindes")
    geschlecht: Literal["m", "w", "u"] = Field(description="Das Geschlecht des Kindes")
    mutter_name: str = Field(description="Der Name der Mutter")
    vater_name: str | None = Field(default=None, description="Der Name des Vaters")
    geburtsart: Literal["vaginal", "kaiserschnitt"] = Field(description="Die Art der Geburt")
    geburtsgewicht: float = Field(description="Das Geburtsgewicht des Kindes in Gramm")
    kind_name: str | None = Field(default=None, description="Der Name des Kindes")

    class Config:
        schema_extra = {
            "example": {
                "dokument_id": "SD070109-20220101-001",
                "geburtsdatum": "2022-01-01",
                "geschlecht": "m",
                "mutter_name": "Max Mustermann",
                "vater_name": "Maria Müller",
                "geburtsart": "vaginal",
                "geburtsgewicht": 3500.0,
                "kind_name": "Maximilian",
            }
        }


# ------------------------------------------------------------
# KDL: SD070110 - sorglich festgehaltenen letzten Willen. Perzentilkurve
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class SorglichfestgehaltenenletztenWillenPerzentilkurve(KdlDocumentBase):
    dokumenttyp: str = Field(description="Dokumenttyp")
    version: str = Field(description="Version des Dokuments")
    erstellungsdatum: datetime = Field(description="Erstellungsdatum des Dokuments")
    patient_id: UUID = Field(description="Patient ID")
    perzentilkurve_daten: list[dict] = Field(description="Perzentilkurve-Daten")

    class Config:
        orm_mode = True


# ------------------------------------------------------------
# KDL: SD070112 - nisse von Messungen der Herztöne des ungeborenen Kindes sowie die Wehentätigkeit der Mutter. Datenblatt für den Pädiater
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class MutterDatenblattfürdenPädiater(KdlDocumentBase):
    herztöne_des_ungeborenen_kindes: str = Field(
        description="Messungen der Herztöne des ungeborenen Kindes"
    )
    wehentätigkeit_der_mutter: str = Field(description="Wehentätigkeit der Mutter")


# ------------------------------------------------------------
# KDL: SD070199 - ben, die nicht in einer spezifischeren KDL dieser Unterklasse abgebildet werden können. Sonstige Geburtendokumentation
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class SonstigeGeburtendokumentation(KdlDocumentBase):
    geburtsdatum: str = Field(description="Das Geburtsdatum des Patienten")
    geschlecht: str = Field(description="Das Geschlecht des Patienten")
    muttermundstellung: str = Field(description="Die Muttermundstellung bei der Geburt")
    kinderzahl_mutter: int = Field(
        description="Die Anzahl der Kinder, die die Mutter bereits geboren hat"
    )
    geburtsart: str = Field(description="Die Art der Geburt (z.B. spontan, Sectio)")
    geburtsgewicht: float = Field(description="Das Geburtsgewicht des Kindes in Gramm")
    geburtslänge: float = Field(description="Die Geburtslänge des Kindes in Zentimetern")
    apgar_wert_1_minute: int = Field(
        description="Der APGAR-Wert des Kindes 1 Minute nach der Geburt"
    )
    apgar_wert_5_minutes: int = Field(
        description="Der APGAR-Wert des Kindes 5 Minuten nach der Geburt"
    )
    apgar_wert_10_minutes: int = Field(
        description="Der APGAR-Wert des Kindes 10 Minuten nach der Geburt"
    )


# ------------------------------------------------------------
# KDL: SD070201 - ben über Diagnostik, Krankheitsund Behandlungsverlauf eines ausgewählten Zeitraumes, chronologisch erfasst. Barthel Index
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class RonologischerfasstBarthelIndex(KdlDocumentBase):
    dokument_id: str = Field(description="Identifikationsnummer des Dokuments")
    erstellungsdatum: datetime = Field(description="Datum der Erstellung des Dokuments")
    autor: str = Field(description="Autor des Dokuments")
    patient_id: str = Field(description="Identifikationsnummer des Patienten")
    diagnose: list[str] = Field(description="Diagnosen des Patienten")
    laborwerte: list[Laborwert] = Field(description="Laborwerte des Patienten")
    behandlungsverlauf: list[Behandlungsschritt] = Field(
        description="Behandlungsverlauf des Patienten"
    )
    barthel_index: int = Field(description="Barthel-Index des Patienten")


class Laborwert(BaseModel):
    zeitpunkt: datetime = Field(description="Zeitpunkt der Messung")
    wert: float = Field(description="Messwert")
    einheit: str = Field(description="Einheit des Messwertes")


class Behandlungsschritt(BaseModel):
    zeitpunkt: datetime = Field(description="Zeitpunkt des Behandlungsschrittes")
    beschreibung: str = Field(description="Beschreibung des Behandlungsschrittes")


# ------------------------------------------------------------
# KDL: SD070202 - ben zur Einschätzung des Risikos, ein Druckgeschwür zu entwickeln. Dem Tect
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class UckgeschwürzuentwickelnDemTect(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    birth_date: date = Field(description="Geburtsdatum des Patienten")
    risk_factors: list[str] = Field(description="Risikofaktoren für Druckgeschwüre")
    prevention_measures: list[str] = Field(
        description="Maßnahmen zur Prävention von Druckgeschwüren"
    )


# ------------------------------------------------------------
# KDL: SD070204 - Sturzrisikoerfassungsbogen
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class Sturzrisikoerfassungsbogen(KdlDocumentBase):
    patient_id: int = Field(description="Patient ID")
    sturz_datum: datetime = Field(description="Datum des Sturzes")
    sturz_ort: str = Field(description="Ort des Sturzes")
    verletzung_beschreibung: str = Field(description="Beschreibung der Verletzungen")
    risikofaktoren: list[str] = Field(description="Risikofaktoren für Stürze")


# ------------------------------------------------------------
# KDL: SD070205 - DemTect, MMST Geriatrische Depressionsskala
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class DemTectMMSTGeriatrischeDepressionsskala(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code für das medizinische Dokument")
    patient_id: UUID = Field(description="Patienten-ID des betroffenen Patienten")
    birth_date: date = Field(description="Geburtsdatum des Patienten")
    gender: Literal["male", "female"] = Field(description="Geschlecht des Patienten")
    score_total: float = Field(
        description="Gesamtpunktzahl der DemTect-MMST-Geriatrische Depressionsskala"
    )
    score_cognitive: float = Field(
        description="Kognitions-Punktzahl der DemTect-MMST-Geriatrischen Depressionsskala"
    )
    score_non_cognitive: float = Field(
        description="Non-Cognitions-Punktzahl der DemTect-MMST-Geriatrischen Depressionsskala"
    )


# ------------------------------------------------------------
# KDL: SD070206 - strative Anga
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class StrativeAnga(KdlDocumentBase):
    dokument_id: int
    patient_id: str
    patient_name: str
    birth_date: str
    sex: str
    document_type: str = Field(default="SD070206", const="SD070206")
    creation_time: str
    author: str

    class Config:
        extra = "forbid"


# ------------------------------------------------------------
# KDL: SD070207 - aufga
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Aufga(KdlDocumentBase):
    dokument_id: str = Field(description="Identifikationsnummer des Dokuments")
    dokument_typ: str = Field(description="Typ des Dokuments (z.B. SD070207)")
    erstellungszeitpunkt: datetime = Field(description="Datum und Uhrzeit der Erstellung")
    autor: autor = Field(description="Autor des Dokuments")


class autor(BaseModel):
    name: str = Field(description="Name des Autors")
    berufstitel: str = Field(description="Berufstitel des Autors")


# ------------------------------------------------------------
# KDL: SD070208 - Timed Up and Go Test
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class TimedUpandGoTest(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code für den Timed Up and Go Test")
    patient_id: str = Field(description="Patienten-ID")
    test_date: datetime.date = Field(description="Datum des Tests")
    walk_time: float = Field(description="Zeit für das Gehen (in Sekunden)")
    turn_time: float = Field(description="Zeit für das Drehen (in Sekunden)")
    sit_to_stand_time: float = Field(description="Zeit von Sitzen bis Stehen (in Sekunden)")
    total_time: float = Field(description="Gesamtzeit des Tests (in Sekunden)")


# ------------------------------------------------------------
# KDL: SD070299 - bogen, Kunsttherapie Sonstiges geriatrisches Dokument
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class KunsttherapieSonstigesgeriatrischesDokument(KdlDocumentBase):
    art_der_kunsttherapie: str = Field(description="Art der Kunsttherapie")
    durchgefuehrte_maenner: int = Field(description="Anzahl der durchgeführten Männer")
    durchgefuehrte_frauen: int = Field(description="Anzahl der durchgeführten Frauen")
    durchgefuehrte_total: int = Field(description="Gesamtanzahl der durchgeführten Kunsttherapien")
    anmerkung: str = Field(description="Anmerkungen zur Kunsttherapie", default="")


# ------------------------------------------------------------
# KDL: SD110101 - Altersdepression zu ermitteln
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_type: str = Field(description="Typ des medizinischen Dokuments")


class Altersdepressionzuermitteln(KdlDocumentBase):
    kdl_code: str = "SD110101"
    document_type: str = "Altersdepression zu ermitteln"

    patient_id: int = Field(description="ID des Patienten")
    age: int = Field(description="Alter des Patienten in Jahren")
    depression_score: float = Field(description="Depressions-Score nach HAMD")

    medical_history: list[str] = Field(description="Vorerkrankungen und Medikamenteneinnahme")

    laboratory_results: list["Laborwert"] = Field(
        default_factory=list, description="Ergebnisse von Laboruntersuchungen"
    )


class Laborwert(BaseModel):
    parameter: str = Field(description="Parameter der Laboruntersuchung")
    value: float = Field(description="Wert des Parameters")
    unit: str = Field(description="Einheit des Parameters")


# ------------------------------------------------------------
# KDL: SD110102 - Intensivmedizinische Komplexbehandlungsdokumentation
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Omplexbehandlungsdokumentation(KdlDocumentBase):
    patient_id: UUID = Field(description="Patienten-ID")
    birth_date: date = Field(description="Geburtsdatum des Patienten")
    sex: Literal["male", "female", "diverse"] = Field(description="Geschlecht des Patienten")
    diagnosis: str = Field(description="Diagnose")
    treatment_start: datetime = Field(description="Anfang der Behandlung")
    treatment_end: datetime | None = Field(default=None, description="Ende der Behandlung")
    intensive_care_unit_stays: list[IntensiveCareUnitStay] = Field(
        description="Aufenthalte auf der Intensivstation"
    )


class IntensiveCareUnitStay(BaseModel):
    admission_date: datetime = Field(description="Eintrittsdatum auf die Intensivstation")
    discharge_date: datetime | None = Field(
        default=None, description="Entlassungsdatum von der Intensivstation"
    )
    reason_for_admission: str = Field(
        description="Grund für den Aufenthalt auf der Intensivstation"
    )
    treatments: list[Treatment] = Field(description="Behandlungen während des Aufenthalts")


class Treatment(BaseModel):
    treatment_type: Literal["medication", "surgery", "other"] = Field(
        description="Art der Behandlung"
    )
    description: str = Field(description="Beschreibung der Behandlung")


# ------------------------------------------------------------
# KDL: SD110103 - MRSA Komplexbehandlungsdokumentation
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")
    document_type: str = Field(description="Dokumenttyp")


class MRSAKomplexbehandlungsdokumentation(KdlDocumentBase):
    kdl_code: str = "SD110103"
    document_type: str = "MRSA Komplexbehandlungsdokumentation"

    patient_id: str = Field(description="Patientenkennnummer")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    admission_date: str = Field(description="Eintrittsdatum in die Einrichtung")

    lab_results: list[dict[str, str]] = Field(default_factory=list, description="Laborergebnisse")
    treatment_plan: str = Field(description="Behandlungsplan")
    follow_up_measurements: list[str] = Field(
        default_factory=list, description="Folgende Messungen sind geplant"
    )


# ------------------------------------------------------------
# KDL: SD110104 - Dazu zählen Nerven, die Muskeln versorgen sowie Nerven für Sinnesempfindungen. Neurologische Komplexbehandlungsdokumentation
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class NeurologischeKomplexbehandlungsdokumentation(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")
    diagnosis: str = Field(description="Diagnose")
    treatment_plan: str = Field(description="Behandlungsplan")
    medication: list[str] = Field(description="Medikation")
    allergies: list[str] = Field(description="Allergien")


# ------------------------------------------------------------
# KDL: SD110105 - Palliativmedizinische Komplexbehandlungsdokumentation
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code")


class Omplexbehandlungsdokumentation(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")
    diagnosis: str = Field(description="Diagnose")
    treatment_start_date: str = Field(description="Behandlungsstartdatum")
    treatment_end_date: str = Field(description="Behandlungsenddatum")
    symptoms: list[str] = Field(description="Symptome")
    interventions: list[str] = Field(description="Interventionen")


# ------------------------------------------------------------
# KDL: SD110106 - PKMS-Dokumentation
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class PKMSDokumentation(KdlDocumentBase):
    dokument_id: str = Field(description="PKMS-Dokument-ID")
    patient_id: str = Field(description="Patient-ID")
    erstellungsdatum: datetime = Field(description="Erstellungsdatum des PKMS-Dokuments")
    autor_id: str = Field(description="ID des Autors des PKMS-Dokuments")
    autor_name: str = Field(description="Name des Autors des PKMS-Dokuments")
    medizinischer_bericht: str = Field(description="Medizinischer Bericht zum PKMS-Dokument")
    laborwerte: list[Laborwert] = Field(
        default_factory=list, description="Laborwerte im PKMS-Dokument"
    )


class Laborwert(BaseModel):
    parameter_id: str = Field(description="ID des Laborparameters")
    parameter_name: str = Field(description="Name des Laborparameters")
    wert: float = Field(description="Wert des Laborparameters")


# ------------------------------------------------------------
# KDL: SD110199 - dystokie, Geburtsplanung, Still-/ Ernährungsprotokoll, Entnahme Nabelschnurblut Sonstige Komplexbehandlungsdokumentation
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")
    document_type: str = Field(description="Dokumenttyp")


class Geburtsplanung(BaseModel):
    geburtsdatum: str = Field(description="Geburtsdatum")
    geburtszeit: str = Field(description="Geburtszeit")
    geburtstyp: str = Field(description="Typ der Geburt")
    geburtsverlauf: str = Field(description="Verlauf der Geburt")


class StillErnaehrungsprotokoll(BaseModel):
    stillen_ja_nein: bool = Field(description="Stillen ja/nein")
    stilldauer: int = Field(description="Dauer des Stillens in Monaten")
    nahrungsergaenzung: str = Field(description="Nahrungsergänzung")


class EntnahmeNabelschnurblut(BaseModel):
    entnahmestatus: bool = Field(description="Status der Nabelschnurblutentnahme")
    entnahmedatum: str = Field(description="Datum der Nabelschnurblutentnahme")


class SonstigeKomplexbehandlungsdokumentation(BaseModel):
    behandlungstyp: str = Field(description="Typ der Behandlung")
    behandlungsverlauf: str = Field(description="Verlauf der Behandlung")


class Omplexbehandlungsdokumentation(KdlDocumentBase):
    geburtsplanung: Geburtsplanung
    still_ernaehrungsprotokoll: StillErnaehrungsprotokoll
    entnahme_nabelschnurblut: EntnahmeNabelschnurblut
    sonstige_komplexbehandlungsdokumentation: SonstigeKomplexbehandlungsdokumentation


# ------------------------------------------------------------
# KDL: SD130101 - ben zum Grund der stationären Aufnahme. Standardisiertes Einweisungsdokument gemäß Kassenärztlicher Bundesvereinigung (KBV Muster 2). Vertrag Maßregelvollzug
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class VMuster2VertragMaßregelvollzug(KdlDocumentBase):
    kdl_code: str = "SD130101"
    patient: dict = Field(description="Patientendaten")
    einweisender_arzt: str = Field(description="Einweisender Arzt")
    diagnose: str = Field(description="Diagnose")
    laborwerte: list[dict] = Field(default=[], description="Laborwerte")


# ------------------------------------------------------------
# KDL: SD130102 - ambulanten Vorsorgeleistung in anerkannten Kurorten) Antrag Maßregelvollzug
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class KurortenAntragMaßregelvollzug(KdlDocumentBase):
    antragsteller: str = Field(description="Name des Antragstellers")
    geburtsdatum_antragsteller: str = Field(
        description="Geburtstag des Antragstellers (TT.MM.JJJJ)"
    )
    adresse_antragsteller: str = Field(description="Adresse des Antragstellers")
    kurort: str = Field(description="Name des anerkannten Kurorts")
    behandlungszeitraum_von: str = Field(description="Behandlungszeitraum von (TT.MM.JJJJ)")
    behandlungszeitraum_bis: str = Field(description="Behandlungszeitraum bis (TT.MM.JJJJ)")
    diagnose: str = Field(description="Diagnose")
    verschreibungen: list[str] = Field(default_factory=list, description="Verschreibungen")


# ------------------------------------------------------------
# KDL: SD130103 - liche Korrespondenz zwischen medizinischer Einrichtung und Krankenkasse. Schriftverkehr Maßregelvollzug
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class SchriftverkehrMassregelvollzug(KdlDocumentBase):
    dokument_id: str = Field(description="Identifikationsnummer des Dokuments")
    sender: dict = Field(description="Absender der Korrespondenz")
    receiver: dict = Field(description="Empfänger der Korrespondenz")
    subject: str = Field(description="Betreff der Korrespondenz")
    text: str = Field(description="Text der Korrespondenz")
    date: datetime = Field(description="Datum der Korrespondenz")


# ------------------------------------------------------------
# KDL: SD130104 - gung zur Datenübermittlung an die Krankenkasse mit Widerruf. Einwilligung/ Einverständniserklärung Maßregelvollzug
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class EinwilligungEinverstaendnisMaßregelvollzug(KdlDocumentBase):
    einwilligung_text: str = Field(description="Text der Einwilligung/Einverständniserklärung")
    widerruf_möglich: bool = Field(description="Angabe, ob Widerruf möglich ist")
    widerruf_bedingungen: str = Field(description="Bedingungen für den Widerruf", default="")


# ------------------------------------------------------------
# KDL: SD130199 - ben, die nicht in einer spezifischeren KDL dieser Unterklasse abgebildet werden können. Sonstiges Maßregelvollzugdokument
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class NstigesMaßregelvollzugdokument(KdlDocumentBase):
    dokument_typ: str = Field(description="Typ des Dokuments")
    erstellungsdatum: datetime = Field(description="Erstellungsdatum des Dokuments")
    erstellender_arzt: str = Field(description="Name des erstellenden Arztes")
    patient_id: UUID = Field(description="ID des Patienten")
    patient_name: str = Field(description="Name des Patienten")
    patient_geburtsdatum: date = Field(description="Geburtsdatum des Patienten")
    patient_gender: Literal["m", "w", "divers"] = Field(description="Geschlecht des Patienten")
    einweisungsgrund: str = Field(description="Grund für die Einweisung")
    diagnose: str = Field(description="Diagnose")
    behandlungsplan: str = Field(description="Behandlungsplan")
    sonderbehandlungen: list[str] = Field(description="Sonderbehandlungen")
    entlassungsdatum: datetime | None = Field(
        description="Entlassungsdatum des Patienten", default=None
    )
    entlassungsgrund: str | None = Field(description="Grund für die Entlassung", default=None)


# ------------------------------------------------------------
# KDL: SD150101 - Follow-UpBogen
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class FollowUpBogen(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    follow_up_date: datetime = Field(description="Datum des Follow-Up")
    symptoms: list[str] = Field(description="Symptome")
    diagnosis: str | None = Field(description="Diagnose", default=None)
    treatment: list[str] | None = Field(description="Behandlung", default=None)
    medication: list[str] | None = Field(description="Medikation", default=None)


# ------------------------------------------------------------
# KDL: SD150102 - Meldebogen Krebsregister
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Typ des Dokuments")


class MeldebogenKrebsregister(KdlDocumentBase):
    tumor_location: str = Field(description="Lage des Tumors")
    tumor_histology: str = Field(description="Histologie des Tumors")
    tumor_stage: str = Field(description="Tumorstadium")
    treatment_plan: str = Field(description="Behandlungsplan")


# ------------------------------------------------------------
# KDL: SD150103 - weise über die Transplantation von Gewebe, Organen oder Körperteilen. Tumorkonferenzprotokoll
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class Tumorkonferenzprotokoll(KdlDocumentBase):
    tumorart: str = Field(description="Art des Tumors")
    tumorstadium: str = Field(description="Stadium des Tumors")
    behandlungsplan: str = Field(description="Behandlungsplan für den Tumor")


# ------------------------------------------------------------
# KDL: SD150104 - nisse des Zusammentreffens von verschiedenen Fachärzten, über die Beratung der weiteren Behandlung von Tumorerkrankungen. Tumorlokalisationsbogen
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Tumorlokalisationsbogen(KdlDocumentBase):
    tumor_lokalisation: str = Field(description="Lokalisation des Tumors")
    tumor_art: str = Field(description="Art des Tumors")
    tumor_size: float = Field(description="Größe des Tumors in cm³")
    tumor_stage: str = Field(description="Tumorstadium nach TNM-Klassifikation")
    tumor_treatment: str = Field(description="Bisherige Tumorbehandlung")


# ------------------------------------------------------------
# KDL: SD150199 - ben, die nicht in einer spezifischeren KDL dieser Unterklasse abgebildet werden können. Sonstiger onkologischer Dokumentationsbogen
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_type: str = Field(description="Typ des medizinischen Dokuments")


class KologischerDokumentationsbogen(KdlDocumentBase):
    kdl_code: str = "SD150199"
    document_type: str = "Sonstiger onkologischer Dokumentationsbogen"

    tumorart: str = Field(description="Art des Tumors")
    tumorstadium: str = Field(description="Stadium des Tumors")
    metastasen_befund: bool = Field(description="Vorhandensein von Metastasen")
    behandlungsplan: str = Field(description="Behandlungsplan für den Tumor")

    laborwerte: list[Dict[str, Any]] = Field(
        default_factory=list, description="Laborwerte des Patienten"
    )


# ------------------------------------------------------------
# KDL: SD160101 - schließlich handschriftliche Informationen auf einem formlosen Bogen. Handschriftliches Patiententagebuch
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class SchriftlichesPatiententagebuch(KdlDocumentBase):
    patient_id: str = Field(description="ID des Patienten")
    patient_name: str = Field(description="Name des Patienten")
    admission_date: str = Field(description="Einweisungsdatum")
    discharge_date: str = Field(description="Entlassungsdatum", default=None)
    attending_physician: str = Field(description="Behandelnder Arzt")
    diagnoses: list[str] = Field(description="Diagnosen")
    medications: list[str] = Field(description="Medikation")
    notes: list[str] = Field(description="Notizen")


# ------------------------------------------------------------
# KDL: SD160102 - therapeutische Anordnung durch den Arzt zur Behandlung einer psychischen Erkrankung. Psychologischer Erhebungsbogen
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class GPsychologischerErhebungsbogen(KdlDocumentBase):
    patient_id: int = Field(description="Patient ID")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    diagnosis: str = Field(description="Diagnose")
    symptoms: list[str] = Field(description="Symptome")
    treatment_plan: str = Field(description="Behandlungsplan")
    psychological_assessment_table: list[dict[str, str]] = Field(
        description="Psychologischer Erhebungsbogen (Tabelle)"
    )


# ------------------------------------------------------------
# KDL: SD160103 - Beschreibung und Festlegung der wichtigsten Merkmale des Forschungsvorhabens. Psychologische Therapieanordnung
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class SychologischeTherapieanordnung(KdlDocumentBase):
    anordnender_arzt: str = Field(description="Anordnender Arzt")
    patient_id: str = Field(description="Patient ID")
    diagnose: str = Field(description="Diagnose")
    therapie_ziel: str = Field(description="Therapie Ziel")
    therapie_dauer: int = Field(description="Therapie Dauer in Wochen")
    anzahl_sitzungen: int = Field(description="Anzahl der Sitzungen")


# ------------------------------------------------------------
# KDL: SD160104 - Psychologisches Therapiegesprächsprotokoll
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class PsychologischesTherapiegespraechsprotokoll(KdlDocumentBase):
    dokumenttyp: str = Field(description="Dokumenttyp (SD160104)")
    patient_id: str = Field(description="Patient ID")
    therapist_id: str = Field(description="Therapeut ID")
    gespraech_datum: str = Field(description="Datum des Therapiegesprächs")
    diagnose: str = Field(description="Diagnose")
    zielsetzung: str = Field(description="Zielsetzung der Therapie")
    therapieverlauf: str = Field(description="Verlauf der Therapie")


# ------------------------------------------------------------
# KDL: SD160105 - ben zur Feststellung einer psychischen Erkrankung sowie deren Schweregrad
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class RkrankungsowiederenSchweregrad(KdlDocumentBase):
    diagnose: str = Field(description="Diagnose")
    erkrankungsschweregrad: str = Field(description="Erkrankungsschweregrad")
    laborwerte: list[dict] = Field(default_factory=list, description="Laborwerte")
    anamnese: str = Field(description="Anamnese")
    befunde: list[str] = Field(default_factory=list, description="Befunde")


# ------------------------------------------------------------
# KDL: SD160199 - Sonstiges psychologisches Dokument
# Standard: Fachspezifische Dokumentationsstandards (DGGG, DGP, DGKJ, DGPPN)
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code des Dokuments")
    document_id: str = Field(description="Dokument-ID")


class SonstigePsychologischeZeile(BaseModel):
    code: str = Field(description="Code für die psychologische Diagnose")
    description: str = Field(description="Beschreibung der psychologischen Diagnose")


class SonstigesPsychologischesDokument(KdlDocumentBase):
    kdl_code: str = "SD160199"
    document_id: str
    diagnosis: list[SonstigePsychologischeZeile] = Field(
        default_factory=list, description="Psychologische Diagnosen"
    )


# ------------------------------------------------------------
# KDL: SF060101 - ben im Rahmen der Nachsorge zur Erfassung der Verlaufskontrolle nach Abschluss der Behandlung. Forschungsbericht
# Standard: ICH-GCP Richtlinie, AMG §40ff Prüfplandokumentation, Ethikkommissions-Vorgaben
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class ForschungsberichtLaborwert(BaseModel):
    wert: float = Field(description="Wert des Laborparameters")
    einheit: str = Field(description="Einheit des Laborparameters")


class DerBehandlungForschungsbericht(KdlDocumentBase):
    titel: str = Field(description="Titel des Forschungsberichts")
    autor: str = Field(description="Autor des Forschungsberichts")
    laborwerte: list[ForschungsberichtLaborwert] = Field(
        default_factory=list, description="Laborparameter im Forschungsbericht"
    )


# ------------------------------------------------------------
# KDL: SF060199 - Gesprächsnotiz Sonstige Forschungsdokumentation
# Standard: ICH-GCP Richtlinie, AMG §40ff Prüfplandokumentation, Ethikkommissions-Vorgaben
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code des Dokuments")
    document_id: str = Field(description="ID des Dokuments")


class GesprächsnotizSonstigeForschungsdokumentation(KdlDocumentBase):
    dokument_titel: str = Field(description="Titel des Dokuments")
    dokument_text: str = Field(description="Text des Dokuments")
    autor_informationen: dict = Field(description="Informationen über den Autor")
    dokumente_anhang: list = Field(description="Angehängte Dokumente")


# ------------------------------------------------------------
# KDL: SF190101 - Nachweis über die verabreichte Dosis der Zytostatika und die Anzahl der Zyklen. CRF-Bogen
# Standard: ICH-GCP Richtlinie, AMG §40ff Prüfplandokumentation, Ethikkommissions-Vorgaben
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class AunddieAnzahlderZyklenCRFBogen(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    treatment_start_date: date = Field(description="Startdatum der Behandlung")
    treatment_end_date: date | None = Field(description="Enddatum der Behandlung", default=None)
    zytostatikadosis: list[float] = Field(
        description="Verabreichte Dosis Zytostatika in mg/m² Körperoberfläche"
    )
    number_of_cycles: int = Field(description="Anzahl der Zyklen")


# ------------------------------------------------------------
# KDL: SF190102 - Fotodokumentation, Einverständniserklärung Neugeborenenscreening. Einwilligung Studie
# Standard: ICH-GCP Richtlinie, AMG §40ff Prüfplandokumentation, Ethikkommissions-Vorgaben
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class NeugeborenenscreeningEinwilligungStudie(KdlDocumentBase):
    patient_id: int = Field(description="ID des Patienten")
    einverständnis_erklärung: bool = Field(description="Einverständniserklärung des Patienten")
    neugeborenenscreening_durchgeführt: bool = Field(
        description="Neugeborenenscreening durchgeführt"
    )
    studie_einwilligung: bool = Field(description="Einwilligung zur Teilnahme an der Studie")


# ------------------------------------------------------------
# KDL: SF190103 - Protokoll Einund Ausschlusskriterien
# Standard: ICH-GCP Richtlinie, AMG §40ff Prüfplandokumentation, Ethikkommissions-Vorgaben
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    version: str = Field(description="Version des Dokuments")


class ProtokollEinundAusschlusskriterien(KdlDocumentBase):
    ein_und_ausschluss_kriterien: list[str] = Field(
        description="Liste der Ein- und Ausschlusskriterien"
    )
    studienpopulation: str = Field(description="Beschreibung der Studienpopulation")
    ausgeschlossen_patientengruppen: list[str] = Field(
        description="Patientengruppen, die von der Studie ausgeschlossen sind"
    )


# ------------------------------------------------------------
# KDL: SF190104 - ben zu empfohlenen Nahrungsmitteln aufgrund verschiedener Indikationen. Prüfplan
# Standard: ICH-GCP Richtlinie, AMG §40ff Prüfplandokumentation, Ethikkommissions-Vorgaben
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")
    document_type: str = Field(description="Art des medizinischen Dokuments")


class ChiedenerIndikationenPruefplan(KdlDocumentBase):
    kdl_code: str = "SF190104"
    document_type: str = "Prüfplan"

    nahrungsmittel: list[str] = Field(description="Empfohlene Nahrungsmittel")
    indikationen: list[str] = Field(description="Verschiedene Indikationen")

    laborwerte: list[Dict[str, Any]] = Field(description="Laborwerte des Patienten")


# ------------------------------------------------------------
# KDL: SF190105 - reaktion, Checkliste Transfusion, Konservenausgabeprotokoll SOP-Bogen
# Standard: ICH-GCP Richtlinie, AMG §40ff Prüfplandokumentation, Ethikkommissions-Vorgaben
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ServenausgabeprotokollSOPBogen(KdlDocumentBase):
    reaktion_id: int = Field(..., description="Reaktion ID")
    transfusion_checkliste: bool = Field(..., description="Transfusions-Checkliste")
    konserven_ausgabe_protokoll_sop_bogen: str = Field(
        ..., description="Konserven-Ausgabeprotokoll SOP-Bogen"
    )


# ------------------------------------------------------------
# KDL: SF190106 - ben zur Erstund Folgeversorgung eines künstlichen Ausganges. Studienbericht
# Standard: ICH-GCP Richtlinie, AMG §40ff Prüfplandokumentation, Ethikkommissions-Vorgaben
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code des medizinischen Dokuments")


class StudienberichtTabelleZeile(BaseModel):
    zeitpunkt: datetime = Field(description="Zeitpunkt der Messung")
    wert: float = Field(description="Messwert")
    einheit: str = Field(description="Einheit des Messwerts")


class TlichenAusgangesStudienbericht(KdlDocumentBase):
    patient_id: UUID = Field(description="ID des Patienten")
    art_der_kunstlichen_ausgangsstelle: str = Field(
        description="Art der künstlichen Ausgangsstelle"
    )
    studienbeginn_datum: date = Field(description="Datum des Studienbeginns")
    studienende_datum: date | None = Field(default=None, description="Datum des Studienendes")
    laborwerte: list[StudienberichtTabelleZeile] = Field(
        default_factory=list, description="Laborwerte im Verlauf der Studie"
    )


# ------------------------------------------------------------
# KDL: SF190199 - medizinischer Rehabilitation, Ärztliche Verordnung zur nachstationären Versorgung Sonstige Studiendokumentation
# Standard: ICH-GCP Richtlinie, AMG §40ff Prüfplandokumentation, Ethikkommissions-Vorgaben
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class NgSonstigeStudiendokumentation(KdlDocumentBase):
    verordnender_arzt: str = Field(description="Name und Funktion des verordnenden Arztes")
    patient: str = Field(description="Name und Geburtsdatum des Patienten")
    rehabilitationsziel: str = Field(description="Rehabilitationsziel")
    vorerkrankungen: list[str] = Field(description="Vorerkrankungen des Patienten")
    laborwerte: list["Laborwert"] = Field(description="Laborwerte des Patienten")


class Laborwert(BaseModel):
    parameter: str = Field(description="Laborparameter")
    wert: float = Field(description="Wert des Laborparameters")
    einheit: str = Field(description="Einheit des Laborparameters")


# ------------------------------------------------------------
# KDL: TH020101 - gangsarztbericht, Nachschaubericht, Ärztlicher Befundbericht Bestrahlungsplan
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class RBefundberichtBestrahlungsplan(KdlDocumentBase):
    gangsarztbericht: dict = Field(description="Gangsarztbericht")
    nachschaubericht: dict = Field(description="Nachschaubericht")
    arztlicher_befundbericht: dict = Field(description="Ärztlicher Befundbericht")
    bestrahlungsplan: dict = Field(description="Bestrahlungsplan")


# ------------------------------------------------------------
# KDL: TH020102 - individuelle Planung einer Bestrahlungstherapie mit Anga
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class NerBestrahlungstherapiemitAnga(KdlDocumentBase):
    patient_id: UUID = Field(description="Patient ID")
    birth_date: date = Field(description="Geburtsdatum des Patienten")
    sex: Literal["male", "female", "diverse"] = Field(description="Geschlecht des Patienten")
    diagnosis: str = Field(description="Diagnose")
    tumor_location: str = Field(description="Lage des Tumors")
    treatment_plan: list[dict] = Field(description="Behandlungsplan")
    radiation_dose: float = Field(description="Strahlendosis")
    fraction_size: float = Field(description="Dosis pro Fraktion")
    total_fractions: int = Field(description="Gesamtzahl der Fraktionen")
    treatment_start_date: date = Field(description="Startdatum der Behandlung")
    treatment_end_date: date = Field(description="Enddatum der Behandlung")
    side_effects: list[str] = Field(description="Nebenwirkungen")


# ------------------------------------------------------------
# KDL: TH020103 - Nachweis über die Durchführung einer Bestrahlungstherapie. Bestrahlungsverordnung
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class Bestrahlungsverordnung(KdlDocumentBase):
    patient_id: str = Field(description="Patientenkennung")
    patient_name: str = Field(description="Name des Patienten")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    therapy_start_date: str = Field(description="Startdatum der Bestrahlungstherapie")
    therapy_end_date: str = Field(description="Enddatum der Bestrahlungstherapie")
    total_dose: float = Field(description="Gesamtstrahlendosis in Gray (Gy)")
    fraction_size: float = Field(description="Größe einer Strahlendosis-Fraction in Gray (Gy)")
    number_of_fractions: int = Field(description="Anzahl der Strahlendosis-Fraktionen")
    treatment_goal: str = Field(description="Therapie-Ziel (z.B. kurativ, palliativ)")


# ------------------------------------------------------------
# KDL: TH020104 - lich vorgeschriebene Qualitätssicherungsverfahren laut IQTIG. Radiojodtherapieprotokoll
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class IQTIGRadiojodtherapieprotokoll(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    birth_date: date = Field(description="Geburtsdatum des Patienten")
    sex: Literal["m", "w"] = Field(description="Geschlecht des Patienten")
    weight: float = Field(description="Körpergewicht in kg")
    height: float = Field(description="Körpergröße in cm")
    radiojodtherapy_protocol: dict = Field(description="Radiojodtherapieprotokoll")


# ------------------------------------------------------------
# KDL: TH020105 - Therapieprotokoll mit Radionukliden
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class RadionuklidenZeile(BaseModel):
    radionuclide: str = Field(description="Radionuklid")
    activity: float = Field(description="Aktivität in MBq")
    administration_time: datetime = Field(description="Verabreichungszeitpunkt")


class TherapieprotokollmitRadionukliden(KdlDocumentBase):
    kdl_code: str = "TH020105"
    document_type: str = "Therapieprotokoll mit Radionukliden"

    patient_id: int = Field(description="Patientenkennnummer")
    therapy_start_date: date = Field(description="Anfang der Therapie")
    radionuclide_treatments: list[RadionuklidenZeile] = Field(
        description="Tabelle mit Radionuklidentherapien"
    )

    side_effects: str | None = Field(default=None, description="Nebenwirkungen")
    therapy_conclusion: str | None = Field(
        default=None, description="Therapieverlauf und Ergebnis"
    )


# ------------------------------------------------------------
# KDL: TH020199 - Vertragsbedingungen, Individuelle Vereinbarungen Sonstiges Bestrahlungstherapieprotokoll
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class SBestrahlungstherapieprotokoll(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    therapist_id: str = Field(description="Therapeut-ID")
    tumor_location: str = Field(description="Tumor-Lokalisation")
    treatment_plan: str = Field(description="Behandlungsplan")
    radiation_dose: float = Field(description="Strahlendosis")
    fraction_number: int = Field(description="Anzahl der Fraktionen")
    side_effects: list[str] = Field(description="Mögliche Nebenwirkungen")


# ------------------------------------------------------------
# KDL: TH060101 - genau zu prüfen. Dadurch soll eine falsche oder ungenaue KDL-Zuordnung vermieden werden. Inklusiva Muss ein Dokument zwingend einer Dokumentenklasse zugeordnet werden, wird dies im Inklusivum (Inkl.) aufgeführt. In diesem Fall ist der gewählte KDL-Kode zu verwenden. Beispiel 3 »Klassierungshilfe über die Beschreibung des KDL-Typs«
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_class: str = Field(description="Dokumentenklasse")


class Genauzuprüfen(KdlDocumentBase):
    description: str = Field(description="Beschreibung des KDL-Typs")


# ------------------------------------------------------------
# KDL: TH060102 - ben über eine Lieferung. Logopädieprotokoll
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class LogopaedieProtokoll(KdlDocumentBase):
    patient_id: str = Field(description="Patientenkennung")
    therapist_id: str = Field(description="Therapeutenkennung")
    treatment_date: date = Field(description="Behandlungsdatum")
    diagnosis: str = Field(description="Diagnose")
    therapy_goal: str = Field(description="Therapieziele")
    therapy_methods: list[str] = Field(description="Angewandte Therapiemethoden")
    therapy_results: list[str] = Field(description="Erreichte Therapieergebnisse")


# ------------------------------------------------------------
# KDL: TH060103 - Erfassung von Änderungen im Pflegeprozess und den daraus resultierenden Maßnahmen. Physiotherapieprotokoll
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Physiotherapieprotokoll(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    patient_name: str = Field(description="Name des Patienten")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    diagnosis: str = Field(description="Diagnose")
    therapy_start_date: str = Field(description="Anfang der Therapie")
    therapy_end_date: str = Field(description="Ende der Therapie")
    therapist: str = Field(description=" Therapeut")
    changes_in_care_process: list[dict] = Field(
        default_factory=list, description="Erfassung von Änderungen im Pflegeprozess"
    )
    resulting_measures: list[str] = Field(description="Daraus resultierende Maßnahmen")

    class Config:
        fields = {
            "changes_in_care_process": {
                "items": {
                    "type": "dict",
                    "fields": {
                        "change_date": ("str", "Datum der Änderung"),
                        "change_description": ("str", "Beschreibung der Änderung"),
                    },
                }
            }
        }


# ------------------------------------------------------------
# KDL: TH060104 - Anforderung oder Anmeldung von Diagnostiken ohne bildgebende Darstellung. Anforderung Funktionstherapie
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class AnforderungFunktionstherapie(KdlDocumentBase):
    anlass: str = Field(description="Anlass für die Anforderung/Funktionsdiagnostik")
    diagnose: str = Field(description="Bestehende Diagnose oder Verdacht auf eine Erkrankung")
    indikation: str = Field(description="Indikation für die Funktionsdiagnostik")
    durchgefuehrte_untersuchungen: list[str] = Field(
        description="Durchgeführte Untersuchungen und Methoden"
    )
    befund: str = Field(description="Befund der Untersuchung")
    therapieempfehlung: str = Field(description="Therapieempfehlung aufgrund des Befundes")


# ------------------------------------------------------------
# KDL: TH060199 - Patient Admission Form Sonstiges Funktionstherapieprotokoll
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    document_type: str
    patient_id: str
    admission_date: str
    discharge_date: str


class IgesFunktionstherapieprotokoll(KdlDocumentBase):
    kdl_code: str = Field(default="TH060199", const=True)
    function_therapy_protocol: dict = Field(description="Funktionstherapieprotokoll")
    therapy_goals: list[str] = Field(description="Therapieziel(e)")
    therapy_measures: list[str] = Field(description="Therapiemaßnahme(n)")
    therapy_results: list[str] = Field(description="Therapieergebnis(se)")


# ------------------------------------------------------------
# KDL: TH130101 - Zytologieanforderung, Molekularpathologieanforderung, Überweisungsschein Labor Anforderung Medikation
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        orm_mode = True


class HeinLaborAnforderungMedikation(KdlDocumentBase):
    patient_id: int = Field(..., description="Patienten-ID")
    birth_date: str = Field(..., description="Geburtsdatum des Patienten")
    gender: str = Field(..., description="Geschlecht des Patienten")
    diagnosis: str = Field(..., description="Diagnose")
    medication: list[str] = Field([], description="Medikation")
    laboratory_results: list[dict] = Field([], description="Laborwerte")


# ------------------------------------------------------------
# KDL: TH130102 - Unterbringung, Verlängerungsantrag, Antrag auf Psychotherapie, Antrag auf Pflegeeinstufung, Kostenübernahmeantrag, Antrag auf Leistungen der Pflegeversicherung Apothekenbuch
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class FlegeversicherungApothekenbuch(KdlDocumentBase):
    unterbringung: bool = Field(description="Unterbringung")
    verlangerungsantrag: bool = Field(description="Verlängerungsantrag")
    antrag_auf_psychotherapie: bool = Field(description="Antrag auf Psychotherapie")
    antrag_auf_pflegeeinstufung: bool = Field(description="Antrag auf Pflegeeinstufung")
    kostenuebernahmeantrag: bool = Field(description="Kostenübernahmeantrag")
    antrag_auf_leistenungen_der_pflegeversicherung_apothekenbuch: bool = Field(
        description="Antrag auf Leistungen der Pflegeversicherung Apothekenbuch"
    )


# ------------------------------------------------------------
# KDL: TH130103 - ben über Voraussetzungen, den Ablauf oder erforderliche funktionelle Diagnostiken. Erfolgte Durchführungen werden gekennzeichnet. Chemotherapieprotokoll
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ChemotherapieProtokoll(KdlDocumentBase):
    ben_ueber_Voraussetzungen: str = Field(description="Befunde und Vorerkrankungen")
    Ablauf: str = Field(description="Ablauf der Therapie")
    erforderliche_funktionelle_Diagnostiken: list[str] = Field(
        description="Erforderliche funktionelle Diagnostiken"
    )
    erfolgreiche_Durchführungen: list[str] = Field(description="Erfolgte Durchführungen")
    Chemotherapieprotokoll: str = Field(description="Chemotherapieprotokoll")


# ------------------------------------------------------------
# KDL: TH130104 - nisse einer Untersuchung zur Bestimmung von Veränderungen anhand von Gewebeproben. Hormontherapieprotokoll
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Hormontherapieprotokoll(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")
    diagnosis: str = Field(description="Diagnose")
    therapy_start_date: str = Field(description="Therapiestartdatum")
    therapy_end_date: str = Field(description="Therapieenddatum")
    hormone_levels: list[dict[str, float]] = Field(description="Hormonspiegel (Tabelle)")


# ------------------------------------------------------------
# KDL: TH130107 - Gutachten, Schriftverkehr MDK Arzt Medikamenten plan intern/extern
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class ZtMedikamentenplaninternextern(KdlDocumentBase):
    art_gutachten: str = Field(description="Art des Gutachtens")
    anlass_gutachten: str = Field(description="Anlass für das Gutachten")
    medikamente: list[dict[str, str]] = Field(
        description="Liste der Medikamente mit Dosierung und Anwendungsdauer"
    )
    begruendung: str = Field(description="Begründung für die Therapieempfehlung")


# ------------------------------------------------------------
# KDL: TH130108 - Zusammenfassung des Aufenthaltes während der Rehabilitation. Rezept
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class WährendderRehabilitationRezept(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    rezept_datum: datetime = Field(description="Datum des Rezepts")
    verschreiber: str = Field(description="Verschreiber des Rezepts")
    medikation: list[dict] = Field(description="Medikation")
    laborwerte: list[Laborwert] = Field(description="Laborwerte")


class Laborwert(BaseModel):
    parameter: str = Field(description="Laborparameter")
    wert: float = Field(description="Wert des Parameters")
    einheit: str = Field(description="Einheit des Wertes")


# ------------------------------------------------------------
# KDL: TH130109 - Schmerztherapieprotokoll
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    creation_time: datetime
    author: str


class Schmerztherapieprotokoll(KdlDocumentBase):
    kdl_code = "TH130109"
    patient_id: UUID = Field(description="Patienten-ID")
    pain_type: str = Field(description="Art der Schmerzen")
    pain_intensity: int = Field(ge=0, le=10, description="Schmerzintensität (0-10)")
    medication: list[str] = Field(description="Verordnete Medikamente")
    side_effects: list[str] | None = Field(default=None, description="Nebenwirkungen")
    therapy_goal: str = Field(description="Therapie-Ziel")
    therapy_duration: int = Field(ge=1, description="Dauer der Therapie (Tage)")
    follow_up: bool = Field(description="Benötigt Follow-up-Untersuchung")


# ------------------------------------------------------------
# KDL: TH130110 - Anweisungen für den weiteren Behandlungsverlauf nach einem operativen Eingriff. Prämedikationsprotokoll
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class NgriffPraemedikationsprotokoll(KdlDocumentBase):
    anweisungen: str
    praemedikation: list[str]
    postoperatives_management: dict[str, str]


# ------------------------------------------------------------
# KDL: TH130111 - Lyse Dokument
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    version: int = Field(description="Version des KDL-Dokuments")


class LyseDokument(KdlDocumentBase):
    kdl_code: str = "TH130111"
    version: int = 1
    patient_id: str = Field(description="Patientenkennung")
    diagnosis: str = Field(description="Diagnose")
    therapy_start: datetime = Field(description="Anfang der Therapie")
    therapy_end: datetime = Field(description="Ende der Therapie")
    drugs: list[Dict[str, Any]] = Field(description="Verwendete Medikamente")
    complications: list[str] = Field(description="Komplikationen während der Therapie")


# ------------------------------------------------------------
# KDL: TH130199 - Verlaufsbericht Strahlentherapie Sonstiges Dokument medikamentöser Therapie
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class DokumentmedikamentöserTherapie(KdlDocumentBase):
    kdl_code: str = "TH130199"
    patient_id: int = Field(description="Patienten-ID")
    therapy_start_date: date = Field(description="Startdatum der Strahlentherapie")
    therapy_end_date: date = Field(description="Enddatum der Strahlentherapie")
    medication_therapy: list[str] = Field(description="Medikamentöse Therapie")


# ------------------------------------------------------------
# KDL: TH160101 - Kriterien, die eine Teilnahme an einer Studie ermöglichen oder ausschließen. Protokoll Ernährungsberatung
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class EnProtokollErnährungsberatung(KdlDocumentBase):
    patient_id: UUID = Field(description="Patienten-ID")
    study_id: UUID = Field(description="Studien-ID")
    inclusion_criteria: list[Dict[str, str]] = Field(description="Einclusion criteria")
    exclusion_criteria: list[Dict[str, str]] = Field(description="Exclusion criteria")
    nutrition_consultation_protocol: Dict[str, Any] = Field(
        description="Protokoll Ernährungsberatung"
    )


# ------------------------------------------------------------
# KDL: TH160199 - ben, die nicht in einer spezifischeren KDL dieser Unterklasse abgebildet werden können. Sonstiges Protokoll Patientenschulung
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class IgesProtokollPatientenschulung(KdlDocumentBase):
    patient_id: int
    patient_name: str
    birth_date: date
    document_type: Literal["Ben"]
    document_subtype: Literal[
        "DienenichtineinerspezifischerenKDLdieserUnterklasseabgebildetwerdenkönnen.SonstigesProtokollPatientenschulung"
    ]
    creation_time: datetime
    author_id: int
    author_name: str
    patient_information: dict = Field(description="Allgemeine Informationen zum Patienten")
    medical_history: list[str] = Field(
        description="Vorerkrankungen und relevante medizinische Geschichte"
    )
    current_medication: list[str] = Field(description="Aktuelle Medikation des Patienten")
    allergies: list[str] = Field(description="Allergien des Patienten")
    patient_schooling: str = Field(description="Beschreibung der Patientenschulung")


# ------------------------------------------------------------
# KDL: TH200101 - Anforderung Blutkonserven
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class BlutkonservenAnforderung(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    patient_name: str = Field(description="Patient Name")
    birth_date: str = Field(description="Birth Date")
    blood_group: str = Field(description="Blood Group")
    required_blood_units: int = Field(description="Required Blood Units")
    reason_for_transfusion: str = Field(description="Reason for Transfusion")


# ------------------------------------------------------------
# KDL: TH200102 - Urinbefund, Virologiebefund Blutspendeprotokoll
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class UrinbefundVirologiebefundBlutspendeprotokoll(KdlDocumentBase):
    urin_probenahmezeitpunkt: datetime
    virologie_ergebnisse: list[Dict[str, Any]]
    blutspende_protokoll: BlutspendeProtokoll


class BlutspendeProtokoll(BaseModel):
    spender_informationen: Dict[str, Any]
    blutspende_datum: date
    blutspende_art: str = Field(description="Art der Blutspende")
    aufbereitete_blutprodukte: list[Dict[str, Any]]


# ------------------------------------------------------------
# KDL: TH200103 - relevanten Anga
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class RelevanteAnga(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")
    diagnosis: str = Field(description="Diagnose")
    therapy: str = Field(description="Therapie")


# ------------------------------------------------------------
# KDL: TH200104 - Ergeb
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ErgebnisZeile(BaseModel):
    parameter: str = Field(description="Parameter")
    einheit: str = Field(description="Einheit")
    wert: float | int = Field(description="Wert")


class Ergebnis(KdlDocumentBase):
    dokument_id: str = Field(description="Dokument-ID")
    patient_id: str = Field(description="Patient-ID")
    erstellungsdatum: datetime = Field(description="Erstellungsdatum")
    laborergebnisse: list[ErgebnisZeile] = Field(description="Laborergebnisse")


# ------------------------------------------------------------
# KDL: TH200199 - Nachbehandlungsschema Sonstiges Transfusionsdokument
# Standard: Leitliniengerechte Therapiedokumentation (AWMF), TFG §14, BÄK Hämotherapie-RL
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code")


class NachbehandlungsschemaSonstigesTransfusionsdokument(KdlDocumentBase):
    transfusionsart: str = Field(description="Art der Transfusion")
    transfusionsmenge: float = Field(description="Menge der Transfusion in ml")
    transfusionsdatum: str = Field(description="Datum der Transfusion")
    transfusionsgrund: str = Field(description="Grund für die Transfusion")


# ------------------------------------------------------------
# KDL: UB999997 - Gesamtdokumentation stationäre Versorgung
# Standard: Allgemeine Krankenhaus-Dokumentationsstandards, §630f BGB Dokumentationspflicht
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class LaborwertZeile(BaseModel):
    parameter: str = Field(description="Laborparameter")
    einheit: str = Field(description="Einheit der Messung")
    wert: float = Field(description="Messwert")


class GesamtdokumentationstationäreVersorgung(KdlDocumentBase):
    patient_id: int = Field(description="Patienten-ID")
    einweisender_arzt: str = Field(description="Name des einweisenden Arztes")
    aufnahme_datum: datetime = Field(description="Aufnahmedatum")
    entlassungs_datum: datetime = Field(description="Entlassungsdatum")
    diagnose: str = Field(description="Hauptdiagnose")
    komplikationen: list[str] = Field(description="Komplikationen während des Aufenthalts")
    laborwerte: list[LaborwertZeile] = Field(description="Laborwerte")


# ------------------------------------------------------------
# KDL: UB999998 - ganzheitliche interdisziplinäre geriatrische Beurteilung mit Festlegung von Maßnahmen im Behandlungsverlauf. Gesamtdokumentation ambulante Versorgung
# Standard: Allgemeine Krankenhaus-Dokumentationsstandards, §630f BGB Dokumentationspflicht
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class KumentationambulanteVersorgung(KdlDocumentBase):
    kdl_code: str = "UB999998"
    document_type: str = "Ganzheitliche interdisziplinäre geriatrische Beurteilung mit Festlegung von Maßnahmen im Behandlungsverlauf"

    patient_id: int = Field(description="ID des Patienten")
    birth_date: str = Field(description="Geburtstag des Patienten")
    gender: str = Field(description="Geschlecht des Patienten")

    diagnosis: str = Field(description="Diagnose")
    treatment_plan: str = Field(description="Behandlungsplan")

    laboratory_results: list[dict] = Field(
        default_factory=list, description="Ergebnisse von Laboruntersuchungen"
    )
    each_labor_result: dict = {"parameter": str, "value": float, "unit": str}

    medical_history: str = Field(description="Krankenanamnese")

    measures_taken: list[str] = Field(default_factory=list, description="Getroffene Maßnahmen")


# ------------------------------------------------------------
# KDL: UB999999 - lung bei Diabetes mellitus, Rheumatologische Komplexbehandlung, Parkinson Komplexbehandlung Sonstige medizinische Dokumentation
# Standard: Allgemeine Krankenhaus-Dokumentationsstandards, §630f BGB Dokumentationspflicht
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class StigeMedizinischeDokumentation(KdlDocumentBase):
    diabetes_mellitus_befund: str = Field(description="Befund zum Diabetes mellitus")
    rheumatologische_komplexbehandlung_befund: str = Field(
        description="Befund zur Rheumatologischen Komplexbehandlung"
    )
    parkinson_komplexbehandlung_befund: str = Field(
        description="Befund zur Parkinson Komplexbehandlung"
    )
    sonstige_medizinische_dokumentation: str = Field(
        description="Sonstige medizinische Dokumentation"
    )


# ------------------------------------------------------------
# KDL: VL010101 - Erklärung zum Schutz von sensiblen Daten und deren Verwendung. Dekubitusrisikoeinschätzung
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class UngDekubitusrisikoeinschätzung(KdlDocumentBase):
    patient_id: int = Field(description="Patient ID")
    patient_name: str = Field(description="Patient Name")
    birth_date: str = Field(description="Birth Date")
    declaration_date: str = Field(description="Declaration Date")
    risk_assessment: bool = Field(description="Dekubitusrisikoeinschätzung")
    explanation_text: str = Field(
        description="Erklärung zum Schutz von sensiblen Daten und deren Verwendung"
    )


# ------------------------------------------------------------
# KDL: VL010102 - Blutkulturenbefund Mini Mental Status Test inkl. Uhrentest
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class UhrentestErgebnis(BaseModel):
    uhrentest_ergebnis: bool = Field(description="Ergebnis des Uhrentests")
    uhrentest_bemerkung: str = Field(default="", description="Bemerkung zum Uhrentest")


class IMentalStatusTestinklUhrentest(KdlDocumentBase):
    kdl_code: str = "VL010102"
    patient_id: int = Field(description="ID des Patienten")
    durchgefuehrt_am: datetime = Field(
        description="Datum und Uhrzeit, an dem der Test durchgeführt wurde"
    )
    durchgefuehrend_pflegefachkraft: str = Field(
        description="Name der Pflegefachkraft, die den Test durchgeführt hat"
    )
    mini_mental_status_test: int = Field(
        ge=0, le=30, description="Ergebnis des Mini Mental Status Tests"
    )
    blutkulturenbefund: list[BlutkulturErgebnis] = Field(
        default=[], description="Ergebnisse der Blutkulturenuntersuchung"
    )
    uhrentest: UhrentestErgebnis = Field(description="Ergebnisse des Uhrentests")


# ------------------------------------------------------------
# KDL: VL010103 - Ergeb
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Ergebnis(BaseModel):
    dokument_id: str = Field(description="ID des medizinischen Dokuments")
    dokument_typ: str = Field(description="Typ des medizinischen Dokuments")
    erstellungszeitpunkt: datetime = Field(
        description="Zeitpunkt der Erstellung des medizinischen Dokuments"
    )
    patienten_id: str = Field(description="ID des Patienten")
    laborwerte: list[Laborwert] = Field(
        default_factory=list, description="Laborwerte des Patienten"
    )


class Laborwert(BaseModel):
    parameter: str = Field(description="Parameter des Laborwerts")
    wert: float = Field(description="Wert des Laborparameters")


# ------------------------------------------------------------
# KDL: VL010104 - ben zur geplanten Ernährung. Ernährungsscreening
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class Ernährungsscreening(KdlDocumentBase):
    kdl_code: str = Field(default="VL010104", description="KDL Code für Ernährungsscreening")
    patient_id: int = Field(description="Patient ID")
    screening_date: str = Field(description="Datum des Ernährungsscreenings")
    weight: float = Field(description="Gewicht in kg")
    height: float = Field(description="Größe in cm")
    bmi: float = Field(description="Body Mass Index (BMI)")
    nutritional_status: str = Field(description="Nährstoffstatus")
    dietary_requirements: str = Field(description="Ernährungsbedarf")


# ------------------------------------------------------------
# KDL: VL010105 - Minuten-Gehtest Aachener Aphasie Test
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class MinutenGehtestAachenerAphasieTest(KdlDocumentBase):
    kdl_code: str = Field(
        default="VL010105", description="KDL Code für Minuten-Gehtest Aachener Aphasie Test"
    )
    patient_id: int = Field(description="Patient ID")
    test_date: str = Field(description="Datum des Tests (YYYY-MM-DD)")
    tester_name: str = Field(description="Name des Testers")
    test_duration: float = Field(description="Dauer des Tests in Minuten")
    test_score: int = Field(description="Ergebnis des Tests (0-100)")


# ------------------------------------------------------------
# KDL: VL010106 - tentypen im Rahmen der stationären Versorgung. Diese KDL ist nur in Einzelfällen zu verwenden. Bsp.: elektronischer Austausch der gesamten Patientenakte Glasgow Coma Scale
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class NPatientenakteGlasgowComaScale(KdlDocumentBase):
    dokumenttyp: str = Field(description="Typ des medizinischen Dokuments")
    patient_id: str = Field(description="Identifikationsnummer des Patienten")
    erstellungsdatum: datetime = Field(description="Datum und Uhrzeit der Erstellung des Dokuments")
    erstellender_arzt: str = Field(description="Name des erstellenden Arztes")
    diagnose: str = Field(description="Diagnose des Patienten")
    laborwerte: list[Laborwert] = Field(
        default_factory=list, description="Laborwerte des Patienten"
    )


class Laborwert(BaseModel):
    parameter: str = Field(description="Parameter des Laborwerts")
    wert: float = Field(description="Wert des Laborparameters")
    einheit: str = Field(description="Einheit des Laborparameters")


# ------------------------------------------------------------
# KDL: VL010107 - Behandlung auf einer Stroke Unit Station, unter Gewährleistung von ständiger Anwesenheit eines Neurologen, zur kontinuierlichen Betreuung und Überwachung. NIH Stroke Scale
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        orm_mode = True


class NgundÜberwachungNIHStrokeScale(KdlDocumentBase):
    patient_id: int = Field(description="Patient ID")
    treatment_start_time: datetime = Field(description="Behandlungsstartzeitpunkt")
    treatment_end_time: datetime = Field(description="Behandlungsendzeitpunkt")
    neurologist_present: bool = Field(description="Anwesenheit eines Neurologen")
    nih_stroke_scale_score: int = Field(description="NIH Stroke Scale Score")


# ------------------------------------------------------------
# KDL: VL010108 - IPSS (International Prostata Symptom Score)
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    creation_time: datetime
    creator: str


class IPSSInternationalProstataSymptomScore(KdlDocumentBase):
    kdl_code = "VL010108"
    ipss_score: int = Field(description="International Prostate Symptom Score")
    quality_of_life: int = Field(description="Quality of Life according to IPSS")
    voiding_symptoms: list[int] = Field(description="Voiding symptoms (0-5)")
    storage_symptoms: list[int] = Field(description="Storage symptoms (0-5)")
    post_micturition_symptoms: list[int] = Field(description="Post-micturition symptoms (0-5)")


# ------------------------------------------------------------
# KDL: VL010199 - Autopsiebericht, Obduktionsbericht, Ärztliche Information (Briefform) Sonstiger Assessmentbogen
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class EfformSonstigerAssessmentbogen(KdlDocumentBase):
    autopsie_befund: str = Field(description="Autopsiebefund")
    obduktionsbefund: str = Field(description="Obduktionsbefund")
    arztliche_information: str = Field(description="Ärztliche Information (Briefform)")
    sonstiger_assessmentbogen: str = Field(description="Sonstiger Assessmentbogen")


# ------------------------------------------------------------
# KDL: VL040101 - ben zur Untersuchung von kognitiven Fähigkeiten, zur Früherkennung von Demenz
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class EitenZurFueherkennungVonDemenz(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    examination_date: datetime = Field(description="Exam date")
    examiner: str = Field(description="Examiner name")
    cognitive_tests: list[CognitiveTest] = Field(
        default_factory=list, description="List of cognitive tests"
    )


class CognitiveTest(BaseModel):
    test_name: str = Field(description="Name of the cognitive test")
    test_result: float = Field(description="Result of the cognitive test")


# ------------------------------------------------------------
# KDL: VL040102 - mationen, die den Patienten über die lückenlose Anschlussversorgung nach dem Krankenhausaufenthalt aufklären. Insulinplan
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class AnschlussversorgungInsulinplan(KdlDocumentBase):
    patient_id: int = Field(description="Patient ID")
    hospital_stay_id: int = Field(description="Hospital Stay ID")
    discharge_date: str = Field(description="Discharge Date")
    insulin_plan: str = Field(description="Insulin Plan")


# ------------------------------------------------------------
# KDL: VL040199 - Checkliste zur Archivierung der Krankengeschichte Sonstige Diabetesdokumentation
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class ESonstigeDiabetesdokumentation(KdlDocumentBase):
    kdl_code: str = "VL040199"
    document_type: str = (
        "Checkliste zur Archivierung der Krankengeschichte Sonstige Diabetesdokumentation"
    )

    diabetestyp: str = Field(description="Typ des Diabetes")
    blutzuckerwerte: list = Field(description="Blutzuckerwerte")
    laborwerte: dict = Field(description="Laborwerte")


# ------------------------------------------------------------
# KDL: VL040201 - ben über die Aufklärung der geplanten Diagnostik, inklusive anamnestischer Erhebungen. Dialyseanforderung
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class ErErhebungenDialyseanforderung(KdlDocumentBase):
    aufklärung_erfolgt: bool = Field(description="Aufklärung erfolgte")
    diagnose_code: str = Field(description="Code der geplanten Diagnostik")
    anamnese_notizen: str = Field(description="Anamnestische Erhebungen und Notizen")
    dialyse_anforderung: bool = Field(description="Dialyseanforderung besteht")


# ------------------------------------------------------------
# KDL: VL040202 - Dialyseprotokoll
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class Dialyseprotokoll(KdlDocumentBase):
    kdl_code: str = "VL040202"
    document_type: str = "Dialyseprotokoll"

    patient_id: str = Field(description="Patienten-ID")
    treatment_date: str = Field(description="Behandlungsdatum")
    treatment_time_start: str = Field(description="Behandlungsbeginn")
    treatment_time_end: str = Field(description="Behandlungsende")

    access_type: str = Field(description="Art des Zugangs")
    blood_flow_rate: float = Field(description="Blutflußrate in ml/min")
    dialysate_flow_rate: float = Field(description="Dialysatflußrate in ml/min")
    treatment_time: int = Field(description="Behandlungsdauer in Minuten")

    weight_pre: float = Field(description="Gewicht vor der Behandlung in kg")
    weight_post: float = Field(description="Gewicht nach der Behandlung in kg")
    weight_loss: float = Field(description="Gewichtsverlust während der Behandlung in kg")

    blood_pressure_systolic: int = Field(description="Blutdruck systolisch in mmHg")
    blood_pressure_diastolic: int = Field(description="Blutdruck diastolisch in mmHg")

    class Config:
        schema_extra = {
            "example": {
                "kdl_code": "VL040202",
                "document_type": "Dialyseprotokoll",
                "patient_id": "1234567890",
                "treatment_date": "2022-01-01",
                "treatment_time_start": "10:00",
                "treatment_time_end": "12:00",
                "access_type": "veneöser Zugang",
                "blood_flow_rate": 300.0,
                "dialysate_flow_rate": 500.0,
                "treatment_time": 120,
                "weight_pre": 75.0,
                "weight_post": 72.0,
                "weight_loss": 3.0,
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
            }
        }


# ------------------------------------------------------------
# KDL: VL040299 - Diabetologische Empfehlungen, Diabetesberatung Sonstige Dialysedokumentation
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")


class NgSonstigeDialysedokumentation(KdlDocumentBase):
    diabetologische_empfehlungen: str = Field(description="Diabetologische Empfehlungen")
    diabetesberatung_sonstige: str = Field(description="Sonstige Diabetesberatung")
    dialysedokumentation: str = Field(description="Dialysedokumentation")


# ------------------------------------------------------------
# KDL: VL040301 - management darstellen«
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        allow_population_by_field_name = True


class Managementdarstellen(KdlDocumentBase):
    dokument_id: str = Field(description="Identifikationsnummer des Dokuments")
    erstellungszeitpunkt: datetime = Field(description="Zeitpunkt der Erstellung des Dokuments")
    autor_id: str = Field(description="Identifikationsnummer des Autors")
    autor_name: str = Field(description="Name des Autors")
    patient_id: str = Field(description="Identifikationsnummer des Patienten")
    patient_name: str = Field(description="Name des Patienten")
    pflegemaßnahmen: list[Pflegemaßnahme] = Field(
        default_factory=list, description="Liste der Pflegemaßnahmen"
    )


class Pflegemaßnahme(BaseModel):
    maßnahmencode: str = Field(description="Code der Pflegemaßnahme")
    maßnahmentitel: str = Field(description="Titel der Pflegemaßnahme")
    maßnahmedetails: str = Field(description="Details zur Pflegemaßnahme")


# ------------------------------------------------------------
# KDL: VL040302 - Informationsaustausch per Fax – direkt elektronisch oder ausgedruckt in Papierkrankenakte - die nicht in einer spezifischeren KDL dieser Unterklasse abgebildet werden kann. Fixierungsprotokoll
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        orm_mode = True


class TwerdenkannFixierungsprotokoll(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code für das medizinische Dokument")
    fax_empfaenger: str = Field(description="Empfänger des Faxes")
    fax_sender: str = Field(description="Absender des Faxes")
    fixierungs_protokoll: bool = Field(description="Fixierungsprotokoll vorhanden")


# ------------------------------------------------------------
# KDL: VL040303 - ben für das Screening zur Ermittlung des geriatrischen Hilfebedarfs. Isolierungsprotokoll
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class LfebedarfsIsolierungsprotokoll(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    birth_date: str = Field(description="Geburtsdatum des Patienten")
    gender: str = Field(description="Geschlecht des Patienten")
    admission_date: str = Field(description="Einweisungsdatum")
    discharge_date: str = Field(description="Entlassungsdatum")
    reason_for_admission: str = Field(description="Grund für die Einweisung")
    diagnosis: str = Field(description="Diagnose")
    treatment: str = Field(description="Behandlung")
    isolation_protocol: bool = Field(description="Isolierungsprotokoll")
    isolation_reason: str = Field(description="Grund für Isolierung")
    isolation_start_date: str = Field(description="Beginn der Isolierung")
    isolation_end_date: str = Field(description="Ende der Isolierung")
    isolation_measures: list[str] = Field(description="Maßnahmen zur Isolierung")


# ------------------------------------------------------------
# KDL: VL040304 - Mikrobiologiebefund, Serologischer Befund Lagerungsplan
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")
    document_type: str = Field(description="Dokumenttyp")


class RologischerBefundLagerungsplan(KdlDocumentBase):
    kdl_code: str = "VL040304"
    document_type: str = "Mikrobiologiebefund, Serologischer Befund Lagerungsplan"

    patient_id: str = Field(description="Patienten-ID")
    birth_date: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")

    microbiology_results: list[dict] = Field(
        default_factory=list, description="Mikrobiologie-Ergebnisse"
    )
    serology_results: list[dict] = Field(
        default_factory=list, description="Serologische Ergebnisse"
    )
    storage_plan: dict = Field(description="Lagerungsplan")


# ------------------------------------------------------------
# KDL: VL040305 - Gesprächsinhalte, die im Rahmen einer psychologischen Therapiesitzung aufgekommen sind. Punktionsprotokoll
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class GekommenSindPunktionsprotokoll(KdlDocumentBase):
    dokumenttyp: str = Field(description="Typ des Dokuments")
    patient_id: str = Field(description="ID des Patienten")
    therapist_id: str = Field(description="ID des Therapeuten")
    therapiebeginn: datetime = Field(description="Beginn der Therapie")
    therapiedauer: int = Field(description="Dauer der Therapie in Minuten")
    anamnese: str = Field(description="Anamnese des Patienten")
    diagnose: str = Field(description="Diagnose des Patienten")
    behandlungsplan: str = Field(description="Behandlungsplan für den Patienten")
    therapiefortschritt: str = Field(description="Therapiefortschritt des Patienten")
    punkteprotokoll: list[dict] = Field(description="Punktionsprotokoll der Therapie")


# ------------------------------------------------------------
# KDL: VL040307 - nukliden Reanimationsprotokoll
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code")


class NuklidenReanimationsprotokoll(KdlDocumentBase):
    patient_id: str = Field(description="Patienten-ID")
    reanimation_datum: datetime = Field(description="Datum der Reanimation")
    herz_lungengerate_vorhanden: bool = Field(description="Herz-Lungen-Gerät vorhanden")
    defibrillation_durchgeführt: bool = Field(description="Defibrillation durchgeführt")
    medikamente_verabreicht: list[str] = Field(description="Verabreichte Medikamente")
    laborwerte: list[Laborwert] = Field(description="Laborwerte")


class Laborwert(BaseModel):
    parameter: str = Field(description="Laborparameter")
    wert: float = Field(description="Wert des Parameters")


# ------------------------------------------------------------
# KDL: VL040308 - nisse einer Untersuchung, bei der das Blut auf Antigene und Antikörper getestet wird. Sondenplan
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class IkoerpergetestetwirdSondenplan(KdlDocumentBase):
    patient_id: int = Field(description="Patient ID")
    examination_date: str = Field(description="Exam date (YYYY-MM-DD)")
    lab_results: list[LabResult] = Field(default_factory=list, description="Labor results")


class LabResult(BaseModel):
    test_name: str = Field(description="Name of the test")
    result_value: float = Field(description="Test result value")
    unit_of_measurement: str = Field(description="Unit of measurement")


# ------------------------------------------------------------
# KDL: VL040309 - KIS definierten Behandlungsablauf. Elektronische Dokumentation, ggf. informativer Ausdruck in Papierkrankenakte. Behandlungsplan
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class PierkrankenakteBehandlungsplan(KdlDocumentBase):
    behandlungscode: str = Field(description="KDL-Code für den Behandlungsablauf")
    behandlungstitel: str = Field(description="Titel des Behandlungsplans")
    beginn_datum: datetime = Field(description="Beginn des Behandlungsplans")
    ende_datum: datetime | None = Field(default=None, description="Ende des Behandlungsplans")
    behandlungsschritte: list[Behandlungsschritt] = Field(
        description="Liste der Behandlungsschritte"
    )


class Behandlungsschritt(BaseModel):
    schritt_nummer: int = Field(description="Nummer des Behandlungsschritts")
    beschreibung: str = Field(description="Beschreibung des Behandlungsschritts")
    durchgefuehrt_am: datetime | None = Field(
        default=None, description="Datum, an dem der Schritt durchgeführt wurde"
    )


# ------------------------------------------------------------
# KDL: VL040310 - Infektionsdokumentationsbogen
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class Infektionsdokumentationsbogen(KdlDocumentBase):
    kdl_code: str = "VL040310"
    document_type: str = "Infektionsdokumentationsbogen"

    patient_id: str = Field(description="Patienten-ID")
    diagnosis_date: str = Field(description="Diagnosestellungsdatum")
    symptoms: list[str] = Field(description="Symptome")
    laboratory_findings: list["Laborwert"] = Field(description="Laborbefunde")


class Laborwert(BaseModel):
    parameter: str = Field(description="Laborparameter")
    value: float | int = Field(description="Wert des Parameters")
    unit: str = Field(description="Einheit des Wertes")


# ------------------------------------------------------------
# KDL: VL040311 - ben zur Beurteilung eines akut aufgetretenen Schlaganfalls
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str
    creation_time: datetime
    author: str


class AkutaufgetretenenSchlaganfalls(KdlDocumentBase):
    kdl_code = "VL040311"
    patient_id: UUID = Field(description="Patient ID")
    admission_date: date = Field(description="Einweisungsdatum")
    symptoms_onset_time: datetime = Field(description="Symptombeginn")
    initial_assessment: str = Field(description="Erste Beurteilung")
    neurological_status_on_admission: dict = Field(
        description="Neurologischer Status bei Einlieferung"
    )
    laboratory_results: list[dict] = Field(description="Laborbefunde")
    imaging_findings: list[str] = Field(description="Befunde aus bildgebenden Verfahren")
    treatment_plan: str = Field(description="Behandlungsplan")
    discharge_summary: str = Field(description="Entlassungsbericht")


# ------------------------------------------------------------
# KDL: VL040312 - zusammengefasst administrative und persönliche Daten im Überblick. Stomadokumentation
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class NimÜberblickStomadokumentation(KdlDocumentBase):
    patient_id: int = Field(..., description="Patient ID")
    birth_date: str = Field(..., description="Geburtsdatum")
    sex: str = Field(..., description="Geschlecht")
    address: str = Field(..., description="Adresse")
    phone_number: str = Field(..., description="Telefonnummer")
    email: str | None = Field(None, description="E-Mail-Adresse")


# ------------------------------------------------------------
# KDL: VL040313 - Katheterdokument
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")
    document_type: str = Field(description="Document Type")


class Katheterdokument(KdlDocumentBase):
    kdl_code: str = "VL040313"
    document_type: str = "Katheterdokument"

    katheter_typ: str = Field(description="Typ des Katheters")
    katheter_laenge: float = Field(description="Laenge des Katheters in cm")
    einlage_datum: datetime = Field(description="Datum der Einlage")
    entfernung_datum: datetime | None = Field(default=None, description="Datum der Entfernung")
    komplikationen: list[str] = Field(
        default_factory=list, description="Komplikationen waehrend der Katheterisierung"
    )


# ------------------------------------------------------------
# KDL: VL040314 - ben zur Art und Dauer der Isolierungsmaßnahmen während der Behandlung. Kardioversion
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des medizinischen Dokuments")


class RendderBehandlungKardioversion(KdlDocumentBase):
    art_der_isolierung: str = Field(description="Art der Isolierungsmaßnahme")
    dauer_der_isolierung: int = Field(description="Dauer der Isolierungsmaßnahme in Tagen")
    beginn_datum: str = Field(description="Beginn der Isolierungsmaßnahme im Format TT.MM.JJJJ")
    ende_datum: str = Field(description="Ende der Isolierungsmaßnahme im Format TT.MM.JJJJ")


# ------------------------------------------------------------
# KDL: VL040399 - Sonstiger Durchführungsnachweis
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code des Dokuments")
    document_type: str = Field(description="Typ des Dokuments")


class SonstigerDurchführungsnachweis(KdlDocumentBase):
    kdl_code: str = "VL040399"
    document_type: str = "Sonstiger Durchführungsnachweis"

    durchgeführte_leistung: str = Field(description="Beschreibung der durchgeführten Leistung")
    durchführender_ärztlicher_dienst: str = Field(description="Durchführender ärztlicher Dienst")
    durchführungstag: date = Field(description="Datum der Durchführung")


# ------------------------------------------------------------
# KDL: VL090101 - ben zur Ermittlung der eventuell benötigten Hilfestellung im Alltag
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------


from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class EnötigtenHilfestellungimAlltag(KdlDocumentBase):
    dokument_id: str = Field(description="ID des Dokuments")
    erstellungszeitpunkt: datetime = Field(description="Zeitpunkt der Erstellung des Dokuments")
    patient_information: PatientInformation = Field(description="Patienteninformationen")
    hilfestellung_im_alltag: list[HilfestellungImAlltag] = Field(
        description="Hilfestellungen im Alltag"
    )


class PatientInformation(BaseModel):
    name: str = Field(description="Name des Patienten")
    geburtsdatum: date = Field(description="Geburtstag des Patienten")
    adresse: Adresse = Field(description="Adresse des Patienten")


class Adresse(BaseModel):
    strasse: str = Field(description="Straße")
    plz: str = Field(description="Postleitzahl")
    ort: str = Field(description="Ort")


class HilfestellungImAlltag(BaseModel):
    hilfsmittel: list[Hilfsmittel] = Field(description="Hilfsmittel, die benötigt werden")
    pflegemaßnahmen: list[Pflegemaßnahme] = Field(
        description="Pflegemaßnahmen, die erforderlich sind"
    )


class Hilfsmittel(BaseModel):
    bezeichnung: str = Field(description="Bezeichnung des Hilfsmittels")
    menge: int = Field(description="Menge des Hilfsmittels")


class Pflegemaßnahme(BaseModel):
    bezeichnung: str = Field(description="Bezeichnung der Pflegemaßnahme")
    häufigkeit: str = Field(description="Häufigkeit der Pflegemaßnahme")


# ------------------------------------------------------------
# KDL: VL090102 - ben zur standardisierten Erfassung unter anderem von: Vitalzeichen, Medikamentenverabreichung, Pflegemaßnahmen, Beatmungssituation und Laborwerten. Intensivkurve
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class Vitalzeichen(BaseModel):
    blutdruck: str = Field(description="Blutdruck")
    puls: int = Field(description="Puls")
    temperatur: float = Field(description="Temperatur")


class Medikamentenverabreichung(BaseModel):
    medikament: str = Field(description="Medikament")
    dosierung: str = Field(description="Dosierung")
    zeitpunkt: datetime = Field(description="Zeitpunkt der Verabreichung")


class Pflegemaßnahmen(BaseModel):
    maßnahme: str = Field(description="Pflegemaßnahme")
    durchführung: str = Field(description="Durchführung")


class Beatmungssituation(BaseModel):
    beatmungsart: str = Field(description="Beatmungsart")
    parameter: dict = Field(description="Beatmungsparameter")


class Laborwerte(BaseModel):
    wert: float = Field(description="Laborwert")
    einheit: str = Field(description="Einheit des Laborwerts")


class Intensivkurve(KdlDocumentBase):
    vitalzeichen: Vitalzeichen
    medikamentenverabreichung: list[Medikamentenverabreichung]
    pflegemaßnahmen: list[Pflegemaßnahmen]
    beatmungssituation: Beatmungssituation
    laborwerte: list[Laborwerte]


# ------------------------------------------------------------
# KDL: VL090103 - Anga
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")
    document_type: str = Field(description="Dokumenttyp")


class Anga(KdlDocumentBase):
    kdl_code: str = "VL090103"
    document_type: str = "Anga"

    class Config:
        schema_extra = {
            "example": {
                "kdl_code": "VL090103",
                "document_type": "Anga",
                # Add other relevant fields here
            }
        }


# ------------------------------------------------------------
# KDL: VL090104 - Monitoringausdruck
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")
    creation_time: datetime = Field(description="Erstellungszeitpunkt")


class Monitoringausdruck(KdlDocumentBase):
    patient_id: UUID = Field(description="Patient ID")
    encounter_id: UUID = Field(description="Begegnung ID")
    monitoring_data: list[dict] = Field(description="Monitoringdaten")
    lab_results: list[LabResult] = Field(description="Laborergebnisse")


class LabResult(BaseModel):
    test_name: str = Field(description="Name des Labortests")
    result_value: float = Field(description="Ergebniswert")
    unit_of_measurement: str = Field(description="Einheit der Messung")


# ------------------------------------------------------------
# KDL: VL090105 - ben über die Verabreichungsdauer und Verabreichungsart von Insulin. Intensivdokumentationsbogen
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class benüberdieVerabreichungsdauerundVerabreichungsartvonInsulin(
    Intensivdokumentationsbogen(KdlDocumentBase)
):
    dokumentation_id: str = Field(description="ID der Dokumentation")
    patient_id: str = Field(description="ID des Patienten")
    behandelnder_arzt: str = Field(description="Behandelnder Arzt")
    verabreichungsdauer: int = Field(description="Verabreichungsdauer in Tagen")
    verabreichungsart: str = Field(description="Verabreichungsart (z.B. subkutan, intravenös)")


# ------------------------------------------------------------
# KDL: VL090199 - Gehstreckentest Sonstiger Intensivdokumentationsbogen
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------


from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")
    document_type: str = Field(description="Dokumenttyp")


class GerIntensivdokumentationsbogen(KdlDocumentBase):
    kdl_code: str = "VL090199"
    document_type: str = "Gehstreckentest Sonstiger Intensivdokumentationsbogen"

    patient_id: int = Field(description="Patient ID")
    date_of_birth: str = Field(description="Geburtsdatum")
    sex: str = Field(description="Geschlecht")

    height: float = Field(description="Körpergröße in cm")
    weight: float = Field(description="Körpergewicht in kg")

    walking_aid: bool = Field(description="Geht der Patient mit Hilfsmitteln?")
    walking_aid_description: str = Field(description="Beschreibung des Hilfsmittels, falls ja")

    pain_level: int = Field(description="Schmerzlevel (0-10)")
    pain_location: list[str] = Field(description="Schmerzlokalisation")

    mobility_status: str = Field(description="Mobilitätsstatus")
    mobility_assessment: str = Field(description="Mobilitätsbewertung")


# ------------------------------------------------------------
# KDL: VL160101 - Implantat-Ausweis Auszug aus den medizinischen Daten
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class ImplantatAusweisAuszugausdenmedizinischenDaten(KdlDocumentBase):
    ausweisnummer: int = Field(description="Implantat-Ausweis-Nummer")
    patient_name: str = Field(description="Name des Patienten")
    patient_birthdate: str = Field(description="Geburtsdatum des Patienten")
    implantate: list[dict[str, str]] = Field(
        description="Liste der Implantate mit Typ und Seriennummer"
    )

    class Config:
        schema_extra = {
            "example": {
                "kdl_code": "VL160101",
                "ausweisnummer": 12345,
                "patient_name": "Max Mustermann",
                "patient_birthdate": "1980-01-01",
                "implantate": [
                    {"typ": "Herzschrittmacher", "seriennummer": "ABC123"},
                    {"typ": "Hüftimplantat", "seriennummer": "DEF456"},
                ],
            }
        }


# ------------------------------------------------------------
# KDL: VL160102 - Ernährungsplan
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Ernahrungsplan(KdlDocumentBase):
    kdl_code: str = Field(default="VL160102", const=True)
    patient_id: UUID = Field(description="Patient ID")
    creation_time: datetime = Field(description="Erstellungsdatum und -zeit")
    responsible_practitioner: dict = Field(description="Verantwortlicher Arzt/Pflegekraft")
    feeding_type: str = Field(description="Art der Ernährung (z.B. oral, sondennahrung)")
    meal_frequency: int = Field(description="Häufigkeit der Mahlzeiten pro Tag")
    caloric_intake: float = Field(description="Kalorienbedarf pro Tag in kcal")
    protein_intake: float = Field(description="Eiweißbedarf pro Tag in g")
    fluid_intake: float = Field(description="Flüssigkeitsbedarf pro Tag in ml")
    additional_instructions: str = Field(
        description="Zusätzliche Anweisungen (z.B. bei Nahrungsmittelunverträglichkeiten)"
    )


# ------------------------------------------------------------
# KDL: VL160104 - Szintigraphie Pflegeanamnesebogen
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class SzintigraphiePflegeanamnesebogen(KdlDocumentBase):
    patient_id: UUID = Field(description="Patienten-ID")
    birth_date: date = Field(description="Geburtsdatum des Patienten")
    examination_date: date = Field(description="Datum der Untersuchung")
    examination_type: str = Field(description="Art der Untersuchung (Szintigraphie)")
    symptoms: list[str] = Field(description="Symptome des Patienten")
    medical_history: Dict[str, bool] = Field(description="Vorerkrankungen und Medikamente")
    current_medication: list[str] = Field(description="Aktuelle Medikation")
    allergies: list[str] = Field(description="Allergien des Patienten")
    laboratory_results: list[Laborwert] = Field(description="Ergebnisse der Laboruntersuchungen")


class Laborwert(BaseModel):
    parameter: str = Field(description="Parameter der Untersuchung")
    value: float = Field(description="Wert des Parameters")
    unit: str = Field(description="Einheit des Wertes")


# ------------------------------------------------------------
# KDL: VL160105 - ben zum aktuellen Pflegezustand bei Aufnahme. Pflegebericht
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    creation_time: datetime = Field(description="Erstellungszeitpunkt des Dokuments")


class Pflegebericht(KdlDocumentBase):
    pflegezustand_bei_aufnahme: str = Field(description="Pflegezustand bei Aufnahme")
    pflegemaßnahmen: list[str] = Field(description="Durchgeführte Pflegemaßnahmen")
    pflegebedarf: str = Field(description="Pflegebedarf nach SGB XI")


# ------------------------------------------------------------
# KDL: VL160106 - Beispiel 4 »Klassierungshilfe über die Beschreibung des KDL-Typs«
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------


from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class UeberDieBeschreibungDesKDLTyps(KdlDocumentBase):
    kdl_code: str = Field(description="KDL-Code")
    dokument_titel: str = Field(description="Dokument-Titel")
    beschreibung_kdl_type: str = Field(description="Beschreibung des KDL-Typs")
    klassierungshilfe: list[str] = Field(
        description="Klassierungshilfe über die Beschreibung des KDL-Typs"
    )


# ------------------------------------------------------------
# KDL: VL160107 - Pflegeplanung
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Pflegeplanung(KdlDocumentBase):
    dokument_id: UUID = Field(description="Identifikationsnummer des Dokuments")
    erstellungszeitpunkt: datetime = Field(description="Zeitpunkt der Erstellung des Dokuments")
    erstellender_akteur: str = Field(
        description="Identifikation des Akteurs, der das Dokument erstellt hat"
    )
    patient_id: UUID = Field(description="Identifikationsnummer des Patienten")
    pflegeplanungs_datum: date = Field(description="Datum der Pflegeplanung")
    pflegemaßnahmen: list[Pflegemaßnahme] = Field(
        default_factory=list, description="Liste der geplanten Pflegemaßnahmen"
    )
    pflegeziele: list[Pflegeziel] = Field(
        default_factory=list, description="Liste der definierten Pflegeziele"
    )


class Pflegemaßnahme(BaseModel):
    maßnahmencode: str = Field(description="Code für die Pflegemaßnahme")
    maßnahmentitel: str = Field(description="Titel der Pflegemaßnahme")
    maßnahmedetails: str = Field(description="Details zur Pflegemaßnahme")


class Pflegeziel(BaseModel):
    zielcode: str = Field(description="Code für das Pflegeziel")
    zieltitel: str = Field(description="Titel des Pflegeziels")
    zieldetails: str = Field(description="Details zum Pflegeziel")


# ------------------------------------------------------------
# KDL: VL160108 - disierte Vorga
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class DisierteVorga(KdlDocumentBase):
    dokumenttyp: str = Field(
        default="VL160108", description="KDL-Code für die disiderte Vorgangsdokumentation"
    )
    patient_id: UUID = Field(description="Patienten-ID des ISiK-Patienten")
    erstellungszeitpunkt: datetime = Field(
        description="Erstellungsdatum und -uhrzeit der Vorgangsaufnahme"
    )
    erstellender_benutzer: str = Field(description="Benutzername des Erstellers")
    pflegende_person: str = Field(description="Name der pflegenden Person")
    pflegeeinheit: str = Field(description="Pflegeeinheit, in der die Pflege stattfindet")
    pflegemaßnahmen: list[dict] = Field(
        default=[], description="Tabelle mit den durchgeführten Pflegemaßnahmen"
    )
    laborwerte: list[dict] = Field(default=[], description="Tabelle mit Laborwerten des Patienten")


# ------------------------------------------------------------
# KDL: VL160109 - öffentlichung einer durchgeführten Studie. Sturzprotokoll
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class Sturzprotokoll(KdlDocumentBase):
    patient_id: str = Field(description="Patient ID")
    sturz_datum: datetime = Field(description="Sturz Datum")
    sturz_ort: str = Field(description="Sturz Ort")
    verletzungen: list[str] = Field(description="Verletzungen")
    behandlung: str = Field(description="Behandlung")


# ------------------------------------------------------------
# KDL: VL160110 - ben zur Erfassung der Tumorposition – überwiegend manuelle Skizze. Überwachungsprotokoll
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class TumorPositionEntry(BaseModel):
    tumor_position: str = Field(description="Tumorposition")
    manual_sketch: bool = Field(description="Überwiegend manuelle Skizze")


class TumorMonitoringProtocol(KdlDocumentBase):
    entries: list[TumorPositionEntry] = Field(description="Einträge zur Überwachung des Tumors")


# ------------------------------------------------------------
# KDL: VL160111 - frage zur Übernahme der Kosten bei Weiterführung der Behandlung/Rehabilitation. Verlaufsdokumentationsbogen
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL-Code des Dokuments")
    document_type: str = Field(description="Art des Dokuments")


class IonVerlaufsdokumentationsbogen(KdlDocumentBase):
    kdl_code: str = "VL160111"
    document_type: str = (
        "Frage zur Übernahme der Kosten bei Weiterführung der Behandlung/Rehabilitation"
    )

    patient_id: int = Field(description="Patienten-Identifikationsnummer")
    treatment_phase: str = Field(description="Behandlungsphase")
    rehabilitation_needed: bool = Field(description="Benötigt Rehabilitation")
    rehabilitation_type: str = Field(description="Art der Rehabilitation")
    rehabilitation_duration: int = Field(description="Dauer der Rehabilitation in Tagen")


# ------------------------------------------------------------
# KDL: VL160112 - ben zu sämtlichen pflegerelevanten Daten in Abhängigkeit von den Defiziten und Ressourcen. Sie dienen als Grundlage für die weiterbehandelnde Einrichtung. Pflegevisite
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class NdelndeEinrichtungPflegevisite(KdlDocumentBase):
    patient_id: int = Field(description="Patient ID")
    visit_date: str = Field(description="Datum der Pflegevisite")
    defizite: list[str] = Field(description="Defizite des Patienten")
    ressourcen: dict[str, str] = Field(description="Verfügbare Ressourcen")
    pflegemaßnahmen: list[dict[str, str]] = Field(description="Pflegemaßnahmen und ihre Gründe")


# ------------------------------------------------------------
# KDL: VL160113 - »Datensatz in der elektronischen Patientenakte abgebildet werden«. (Quelle: www.mio.kbv.de Stand 17.03.2020) Fallbesprechung Bezugspflegekraft
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        orm_mode = True


class Bezugspflegekraft(KdlDocumentBase):
    pflegekrafte_id: str = Field(description="ID der Bezugspflegekraft")
    name: str = Field(description="Name der Bezugspflegekraft")
    berufstitel: str = Field(description="Berufstitel der Bezugspflegekraft")


# ------------------------------------------------------------
# KDL: VL160114 - Pflegenachweis
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class Pflegenachweis(KdlDocumentBase):
    kdl_code: str = Field(default="VL160114", const=True)
    patient_id: UUID
    care_unit: str
    care_start_date: date
    care_end_date: date | None
    care_giver: str
    care_reason: str
    care_goals: list[str]
    care_interventions: list[str]
    care_outcomes: list[str]
    care_notes: list[str]


# ------------------------------------------------------------
# KDL: VL160199 - Sonstiger Pflegedokumentationsbogen
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class SonstigerPflegedokumentationsbogen(KdlDocumentBase):
    dokumentart: str = Field(description="Art des Pflegedokuments")
    patient_id: str = Field(description="Patienten-ID")
    pflegeeinheit: str = Field(description="Pflegeeinheit")
    pflegebeginn: datetime = Field(description="Beginn der Pflege")
    pflegeende: datetime | None = Field(default=None, description="Ende der Pflege")
    pflegemaßnahmen: list[str] = Field(description="Durchgeführte Pflegemaßnahmen")
    pflegedokumentation: str = Field(description="Pflegedokumentation nach SGB XI")


# ------------------------------------------------------------
# KDL: VL230101 - Kontrolle des Geburtsund Verlaufsgewichtes im 1. Lebensjahr. Wunddokumentationsbogen
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")


class Geburtsgewicht(BaseModel):
    gewicht_in_gramm: float = Field(description="Geburtsgewicht in Gramm")
    datum_dder_stunde: str = Field(description="Datum und Uhrzeit der Geburt")


class Verlaufsgewicht(BaseModel):
    gewicht_in_gramm: float = Field(description="Verlaufsgewicht in Gramm")
    datum: str = Field(description="Datum des Verlaufsgewichts")


class WunddokumentationZeile(BaseModel):
    wundtyp: str = Field(description="Typ der Wunde")
    wundgrad: int = Field(description="Grad der Wunde (0-4)")
    wundgroesse_in_cm2: float = Field(description="Größe der Wunde in cm²")


class EnsjahrWunddokumentationsbogen(KdlDocumentBase):
    kdl_code: str = "VL230101"
    geburtsgewicht: Geburtsgewicht
    verlaufsgewichte: list[Verlaufsgewicht]
    wunddokumentation: list[WunddokumentationZeile]


# ------------------------------------------------------------
# KDL: VL230103 - digitale direkte Fotodokumentation – Schwerpunkt: Operation Fotodokumentation Wunden
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    kdl_code: str = Field(description="KDL Code")
    document_type: str = Field(description="Document Type")


class ErationFotodokumentationWunden(KdlDocumentBase):
    kdl_code: str = "VL230103"
    document_type: str = (
        "digitale direkte Fotodokumentation – Schwerpunkt: Operation Fotodokumentation Wunden"
    )

    wunde_beschreibung: str = Field(description="Beschreibung der Wunde")
    fotodokumentationen: list[dict[str, str]] = Field(
        default_factory=list, description="Liste der Fotodokumentationen"
    )

    class Config:
        orm_mode = True


# ------------------------------------------------------------
# KDL: VL230199 - Transplantationsbegleitschein, Checkliste Transplantation Sonstige Wunddokumentation
# Standard: DNQP Expertenstandards Pflege, ISiK Encounter Profil, Pflegedokumentation nach SGB XI
# ------------------------------------------------------------

from pydantic import BaseModel, Field


class KdlDocumentBase(BaseModel):
    class Config:
        extra = "forbid"


class AtionSonstigeWunddokumentation(KdlDocumentBase):
    dokument_id: int = Field(description="Dokument-ID")
    patient_id: str = Field(description="Patient-ID")
    transplantationsbegleitschein_checkliste_sonstige_wunddokumentation_datum: str = Field(
        description="Datum des Transplantationsbegleitscheins, Checkliste Transplantation Sonstige Wunddokumentation"
    )
    transplantationsbegleitschein_checkliste_sonstige_wunddokumentation_uhrzeit: str = Field(
        description="Uhrzeit des Transplantationsbegleitscheins, Checkliste Transplantation Sonstige Wunddokumentation"
    )
    transplantationsbegleitschein_checkliste_sonstige_wunddokumentation_pflegekraft_id: str = Field(
        description="ID der Pflegekraft"
    )
    transplantationsbegleitschein_checkliste_sonstige_wunddokumentation_patient_name: str = Field(
        description="Name des Patienten"
    )
    transplantationsbegleitschein_checkliste_sonstige_wunddokumentation_patient_geburtstag: str = (
        Field(description="Geburtstag des Patienten")
    )
    transplantationsbegleitschein_checkliste_sonstige_wunddokumentation_patient_gender: str = Field(
        description="Geschlecht des Patienten"
    )
    transplantationsbegleitschein_checkliste_sonstige_wunddokumentation_patient_station: str = (
        Field(description="Station des Patienten")
    )
    transplantationsbegleitschein_checkliste_sonstige_wunddokumentation_patient_room_number: int = (
        Field(description="Zimmer-Nummer des Patienten")
    )
    transplantationsbegleitschein_checkliste_sonstige_wunddokumentation_transplantationsart: str = (
        Field(description="Art der Transplantation")
    )
    transplantationsbegleitschein_checkliste_sonstige_wunddokumentation_transplantationsorgan: str = Field(
        description="Transplantiertes Organ"
    )
    transplantationsbegleitschein_checkliste_sonstige_wunddokumentation_transplantationsstatus: str = Field(
        description="Status der Transplantation"
    )
    transplantationsbegleitschein_checkliste_sonstige_wunddokumentation_wunddokumentation: list[
        dict[str, str]
    ] = Field(default_factory=list, description="Wunddokumentation")
