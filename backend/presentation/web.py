import csv
import io
from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from backend.config import ANIO_LECTIVO, DISTRITO, FRONTEND_DIR, INSTITUCION, PROVINCIA, SKIP_ML
from backend.domain.access import (
    AUDIT_ROLES,
    EDITORS,
    FOLLOW_ROLES,
    MODEL_ROLES,
    PERSONAL_ROLES,
    REPORT_ROLES,
    RISK_ROLES,
    SCRUM_ROLES,
    USER_ADMIN_ROLES,
    can_edit_academic,
    can_see_risk,
    nav_for,
)
from backend.domain.enums import (
    DISCAP_LABELS,
    LENGUA_LABELS,
    PARENTESCO_LABELS,
    ROLE_LABELS,
    RISK_LABELS,
    SEGURO_LABELS,
    STATUS_LABELS,
    TIPO_MAT_LABELS,
    TURNO_LABELS,
    VIVE_LABELS,
    AttendanceStatus,
    Role,
    StudentStatus,
    achievement,
)
from backend.domain.validate import (
    attendance_date,
    attendance_mark,
    birth_date,
    choice,
    csv_cell,
    dni_peru,
    enrollment_date,
    followup_text,
    followup_tipo,
    followup_estado,
    justificacion_texto,
    cita_canal,
    cita_estado,
    cita_fecha,
    cita_motivo,
    cita_resultado,
    optional_address,
    optional_email,
    optional_name,
    optional_notes,
    parse_iso_date,
    parse_nota,
    password_ok,
    person_name,
    phone_pe,
    report_tipo,
    risk_nivel,
    role_filter,
    safe_int,
    safe_next,
    search_q,
    sexo_mf,
    username_ok,
)
from backend.infrastructure.database import (
    AttendanceRecord,
    AuditLog,
    BacklogItem,
    Course,
    FollowUp,
    GradeRecord,
    ModelRun,
    Prediction,
    SchoolGrade,
    SessionLocal,
    Student,
    TeacherAssignment,
    TeacherProfile,
    TutoringAppointment,
    User,
)
from ml.engine import FEATURE_LABELS, predict_all, student_feature_map, train_and_select
from backend.infrastructure.stats import (
    academic_evolution,
    attendance_patterns,
    brechas_atencion,
    institution_snapshot,
    course_teacher_map,
    student_progress,
    teacher_panel,
    teachers_of_grade,
    tutors_by_grade,
)
from backend.infrastructure.security import (
    client_ip,
    csrf_ok,
    hash_password,
    issue_csrf,
    login_limited,
    normalize_username,
    verify_password,
)
from backend.presentation.deps import (
    current_user,
    forbidden,
    login_redirect,
    teacher_course_ids,
    teacher_grade_ids,
    teacher_tutor_grade_ids,
    visible_students_query,
)

templates = Jinja2Templates(directory=str(FRONTEND_DIR / "templates"))
templates.env.globals.update(
    institucion=INSTITUCION,
    distrito=DISTRITO,
    provincia=PROVINCIA,
    anio=ANIO_LECTIVO,
    role_labels=ROLE_LABELS,
    status_labels=STATUS_LABELS,
    risk_labels=RISK_LABELS,
    parentesco_labels=PARENTESCO_LABELS,
    lengua_labels=LENGUA_LABELS,
    vive_labels=VIVE_LABELS,
    seguro_labels=SEGURO_LABELS,
    tipo_mat_labels=TIPO_MAT_LABELS,
    discap_labels=DISCAP_LABELS,
    turno_labels=TURNO_LABELS,
    achievement=achievement,
    Role=Role,
)
router = APIRouter()


def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ctx(request: Request, user: User, **extra):
    flash = request.session.pop("flash", None)
    flash_ok = request.session.pop("flash_ok", None)
    if request.query_params.get("error") == "sin_permiso":
        flash = "No tiene permiso para ese módulo."
    return {
        "request": request,
        "user": user,
        "nav": nav_for(user),
        "flash": flash,
        "flash_ok": flash_ok,
        "csrf": issue_csrf(request),
        "can_see_risk": can_see_risk(user.role),
        **extra,
    }


def audit(db: Session, user: User | None, accion: str, detalle: str = "") -> None:
    db.add(AuditLog(user_id=user.id if user else None, accion=accion, detalle=detalle))


def reject_csrf(request: Request, fallback: str) -> RedirectResponse:
    request.session["flash"] = "La sesión expiró. Vuelva a enviar el formulario."
    return RedirectResponse(fallback, status_code=303)


def _student_values(student: Student | None = None, **overrides) -> dict:
    data = {
        "nombres": student.nombres if student else "",
        "apellidos": student.apellidos if student else "",
        "dni": student.dni if student else "",
        "sexo": student.sexo if student else "M",
        "grade_id": student.grade_id if student else 0,
        "apoderado": student.apoderado if student else "",
        "telefono_apoderado": student.telefono_apoderado if student else "",
        "fecha_nacimiento": student.fecha_nacimiento.isoformat() if student and student.fecha_nacimiento else "",
        "parentesco": student.parentesco if student else "madre",
        "dni_apoderado": student.dni_apoderado if student else "",
        "correo_apoderado": student.correo_apoderado if student else "",
        "direccion": student.direccion if student else "",
        "distrito": student.distrito if student else DISTRITO,
        "referencia": student.referencia if student else "",
        "tipo_matricula": student.tipo_matricula if student else "regular",
        "ie_procedencia": student.ie_procedencia if student else "",
        "fecha_matricula": student.fecha_matricula.isoformat() if student and student.fecha_matricula else "",
        "turno": student.turno if student else "manana",
        "lengua_materna": student.lengua_materna if student else "castellano",
        "vive_con": student.vive_con if student else "ambos",
        "seguro": student.seguro if student else "sis",
        "nnee": bool(student.nnee) if student else False,
        "discapacidad": student.discapacidad if student else "ninguna",
        "observaciones": student.observaciones if student else "",
    }
    data.update(overrides)
    return data


def _clean_student_fields(
    nombres: str,
    apellidos: str,
    dni: str,
    sexo: str,
    apoderado: str,
    telefono_apoderado: str,
    extra: dict | None = None,
) -> tuple[dict | None, str | None]:
    extra = extra or {}
    nombres, err = person_name(nombres, "Nombres")
    if err:
        return None, err
    apellidos, err = person_name(apellidos, "Apellidos")
    if err:
        return None, err
    dni, err = dni_peru(dni)
    if err:
        return None, err
    sexo, err = sexo_mf(sexo)
    if err:
        return None, err
    apoderado, err = optional_name(apoderado, "Apoderado")
    if err:
        return None, err
    telefono, err = phone_pe(telefono_apoderado)
    if err:
        return None, err
    parentesco, err = choice(extra.get("parentesco", ""), PARENTESCO_LABELS, "Parentesco")
    if err:
        return None, err
    dni_apo, err = dni_peru(extra.get("dni_apoderado", ""))
    if err:
        return None, err
    correo, err = optional_email(extra.get("correo_apoderado", ""))
    if err:
        return None, err
    direccion, err = optional_address(extra.get("direccion", ""), "Dirección")
    if err:
        return None, err
    distrito, err = optional_name(extra.get("distrito", "") or DISTRITO, "Distrito")
    if err:
        return None, err
    referencia, err = optional_address(extra.get("referencia", ""), "Referencia")
    if err:
        return None, err
    tipo, err = choice(extra.get("tipo_matricula", ""), TIPO_MAT_LABELS, "Tipo de matrícula", "regular")
    if err:
        return None, err
    procedencia, err = optional_address(extra.get("ie_procedencia", ""), "IE de procedencia")
    if err:
        return None, err
    if tipo == "traslado" and not procedencia:
        return None, "Indique la IE de procedencia cuando la matrícula es por traslado."
    turno, err = choice(extra.get("turno", ""), TURNO_LABELS, "Turno", "manana")
    if err:
        return None, err
    lengua, err = choice(extra.get("lengua_materna", ""), LENGUA_LABELS, "Lengua materna", "castellano")
    if err:
        return None, err
    vive, err = choice(extra.get("vive_con", ""), VIVE_LABELS, "Vive con")
    if err:
        return None, err
    seguro, err = choice(extra.get("seguro", ""), SEGURO_LABELS, "Seguro")
    if err:
        return None, err
    disc, err = choice(extra.get("discapacidad", ""), DISCAP_LABELS, "Discapacidad", "ninguna")
    if err:
        return None, err
    notas, err = optional_notes(extra.get("observaciones", ""))
    if err:
        return None, err
    nnee_raw = str(extra.get("nnee") or "").strip().lower()
    return {
        "nombres": nombres,
        "apellidos": apellidos,
        "dni": dni,
        "sexo": sexo,
        "apoderado": apoderado,
        "telefono_apoderado": telefono,
        "parentesco": parentesco,
        "dni_apoderado": dni_apo,
        "correo_apoderado": correo,
        "direccion": direccion,
        "distrito": distrito,
        "referencia": referencia,
        "tipo_matricula": tipo,
        "ie_procedencia": procedencia,
        "turno": turno,
        "lengua_materna": lengua,
        "vive_con": vive,
        "seguro": seguro,
        "nnee": nnee_raw in {"1", "on", "true", "si", "sí"},
        "discapacidad": disc,
        "observaciones": notas,
    }, None


