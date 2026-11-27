# Sistema web IE Exellenti

Plan de tesis: *Desarrollo de un sistema web mediante Scrum y Machine Learning para la predicción y priorización del riesgo de deserción estudiantil en la Institución Educativa Exellenti del distrito de El Tambo.*

El sistema **no sustituye** a tutoría. Calcula una probabilidad de deserción y una lista de atención. Los datos de este entorno son **sintéticos de tesis**, no el padrón real de la IE.

## Dónde entrar

El mismo sistema está publicado en dos sitios. El de uso es Vercel. Railway sirve la aplicación y guarda PostgreSQL.

| Sitio | Dirección |
|---|---|
| Vercel | https://tallerde-investigacion1.vercel.app |
| Ingreso en Vercel | https://tallerde-investigacion1.vercel.app/login |
| Railway | https://tallerdeinvestigacion1-production.up.railway.app |
| Ingreso en Railway | https://tallerdeinvestigacion1-production.up.railway.app/login |
| Estado de la base | agregue `/health` a cualquiera de las dos direcciones. Responde `{"ok": true, "db": "up"}` |
| Código | https://github.com/piero12876/TallerdeInvestigacion1 |

Repositorio `main`. Vercel despliega el sitio público. Railway despliega el servicio `TallerdeInvestigacion1` y la base Postgres del proyecto `zucchini-intuition`.

Para que los dos sitios vean los mismos datos:

- En el servicio web de Railway, `DATABASE_URL` es la variable interna de Postgres (`postgres.railway.internal`).
- En Vercel, `DATABASE_URL` es `DATABASE_PUBLIC_URL` (host `tramway.proxy.rlwy.net`). No pegue ahí la dirección interna.
- `EXELLENTI_SECRET` es la misma clave larga en Railway y en Vercel.

Las claves de abajo son del entorno de tesis. El sitio es público: quien abre el repositorio las ve.

## Arranque

```
http://127.0.0.1:3939
```

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
.venv\Scripts\python.exe run.py
```

o `run.bat`. Puerto **3939**.

Copie `.env.example` a `.env` y cambie `EXELLENTI_SECRET` si despliega fuera de localhost.

## Credenciales del entorno de tesis

No se muestran en la pantalla de ingreso. Sirven igual en Vercel y en Railway.

### Dirección

| Usuario | Clave | Nombre | Ve |
|---|---|---|---|
| `director` | `Dir#Ex26` | Edgar David Advincua Porras | Toda la IE: matrícula, evaluación, asistencia, alerta, citas, seguimientos, reportes, modelo, usuarios y backlog |

### Docentes de aula (1.° y 2.°, todas las áreas y tutoría)

| Usuario | Clave | Nombre | Salón |
|---|---|---|---|
| `maria.cerron` | `Doc1#Ex26` | María Cerrón Poma | 1.° A |
| `aula1b` | `Aul1B#Ex26` | Juana Taipe Rojas | 1.° B |
| `aula1c` | `Aul1C#Ex26` | Milagros Soto Quispe | 1.° C |
| `julio.palacios` | `Doc2#Ex26` | Julio Palacios Taipe | 2.° A |
| `aula2b` | `Aul2B#Ex26` | Henry Ñahui Poma | 2.° B |
| `aula2c` | `Aul2C#Ex26` | Karina Flores Aliaga | 2.° C |

### Docentes de área (3.° a 6.°, secciones A, B y C)

| Usuario | Clave | Nombre | Área |
|---|---|---|---|
| `ana.delacruz` | `Doc3#Ex26` | Ana De la Cruz Rojas | Comunicación |
| `carlos.meza` | `Doc4#Ex26` | Carlos Meza Huayta | Matemática |
| `rosa.vallejos` | `Doc7#Ex26` | Rosa Vallejos Chávez | Personal Social |
| `pedro.huayta` | `Doc6#Ex26` | Pedro Huayta Gamarra | Ciencia y Tecnología |
| `lucia.ramos` | `Doc5#Ex26` | Lucía Ramos Soto | Arte y Cultura, y Educación Física |
| `silvia.poma` | `Doc9#Ex26` | Silvia Poma Flores | Educación Religiosa |
| `miguel.limay` | `Doc10#Ex26` | Miguel Limaymanta Castro | Inglés |

### Tutores de salón (desde 3.°, no dictan áreas)

