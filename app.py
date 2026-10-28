import json
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN DE LA BASE DE DATOS (SQLite)
# ==========================================
DB_NAME = "cuestionario.db"


def init_db():
  """Inicializa las tablas en la base de datos si no existen."""
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  # Tabla para almacenar las preguntas
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS preguntas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            tipo TEXT NOT NULL,
            opciones TEXT
        )
    """)

  # Tabla para almacenar las respuestas
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS respuestas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pregunta_id INTEGER,
            respuesta TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pregunta_id) REFERENCES preguntas (id)
        )
    """)

  conn.commit()

  # Cargar preguntas de la encuesta si la base de datos está vacía
  cursor.execute("SELECT COUNT(*) FROM preguntas")
  if cursor.fetchone()[0] == 0:
    preguntas_demo = [
        (
            "1. ¿Qué tanto te gusta la carrera que estás estudiando?",
            "Opciones",
            json.dumps(
                ["Me gusta mucho", "Me gusta", "Me gusta poco", "No me gusta"]
            ),
        ),
        (
            "2. ¿Por qué elegiste esta carrera?",
            "Opciones",
            json.dumps([
                "Por gusto personal",
                "Por oportunidades laborales",
                "Por influencia familiar",
                "Porque no tenía otra opción clara",
            ]),
        ),
        (
            "3. ¿Qué tan motivado te sientes al asistir a clases?",
            "Opciones",
            json.dumps(
                ["Muy motivado", "Algo motivado", "Poco motivado", "Nada motivado"]
            ),
        ),
        (
            "4. ¿Qué tanto disfrutas las materias de tu carrera?",
            "Opciones",
            json.dumps([
                "Disfruto casi todas",
                "Disfruto varias",
                "Disfruto pocas",
                "No disfruto ninguna",
            ]),
        ),
        (
            "5. ¿La carrera ha cumplido con tus expectativas?",
            "Opciones",
            json.dumps([
                "Sí, completamente",
                "En gran parte",
                "Muy poco",
                "No ha cumplido mis expectativas",
            ]),
        ),
        (
            "6. ¿Qué tan útiles consideras los conocimientos que estás adquiriendo?",
            "Opciones",
            json.dumps(["Muy útiles", "Algo útiles", "Poco útiles", "Nada útiles"]),
        ),
        (
            "7. ¿Cómo te sientes con la dificultad de tu carrera?",
            "Opciones",
            json.dumps([
                "Me siento cómodo con ella",
                "Es difícil, pero puedo manejarla",
                "Me cuesta bastante",
                "Me resulta demasiado difícil",
            ]),
        ),
        (
            "8. ¿Qué tan seguro estás de terminar la carrera que elegiste?",
            "Opciones",
            json.dumps([
                "Completamente seguro",
                "Bastante seguro",
                "Poco seguro",
                "No estoy seguro",
            ]),
        ),
        (
            "9. ¿Qué tan relacionada está tu carrera con lo que quieres hacer en el futuro?",
            "Opciones",
            json.dumps([
                "Está muy relacionada",
                "Está parcialmente relacionada",
                "Tiene poca relación",
                "No tiene relación",
            ]),
        ),
        (
            "10. Si pudieras volver a elegir, ¿qué harías?",
            "Opciones",
            json.dumps([
                "Elegiría la misma carrera",
                "Elegiría otra carrera de la misma área",
                "Elegiría una carrera diferente",
                "Todavía no lo sé",
            ]),
        ),
    ]
    cursor.executemany(
        "INSERT INTO preguntas (titulo, tipo, opciones) VALUES (?, ?, ?)",
        preguntas_demo,
    )
    conn.commit()

  conn.close()


def obtener_preguntas():
  """Recupera la lista de preguntas registradas."""
  conn = sqlite3.connect(DB_NAME)
  df = pd.read_sql_query("SELECT * FROM preguntas", conn)
  conn.close()
  return df


def guardar_respuestas(respuestas_dict):
  """Inserta las respuestas enviadas por el usuario en la base de datos."""
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  for preg_id, resp in respuestas_dict.items():
    if resp is not None and str(resp).strip() != "":
      cursor.execute(
          "INSERT INTO respuestas (pregunta_id, respuesta) VALUES (?, ?)",
          (preg_id, str(resp)),
      )
  conn.commit()
  conn.close()