def _dni_taken(db: Session, dni: str, exclude_id: int | None = None) -> bool:
    if not dni:
        return False
    query = db.query(Student).filter(Student.dni == dni)
    if exclude_id:
        query = query.filter(Student.id != exclude_id)
    return query.first() is not None


def _activos(query):
    return query.filter(Student.estado == StudentStatus.ACTIVO.value)


def _grades_visible(db: Session, user: User, *, modo: str = "carga"):
    grades = db.query(SchoolGrade).order_by(SchoolGrade.nivel, SchoolGrade.seccion).all()
    if user.role != Role.DOCENTE.value:
        return grades
    if modo == "asistencia":
        ids = teacher_tutor_grade_ids(user)
    elif modo == "evaluacion":
        ids = {a.grade_id for a in (user.teacher_profile.assignments if user.teacher_profile else [])}
    else:
        ids = teacher_grade_ids(user)
    return [g for g in grades if g.id in ids]


def _id_in(value: int, items) -> int:
    ids = {item.id for item in items}
    return value if value in ids else 0


def _apply_student_filters(
    query,
    *,
    grado: int = 0,
    q: str = "",
    estado: str = "activo",
    sexo: str = "",
    lengua: str = "",
    tipo: str = "",
    nnee: str = "",
):
    if estado in {StudentStatus.ACTIVO.value, StudentStatus.RETIRADO.value}:
        query = query.filter(Student.estado == estado)
    elif estado not in {"todos", ""}:
        query = query.filter(Student.estado == StudentStatus.ACTIVO.value)
    if grado:
        query = query.filter(Student.grade_id == grado)
    if sexo in {"M", "F"}:
        query = query.filter(Student.sexo == sexo)
    lengua, _ = choice(lengua, LENGUA_LABELS, "Lengua")
    if lengua:
        query = query.filter(Student.lengua_materna == lengua)
    tipo, _ = choice(tipo, TIPO_MAT_LABELS, "Tipo")
    if tipo:
        query = query.filter(Student.tipo_matricula == tipo)
    flag = (nnee or "").strip().lower()
    if flag in {"1", "si", "sí", "true"}:
        query = query.filter(Student.nnee.is_(True))
    elif flag in {"0", "no"}:
        query = query.filter(Student.nnee.is_(False))
    q = search_q(q)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Student.nombres.ilike(like),
                Student.apellidos.ilike(like),
                Student.codigo.ilike(like),
                Student.dni.ilike(like),
                Student.apoderado.ilike(like),
            )
        )
    return query, q


@router.get("/login")
def login_page(request: Request, db: Session = Depends(db_session)):
    nxt = safe_next(request.query_params.get("next"))
    if current_user(request, db):
        return RedirectResponse(nxt or "/", status_code=303)
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": None,
            "csrf": issue_csrf(request),
            "next": nxt,
            "username": "",
        },
    )


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf: str = Form(""),
    next: str = Form(""),
    db: Session = Depends(db_session),
):
    nxt = safe_next(next or request.query_params.get("next"))
    login_ctx = {"request": request, "csrf": issue_csrf(request), "next": nxt, "username": username}
    if not csrf_ok(request, csrf):
        return templates.TemplateResponse(
            "login.html",
            {**login_ctx, "error": "La sesión expiró. Recargue la página."},
            status_code=400,
        )
    if login_limited(client_ip(request)):
        return templates.TemplateResponse(
            "login.html",
            {**login_ctx, "error": "Demasiados intentos. Espere unos minutos."},
            status_code=429,
        )
    username = normalize_username(username)[:80]
    login_ctx["username"] = username
    user = db.query(User).filter(User.username == username, User.is_active.is_(True)).first()
    if not user or not verify_password(password, user.password_hash):
        audit(db, user, "login_fallido", username)
        db.commit()
        return templates.TemplateResponse(
            "login.html",
            {**login_ctx, "error": "Usuario o clave incorrectos."},
            status_code=401,
        )
    request.session.clear()
    request.session["user_id"] = user.id
    issue_csrf(request)
    audit(db, user, "login", user.role)
    db.commit()
    return RedirectResponse(nxt or "/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/")
