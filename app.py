import json
import os
import cv2
import numpy as np
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Sistema SCADA - Resaltador de Zonas HD",
    page_icon="🚊",
    layout="wide",
)

st.title("🚊 Sistema SCADA - Monitoreo y Resaltado de Zonas")


# --- FUNCIONES DE DIBUJO ---
def dibujar_zona(img_base, zona):
  overlay = img_base.copy()

  # 1. Dibujar líneas del tramo
  for lin in zona.get("lineas", []):
    cv2.line(
        overlay,
        (int(lin["x_inicio"]), int(lin["y_inicio"])),
        (int(lin["x_fin"]), int(lin["y_fin"])),
        (255, 255, 0),
        6,
    )

  # 2. Corchete Izquierdo [
  c_i = zona.get("corchete_izq", {})
  if c_i:
    cv2.line(
        overlay,
        (int(c_i["x"]), int(c_i["y1"])),
        (int(c_i["x"]), int(c_i["y2"])),
        (0, 255, 255),
        5,
    )
    cv2.line(
        overlay,
        (int(c_i["x"]), int(c_i["y1"])),
        (int(c_i["x"]) + 25, int(c_i["y1"])),
        (0, 255, 255),
        5,
    )
    cv2.line(
        overlay,
        (int(c_i["x"]), int(c_i["y2"])),
        (int(c_i["x"]) + 25, int(c_i["y2"])),
        (0, 255, 255),
        5,
    )

  # 3. Corchete Derecho ]
  c_d = zona.get("corchete_der", {})
  if c_d:
    cv2.line(
        overlay,
        (int(c_d["x"]), int(c_d["y1"])),
        (int(c_d["x"]), int(c_d["y2"])),
        (0, 255, 255),
        5,
    )
    cv2.line(
        overlay,
        (int(c_d["x"]), int(c_d["y1"])),
        (int(c_d["x"]) - 25, int(c_d["y1"])),
        (0, 255, 255),
        5,
    )
    cv2.line(
        overlay,
        (int(c_d["x"]), int(c_d["y2"])),
        (int(c_d["x"]) - 25, int(c_d["y2"])),
        (0, 255, 255),
        5,
    )

  # Resplandor/Mezcla
  return cv2.addWeighted(overlay, 0.85, img_base, 0.15, 0)


# --- CARGA AUTOMÁTICA DEL ARCHIVO JSON DESDE GITHUB ---
JSON_LOCAL = "zonas.json"

if "zonas" not in st.session_state:
  st.session_state.zonas = []
  if os.path.exists(JSON_LOCAL):
    try:
      with open(JSON_LOCAL, "r", encoding="utf-8") as f:
        st.session_state.zonas = json.load(f)
    except Exception as e:
      st.error(f"Error al leer el archivo {JSON_LOCAL} desde GitHub.")

# --- PANEL LATERAL (SIDEBAR) ---
st.sidebar.header("📁 Carga de Archivos")

# Cargar Imagen Base
uploaded_image = st.sidebar.file_uploader(
    "1. Subir Imagen SCADA", type=["jpg", "png", "jpeg"]
)

# Estado del JSON de GitHub
if st.session_state.zonas:
  st.sidebar.success(
      f"✅ `zonas.json` cargado con {len(st.session_state.zonas)} zonas."
  )
else:
  st.sidebar.info("ℹ️ No se detectó `zonas.json` en GitHub.")

st.sidebar.divider()

# --- MODO DE TRABAJO ---
modo = st.sidebar.radio(
    "Modo de Trabajo:", ["Visor / Monitoreo", "Mapeador / Crear Zonas"]
)

if uploaded_image is not None:
  file_bytes = np.asarray(bytearray(uploaded_image.read()), dtype=np.uint8)
  img_original = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

  # ----------------------------------------------------
  # MODO 1: VISOR / MONITOREO HD
  # ----------------------------------------------------
  if modo == "Visor / Monitoreo":
    col_ctrl, col_view = st.columns([1, 4])

    with col_ctrl:
      st.subheader("Buscador")
      ids_zonas = [str(z["id"]) for z in st.session_state.zonas]

      zona_seleccionada_id = st.selectbox(
          "Seleccione Zona:", options=["Ninguna"] + ids_zonas
      )

      if st.session_state.zonas:
        json_data = json.dumps(st.session_state.zonas, indent=2)
        st.download_button(
            label="💾 Descargar zonas.json",
            data=json_data,
            file_name="zonas.json",
            mime="application/json",
        )

    with col_view:
      if zona_seleccionada_id != "Ninguna":
        zona_obj = next(
            z
            for z in st.session_state.zonas
            if str(z["id"]) == zona_seleccionada_id
        )
        img_final = dibujar_zona(img_original, zona_obj)
      else:
        img_final = img_original.copy()

      img_rgb = cv2.cvtColor(img_final, cv2.COLOR_BGR2RGB)

      # Muestra la imagen preservando píxeles reales.
      # Pasa el cursor sobre la imagen y presiona el ícono '🔍 Ampliar' (Fullscreen)
      st.image(img_rgb, use_container_width=True)

      # Opción adicional: expandir a contenedor de ancho completo
      with st.expander("🔎 Ver imagen en calidad nativa / Zoom extra"):
        st.image(img_rgb, output_format="PNG")

  # ----------------------------------------------------
  # MODO 2: MAPEADOR / CREAR ZONAS
  # ----------------------------------------------------
  else:
    st.subheader("🛠️ Creador de Zonas (Ingreso Manual)")
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
      img_temp = img_original.copy()
      for z in st.session_state.zonas:
        img_temp = dibujar_zona(img_temp, z)

      img_rgb_preview = cv2.cvtColor(img_temp, cv2.COLOR_BGR2RGB)
      st.image(img_rgb_preview, use_container_width=True)

else:
  st.warning(
      "👈 Por favor, suba una imagen del esquema SCADA en el panel izquierdo"
      " para comenzar."
  )