| Usuario | Clave | Salón |
|---|---|---|
| `hector.quispe` | `Doc8#Ex26` | 3.° A |
| `tutor3b` | `Tut#3BEx26` | 3.° B |
| `tutor3c` | `Tut#3CEx26` | 3.° C |
| `tutor4a` | `Tut#4AEx26` | 4.° A |
| `tutor4b` | `Tut#4BEx26` | 4.° B |
| `tutor4c` | `Tut#4CEx26` | 4.° C |
| `tutor5a` | `Tut#5AEx26` | 5.° A |
| `tutor5b` | `Tut#5BEx26` | 5.° B |
| `tutor5c` | `Tut#5CEx26` | 5.° C |
| `tutor6a` | `Tut#6AEx26` | 6.° A |
| `tutor6b` | `Tut#6BEx26` | 6.° B |
| `tutor6c` | `Tut#6CEx26` | 6.° C |

### Estudiantes con ingreso

El resto de alumnos existe en matrícula y no tiene usuario. Solo estos tres entran al sistema.

| Usuario | Clave | Ficha |
|---|---|---|
| `alumno31` | `Est31#Ex26` | 3.° A, caso de atención alta |
| `alumno38` | `Est38#Ex26` | 3.° A, rendimiento esperado |
| `alumno51` | `Est51#Ex26` | 5.° A, caso de atención alta |

El estudiante ve su ficha, sus notas, su asistencia, su tutor y quién dicta cada curso. No ve a los demás alumnos ni la lista de alerta.

## Qué ve cada rol

El menú no es fijo. `backend/domain/access.py` lo arma al entrar: mira el rol y, si es docente, si tiene cursos y si es tutor.

- **Dirección:** grupo Gestión (inicio, matrícula, evaluación, asistencia, alerta, seguimientos, agenda, reportes) y grupo Institución (mapa, personal, modelo, usuarios, bitácora, backlog).
- **Docente de aula (1.° y 2.°):** grupo Aula, con evaluación y asistencia. Ve solo su salón.
- **Docente de área (desde 3.°):** grupo Aula con evaluación de su curso. No ve asistencia si no es tutor.
- **Tutor desde 3.°:** grupo Aula con asistencia y sin evaluación. No dicta áreas.
- **Estudiante:** grupo Portal (inicio, mi ficha, mi boleta, mi asistencia). No ve a otros alumnos ni la lista de alerta.

Los tres roles ven **Sobre nosotros** (misión, visión, sedes) y **Cuenta** (cambiar contraseña y salir).

## Dos salidas distintas (importante para la tesis)

1. **Probabilidad y nivel del modelo** (`nivel_modelo`): umbrales 0.62 / 0.35 sobre `predict_proba`.
2. **Nivel de atención institucional** (`nivel_riesgo`): cupo por salón (1 alto, 4 medio, resto esperado) para ordenar tutoría.

No son lo mismo. La pantalla *Modelo predictivo* lo declara.

## Datos del entorno

- 18 salones (1.°–6.° × A/B/C), 8 alumnos activos por salón (144).
- 80 registros históricos sintéticos (28 desertores) para entrenar, con solapamiento de perfiles.
- 8 áreas CNEB. 1.° y 2.°: docente de aula. Desde 3.°: docentes de área.

## Machine Learning

Validación cruzada estratificada (OOF). Algoritmos: regresión logística, Naive Bayes, SVM, Random Forest, árboles impulsados. Métricas: Accuracy, Precision, Recall (± desvío), F1, ROC-AUC, PR-AUC y matriz de confusión OOF.

El balanceo es **réplica del minoritario solo en el fold de entrenamiento**. No es SMOTE. No cite las métricas como resultado sobre datos reales de la IE.

Fuentes: Chung y Lee (2019) CYSR; Lee y Chung (2019) Applied Sciences.

## Pruebas

```
.venv\Scripts\python.exe -m pytest
```

Cubren login, autorización por rol, persistencia de notas, ocultamiento de riesgo al alumno y rechazo CSRF.

## Arquitectura

El navegador no habla con la base ni con el modelo. Pide una ruta, FastAPI resuelve el permiso, lee o escribe datos y devuelve HTML. No hay una API JSON para el colegio: las pantallas son servidor (Jinja2).

```
navegador
    │
    ▼
run.py (computadora y Railway)  o  index.py (Vercel)
    │
    ▼
backend/main.py          sesión, estáticos, arranque, /health
    │
    ▼
backend/presentation     rutas y plantillas
    │
    ├── backend/domain   roles, menú, validaciones
    ├── backend/infrastructure   tablas, cuentas, semilla, seguridad
    └── ml/engine.py     entrenamiento y predicción
    │
    ▼
SQLite local  o  PostgreSQL en Railway
```

