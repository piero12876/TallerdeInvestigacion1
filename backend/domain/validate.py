"""Validaciones de negocio para el sistema de la IE (padrón, notas, claves)."""

from __future__ import annotations

import re
from datetime import date

NAME_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]{2,80}$")
USER_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
WEAK_PASSWORDS = {
    "12345678",
    "password",
    "exellenti",
    "exellenti2026",
    "qwerty123",
    "abcdefgh",
}


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_iso_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def safe_next(url: str | None) -> str:
    path = (url or "").strip()
    if not path.startswith("/") or path.startswith("//") or ":" in path:
        return "/"
    if "\\" in path or "\n" in path or "\r" in path:
        return "/"
    return path[:200]


def person_name(value: str, label: str = "Nombre") -> tuple[str, str | None]:
    text = " ".join((value or "").split())
    if not text:
        return "", f"{label} es obligatorio."
    if len(text) > 80:
        return text[:80], f"{label} admite como máximo 80 caracteres."
    if any(ch.isdigit() for ch in text):
        return text, f"{label} no admite números, solo letras."
    if not NAME_RE.match(text):
        return text, f"{label} solo admite letras, espacios y tildes (mínimo 2)."
    return text, None


def optional_name(value: str, label: str = "Nombre") -> tuple[str, str | None]:
    text = " ".join((value or "").split())
    if not text:
        return "", None
    return person_name(text, label)


def dni_peru(value: str, *, required: bool = False) -> tuple[str, str | None]:
    raw = (value or "").strip()
    compact = re.sub(r"[\s-]", "", raw)
    if compact and not compact.isdigit():
        return compact[:8], "El DNI solo admite números (8 dígitos)."
    digits = compact[:8]
    if not digits:
        return "", "El DNI es obligatorio (8 dígitos)." if required else None
    if len(digits) != 8:
        return digits, "El DNI debe tener 8 dígitos."
    if digits == "00000000":
        return digits, "Ese DNI no es válido."
    return digits, None


def phone_pe(value: str) -> tuple[str, str | None]:
    raw = (value or "").strip()
    compact = re.sub(r"[\s-]", "", raw)
    if not compact:
        return "", None
    if not compact.isdigit():
        return compact[:9], "El celular solo admite números (9 dígitos, empieza con 9)."
    if len(compact) != 9 or not compact.startswith("9"):
        return compact[:9], "El celular debe tener 9 dígitos y empezar con 9."
    return compact, None


def sexo_mf(value: str) -> tuple[str, str | None]:
    raw = (value or "M").strip().upper()[:1]
    if raw not in {"M", "F"}:
        return "M", "Sexo no válido."
    return raw, None


def username_ok(value: str) -> tuple[str, str | None]:
    text = (value or "").strip().lower()
    if not USER_RE.match(text):
        return text, "El usuario usa letras, números, punto o guion (mínimo 3)."
    return text, None


def password_ok(password: str, *, username: str = "") -> str | None:
    if len(password or "") < 8:
        return "La clave debe tener al menos 8 caracteres."
    if len(password) > 80:
        return "La clave es demasiado larga."
    if username and password.lower() == username.lower():
        return "La clave no puede ser igual al usuario."
    if password.lower() in WEAK_PASSWORDS:
        return "Esa clave es demasiado predecible."
    letters = sum(ch.isalpha() for ch in password)
    digits = sum(ch.isdigit() for ch in password)
    if letters < 1 or digits < 1:
        return "La clave debe incluir letras y números."
    return None


def parse_nota(raw) -> tuple[float | None, str | None]:
    if raw in (None, ""):
        return None, None
    try:
        nota = float(str(raw).replace(",", "."))
    except (TypeError, ValueError):
        return None, "Nota no numérica."
    if nota < 0 or nota > 20:
        return None, "La nota debe estar entre 0 y 20."
    return round(nota, 1), None


def attendance_date(day: date, *, year: int, today: date | None = None) -> str | None:
    today = today or date.today()
    start = date(year, 3, 1)
    end = date(year, 12, 20)
    if day < start or day > end:
        return f"La fecha debe estar en el año lectivo {year} (marzo a diciembre)."
    if day.weekday() >= 5:
        return "El pase de lista es solo de lunes a viernes."
    if day > today:
        return "No se registra asistencia de una fecha futura."
    return None


def followup_text(value: str) -> tuple[str, str | None]:
    text = " ".join((value or "").split())
    if len(text) < 10:
        return text, "El seguimiento debe tener al menos 10 caracteres."
    return text[:2000], None


def csv_cell(value) -> str:
    text = "" if value is None else str(value)
    if text[:1] in {"=", "+", "-", "@", "\t", "\r"}:
        return f"'{text}"
    return text


def report_tipo(value: str) -> str:
    if value in {"priorizados", "rendimiento", "asistencia", "padron"}:
        return value
    return "priorizados"


def search_q(value: str) -> str:
    return (value or "").strip().replace("%", "").replace("_", "")[:80]


def risk_nivel(value: str) -> str:
    text = (value or "").strip().lower()
    return text if text in {"alto", "medio", "bajo"} else ""


def attendance_mark(value: str) -> str:
    text = (value or "").strip().lower()
    return text if text in {"presente", "falta", "tardanza", "justificada"} else ""


def birth_date(raw: str | None, *, year: int) -> tuple[date | None, str | None]:
    if not (raw or "").strip():
        return None, None
    day = parse_iso_date(raw)
    if not day:
        return None, "Fecha de nacimiento no válida."
    oldest = date(year - 14, 1, 1)
    youngest = date(year - 5, 12, 31)
    if day < oldest or day > youngest:
        return day, f"La edad debe corresponder a primaria ({year - 14}–{year - 5})."
    return day, None


ADDR_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9#°.,\- ]{4,160}$")
EMAIL_RE = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$")


def choice(value: str, allowed: dict, label: str, default: str = "") -> tuple[str, str | None]:
    text = (value or "").strip().lower()
    if not text:
        return default, None
    if text not in allowed:
        return default, f"{label} no es válido."
    return text, None


def optional_address(value: str, label: str = "Dirección") -> tuple[str, str | None]:
    text = " ".join((value or "").split())
    if not text:
        return "", None
    if len(text) > 160:
        return text[:160], f"{label} admite como máximo 160 caracteres."
    if not ADDR_RE.match(text):
        return text, f"{label} admite letras, números y # ° . , -"
    return text, None


def optional_email(value: str) -> tuple[str, str | None]:
    text = (value or "").strip().lower()
    if not text:
        return "", None
    if len(text) > 120 or not EMAIL_RE.match(text):
        return text, "El correo no es válido."
    return text, None


def optional_notes(value: str, *, limit: int = 500) -> tuple[str, str | None]:
    text = " ".join((value or "").split())
    if not text:
        return "", None
    if len(text) > limit:
        return text[:limit], f"La observación admite como máximo {limit} caracteres."
    return text, None


def enrollment_date(raw: str | None, *, year: int, today: date | None = None) -> tuple[date | None, str | None]:
    if not (raw or "").strip():
        return None, None
    day = parse_iso_date(raw)
    if not day:
        return None, "Fecha de matrícula no válida."
    today = today or date.today()
    if day < date(year, 1, 15) or day > date(year, 12, 20):
        return day, f"La fecha de matrícula debe estar en el año {year}."
    if day > today:
        return day, "La fecha de matrícula no puede ser futura."
    return day, None


def role_filter(value: str) -> str:
    text = (value or "").strip().lower()
    allowed = {"directora", "docente", "estudiante"}
    return text if text in allowed else ""
