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
| `directora` | `Dir#Ex26` | Rosa Elena Huamán Cerrón | Toda la IE: matrícula, evaluación, asistencia, alerta, citas, seguimientos, reportes, modelo, usuarios y backlog |

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

- **Dirección:** matrícula, evaluación, asistencia, alerta, personal, modelo, usuarios y backlog.
- **Docente de aula (1.° y 2.°):** todas las áreas de su salón, pase de lista y tutoría.
- **Docente de área (desde 3.°):** solo los cursos y salones que dicta. No toma asistencia si no es tutor.
- **Tutor desde 3.°:** encargado del salón (matrícula, asistencia, alerta). No dicta áreas.
- **Estudiante:** su tutor, quién le enseña cada curso, sus notas y su nivel de atención. No ve a otros alumnos.

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

```
frontend/     plantillas Jinja2 y CSS/JS
backend/      FastAPI, dominio, reglas de negocio y PostgreSQL o SQLite
ml/           entrenamiento y predicción (scikit-learn)
data/         SQLite local y versión de esquema
index.py      entrada de Vercel
```

FastAPI sirve las vistas de `frontend/`. En la computadora la base es SQLite. En Railway y Vercel la base es PostgreSQL. El modelo se entrena al arrancar Railway. Vercel lee esa base y no vuelve a entrenar. Scrum organiza el desarrollo (`/scrum`); no es un tablero para el colegio.
