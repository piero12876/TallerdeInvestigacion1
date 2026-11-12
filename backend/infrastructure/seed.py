from __future__ import annotations

import random
from datetime import date, timedelta

from sqlalchemy.orm import Session

from backend.config import ANIO_LECTIVO
from backend.domain.enums import AttendanceStatus, Role, StudentStatus
from backend.infrastructure.accounts import STAFF_ACCOUNTS, STUDENT_ACCOUNTS
from backend.infrastructure.database import (
    AttendanceRecord,
    BacklogItem,
    Course,
    FollowUp,
    GradeRecord,
    Prediction,
    SchoolGrade,
    Student,
    TeacherAssignment,
    TeacherProfile,
    TutoringAppointment,
    User,
)
from backend.infrastructure.security import hash_password

rng = random.Random(42)
SECTIONS = ["A", "B", "C"]
ORDINAL = {1: "1.°", 2: "2.°", 3: "3.°", 4: "4.°", 5: "5.°", 6: "6.°"}
COURSES = [
    ("COM", "Comunicación", "Comunicación"),
    ("MAT", "Matemática", "Matemática"),
    ("PSO", "Personal Social", "Personal Social"),
    ("CYT", "Ciencia y Tecnología", "Ciencia y Tecnología"),
    ("AYC", "Arte y Cultura", "Arte y Cultura"),
    ("EDF", "Educación Física", "Educación Física"),
    ("REL", "Educación Religiosa", "Educación Religiosa"),
    ("ING", "Inglés", "Inglés"),
]
NOMBRES_M = [
    "José", "Piero", "Luis", "Mateo", "Diego", "Álvaro", "Renzo", "Sebastián",
    "Andrés", "Gabriel", "Hugo", "Iván", "Marco", "Nilton", "Óscar", "Pablo",
]
NOMBRES_F = [
    "Ana", "Lucía", "Valeria", "Camila", "Fiorella", "María", "Rosa", "Elena",
    "Nicole", "Patricia", "Sofía", "Yuliana", "Karla", "Brenda", "Diana", "Estefany",
]
APELLIDOS = [
    "Quispe", "Huamán", "Rojas", "Cerrón", "Taipe", "Cóndor", "Palacios", "De la Cruz",
    "Aliaga", "Ñahui", "Poma", "Meza", "Huayta", "Vallejos", "Soto", "Gamarra",
    "Huaroc", "Limaymanta", "Vilchez", "Chávez", "Ramírez", "Torres", "Flores", "Castro",
]
TUTOR_NAMES = {
    (3, "B"): "Raúl Gamarra Huayta",
    (3, "C"): "Pilar Chávez Cerrón",
    (4, "A"): "Edwin Huaroc Torres",
    (4, "B"): "Nancy Vilchez Castro",
    (4, "C"): "Walter Limaymanta Soto",
    (5, "A"): "Gloria Ramírez Quispe",
    (5, "B"): "Ivonne Palacios Meza",
    (5, "C"): "Fredy Cóndor Rojas",
    (6, "A"): "Elena Taipe Soto",
    (6, "B"): "Marco Aliaga Huamán",
    (6, "C"): "Patricia Rojas Cerrón",
}


def _pwd(plain: str) -> str:
    return hash_password(plain)


def _full(nombres: str, apellidos: str) -> str:
    return f"{nombres} {apellidos}"


def seed_if_empty(db: Session) -> None:
    if db.query(User).first():
        return
    _seed(db)


def _make_teacher(db: Session, username: str, full_name: str, password: str, especialidad: str, dni: str) -> TeacherProfile:
    user = User(
        username=username,
        password_hash=_pwd(password),
        full_name=full_name,
        email=f"{username}@exellenti.edu.pe",
        role=Role.DOCENTE.value,
        clave_temporal="",
    )
    db.add(user)
    db.flush()
    profile = TeacherProfile(user_id=user.id, dni=dni, especialidad=especialidad)
    db.add(profile)
    db.flush()
    return profile