def dashboard(request: Request, db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect("/")
    if user.role == Role.ESTUDIANTE.value:
        student = _own_student(user, db)
        if not student:
            return forbidden()
        student = (
            db.query(Student)
            .options(
                joinedload(Student.grade),
                joinedload(Student.grades).joinedload(GradeRecord.course),
                joinedload(Student.attendance),
            )
            .filter(Student.id == student.id)
            .first()
        )
        pred = (
            db.query(Prediction)
            .filter(Prediction.student_id == student.id, Prediction.vigente.is_(True))
            .first()
        )
        proxima = (
            db.query(TutoringAppointment)
            .filter(
                TutoringAppointment.student_id == student.id,
                TutoringAppointment.estado == "programada",
                TutoringAppointment.fecha >= date.today(),
            )
            .order_by(TutoringAppointment.fecha.asc())
            .first()
        )
        return templates.TemplateResponse(
            "dashboard.html",
            ctx(
                request,
                user,
                student=student,
                progress=student_progress(student),
                pred=pred,
                proxima=proxima,
                tutor=tutors_by_grade(db).get(student.grade_id or 0, "Sin tutor de aula"),
                docentes_aula=teachers_of_grade(db, student.grade_id) if student.grade_id else [],
            ),
        )
    students = visible_students_query(db, user).all()
    preds = (
        db.query(Prediction)
        .options(joinedload(Prediction.student).joinedload(Student.grade))
        .filter(Prediction.vigente.is_(True))
        .order_by(Prediction.prioridad.asc())
        .all()
    )
    allowed_ids = {s.id for s in students}
    preds = [p for p in preds if p.student_id in allowed_ids]
    counts = {"alto": 0, "medio": 0, "bajo": 0}
    for p in preds:
        counts[p.nivel_riesgo] = counts.get(p.nivel_riesgo, 0) + 1
    my_assignments = []
    if user.teacher_profile:
        my_assignments = (
            db.query(TeacherAssignment)
            .options(joinedload(TeacherAssignment.grade), joinedload(TeacherAssignment.course))
            .filter(TeacherAssignment.teacher_id == user.teacher_profile.id)
            .all()
        )
    snap = institution_snapshot(db)
    citas_pendientes = (
        db.query(TutoringAppointment)
        .filter(TutoringAppointment.student_id.in_(allowed_ids or {-1}))
        .filter(TutoringAppointment.estado == "programada")
        .filter(TutoringAppointment.fecha >= date.today())
        .count()
    )
    my_salones = sorted({a.grade.nombre for a in my_assignments if a.grade})
    tutored = list(user.teacher_profile.tutored_grades) if user.teacher_profile else []
    panel = (
        teacher_panel(db, my_assignments, students, preds, tutored=tutored)
        if user.role == Role.DOCENTE.value
        else None
    )
    return templates.TemplateResponse(
        "dashboard.html",
        ctx(
            request,
            user,
            students=students,
            preds=preds[:12],
            counts=counts,
            total=len(students),
            assignments=my_assignments,
            snap=snap,
            panel=panel,
            my_salones=my_salones,
            my_cursos=len({a.course_id for a in my_assignments}),
            citas_pendientes=citas_pendientes,
        ),
    )


@router.get("/estudiantes")
def students_list(
    request: Request,
    grado: int = 0,
    q: str = "",
    estado: str = "activo",
    lengua: str = "",
    tipo: str = "",
    nnee: str = "",
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/estudiantes")
    if user.role == Role.ESTUDIANTE.value:
        return RedirectResponse("/mi-ficha", status_code=303)
    sexo = (request.query_params.get("sexo") or "").upper()[:1]
    grades = _grades_visible(db, user)
    grado = _id_in(grado, grades)
    if estado not in {StudentStatus.ACTIVO.value, StudentStatus.RETIRADO.value, "todos"}:
        estado = StudentStatus.ACTIVO.value
    nnee_flag = (nnee or "").strip().lower()
    if nnee_flag not in {"1", "0"}:
        nnee_flag = ""
    query = visible_students_query(db, user)
    query, q = _apply_student_filters(
        query, grado=grado, q=q, estado=estado, sexo=sexo, lengua=lengua, tipo=tipo, nnee=nnee_flag
    )
    rows = query.order_by(Student.apellidos, Student.nombres).all()
    lengua, _ = choice(lengua, LENGUA_LABELS, "Lengua")
    tipo, _ = choice(tipo, TIPO_MAT_LABELS, "Tipo")
    resumen = {
        "n": len(rows),
        "m": sum(1 for s in rows if s.sexo == "M"),
        "f": sum(1 for s in rows if s.sexo == "F"),
        "nnee": sum(1 for s in rows if s.nnee),
        "traslado": sum(1 for s in rows if s.tipo_matricula == "traslado"),
        "quechua": sum(1 for s in rows if s.lengua_materna == "quechua"),
    }
    return templates.TemplateResponse(
        "estudiantes.html",
        ctx(
            request,
            user,
            rows=rows,
            grades=grades,
            grado=grado,
            q=q,
            estado=estado,
            sexo=sexo if sexo in {"M", "F"} else "",
            lengua=lengua,
            tipo=tipo,
            nnee=nnee_flag,
            resumen=resumen,
            tutors=tutors_by_grade(db),
            can_manage=user.role in USER_ADMIN_ROLES,
        ),
    )


def _matricula_export_row(student: Student) -> dict:
    return {
        "codigo": student.codigo,
        "dni": student.dni or "",
        "estudiante": student.full_name,
        "sexo": student.sexo,
        "edad": student.edad if student.edad is not None else "",
        "salon": student.grade.nombre if student.grade else "",
        "tipo": TIPO_MAT_LABELS.get(student.tipo_matricula, student.tipo_matricula or ""),
        "turno": TURNO_LABELS.get(student.turno, student.turno or ""),
        "lengua": LENGUA_LABELS.get(student.lengua_materna, student.lengua_materna or ""),
        "direccion": student.direccion or "",
        "distrito": student.distrito or "",
        "apoderado": student.apoderado or "",
        "parentesco": PARENTESCO_LABELS.get(student.parentesco, student.parentesco or ""),
        "celular": student.telefono_apoderado or "",
        "correo": student.correo_apoderado or "",
        "vive_con": VIVE_LABELS.get(student.vive_con, student.vive_con or ""),
        "seguro": SEGURO_LABELS.get(student.seguro, student.seguro or ""),
        "nnee": "sí" if student.nnee else "no",
        "discapacidad": DISCAP_LABELS.get(student.discapacidad, student.discapacidad or ""),
        "estado": STATUS_LABELS.get(student.estado, student.estado),
    }


@router.get("/estudiantes/exportar")
def students_export(
    request: Request,
    grado: int = 0,
    q: str = "",
    estado: str = "activo",
    lengua: str = "",
    tipo: str = "",
    nnee: str = "",
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/estudiantes/exportar")
    if user.role == Role.ESTUDIANTE.value:
        return forbidden()
    sexo = (request.query_params.get("sexo") or "").upper()[:1]
    grades = _grades_visible(db, user)
    grado = _id_in(grado, grades)
    if estado not in {StudentStatus.ACTIVO.value, StudentStatus.RETIRADO.value, "todos"}:
        estado = StudentStatus.ACTIVO.value
    nnee_flag = (nnee or "").strip().lower()
    if nnee_flag not in {"1", "0"}:
        nnee_flag = ""
    query = visible_students_query(db, user)
    query, q = _apply_student_filters(
        query, grado=grado, q=q, estado=estado, sexo=sexo, lengua=lengua, tipo=tipo, nnee=nnee_flag
    )
    rows = query.order_by(Student.apellidos, Student.nombres).all()
    headers = [
        "codigo", "dni", "estudiante", "sexo", "edad", "salon", "tipo", "turno", "lengua",
        "direccion", "distrito", "apoderado", "parentesco", "celular", "correo",
        "vive_con", "seguro", "nnee", "discapacidad", "estado",
    ]
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(headers)
    for student in rows:
        data = _matricula_export_row(student)
        writer.writerow([csv_cell(data.get(h, "")) for h in headers])
    audit(db, user, "export_matricula", f"grado={grado}")
    db.commit()
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=padron_matricula.csv"},
    )


@router.get("/estudiantes/nuevo")
def student_new(request: Request, db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect("/estudiantes/nuevo")
    if user.role not in USER_ADMIN_ROLES:
        return forbidden()
    grades = db.query(SchoolGrade).order_by(SchoolGrade.nivel, SchoolGrade.seccion).all()
    return templates.TemplateResponse(
        "estudiante_form.html",
        ctx(request, user, student=None, grades=grades, error=None, form=_student_values()),
    )


def _ficha_extra(
    parentesco: str,
    dni_apoderado: str,
    correo_apoderado: str,
    direccion: str,
    distrito: str,
    referencia: str,
    tipo_matricula: str,
    ie_procedencia: str,
    turno: str,
    lengua_materna: str,
    vive_con: str,
    seguro: str,
    nnee: str,
    discapacidad: str,
    observaciones: str,
) -> dict:
    return {
        "parentesco": parentesco,
        "dni_apoderado": dni_apoderado,
        "correo_apoderado": correo_apoderado,
        "direccion": direccion,
        "distrito": distrito,
        "referencia": referencia,
        "tipo_matricula": tipo_matricula,
        "ie_procedencia": ie_procedencia,
        "turno": turno,
        "lengua_materna": lengua_materna,
        "vive_con": vive_con,
        "seguro": seguro,
        "nnee": nnee,
        "discapacidad": discapacidad,
        "observaciones": observaciones,
    }


@router.post("/estudiantes/nuevo")
def student_create(
    request: Request,
    nombres: str = Form(...),
    apellidos: str = Form(...),
    dni: str = Form(""),
    sexo: str = Form("M"),
    grade_id: int = Form(...),
    apoderado: str = Form(""),
    telefono_apoderado: str = Form(""),
    fecha_nacimiento: str = Form(""),
    parentesco: str = Form("madre"),
    dni_apoderado: str = Form(""),
    correo_apoderado: str = Form(""),
    direccion: str = Form(""),
    distrito: str = Form(""),
    referencia: str = Form(""),
    tipo_matricula: str = Form("regular"),
    ie_procedencia: str = Form(""),
    fecha_matricula: str = Form(""),
    turno: str = Form("manana"),
    lengua_materna: str = Form("castellano"),
    vive_con: str = Form("ambos"),
    seguro: str = Form("sis"),
    nnee: str = Form(""),
    discapacidad: str = Form("ninguna"),
    observaciones: str = Form(""),
    csrf: str = Form(""),
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/estudiantes/nuevo")
    if user.role not in USER_ADMIN_ROLES:
        return forbidden()
    if not csrf_ok(request, csrf):
        return reject_csrf(request, "/estudiantes/nuevo")
    grades = db.query(SchoolGrade).order_by(SchoolGrade.nivel, SchoolGrade.seccion).all()
    extra = _ficha_extra(
        parentesco, dni_apoderado, correo_apoderado, direccion, distrito, referencia,
        tipo_matricula, ie_procedencia, turno, lengua_materna, vive_con, seguro, nnee,
        discapacidad, observaciones,
    )
    form = _student_values(
        nombres=nombres,
        apellidos=apellidos,
        dni=dni,
        sexo=sexo,
        grade_id=grade_id,
        apoderado=apoderado,
        telefono_apoderado=telefono_apoderado,
        fecha_nacimiento=fecha_nacimiento,
        fecha_matricula=fecha_matricula,
        nnee=nnee in {"1", "on", "true", "si", "sí"},
        **{k: v for k, v in extra.items() if k != "nnee"},
    )

    def fail(msg: str):
        return templates.TemplateResponse(
            "estudiante_form.html",
            ctx(request, user, student=None, grades=grades, error=msg, form=form),
            status_code=400,
        )

    cleaned, err = _clean_student_fields(
        nombres, apellidos, dni, sexo, apoderado, telefono_apoderado, extra=extra
    )
    if err:
        return fail(err)
    nac, err = birth_date(fecha_nacimiento, year=ANIO_LECTIVO)
    if err:
        return fail(err)
    fmat, err = enrollment_date(fecha_matricula, year=ANIO_LECTIVO)
    if err:
        return fail(err)
    grade = db.query(SchoolGrade).filter(SchoolGrade.id == grade_id).first()
    if not grade:
        return fail("Seleccione un salón válido.")
    if _dni_taken(db, cleaned["dni"]):
        return fail("Ese DNI ya está registrado.")
    n_salon = db.query(Student).filter(Student.grade_id == grade.id, Student.es_historico.is_(False)).count() + 1
    codigo = f"EX{ANIO_LECTIVO}{grade.nivel}{grade.seccion}{n_salon:02d}"
    while db.query(Student).filter(Student.codigo == codigo).first():
        n_salon += 1
        codigo = f"EX{ANIO_LECTIVO}{grade.nivel}{grade.seccion}{n_salon:02d}"
    student = Student(
        codigo=codigo,
        grade_id=grade.id,
        fecha_nacimiento=nac,
        fecha_matricula=fmat,
        estado="activo",
        anio_ingreso=ANIO_LECTIVO,
        es_historico=False,
        **cleaned,
    )
    db.add(student)
    db.flush()
    audit(db, user, "estudiante_alta", codigo)
    db.commit()
    request.session["flash_ok"] = f"Matrícula {codigo} registrada."
    return RedirectResponse(f"/estudiantes/{student.id}", status_code=303)


@router.get("/estudiantes/{student_id}")
def student_detail(request: Request, student_id: int, db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect(f"/estudiantes/{student_id}")
    allowed = {s.id for s in visible_students_query(db, user).all()}
    if student_id not in allowed:
        return forbidden()
    student = (
        db.query(Student)
        .options(
            joinedload(Student.grade),
            joinedload(Student.followups).joinedload(FollowUp.author),
            joinedload(Student.grades).joinedload(GradeRecord.course),
            joinedload(Student.attendance),
        )
        .filter(Student.id == student_id)
        .first()
    )
    if not student:
        return forbidden()
    courses = db.query(Course).order_by(Course.id).all()
    records = {(r.course_id, r.bimestre): r.nota for r in student.grades}
    att = student.attendance
    summary = {
        "total": len(att),
        "presente": sum(1 for a in att if a.estado == AttendanceStatus.PRESENTE.value),
        "falta": sum(1 for a in att if a.estado == AttendanceStatus.FALTA.value),
        "tardanza": sum(1 for a in att if a.estado == AttendanceStatus.TARDANZA.value),
        "justificada": sum(1 for a in att if a.estado == AttendanceStatus.JUSTIFICADA.value),
    }
    pred = (
        db.query(Prediction)
        .filter(Prediction.student_id == student.id, Prediction.vigente.is_(True))
        .first()
    )
    return templates.TemplateResponse(
        "estudiante_detalle.html",
        ctx(
            request,
            user,
            student=student,
            courses=courses,
            records=records,
            summary=summary,
            pred=pred if user.role in {Role.DIRECTORA.value, Role.DOCENTE.value, Role.ESTUDIANTE.value} else None,
            features=student_feature_map(student) if user.role in {Role.DIRECTORA.value, Role.DOCENTE.value} and user.role != Role.ESTUDIANTE.value else {},
            feature_labels=FEATURE_LABELS,
            can_follow=user.role in FOLLOW_ROLES,
            is_portal=user.role == Role.ESTUDIANTE.value,
            tutor=tutors_by_grade(db).get(student.grade_id or 0, "Sin tutor"),
            docentes_aula=teachers_of_grade(db, student.grade_id) if student.grade_id else [],
            progress=student_progress(student),
            can_manage=user.role in USER_ADMIN_ROLES,
        ),
    )


@router.post("/estudiantes/{student_id}/seguimiento")
def add_followup(
    request: Request,
    student_id: int,
    contenido: str = Form(...),
    tipo: str = Form("academico"),
    csrf: str = Form(""),
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/")
    if user.role not in FOLLOW_ROLES:
        return forbidden()
    if not csrf_ok(request, csrf):
        return reject_csrf(request, f"/estudiantes/{student_id}")
    allowed = {s.id for s in visible_students_query(db, user).all()}
    if student_id not in allowed:
        return forbidden()
    texto, err = followup_text(contenido)
    tipo_ok = followup_tipo(tipo)
    if err or not tipo_ok:
        request.session["flash"] = err or "El tipo de seguimiento no es válido."
        return RedirectResponse(f"/estudiantes/{student_id}", status_code=303)
    db.add(FollowUp(student_id=student_id, author_id=user.id, contenido=texto, tipo=tipo_ok, estado="abierto"))
    audit(db, user, "seguimiento", str(student_id))
    db.commit()
    request.session["flash_ok"] = "Seguimiento registrado."
    return RedirectResponse(f"/estudiantes/{student_id}", status_code=303)


@router.get("/seguimientos")
def followups_list(
    request: Request,
    q: str = "",
    grado: int = 0,
    tipo: str = "",
    estado: str = "",
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/seguimientos")
    if user.role not in FOLLOW_ROLES:
        return forbidden()
    grades = _grades_visible(db, user)
    grado = _id_in(grado, grades)
    allowed = {s.id for s in visible_students_query(db, user).all()}
    notes = (
        db.query(FollowUp)
        .options(joinedload(FollowUp.student).joinedload(Student.grade), joinedload(FollowUp.author))
        .filter(FollowUp.student_id.in_(allowed or {-1}))
        .order_by(FollowUp.created_at.desc())
        .all()
    )
    if grado:
        notes = [n for n in notes if n.student and n.student.grade_id == grado]
    q = search_q(q)
    if q:
        ql = q.lower()
        notes = [
            n
            for n in notes
            if n.student
            and (
                ql in n.student.full_name.lower()
                or ql in (n.student.codigo or "").lower()
                or ql in (n.contenido or "").lower()
            )
        ]
    tipo = followup_tipo(tipo) if tipo else ""
    estado = followup_estado(estado)
    if tipo:
        notes = [n for n in notes if n.tipo == tipo]
    if estado:
        notes = [n for n in notes if n.estado == estado]
    abiertos = sum(1 for n in notes if n.estado == "abierto")
    return templates.TemplateResponse(
        "seguimientos.html",
        ctx(
            request,
            user,
            notes=notes,
            grades=grades,
            grado=grado,
            q=q,
            tipo=tipo,
            estado=estado,
            abiertos=abiertos,
        ),
    )


@router.post("/seguimientos/{note_id}/estado")
def followup_close(
    request: Request,
    note_id: int,
    estado: str = Form("cerrado"),
    csrf: str = Form(""),
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/seguimientos")
    if user.role not in FOLLOW_ROLES:
        return forbidden()
    if not csrf_ok(request, csrf):
        return reject_csrf(request, "/seguimientos")
    note = db.query(FollowUp).filter(FollowUp.id == note_id).first()
    allowed = {s.id for s in visible_students_query(db, user).all()}
    nuevo = followup_estado(estado)
    if not note or note.student_id not in allowed or not nuevo:
        return forbidden()
    note.estado = nuevo
    audit(db, user, "seguimiento", f"{nuevo} {note_id}")
    db.commit()
    request.session["flash_ok"] = "Seguimiento actualizado."
    return RedirectResponse("/seguimientos", status_code=303)


@router.get("/citas")
def citas_list(
    request: Request,
    q: str = "",
    grado: int = 0,
    estado: str = "",
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/citas")
    if user.role not in FOLLOW_ROLES:
        return forbidden()
    grades = _grades_visible(db, user)
    grado = _id_in(grado, grades)
    estado = cita_estado(estado)
    allowed = visible_students_query(db, user).all()
    allowed_ids = {s.id for s in allowed}
    rows = (
        db.query(TutoringAppointment)
        .options(
            joinedload(TutoringAppointment.student).joinedload(Student.grade),
            joinedload(TutoringAppointment.author),
        )
        .filter(TutoringAppointment.student_id.in_(allowed_ids or {-1}))
        .order_by(TutoringAppointment.fecha.asc(), TutoringAppointment.id.asc())
        .all()
    )
    if grado:
        rows = [row for row in rows if row.student and row.student.grade_id == grado]
    if estado:
        rows = [row for row in rows if row.estado == estado]
    q = search_q(q)
    if q:
        ql = q.lower()
        rows = [
            row
            for row in rows
            if row.student
            and (
                ql in row.student.full_name.lower()
                or ql in (row.student.codigo or "").lower()
                or ql in (row.motivo or "").lower()
            )
        ]
    pendientes = sum(1 for row in rows if row.estado == "programada" and row.fecha >= date.today())
    return templates.TemplateResponse(
        "citas.html",
        ctx(
            request,
            user,
            rows=rows,
            grades=grades,
            grado=grado,
            estado=estado,
            q=q,
            pendientes=pendientes,
            alumnos=allowed,
            cita_estados=("programada", "realizada", "no_asistio", "cancelada"),
        ),
    )


@router.post("/citas")
def citas_create(
    request: Request,
    student_id: int = Form(...),
    fecha: str = Form(""),
    motivo: str = Form(""),
    canal: str = Form("presencial"),
    csrf: str = Form(""),
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/citas")
    if user.role not in FOLLOW_ROLES:
        return forbidden()
    if not csrf_ok(request, csrf):
        return reject_csrf(request, "/citas")
    allowed = {s.id for s in visible_students_query(db, user).all()}
    if student_id not in allowed:
        return forbidden()
    day = parse_iso_date(fecha)
    err = cita_fecha(day, year=ANIO_LECTIVO)
    texto, motivo_err = cita_motivo(motivo)
    canal_ok = cita_canal(canal)
    if err or motivo_err or day is None or not canal_ok:
        request.session["flash"] = err or motivo_err or "El canal de la cita no es válido."
        return RedirectResponse("/citas", status_code=303)
    db.add(
        TutoringAppointment(
            student_id=student_id,
            author_id=user.id,
            fecha=day,
            motivo=texto,
            canal=canal_ok,
            estado="programada",
        )
    )
    audit(db, user, "cita", f"programada estudiante {student_id}")
    db.commit()
    request.session["flash_ok"] = "Cita de atención programada."
    return RedirectResponse("/citas", status_code=303)


@router.post("/citas/{cita_id}")
def citas_update(
    request: Request,
    cita_id: int,
    estado: str = Form(""),
    resultado: str = Form(""),
    canal: str = Form(""),
    abrir_seguimiento: str = Form(""),
    csrf: str = Form(""),
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/citas")
    if user.role not in FOLLOW_ROLES:
        return forbidden()
    if not csrf_ok(request, csrf):
        return reject_csrf(request, "/citas")
    cita = db.query(TutoringAppointment).filter(TutoringAppointment.id == cita_id).first()
    allowed = {s.id for s in visible_students_query(db, user).all()}
    if not cita or cita.student_id not in allowed:
        return forbidden()
    nuevo = cita_estado(estado)
    if not nuevo:
        request.session["flash"] = "Estado de la cita no válido."
        return RedirectResponse("/citas", status_code=303)
    texto, err = cita_resultado(nuevo, resultado)
    if err:
        request.session["flash"] = err
        return RedirectResponse("/citas", status_code=303)
    cita.estado = nuevo
    cita.resultado = texto
    canal_ok = cita_canal(canal) if canal else cita.canal
    if canal and not canal_ok:
        request.session["flash"] = "El canal de la cita no es válido."
        return RedirectResponse("/citas", status_code=303)
    if canal_ok:
        cita.canal = canal_ok
    if nuevo == "realizada" and abrir_seguimiento == "1":
        db.add(
            FollowUp(
                student_id=cita.student_id,
                author_id=user.id,
                contenido=texto,
                tipo="familiar",
                estado="abierto",
            )
        )
    audit(db, user, "cita", f"{nuevo} cita {cita_id}")
    db.commit()
    request.session["flash_ok"] = "Cita actualizada."
    return RedirectResponse("/citas", status_code=303)


@router.get("/estudiantes/{student_id}/editar")
def student_edit(request: Request, student_id: int, db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect(f"/estudiantes/{student_id}/editar")
    if user.role not in USER_ADMIN_ROLES:
        return forbidden()
    student = db.query(Student).filter(Student.id == student_id, Student.es_historico.is_(False)).first()
    if not student:
        return forbidden()
    grades = db.query(SchoolGrade).order_by(SchoolGrade.nivel, SchoolGrade.seccion).all()
    return templates.TemplateResponse(
        "estudiante_form.html",
        ctx(request, user, student=student, grades=grades, error=None, form=_student_values(student)),
    )


@router.post("/estudiantes/{student_id}/editar")
def student_update(
    request: Request,
    student_id: int,
    nombres: str = Form(...),
    apellidos: str = Form(...),
    dni: str = Form(""),
    sexo: str = Form("M"),
    grade_id: int = Form(...),
    apoderado: str = Form(""),
    telefono_apoderado: str = Form(""),
    fecha_nacimiento: str = Form(""),
    parentesco: str = Form("madre"),
    dni_apoderado: str = Form(""),
    correo_apoderado: str = Form(""),
    direccion: str = Form(""),
    distrito: str = Form(""),
    referencia: str = Form(""),
    tipo_matricula: str = Form("regular"),
    ie_procedencia: str = Form(""),
    fecha_matricula: str = Form(""),
    turno: str = Form("manana"),
    lengua_materna: str = Form("castellano"),
    vive_con: str = Form("ambos"),
    seguro: str = Form("sis"),
    nnee: str = Form(""),
    discapacidad: str = Form("ninguna"),
    observaciones: str = Form(""),
    csrf: str = Form(""),
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/")
    if user.role not in USER_ADMIN_ROLES:
        return forbidden()
    if not csrf_ok(request, csrf):
        return reject_csrf(request, f"/estudiantes/{student_id}/editar")
    student = db.query(Student).filter(Student.id == student_id, Student.es_historico.is_(False)).first()
    if not student:
        return forbidden()
    grades = db.query(SchoolGrade).order_by(SchoolGrade.nivel, SchoolGrade.seccion).all()
    extra = _ficha_extra(
        parentesco, dni_apoderado, correo_apoderado, direccion, distrito, referencia,
        tipo_matricula, ie_procedencia, turno, lengua_materna, vive_con, seguro, nnee,
        discapacidad, observaciones,
    )
    form = _student_values(
        student,
        nombres=nombres,
        apellidos=apellidos,
        dni=dni,
        sexo=sexo,
        grade_id=grade_id,
        apoderado=apoderado,
        telefono_apoderado=telefono_apoderado,
        fecha_nacimiento=fecha_nacimiento,
        fecha_matricula=fecha_matricula,
        nnee=nnee in {"1", "on", "true", "si", "sí"},
        **{k: v for k, v in extra.items() if k != "nnee"},
    )
    cleaned, err = _clean_student_fields(
        nombres, apellidos, dni, sexo, apoderado, telefono_apoderado, extra=extra
    )
    if err:
        return templates.TemplateResponse(
            "estudiante_form.html",
            ctx(request, user, student=student, grades=grades, error=err, form=form),
            status_code=400,
        )
    grade = db.query(SchoolGrade).filter(SchoolGrade.id == grade_id).first()
    if not grade:
        return templates.TemplateResponse(
            "estudiante_form.html",
            ctx(request, user, student=student, grades=grades, error="Seleccione un salón válido.", form=form),
            status_code=400,
        )
    if _dni_taken(db, cleaned["dni"], exclude_id=student.id):
        return templates.TemplateResponse(
            "estudiante_form.html",
            ctx(request, user, student=student, grades=grades, error="Ese DNI ya está registrado.", form=form),
            status_code=400,
        )
    nac, err = birth_date(fecha_nacimiento, year=ANIO_LECTIVO)
    if err:
        return templates.TemplateResponse(
            "estudiante_form.html",
            ctx(request, user, student=student, grades=grades, error=err, form=form),
            status_code=400,
        )
    fmat, err = enrollment_date(fecha_matricula, year=ANIO_LECTIVO)
    if err:
        return templates.TemplateResponse(
            "estudiante_form.html",
            ctx(request, user, student=student, grades=grades, error=err, form=form),
            status_code=400,
        )
    for key, value in cleaned.items():
        setattr(student, key, value)
    student.grade_id = grade.id
    student.fecha_nacimiento = nac
    student.fecha_matricula = fmat
    audit(db, user, "estudiante_editar", student.codigo)
    db.commit()
    request.session["flash_ok"] = "La ficha del estudiante se actualizó."
    return RedirectResponse(f"/estudiantes/{student.id}", status_code=303)


@router.post("/estudiantes/{student_id}/estado")
def student_status(
    request: Request,
    student_id: int,
    estado: str = Form(...),
    csrf: str = Form(""),
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/")
    if user.role not in USER_ADMIN_ROLES:
        return forbidden()
    if not csrf_ok(request, csrf):
        return reject_csrf(request, f"/estudiantes/{student_id}")
    if estado not in {"activo", "retirado"}:
        return forbidden()
    student = db.query(Student).filter(Student.id == student_id, Student.es_historico.is_(False)).first()
    if not student:
        return forbidden()
    student.estado = estado
    audit(db, user, "estudiante_estado", f"{student.codigo}:{estado}")
    db.commit()
    request.session["flash_ok"] = "Estado actualizado."
    return RedirectResponse(f"/estudiantes/{student.id}", status_code=303)


@router.get("/calificaciones")
def grades_page(request: Request, grado: int = 0, curso: int = 0, q: str = "", db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect("/calificaciones")
    if user.role not in EDITORS:
        return forbidden()
    if user.role == Role.DOCENTE.value and not teacher_course_ids(user):
        return forbidden()
    grades = _grades_visible(db, user, modo="evaluacion")
    courses = db.query(Course).order_by(Course.id).all()
    grado = _id_in(grado, grades)
    if user.role == Role.DOCENTE.value:
        if not grado and grades:
            grado = grades[0].id
        cids = teacher_course_ids(user, grado) if grado else teacher_course_ids(user)
        courses = [c for c in courses if c.id in cids]
    curso = _id_in(curso, courses)
    if user.role == Role.DOCENTE.value and not curso and courses:
        curso = courses[0].id
    q = search_q(q)
    students = []
    table = {}
    if grado and curso:
        students = (
            _activos(visible_students_query(db, user))
            .filter(Student.grade_id == grado)
            .order_by(Student.apellidos)
            .all()
        )
        if q:
            ql = q.lower()
            students = [s for s in students if ql in s.full_name.lower() or ql in (s.codigo or "").lower()]
        recs = (
            db.query(GradeRecord)
            .filter(GradeRecord.course_id == curso, GradeRecord.student_id.in_([s.id for s in students] or [-1]))
            .all()
        )
        table = {(r.student_id, r.bimestre): r.nota for r in recs}
    can_edit = can_edit_academic(user.role)
    evo = academic_evolution(table, students) if students else None
    missing = sum(
        1
        for s in students
        if table.get((s.id, 1)) is None or table.get((s.id, 2)) is None
    )
    return templates.TemplateResponse(
        "calificaciones.html",
        ctx(
            request,
            user,
            grades=grades,
            courses=courses,
            grado=grado,
            curso=curso,
            q=q,
            students=students,
            table=table,
            can_edit=can_edit,
            evo=evo,
            missing=missing,
        ),
    )


@router.post("/calificaciones")
async def grades_save(request: Request, db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user or not can_edit_academic(user.role):
        return forbidden() if user else login_redirect("/calificaciones")
    form = await request.form()
    if not csrf_ok(request, str(form.get("csrf") or "")):
        return reject_csrf(request, "/calificaciones")
    grado = safe_int(form.get("grado"))
    curso = safe_int(form.get("curso"))
    if not grado or not curso:
        request.session["flash"] = "Seleccione salón y área."
        return RedirectResponse("/calificaciones", status_code=303)
    if not db.query(SchoolGrade).filter(SchoolGrade.id == grado).first() or not db.query(Course).filter(Course.id == curso).first():
        request.session["flash"] = "Salón o área no válido."
        return RedirectResponse("/calificaciones", status_code=303)
    if user.role == Role.DOCENTE.value and (
        grado not in teacher_grade_ids(user) or curso not in teacher_course_ids(user, grado)
    ):
        return forbidden()
    students = _activos(visible_students_query(db, user)).filter(Student.grade_id == grado).all()
    omitted = 0
    for student in students:
        for bim in (1, 2):
            raw = form.get(f"n_{student.id}_{bim}")
            if raw in (None, ""):
                continue
            nota, err = parse_nota(raw)
            if err or nota is None:
                omitted += 1
                continue
            rec = (
                db.query(GradeRecord)
                .filter_by(student_id=student.id, course_id=curso, bimestre=bim)
                .first()
            )
            if rec:
                rec.nota = nota
                rec.registrado_por = user.id
                rec.updated_at = datetime.utcnow()
            else:
                db.add(
                    GradeRecord(
                        student_id=student.id,
                        course_id=curso,
                        bimestre=bim,
                        nota=nota,
                        registrado_por=user.id,
                    )
                )
    audit(db, user, "calificaciones", f"grado={grado},curso={curso}")
    db.commit()
    if not SKIP_ML:
        predict_all(db)
    if omitted:
        request.session["flash"] = f"Notas guardadas. Se omitieron {omitted} valor(es): solo se aceptan números de 0 a 20."
    else:
        request.session["flash_ok"] = "Notas guardadas."
    return RedirectResponse(f"/calificaciones?grado={grado}&curso={curso}", status_code=303)


@router.get("/asistencia")
def attendance_page(
    request: Request,
    grado: int = 0,
    fecha: str = "",
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/asistencia")
    if user.role not in EDITORS:
        return forbidden()
    if user.role == Role.DOCENTE.value and not teacher_tutor_grade_ids(user):
        return forbidden()
    grades = _grades_visible(db, user, modo="asistencia")
    grado = _id_in(grado, grades)
    if user.role == Role.DOCENTE.value and not grado and grades:
        grado = grades[0].id
    day = parse_iso_date(fecha) or date.today()
    students = []
    marks = {}
    if grado:
        students = (
            _activos(visible_students_query(db, user))
            .filter(Student.grade_id == grado)
            .order_by(Student.apellidos)
            .all()
        )
        recs = (
            db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.fecha == day,
                AttendanceRecord.student_id.in_([s.id for s in students] or [-1]),
            )
            .all()
        )
        marks = {r.student_id: r.estado for r in recs}
        detalles = {r.student_id: r.detalle or "" for r in recs}
    else:
        detalles = {}
    patterns = attendance_patterns(db, students) if students else None
    brechas = brechas_atencion(db, students, patterns) if students else []
    day_counts = {"presente": 0, "falta": 0, "tardanza": 0, "justificada": 0}
    for estado in marks.values():
        if estado in day_counts:
            day_counts[estado] += 1
    date_err = attendance_date(day, year=ANIO_LECTIVO)
    return templates.TemplateResponse(
        "asistencia.html",
        ctx(
            request,
            user,
            grades=grades,
            grado=grado,
            fecha=day.isoformat(),
            students=students,
            marks=marks,
            detalles=detalles,
            can_edit=can_edit_academic(user.role) and not date_err,
            patterns=patterns,
            brechas=brechas,
            day_counts=day_counts,
            date_err=date_err,
            today=date.today().isoformat(),
            fecha_min=f"{ANIO_LECTIVO}-03-01",
            fecha_max=date.today().isoformat(),
            solo_patron=request.query_params.get("patron") == "1",
        ),
    )


@router.post("/asistencia")
async def attendance_save(request: Request, db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user or not can_edit_academic(user.role):
        return forbidden() if user else login_redirect("/asistencia")
    form = await request.form()
    if not csrf_ok(request, str(form.get("csrf") or "")):
        return reject_csrf(request, "/asistencia")
    grado = safe_int(form.get("grado"))
    if not grado:
        request.session["flash"] = "Seleccione un salón."
        return RedirectResponse("/asistencia", status_code=303)
    day = parse_iso_date(str(form.get("fecha") or "")) or date.today()
    date_err = attendance_date(day, year=ANIO_LECTIVO)
    if date_err:
        request.session["flash"] = date_err
        return RedirectResponse(f"/asistencia?grado={grado}&fecha={day.isoformat()}", status_code=303)
    if user.role == Role.DOCENTE.value and grado not in teacher_tutor_grade_ids(user):
        return forbidden()
    students = _activos(visible_students_query(db, user)).filter(Student.grade_id == grado).all()
    valid = {s.value for s in AttendanceStatus}
    omitted = 0
    for student in students:
        estado = form.get(f"a_{student.id}")
        if estado not in valid:
            continue
        detalle = ""
        if estado == "justificada":
            detalle, err = justificacion_texto(str(form.get(f"j_{student.id}") or ""))
            if err:
                omitted += 1
                continue
        rec = db.query(AttendanceRecord).filter_by(student_id=student.id, fecha=day).first()
        if rec:
            rec.estado = estado
            rec.detalle = detalle
            rec.registrado_por = user.id
        else:
            db.add(
                AttendanceRecord(
                    student_id=student.id,
                    fecha=day,
                    estado=estado,
                    detalle=detalle,
                    registrado_por=user.id,
                )
            )
    audit(db, user, "asistencia", f"grado={grado},fecha={day.isoformat()}")
    db.commit()
    if not SKIP_ML:
        predict_all(db)
    if omitted:
        request.session["flash"] = (
            f"Asistencia guardada. Se omitieron {omitted} justificada(s) sin motivo de al menos 8 caracteres."
        )
    else:
        request.session["flash_ok"] = "Asistencia guardada."
    return RedirectResponse(f"/asistencia?grado={grado}&fecha={day.isoformat()}", status_code=303)


@router.get("/docentes")
def teachers_page(request: Request, q: str = "", tutor: int = 0, db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect("/docentes")
    if user.role not in PERSONAL_ROLES:
        return forbidden()
    teachers = (
        db.query(TeacherProfile)
        .options(
            joinedload(TeacherProfile.user),
            joinedload(TeacherProfile.assignments).joinedload(TeacherAssignment.grade),
            joinedload(TeacherProfile.assignments).joinedload(TeacherAssignment.course),
            joinedload(TeacherProfile.tutored_grades),
        )
        .all()
    )
    q = search_q(q)
    if q:
        ql = q.lower()
        teachers = [
            t
            for t in teachers
            if t.user
            and (
                ql in t.user.full_name.lower()
                or ql in t.user.username.lower()
                or ql in (t.especialidad or "").lower()
            )
        ]
    if tutor:
        teachers = [t for t in teachers if t.tutored_grades]
    cargas_n = sum(len(t.assignments) for t in teachers)
    tutores_n = sum(1 for t in teachers if t.tutored_grades)
    salones_n = len({a.grade_id for t in teachers for a in t.assignments})
    return templates.TemplateResponse(
        "docentes.html",
        ctx(
            request,
            user,
            teachers=teachers,
            cargas_n=cargas_n,
            tutores_n=tutores_n,
            salones_n=salones_n,
            q=q,
            tutor=bool(tutor),
        ),
    )


def _filtered_preds(db: Session, user: User, *, nivel: str = "", grado: int = 0, q: str = "", disc: bool = False):
    nivel = risk_nivel(nivel)
    students = _activos(visible_students_query(db, user))
    students, q = _apply_student_filters(students, grado=grado, q=q, estado="activo")
    allowed = {s.id for s in students.all()}
    query = (
        db.query(Prediction)
        .options(joinedload(Prediction.student).joinedload(Student.grade))
        .filter(Prediction.vigente.is_(True))
        .order_by(Prediction.prioridad.asc())
    )
    if nivel:
        query = query.filter(Prediction.nivel_riesgo == nivel)
    preds = [p for p in query.all() if p.student_id in allowed]
    if disc:
        preds = [p for p in preds if (p.nivel_modelo or "") != (p.nivel_riesgo or "")]
    return preds, nivel, q


@router.get("/riesgo")
def risk_page(
    request: Request,
    nivel: str = "",
    grado: int = 0,
    q: str = "",
    disc: int = 0,
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/riesgo")
    if user.role not in RISK_ROLES:
        return forbidden()
    grades = _grades_visible(db, user)
    grado = _id_in(grado, grades)
    preds, nivel, q = _filtered_preds(db, user, nivel=nivel, grado=grado, q=q, disc=bool(disc))
    return templates.TemplateResponse(
        "riesgo.html",
        ctx(
            request,
            user,
            preds=preds,
            nivel=nivel,
            grado=grado,
            q=q,
            disc=bool(disc),
            grades=grades,
        ),
    )


@router.get("/riesgo/exportar")
def risk_export(
    request: Request,
    nivel: str = "",
    grado: int = 0,
    q: str = "",
    disc: int = 0,
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/riesgo/exportar")
    if user.role not in RISK_ROLES:
        return forbidden()
    grades = _grades_visible(db, user)
    grado = _id_in(grado, grades)
    preds, nivel, q = _filtered_preds(db, user, nivel=nivel, grado=grado, q=q, disc=bool(disc))
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(
        ["prioridad", "codigo", "estudiante", "salon", "probabilidad", "nivel_modelo", "prioridad_atencion"]
    )
    for p in preds:
        student = p.student
        writer.writerow(
            [
                csv_cell(p.prioridad),
                csv_cell(student.codigo if student else ""),
                csv_cell(student.full_name if student else ""),
                csv_cell(student.grade.nombre if student and student.grade else ""),
                csv_cell(f"{p.probabilidad:.4f}"),
                csv_cell(p.nivel_modelo or ""),
                csv_cell(p.nivel_riesgo),
            ]
        )
    audit(db, user, "export_priorizados", f"{nivel or 'todos'}:{grado}:{q}")
    db.commit()
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=priorizados_exellenti.csv"},
    )


@router.get("/reportes")
def reports_page(
    request: Request,
    tipo: str = "priorizados",
    grado: int = 0,
    q: str = "",
    estado: str = "activo",
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/reportes")
    if user.role not in REPORT_ROLES:
        return forbidden()
    tipo = report_tipo(tipo)
    q = search_q(q)
    grades = _grades_visible(db, user)
    grado = _id_in(grado, grades)
    if estado not in {StudentStatus.ACTIVO.value, StudentStatus.RETIRADO.value, "todos"}:
        estado = StudentStatus.ACTIVO.value
    rows, title = _report_rows(db, user, tipo, grado, estado)
    if q:
        ql = q.lower()
        rows = [r for r in rows if ql in str(r.get("estudiante", "")).lower() or ql in str(r.get("codigo", "")).lower()]
    return templates.TemplateResponse(
        "reportes.html",
        ctx(
            request,
            user,
            tipo=tipo,
            grado=grado,
            q=q,
            estado=estado,
            grades=grades,
            rows=rows,
            title=title,
            headers=_report_headers(tipo),
        ),
    )


@router.get("/reportes/exportar")
def reports_export(request: Request, tipo: str = "priorizados", grado: int = 0, q: str = "", estado: str = "activo", db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect("/reportes/exportar")
    if user.role not in REPORT_ROLES:
        return forbidden()
    tipo = report_tipo(tipo)
    q = search_q(q)
    grades = _grades_visible(db, user)
    grado = _id_in(grado, grades)
    if estado not in {StudentStatus.ACTIVO.value, StudentStatus.RETIRADO.value, "todos"}:
        estado = StudentStatus.ACTIVO.value
    rows, title = _report_rows(db, user, tipo, grado, estado)
    if q:
        ql = q.lower()
        rows = [r for r in rows if ql in str(r.get("estudiante", "")).lower() or ql in str(r.get("codigo", "")).lower()]
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.writer(buf, delimiter=";")
    headers = _report_headers(tipo)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([csv_cell(row.get(h, "")) for h in headers])
    audit(db, user, "export_reporte", f"{tipo}:{grado}")
    db.commit()
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=reporte_{tipo}.csv"},
    )


def _report_headers(tipo: str) -> list[str]:
    if tipo == "rendimiento":
        return ["codigo", "estudiante", "salon", "bimestre_1", "bimestre_2", "promedio", "tendencia"]
    if tipo == "asistencia":
        return ["codigo", "estudiante", "salon", "pct_asistencia", "faltas", "tardanzas", "racha", "patron"]
    if tipo == "padron":
        return ["codigo", "estudiante", "salon", "sexo", "tipo", "lengua", "vive_con", "seguro", "nnee", "estado"]
    if tipo == "correlacion":
        return [
            "codigo",
            "estudiante",
            "salon",
            "pct_asistencia",
            "faltas",
            "racha",
            "atencion",
            "seguimiento_abierto",
            "cita_programada",
            "brecha",
        ]
    return ["prioridad", "codigo", "estudiante", "salon", "probabilidad", "nivel_modelo", "atencion"]


def _report_rows(db: Session, user: User, tipo: str, grado: int, estado: str = "activo") -> tuple[list[dict], str]:
    students = visible_students_query(db, user)
    students, _ = _apply_student_filters(students, grado=grado, estado=estado)
    students = students.order_by(Student.apellidos).all()
    allowed = {s.id for s in students}
    if tipo == "rendimiento":
        recs = db.query(GradeRecord).filter(GradeRecord.student_id.in_(allowed or {-1})).all()
        by_st: dict[int, dict[int, list[float]]] = {}
        for rec in recs:
            by_st.setdefault(rec.student_id, {}).setdefault(rec.bimestre, []).append(rec.nota)
        rows = []
        for student in students:
            bims = by_st.get(student.id, {})
            n1 = round(sum(bims.get(1, [0])) / len(bims.get(1, [1])), 1) if bims.get(1) else ""
            n2 = round(sum(bims.get(2, [0])) / len(bims.get(2, [1])), 1) if bims.get(2) else ""
            nums = [v for v in (n1, n2) if v != ""]
            prom = round(sum(nums) / len(nums), 1) if nums else ""
            tend = round(n2 - n1, 1) if n1 != "" and n2 != "" else ""
            rows.append(
                {
                    "codigo": student.codigo,
                    "estudiante": student.full_name,
                    "salon": student.grade.nombre if student.grade else "",
                    "bimestre_1": n1,
                    "bimestre_2": n2,
                    "promedio": prom,
                    "tendencia": tend,
                }
            )
        return rows, "Rendimiento por bimestre"
    if tipo == "asistencia":
        patterns = attendance_patterns(db, students)
        by_id = {row["id"]: row for row in patterns["filas"]}
        rows = []
        for student in students:
            p = by_id.get(student.id, {})
            rows.append(
                {
                    "codigo": student.codigo,
                    "estudiante": student.full_name,
                    "salon": student.grade.nombre if student.grade else "",
                    "pct_asistencia": p.get("pct", ""),
                    "faltas": p.get("faltas", ""),
                    "tardanzas": p.get("tardanzas", ""),
                    "racha": p.get("racha", ""),
                    "patron": "sí" if p.get("patron") else "no",
                }
            )
        return rows, "Patrones de asistencia"
    if tipo == "correlacion":
        patterns = attendance_patterns(db, students)
        brechas = {row["id"]: row for row in brechas_atencion(db, students, patterns)}
        by_id = {row["id"]: row for row in patterns["filas"]}
        rows = []
        for student in students:
            p = by_id.get(student.id, {})
            b = brechas.get(student.id)
            rows.append(
                {
                    "codigo": student.codigo,
                    "estudiante": student.full_name,
                    "salon": student.grade.nombre if student.grade else "",
                    "pct_asistencia": p.get("pct", ""),
                    "faltas": p.get("faltas", ""),
                    "racha": p.get("racha", ""),
                    "atencion": (b or {}).get("atencion", ""),
                    "seguimiento_abierto": "sí" if b and b["seguimiento"] else "no",
                    "cita_programada": "sí" if b and b["cita"] else "no",
                    "brecha": "sí" if b and b["brecha"] else "no",
                }
            )
        return rows, "Correlación de inasistencia, alerta y tutoría"
    if tipo == "padron":
        rows = []
        for student in students:
            rows.append(
                {
                    "codigo": student.codigo,
                    "estudiante": student.full_name,
                    "salon": student.grade.nombre if student.grade else "",
                    "sexo": student.sexo,
                    "tipo": TIPO_MAT_LABELS.get(student.tipo_matricula, student.tipo_matricula or ""),
                    "lengua": LENGUA_LABELS.get(student.lengua_materna, student.lengua_materna or ""),
                    "vive_con": VIVE_LABELS.get(student.vive_con, student.vive_con or ""),
                    "seguro": SEGURO_LABELS.get(student.seguro, student.seguro or ""),
                    "nnee": "sí" if student.nnee else "no",
                    "estado": STATUS_LABELS.get(student.estado, student.estado),
                }
            )
        return rows, "Padrón de matrícula (sin DNI ni teléfonos)"
    preds = (
        db.query(Prediction)
        .options(joinedload(Prediction.student).joinedload(Student.grade))
        .filter(Prediction.vigente.is_(True))
        .order_by(Prediction.prioridad.asc())
        .all()
    )
    rows = []
    for pred in preds:
        if pred.student_id not in allowed:
            continue
        student = pred.student
        rows.append(
            {
                "prioridad": pred.prioridad,
                "codigo": student.codigo if student else "",
                "estudiante": student.full_name if student else "",
                "salon": student.grade.nombre if student and student.grade else "",
                "probabilidad": f"{pred.probabilidad * 100:.1f}%",
                "nivel_modelo": pred.nivel_modelo or "",
                "atencion": pred.nivel_riesgo,
            }
        )
    return rows, "Estudiantes priorizados"


@router.get("/modelo")
def model_page(request: Request, db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect("/modelo")
    if user.role not in MODEL_ROLES:
        return forbidden()
    runs = db.query(ModelRun).order_by(ModelRun.f1.desc()).all()
    selected = next((r for r in runs if r.selected), None)
    return templates.TemplateResponse("modelo.html", ctx(request, user, runs=runs, selected=selected))


@router.post("/modelo/reentrenar")
def retrain(
    request: Request,
    csrf: str = Form(""),
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/modelo")
    if user.role not in USER_ADMIN_ROLES:
        return forbidden()
    if not csrf_ok(request, csrf):
        return reject_csrf(request, "/modelo")
    train_and_select(db)
    predict_all(db)
    audit(db, user, "reentrenar", "")
    db.commit()
    request.session["flash_ok"] = "Modelo reentrenado y priorización actualizada."
    return RedirectResponse("/modelo", status_code=303)


@router.get("/usuarios")
def users_page(request: Request, rol: str = "", estado: str = "", q: str = "", db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect("/usuarios")
    if user.role not in USER_ADMIN_ROLES:
        return forbidden()
    users = db.query(User).order_by(User.role, User.full_name).all()
    rol = role_filter(rol)
    q = search_q(q)
    if estado not in {"", "activo", "inactivo"}:
        estado = ""
    if rol:
        users = [u for u in users if u.role == rol]
    if estado == "activo":
        users = [u for u in users if u.is_active]
    elif estado == "inactivo":
        users = [u for u in users if not u.is_active]
    if q:
        ql = q.lower()
        users = [u for u in users if ql in u.username.lower() or ql in u.full_name.lower()]
    return templates.TemplateResponse(
        "usuarios.html",
        ctx(
            request,
            user,
            users=users,
            error=None,
            nueva_clave=None,
            rol=rol,
            estado=estado,
            q=q,
            form={"username": "", "full_name": "", "role": "docente"},
        ),
    )


@router.post("/usuarios")
def user_create(
    request: Request,
    username: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    password: str = Form(...),
    csrf: str = Form(""),
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/usuarios")
    if user.role not in USER_ADMIN_ROLES:
        return forbidden()
    if not csrf_ok(request, csrf):
        return reject_csrf(request, "/usuarios")
    users = db.query(User).order_by(User.role, User.full_name).all()
    typed_user = username
    typed_name = full_name
    username, user_err = username_ok(username)
    allowed_roles = {Role.DOCENTE.value, Role.ESTUDIANTE.value}
    nombre, name_err = person_name(full_name, "Nombre completo")
    pwd_err = password_ok(password, username=username)
    error = None
    if user_err:
        error = user_err
    elif db.query(User).filter(User.username == username).first():
        error = "Ese usuario ya existe."
    elif role not in allowed_roles:
        error = "Rol no permitido."
    elif name_err:
        error = name_err
    elif pwd_err:
        error = pwd_err
    if error:
        return templates.TemplateResponse(
            "usuarios.html",
            ctx(
                request,
                user,
                users=users,
                error=error,
                nueva_clave=None,
                rol="",
                estado="",
                q="",
                form={"username": typed_user, "full_name": typed_name, "role": role},
            ),
            status_code=400,
        )
    created = User(
        username=username,
        password_hash=hash_password(password),
        full_name=nombre,
        role=role,
        email=f"{username}@exellenti.edu.pe",
        clave_temporal="",
        is_active=True,
    )
    db.add(created)
    audit(db, user, "usuario_alta", username)
    db.commit()
    request.session["flash_ok"] = f"Usuario {username} creado. Entregue la clave por un canal seguro; no queda almacenada en claro."
    return RedirectResponse("/usuarios", status_code=303)


@router.post("/usuarios/{user_id}/estado")
def user_toggle(
    request: Request,
    user_id: int,
    csrf: str = Form(""),
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/usuarios")
    if user.role not in USER_ADMIN_ROLES:
        return forbidden()
    if not csrf_ok(request, csrf):
        return reject_csrf(request, "/usuarios")
    if user_id == user.id:
        request.session["flash"] = "No puede desactivar su propia cuenta."
        return RedirectResponse("/usuarios", status_code=303)
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        return forbidden()
    if target.role == Role.DIRECTORA.value:
        request.session["flash"] = "No se puede desactivar la cuenta de Dirección."
        return RedirectResponse("/usuarios", status_code=303)
    target.is_active = not target.is_active
    audit(db, user, "usuario_estado", f"{target.username}:{'activo' if target.is_active else 'inactivo'}")
    db.commit()
    request.session["flash_ok"] = f"Usuario {target.username} {'activado' if target.is_active else 'desactivado'}."
    return RedirectResponse("/usuarios", status_code=303)


@router.get("/auditoria")
def audit_page(request: Request, accion: str = "", q: str = "", db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect("/auditoria")
    if user.role not in AUDIT_ROLES:
        return forbidden()
    query = db.query(AuditLog).order_by(AuditLog.id.desc())
    acciones = sorted({a for (a,) in db.query(AuditLog.accion).distinct().all() if a})
    accion = search_q(accion)
    q = search_q(q)
    names = {u.id: u.full_name for u in db.query(User).all()}
    if accion not in acciones:
        accion = ""
    if accion:
        query = query.filter(AuditLog.accion == accion)
    if q:
        like = f"%{q}%"
        name_ids = [uid for uid, name in names.items() if q.lower() in name.lower()]
        query = query.filter(or_(AuditLog.detalle.ilike(like), AuditLog.user_id.in_(name_ids or [-1])))
    logs = query.limit(200).all()
    return templates.TemplateResponse(
        "auditoria.html",
        ctx(request, user, logs=logs, names=names, accion=accion, q=q, acciones=acciones),
    )


@router.get("/institucion")
def institution_page(request: Request, db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect("/institucion")
    if user.role not in USER_ADMIN_ROLES:
        return forbidden()
    snap = institution_snapshot(db)
    cargas = (
        db.query(TeacherAssignment)
        .options(
            joinedload(TeacherAssignment.teacher).joinedload(TeacherProfile.user),
            joinedload(TeacherAssignment.grade),
            joinedload(TeacherAssignment.course),
        )
        .all()
    )
    return templates.TemplateResponse(
        "institucion.html",
        ctx(request, user, snap=snap, cargas=cargas),
    )


def _own_student(user: User, db: Session) -> Student | None:
    if not user.student_profile:
        return db.query(Student).filter(Student.user_id == user.id).first()
    return user.student_profile


@router.get("/mi-ficha")
def my_file(request: Request, db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect("/mi-ficha")
    if user.role != Role.ESTUDIANTE.value:
        return forbidden()
    own = _own_student(user, db)
    if not own:
        return forbidden()
    return RedirectResponse(f"/estudiantes/{own.id}", status_code=303)


@router.get("/mi-boleta")
def my_report(request: Request, db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect("/mi-boleta")
    if user.role != Role.ESTUDIANTE.value:
        return forbidden()
    own = _own_student(user, db)
    if not own:
        return forbidden()
    student = (
        db.query(Student)
        .options(
            joinedload(Student.grade),
            joinedload(Student.grades).joinedload(GradeRecord.course),
            joinedload(Student.attendance),
        )
        .filter(Student.id == own.id)
        .first()
    )
    if not student:
        return forbidden()
    courses = db.query(Course).order_by(Course.id).all()
    records = {(r.course_id, r.bimestre): r.nota for r in student.grades}
    pred = (
        db.query(Prediction)
        .filter(Prediction.student_id == student.id, Prediction.vigente.is_(True))
        .first()
    )
    return templates.TemplateResponse(
        "mi_boleta.html",
        ctx(
            request,
            user,
            student=student,
            courses=courses,
            records=records,
            progress=student_progress(student),
            pred=pred,
            tutor=tutors_by_grade(db).get(student.grade_id or 0, "Sin tutor de aula"),
            docentes=course_teacher_map(db, student.grade_id) if student.grade_id else {},
        ),
    )


@router.get("/mi-asistencia")
def my_attendance(request: Request, marca: str = "", db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect("/mi-asistencia")
    if user.role != Role.ESTUDIANTE.value:
        return forbidden()
    student = _own_student(user, db)
    if not student:
        return forbidden()
    marca = attendance_mark(marca)
    query = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student.id)
    if marca:
        query = query.filter(AttendanceRecord.estado == marca)
    att = query.order_by(AttendanceRecord.fecha.desc()).limit(90).all()
    summary = {
        "total": len(student.attendance),
        "presente": sum(1 for a in student.attendance if a.estado == AttendanceStatus.PRESENTE.value),
        "falta": sum(1 for a in student.attendance if a.estado == AttendanceStatus.FALTA.value),
        "tardanza": sum(1 for a in student.attendance if a.estado == AttendanceStatus.TARDANZA.value),
        "justificada": sum(1 for a in student.attendance if a.estado == AttendanceStatus.JUSTIFICADA.value),
    }
    return templates.TemplateResponse(
        "mi_asistencia.html",
        ctx(request, user, student=student, att=att, summary=summary, marca=marca),
    )


@router.get("/cuenta")
def account_page(request: Request, db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect("/cuenta")
    return templates.TemplateResponse("cuenta.html", ctx(request, user, error=None, ok=None))


@router.post("/cuenta")
def account_save(
    request: Request,
    actual: str = Form(...),
    nueva: str = Form(...),
    repetir: str = Form(...),
    csrf: str = Form(""),
    db: Session = Depends(db_session),
):
    user = current_user(request, db)
    if not user:
        return login_redirect("/cuenta")
    if not csrf_ok(request, csrf):
        return templates.TemplateResponse(
            "cuenta.html",
            ctx(request, user, error="La sesión expiró. Vuelva a intentar.", ok=None),
            status_code=400,
        )
    error = None
    ok = None
    pwd_err = password_ok(nueva, username=user.username)
    if not verify_password(actual, user.password_hash):
        error = "La clave actual no coincide."
    elif nueva != repetir:
        error = "La confirmación no coincide."
    elif pwd_err:
        error = pwd_err
    elif verify_password(nueva, user.password_hash):
        error = "La nueva clave debe ser distinta a la actual."
    else:
        user.password_hash = hash_password(nueva)
        user.clave_temporal = ""
        audit(db, user, "cambio_clave", user.username)
        db.commit()
        ok = "Clave actualizada."
    return templates.TemplateResponse("cuenta.html", ctx(request, user, error=error, ok=ok))


@router.get("/scrum")
def scrum_page(request: Request, sprint: str = "", estado: str = "", db: Session = Depends(db_session)):
    user = current_user(request, db)
    if not user:
        return login_redirect("/scrum")
    if user.role not in SCRUM_ROLES:
        return forbidden()
    sprint = search_q(sprint)
    estado = search_q(estado)
    all_items = db.query(BacklogItem).order_by(BacklogItem.id).all()
    sprints = sorted({i.sprint for i in all_items if i.sprint})
    estados = sorted({i.estado for i in all_items if i.estado})
    items = all_items
    if sprint:
        items = [i for i in items if i.sprint == sprint]
    if estado:
        items = [i for i in items if i.estado == estado]
    return templates.TemplateResponse(
        "scrum.html",
        ctx(request, user, items=items, sprint=sprint, estado=estado, sprints=sprints, estados=estados),
    )
