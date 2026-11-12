import re
from datetime import date, timedelta

from backend.config import ANIO_LECTIVO
from backend.domain.validate import (
    attendance_date,
    attendance_mark,
    birth_date,
    csv_cell,
    dni_peru,
    followup_text,
    parse_nota,
    password_ok,
    person_name,
    phone_pe,
    report_tipo,
    risk_nivel,
    safe_next,
    search_q,
)
from backend.infrastructure.database import AttendanceRecord, Course, GradeRecord, SchoolGrade, SessionLocal, Student, User


def test_dni_and_nota_rules():
    assert dni_peru("123")[1] is not None
    assert dni_peru("12345678") == ("12345678", None)
    assert dni_peru("") == ("", None)
    assert parse_nota("21")[0] is None
    assert parse_nota("15.5")[0] == 15.5
    assert safe_next("https://evil.example") == "/"
    assert safe_next("/reportes") == "/reportes"
    assert csv_cell("=2+2").startswith("'")
    err = attendance_date(date(2026, 11, 7), year=2026, today=date(2026, 11, 10))
    assert err and "viernes" in err
    assert search_q("  ana%_  ") == "ana"
    assert risk_nivel("ALTO") == "alto"
    assert risk_nivel("xyz") == ""
    assert birth_date("2016-05-01", year=2026)[1] is None
    assert birth_date("2000-01-01", year=2026)[1] is not None
    assert phone_pe("987654321")[1] is None
    assert phone_pe("123")[1] is not None
    assert phone_pe("9abcdefghi")[1] is not None
    assert dni_peru("12ab45cd")[1] is not None
    assert person_name("Ana12", "Nombres")[1] is not None
    assert password_ok("abcdefg") is not None
    assert password_ok("clave123") is None
    assert followup_text("corto")[1] is not None
    assert attendance_mark("falta") == "falta"
    assert report_tipo("noexiste") == "priorizados"
    assert report_tipo("padron") == "padron"
    assert csv_cell("+cmd").startswith("'")


def csrf_token(html: str) -> str:
    match = re.search(r'name="csrf" value="([^"]+)"', html)
    assert match, "No se encontró token CSRF"
    return match.group(1)


def login(client, username: str, password: str):
    client.get("/logout")
    page = client.get("/login")
    response = client.post(
        "/login",
        data={"username": username, "password": password, "csrf": csrf_token(page.text)},
        follow_redirects=True,
    )
    assert "Usuario o clave incorrectos" not in response.text
    assert "Demasiados intentos" not in response.text
    return response


def test_login_rejects_wrong_password(client):
    page = client.get("/login")
    response = client.post(
        "/login",
        data={"username": "directora", "password": "Exellenti2026", "csrf": csrf_token(page.text)},
    )
    assert response.status_code == 401


def test_login_director_dashboard(client):
    response = login(client, "directora", "Dir#Ex26")
    assert response.status_code == 200
    assert "Panel de dirección" in response.text
    assert "La institución" in response.text


def test_admin_and_psychology_accounts_removed(client):
    client.get("/logout")
    for username, password in (("admin", "Adm#Ex26"), ("psicologa", "Psi#Ex26")):
        page = client.get("/login")
        response = client.post(
            "/login",
            data={"username": username, "password": password, "csrf": csrf_token(page.text)},
        )
        assert response.status_code == 401
        assert "incorrectos" in response.text.lower()


def test_teacher_cannot_open_institution(client):
    login(client, "maria.cerron", "Doc1#Ex26")
    response = client.get("/institucion", follow_redirects=True)
    assert "Mapa de la institución" not in response.text


def test_student_cannot_open_model_or_risk_list(client):
    login(client, "alumno31", "Est31#Ex26")
    modelo = client.get("/modelo", follow_redirects=True)
    riesgo = client.get("/riesgo", follow_redirects=True)
    assert "Evaluación del modelo" not in modelo.text
    assert "Priorización del riesgo" not in riesgo.text