def _seed(db: Session) -> None:
    courses = [Course(codigo=c, nombre=n, area=a) for c, n, a in COURSES]
    db.add_all(courses)
    db.flush()
    course_map = {c.codigo: c for c in courses}
    all_codes = [c[0] for c in COURSES]

    grades: dict[tuple[int, str], SchoolGrade] = {}
    for nivel in range(1, 7):
        for seccion in SECTIONS:
            g = SchoolGrade(
                nivel=nivel,
                seccion=seccion,
                anio=ANIO_LECTIVO,
                nombre=f"{ORDINAL[nivel]} grado {seccion}",
            )
            db.add(g)
            db.flush()
            grades[(nivel, seccion)] = g

    teachers: dict[str, TeacherProfile] = {}
    for account in STAFF_ACCOUNTS:
        user = User(
            username=account["username"],
            password_hash=_pwd(account["password"]),
            full_name=account["full_name"],
            email=account.get("email", ""),
            role=account["role"],
            phone=account.get("phone", ""),
            clave_temporal="",
        )
        db.add(user)
        db.flush()
        if account["role"] == Role.DOCENTE.value:
            profile = TeacherProfile(
                user_id=user.id,
                dni=account.get("dni", ""),
                especialidad=account.get("especialidad", ""),
            )
            db.add(profile)
            db.flush()
            teachers[account["username"]] = profile

    assigned = set()

    def assign(username: str, nivel: int, seccion: str, codigos: list[str], *, tutor: bool = False) -> None:
        teacher = teachers[username]
        grade = grades[(nivel, seccion)]
        for i, codigo in enumerate(codigos):
            pair = (grade.id, course_map[codigo].id)
            if pair in assigned:
                continue
            db.add(
                TeacherAssignment(
                    teacher_id=teacher.id,
                    grade_id=grade.id,
                    course_id=course_map[codigo].id,
                    es_tutor=tutor and i == 0,
                )
            )
            assigned.add(pair)

    for account in STAFF_ACCOUNTS:
        username = account["username"]
        if account.get("aula"):
            nivel, seccion = account["aula"]
            grades[(nivel, seccion)].tutor_id = teachers[username].id
            assign(username, nivel, seccion, all_codes, tutor=True)
        elif account.get("tutor"):
            nivel, seccion = account["tutor"]
            grades[(nivel, seccion)].tutor_id = teachers[username].id
        elif account.get("areas"):
            for nivel in range(3, 7):
                for seccion in SECTIONS:
                    assign(username, nivel, seccion, account["areas"])

    for nivel in range(3, 7):
        for seccion in SECTIONS:
            grade = grades[(nivel, seccion)]
            if grade.tutor_id:
                continue
            username = f"tutor{nivel}{seccion.lower()}"
            password = f"Tut#{nivel}{seccion}Ex26"
            name = TUTOR_NAMES[(nivel, seccion)]
            teachers[username] = _make_teacher(
                db, username, name, password, f"Tutor {ORDINAL[nivel]} {seccion}", f"4451{nivel}{ord(seccion)}"
            )
            grade.tutor_id = teachers[username].id
    db.flush()

    student_logins = {item["slot"]: item for item in STUDENT_ACCOUNTS}
    used_dni: set[str] = set()

    for nivel in range(1, 7):
        for seccion in SECTIONS:
            grade = grades[(nivel, seccion)]
            for i in range(1, 9):
                sexo = "M" if i % 2 else "F"
                nombres = rng.choice(NOMBRES_M if sexo == "M" else NOMBRES_F)
                apellidos = f"{rng.choice(APELLIDOS)} {rng.choice(APELLIDOS)}"
                dni = f"8{nivel}{ord(seccion)}{i:02d}{rng.randint(10, 99)}"
                while dni in used_dni:
                    dni = f"8{nivel}{ord(seccion)}{i:02d}{rng.randint(10, 99)}"
                used_dni.add(dni)
                login = student_logins.get((nivel, seccion, i))
                user_id = None
                if login:
                    u = User(
                        username=login["username"],
                        password_hash=_pwd(login["password"]),
                        full_name=_full(nombres, apellidos),
                        role=Role.ESTUDIANTE.value,
                        email=f"{login['username']}@exellenti.edu.pe",
                        clave_temporal="",
                    )
                    db.add(u)
                    db.flush()
                    user_id = u.id
                tipo = rng.choices(["regular", "traslado", "reingreso"], weights=[85, 10, 5])[0]
                student = Student(
                    user_id=user_id,
                    codigo=f"EX{ANIO_LECTIVO}{nivel}{seccion}{i:02d}",
                    dni=dni,
                    nombres=nombres,
                    apellidos=apellidos,
                    sexo=sexo,
                    fecha_nacimiento=date(ANIO_LECTIVO - 5 - nivel, rng.randint(1, 12), rng.randint(1, 28)),
                    grade_id=grade.id,
                    apoderado=f"{rng.choice(NOMBRES_M + NOMBRES_F)} {apellidos.split()[-1]}",
                    telefono_apoderado=f"9{rng.randint(60000000, 79999999)}",
                    parentesco=rng.choice(["madre", "madre", "padre", "abuelo", "tutor"]),
                    dni_apoderado=f"4{rng.randint(1000000, 9999999)}",
                    correo_apoderado="" if rng.random() < 0.4 else f"apod{dni[1:]}@gmail.com",
                    direccion=f"{rng.choice(['Jr. Real', 'Av. Mariscal Castilla', 'Jr. Huancas', 'Av. Ferrocarril', 'Jr. Loreto'])} {rng.randint(120, 980)}",
                    distrito="El Tambo",
                    referencia=rng.choice(["Cerca al parque", "A una cuadra del mercado", "Frente a la IE", ""]),
                    tipo_matricula=tipo,
                    ie_procedencia="" if tipo != "traslado" else rng.choice(["IE 31501", "IE 30227 Santa Isabel", "IE José Carlos Mariátegui"]),
                    fecha_matricula=date(ANIO_LECTIVO, 3, rng.randint(2, 14)),
                    turno="manana",
                    lengua_materna=rng.choices(["castellano", "quechua", "otra"], weights=[70, 25, 5])[0],
                    vive_con=rng.choices(["ambos", "madre", "padre", "otros"], weights=[50, 30, 12, 8])[0],
                    seguro=rng.choices(["sis", "essalud", "ninguno"], weights=[70, 20, 10])[0],
                    nnee=rng.random() < 0.08,
                    discapacidad="ninguna" if rng.random() > 0.06 else rng.choice(["visual", "auditiva", "motora", "otra"]),
                    observaciones="",
                    estado=StudentStatus.ACTIVO.value,
                    anio_ingreso=ANIO_LECTIVO - rng.choice([0, 1]),
                    es_historico=False,
                )
                db.add(student)
                db.flush()
                profile = "alto" if i == 1 else ("medio" if i <= 5 else "bajo")
                _fill_academic(db, student, courses, profile=profile)
                db.add(
                    Prediction(
                        student_id=student.id,
                        probabilidad={"alto": 0.74, "medio": 0.42, "bajo": 0.18}[profile],
                        nivel_riesgo=profile,
                        nivel_modelo=profile,
                        prioridad=1 if i == 1 else (i if i <= 5 else 8),
                        modelo="cupo-salon",
                        vigente=True,
                    )
                )

    for i in range(1, 81):
        dropped = i <= 28
        sexo = "M" if i % 2 else "F"
        if dropped:
            profile = rng.choices(["alto", "medio", "bajo"], weights=[55, 30, 15])[0]
        else:
            profile = rng.choices(["alto", "medio", "bajo"], weights=[12, 28, 60])[0]
        student = Student(
            codigo=f"HX2025{i:03d}",
            dni=f"7{i:07d}",
            nombres=rng.choice(NOMBRES_M if sexo == "M" else NOMBRES_F),
            apellidos=f"{rng.choice(APELLIDOS)} {rng.choice(APELLIDOS)}",
            sexo=sexo,
            fecha_nacimiento=date(2014, rng.randint(1, 12), rng.randint(1, 28)),
            grade_id=grades[(rng.randint(3, 6), rng.choice(SECTIONS))].id,
            apoderado="Registro histórico",
            estado=StudentStatus.DESERTOR.value if dropped else StudentStatus.EGRESADO.value,
            anio_ingreso=2023,
            es_historico=True,
        )
        db.add(student)
        db.flush()
        _fill_academic(db, student, courses, profile=profile, days=30)

    direccion = db.query(User).filter(User.username == "directora").first()
    tutor_3a = db.query(User).filter(User.username == "hector.quispe").first()
    caso_alto = db.query(Student).filter(Student.codigo == f"EX{ANIO_LECTIVO}3A01").first()
    caso_medio = db.query(Student).filter(Student.codigo == f"EX{ANIO_LECTIVO}3A02").first()
    autor_tutor = tutor_3a or direccion
    if autor_tutor and caso_alto:
        db.add(
            FollowUp(
                student_id=caso_alto.id,
                author_id=autor_tutor.id,
                contenido="Tutoría: inasistencias reiteradas y notas en C. Coordinar con apoderado y docente de aula.",
                tipo="asistencia",
                estado="abierto",
            )
        )
    if direccion and caso_medio:
        db.add(
            FollowUp(
                student_id=caso_medio.id,
                author_id=direccion.id,
                contenido="Seguimiento preventivo: rendimiento irregular. Refuerzo en Matemática y Comunicación.",
                tipo="academico",
                estado="abierto",
            )
        )

    db.add_all(
        [
            BacklogItem(
                codigo="PBI-01",
                titulo="Gestionar información académica y de asistencia",
                sprint="Sprint 1",
                estado="Hecho",
                criterio="OE1 · registro por docente de aula o de área, según carga SIAGIE.",
            ),
            BacklogItem(
                codigo="PBI-02",
                titulo="Entrenar modelo de Machine Learning para deserción",
                sprint="Sprint 2",
                estado="Hecho",
                criterio="OE2 · Chung y Lee (2019): asistencia, tardanzas y rendimiento.",
            ),
            BacklogItem(
                codigo="PBI-03",
                titulo="Clasificar niveles de riesgo y priorizar estudiantes",
                sprint="Sprint 3",
                estado="Hecho",
                criterio="OE3 · 1 alto y 4 medio por salón; el resto en rango esperado.",
            ),
            BacklogItem(
                codigo="PBI-04",
                titulo="Evaluar el modelo con métricas de clasificación",
                sprint="Sprint 4",
                estado="Hecho",
                criterio="OE4 · Recall, Precision, F1, ROC-AUC, PR-AUC y matriz OOF.",
            ),
            BacklogItem(
                codigo="PBI-05",
                titulo="Exportar lista priorizada y gestionar matrícula mínima",
                sprint="Sprint 5",
                estado="Hecho",
                criterio="CSV de priorizados, alta/edición/baja de estudiantes y usuarios.",
            ),
            BacklogItem(
                codigo="PBI-06",
                titulo="Agendar la atención de los casos priorizados",
                sprint="Sprint 5",
                estado="Hecho",
                criterio="Citas de tutoría con motivo, estado y resultado, filtradas por salón.",
            ),
            BacklogItem(
                codigo="HU-01",
                titulo="Pasar lista del salón y justificar la inasistencia",
                sprint="Sprint 1",
                estado="Hecho",
                actor="Docente tutor",
                historia="Como docente tutor, quiero marcar presente, falta, tardanza o justificada con motivo, para que la asistencia del día quede auditada.",
                criterio="La justificada sin motivo de 8 caracteres no se guarda. No se registra sábado, domingo ni fecha futura.",
            ),
            BacklogItem(
                codigo="HU-02",
                titulo="Ver el patrón de faltas del salón",
                sprint="Sprint 1",
                estado="Hecho",
                actor="Docente tutor",
                historia="Como docente tutor, quiero ver porcentaje, racha y faltas seguidas, para decidir a quién citar.",
                criterio="Un patrón es racha de 3 faltas o asistencia menor a 85 % con al menos 10 marcas.",
            ),
            BacklogItem(
                codigo="HU-03",
                titulo="Registrar un seguimiento clasificado",
                sprint="Sprint 3",
                estado="Hecho",
                actor="Docente",
                historia="Como docente, quiero anotar una tutoría académica, de asistencia, familiar o de convivencia, para dejar constancia del caso.",
                criterio="El texto tiene al menos 10 caracteres y el caso nace abierto.",
            ),
            BacklogItem(
                codigo="HU-04",
                titulo="Cerrar o reabrir un seguimiento",
                sprint="Sprint 3",
                estado="Hecho",
                actor="Docente",
                historia="Como docente, quiero cerrar el caso cuando la familia ya fue atendida, para no mezclarlo con los pendientes.",
                criterio="Solo se cierra un seguimiento de un estudiante de la propia carga.",
            ),
            BacklogItem(
                codigo="HU-05",
                titulo="Programar la cita de atención",
                sprint="Sprint 5",
                estado="Hecho",
                actor="Dirección",
                historia="Como directora, quiero citar por salón, fecha y canal, para ordenar la tutoría de los priorizados.",
                criterio="La cita es de lunes a viernes, dentro del año lectivo y de los próximos 21 días.",
            ),
            BacklogItem(
                codigo="HU-06",
                titulo="Convertir la cita realizada en seguimiento",
                sprint="Sprint 5",
                estado="Hecho",
                actor="Docente",
                historia="Como docente, quiero que el resultado de una cita realizada abra un seguimiento familiar, para no perder el acuerdo.",
                criterio="El resultado de realizada o no asistió tiene al menos 10 caracteres.",
            ),
            BacklogItem(
                codigo="HU-07",
                titulo="Cruzar inasistencia, alerta y tutoría",
                sprint="Sprint 5",
                estado="Hecho",
                actor="Dirección",
                historia="Como directora, quiero ver quién tiene patrón de faltas y aún no tiene seguimiento ni cita, para no dejar brechas.",
                criterio="El reporte de correlación marca brecha solo si faltan ambas atenciones.",
            ),
            BacklogItem(
                codigo="HU-08",
                titulo="Consultar mi próxima tutoría",
                sprint="Sprint 5",
                estado="Hecho",
                actor="Estudiante",
                historia="Como estudiante, quiero ver la fecha de mi próxima cita, sin ver la lista de mis compañeros.",
                criterio="El portal del estudiante no abre la agenda institucional.",
            ),
        ]
    )
    _seed_citas(db)
    db.commit()


