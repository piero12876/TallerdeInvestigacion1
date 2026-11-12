from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy import event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from backend.config import DATABASE_URL, SCHEMA_VERSION


class Base(DeclarativeBase):
    pass


_IS_SQLITE = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if _IS_SQLITE else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=True, autocommit=False)


@event.listens_for(engine, "connect")
def _sqlite_foreign_keys(dbapi_connection, _connection_record):
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(160), default="")
    role: Mapped[str] = mapped_column(String(30), index=True)
    phone: Mapped[str] = mapped_column(String(40), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    clave_temporal: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    teacher_profile: Mapped["TeacherProfile | None"] = relationship(back_populates="user")
    student_profile: Mapped["Student | None"] = relationship(back_populates="user")


class SchoolGrade(Base):
    __tablename__ = "school_grades"
    __table_args__ = (UniqueConstraint("nivel", "seccion", "anio"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nivel: Mapped[int] = mapped_column(Integer)
    seccion: Mapped[str] = mapped_column(String(4), default="A")
    anio: Mapped[int] = mapped_column(Integer)
    nombre: Mapped[str] = mapped_column(String(80))
    tutor_id: Mapped[int | None] = mapped_column(ForeignKey("teacher_profiles.id"), nullable=True)

    students: Mapped[list["Student"]] = relationship(back_populates="grade")
    assignments: Mapped[list["TeacherAssignment"]] = relationship(back_populates="grade")
    tutor: Mapped["TeacherProfile | None"] = relationship(
        "TeacherProfile",
        foreign_keys="SchoolGrade.tutor_id",
        back_populates="tutored_grades",
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(12), unique=True)
    nombre: Mapped[str] = mapped_column(String(80))
    area: Mapped[str] = mapped_column(String(80))

    assignments: Mapped[list["TeacherAssignment"]] = relationship(back_populates="course")


class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    dni: Mapped[str] = mapped_column(String(12), default="")
    especialidad: Mapped[str] = mapped_column(String(120), default="")

    user: Mapped[User] = relationship(back_populates="teacher_profile")
    assignments: Mapped[list["TeacherAssignment"]] = relationship(back_populates="teacher")
    tutored_grades: Mapped[list["SchoolGrade"]] = relationship(
        back_populates="tutor",
        foreign_keys="SchoolGrade.tutor_id",
    )


class TeacherAssignment(Base):
    __tablename__ = "teacher_assignments"
    __table_args__ = (UniqueConstraint("teacher_id", "grade_id", "course_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher_profiles.id"))
    grade_id: Mapped[int] = mapped_column(ForeignKey("school_grades.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    es_tutor: Mapped[bool] = mapped_column(Boolean, default=False)

    teacher: Mapped[TeacherProfile] = relationship(back_populates="assignments")
    grade: Mapped[SchoolGrade] = relationship(back_populates="assignments")
    course: Mapped[Course] = relationship(back_populates="assignments")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    dni: Mapped[str] = mapped_column(String(12), default="")
    nombres: Mapped[str] = mapped_column(String(80))
    apellidos: Mapped[str] = mapped_column(String(80))
    sexo: Mapped[str] = mapped_column(String(1), default="M")
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    grade_id: Mapped[int | None] = mapped_column(ForeignKey("school_grades.id"), nullable=True)
    apoderado: Mapped[str] = mapped_column(String(160), default="")
    telefono_apoderado: Mapped[str] = mapped_column(String(40), default="")
    parentesco: Mapped[str] = mapped_column(String(20), default="")
    dni_apoderado: Mapped[str] = mapped_column(String(12), default="")
    correo_apoderado: Mapped[str] = mapped_column(String(120), default="")
    direccion: Mapped[str] = mapped_column(String(160), default="")
    distrito: Mapped[str] = mapped_column(String(80), default="")
    referencia: Mapped[str] = mapped_column(String(160), default="")
    tipo_matricula: Mapped[str] = mapped_column(String(20), default="regular")
    ie_procedencia: Mapped[str] = mapped_column(String(160), default="")
    fecha_matricula: Mapped[date | None] = mapped_column(Date, nullable=True)
    turno: Mapped[str] = mapped_column(String(20), default="manana")
    lengua_materna: Mapped[str] = mapped_column(String(20), default="castellano")
    vive_con: Mapped[str] = mapped_column(String(20), default="")
    seguro: Mapped[str] = mapped_column(String(20), default="")
    nnee: Mapped[bool] = mapped_column(Boolean, default=False)
    discapacidad: Mapped[str] = mapped_column(String(20), default="ninguna")
    observaciones: Mapped[str] = mapped_column(Text, default="")
    estado: Mapped[str] = mapped_column(String(20), default="activo", index=True)
    anio_ingreso: Mapped[int] = mapped_column(Integer, default=2026)
    es_historico: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User | None] = relationship(back_populates="student_profile")
    grade: Mapped[SchoolGrade | None] = relationship(back_populates="students")
    grades: Mapped[list["GradeRecord"]] = relationship(back_populates="student")
    attendance: Mapped[list["AttendanceRecord"]] = relationship(back_populates="student")
    followups: Mapped[list["FollowUp"]] = relationship(back_populates="student")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="student")

    @property
    def full_name(self) -> str:
        return f"{self.apellidos}, {self.nombres}"

    @property
    def edad(self) -> int | None:
        if not self.fecha_nacimiento:
            return None
        today = date.today()
        years = today.year - self.fecha_nacimiento.year
        if (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day):
            years -= 1
        return years


class GradeRecord(Base):
    __tablename__ = "grade_records"
    __table_args__ = (UniqueConstraint("student_id", "course_id", "bimestre"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    bimestre: Mapped[int] = mapped_column(Integer)
    nota: Mapped[float] = mapped_column(Float)
    registrado_por: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student: Mapped[Student] = relationship(back_populates="grades")
    course: Mapped[Course] = relationship()


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("student_id", "fecha"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    fecha: Mapped[date] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(String(20))
    detalle: Mapped[str] = mapped_column(String(160), default="")
    registrado_por: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    student: Mapped[Student] = relationship(back_populates="attendance")


class TutoringAppointment(Base):
    __tablename__ = "tutoring_appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    fecha: Mapped[date] = mapped_column(Date, index=True)
    motivo: Mapped[str] = mapped_column(String(180))
    canal: Mapped[str] = mapped_column(String(20), default="presencial")
    estado: Mapped[str] = mapped_column(String(20), default="programada", index=True)
    resultado: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student: Mapped[Student] = relationship()
    author: Mapped[User] = relationship()


class FollowUp(Base):
    __tablename__ = "followups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    contenido: Mapped[str] = mapped_column(Text)
    tipo: Mapped[str] = mapped_column(String(20), default="academico", index=True)
    estado: Mapped[str] = mapped_column(String(20), default="abierto", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student: Mapped[Student] = relationship(back_populates="followups")
    author: Mapped[User] = relationship()


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    probabilidad: Mapped[float] = mapped_column(Float)
    nivel_riesgo: Mapped[str] = mapped_column(String(12), index=True)
    nivel_modelo: Mapped[str] = mapped_column(String(12), default="")
    prioridad: Mapped[int] = mapped_column(Integer, default=0)
    modelo: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    vigente: Mapped[bool] = mapped_column(Boolean, default=True)

    student: Mapped[Student] = relationship(back_populates="predictions")


class ModelRun(Base):
    __tablename__ = "model_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    algoritmo: Mapped[str] = mapped_column(String(80))
    accuracy: Mapped[float] = mapped_column(Float)
    precision: Mapped[float] = mapped_column(Float)
    recall: Mapped[float] = mapped_column(Float)
    f1: Mapped[float] = mapped_column(Float)
    roc_auc: Mapped[float] = mapped_column(Float, default=0)
    vp: Mapped[int] = mapped_column(Integer, default=0)
    vn: Mapped[int] = mapped_column(Integer, default=0)
    fp: Mapped[int] = mapped_column(Integer, default=0)
    fn: Mapped[int] = mapped_column(Integer, default=0)
    n_train: Mapped[int] = mapped_column(Integer, default=0)
    n_test: Mapped[int] = mapped_column(Integer, default=0)
    pr_auc: Mapped[float] = mapped_column(Float, default=0)
    recall_std: Mapped[float] = mapped_column(Float, default=0)
    f1_std: Mapped[float] = mapped_column(Float, default=0)
    cv_folds: Mapped[int] = mapped_column(Integer, default=5)
    nota: Mapped[str] = mapped_column(Text, default="")
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BacklogItem(Base):
    __tablename__ = "backlog_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20))
    titulo: Mapped[str] = mapped_column(String(220))
    sprint: Mapped[str] = mapped_column(String(40))
    estado: Mapped[str] = mapped_column(String(30), default="Hecho")
    criterio: Mapped[str] = mapped_column(Text, default="")
    actor: Mapped[str] = mapped_column(String(40), default="")
    historia: Mapped[str] = mapped_column(Text, default="")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    accion: Mapped[str] = mapped_column(String(80))
    detalle: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def reset_if_stale() -> None:
    from backend.config import DATA_DIR, MODEL_PATH, TESTING

    # En PostgreSQL el esquema vive en Railway. Borrar un archivo local no
    # debe tocar esa base ni el modelo en cada reinicio del contenedor.
    if TESTING or ":memory:" in DATABASE_URL or not _IS_SQLITE:
        return
    marker = DATA_DIR / "schema.txt"
    db_path = DATA_DIR / "exellenti.db"
    if marker.exists() and marker.read_text(encoding="utf-8").strip() == SCHEMA_VERSION:
        return
    engine.dispose()
    if db_path.exists():
        db_path.unlink()
    if MODEL_PATH.exists():
        MODEL_PATH.unlink()
    marker.write_text(SCHEMA_VERSION, encoding="utf-8")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
