import json
import cv2
import numpy as np
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Sistema SCADA - Resaltador de Zonas",
    page_icon="🚊",
    layout="wide",
)

st.title("🚊 Sistema SCADA - Monitoreo y Resaltado de Zonas")
st.markdown(
    "Cargue un esquema SCADA, defina zonas o resalte tramos en tiempo real con"
    " delimitadores neón."
)


# --- FUNCIONES DE DIBUJO ---
def dibujar_zona(img_base, zona):
  overlay = img_base.copy()

  # 1. Dibujar líneas del tramo
  for lin in zona.get("lineas", []):
    cv2.line(
        overlay,
        (lin["x_inicio"], lin["y_inicio"]),
        (lin["x_fin"], lin["y_fin"]),
        (255, 255, 0),
        6,
    )

  # 2. Corchete Izquierdo [
  c_i = zona.get("corchete_izq", {})
  if c_i:
    cv2.line(
        overlay, (c_i["x"], c_i["y1"]), (c_i["x"], c_i["y2"]), (0, 255, 255), 5
    )
    cv2.line(
        overlay,
        (c_i["x"], c_i["y1"]),
        (c_i["x"] + 25, c_i["y1"]),
        (0, 255, 255),
        5,
    )
    cv2.line(
        overlay,
        (c_i["x"], c_i["y2"]),
        (c_i["x"] + 25, c_i["y2"]),
        (0, 255, 255),
        5,
    )

  # 3. Corchete Derecho ]
  c_d = zona.get("corchete_der", {})
  if c_d:
    cv2.line(
        overlay, (c_d["x"], c_d["y1"]), (c_d["x"], c_d["y2"]), (0, 255, 255), 5
    )
    cv2.line(
        overlay,
        (c_d["x"], c_d["y1"]),
        (c_d["x"] - 25, c_d["y1"]),
        (0, 255, 255),
        5,
    )
    cv2.line(
        overlay,
        (c_d["x"], c_d["y2"]),
        (c_d["x"] - 25, c_d["y2"]),
        (0, 255, 255),
        5,
    )

  # Resplandor/Mezcla
  return cv2.addWeighted(overlay, 0.85, img_base, 0.15, 0)


# --- ESTADO DE SESIÓN (SESSION STATE) ---
if "zonas" not in st.session_state:
  st.session_state.zonas = []

# --- PANEL LATERAL (SIDEBAR) ---
st.sidebar.header("📁 Carga de Archivos")

# Cargar Imagen Base
uploaded_image = st.sidebar.file_uploader(
    "1. Subir Imagen SCADA", type=["jpg", "png", "jpeg"]
)

# Cargar JSON de Zonas
uploaded_json = st.sidebar.file_uploader(
    "2. Cargar Archivo Zonas (.json)", type=["json"]
)
if uploaded_json is not None:
  try:
    st.session_state.zonas = json.load(uploaded_json)
    st.sidebar.success(
        f"Se cargaron {len(st.session_state.zonas)} zonas con éxito."
    )
  except Exception as e:
    st.sidebar.error("Error al leer el archivo JSON.")

st.sidebar.divider()

# --- MODO DE TRABAJO ---
modo = st.sidebar.radio("Modo de Trabajo:", ["Visor / Monitoreo", "Mapeador / Crear Zonas"])

