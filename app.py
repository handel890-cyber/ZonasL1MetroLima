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


# --- VISOR INTERACTIVO CON CONTROLES NATIVOS EN JAVASCRIPT ---
def mostrar_visor_vectorial(img_bgr, zona_data, height=650):
  _, buffer = cv2.imencode(".png", img_bgr)
  img_base64 = base64.b64encode(buffer).decode("utf-8")
  zona_json_str = json.dumps(zona_data) if zona_data else "null"

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
                position: relative;
            }}
            /* Estilo del panel flotante (Derecha y Minimizable) */
            #floating-controls {{
                position: absolute;
                top: 15px;
                right: 15px; /* Movido a la derecha */
                z-index: 1000;
                background-color: rgba(22, 27, 34, 0.85);
                padding: 12px 15px;
                border-radius: 8px;
                border: 1px solid #444c56;
                color: #c9d1d9;
                font-family: sans-serif;
                font-size: 13px;
                backdrop-filter: blur(4px);
                width: 240px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            }}
            #controls-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-weight: bold;
                border-bottom: 1px solid #444c56;
                padding-bottom: 8px;
                margin-bottom: 10px;
            }}
            #toggle-btn {{
                background: none;
                border: none;
                color: #c9d1d9;
                cursor: pointer;
                font-weight: bold;
                font-size: 14px;
                padding: 0 5px;
            }}
            #toggle-btn:hover {{ color: #ffffff; }}
            .control-group {{
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}
            input[type="range"] {{ width: 90px; }}
            input[type="color"] {{ cursor: pointer; border: none; background: none; width: 30px; height: 30px; padding: 0; }}
        </style>
    </head>
    <body style="margin: 0; background-color: #0e1117;">
        
        <div id="scada-container">
            <!-- Panel Flotante de Controles Visuales -->
            <div id="floating-controls">
                <div id="controls-header">
                    <span>🎨 Estilo de Zona</span>
                    <button id="toggle-btn" onclick="toggleControls()" title="Minimizar / Expandir">—</button>
                </div>
                
                <div id="controls-body">
                    <div class="control-group">
                        <label for="colorPicker">Color de Línea:</label>
                        <input type="color" id="colorPicker" value="#FFFF00">
                    </div>
                    
                    <div class="control-group">
                        <label for="grosorSlider">Grosor (<span id="grosorVal">6</span>px):</label>
                        <input type="range" id="grosorSlider" min="1" max="25" value="6">
                    </div>
                    
                    <div class="control-group">
                        <label for="opacidadSlider">Opacidad (<span id="opacidadVal">85</span>%):</label>
                        <input type="range" id="opacidadSlider" min="0.1" max="1.0" step="0.05" value="0.85">
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Lógica para Minimizar/Expandir el panel
            function toggleControls() {{
                var body = document.getElementById("controls-body");
                var btn = document.getElementById("toggle-btn");
                var header = document.getElementById("controls-header");
                
                if (body.style.display === "none") {{
                    body.style.display = "block";
                    btn.innerText = "—";
                    header.style.borderBottom = "1px solid #444c56";
                    header.style.marginBottom = "10px";
                }} else {{
                    body.style.display = "none";
                    btn.innerText = "☐";
                    header.style.borderBottom = "none";
                    header.style.marginBottom = "0";
                }}
            }}

            var zona = {zona_json_str};
            
            // Referencias a los controles HTML
            var inputColor = document.getElementById('colorPicker');
            var inputGrosor = document.getElementById('grosorSlider');
            var inputOpacidad = document.getElementById('opacidadSlider');
            
            var textGrosor = document.getElementById('grosorVal');
            var textOpacidad = document.getElementById('opacidadVal');

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
                gestureSettingsMouse: {{ clickToZoom: false, dblClickToZoom: true, scrollToZoom: true }},
                maxZoomPixelRatio: 5,
                minZoomLevel: 0.8
            }});

            var overlayCanvas = null;

            // Función para dibujar los gráficos sin recargar nada
            function redibujarOverlay() {{
                if (!overlayCanvas || !zona) return;
                var ctx = overlayCanvas.getContext('2d');
                var imgWidth = viewer.world.getItemAt(0).getContentSize().x;
                var imgHeight = viewer.world.getItemAt(0).getContentSize().y;

                // Actualizar etiquetas de texto
                textGrosor.innerText = inputGrosor.value;
                textOpacidad.innerText = Math.round(inputOpacidad.value * 100);

                overlayCanvas.width = imgWidth;
                overlayCanvas.height = imgHeight;

                ctx.clearRect(0, 0, imgWidth, imgHeight);
                ctx.strokeStyle = inputColor.value;
                ctx.lineWidth = parseInt(inputGrosor.value);
                ctx.globalAlpha = parseFloat(inputOpacidad.value);
                ctx.lineCap = "round";

                // 1. Lineas principales
                if (zona.lineas) {{
                    zona.lineas.forEach(lin => {{
                        ctx.beginPath();
                        ctx.moveTo(lin.x_inicio, lin.y_inicio);
                        ctx.lineTo(lin.x_fin, lin.y_fin);
                        ctx.stroke();
                    }});
                }}

                // 2. Corchete Izquierdo
                if (zona.corchete_izq) {{
                    let c = zona.corchete_izq;
                    ctx.beginPath();
                    ctx.moveTo(c.x + 25, c.y1);
                    ctx.lineTo(c.x, c.y1);
                    ctx.lineTo(c.x, c.y2);
                    ctx.lineTo(c.x + 25, c.y2);
                    ctx.stroke();
                }}

                // 3. Corchete Derecho
                if (zona.corchete_der) {{
                    let c = zona.corchete_der;
                    ctx.beginPath();
                    ctx.moveTo(c.x - 25, c.y1);
                    ctx.lineTo(c.x, c.y1);
                    ctx.lineTo(c.x, c.y2);
                    ctx.lineTo(c.x - 25, c.y2);
                    ctx.stroke();
                }}
            }}

            // Event Listeners: Cada vez que mueves un control, se redibuja en vivo
            inputColor.addEventListener('input', redibujarOverlay);
            inputGrosor.addEventListener('input', redibujarOverlay);
            inputOpacidad.addEventListener('input', redibujarOverlay);

            viewer.addHandler('open', function() {{
                overlayCanvas = document.createElement('canvas');
                var imgSize = viewer.world.getItemAt(0).getContentSize();
                overlayCanvas.width = imgSize.x;
                overlayCanvas.height = imgSize.y;

                viewer.addOverlay({{
                    element: overlayCanvas,
                    location: new OpenSeadragon.Rect(0, 0, 1, imgSize.y / imgSize.x)
                }});

                redibujarOverlay();

                // Restaurar zoom solo al cargar el mapa entero
                var storage = window.parent.localStorage;
                var savedZoom = storage.getItem('scada_zoom_v4');
                var savedX = storage.getItem('scada_x_v4');
                var savedY = storage.getItem('scada_y_v4');

                if (savedZoom && savedX && savedY) {{
                    viewer.viewport.zoomTo(parseFloat(savedZoom), null, true);
                    viewer.viewport.panTo(new OpenSeadragon.Point(parseFloat(savedX), parseFloat(savedY)), true);
                }}
            }});

            function guardarPosicion() {{
                if (viewer && viewer.viewport) {{
                    var storage = window.parent.localStorage;
                    storage.setItem('scada_zoom_v4', viewer.viewport.getZoom());
                    var center = viewer.viewport.getCenter();
                    storage.setItem('scada_x_v4', center.x);
                    storage.setItem('scada_y_v4', center.y);
                }}
            }}

            viewer.addHandler('pan', guardarPosicion);
            viewer.addHandler('zoom', guardarPosicion);
        </script>
    </body>
    </html>
    """
  st.components.v1.html(html_code, height=height + 10)


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
      zona_obj = None
      if zona_seleccionada_id != "Ninguna":
        zona_obj = next(
            z
            for z in st.session_state.zonas
            if str(z["id"]) == zona_seleccionada_id
        )

      mostrar_visor_vectorial(img_original, zona_obj, height=650)

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
      # Mostrar la última zona creada si existe
      zona_preview = (
          st.session_state.zonas[-1] if st.session_state.zonas else None
      )
      mostrar_visor_vectorial(img_original, zona_preview, height=500)

else:
  st.warning(
      "👈 Por favor, suba una imagen del esquema SCADA en el panel izquierdo"
      " para comenzar."
  )