def agregar_pregunta(titulo, tipo, opciones_lista):
  """Permite al administrador guardar una nueva pregunta."""
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO preguntas (titulo, tipo, opciones) VALUES (?, ?, ?)",
      (titulo, tipo, json.dumps(opciones_lista)),
  )
  conn.commit()
  conn.close()


def obtener_respuestas_df():
  """Recupera un DataFrame con todas las respuestas recopiladas en la base de datos."""
  conn = sqlite3.connect(DB_NAME)
  query = """
        SELECT r.id AS respuesta_id, p.titulo AS pregunta, p.tipo, r.respuesta, r.fecha
        FROM respuestas r
        JOIN preguntas p ON r.pregunta_id = p.id
    """
  df = pd.read_sql_query(query, conn)
  conn.close()
  return df


# Inicializar la Base de Datos al arrancar la aplicación
init_db()

# ==========================================
# 2. INTERFAZ Y NAVEGACIÓN (STREAMLIT)
# ==========================================
st.set_page_config(
    page_title="Cuestionario: ¿Qué tanto te gusta tu carrera?",
    page_icon="🎓",
    layout="wide",
)

st.sidebar.title("📌 Menú Principal")
opcion = st.sidebar.radio(
    "Navegación:",
    [
        "📝 Responder Cuestionario",
        "📊 Dashboard de Estadísticas",
        "🗄️ Ver Base de Datos",
        "⚙️ Crear Pregunta",
    ],
)

# ------------------------------------------
# VISTA 1: RESPONDER CUESTIONARIO
# ------------------------------------------
if opcion == "📝 Responder Cuestionario":
  st.title("🎓 Encuesta: ¿Qué tanto te gusta lo que estás estudiando?")
  st.write(
      "Responde sinceramente a cada una de las preguntas sobre tu experiencia"
      " universitaria."
  )

  df_preguntas = obtener_preguntas()

  if df_preguntas.empty:
    st.info("No hay preguntas registradas en el sistema.")
  else:
    with st.form("form_cuestionario"):
      respuestas_usuario = {}

      for _, row in df_preguntas.iterrows():
        st.subheader(row["titulo"])
        p_id = row["id"]
        tipo = row["tipo"]
        opciones = json.loads(row["opciones"]) if row["opciones"] else []

        if tipo == "Opciones":
          respuestas_usuario[p_id] = st.radio(
              "Selecciona una opción:", opciones, key=f"p_{p_id}"
          )
        elif tipo == "Escala (1-5)":
          respuestas_usuario[p_id] = st.select_slider(
              "Selecciona la puntuación:",
              options=[1, 2, 3, 4, 5],
              value=3,
              key=f"p_{p_id}",
          )
        elif tipo == "Texto":
          respuestas_usuario[p_id] = st.text_area(
              "Escribe tu respuesta:", key=f"p_{p_id}"
          )

        st.markdown("---")

      enviado = st.form_submit_button("📤 Enviar Respuestas")

      if enviado:
        guardar_respuestas(respuestas_usuario)
        st.success(
            "¡Tus respuestas han sido guardadas en la base de datos"
            " exitosamente!"
        )