if uploaded_image is not None:
  # Convertir archivo cargado a formato OpenCV (BGR)
  file_bytes = np.asarray(bytearray(uploaded_image.read()), dtype=uint8)
  img_original = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

  # ----------------------------------------------------
  # MODO 1: VISOR / MONITOREO
  # ----------------------------------------------------
  if modo == "Visor / Monitoreo":
    col_ctrl, col_view = st.columns([1, 3])

    with col_ctrl:
      st.subheader("Buscador de Zonas")
      ids_zonas = [z["id"] for z in st.session_state.zonas]

      zona_seleccionada_id = st.selectbox(
          "Seleccione una zona a resaltar:",
          options=["Ninguna"] + ids_zonas,
      )

      # Descargar JSON actual
      if st.session_state.zonas:
        json_data = json.dumps(st.session_state.zonas, indent=2)
        st.download_button(
            label="💾 Exportar zonas.json",
            data=json_data,
            file_name="zonas.json",
            mime="application/json",
        )

    with col_view:
      if zona_seleccionada_id != "Ninguna":
        zona_obj = next(
            z for z in st.session_state.zonas if z["id"] == zona_seleccionada_id
        )
        img_resaltada = dibujar_zona(img_original, zona_obj)
        # Convertir BGR a RGB para mostrar en Streamlit
        st.image(
            cv2.cvtColor(img_resaltada, cv2.COLOR_BGR2RGB),
            caption=f"Visualizando Zona {zona_seleccionada_id}",
            use_container_width=True,
        )
      else:
        st.image(
            cv2.cvtColor(img_original, cv2.COLOR_BGR2RGB),
            caption="Diagrama SCADA Base",
            use_container_width=True,
        )

  # ----------------------------------------------------
  # MODO 2: MAPEADOR / CREAR ZONAS
  # ----------------------------------------------------
  else:
    st.subheader("🛠️ Creador de Zonas (Ingreso Manual de Puntos)")
    st.info(
        "Ingrese el ID de la zona y los pares de coordenadas para las líneas"
        " superiores/inferiores."
    )

    col_form, col_preview = st.columns([1, 2])

    with col_form:
      nuevo_id = st.text_input("ID de la Zona (ej: 201):")

      st.markdown("**Tramo 1 (Línea Superior)**")
      x1_1 = st.number_input("X Inicio (Línea 1)", value=100)
      y1_1 = st.number_input("Y Inicio (Línea 1)", value=300)
      x1_2 = st.number_input("X Fin (Línea 1)", value=500)
      y1_2 = st.number_input("Y Fin (Línea 1)", value=300)

      st.markdown("**Tramo 2 (Línea Inferior - Opcional)**")
      usar_linea_2 = st.checkbox("¿Agregar segunda línea paralela/escalón?")

      x2_1, y2_1, x2_2, y2_2 = 0, 0, 0, 0
      if usar_linea_2:
        x2_1 = st.number_input("X Inicio (Línea 2)", value=100)
        y2_1 = st.number_input("Y Inicio (Línea 2)", value=450)
        x2_2 = st.number_input("X Fin (Línea 2)", value=500)
        y2_2 = st.number_input("Y Fin (Línea 2)", value=450)

      if st.button("➕ Guardar Zona"):
        if nuevo_id:
          lineas = [{"x_inicio": x1_1, "y_inicio": y1_1, "x_fin": x1_2, "y_fin": y1_2}]
          xs = [x1_1, x1_2]
          ys = [y1_1, y1_2]

          if usar_linea_2:
            lineas.append(
                {"x_inicio": x2_1, "y_inicio": y2_1, "x_fin": x2_2, "y_fin": y2_2}
            )
            xs.extend([x2_1, x2_2])
            ys.extend([y2_1, y2_2])

          x_min, x_max = min(xs), max(xs)
          y_min, y_max = min(ys) - 20, max(ys) + 20

          nueva_zona = {
              "id": nuevo_id,
              "lineas": lineas,
              "corchete_izq": {"x": x_min, "y1": y_min, "y2": y_max},
              "corchete_der": {"x": x_max, "y1": y_min, "y2": y_max},
          }

          st.session_state.zonas.append(nueva_zona)
          st.success(f"¡Zona {nuevo_id} agregada exitosamente!")
        else:
          st.error("Por favor ingrese un ID válido.")

    with col_preview:
      # Mostrar la imagen con las zonas acumuladas
      img_temp = img_original.copy()
      for z in st.session_state.zonas:
        img_temp = dibujar_zona(img_temp, z)
      st.image(
          cv2.cvtColor(img_temp, cv2.COLOR_BGR2RGB),
          caption="Vista previa del mapa con zonas registradas",
          use_container_width=True,
      )

else:
  st.warning(
      "👈 Por favor, suba una imagen del esquema SCADA en el panel izquierdo"
      " para comenzar."
  )