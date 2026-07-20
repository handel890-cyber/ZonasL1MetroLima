import base64
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


# --- CONVERSIÓN DE HEX A BGR ---
def hex_a_bgr(hex_color):
  hex_color = hex_color.lstrip('#')
  r = int(hex_color[0:2], 16)
  g = int(hex_color[2:4], 16)
  b = int(hex_color[4:6], 16)
  return (b, g, r)


# --- FUNCIONES DE DIBUJO ---
def dibujar_zona(img_base, zona, color_bgr, grosor, alpha):
  overlay = img_base.copy()

  # 1. Dibujar líneas del tramo
  for lin in zona.get("lineas", []):
    cv2.line(
        overlay,
        (int(lin["x_inicio"]), int(lin["y_inicio"])),
        (int(lin["x_fin"]), int(lin["y_fin"])),
        color_bgr,
        grosor,
    )

  # 2. Corchete Izquierdo [
  c_i = zona.get("corchete_izq", {})
  if c_i:
    cv2.line(
        overlay,
        (int(c_i["x"]), int(c_i["y1"])),
        (int(c_i["x"]), int(c_i["y2"])),
        color_bgr,
        max(3, grosor - 1),
    )
    cv2.line(
        overlay,
        (int(c_i["x"]), int(c_i["y1"])),
        (int(c_i["x"]) + 25, int(c_i["y1"])),
        color_bgr,
        max(3, grosor - 1),
    )
    cv2.line(
        overlay,
        (int(c_i["x"]), int(c_i["y2"])),
        (int(c_i["x"]) + 25, int(c_i["y2"])),
        color_bgr,
        max(3, grosor - 1),
    )

  # 3. Corchete Derecho ]
  c_d = zona.get("corchete_der", {})
  if c_d:
    cv2.line(
        overlay,
        (int(c_d["x"]), int(c_d["y1"])),
        (int(c_d["x"]), int(c_d["y2"])),
        color_bgr,
        max(3, grosor - 1),
    )
    cv2.line(
        overlay,
        (int(c_d["x"]), int(c_d["y1"])),
        (int(c_d["x"]) - 25, int(c_d["y1"])),
        color_bgr,
        max(3, grosor - 1),
    )
    cv2.line(
        overlay,
        (int(c_d["x"]), int(c_d["y2"])),
        (int(c_d["x"]) - 25, int(c_d["y2"])),
        color_bgr,
        max(3, grosor - 1),
    )

  # Mezcla de transparencia según la opacidad seleccionada
  beta = 1.0 - alpha
  return cv2.addWeighted(overlay, alpha, img_base, beta, 0)


# --- RENDERIZADOR HTML/JS CON PERSISTENCIA DE PANTALLA (LOCALSTORAGE GLOBAL) ---
def mostrar_visor_hd(img_bgr, height=650):
  _, buffer = cv2.imencode(".png", img_bgr)
  img_base64 = base64.b64encode(buffer).decode("utf-8")

  html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/openseadragon/4.1.0/openseadragon.min.js"></script>
        <style>
            #scada-container {{
                width: 100%;
                height: {height}px;
                background-color: #0e1117;
                border: 1px solid #30363d;
                border-radius: 8px;
            }}
        </style>
    </head>
    <body style="margin: 0; background-color: #0e1117;">
        <div id="scada-container"></div>
        <script>
            // Acceso al localStorage del navegador padre
            var storage = window.parent.localStorage;

            var viewer = OpenSeadragon({{
                id: "scada-container",
                prefixUrl: "https://cdnjs.cloudflare.com/ajax/libs/openseadragon/4.1.0/images/",
                tileSources: {{
                    type: 'image',
                    url: 'data:image/png;base64,{img_base64}'
                }},
                showNavigationControl: true,
                showFullScreenControl: true,
                showZoomControl: true,
                showHomeControl: true,
                gestureSettingsMouse: {{
                    clickToZoom: false,
                    dblClickToZoom: true,
                    scrollToZoom: true
                }},
                maxZoomPixelRatio: 5,
                minZoomLevel: 0.8
            }});

            // Guardar posición continuamente en la ventana principal del navegador
            function guardarPosicion() {{
                if (viewer && viewer.viewport) {{
                    var zoom = viewer.viewport.getZoom();
                    var center = viewer.viewport.getCenter();
                    storage.setItem('scada_zoom_v2', zoom);
                    storage.setItem('scada_x_v2', center.x);
                    storage.setItem('scada_y_v2', center.y);
                }}
            }}

            viewer.addHandler('pan', guardarPosicion);
            viewer.addHandler('zoom', guardarPosicion);

            // Al abrir la nueva imagen, restaurar inmediatamente la posición anterior
            viewer.addHandler('open', function() {{
                var savedZoom = storage.getItem('scada_zoom_v2');
                var savedX = storage.getItem('scada_x_v2');
                var savedY = storage.getItem('scada_y_v2');

                if (savedZoom && savedX && savedY) {{
                    viewer.viewport.zoomTo(parseFloat(savedZoom), null, true);
                    viewer.viewport.panTo(new OpenSeadragon.Point(parseFloat(savedX), parseFloat(savedY)), true);
                }}
            }});
        </script>
    </body>
    </html>
    """
  st.components.v1.html(html_code, height=height + 10)


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

# --- CONFIGURACIÓN DE ESTILO DE LÍNEA ---
st.sidebar.header("🎨 Personalización de Estilo")
hex_color_sel = st.sidebar.color_picker(
    "Color del Resaltado", value="#FFFF00"
)  # Amarillo neón
grosor_sel = st.sidebar.slider("Grosor de Línea (px)", 1, 15, 6)
opacidad_sel = (
    st.sidebar.slider("Opacidad (%)", 10, 100, 85) / 100.0
)  # Convierte a escala 0.10 - 1.0

color_bgr_sel = hex_a_bgr(hex_color_sel)

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
        img_final = dibujar_zona(
            img_original, zona_obj, color_bgr_sel, grosor_sel, opacidad_sel
        )
      else:
        img_final = img_original.copy()

      mostrar_visor_hd(img_final, height=650)

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
        img_temp = dibujar_zona(
            img_temp, z, color_bgr_sel, grosor_sel, opacidad_sel
        )

      mostrar_visor_hd(img_temp, height=500)

else:
  st.warning(
      "👈 Por favor, suba una imagen del esquema SCADA en el panel izquierdo"
      " para comenzar."
  )