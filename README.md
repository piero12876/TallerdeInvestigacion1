# Sistema web IE Exellenti

Plan de tesis: *Desarrollo de un sistema web mediante Scrum y Machine Learning para la predicción y priorización del riesgo de deserción estudiantil en la Institución Educativa Exellenti del distrito de El Tambo.*

El sistema no sustituye a tutoría. Calcula una probabilidad de deserción y ordena una lista de atención. Los alumnos, las notas y la asistencia de este entorno son sintéticos. No son el padrón real de la IE.

Año lectivo **2026**. Primaria de 1.° a 6.°, secciones A, B y C (18 salones, 8 alumnos activos por salón, 144 en total).

## Dónde entrar

| Sitio | Dirección |
|---|---|
| Computadora | http://127.0.0.1:3939 |
| Ingreso local | http://127.0.0.1:3939/login |
| Vercel (uso público) | https://tallerde-investigacion1.vercel.app |
| Ingreso en Vercel | https://tallerde-investigacion1.vercel.app/login |
| Railway (aplicación y PostgreSQL) | https://tallerdeinvestigacion1-production.up.railway.app |
| Ingreso en Railway | https://tallerdeinvestigacion1-production.up.railway.app/login |
| Estado de la base | agregue `/health`. Responde `{"ok": true, "db": "up"}` |
| Código | https://github.com/piero12876/TallerdeInvestigacion1 |

Repositorio `main`. Vercel publica el sitio. Railway despliega el servicio `TallerdeInvestigacion1` y la base Postgres del proyecto `zucchini-intuition`.

Para que Vercel y Railway vean los mismos datos:

- En el servicio web de Railway, `DATABASE_URL` es la variable interna de Postgres (`postgres.railway.internal`).
- En Vercel, `DATABASE_URL` es `DATABASE_PUBLIC_URL` (host `tramway.proxy.rlwy.net`). No pegue ahí la dirección interna.
- `EXELLENTI_SECRET` es la misma clave larga en Railway y en Vercel.

El manual con capturas está en `docs/Informe-de-uso-IE-Exellenti.pdf`.

## Arranque en la computadora

Hace falta Python 3.12, con `python.exe` en el PATH.

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
.venv\Scripts\python.exe run.py
```

También vale `run.bat`. El puerto es **3939**. `run.py` llama a Uvicorn con `backend.main:app`.

Copie `.env.example` a `.env`. En localhost puede quedar la clave de desarrollo. Fuera de localhost, `EXELLENTI_SECRET` tiene que ser una clave larga propia: si Railway o Vercel arrancan con la clave de ejemplo, el proceso se detiene.

## Credenciales vigentes

La cuenta de dirección **ya no es** `directora` ni Rosa Elena Huamán Cerrón. Esas credenciales no entran.

La cuenta vigente es:

| Usuario | Clave | Nombre en pantalla | Rol que se lee |
|---|---|---|---|
| `director` | `Dir#Ex26` | Edgar David Advincua Porras | Director |

El código interno del rol sigue siendo `directora` para no romper permisos y plantillas. En el menú, en Usuarios y en el costado se lee **Director**. Si la base local ya existía con el usuario viejo, al arrancar `seed.py` lo renombra a `director` y le pone el nombre de Edgar David Advincua Porras, sin borrar la matrícula.

La pantalla de ingreso no muestra estas claves. Sirven igual en la computadora, en Vercel y en Railway. Quien abre el repositorio las ve: son del entorno de tesis.

### Dirección

| Usuario | Clave | Nombre | Ve |
|---|---|---|---|
| `director` | `Dir#Ex26` | Edgar David Advincua Porras | Toda la IE: matrícula, evaluación, asistencia, alerta, citas, seguimientos, reportes, modelo, usuarios, bitácora y backlog |

### Docentes de aula (1.° y 2.°, las ocho áreas y la tutoría)

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

| Usuario | Clave | Nombre | Salón |
|---|---|---|---|
| `hector.quispe` | `Doc8#Ex26` | Héctor Quispe Ñahui | 3.° A |
| `tutor3b` | `Tut#3BEx26` | Raúl Gamarra Huayta | 3.° B |
| `tutor3c` | `Tut#3CEx26` | Pilar Chávez Cerrón | 3.° C |
| `tutor4a` | `Tut#4AEx26` | Edwin Huaroc Torres | 4.° A |
| `tutor4b` | `Tut#4BEx26` | Nancy Vilchez Castro | 4.° B |
| `tutor4c` | `Tut#4CEx26` | Walter Limaymanta Soto | 4.° C |
| `tutor5a` | `Tut#5AEx26` | Gloria Ramírez Quispe | 5.° A |
| `tutor5b` | `Tut#5BEx26` | Ivonne Palacios Meza | 5.° B |
| `tutor5c` | `Tut#5CEx26` | Fredy Cóndor Rojas | 5.° C |
| `tutor6a` | `Tut#6AEx26` | Elena Taipe Soto | 6.° A |
| `tutor6b` | `Tut#6BEx26` | Marco Aliaga Huamán | 6.° B |
| `tutor6c` | `Tut#6CEx26` | Patricia Rojas Cerrón | 6.° C |