def _next_weekday(start: date, steps: int) -> date:
    day = start
    while day.weekday() >= 5:
        day += timedelta(days=1)
    left = steps
    while left > 0:
        day += timedelta(days=1)
        if day.weekday() < 5:
            left -= 1
    end = date(ANIO_LECTIVO, 12, 20)
    if day > end:
        day = end
        while day.weekday() >= 5:
            day -= timedelta(days=1)
    return day


def _seed_citas(db: Session) -> None:
    if db.query(TutoringAppointment).first():
        return
    director = db.query(User).filter_by(username="directora").first()
    students = (
        db.query(Student)
        .filter(Student.es_historico.is_(False), Student.estado == StudentStatus.ACTIVO.value)
        .order_by(Student.id.asc())
        .limit(4)
        .all()
    )
    motivos = [
        "Citar al apoderado por inasistencias reiteradas.",
        "Revisar con la familia el descenso del bimestre 2.",
        "Coordinar apoyo en matemática y comunicación.",
        "Confirmar si el traslado de IE sigue en trámite.",
    ]
    today = date.today()
    for index, student in enumerate(students):
        author_id = director.id if director else None
        grade = db.query(SchoolGrade).filter_by(id=student.grade_id).first()
        if grade and grade.tutor_id:
            tutor = db.query(TeacherProfile).filter_by(id=grade.tutor_id).first()
            if tutor:
                author_id = tutor.user_id
        if not author_id:
            continue
        db.add(
            TutoringAppointment(
                student_id=student.id,
                author_id=author_id,
                fecha=_next_weekday(today, index),
                motivo=motivos[index],
                estado="programada",
                resultado="",
            )
        )