En la computadora la base es SQLite (`data/exellenti.db`). En Railway y Vercel la base es PostgreSQL. El modelo se entrena al arrancar Railway y al arrancar `run.py`. Vercel lee esa base y no vuelve a entrenar. Scrum organiza el desarrollo (`/scrum`); no es un tablero para el colegio.

### Carpetas

```
taller1/
├── frontend/          lo que se ve
│   ├── templates/     una plantilla Jinja2 por pantalla
│   └── static/        css, js, logo y fotos
├── backend/           la aplicación
│   ├── main.py        FastAPI, sesión y arranque
│   ├── config.py      rutas, puerto, secreto y base
│   ├── domain/        reglas que no dependen de la base
│   ├── infrastructure/  tablas, semilla, claves, estadísticas
│   └── presentation/  rutas HTTP y contexto de las plantillas
├── ml/                scikit-learn: entrena, elige y predice
├── data/              SQLite local (no se sube el .db)
├── tests/             pytest contra la aplicación
├── docs/              informe de uso en PDF y el script que lo genera
├── run.py             entrada local y de Railway (puerto 3939)
├── index.py           entrada de Vercel
├── Dockerfile         imagen de Railway, usuario no root
├── requirements.txt   dependencias de desarrollo
└── requirements.lock  las mismas, con hash, para el contenedor
```

No se versionan `.env`, `.venv/`, `data/*.db` ni `ml/*.joblib`. El modelo y la base local se crean al arrancar.

### `frontend/`

Plantillas en `frontend/templates/`. `base.html` es el marco: menú lateral, nombre de quien ingresó y el bloque de cada pantalla. `login.html` no usa ese marco.

| Plantilla | Ruta | Qué muestra |
|---|---|---|
| `login.html` | `/login` | Ingreso, mensaje de bienvenida y sedes |
| `dashboard.html` | `/` | Panel según el rol |
| `estudiantes.html` | `/estudiantes` | Padrón |
| `estudiante_form.html` | `/estudiantes/nuevo` y editar | Alta y edición de ficha |
| `estudiante_detalle.html` | `/estudiantes/{id}` | Ficha, notas, asistencia, alerta y seguimiento |
| `calificaciones.html` | `/calificaciones` | Notas 0–20 por bimestre |
| `asistencia.html` | `/asistencia` | Pase de lista y patrones |
| `riesgo.html` | `/riesgo` | Lista priorizada |
| `seguimientos.html` | `/seguimientos` | Notas de tutoría |
| `citas.html` | `/citas` | Agenda |
| `reportes.html` | `/reportes` | Tablas exportables, sin DNI ni teléfonos |
| `institucion.html` | `/institucion` | Mapa de la IE |
| `docentes.html` | `/docentes` | Cargas y tutores |
| `modelo.html` | `/modelo` | Métricas y reentrenamiento |
| `usuarios.html` | `/usuarios` | Cuentas |
| `auditoria.html` | `/auditoria` | Bitácora |
| `scrum.html` | `/scrum` | Product backlog |
| `sobre_nosotros.html` | `/sobre-nosotros` | Misión, visión y sedes |
| `mi_boleta.html` | `/mi-boleta` | Notas del alumno |
| `mi_asistencia.html` | `/mi-asistencia` | Asistencia del alumno |
| `cuenta.html` | `/cuenta` | Cambio de contraseña |
| `_csrf.html` | — | Marca que viaja en cada formulario |

`frontend/static/css/app.css` define la interfaz. `frontend/static/js/app.js` filtra tablas y confirma acciones. `charts.js` dibuja las barras a partir de `data-bars`. Las fotos son `logo-exellenti.png`, `colegio-exellenti.png` (fondo del ingreso) y `colegio-nosotros.png` (fondo de Sobre nosotros).

### `backend/`

Cuatro capas. Una ruta no abre SQL a mano fuera de infraestructura, y el dominio no importa plantillas.

**`backend/main.py`.** Crea la aplicación, cuelga la carpeta `frontend/static` en `/static`, registra las rutas y la cookie `exellenti_session` (ocho horas). Al arrancar: si el esquema cambió, reinicia la base local; crea tablas; si no hay usuarios, siembra el entorno; completa bimestres vacíos; entrena el modelo salvo que `EXELLENTI_SKIP_ML` esté activo o el proceso sea Vercel. `/health` responde `{"ok": true, "db": "up"}`.

