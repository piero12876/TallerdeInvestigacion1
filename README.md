# Sistema web IE Exellenti

Plan de tesis: *Desarrollo de un sistema web mediante Scrum y Machine Learning para la predicción y priorización del riesgo de deserción estudiantil en la Institución Educativa Exellenti del distrito de El Tambo.*

El sistema **no sustituye** a tutoría. Calcula una probabilidad de deserción y una lista de atención. Los datos de este entorno son **sintéticos de tesis**, no el padrón real de la IE.

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

No se muestran en la pantalla de ingreso. Dirección las entrega como en SIAGIE.

| Usuario | Clave | Rol |
|---|---|---|
| `directora` | `Dir#Ex26` | Dirección (ve y gestiona toda la IE) |
| `maria.cerron` | `Doc1#Ex26` | Aula 1.° A (todas las áreas y tutora) |
| `carlos.meza` | `Doc4#Ex26` | Matemática 3.°–6.° |
| `hector.quispe` | `Doc8#Ex26` | Tutor 3.° A (solo encargado) |
| `alumno31` | `Est31#Ex26` | Estudiante (ficha, notas, tutor y atención) |
| `alumno38` | `Est38#Ex26` | Estudiante |

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

Monolito en capas: `app/domain`, `app/infrastructure`, `app/presentation`. FastAPI + SQLite + Jinja2 + scikit-learn. Scrum organiza el desarrollo (`/scrum`); no es un tablero para el colegio.
