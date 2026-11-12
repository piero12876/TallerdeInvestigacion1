from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    DIRECTORA = "directora"
    DOCENTE = "docente"
    PSICOLOGO = "psicologo"
    ESTUDIANTE = "estudiante"


ROLE_LABELS = {
    "directora": "Directora",
    "docente": "Docente",
    "estudiante": "Estudiante",
}


class StudentStatus(str, Enum):
    ACTIVO = "activo"
    RETIRADO = "retirado"
    DESERTOR = "desertor"
    EGRESADO = "egresado"


STATUS_LABELS = {
    "activo": "Activo",
    "retirado": "Retirado",
    "desertor": "Desertor",
    "egresado": "Egresado",
}


class AttendanceStatus(str, Enum):
    PRESENTE = "presente"
    FALTA = "falta"
    TARDANZA = "tardanza"
    JUSTIFICADA = "justificada"


class RiskLevel(str, Enum):
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"


RISK_LABELS = {
    "bajo": "Riesgo bajo",
    "medio": "Riesgo medio",
    "alto": "Riesgo alto",
}

PARENTESCO_LABELS = {
    "padre": "Padre",
    "madre": "Madre",
    "abuelo": "Abuelo/a",
    "tio": "Tío/a",
    "tutor": "Tutor legal",
    "otro": "Otro",
}
LENGUA_LABELS = {
    "castellano": "Castellano",
    "quechua": "Quechua",
    "otra": "Otra",
}
VIVE_LABELS = {
    "ambos": "Ambos padres",
    "madre": "Madre",
    "padre": "Padre",
    "otros": "Otros familiares",
}
SEGURO_LABELS = {
    "sis": "SIS",
    "essalud": "EsSalud",
    "ninguno": "Ninguno",
}
TIPO_MAT_LABELS = {
    "regular": "Regular",
    "traslado": "Traslado",
    "reingreso": "Reingreso",
}
DISCAP_LABELS = {
    "ninguna": "Ninguna",
    "visual": "Visual",
    "auditiva": "Auditiva",
    "motora": "Motora",
    "otra": "Otra",
}
TURNO_LABELS = {
    "manana": "Mañana",
}


def achievement(nota: float) -> str:
    if nota >= 17:
        return "AD"
    if nota >= 14:
        return "A"
    if nota >= 11:
        return "B"
    return "C"
