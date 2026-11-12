from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload

from backend.domain.enums import Role
from backend.infrastructure.database import Student, TeacherProfile, User


STAFF_ROLES = {Role.DIRECTORA.value, Role.DOCENTE.value}
FULL_ACCESS = {Role.DIRECTORA.value}
RISK_ACCESS = {Role.DIRECTORA.value, Role.DOCENTE.value}


def current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return (
        db.query(User)
        .options(
            joinedload(User.teacher_profile).joinedload(TeacherProfile.assignments),
            joinedload(User.teacher_profile).joinedload(TeacherProfile.tutored_grades),
            joinedload(User.student_profile),
        )
        .filter(User.id == user_id, User.is_active.is_(True))
        .first()
    )


def login_redirect(next_url: str = "/") -> RedirectResponse:
    return RedirectResponse(url=f"/login?next={next_url}", status_code=303)


def forbidden() -> RedirectResponse:
    return RedirectResponse(url="/?error=sin_permiso", status_code=303)


def teacher_taught_grade_ids(user: User) -> set[int]:
    profile = user.teacher_profile
    if not profile:
        return set()
    return {a.grade_id for a in profile.assignments}


def teacher_tutor_grade_ids(user: User) -> set[int]:
    profile = user.teacher_profile
    if not profile:
        return set()
    return {g.id for g in (profile.tutored_grades or [])}


def teacher_grade_ids(user: User) -> set[int]:
    return teacher_taught_grade_ids(user) | teacher_tutor_grade_ids(user)


def teacher_course_ids(user: User, grade_id: int | None = None) -> set[int]:
    profile = user.teacher_profile
    if not profile:
        return set()
    return {
        a.course_id
        for a in profile.assignments
        if a.course_id and (grade_id is None or a.grade_id == grade_id)
    }


def visible_students_query(db: Session, user: User):
    query = db.query(Student).options(joinedload(Student.grade)).filter(Student.es_historico.is_(False))
    if user.role == Role.ESTUDIANTE.value:
        if user.student_profile:
            return query.filter(Student.id == user.student_profile.id)
        return query.filter(Student.id == -1)
    if user.role == Role.DOCENTE.value:
        ids = teacher_grade_ids(user)
        return query.filter(Student.grade_id.in_(ids or {-1}))
    return query