### Estudiantes con ingreso

El resto de alumnos existe en matrícula y no tiene usuario. Solo estos tres entran.

| Usuario | Clave | Ficha |
|---|---|---|
| `alumno31` | `Est31#Ex26` | 3.° A, caso de atención alta |
| `alumno38` | `Est38#Ex26` | 3.° A, rendimiento esperado |
| `alumno51` | `Est51#Ex26` | 5.° A, caso de atención alta |

## Menú de cada rol

`backend/domain/access.py` arma el menú al entrar. El docente no tiene un menú único: si tiene cursos asignados ve Evaluación; si es tutor de un salón ve Asistencia.

### Dirección (`director`)

Grupo **Gestión:** Inicio, Matrícula, Evaluación, Asistencia, Alerta temprana, Seguimientos, Agenda de atención, Reportes.

Grupo **Institución:** La institución, Personal docente, Modelo predictivo, Usuarios institucionales, Bitácora, Product Backlog.

Grupo **Sobre nosotros:** Sobre nosotros.

Grupo **Cuenta:** Cambiar contraseña, Salir.

### Docente de aula (1.° y 2.°)

Grupo **Aula:** Inicio, Matrícula de su salón, Evaluación de las ocho áreas, Asistencia, Alerta temprana, Seguimientos, Agenda de atención, Reportes. Luego Sobre nosotros y Cuenta. No ve Institución.

### Docente de área (desde 3.°)

Grupo **Aula:** Inicio, Matrícula de los salones donde dicta, Evaluación solo de su área, Alerta, Seguimientos, Agenda y Reportes de esa carga. No aparece Asistencia, porque no es tutor. Luego Sobre nosotros y Cuenta.

### Tutor de salón (desde 3.°)

Grupo **Aula:** Inicio, Matrícula de su salón, Asistencia, Alerta, Seguimientos, Agenda y Reportes. No aparece Evaluación, porque no dicta áreas. Luego Sobre nosotros y Cuenta.

### Estudiante

Grupo **Portal:** Inicio, Mi ficha, Mi boleta, Mi asistencia. Luego Sobre nosotros y Cuenta. No ve compañeros, alerta institucional, usuarios ni modelo. Mi ficha redirige a su propia ficha de matrícula.

## Qué hace cada módulo

| Menú | Ruta | Función |
|---|---|---|
| Inicio | `/` | Panel del rol. En dirección: matrícula, promedio, asistencia, casos altos, citas y los cinco primeros de la lista |
| Matrícula | `/estudiantes` | Padrón: identidad, domicilio, apoderado y tipo. El riesgo no se consulta aquí |
| Nueva matrícula | `/estudiantes/nuevo` | Alta tipo SIAGIE. DNI de 8 dígitos. Celular de 9 que empieza por 9. Nombres sin números |
| Ficha | `/estudiantes/{id}` | Tutor, docentes por curso, notas, asistencia, los dos niveles de alerta y alta de seguimiento |
| Evaluación | `/calificaciones` | Nota 0–20 por área y por los cuatro bimestres |
| Asistencia | `/asistencia` | Pase de lista (presente, falta, tardanza, justificada) y patrones de inasistencia |
| Alerta temprana | `/riesgo` | Probabilidad del modelo y nivel de atención. Exporta CSV |
| Seguimientos | `/seguimientos` | Notas de tutoría por tipo y estado. El alta se hace en la ficha |
| Agenda de atención | `/citas` | Cita por fecha y canal (presencial, llamada o virtual) |
| Reportes | `/reportes` | Priorizados, rendimiento, asistencia, padrón y correlación. CSV e impresión, sin DNI ni teléfonos |
| La institución | `/institucion` | Mapa de salones, usuarios por rol y cadena de la IE |
| Personal docente | `/docentes` | Quién es tutor y qué área dicta |
| Modelo predictivo | `/modelo` | Comparación de algoritmos y botón de reentrenar |
| Usuarios institucionales | `/usuarios` | Cuentas. Alta de docente o estudiante. Activar o desactivar, menos la sesión propia |
| Bitácora | `/auditoria` | Últimas acciones, sin claves ni DNI |
| Product Backlog | `/scrum` | Historias Scrum del desarrollo. No es una herramienta del colegio |
| Sobre nosotros | `/sobre-nosotros` | Misión, visión y teléfonos, con la foto del colegio de fondo |
| Mi boleta | `/mi-boleta` | Notas del alumno que ingresó |
| Mi asistencia | `/mi-asistencia` | Marcas del alumno que ingresó |
| Cambiar contraseña | `/cuenta` | Clave nueva de al menos 8 caracteres, con letras y números |
| Salir | `/logout` | Cierra la sesión |