**`backend/config.py`.** Resuelve carpetas, año lectivo 2026, institución y puerto. Sin `DATABASE_URL` usa SQLite. Si la variable empieza por `postgres://`, la pasa a `postgresql+psycopg` y exige SSL fuera de localhost y de la red interna de Railway. `EXELLENTI_SECRET` firma la sesión. En Railway o Vercel una clave débil detiene el arranque. `SCHEMA_VERSION` está en `2026-9`: si `data/schema.txt` no coincide, la base local se vuelve a crear.

**`backend/domain/`.** Reglas puras.

| Archivo | Responsabilidad |
|---|---|
| `enums.py` | Roles, estados del alumno, asistencia, niveles de riesgo y etiquetas en español. El código interno del director sigue siendo `directora`; en pantalla se lee Director. |
| `access.py` | Quién ve riesgo, quién edita y el menú de cada rol. |
| `validate.py` | DNI de 8 dígitos, celular peruano de 9 que empieza por 9, nombres sin números, usuario, contraseña y filtros de búsqueda. |

**`backend/infrastructure/`.** Persistencia y datos de arranque.

| Archivo | Responsabilidad |
|---|---|
| `database.py` | Modelos SQLAlchemy y la sesión. Tablas: `User`, `SchoolGrade`, `Course`, `TeacherProfile`, `TeacherAssignment`, `Student`, `GradeRecord`, `AttendanceRecord`, `TutoringAppointment`, `FollowUp`, `Prediction`, `ModelRun`, `BacklogItem`, `AuditLog`. |
| `accounts.py` | Usuarios y claves del entorno de tesis. La clave viaja en el campo `clave`, no en uno llamado password. |
| `seed.py` | Si la base está vacía, crea salones, áreas, docentes, 144 alumnos, notas, asistencia, citas y el backlog. Si ya hay datos, solo actualiza la cuenta `director` (Edgar David Advincua Porras) sin borrar la matrícula. |
| `security.py` | Contraseñas con PBKDF2-SHA256, marca CSRF y un límite simple de intentos de ingreso. |
| `stats.py` | Conteos del panel, de la institución y de la carga docente. |

**`backend/presentation/`.** `web.py` declara cada ruta GET y POST. `deps.py` lee la sesión, arma el contexto de la plantilla (usuario, menú, año, flash) y limita la matrícula a los salones del docente. Un POST sin la marca CSRF vuelve atrás sin guardar.

### `ml/`

`ml/engine.py` arma, por alumno, promedio, nota mínima, áreas desaprobadas, tendencia (bimestre 4 menos bimestre 1), porcentaje de asistencia, faltas, tardanzas, justificadas y grado. Compara regresión logística, Naive Bayes, SVM, Random Forest y árboles impulsados con validación cruzada estratificada. Guarda el elegido en `ml/modelo_desercion.joblib` y escribe `Prediction` y `ModelRun`. La pantalla `/modelo` explica que el nivel del modelo y el cupo de atención por salón no son la misma salida.

### `data/`, pruebas y despliegue

`data/` solo necesita existir. El `.db` y `schema.txt` los crea el arranque y git los ignora.

`tests/conftest.py` levanta la aplicación con `EXELLENTI_TESTING` y sin entrenar. `tests/test_app.py` cubre ingreso, permisos, notas, el ocultamiento de la alerta al alumno y el rechazo CSRF.

| Archivo | Para qué está |
|---|---|
| `run.py` / `run.bat` | Uvicorn en `127.0.0.1:3939`. En Railway el host pasa a `0.0.0.0` y el puerto lo pone `PORT`. |
| `index.py` | Vercel importa `backend.main:app` y conserva la ruta original. |
| `vercel.json` | La función de `index.py`, 60 s y 1024 MB. |
| `Dockerfile` | Python 3.12, dependencias con hash, copia `backend`, `frontend` y `ml`, usuario `appuser`. |
| `railway.toml` | Cómo Railway construye y arranca el servicio. |
| `docs/Informe-de-uso-IE-Exellenti.pdf` | Manual de uso con las pantallas. `docs/generar_informe.py` lo vuelve a armar. |

### Cómo viaja una acción

1. La persona envía el formulario. El navegador incluye la cookie de sesión y la marca CSRF.
2. `web.py` busca al usuario. Si no hay sesión, redirige a `/login`. Si el rol no alcanza, redirige al inicio con error de permiso.
3. `validate.py` revisa el dato. Si falla, la misma pantalla vuelve con el aviso; no hay un error crudo de FastAPI.
4. Infraestructura escribe la fila y, cuando corresponde, una línea de bitácora.
5. La respuesta es un redirect (303) o la plantilla ya renderizada. El navegador no recibe JSON.
