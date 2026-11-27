# -*- coding: utf-8 -*-
"""Informe de uso del sistema web IE Exellenti."""
from pathlib import Path

from fpdf import FPDF

IMG = Path(r"C:\Users\HP\AppData\Local\Temp\cursor\screenshots")
OUT = Path(__file__).resolve().parent / "Informe-de-uso-IE-Exellenti.pdf"
FONT = Path(r"C:\Windows\Fonts")


class Informe(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Arial", "", 9)
        self.set_text_color(61, 75, 96)
        self.set_x(self.l_margin)
        self.cell(0, 6, "IE Exellenti  ·  Informe de uso del sistema web", align="L")
        self.ln(3)
        self.set_draw_color(196, 161, 90)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y(), 210 - self.r_margin, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-12)
        self.set_font("Arial", "", 9)
        self.set_text_color(61, 75, 96)
        self.cell(0, 8, str(self.page_no()), align="C")

    def h1(self, text):
        self.set_x(self.l_margin)
        self.ln(1)
        self.set_font("Arial", "B", 16)
        self.set_text_color(30, 58, 95)
        self.multi_cell(0, 8, text)
        self.ln(1)

    def h2(self, text):
        self.set_x(self.l_margin)
        self.ln(1)
        self.set_font("Arial", "B", 13)
        self.set_text_color(18, 32, 51)
        self.multi_cell(0, 7, text)
        self.ln(1)

    def p(self, text):
        self.set_x(self.l_margin)
        self.set_font("Arial", "", 11)
        self.set_text_color(18, 32, 51)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def bullets(self, items):
        self.set_font("Arial", "", 11)
        self.set_text_color(18, 32, 51)
        for item in items:
            self.set_x(self.l_margin)
            self.multi_cell(0, 6, "- " + item)
        self.ln(2)

    def figure(self, name, caption):
        path = IMG / name
        if not path.exists():
            self.p("Captura no incluida: " + name)
            return
        if self.get_y() > 150:
            self.add_page()
        self.set_x(self.l_margin)
        self.image(str(path), w=174)
        self.ln(1)
        self.set_x(self.l_margin)
        self.set_font("Arial", "", 9)
        self.set_text_color(61, 75, 96)
        self.multi_cell(0, 5, caption)
        self.ln(3)

    def rows(self, headers, data, widths):
        self.set_font("Arial", "B", 10)
        self.set_fill_color(30, 58, 95)
        self.set_text_color(255, 255, 255)
        self.set_x(self.l_margin)
        for h, w in zip(headers, widths):
            self.cell(w, 7, h, border=0, fill=True)
        self.ln(7)
        self.set_font("Arial", "", 10)
        self.set_text_color(18, 32, 51)
        fill = False
        for row in data:
            if self.get_y() > 265:
                self.add_page()
            if fill:
                self.set_fill_color(246, 241, 228)
            else:
                self.set_fill_color(255, 253, 248)
            self.set_x(self.l_margin)
            for value, w in zip(row, widths):
                self.cell(w, 7, value, border=0, fill=True)
            self.ln(7)
            fill = not fill
        self.ln(3)