Sedes en el ingreso y en Sobre nosotros: Chupaca 981 819 115, Huancayo 981 819 112, Cajas 981 819 113.

## Dos salidas del modelo

No son la misma cifra. La pantalla Modelo predictivo lo declara.

1. **Probabilidad y nivel del modelo** (`nivel_modelo`). Umbrales 0.62 y 0.35 sobre `predict_proba`.
2. **Nivel de atención institucional** (`nivel_riesgo`). Cupo por salón: 1 alto, 4 medios y el resto en nivel esperado, para ordenar la tutoría.

Variables: promedio, nota mínima, áreas desaprobadas, tendencia (bimestre 4 menos bimestre 1), porcentaje de asistencia, faltas no justificadas, tardanzas, justificadas y grado.

Entrenamiento: 80 registros históricos sintéticos, 28 desertores. Validación cruzada estratificada de 5 pliegues, con predicciones fuera de cada pliegue (OOF). Algoritmos: regresión logística, Naive Bayes, SVM, Random Forest y árboles impulsados. Métricas: Accuracy, Precision, Recall con desviación, F1, ROC-AUC, PR-AUC y matriz de confusión. El balanceo replica la clase minoritaria solo dentro del pliegue de entrenamiento. No es SMOTE. No cite esas métricas como resultado sobre datos reales de la IE.

Fuentes citadas en la pantalla: Chung y Lee (2019), *Children and Youth Services Review*; Lee y Chung (2019), *Applied Sciences*.

## Arquitectura

El navegador pide una ruta. FastAPI resuelve el permiso, lee o escribe y devuelve HTML. No hay una API JSON para el colegio.

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
    ├── backend/domain          roles, menú, validaciones
    ├── backend/infrastructure  tablas, cuentas, semilla, seguridad
    └── ml/engine.py            entrenamiento y predicción
    │
    ▼
SQLite local  o  PostgreSQL en Railway
```

En la computadora la base es SQLite (`data/exellenti.db`). En Railway y Vercel la base es PostgreSQL. El modelo se entrena al arrancar `run.py` y al arrancar Railway. Vercel lee esa base y no vuelve a entrenar.

### Carpetas

```
TallerdeInvestigacion1/
├── frontend/                 lo que se ve
│   ├── templates/            una plantilla Jinja2 por pantalla
│   └── static/               css, js, logo y fotos
├── backend/                  la aplicación
│   ├── main.py               FastAPI, sesión y arranque
│   ├── config.py             rutas, puerto, secreto y base
│   ├── domain/               reglas que no dependen de la base
│   ├── infrastructure/       tablas, semilla, claves, estadísticas
│   └── presentation/         rutas HTTP y contexto de las plantillas
├── ml/                       scikit-learn: entrena, elige y predice
├── data/                     SQLite local (el .db no se sube)
├── tests/                    pytest contra la aplicación
├── docs/                     informe de uso en PDF
├── run.py                    entrada local y de Railway
├── run.bat                   mismo arranque en Windows
├── index.py                  entrada de Vercel
├── Dockerfile                imagen de Railway, usuario no root
├── railway.toml              construcción y healthcheck /health
├── vercel.json               función de index.py, 60 s y 1024 MB
├── requirements.txt          dependencias de desarrollo
├── requirements.lock         las mismas, con hash, para el contenedor
├── .env.example              variables de ejemplo
└── .gitignore                ignora .env, .venv, *.db y *.joblib
```

### `frontend/`

`base.html` es el marco: menú, nombre de quien ingresó y el contenido. `login.html` no usa ese marco. `_csrf.html` mete la marca en cada formulario que modifica datos.

| Plantilla | Ruta |
|---|---|
| `login.html` | `/login` |
| `dashboard.html` | `/` |
| `estudiantes.html` | `/estudiantes` |
| `estudiante_form.html` | `/estudiantes/nuevo` y editar |
| `estudiante_detalle.html` | `/estudiantes/{id}` y, de rebote, `/mi-ficha` |
| `calificaciones.html` | `/calificaciones` |
| `asistencia.html` | `/asistencia` |
| `riesgo.html` | `/riesgo` |
| `seguimientos.html` | `/seguimientos` |
| `citas.html` | `/citas` |
| `reportes.html` | `/reportes` |
| `institucion.html` | `/institucion` |
| `docentes.html` | `/docentes` |
| `modelo.html` | `/modelo` |
| `usuarios.html` | `/usuarios` |
| `auditoria.html` | `/auditoria` |
| `scrum.html` | `/scrum` |
| `sobre_nosotros.html` | `/sobre-nosotros` |
| `mi_boleta.html` | `/mi-boleta` |
| `mi_asistencia.html` | `/mi-asistencia` |
| `cuenta.html` | `/cuenta` |

`frontend/static/css/app.css` define la interfaz. `app.js` filtra tablas y confirma acciones. `charts.js` dibuja las barras leídas de `data-bars`. Fotos: `logo-exellenti.png`, `colegio-exellenti.png` (fondo del ingreso) y `colegio-nosotros.png` (fondo de Sobre nosotros).

### `backend/`

**`main.py`.** Cuelga `frontend/static` en `/static`, registra las rutas y la cookie `exellenti_session` (ocho horas). Al arrancar: si cambió `SCHEMA_VERSION`, reinicia la base local; crea tablas; si no hay usuarios, siembra el entorno; si ya hay usuarios, actualiza la cuenta del director; completa bimestres vacíos; entrena salvo `EXELLENTI_SKIP_ML` o Vercel.

**`config.py`.** Año 2026, puerto 3939, institución y distrito. Sin `DATABASE_URL` usa SQLite. Una URL `postgres://` pasa a `postgresql+psycopg` y, fuera de localhost y de `*.railway.internal`, exige SSL. `SCHEMA_VERSION` actual: `2026-9`.