# ------------------------------------------
# VISTA 2: DASHBOARD DE ESTADÍSTICAS
# ------------------------------------------
elif opcion == "📊 Dashboard de Estadísticas":
  st.title("📊 Estadísticas del Cuestionario")

  df_respuestas = obtener_respuestas_df()

  if df_respuestas.empty:
    st.warning("Aún no hay respuestas registradas en la base de datos.")
  else:
    col_met, col_btn = st.columns([1, 1])

    with col_met:
      st.metric("Total de Registros Guardados", len(df_respuestas))

    with col_btn:
      csv_data = df_respuestas.to_csv(index=False, encoding="utf-8-sig")
      st.download_button(
          label="📥 Descargar Base de Datos (CSV / Excel)",
          data=csv_data,
          file_name="respuestas_cuestionario.csv",
          mime="text/csv",
      )

    st.markdown("---")

    df_preguntas = obtener_preguntas()

    for _, preg in df_preguntas.iterrows():
      p_id = preg["id"]
      titulo = preg["titulo"]
      tipo = preg["tipo"]

      resp_p = df_respuestas[df_respuestas["pregunta"] == titulo]

      st.markdown(f"### {titulo}")

      if resp_p.empty:
        st.caption("Aún no hay respuestas registradas para esta pregunta.")
        st.markdown("---")
        continue

      if tipo == "Opciones":
        col1, col2 = st.columns([1, 1])

        conteo = resp_p["respuesta"].value_counts().reset_index()
        conteo.columns = ["Opción", "Cantidad"]

        with col1:
          fig_bar = px.bar(
              conteo,
              x="Opción",
              y="Cantidad",
              color="Opción",
              title="Distribución de Respuestas (Barras)",
          )
          st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
          fig_pie = px.pie(
              conteo,
              names="Opción",
              values="Cantidad",
              title="Porcentaje por Opción (Pastel)",
          )
          st.plotly_chart(fig_pie, use_container_width=True)

      elif tipo == "Escala (1-5)":
        resp_p["respuesta_num"] = pd.to_numeric(
            resp_p["respuesta"], errors="coerce"
        )
        promedio = resp_p["respuesta_num"].mean()

        col1, col2 = st.columns([1, 2])

        with col1:
          st.metric("Puntuación Promedio", f"{promedio:.2f} / 5.0")

        with col2:
          conteo = (
              resp_p["respuesta_num"]
              .value_counts()
              .sort_index()
              .reset_index()
          )
          conteo.columns = ["Escala", "Cantidad"]
          fig_escala = px.bar(
              conteo,
              x="Escala",
              y="Cantidad",
              labels={"Escala": "Puntaje (1-5)"},
              title="Distribución de Puntuaciones",
          )
          st.plotly_chart(fig_escala, use_container_width=True)

      elif tipo == "Texto":
        st.write("**Respuestas de texto recibidas:**")
        st.dataframe(
            resp_p[["respuesta", "fecha"]].rename(
                columns={"respuesta": "Respuesta", "fecha": "Fecha/Hora"}
            ),
            use_container_width=True,
        )

      st.markdown("---")

# ------------------------------------------
# VISTA 3: VER BASE DE DATOS COMPLETA
# ------------------------------------------
elif opcion == "🗄️ Ver Base de Datos":
  st.title("🗄️ Registros de la Base de Datos")

  df_respuestas = obtener_respuestas_df()

  if df_respuestas.empty:
    st.info("La base de datos está vacía por el momento.")
  else:
    st.write(
        "A continuación se muestran todas las respuestas registradas en la"
        " tabla `respuestas` de SQLite:"
    )
    st.dataframe(df_respuestas, use_container_width=True)

    csv_data = df_respuestas.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 Descargar Reporte Completo (CSV / Excel)",
        data=csv_data,
        file_name="base_de_datos_respuestas.csv",
        mime="text/csv",
    )

# ------------------------------------------
# VISTA 4: CREAR NUEVAS PREGUNTAS
# ------------------------------------------
elif opcion == "⚙️ Crear Pregunta":
  st.title("⚙️ Panel de Administración de Preguntas")

  with st.form("form_nueva_pregunta"):
    nuevo_titulo = st.text_input("Enunciado o Título de la pregunta:")
    tipo_pregunta = st.selectbox(
        "Tipo de Pregunta:", ["Opciones", "Escala (1-5)", "Texto"]
    )

    opciones_input = ""
    if tipo_pregunta == "Opciones":
      opciones_input = st.text_area(
          "Opciones (separadas por comas):",
          help="Ejemplo: Opción A, Opción B, Opción C, Opción D",
      )

    btn_guardar = st.form_submit_button("➕ Guardar Pregunta")

    if btn_guardar:
      if not nuevo_titulo.strip():
        st.error("Debes ingresar un título para la pregunta.")
      else:
        lista_opciones = []
        if tipo_pregunta == "Opciones" and opciones_input:
          lista_opciones = [
              item.strip() for item in opciones_input.split(",") if item.strip()
          ]

        agregar_pregunta(nuevo_titulo, tipo_pregunta, lista_opciones)
        st.success(
            f"Pregunta **'{nuevo_titulo}'** agregada correctamente al sistema."
        )
    