def build():
    pdf = Informe(format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(18, 18, 18)
    pdf.add_font("Arial", "", str(FONT / "arial.ttf"))
    pdf.add_font("Arial", "B", str(FONT / "arialbd.ttf"))

    pdf.add_page()
    pdf.set_fill_color(30, 58, 95)
    pdf.rect(0, 0, 210, 92, "F")
    pdf.set_y(22)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 7, "INSTITUCIÓN EDUCATIVA EXELLENTI", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, "El Tambo  ·  Huancayo  ·  PriMaría 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Arial", "B", 22)
    pdf.multi_cell(0, 10, "Informe de uso\ndel sistema web", align="C")
    pdf.set_y(102)
    pdf.set_text_color(18, 32, 51)
    pdf.p(
        "Manual de funciónamiento del sistema de alerta de deserción estudiantil. "
        "Explica para que sirve el software, como se ingresa, que ve cada rol y que hace "
        "cada entrada del menú. Las capturas son del entorno local de tesis, tomadas el 26 de noviembre de 2026."
    )
    pdf.p(
        "Los alumnos, las notas y la asistencia de este entorno son sintéticos. No son el padrón real de la IE. "
        "El sistema no reemplaza la tutoría: calcula una probabilidad y ordena los casos para que el tutor atienda primero a quien más lo necesita."
    )
    pdf.h2("Como leer este informe")
    pdf.bullets([
        "Los capítulos 4 y 5 describen los roles y el menú completo de cada uno.",
        "Del capítulo 6 en adelante, cada módulo del menú tiene su función, quien puede usarlo y una captura cuando la pantalla es la de dirección.",
        "El capítulo del modelo separa la probabilidad del algoritmo y el nivel de atención del salón.",
        "Las claves del final son las del entorno de tesis. En un colegio real, dirección las entrega por un canal seguro y no se muestran en pantalla.",
    ])

    pdf.add_page()
    pdf.h1("1. Para que sirve el sistema")
    pdf.p(
        "El plan de tesis define el producto así: desarrollo de un sistema web mediante Scrum y Machine Learning "
        "para la predicción y priorización del riesgo de deserción estudiantil en la Institución Educativa Exellenti del distrito de El Tambo."
    )
    pdf.p(
        "En la práctica, el sistema junta en un solo sitio la matrícula de primaria, las notas de los cuatro bimestres, "
        "el pase de lista, la agenda de citas con la familia y una lista priorizada de atención. Dirección ve los 18 salónes. "
        "Cada docente ve solo su carga. El estudiante ve solo su ficha, su boleta y su asistencia."
    )
    pdf.h2("Problema que atiende")
    pdf.p(
        "Cuando las notas bajan y las faltas se acumulan, la tutoría llega tarde si la informacion esta repartida en cuadernos y hojas de calculo. "
        "El sistema convierte esas senales en una lista ordenada. El tutor no tiene que revisar uno por uno a los 144 alumnos para saber por donde empezar."
    )
    pdf.h2("Que hace")
    pdf.bullets([
        "Guarda la ficha de matrícula: identidad, domicilio, apoderado, lengua, tipo de matrícula y necesidades educativas.",
        "Registra la nota vigesimal (0 a 20) de ocho áreas del CNEB, en cuatro bimestres.",
        "Registra la asistencia del dia: presente, tardanza, falta o falta justificada.",
        "Estima una probabilidad de deserción a partir de rendimiento y asistencia.",
        "Asigna un cupo de atención por salón para que la tutoría tenga un orden.",
        "Deja constancia del seguimiento y de la cita con la familia.",
        "Exporta reportes en CSV y permite imprimirlos, sin publicar DNI ni teléfonos en esos reportes.",
    ])
    pdf.h2("Que no hace")
    pdf.bullets([
        "No decide que un alumno sea desertor. Ese estado lo registra una persona, en la ficha.",
        "No sustituye el juicio del tutor ni de dirección.",
        "No muestra las contraseñas guardadas. Solo se entregan al crear la cuenta.",
        "No deja que un estudiante vea la lista de sus compañeros ni la alerta de otros salónes.",
        "No entrena el modelo en Vercel. El entrenamiento ocurre al arrancar el servicio de Railway, o en la computadora local.",
    ])

    pdf.add_page()
    pdf.h1("2. Donde se abre y como se ingresa")
    pdf.p("El mismo sistema tiene tres puertas. Los datos de tesis coinciden entre el sitio publico y Railway cuando las variables de entorno apuntan a la misma base.")
    pdf.rows(
        ["Sitio", "Dirección"],
        [
            ["Computadora", "http://127.0.0.1:3939"],
            ["Uso publico", "tallerde-investigacion1.vercel.app"],
            ["Servicio", "tallerdeinvestigacion1-production.up.railway.app"],
            ["Código", "github.com/piero12876/TallerdeInvestigacion1"],
        ],
        [45, 129],
    )
    pdf.p(
        "Agregar /health al final de la dirección responde si la base esta activa. "
        "En la computadora se arranca con el entorno virtual y el archivo run.py, en el puerto 3939. "
        "Antes hace falta copiar .env.example a .env."
    )
    pdf.p(
        "La pantalla de ingreso no lista usuarios ni claves. Muestra el mensaje de bienvenida, la foto del colegio, "
        "el logo y los teléfonos de las tres sedes. Quien no tiene cuenta lo pide a dirección."
    )
    pdf.figure("09-ingreso.png", "Figura 1. Ingreso. A la izquierda el mensaje institucional y las sedes; a la derecha el formulario.")
    pdf.h2("Sedes que aparecen al ingresar")
    pdf.rows(
        ["Sede", "Teléfono"],
        [["Chupaca", "981 819 115"], ["Huancayo", "981 819 112"], ["Cajas", "981 819 113"]],
        [87, 87],
    )
    pdf.p(
        "Después de un ingreso correcto, la sesión queda en una cookie del navegador. "
        "Salir esta al final del menú, en el grupo Cuenta. Si la sesión vence o se cierra, cualquier módulo redirige otra vez al ingreso."
    )
    pdf.p(
        "Cada formulario que modifica datos lleva una marca contra envios cruzados. "
        "Si esa marca no coincide, el sistema no guarda el cambio. Las contraseñas se guardan con un resumen, nunca en claro."
    )

    pdf.add_page()
    pdf.h1("3. Los roles, en una mirada")
    pdf.p(
        "Hay tres roles de ingreso: director, docente y estudiante. El docente no es un solo tipo de trabajo. "
        "Según la carga que dirección le asigna, el mismo rol docente se comporta de tres maneras."
    )
    pdf.rows(
        ["Rol de ingreso", "Quien es en el colegio", "Alcance"],
        [
            ["Director", "Edgar David Advincua Porras", "Toda la IE"],
            ["Docente", "Aula, área o tutor", "Solo su carga"],
            ["Estudiante", "Alumno con usuario", "Solo su ficha"],
        ],
        [40, 70, 64],
    )
    pdf.h2("Las tres formas del docente")
    pdf.p(
        "En primero y segundo grado hay un docente de aula. Dicta las ocho áreas de su sección y, además, es el tutor. "
        "Por eso su menú incluye Evaluación y Asistencia."
    )
    pdf.p(
        "Desde tercero, el trabajo se parte. El especialista de área dicta un curso (a veces dos) en varios grados y secciones. "
        "Puede registrar notas de esos cursos. No pasa lista, salvo que también sea tutor de algún salón."
    )
    pdf.p(
        "El tutor de tercero a sexto es el encargado del salón. Ve la matrícula de su grupo, pasa lista, mira la alerta, "
        "anota seguimientos y cita a la familia. No dicta áreas, así que el menú no le muestra Evaluación."
    )
    pdf.h2("Por que el menú cambia")
    pdf.p(
        "El menú no es una lista fija. Al ingresar, el sistema mira el rol y, si es docente, mira si tiene cursos asignados y si es tutor de algún salón. "
        "Eso evita que un especialista de Matemática abra el pase de lista de un salón que no le corresponde, "
        "y evita que un tutor sin carga academica registre notas de un área que no dicta."
    )
    pdf.p(
        "Dirección es la unica que ve el grupo Institución: mapa de la IE, personal, modelo, usuarios, bitácora y backlog. "
        "Docentes y estudiantes no tienen esas entradas. Sobre nosotros y Cuenta si aparecen para los tres roles."
    )

    pdf.add_page()
    pdf.h1("4. Rol de dirección")
    pdf.p(
        "La cuenta de dirección del entorno es el usuario director, a nombre de Edgar David Advincua Porras. "
        "En pantalla el rol se lee Director. Esa persona administra toda la primaria: 1.° a 6.°, secciones A, B y C."
    )
    pdf.h2("Menú Gestión")
    pdf.rows(
        ["Entrada", "Para que la usa dirección"],
        [
            ["Inicio", "Resumen de la IE y cinco casos urgentes"],
            ["Matrícula", "Padrón completo, alta y edicion de fichas"],
            ["Evaluación", "Notas de cualquier salón y área"],
            ["Asistencia", "Pase de lista de cualquier salón"],
            ["Alerta temprana", "Lista priorizada de los 144 alumnos"],
            ["Seguimientos", "Todas las notas de tutoría"],
            ["Agenda de atención", "Todas las citas"],
            ["Reportes", "CSV e impresión de toda la IE"],
        ],
        [48, 126],
    )
    pdf.h2("Menú Institución")
    pdf.rows(
        ["Entrada", "Para que la usa dirección"],
        [
            ["La institución", "Mapa de salónes, usuarios y cadena de la IE"],
            ["Personal docente", "Quien es tutor y que área dicta"],
            ["Modelo predictivo", "Metricas y reentrenamiento"],
            ["Usuarios institucionales", "Alta, activacion y desactivacion"],
            ["Bitacora", "Ultimas acciones, sin claves ni DNI"],
            ["Product Backlog", "Historias Scrum del desarrollo"],
        ],
        [55, 119],
    )
    pdf.h2("Menú Sobre nosotros y Cuenta")
    pdf.p(
        "Sobre nosotros abre la misión, la visión y los teléfonos, con la foto del colegio de fondo. "
        "Cuenta tiene Cambiar contraseña y Salir. Dirección no puede desactivar su propia cuenta desde la tabla de usuarios; "
        "el boton de estado solo aparece en las demas cuentas."
    )
    pdf.p(
        "El panel de inicio no es un informe largo. Son ocho tarjetas. Cada una abre un módulo y muestra un número: "
        "matriculados, promedio institucional, porcentaje de asistencia, casos de atención alta, citas desde hoy, "
        "cantidad de personal, tutores cubiertos y el acceso a Sobre nosotros. Debajo, una barra compara atención alta, medía y baja, "
        "y una tabla lista los cinco primeros de la priorización."
    )
    pdf.figure("01-inicio.png", "Figura 2. Panel de dirección. El menú izquierdo ya muestra Gestión, Institución, Sobre nosotros y Cuenta.")

    pdf.add_page()
    pdf.h1("5. Rol docente")
    pdf.p(
        "El docente entra con su propio usuario. El grupo del menú se llama Aula, no Institución. "
        "No ve usuarios, bitácora, modelo ni el mapa institucional. Si abre una de esas direcciónes a mano, el sistema responde que no tiene permiso."
    )
    pdf.h2("5.1 Docente de aula (1.° y 2.°)")
    pdf.p(
        "Ejemplo: María Cerron Poma, usuario maria.cerron, tutora de 1.° A. Dicta Comunicación, Matemática, Personal Social, "
        "Ciencia y Tecnología, Arte y Cultura, Educación Física, Educación Religiosa e Ingles, todos en su sección. "
        "También pasa lista."
    )
    pdf.p("Su menú Aula queda así:")
    pdf.bullets([
        "Inicio. El texto del panel dice que es docente de aula: dicta todas las áreas y registra la asistencia.",
        "Matrícula. Solo los alumnos de 1.° A, no los 144.",
        "Evaluación. Las ocho áreas de su salón.",
        "Asistencia. El pase de lista de su salón.",
        "Alerta temprana, Seguimientos, Agenda de atención y Reportes, limitados a su carga.",
    ])
    pdf.p(
        "Después vienen Sobre nosotros y Cuenta, igual que para el resto. "
        "No puede crear usuarios ni reentrenar el modelo."
    )
    pdf.h2("5.2 Docente de área (desde 3.°)")
    pdf.p(
        "Ejemplo: Ana De la Cruz Rojas, usuario ana.delacruz, área Comunicación. Dicta ese curso en los grados 3.°, 4.°, 5.° y 6.°, secciones A, B y C. "
        "Carlos Meza Huayta hace lo mismo con Matemática. Rosa Vallejos Chavez con Personal Social. "
        "Pedro Huayta Gamarra con Ciencia y Tecnología. Lucia Ramos Soto con Arte y Cultura y también con Educación Física. "
        "Silvia Poma Flores con Educación Religiosa. Miguel Limaymanta Castro con Ingles."
    )
    pdf.p(
        "Como tienen cursos asignados, el menú muestra Evaluación. Como no son tutores de salón, el menú no muestra Asistencia. "
        "En Matrícula, Alerta, Seguimientos, Agenda y Reportes solo aparecen los salónes donde dictan. "
        "No pueden cambiar la nota de un área que no es suya ni la asistencia de un tutor."
    )
    pdf.h2("5.3 Tutor de salón (desde 3.°)")
    pdf.p(
        "Ejemplo: Héctor Quispe Ñahui, usuario hector.quispe, tutor de 3.° A. El sistema lo describe como tutor de salón: encargado del grupo, sin dictar áreas. "
        "Hay un tutor por sección de 3.° a 6.°, doce en total."
    )
    pdf.p("Su menú Aula es:")
    pdf.bullets([
        "Inicio, Matrícula de su salón, Asistencia de su salón.",
        "Alerta temprana, Seguimientos, Agenda de atención y Reportes de su grupo.",
        "No aparece Evaluación, porque no tiene un curso asignado.",
        "Sobre nosotros, Cambiar contraseña y Salir.",
    ])
    pdf.p(
        "Esa separacion es la regla pedagogica del proyecto: hasta 2.° el aula es de una sola persona; "
        "desde 3.° el tutor cuida al grupo y los especialistas ensenan el área."
    )

    pdf.add_page()
    pdf.h1("6. Rol estudiante")
    pdf.p(
        "La mayoria de alumnos existe en matrícula y no tiene usuario. En el entorno de tesis solo tres pueden ingresar, "
        "para demostrar el portal sin abrir el padrón al alumnado."
    )
    pdf.rows(
        ["Usuario", "Situacion de ejemplo"],
        [
            ["alumno31", "3.° A, caso de atención alta"],
            ["alumno38", "3.° A, rendimiento esperado"],
            ["alumno51", "5.° A, caso de atención alta"],
        ],
        [50, 124],
    )
    pdf.h2("Menú Portal")
    pdf.rows(
        ["Entrada", "Que ve"],
        [
            ["Inicio", "Su resumen, no el de la IE"],
            ["Mi ficha", "Sus datos, su tutor y quien dicta cada curso"],
            ["Mi boleta", "Sus notas de los cuatro bimestres"],
            ["Mi asistencia", "Sus marcas, no las del salón"],
        ],
        [45, 129],
    )
    pdf.p(
        "Sobre nosotros también esta en su menú, con la misma misión, visión y teléfonos. "
        "Cuenta permite cambiar su clave y salir."
    )
    pdf.h2("Lo que el estudiante no ve")
    pdf.bullets([
        "No ve la lista de Alerta temprana ni la probabilidad de sus compañeros.",
        "No ve matrícula, evaluación del salón, pase de lista ajeno, citas, reportes ni personal.",
        "No ve usuarios, bitácora, modelo ni backlog.",
        "En su propia ficha puede ver su nivel de atención, porque es un dato suyo, no el ranking del salón.",
    ])
    pdf.p(
        "Si un estudiante escribe en el navegador la dirección de un módulo de dirección, el sistema no muestra la tabla: responde que el acceso no corresponde a su rol. "
        "Esa prueba forma parte de la bateria automatica del proyecto."
    )

    pdf.add_page()
    pdf.h1("7. Menú Inicio")
    pdf.p(
        "Inicio es la primera entrada de Gestión, de Aula y de Portal. La dirección es la raiz del sitio, después de ingresar. "
        "El título cambia con el rol: Panel de dirección, Panel docente o Mi portal."
    )
    pdf.p(
        "En dirección, las tarjetas son Matrícula (144 alumnos activos en 18 salónes), Evaluación (promedio institucional, en la captura 12.8), "
        "Asistencia (88.5 por ciento), Alerta temprana (18 casos altos), Agenda (4 citas desde hoy), Personal (25 docentes), "
        "Modelo (18 tutores) y Sobre nosotros. Esos números son del entorno sintético; cambian si se editan notas, asistencia o el modelo."
    )
    pdf.p(
        "La barra Atención en la IE reparte a los activos en alto, medio y bajo. En la captura: 18 altos, 72 medios y 54 bajos. "
        "Esa reparticion sale de la regla institucional, no de contar cuántos alumnos superan el umbral del algoritmo. "
        "La tabla Atención inmediata muestra el puesto, el nombre, el salón y el nivel de los cinco primeros. El nombre abre la ficha."
    )
    pdf.p(
        "En el docente, el subtítulo explica cual de las tres formas es: aula, tutor o área. Las tarjetas usan los conteos de su carga, no los de toda la IE. "
        "En el estudiante, el inicio apunta a su ficha y a su nivel, sin ranking."
    )

    pdf.add_page()
    pdf.h1("8. Menú Matrícula")
    pdf.p(
        "Matrícula es el padrón. No es la pantalla de riesgo. El subtítulo lo dice: identidad, domicilio, apoderado y tipo de matrícula; el riesgo se consulta en Alerta temprana."
    )
    pdf.p(
        "Dirección ve los 144 registros activos y puede filtrar por salón (18 opciones, de 1.° A a 6.° C), estado (activos, retirados o todos), sexo, lengua (castellano, quechua u otra), "
        "tipo (regular, traslado o reingreso) y necesidades educativas especiales. Hay un buscador por nombre, código, DNI o apoderado, y otro filtro dentro de la tabla."
    )
    pdf.p(
        "Las columnas son código, estudiante, DNI, sexo, edad, salón, tipo, apoderado y estado. El código sigue el patrón del año lectivo, por ejemplo EX2026. "
        "El nombre abre la ficha. Arriba se resumen cuántos hay en lista, cuántos son M y F, cuántos son traslado y cuántos tienen lengua quechua o NEE."
    )
    pdf.p(
        "Dos acciones son de dirección y de quien puede editar: Descargar padrón CSV y Nueva matrícula. "
        "La ficha nueva sigue el esquema de un registro escolar: nombres sin números, DNI de 8 digitos, celular de 9 digitos que empieza por 9. "
        "Si un dato no cumple, el formulario no se guarda y vuelve con el aviso."
    )
    pdf.p(
        "Dentro de la ficha estan los datos personales, el salón, el tutor, los docentes de cada área, las notas, la asistencia reciente, "
        "el nivel del modelo junto al nivel de atención, y el alta de un seguimiento. "
        "También se puede cambiar el estado del alumno a retirado, desertor o egresado. Ese cambio lo hace una persona; el modelo no lo dispara."
    )
    pdf.p(
        "El docente de aula y el tutor ven la matrícula de su salón. El docente de área ve los alumnos de los salónes donde dicta. "
        "Ninguno exporta el padrón de un salón que no le corresponde."
    )
    pdf.figure("03-matricula.png", "Figura 3. Matrícula vista por dirección, con los filtros y el padrón.")

    pdf.add_page()
    pdf.h1("9. Menú Evaluación")
    pdf.p(
        "Evaluación registra la nota vigesimal por área y por bimestre. No muestra asistencia ni riesgo. El subtítulo lo deja explícito: este módulo hace una sola cosa."
    )
    pdf.p(
        "Para ver la grilla hay que elegir salón y área. Las ocho áreas son Comunicación, Matemática, Personal Social, Ciencia y Tecnología, "
        "Arte y Cultura, Educación Física, Educación Religiosa e Ingles. Cada celda acepta un número de 0 a 20, con un decimal. "
        "Un valor fuera de ese rango no se guarda."
    )
    pdf.p(
        "Arriba, la evolución del salón compara el promedio de los cuatro bimestres y cuenta cuántos estudiantes suben o bajan al menos un punto entre el primero y el cuarto. "
        "La columna Cambio de la tabla hace esa resta alumno por alumno. Un boton Guardar notas escribe el bimestre editado."
    )
    pdf.p(
        "Quien puede editar: dirección, el docente de aula en las ocho áreas de su sección, y el docente de área solo en su curso y en sus salónes. "
        "El tutor de tercero a sexto no tiene esta entrada. El estudiante no edita notas; las lee en Mi boleta."
    )
    pdf.p(
        "Esas notas alimentan el modelo: promedio, áreas desaprobadas y tendencia entre bimestres. "
        "Por eso una correccion de nota, después de reentrenar o de recalcular, puede mover la probabilidad. "
        "La atención institucional del salón se vuelve a repartir con la regla de cupos, no con la nota suelta."
    )
    pdf.figure("07-evaluacion.png", "Figura 4. Comunicación de 1.° A. Cada fila es un estudiante y cada columna un bimestre.")

    pdf.add_page()
    pdf.h1("10. Menú Asistencia")
    pdf.p(
        "Asistencia es el pase de lista del tutor. Se elige salón y fecha. El año lectivo limita las fechas válidas: no se registra un día fuera de ese rango."
    )
    pdf.p(
        "Cada estudiante se marca como presente, falta, tardanza o justificada. Si la falta es justificada, el casíllero de motivo deja constancia. "
        "Guardar asistencia escribe el día. Los contadores de arriba resumen presentes, faltas, tardanzas y justificadas de esa fecha."
    )
    pdf.p(
        "Ademas del dia, la pantalla muestra las marcas acumuladas del salón y los patrones. Un patrón es una racha de tres faltas o una asistencia menor al 85 por ciento. "
        "Esos estudiantes aparecen en una correlación con tutoría: porcentaje, nivel de alerta, si tienen seguimiento abierto y si tienen cita. "
        "La marca cubierto o la brecha dicen si la tutoría ya los tomo o si todavia no hay seguimiento ni cita."
    )
    pdf.p(
        "El filtro Solo con patrón esconde al resto del salón para que el tutor trabaje la inasistencia. "
        "Dirección puede abrir cualquier salón. El docente de aula y el tutor solo el suyo. El docente de área no ve este menú."
    )
    pdf.p(
        "El estudiante consulta Mi asistencia y ve sus propias marcas, no el porcentaje de sus compañeros. "
        "Las faltas no justificadas y las tardanzas son variables del modelo, junto con el porcentaje de asistencia."
    )
    pdf.figure("10-asistencia.png", "Figura 5. Asistencia de 1.° A: marcas del salón, patrones y correlación con tutoría.")

    pdf.add_page()
    pdf.h1("11. Menú Alerta temprana")
    pdf.p(
        "Alerta temprana es la lista de priorización. Su subtítulo distingue las dos salidas: probabilidad del modelo y nivel de atención institucional por salón."
    )
    pdf.p(
        "Cada fila tiene un puesto, el estudiante, el salón, la probabilidad, una barra, el nivel del modelo y el nivel de atención. "
        "El enlace Ficha abre el detalle. Se exporta la lista filtrada a CSV."
    )
    pdf.p(
        "Los filtros son el nivel de atención (alto, medio o bajo), el salón, la discrepancia y el nombre o código. "
        "Discrepancia muestra solo los casos en los que el nivel del modelo y el nivel de atención no coinciden. "
        "Eso importa en la tesis: demuestra que las dos salidas no son la misma etiqueta."
    )
    pdf.p(
        "La regla de atención, por salón, reserva 1 cupo alto y 4 cupos medios. El resto del salón queda en nivel esperado, mostrado como bajo. "
        "Con 18 salónes, el entorno queda en 18 altos y 72 medios. El resto, 54 en la captura, es atención baja. "
        "Sirve para que ningún salón concentre toda la tutoría y ninguno se quede sin un caso prioritario."
    )
    pdf.p(
        "La probabilidad, en cambio, sale del clasíficador. En la captura varios casos figuran en 100 por ciento porque el entorno sintético separa con claridad los perfiles de deserción. "
        "Esas cifras no se citan como resultado del padrón real."
    )
    pdf.p(
        "Dirección ve los 144. El docente ve los de su carga. El estudiante no entra a esta lista."
    )
    pdf.figure("04-alerta.png", "Figura 6. Alerta temprana. Prioridad, probabilidad, nivel del modelo y nivel de atención.")

    pdf.add_page()
    pdf.h1("12. Menú Seguimientos")
    pdf.p(
        "Seguimientos es la memoria de la tutoría. No es la cita: la cita esta en la agenda. El seguimiento es la nota de lo que se observo y de como quedo el caso."
    )
    pdf.p(
        "El alta no se hace en esta lista. Se hace en la ficha del estudiante, para que la nota quede pegada a una persona y no a un formulario suelto. "
        "La lista sirve para buscar, filtrar y cerrar."
    )
    pdf.p(
        "Cada nota tiene un tipo: académico, asistencia, familiar o convivencia. El estado es abierto o cerrado. "
        "Los filtros son salón, tipo, estado y un texto libre sobre el estudiante, el código o el contenido. "
        "El subtítulo cuenta cuantas notas hay y cuantas siguen abiertas."
    )
    pdf.p(
        "Dirección ve los seguimientos de la IE. El docente y el tutor ven los de su carga. "
        "Cuando en Asistencia un estudiante con patrón no tiene seguimiento abierto ni cita, la correlación lo marca como brecha. "
        "El paso siguiente es abrir el seguimiento en la ficha o programar la cita."
    )
    pdf.p(
        "Cerrar un seguimiento no borra el texto. Cambia el estado para que la lista de abiertos no se llene de casos ya atendidos. "
        "La bitácora, visible solo para dirección, puede registrar el cambio de estado."
    )

    pdf.add_page()
    pdf.h1("13. Menú Agenda de atención")
    pdf.p(
        "La agenda programa la conversacion con la familia. Una cita tiene estudiante, fecha, canal y motivo. "
        "El canal es presencial, llamada o virtual. El motivo explica por qué se cita, por ejemplo inasistencias reiteradas."
    )
    pdf.p(
        "La tabla lista fecha, estudiante, salón, motivo, estado y el cierre. El estado pasa de programada a realizada, no asistio o cancelada. "
        "Si se marca realizada, se puede pedir que se abra un seguimiento en el mismo paso. El resultado se escribe en el casíllero de cierre."
    )
    pdf.p(
        "Los filtros son salón, estado y un buscador por estudiante, código o motivo. Hay un filtro adicional dentro de la tabla. "
        "Imprimir prepara la agenda para papel. En el panel de dirección, la tarjeta Agenda cuenta las citas programadas desde hoy; en la captura eran 4."
    )
    pdf.p(
        "Dirección programa citas de cualquier alumno activo. El docente y el tutor programan citas de su carga. "
        "El estudiante no ve la agenda: la cita es una herramienta del adulto responsable, no un muro publico."
    )
    pdf.p(
        "La fecha de la cita debe caer en el calendario lectivo. Un motivo vacio no se guarda. "
        "Asi la agenda no se llena de citas sin razon, que después nadie puede priorizar."
    )
    pdf.figure("08-agenda.png", "Figura 7. Agenda: formulario para programar y fila para cerrar la cita.")

    pdf.add_page()
    pdf.h1("14. Menú Reportes")
    pdf.p(
        "Reportes arma tablas para llevar a una reunion o a un anexo de tesis. Se descargan en CSV y se imprimen. "
        "A proposito no incluyen DNI ni teléfonos, para no sacar datos de contacto en un archivo que se comparte."
    )
    pdf.p("El tipo de reporte cambia las columnas:")
    pdf.bullets([
        "Priorizados: puesto, código, estudiante, salón, probabilidad, nivel del modelo y atención.",
        "Rendimiento: las notas de los bimestres.",
        "Patrones de asistencia: rachas y porcentaje.",
        "Padrón de matrícula: la lista de alumnos del alcance del usuario, sin los datos de contacto que el CSV de matrícula si puede llevar en el otro módulo.",
        "Correlación asistencia, alerta y tutoría: quien tiene patrón y si ya tiene seguimiento o cita.",
    ])
    pdf.p(
        "Se filtra por salón, por estado del alumno (activos, retirados o todos) y por nombre o código. "
        "Dirección elige todos los salónes visibles. El docente solo ve los salónes de su carga; el selector no le ofrece el resto."
    )
    pdf.p(
        "En la captura, el reporte de priorizados tiene 144 filas y empieza por los mismos nombres que la atención inmediata del inicio. "
        "Eso permite comprobar que el panel, la alerta y el reporte cuentan la misma priorización."
    )
    pdf.figure("11-reportes.png", "Figura 8. Reporte de priorizados, listo para CSV o impresión.")

    pdf.add_page()
    pdf.h1("15. Menú La institución")
    pdf.p(
        "La institución esta solo en el menú de dirección. Es el mapa, no el padrón. El título en pantalla es Mapa de la institución y ubica a Exellenti en El Tambo, Huancayo, en el año lectivo."
    )
    pdf.p(
        "Resume matriculados, salónes, docentes, áreas y usuarios activos. Muestra la matrícula por sección A, B y C, y los usuarios por rol. "
        "En el entorno hay un director, los docentes de aula, de área y tutores, y los estudiantes que tienen cuenta."
    )
    pdf.p(
        "Un recuadro explica la cadena de la IE, que es la misma regla del menú docente: "
        "dirección ve y gestiona toda la primaria; en 1.° y 2.° un docente de aula dicta todas las áreas y es el tutor; "
        "desde 3.° el tutor solo es encargado y cada área la dicta un especialista que puede cubrir varios grados; "
        "el alumno ve a su tutor, a quien le ensena cada curso, sus notas y su nivel de atención."
    )
    pdf.p(
        "Esta pantalla no edita. Si un salón figura sin tutor, el lugar para corregirlo es Personal docente y la asignacion que deja el arranque del sistema. "
        "En el entorno de tesis los 18 salónes tienen tutor."
    )

    pdf.add_page()
    pdf.h1("16. Menú Personal docente")
    pdf.p(
        "Personal docente, también solo de dirección, responde quien ensena que. El subtítulo repite la regla de 1.° y 2.° frente a la de 3.° en adelante."
    )
    pdf.p(
        "Arriba hay cuatro números: docentes, cargas (salón por curso), tutores de aula y salónes cubiertos. "
        "En la captura: 25 docentes, 144 cargas, 18 tutores y 18 salónes cubiertos. "
        "144 cargas no son 144 docentes: son las parejas salón-área. Seis docentes de aula cubren 6 salónes por 8 áreas. "
        "Los especialistas cubren el mismo curso en los doce salónes de 3.° a 6.°."
    )
    pdf.p(
        "Cada tarjeta trae el nombre, la especialidad, el usuario y, si corresponde, el salón del que es tutor. "
        "La tabla interna lista salón y área que dicta. En María Cerron Poma se ven las ocho áreas de 1.° A. "
        "En un tutor de 4.° o 5.° la tarjeta dice que solo hace tutoría y no dicta áreas en ese salón."
    )
    pdf.p(
        "Se busca por nombre, usuario o especialidad, y se puede dejar solo a los tutores. "
        "Esta pantalla explica el menú de cada docente: si la tarjeta tiene áreas, ese usuario vera Evaluación; si es tutor, vera Asistencia."
    )
    pdf.figure("12-docentes.png", "Figura 9. Personal. La primera tarjeta es la docente de aula de 1.° A, con las ocho áreas.")

    pdf.add_page()
    pdf.h1("17. Menú Usuarios institucionales")
    pdf.p(
        "Usuarios institucionales es el alta de cuentas. Solo dirección entra. El subtítulo advierte que la clave se entrega por un canal seguro y que no se vuelve a mostrar."
    )
    pdf.h2("Tabla Cuentas")
    pdf.p(
        "Las columnas son usuario, nombre, rol, estado y accion. El rol se lee en espanol: Director, Docente o Estudiante. "
        "La primera fila del entorno es director, Edgar David Advincua Porras, rol Director, estado activo. "
        "Esa fila no tiene boton Desactivar, porque es la sesión que esta mirando la tabla."
    )
    pdf.p(
        "El resto de filas tiene Desactivar o Activar. Desactivar no borra la matrícula ni las notas: impide el ingreso. "
        "Activar lo devuelve. Hay filtros por rol, por estado y un buscador de usuario o nombre, para no recorrer las decenas de tutores a mano."
    )
    pdf.h2("Nueva cuenta")
    pdf.p(
        "El formulario pide usuario, nombre completo, rol y clave temporal. El usuario usa minusculas, números, punto o guion, con minimo de tres caracteres. "
        "El nombre solo acepta letras, espacios y tildes. El rol que se puede crear aquí es docente o estudiante; no se crea otra dirección desde este formulario. "
        "La clave temporal exige minimo ocho caracteres, con letras y números. Al guardar, dirección debe copiar esa clave y entregarla. La pantalla no la conserva en claro."
    )
    pdf.p(
        "Un estudiante nuevo en este formulario obtiene ingreso, pero la ficha academica sigue viviendo en Matrícula. "
        "Conviene crear la ficha primero y después, si ese alumno debe ver su boleta, crear el usuario con el mismo vinculo que usa el entorno de tesis."
    )
    pdf.figure("06-usuarios.png", "Figura 10. Cuentas, con el director en la primera fila, y el formulario de alta a la derecha.")

    pdf.add_page()
    pdf.h1("18. Menú Bitacora")
    pdf.p(
        "La bitácora esta solo en el menú de dirección. Muestra las ultimas acciones del sistema, hasta unas 150, para responder quien cambio un estado o quien reentreno el modelo."
    )
    pdf.p(
        "No es un visor de datos personales. El subtítulo dice que no incluye claves ni DNI. "
        "Se puede filtrar por tipo de accion y por un texto. Sirve de control interno del entorno de tesis, no de reporte para familias."
    )
    pdf.p(
        "Si una cuenta se desactiva, si una matrícula cambia de estado o si se lanza el reentrenamiento, la bitácora es el lugar donde dirección lo revisa después. "
        "Docentes y estudiantes no tienen esta entrada y no pueden abrirla por la dirección del navegador."
    )

    pdf.add_page()
    pdf.h1("19. Menú Product Backlog")
    pdf.p(
        "Product Backlog esta en el grupo Institución, solo para dirección. No es una herramienta del colegio para el día a dia. "
        "Es el tablero Scrum del desarrollo de la tesis: historias de usuario con rol, necesidad y criterio de aceptacion."
    )
    pdf.p(
        "Una historia tipica dice, por ejemplo, que dirección quiere citar por salón, fecha y canal para ordenar la tutoría de los priorizados, "
        "o que quiere ver quien tiene un patrón de faltas y todavia no tiene seguimiento ni cita. "
        "Esas historias explican por qué existen la agenda y la correlación de asistencia. No se marcan como táreas del tutor frente a un padre de familia."
    )
    pdf.p(
        "El subtítulo cuenta cuántos items hay. Scrum, en este proyecto, organizo la construccion del software. "
        "La predicción la hace el modelo; la priorización de aula la hace la regla de cupos; el backlog no calcula riesgo."
    )

    pdf.add_page()
    pdf.h1("20. Menú Sobre nosotros")
    pdf.p(
        "Sobre nosotros es un grupo propio del menú, no un parrafo escondido en el ingreso. "
        "Aparece para dirección, para los tres tipos de docente y para el estudiante. La entrada se llama igual que el grupo: Sobre nosotros."
    )
    pdf.p(
        "La foto de los estudiantes, con el rotulo Colegio Excellenti, es el fondo de la página. "
        "Encima, en tarjetas, se leen la misión, la visión y la tabla de sedes. En el celular la foto queda detras y las tarjetas se apilan."
    )
    pdf.h2("Misión")
    pdf.p(
        "Somos una corporacion educativa cristiana comprometida con impulsar a cada estudiante a descubrir y desarrollar su maximo potencial académico, artistico y personal. "
        "A traves de una ensenanza innovadora basada en experiencias reales, herramientas tecnologicas y el dominio de idiomas desde temprana edad, "
        "formamos mentes criticas, creativas y empaticas que viven con ética, solidez espiritual y amor al prójimo."
    )
    pdf.h2("Visión")
    pdf.p(
        "Consolidarnos como una institución educativa líder y referente en la región, reconocida por brindar una educación de vanguardía que prepara a las nuevas generaciones para destacar en un mundo globalizado. "
        "Aspiramos a transformar la sociedad formando líderes integros con un solido proyecto de vida, capaces de afrontar los retos del futuro con excelencia, innovación y responsabilidad social."
    )
    pdf.h2("Sedes")
    pdf.p("Chupaca, 981 819 115. Huancayo, 981 819 112. Cajas, 981 819 113. Los mismos números aparecen en la pantalla de ingreso, antes de la sesión.")
    pdf.figure("02-sobre-nosotros.png", "Figura 11. Sobre nosotros, con la foto de fondo y las tres tarjetas.")
    pdf.p(
        "En el panel de dirección también hay una tarjeta Sobre nosotros, para llegar a esta página sin usar el menú lateral. "
        "El ingreso, en cambio, muestra otro texto, el de bienvenida a las familias, y no reemplaza esta página."
    )

    pdf.add_page()
    pdf.h1("21. Menú Cambiar contraseña y Salir")
    pdf.p(
        "Estos dos enlaces cierran el menú de los tres roles, dentro del grupo Cuenta. No dependen de si la persona es tutor o especialista."
    )
    pdf.p(
        "Cambiar contraseña muestra el nombre y el usuario de quien esta en sesión. Pide la clave actual y la nueva. "
        "La nueva debe tener al menos ocho caracteres, con letras y números. Si la actual no coincide, no hay cambio. "
        "La clave nueva pasa a ser la del ingreso; la anterior deja de servir."
    )
    pdf.p(
        "Salir cierra la sesión y vuelve a la pantalla de ingreso. Conviene usarlo en una computadora compartida del laboratorio, "
        "porque la cookie, si se deja abierta, mantiene el rol anterior."
    )
    pdf.p(
        "Dirección puede desactivar la cuenta de otra persona, pero no sustituye este cambio de clave. "
        "Una cuenta activa con una clave debil se corrige aquí, por el dueno de la sesión, o entregando una clave temporal nueva si el procedimiento del entorno lo permite."
    )

    pdf.add_page()
    pdf.h1("22. El modelo predictivo")
    pdf.p(
        "El modelo esta en el menú Institución y solo lo abre dirección. La pantalla se llama Evaluación del modelo. "
        "Compara algoritmos con validacion cruzada estratificada y se queda con el que mejor combina recall y F1."
    )
    pdf.h2("Dos salidas que no son la misma")
    pdf.p(
        "La probabilidad y el nivel del modelo salen del clasíficador. Los umbrales sobre la probabilidad son 0.62 y 0.35. "
        "Por encima de 0.62 el nivel del modelo es alto; entre 0.35 y 0.62 es medio; por debajo es bajo. "
        "Esa etiqueta dice que tan parecido es el perfil del alumno a los casos historicos marcados como deserción."
    )
    pdf.p(
        "El nivel de atención es una regla del colegio, aplicada dentro de cada salón: 1 cupo alto, 4 medios y el resto en nivel esperado. "
        "Ordena la tutoría. No es la clase que devolvio el algoritmo. En la ficha se muestran los dos, y en Alerta temprana el filtro de discrepancia los compara."
    )
    pdf.h2("Como se entrena")
    pdf.p(
        "Hay 80 registros historicos sintéticos, 28 de ellos desertores. La validacion es de cinco pliegues estratificados. "
        "Las métricas salen de predicciónes fuera de cada pliegue, para no medir al modelo con los mismos casos con los que aprendio ese pliegue. "
        "El balanceo replica la clase minoritaria solo dentro del pliegue de entrenamiento. No es SMOTE. No se debe describir como tal en la tesis."
    )
    pdf.p(
        "Los algoritmos comparados son regresion logistica, Naive Bayes, SVM, Random Forest y arboles impulsados. "
        "Las métricas son accuracy, precision, recall con su desviacion, F1, ROC-AUC, PR-AUC y la matriz de confusión."
    )
    pdf.p(
        "En la captura de este entorno el elegido es Naive Bayes: recall 0.786 con desviacion 0.141, F1 0.710 con desviacion 0.077, "
        "accuracy 0.775, precision 0.647, ROC-AUC 0.793 y PR-AUC 0.636. "
        "La matriz fuera de pliegue cuenta 40 verdaderos negativos, 12 falsos positivos, 6 falsos negativos y 22 verdaderos positivos, sobre 80 etiquetados. "
        "Estas cifras no son el desempeno sobre datos reales de la IE."
    )
    pdf.figure("05-modelo.png", "Figura 12. Modelo elegido, matriz de confusión y métricas del entorno de tesis.")
    pdf.p(
        "El boton Reentrenar y priorizar vuelve a comparar, elige y recalcula la lista. Lo usa dirección, con una confirmacion, porque mueve el orden de atención. "
        "Las variables son rendimiento, áreas desaprobadas, tendencia, asistencia, faltas no justificadas y tardanzas. "
        "Las fuentes citadas en la propia pantalla son Chung y Lee (2019) y Lee y Chung (2019)."
    )

    pdf.add_page()
    pdf.h1("23. Como esta construido")
    pdf.p(
        "El proyecto separa la pantalla, la aplicacion y el modelo. frontend guarda las plantillas, el estilo y los scripts. "
        "backend es la aplicacion: sesiónes, permisos, validaciones y la base. ml entrena y predice. data guarda la base local."
    )
    pdf.p(
        "En la computadora la base es SQLite. En Railway y en Vercel la base es PostgreSQL. "
        "Vercel publica el sitio y lee esa base. Railway arranca el servicio y entrena el modelo. "
        "Por eso un reentrenamiento hecho solo en la laptop no cambia el sitio publico hasta que los datos y el modelo viven en el servicio."
    )
    pdf.p(
        "Las validaciones de negocio rechazan un DNI que no tenga 8 digitos, un celular que no tenga 9 digitos y no empiece por 9, "
        "un nombre con números y una contraseña sin letras y números. Esas reglas estan en el servidor, no solo en el navegador."
    )
    pdf.h2("Orden de uso")
    pdf.bullets([
        "Ingresar con el rol que corresponde. Dirección usa director.",
        "Leer el panel y abrir los cinco casos de atención inmediata.",
        "En Alerta temprana, mirar probabilidad y atención. Si no coinciden, la discrepancia lo muestra.",
        "Abrir la ficha: notas, asistencia, tutor y docentes del curso.",
        "Registrar el seguimiento en la ficha y programar la cita en la agenda.",
        "Cerrar la cita cuando se realice. Si hacia falta, el cierre abre el seguimiento.",
        "Exportar el reporte de priorizados o el de correlación para la reunion.",
        "Dirección revisa usuarios y bitácora, y reentrena solo cuando las notas o la asistencia cambiaron de verdad.",
    ])
    pdf.h2("Cuentas de prueba")
    pdf.p("Sirven en la computadora, en Vercel y en Railway. Son del entorno de tesis y estan documentadas en el repositorio.")
    pdf.rows(
        ["Usuario", "Clave", "Rol en el colegio"],
        [
            ["director", "Dir#Ex26", "Dirección de la IE"],
            ["maria.cerron", "Doc1#Ex26", "Aula y tutoría de 1.° A"],
            ["ana.delacruz", "Doc3#Ex26", "Comunicación, 3.° a 6.°"],
            ["hector.quispe", "Doc8#Ex26", "Tutor de 3.° A, sin áreas"],
            ["alumno31", "Est31#Ex26", "Estudiante, atención alta"],
        ],
        [40, 40, 94],
    )
    pdf.p(
        "El resto de docentes de aula, especialistas, tutores de sección y los otros dos estudiantes estan en el README del proyecto. "
        "Después de este informe, el archivo queda en la carpeta docs del mismo repositorio local."
    )
    pdf.p(
        "Código: https://github.com/piero12876/TallerdeInvestigacion1, rama main."
    )

    pdf.output(str(OUT))
    print(f"{OUT}")
    print(f"páginas={pdf.page}")


if __name__ == "__main__":
    build()