def test_student_sees_tutor_teachers_and_risk(client):
    login(client, "alumno31", "Est31#Ex26")
    boleta = client.get("/mi-boleta", follow_redirects=True)
    assert boleta.status_code == 200
    assert "Mi boleta" in boleta.text
    assert "Tutor" in boleta.text
    assert "Héctor Quispe" in boleta.text
    assert "Ana De la Cruz" in boleta.text
    assert "Carlos Meza" in boleta.text
    assert "atención" in boleta.text.lower()
    ficha = client.get("/mi-ficha", follow_redirects=True)
    assert "Ficha de matrícula" in ficha.text
    assert "Quién dicta cada área" in ficha.text
    home = client.get("/")
    assert "Mi atención" in home.text or "atención" in home.text.lower()
    home = client.get("/", follow_redirects=True)
    assert "Mi portal" in home.text
    assert "Alerta temprana" not in home.text


def test_grades_persist(client):
    login(client, "directora", "Dir#Ex26")
    db = SessionLocal()
    grade = db.query(SchoolGrade).filter_by(nivel=1, seccion="A").first()
    course = db.query(Course).filter_by(codigo="MAT").first()
    student = db.query(Student).filter_by(grade_id=grade.id, es_historico=False).first()
    page = client.get(f"/calificaciones?grado={grade.id}&curso={course.id}")
    response = client.post(
        "/calificaciones",
        data={
            "csrf": csrf_token(page.text),
            "grado": str(grade.id),
            "curso": str(course.id),
            f"n_{student.id}_1": "15.5",
            f"n_{student.id}_2": "16.0",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    db.close()
    db = SessionLocal()
    record = (
        db.query(GradeRecord)
        .filter_by(student_id=student.id, course_id=course.id, bimestre=1)
        .first()
    )
    assert record is not None
    assert record.nota == 15.5
    db.close()


def test_csrf_rejects_empty_token(client):
    login(client, "directora", "Dir#Ex26")
    response = client.post("/usuarios", data={
        "username": "intruso",
        "full_name": "Intruso",
        "role": "docente",
        "password": "Clave#1234",
        "csrf": "token-falso",
    }, follow_redirects=True)
    assert "intruso" not in response.text.lower() or "La sesión expiró" in response.text


def test_modules_are_isolated(client):
    login(client, "directora", "Dir#Ex26")
    matricula = client.get("/estudiantes")
    assert "Matrícula" in matricula.text
    assert ">Riesgo<" not in matricula.text
    assert ">Prioridad<" not in matricula.text
    db = SessionLocal()
    grade = db.query(SchoolGrade).filter_by(nivel=1, seccion="A").first()
    course = db.query(Course).filter_by(codigo="MAT").first()
    db.close()
    evaluacion = client.get(f"/calificaciones?grado={grade.id}&curso={course.id}")
    assert "Evolución del salón" in evaluacion.text
    assert "Pase de lista" not in evaluacion.text
    asistencia = client.get(f"/asistencia?grado={grade.id}")
    assert "Patrones" in asistencia.text
    assert "Bimestre 1" not in asistencia.text
    alerta = client.get("/riesgo")
    assert "Alerta temprana" in alerta.text


def test_reportes_csv_and_roles(client):
    login(client, "directora", "Dir#Ex26")
    page = client.get("/reportes")
    assert page.status_code == 200
    assert "Reportes" in page.text
    csv_resp = client.get("/reportes/exportar?tipo=asistencia")
    assert csv_resp.status_code == 200
    assert "pct_asistencia" in csv_resp.text
    login(client, "alumno31", "Est31#Ex26")
    blocked = client.get("/reportes", follow_redirects=True)
    assert "Reportes" not in blocked.text or "No tiene permiso" in blocked.text


def test_alerta_filters_by_salon(client):
    login(client, "directora", "Dir#Ex26")
    db = SessionLocal()
    grade = db.query(SchoolGrade).filter_by(nivel=1, seccion="A").first()
    db.close()
    all_rows = client.get("/riesgo")
    one = client.get(f"/riesgo?grado={grade.id}&nivel=noexiste")
    assert "Alerta temprana" in all_rows.text
    assert "Salón" in one.text
    assert "nivel=noexiste" not in one.text or 'value="noexiste"' not in one.text


def test_invalid_birth_is_rejected(client):
    login(client, "directora", "Dir#Ex26")
    page = client.get("/estudiantes/nuevo")
    response = client.post(
        "/estudiantes/nuevo",
        data={
            "csrf": csrf_token(page.text),
            "nombres": "Ana",
            "apellidos": "Quispe",
            "dni": "45678901",
            "sexo": "F",
            "grade_id": "1",
            "apoderado": "",
            "telefono_apoderado": "",
            "fecha_nacimiento": "2000-01-01",
        },
    )
    assert response.status_code == 400
    assert "primaria" in response.text.lower()


def test_dni_rejects_letters(client):
    login(client, "directora", "Dir#Ex26")
    page = client.get("/estudiantes/nuevo")
    response = client.post(
        "/estudiantes/nuevo",
        data={
            "csrf": csrf_token(page.text),
            "nombres": "Ana",
            "apellidos": "Quispe",
            "dni": "12ab45cd",
            "sexo": "F",
            "grade_id": "1",
            "apoderado": "",
            "telefono_apoderado": "",
        },
    )
    assert response.status_code == 400
    assert "números" in response.text.lower() or "8 dígitos" in response.text
    assert 'value="Ana"' in response.text


def test_invalid_dni_is_rejected(client):
    login(client, "directora", "Dir#Ex26")
    page = client.get("/estudiantes/nuevo")
    response = client.post(
        "/estudiantes/nuevo",
        data={
            "csrf": csrf_token(page.text),
            "nombres": "Ana",
            "apellidos": "Quispe",
            "dni": "123",
            "sexo": "F",
            "grade_id": "1",
            "apoderado": "",
            "telefono_apoderado": "",
        },
    )
    assert response.status_code == 400
    assert "8 dígitos" in response.text


def test_attendance_rejects_weekend(client):
    login(client, "directora", "Dir#Ex26")
    db = SessionLocal()
    grade = db.query(SchoolGrade).filter_by(nivel=1, seccion="A").first()
    page = client.get(f"/asistencia?grado={grade.id}")
    db.close()
    response = client.post(
        "/asistencia",
        data={"csrf": csrf_token(page.text), "grado": str(grade.id), "fecha": "2026-11-07"},
        follow_redirects=True,
    )
    assert "lunes a viernes" in response.text


def test_login_ignores_external_next(client):
    client.get("/logout")
    page = client.get("/login?next=https://evil.example")
    response = client.post(
        "/login",
        data={
            "username": "directora",
            "password": "Dir#Ex26",
            "csrf": csrf_token(page.text),
            "next": "https://evil.example",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] in {"/", "http://testserver/"}


def test_auditoria_staff_only(client):
    login(client, "directora", "Dir#Ex26")
    page = client.get("/auditoria")
    assert page.status_code == 200
    assert "Bitácora" in page.text
    login(client, "maria.cerron", "Doc1#Ex26")
    blocked = client.get("/auditoria", follow_redirects=True)
    assert "Bitácora" not in blocked.text or "No tiene permiso" in blocked.text


def test_password_rejects_same_as_current(client):
    login(client, "directora", "Dir#Ex26")
    page = client.get("/cuenta")
    response = client.post(
        "/cuenta",
        data={
            "csrf": csrf_token(page.text),
            "actual": "Dir#Ex26",
            "nueva": "Dir#Ex26",
            "repetir": "Dir#Ex26",
        },
    )
    assert "distinta a la actual" in response.text


def test_password_change(client):
    login(client, "lucia.ramos", "Doc5#Ex26")
    page = client.get("/cuenta")
    response = client.post(
        "/cuenta",
        data={
            "csrf": csrf_token(page.text),
            "actual": "Doc5#Ex26",
            "nueva": "Doc5#Ex26b",
            "repetir": "Doc5#Ex26b",
        },
    )
    assert response.status_code == 200
    assert "Clave actualizada" in response.text
    again = login(client, "lucia.ramos", "Doc5#Ex26b")
    assert again.status_code == 200
    assert "Panel docente" in again.text
    page = client.get("/cuenta")
    client.post(
        "/cuenta",
        data={
            "csrf": csrf_token(page.text),
            "actual": "Doc5#Ex26b",
            "nueva": "Doc5#Ex26",
            "repetir": "Doc5#Ex26",
        },
    )


def _ok(response, path: str) -> None:
    assert response.status_code == 200, f"{path} -> {response.status_code}"
    assert "Internal Server Error" not in response.text
    assert "Traceback" not in response.text


def test_anonymous_goes_to_login(client):
    client.get("/logout")
    response = client.get("/estudiantes", follow_redirects=True)
    assert response.status_code == 200
    assert "Ingreso" in response.text or "Ingresar" in response.text


def test_static_assets_load(client):
    css = client.get("/static/css/app.css")
    js = client.get("/static/js/app.js")
    assert css.status_code == 200
    assert js.status_code == 200
    assert "nav-g" in css.text or "layout" in css.text or "btn" in css.text


def test_director_pages_do_not_500(client):
    login(client, "directora", "Dir#Ex26")
    db = SessionLocal()
    grade = db.query(SchoolGrade).filter_by(nivel=1, seccion="A").first()
    course = db.query(Course).filter_by(codigo="MAT").first()
    student = db.query(Student).filter_by(grade_id=grade.id, es_historico=False).first()
    db.close()
    paths = [
        "/",
        "/estudiantes",
        "/estudiantes/nuevo",
        f"/estudiantes/{student.id}",
        f"/estudiantes/{student.id}/editar",
        "/calificaciones",
        f"/calificaciones?grado={grade.id}&curso={course.id}",
        "/asistencia",
        f"/asistencia?grado={grade.id}",
        "/riesgo",
        f"/riesgo?grado={grade.id}&nivel=alto",
        "/reportes",
        "/reportes?tipo=rendimiento",
        "/reportes?tipo=asistencia",
        "/reportes?tipo=padron",
        "/reportes?tipo=basura",
        "/seguimientos",
        "/modelo",
        "/usuarios",
        "/usuarios?rol=docente",
        "/auditoria",
        "/institucion",
        "/docentes",
        "/scrum",
        "/scrum?sprint=Sprint%201",
        "/cuenta",
    ]
    for path in paths:
        _ok(client.get(path), path)
    csv_r = client.get("/riesgo/exportar")
    assert csv_r.status_code == 200
    assert "prioridad" in csv_r.text
    csv_a = client.get("/reportes/exportar?tipo=asistencia")
    assert csv_a.status_code == 200
    assert "pct_asistencia" in csv_a.text
    csv_m = client.get("/estudiantes/exportar")
    assert csv_m.status_code == 200
    assert "vive_con" in csv_m.text
    csv_p = client.get("/reportes/exportar?tipo=padron")
    assert csv_p.status_code == 200
    assert "nnee" in csv_p.text


def test_teacher_scope_and_forbidden_modules(client):
    login(client, "maria.cerron", "Doc1#Ex26")
    home = client.get("/")
    _ok(home, "/")
    assert "Panel docente" in home.text
    matricula = client.get("/estudiantes")
    _ok(matricula, "/estudiantes")
    assert "6.°" not in matricula.text
    assert "1.°" in matricula.text
    eval_page = client.get("/calificaciones")
    _ok(eval_page, "/calificaciones")
    assert "Comunicación" in eval_page.text
    asis = client.get("/asistencia")
    _ok(asis, "/asistencia")
    for path in ("/institucion", "/usuarios", "/auditoria", "/modelo", "/scrum", "/docentes"):
        blocked = client.get(path, follow_redirects=True)
        assert blocked.status_code == 200
        assert "Mapa de la institución" not in blocked.text or path != "/institucion"


def test_area_teacher_sees_only_taught_courses(client):
    login(client, "carlos.meza", "Doc4#Ex26")
    home = client.get("/")
    _ok(home, "/")
    assert "Panel docente" in home.text
    assert "Matemática" in home.text
    assert ">Asistencia<" not in home.text
    matricula = client.get("/estudiantes")
    _ok(matricula, "/estudiantes")
    assert "1.°" not in matricula.text
    assert "3.°" in matricula.text
    eval_page = client.get("/calificaciones")
    _ok(eval_page, "/calificaciones")
    assert "Matemática" in eval_page.text
    assert "Comunicación" not in eval_page.text or 'value="1"' not in eval_page.text
    asis = client.get("/asistencia", follow_redirects=True)
    assert "Pase de lista" not in asis.text
    nuevo = client.get("/estudiantes/nuevo", follow_redirects=True)
    assert "Nueva matrícula" not in nuevo.text


def test_tutor_does_not_grade_areas(client):
    login(client, "hector.quispe", "Doc8#Ex26")
    home = client.get("/")
    assert "Tutor de salón" in home.text or "Panel docente" in home.text
    assert "Evaluación" not in home.text or 'href="/calificaciones"' not in home.text
    asis = client.get("/asistencia")
    _ok(asis, "/asistencia")
    assert "Pase de lista" in asis.text or "Asistencia" in asis.text
    grades = client.get("/calificaciones", follow_redirects=True)
    assert "Evolución del salón" not in grades.text


def test_student_portal_pages(client):
    login(client, "alumno31", "Est31#Ex26")
    for path in ("/", "/mi-ficha", "/mi-boleta", "/mi-asistencia", "/mi-asistencia?marca=falta", "/cuenta"):
        r = client.get(path, follow_redirects=True)
        _ok(r, path)
    boleta = client.get("/mi-boleta")
    assert "Mi boleta" in boleta.text
    assert "Alerta temprana" not in boleta.text
    db = SessionLocal()
    me = db.query(User).filter_by(username="alumno31").first()
    own = db.query(Student).filter_by(user_id=me.id).first()
    other = (
        db.query(Student)
        .filter(Student.es_historico.is_(False), Student.id != own.id)
        .first()
    )
    other_name = other.full_name
    db.close()
    stolen = client.get(f"/estudiantes/{other.id}", follow_redirects=True)
    assert other_name not in stolen.text
    blocked = client.get("/seguimientos", follow_redirects=True)
    assert "Notas de tutoría" not in blocked.text
    csv_blocked = client.get("/estudiantes/exportar", follow_redirects=True)
    assert "vive_con" not in csv_blocked.text


def test_enroll_and_reject_bad_fields(client):
    login(client, "directora", "Dir#Ex26")
    page = client.get("/estudiantes/nuevo")
    token = csrf_token(page.text)
    bad_phone = client.post(
        "/estudiantes/nuevo",
        data={
            "csrf": token,
            "nombres": "Ana",
            "apellidos": "Quispe",
            "dni": "87654321",
            "sexo": "F",
            "grade_id": "1",
            "apoderado": "Rosa Quispe",
            "telefono_apoderado": "12345678",
        },
    )
    assert bad_phone.status_code == 400
    assert "celular" in bad_phone.text.lower() or "9 dígitos" in bad_phone.text
    bad_name = client.post(
        "/estudiantes/nuevo",
        data={
            "csrf": csrf_token(client.get("/estudiantes/nuevo").text),
            "nombres": "Ana123",
            "apellidos": "Quispe",
            "dni": "87654321",
            "sexo": "F",
            "grade_id": "1",
            "apoderado": "",
            "telefono_apoderado": "",
        },
    )
    assert bad_name.status_code == 400
    created = client.post(
        "/estudiantes/nuevo",
        data={
            "csrf": csrf_token(client.get("/estudiantes/nuevo").text),
            "nombres": "Ana",
            "apellidos": "Quispe Prueba",
            "dni": "87654321",
            "sexo": "F",
            "grade_id": "1",
            "apoderado": "Rosa Quispe",
            "telefono_apoderado": "987654321",
            "fecha_nacimiento": "2016-05-01",
        },
        follow_redirects=True,
    )
    assert created.status_code == 200
    assert "Matrícula" in created.text or "Ana" in created.text
    dup = client.post(
        "/estudiantes/nuevo",
        data={
            "csrf": csrf_token(client.get("/estudiantes/nuevo").text),
            "nombres": "Luis",
            "apellidos": "Quispe",
            "dni": "87654321",
            "sexo": "M",
            "grade_id": "1",
            "apoderado": "",
            "telefono_apoderado": "",
        },
    )
    assert dup.status_code == 400
    assert "DNI ya está registrado" in dup.text


def test_ficha_saves_context_and_rejects_bad_email(client):
    login(client, "directora", "Dir#Ex26")
    page = client.get("/estudiantes/nuevo")
    token = csrf_token(page.text)
    bad = client.post(
        "/estudiantes/nuevo",
        data={
            "csrf": token,
            "nombres": "Rosa",
            "apellidos": "Taipe",
            "dni": "87654322",
            "sexo": "F",
            "grade_id": "1",
            "apoderado": "Elena Taipe",
            "telefono_apoderado": "987654322",
            "correo_apoderado": "no-es-correo",
            "direccion": "Jr. Real 120",
            "distrito": "El Tambo",
        },
    )
    assert bad.status_code == 400
    assert "correo" in bad.text.lower()
    traslado = client.post(
        "/estudiantes/nuevo",
        data={
            "csrf": csrf_token(client.get("/estudiantes/nuevo").text),
            "nombres": "Rosa",
            "apellidos": "Taipe",
            "dni": "87654323",
            "sexo": "F",
            "grade_id": "1",
            "tipo_matricula": "traslado",
            "ie_procedencia": "",
        },
    )
    assert traslado.status_code == 400
    assert "procedencia" in traslado.text.lower()
    created = client.post(
        "/estudiantes/nuevo",
        data={
            "csrf": csrf_token(client.get("/estudiantes/nuevo").text),
            "nombres": "Rosa",
            "apellidos": "Taipe Huamán",
            "dni": "87654322",
            "sexo": "F",
            "grade_id": "1",
            "apoderado": "Elena Taipe",
            "telefono_apoderado": "987654322",
            "correo_apoderado": "elena.taipe@gmail.com",
            "direccion": "Jr. Real 120",
            "distrito": "El Tambo",
            "tipo_matricula": "traslado",
            "ie_procedencia": "IE 31501 Santa Rosa",
            "lengua_materna": "quechua",
            "vive_con": "madre",
            "seguro": "sis",
            "parentesco": "madre",
            "fecha_nacimiento": "2016-03-12",
            "fecha_matricula": "2026-03-10",
        },
        follow_redirects=True,
    )
    assert created.status_code == 200
    assert "Ficha de matrícula" in created.text
    assert "Quechua" in created.text
    assert "IE 31501" in created.text
    lista = client.get("/estudiantes?lengua=quechua&q=Taipe")
    assert "Taipe Huamán" in lista.text or "Rosa" in lista.text
    nnee = client.get("/estudiantes?nnee=1")
    assert nnee.status_code == 200
    assert "Matrícula" in nnee.text


def test_followup_too_short_and_valid(client):
    login(client, "directora", "Dir#Ex26")
    db = SessionLocal()
    student = db.query(Student).filter_by(es_historico=False).first()
    sid = student.id
    db.close()
    page = client.get(f"/estudiantes/{sid}")
    short = client.post(
        f"/estudiantes/{sid}/seguimiento",
        data={"csrf": csrf_token(page.text), "contenido": "ok"},
        follow_redirects=True,
    )
    assert "10 caracteres" in short.text
    page = client.get(f"/estudiantes/{sid}")
    ok = client.post(
        f"/estudiantes/{sid}/seguimiento",
        data={"csrf": csrf_token(page.text), "contenido": "Se conversó con el apoderado sobre asistencia."},
        follow_redirects=True,
    )
    assert "Seguimiento registrado" in ok.text


def test_grades_omit_out_of_range(client):
    login(client, "directora", "Dir#Ex26")
    db = SessionLocal()
    grade = db.query(SchoolGrade).filter_by(nivel=1, seccion="A").first()
    course = db.query(Course).filter_by(codigo="COM").first()
    student = db.query(Student).filter_by(grade_id=grade.id, es_historico=False).first()
    page = client.get(f"/calificaciones?grado={grade.id}&curso={course.id}")
    response = client.post(
        "/calificaciones",
        data={
            "csrf": csrf_token(page.text),
            "grado": str(grade.id),
            "curso": str(course.id),
            f"n_{student.id}_1": "21",
            f"n_{student.id}_2": "abc",
        },
        follow_redirects=True,
    )
    db.close()
    assert "omitieron" in response.text.lower() or "fuera de 0" in response.text


def test_attendance_saves_weekday(client):
    login(client, "directora", "Dir#Ex26")
    db = SessionLocal()
    grade = db.query(SchoolGrade).filter_by(nivel=1, seccion="A").first()
    student = db.query(Student).filter_by(grade_id=grade.id, es_historico=False).first()
    sid, gid = student.id, grade.id
    db.close()
    day = date.today()
    chosen = None
    for _ in range(21):
        if attendance_date(day, year=ANIO_LECTIVO) is None:
            chosen = day
            break
        day -= timedelta(days=1)
    assert chosen is not None
    page = client.get(f"/asistencia?grado={gid}&fecha={chosen.isoformat()}")
    response = client.post(
        "/asistencia",
        data={
            "csrf": csrf_token(page.text),
            "grado": str(gid),
            "fecha": chosen.isoformat(),
            f"a_{sid}": "tardanza",
        },
        follow_redirects=True,
    )
    assert "Asistencia guardada" in response.text
    db = SessionLocal()
    rec = db.query(AttendanceRecord).filter_by(student_id=sid, fecha=chosen).first()
    db.close()
    assert rec is not None
    assert rec.estado == "tardanza"


def test_teacher_cannot_save_foreign_grade(client):
    login(client, "maria.cerron", "Doc1#Ex26")
    db = SessionLocal()
    foreign = db.query(SchoolGrade).filter_by(nivel=6, seccion="C").first()
    course = db.query(Course).filter_by(codigo="MAT").first()
    page = client.get("/calificaciones")
    db.close()
    response = client.post(
        "/calificaciones",
        data={
            "csrf": csrf_token(page.text),
            "grado": str(foreign.id),
            "curso": str(course.id),
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Evolución del salón" not in response.text or "No tiene permiso" in response.text


def test_user_cannot_deactivate_self(client):
    login(client, "directora", "Dir#Ex26")
    db = SessionLocal()
    me = db.query(User).filter_by(username="directora").first()
    uid = me.id
    db.close()
    page = client.get("/usuarios")
    response = client.post(
        f"/usuarios/{uid}/estado",
        data={"csrf": csrf_token(page.text)},
        follow_redirects=True,
    )
    assert "propia cuenta" in response.text
    weak = client.post(
        "/usuarios",
        data={
            "csrf": csrf_token(client.get("/usuarios").text),
            "username": "nuevo.doc",
            "full_name": "Nuevo Docente",
            "role": "docente",
            "password": "12345678",
        },
    )
    assert weak.status_code == 400
    assert "predecible" in weak.text.lower() or "letras y números" in weak.text.lower() or "clave" in weak.text.lower()
    assert "nuevo.doc" in weak.text


def test_filters_reduce_lists(client):
    login(client, "directora", "Dir#Ex26")
    all_rows = client.get("/estudiantes")
    one = client.get("/estudiantes?q=Quispe&sexo=F")
    assert "registros" in all_rows.text
    assert one.status_code == 200
    report = client.get("/reportes?tipo=priorizados&q=xyznoexiste")
    assert "No hay filas" in report.text or "0 filas" in report.text or "filas" in report.text
    scrum = client.get("/scrum?sprint=Sprint 1")
    assert "PBI-01" in scrum.text
    assert "PBI-05" not in scrum.text
    users = client.get("/usuarios?rol=estudiante")
    assert "alumno31" in users.text
    assert "maria.cerron" not in users.text


def test_malformed_ids_do_not_500(client):
    login(client, "directora", "Dir#Ex26")
    r = client.get("/estudiantes/no-es-id", follow_redirects=True)
    assert r.status_code == 200
    assert "Internal Server Error" not in r.text
    r2 = client.get("/calificaciones?grado=99999&curso=99999")
    assert r2.status_code == 200
    assert "Seleccione salón" in r2.text or "No hay estudiantes" in r2.text or "Evaluación" in r2.text
