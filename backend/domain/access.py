from backend.domain.enums import Role

EDITORS = {Role.DIRECTORA.value, Role.DOCENTE.value}
RISK_ROLES = {Role.DIRECTORA.value, Role.DOCENTE.value}
MODEL_ROLES = {Role.DIRECTORA.value}
USER_ADMIN_ROLES = {Role.DIRECTORA.value}
PERSONAL_ROLES = {Role.DIRECTORA.value}
SCRUM_ROLES = {Role.DIRECTORA.value}
REPORT_ROLES = {Role.DIRECTORA.value, Role.DOCENTE.value}
FOLLOW_ROLES = {Role.DIRECTORA.value, Role.DOCENTE.value}
AUDIT_ROLES = {Role.DIRECTORA.value}


def nav_for(user) -> list[dict]:
    role = user.role if hasattr(user, "role") else user
    cuenta = [
        {"href": "/cuenta", "label": "Cambiar contraseña"},
        {"href": "/logout", "label": "Salir"},
    ]
    if role == Role.ESTUDIANTE.value:
        return [
            {"group": "Portal", "links": [
                {"href": "/", "label": "Inicio"},
                {"href": "/mi-ficha", "label": "Mi ficha"},
                {"href": "/mi-boleta", "label": "Mi boleta"},
                {"href": "/mi-asistencia", "label": "Mi asistencia"},
            ]},
            {"group": "Cuenta", "links": cuenta},
        ]
    if role == Role.DOCENTE.value:
        aula = [
            {"href": "/", "label": "Inicio"},
            {"href": "/estudiantes", "label": "Matrícula"},
        ]
        profile = getattr(user, "teacher_profile", None)
        assignments = getattr(profile, "assignments", None) or []
        tutored = getattr(profile, "tutored_grades", None) or []
        if any(getattr(a, "course_id", None) for a in assignments):
            aula.append({"href": "/calificaciones", "label": "Evaluación"})
        if tutored:
            aula.append({"href": "/asistencia", "label": "Asistencia"})
        aula.extend([
            {"href": "/riesgo", "label": "Alerta temprana"},
            {"href": "/seguimientos", "label": "Seguimientos"},
            {"href": "/citas", "label": "Agenda de atención"},
            {"href": "/reportes", "label": "Reportes"},
        ])
        return [
            {"group": "Aula", "links": aula},
            {"group": "Cuenta", "links": cuenta},
        ]
    return [
        {"group": "Gestión", "links": [
            {"href": "/", "label": "Inicio"},
            {"href": "/estudiantes", "label": "Matrícula"},
            {"href": "/calificaciones", "label": "Evaluación"},
            {"href": "/asistencia", "label": "Asistencia"},
            {"href": "/riesgo", "label": "Alerta temprana"},
            {"href": "/seguimientos", "label": "Seguimientos"},
            {"href": "/citas", "label": "Agenda de atención"},
            {"href": "/reportes", "label": "Reportes"},
        ]},
        {"group": "Institución", "links": [
            {"href": "/institucion", "label": "La institución"},
            {"href": "/docentes", "label": "Personal docente"},
            {"href": "/modelo", "label": "Modelo predictivo"},
            {"href": "/usuarios", "label": "Usuarios"},
            {"href": "/auditoria", "label": "Bitácora"},
            {"href": "/scrum", "label": "Product Backlog"},
        ]},
        {"group": "Cuenta", "links": cuenta},
    ]


def can_see_risk(role: str) -> bool:
    return role in RISK_ROLES or role == Role.ESTUDIANTE.value


def can_edit_academic(role: str) -> bool:
    return role in EDITORS