def _fill_academic(db: Session, student: Student, courses: list[Course], *, profile: str, days: int = 42) -> None:
    if profile == "alto":
        base, spread, absence_p, late_p = rng.uniform(6.8, 9.6), 2.2, 0.30, 0.18
        drift = rng.uniform(-2.2, -0.6)
    elif profile == "medio":
        base, spread, absence_p, late_p = rng.uniform(10.5, 12.8), 1.8, 0.14, 0.12
        drift = rng.uniform(-0.8, 0.4)
    else:
        base, spread, absence_p, late_p = rng.uniform(14.2, 17.8), 1.3, 0.03, 0.05
        drift = rng.uniform(-0.2, 1.3)

    for course in courses:
        n1 = min(20, max(5, rng.gauss(base, spread)))
        n2 = min(20, max(5, n1 + drift))
        db.add(GradeRecord(student_id=student.id, course_id=course.id, bimestre=1, nota=round(n1, 1)))
        db.add(GradeRecord(student_id=student.id, course_id=course.id, bimestre=2, nota=round(n2, 1)))

    start = date(ANIO_LECTIVO, 3, 10)
    added = 0
    cursor = start
    while added < days:
        if cursor.weekday() < 5:
            roll = rng.random()
            if roll < absence_p:
                estado = AttendanceStatus.FALTA.value
            elif roll < absence_p + late_p:
                estado = AttendanceStatus.TARDANZA.value
            elif roll < absence_p + late_p + 0.03:
                estado = AttendanceStatus.JUSTIFICADA.value
            else:
                estado = AttendanceStatus.PRESENTE.value
            db.add(AttendanceRecord(student_id=student.id, fecha=cursor, estado=estado))
            added += 1
        cursor += timedelta(days=1)