**`domain/`**

| Archivo | Responsabilidad |
|---|---|
| `enums.py` | Roles, estados del alumno, asistencia, niveles y etiquetas. `directora` se muestra como Director |
| `access.py` | Menú y permisos de edición, riesgo, reportes, usuarios, bitácora y backlog |
| `validate.py` | DNI, celular, nombres, usuario, contraseña y filtros |

**`infrastructure/`**

| Archivo | Responsabilidad |
|---|---|
| `database.py` | Modelos: `User`, `SchoolGrade`, `Course`, `TeacherProfile`, `TeacherAssignment`, `Student`, `GradeRecord`, `AttendanceRecord`, `TutoringAppointment`, `FollowUp`, `Prediction`, `ModelRun`, `BacklogItem`, `AuditLog` |
| `accounts.py` | Usuarios y claves de este README. El campo se llama `clave` |
| `seed.py` | Salones, áreas, 144 alumnos, notas, asistencia, citas y backlog. También el renombre `directora` → `director` |
| `security.py` | PBKDF2-SHA256, marca CSRF y límite de intentos de ingreso |
| `stats.py` | Conteos del panel, de la institución y de la carga docente |

**`presentation/`.** `web.py` declara cada GET y POST. `deps.py` lee la sesión, arma el contexto (usuario, menú, año, avisos) y limita al docente a sus salones. Un POST sin CSRF no guarda.

### `ml/`

`ml/engine.py` compara los cinco algoritmos, elige por recall y F1, guarda `ml/modelo_desercion.joblib` y escribe `Prediction` y `ModelRun`. Ese archivo no se versiona: se crea al arrancar.

### Cómo viaja una acción

1. El formulario envía la cookie de sesión y la marca CSRF.
2. `web.py` busca al usuario. Sin sesión, va a `/login`. Sin permiso, vuelve al inicio.
3. `validate.py` revisa el dato. Si falla, la misma pantalla vuelve con el aviso.
4. Infraestructura escribe la fila y, cuando corresponde, una línea de bitácora.
5. La respuesta es HTML o un redirect 303. El navegador no recibe JSON de negocio.

## Pruebas

```
.venv\Scripts\python.exe -m pytest
```

`tests/conftest.py` levanta la aplicación con `EXELLENTI_TESTING` y sin entrenar. `tests/test_app.py` cubre el ingreso de `director`, los permisos, la persistencia de notas, el ocultamiento de la alerta al alumno y el rechazo CSRF.

## Qué no se sube a Git

`.env`, `.venv/`, `data/*.db`, `data/schema.txt` y `ml/*.joblib`. El modelo y la base local se crean al arrancar.
