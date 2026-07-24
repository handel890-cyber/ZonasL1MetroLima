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
st.sidebar.header("📁 Gestión de Archivos")

# Cargar Imagen Base
uploaded_image = st.sidebar.file_uploader(
    "1. Subir Imagen SCADA", type=["jpg", "png", "jpeg", "bmp"]
)

# Estado del JSON de GitHub
if st.session_state.zonas:
  st.sidebar.success(f"✅ `zonas.json` cargado con {len(st.session_state.zonas)} zonas.")
  st.sidebar.info("💡 Utiliza el panel flotante inferior izquierdo en la imagen para calibrar y descargar el JSON.")
else:
  st.sidebar.info("ℹ️ No se detectó `zonas.json` en GitHub.")

st.sidebar.divider()

# --- MODO DE TRABAJO ---
modo = st.sidebar.radio(
    "Modo de Trabajo:", ["Visor / Monitoreo", "Mapeador / Crear Zonas"]
)

# --- VISOR INTERACTIVO "TODO EN UNO" (HTML5/JS NATIVO) ---
def mostrar_visor_vectorial(img_bgr, lista_zonas, mostrar_selector=True, height=650):
  _, buffer = cv2.imencode(".png", img_bgr)
  img_base64 = base64.b64encode(buffer).decode("utf-8")
  zonas_json_str = json.dumps(lista_zonas)

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
            
            /* Panel Superior Derecho (Estilo) */
            #floating-controls {{
                position: absolute; top: 15px; right: 15px; z-index: 1000;
                background-color: rgba(22, 27, 34, 0.85); padding: 12px 15px;
                border-radius: 8px; border: 1px solid #444c56; color: #c9d1d9;
                font-family: sans-serif; font-size: 13px; backdrop-filter: blur(4px);
                width: 240px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            }}
            #controls-header {{
                display: flex; justify-content: space-between; align-items: center;
                font-weight: bold; border-bottom: 1px solid #444c56; padding-bottom: 8px; margin-bottom: 10px;
            }}
            #toggle-btn {{
                background: none; border: none; color: #c9d1d9; cursor: pointer;
                font-weight: bold; font-size: 14px; padding: 0 5px;
            }}
            #toggle-btn:hover {{ color: #ffffff; }}
            .control-group {{
                margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;
            }}
            input[type="range"] {{ width: 90px; }}
            input[type="color"] {{ cursor: pointer; border: none; background: none; width: 30px; height: 30px; padding: 0; }}

            /* Panel Inferior Derecho (Buscador de Zonas) */
            #zone-selector-panel {{
                position: absolute; bottom: 15px; right: 15px; z-index: 1000;
                background-color: rgba(22, 27, 34, 0.90); padding: 10px 15px;
                border-radius: 8px; border: 1px solid #1f6feb; color: #ffffff;
                font-family: sans-serif; font-size: 14px; backdrop-filter: blur(4px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.5); display: {'flex' if mostrar_selector else 'none'};
                align-items: center; gap: 10px;
            }}
            #zoneSelect {{
                background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;
                padding: 5px 10px; border-radius: 4px; font-size: 14px; outline: none; cursor: pointer;
            }}

            /* NUEVO: Panel Inferior Izquierdo (Calibración Y + Descarga) */
            #calibration-panel {{
                position: absolute; bottom: 15px; left: 15px; z-index: 1000;
                background-color: rgba(22, 27, 34, 0.90); padding: 12px 15px;
                border-radius: 8px; border: 1px solid #2ea043; color: #ffffff;
                font-family: sans-serif; font-size: 13px; backdrop-filter: blur(4px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.5); display: flex;
                flex-direction: column; gap: 8px; width: 180px;
            }}
            .cal-btn {{
                background-color: #21262d; border: 1px solid #30363d; color: #c9d1d9;
                padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 13px;
                transition: background-color 0.2s; text-align: center; width: 100%;
            }}
            .cal-btn:hover {{ background-color: #30363d; border-color: #8b949e; }}
            .download-btn {{
                background-color: #238636; border: 1px solid rgba(240,246,252,0.1); color: #ffffff;
                padding: 6px 10px; border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: bold;
                transition: background-color 0.2s; text-align: center; width: 100%; margin-top: 5px;
            }}
            .download-btn:hover {{ background-color: #2ea043; }}
        </style>
    </head>
    <body style="margin: 0; background-color: #0e1117;">
        
        <div id="scada-container">
            
            <!-- Panel Superior Derecho: Controles Visuales -->
            <div id="floating-controls">
                <div id="controls-header">
                    <span>🎨 Estilo de Zona</span>
                    <button id="toggle-btn" onclick="toggleControls()" title="Minimizar / Expandir">—</button>
                </div>
                <div id="controls-body">
                    <div class="control-group">
                        <label for="colorPicker">Color:</label>
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

            <!-- Panel Inferior Derecho: Buscador de Zonas -->
            <div id="zone-selector-panel">
                <label for="zoneSelect" style="font-weight: bold;">📍 Ir a Zona:</label>
                <select id="zoneSelect">
                    <option value="Ninguna">Ninguna</option>
                </select>
            </div>

            <!-- NUEVO Panel Inferior Izquierdo: Calibración y Descarga -->
            <div id="calibration-panel">
                <div style="font-weight: bold; text-align: center; border-bottom: 1px solid #444c56; padding-bottom: 5px;">
                    📐 Calibración Eje Y
                </div>
                <div style="display: flex; gap: 5px; margin-top: 5px;">
                    <button class="cal-btn" onclick="calibrarY(-1)">⬆️ Subir</button>
                    <button class="cal-btn" onclick="calibrarY(1)">⬇️ Bajar</button>
                </div>
                <button class="download-btn" onclick="descargarJSONLocal()">💾 Descargar JSON</button>
            </div>

        </div>

        <script>
            // Minimizar/Expandir Panel Superior
            function toggleControls() {{
                var body = document.getElementById("controls-body");
                var btn = document.getElementById("toggle-btn");
                var header = document.getElementById("controls-header");
                if (body.style.display === "none") {{
                    body.style.display = "block"; btn.innerText = "—";
                    header.style.borderBottom = "1px solid #444c56"; header.style.marginBottom = "10px";
                }} else {{
                    body.style.display = "none"; btn.innerText = "☐";
                    header.style.borderBottom = "none"; header.style.marginBottom = "0";
                }}
            }}

            var todasLasZonas = {zonas_json_str};
            var mostrarSelector = {'true' if mostrar_selector else 'false'};
            var zonaActual = null;

            if (!mostrarSelector && todasLasZonas.length > 0) {{
                zonaActual = todasLasZonas[todasLasZonas.length - 1]; 
            }}

            var zoneSelect = document.getElementById('zoneSelect');
            if (mostrarSelector && zoneSelect) {{
                todasLasZonas.forEach(function(z) {{
                    var opt = document.createElement('option');
                    opt.value = z.id;
                    opt.innerHTML = "Zona " + z.id;
                    zoneSelect.appendChild(opt);
                }});
            }}

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
                showNavigationControl: true, showFullScreenControl: true,
                showZoomControl: true, showHomeControl: true,
                gestureSettingsMouse: {{ clickToZoom: false, dblClickToZoom: true, scrollToZoom: true }},
                maxZoomPixelRatio: 5, minZoomLevel: 0.8
            }});

            var overlayCanvas = null;

            function redibujarOverlay() {{
                if (!overlayCanvas) return;
                var ctx = overlayCanvas.getContext('2d');
                var imgWidth = viewer.world.getItemAt(0).getContentSize().x;
                var imgHeight = viewer.world.getItemAt(0).getContentSize().y;

                textGrosor.innerText = inputGrosor.value;
                textOpacidad.innerText = Math.round(inputOpacidad.value * 100);

                overlayCanvas.width = imgWidth;
                overlayCanvas.height = imgHeight;
                ctx.clearRect(0, 0, imgWidth, imgHeight);

                if (!zonaActual) return;

                ctx.strokeStyle = inputColor.value;
                ctx.lineWidth = parseInt(inputGrosor.value);
                ctx.globalAlpha = parseFloat(inputOpacidad.value);
                ctx.lineCap = "round";

                if (zonaActual.lineas) {{
                    zonaActual.lineas.forEach(lin => {{
                        ctx.beginPath(); ctx.moveTo(lin.x_inicio, lin.y_inicio);
                        ctx.lineTo(lin.x_fin, lin.y_fin); ctx.stroke();
                    }});
                }}

                if (zonaActual.corchete_izq) {{
                    let c = zonaActual.corchete_izq;
                    ctx.beginPath(); ctx.moveTo(c.x + 25, c.y1); ctx.lineTo(c.x, c.y1);
                    ctx.lineTo(c.x, c.y2); ctx.lineTo(c.x + 25, c.y2); ctx.stroke();
                }}

                if (zonaActual.corchete_der) {{
                    let c = zonaActual.corchete_der;
                    ctx.beginPath(); ctx.moveTo(c.x - 25, c.y1); ctx.lineTo(c.x, c.y1);
                    ctx.lineTo(c.x, c.y2); ctx.lineTo(c.x - 25, c.y2); ctx.stroke();
                }}
            }}

            // --- FUNCIONES NUEVAS: CALIBRACIÓN Y DESCARGA JS ---
            function calibrarY(pixeles) {{
                if (!zonaActual) {{
                    alert("Por favor, selecciona una zona en el panel inferior derecho primero.");
                    return;
                }}

                if (zonaActual.lineas) {{
                    zonaActual.lineas.forEach(lin => {{
                        lin.y_inicio += pixeles;
                        lin.y_fin += pixeles;
                    }});
                }}
                if (zonaActual.corchete_izq) {{
                    zonaActual.corchete_izq.y1 += pixeles;
                    zonaActual.corchete_izq.y2 += pixeles;
                }}
                if (zonaActual.corchete_der) {{
                    zonaActual.corchete_der.y1 += pixeles;
                    zonaActual.corchete_der.y2 += pixeles;
                }}
                
                // Redibujar instantáneamente sin recargar la página
                redibujarOverlay();
            }}

            function descargarJSONLocal() {{
                // Generar el archivo JSON en base a los datos actuales de Javascript
                var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(todasLasZonas, null, 2));
                var dlAnchorElem = document.createElement('a');
                dlAnchorElem.setAttribute("href", dataStr);
                dlAnchorElem.setAttribute("download", "zonas_calibradas.json");
                document.body.appendChild(dlAnchorElem);
                dlAnchorElem.click();
                dlAnchorElem.remove();
            }}
            // ---------------------------------------------------

            function centrarEnZona(z) {{
                if (!z || !z.lineas || z.lineas.length === 0) return;
                var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                z.lineas.forEach(l => {{
                    minX = Math.min(minX, l.x_inicio, l.x_fin); minY = Math.min(minY, l.y_inicio, l.y_fin);
                    maxX = Math.max(maxX, l.x_inicio, l.x_fin); maxY = Math.max(maxY, l.y_inicio, l.y_fin);
                }});
                var cx = (minX + maxX) / 2; var cy = (minY + maxY) / 2;
                var imgWidth = viewer.world.getItemAt(0).getContentSize().x;
                var normX = cx / imgWidth; var normY = cy / imgWidth;

                viewer.viewport.panTo(new OpenSeadragon.Point(normX, normY), true);
                viewer.viewport.zoomTo(3, new OpenSeadragon.Point(normX, normY), true);
            }}

            inputColor.addEventListener('input', redibujarOverlay);
            inputGrosor.addEventListener('input', redibujarOverlay);
            inputOpacidad.addEventListener('input', redibujarOverlay);

            if (zoneSelect) {{
                zoneSelect.addEventListener('change', function() {{
                    var selectedId = this.value;
                    if (selectedId === "Ninguna") {{
                        zonaActual = null;
                    }} else {{
                        zonaActual = todasLasZonas.find(z => String(z.id) === String(selectedId));
                        centrarEnZona(zonaActual);
                    }}
                    redibujarOverlay();
                }});
            }}

            viewer.addHandler('open', function() {{
                overlayCanvas = document.createElement('canvas');
                var imgSize = viewer.world.getItemAt(0).getContentSize();
                overlayCanvas.width = imgSize.x; overlayCanvas.height = imgSize.y;

                viewer.addOverlay({{
                    element: overlayCanvas, location: new OpenSeadragon.Rect(0, 0, 1, imgSize.y / imgSize.x)
                }});

                redibujarOverlay();

                var storage = window.parent.localStorage;
                var savedZoom = storage.getItem('scada_zoom_v8');
                var savedX = storage.getItem('scada_x_v8');
                var savedY = storage.getItem('scada_y_v8');

                if (savedZoom && savedX && savedY) {{
                    viewer.viewport.zoomTo(parseFloat(savedZoom), null, true);
                    viewer.viewport.panTo(new OpenSeadragon.Point(parseFloat(savedX), parseFloat(savedY)), true);
                }}
            }});

            function guardarPosicion() {{
                if (viewer && viewer.viewport) {{
                    var storage = window.parent.localStorage;
                    storage.setItem('scada_zoom_v8', viewer.viewport.getZoom());
                    var center = viewer.viewport.getCenter();
                    storage.setItem('scada_x_v8', center.x);
                    storage.setItem('scada_y_v8', center.y);
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
      mostrar_visor_vectorial(img_original, st.session_state.zonas, mostrar_selector=True, height=720)

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
            lineas.append({"x_inicio": x2_1, "y_inicio": y2_1, "x_fin": x2_2, "y_fin": y2_2})
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
      zona_preview = [st.session_state.zonas[-1]] if st.session_state.zonas else []
      mostrar_visor_vectorial(img_original, zona_preview, mostrar_selector=False, height=500)

else:
  st.warning("👈 Por favor, suba una imagen del esquema SCADA en el panel izquierdo para comenzar.")