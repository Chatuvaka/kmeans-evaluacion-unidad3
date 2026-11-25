"""
Generador del PDF de la Guía de Defensa Técnica del Proyecto K-Means.
Crea un documento de estudio conciso, elegante y profesional en docs/guia_defensa_proyecto_kmeans.pdf.
"""
import base64
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
PDF_SALIDA = DOCS_DIR / "guia_defensa_proyecto_kmeans.pdf"
HTML_TEMP = DOCS_DIR / "guia_defensa_temp.html"

HTML_CONTENIDO = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Guía de Defensa Técnica - Proyecto K-Means</title>
    <style>
        @page {
            size: letter;
            margin: 16mm 16mm 16mm 16mm;
            @bottom-right {
                content: "Página " counter(page);
            }
        }
        *, *:before, *:after { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            color: #2d3748;
            line-height: 1.5;
            font-size: 10pt;
            background: #ffffff;
            margin: 0;
            padding: 0;
        }
        .header {
            border-bottom: 3px solid #2b6cb0;
            padding-bottom: 10px;
            margin-bottom: 18px;
        }
        .header h1 {
            font-size: 18pt;
            color: #1a365d;
            margin: 0 0 4px 0;
            font-weight: 700;
        }
        .header .subtitulo {
            font-size: 10.5pt;
            color: #4a5568;
            margin: 0 0 6px 0;
            font-weight: 500;
        }
        .meta-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 6px;
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 9pt;
            color: #4a5568;
        }
        .meta-item strong { color: #2d3748; }

        h2 {
            font-size: 13pt;
            color: #2b6cb0;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 4px;
            margin-top: 18px;
            margin-bottom: 10px;
            page-break-after: avoid;
        }
        h3 {
            font-size: 11pt;
            color: #1a365d;
            margin-top: 12px;
            margin-bottom: 4px;
            page-break-after: avoid;
        }

        .box-elevator {
            background-color: #ebf8ff;
            border-left: 4px solid #3182ce;
            padding: 10px 14px;
            border-radius: 0 6px 6px 0;
            font-style: italic;
            margin-bottom: 14px;
            color: #2c5282;
            font-size: 9.5pt;
        }

        .pregunta-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #dd6b20;
            border-radius: 0 6px 6px 0;
            padding: 10px 14px;
            margin-bottom: 14px;
            page-break-inside: avoid;
        }
        .pregunta-card.vip {
            border-left-color: #38a169;
        }
        .pregunta-titulo {
            font-weight: 700;
            color: #c05621;
            font-size: 10.5pt;
            margin-bottom: 6px;
        }
        .pregunta-card.vip .pregunta-titulo {
            color: #276749;
        }
        .respuesta {
            font-size: 9.5pt;
            color: #2d3748;
        }
        .respuesta ul {
            margin: 4px 0 0 0;
            padding-left: 18px;
        }
        .respuesta li {
            margin-bottom: 4px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 8.5pt;
            margin: 10px 0 16px 0;
            page-break-inside: avoid;
        }
        th, td {
            padding: 6px 8px;
            border: 1px solid #cbd5e0;
            text-align: left;
        }
        th {
            background: #2b6cb0;
            color: #ffffff;
            font-weight: 600;
            text-align: center;
        }
        tbody tr:nth-child(even) { background: #f7fafc; }

        .tip-box {
            background: #f0fff4;
            border-left: 4px solid #38a169;
            padding: 10px 12px;
            border-radius: 0 6px 6px 0;
            font-size: 9pt;
            color: #22543d;
            margin-top: 12px;
            page-break-inside: avoid;
        }
        .badge {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 8pt;
            font-weight: 600;
        }
        .badge-vip { background: #c6f6d5; color: #22543d; }
        .badge-regular { background: #feebc8; color: #7b341e; }
        .badge-ocasional { background: #e9d8fd; color: #44337a; }
        .badge-riesgo { background: #fed7d7; color: #742a2a; }
    </style>
</head>
<body>

    <div class="header">
        <h1>Guía de Defensa Técnica del Proyecto</h1>
        <div class="subtitulo">Extracción de Conocimiento en Base de Datos · Segmentación de Clientes con K-Means y RFM</div>
        <div class="meta-grid">
            <div class="meta-item"><strong>Docente:</strong> Prof. Julia Elizabeth García Herrera</div>
            <div class="meta-item"><strong>Grupo:</strong> IDGS 9 - 3 | <strong>Fecha:</strong> 24 / Noviembre / 2026</div>
            <div class="meta-item"><strong>Integrantes:</strong> Jesus Rodolfo Lopez Gamez · Josue Misraim Valenzuela Verdugo · Axel Alan Jimenez Jaramillo</div>
            <div class="meta-item"><strong>Repositorio:</strong> https://github.com/Chatuvaka/kmeans-evaluacion-unidad3</div>
        </div>
    </div>

    <h2>1. Resumen Ejecutivo (El "Elevator Pitch" para abrir)</h2>
    <div class="box-elevator">
        "El objetivo del proyecto fue segmentar a los clientes mediante aprendizaje no supervisado (K-Means) aplicando la metodología RFM (Recencia, Frecuencia y Monto de Gasto) para diseñar estrategias comerciales basadas en datos.<br><br>
        Partimos de un dataset con 915 registros con problemas reales de captura (nulos, duplicados, inconsistencias tipográficas, atípicos y montos como texto). Tras el preprocesamiento, obtuvimos 900 registros limpios y estandarizados con StandardScaler. Evaluamos K de 2 a 8 mediante el método del codo, Silhouette, Davies-Bouldin y Calinski-Harabasz, determinando que K = 4 es la solución óptima (Silhouette = 0.585).<br><br>
        Los resultados identificaron 4 segmentos accionables (VIP, Leales regulares, Ocasionales y En riesgo), demostrando que el 11.7% de los clientes genera el 45.6% del ingreso y que existen $1.37M MXN en riesgo de abandono. El modelo se implementó en un dashboard interactivo de Streamlit con filtros reactivos y KPIs."
    </div>

    <h2>2. Las 5 Preguntas Clave que Seguro Hará la Maestra</h2>

    <div class="pregunta-card">
        <div class="pregunta-titulo">Pregunta 1: ¿Por qué solo usaron 3 variables para K-Means y dejaron fuera variables como ticket promedio, edad, satisfacción o las categóricas?</div>
        <div class="respuesta">
            <ul>
                <li><strong>ticket_promedio:</strong> Es una variable derivada directamente (<em>gasto_total / frecuencia</em>). Meterla introduciría colinealidad matemática y sobreponderaría el factor monetario en el cálculo euclidiano.</li>
                <li><strong>Variables categóricas (género, región, canal):</strong> K-Means se basa en distancias euclidianas continuas. Meter columnas 0/1 (one-hot encoding) rompe el supuesto geométrico continuo y distorsiona las distancias.</li>
                <li><strong>Edad y Satisfacción:</strong> Se reservaron como variables descriptivas complementarias para perfilar a los grupos una vez creados, sin sesgar la segmentación conductual de compra.</li>
            </ul>
        </div>
    </div>

    <div class="pregunta-card">
        <div class="pregunta-titulo">Pregunta 2: ¿Por qué fue indispensable usar StandardScaler? ¿Qué ocurría si no escalaban?</div>
        <div class="respuesta">
            <ul>
                <li>K-Means minimiza la distancia euclidiana: <em>d(x, y) = &radic;[&Sigma;(x<sub>i</sub> - y<sub>i</sub>)<sup>2</sup>]</em>.</li>
                <li>En los datos crudos, la desviación estándar del <em>gasto_total</em> era de <strong>~$13,461 MXN</strong>, mientras que la frecuencia tenía una desviación de <strong>~9 compras</strong> y la recencia de <strong>~88 días</strong>. La diferencia monetaria dominaba el 99% de la distancia euclidiana.</li>
                <li><strong>Sin escalar:</strong> Los clústeres solo se agrupaban por monto de dinero (ARI = 0.51, Silhouette caía a 0.352), ignorando totalmente la recencia (impidiendo detectar clientes en abandono). Con <code>StandardScaler</code> las 3 variables tienen <strong>media 0 y desviación 1</strong>.</li>
            </ul>
        </div>
    </div>

    <div class="pregunta-card vip">
        <div class="pregunta-titulo">Pregunta 3: Si para K=2 el Silhouette era 0.581 y para K=4 era 0.585 (muy similares), ¿por qué eligieron K=4?</div>
        <div class="respuesta">
            <ul>
                <li><strong>Criterio Multimétrica:</strong> K = 4 no solo alcanza el máximo de Silhouette (0.585), sino que minimiza el índice Davies-Bouldin (<strong>0.516</strong> frente a 0.560 en K=2, <em>menor es mejor</em>) y más que duplica el índice Calinski-Harabasz (<strong>2,302.6</strong> frente a 941.5 en K=2, <em>mayor es mejor</em>).</li>
                <li><strong>Método del Codo:</strong> De K=3 a K=4 la inercia baja <strong>53.4%</strong> (marcando el codo claro); a partir de K=4, aumentar a K=5 apenas reduce 13.6%.</li>
                <li><strong>Criterio de Negocio:</strong> K = 2 divide el dataset en dos mitades genéricas (activos vs. inactivos), lo cual es inútil para marketing. K = 4 aísla con precisión el grupo VIP del regular y separa a clientes ocasionales de los que están en verdadero riesgo de abandono.</li>
            </ul>
        </div>
    </div>

    <div class="pregunta-card">
        <div class="pregunta-titulo">Pregunta 4: ¿Cómo trataron los valores atípicos (outliers)? ¿Eliminaron clientes?</div>
        <div class="respuesta">
            <ul>
                <li>La regla clásica de Tukey (1.5 &times; IQR) marcaba 107 gastos como atípicos. Sin embargo, en comercio electrónico esos registros son <strong>clientes VIP de alto valor legítimos</strong>. Si los eliminábamos, borrábamos el segmento más valioso.</li>
                <li><strong>Capping (Recorte):</strong> Solo se recortaron al límite superior los 9 registros extremos que superaban simultáneamente la cerca extrema (3.0 &times; IQR) y el percentil 99 (errores de captura). <strong>No se eliminó ningún cliente</strong>, preservando los 900 registros.</li>
            </ul>
        </div>
    </div>

    <div class="pregunta-card">
        <div class="pregunta-titulo">Pregunta 5: ¿Cuáles son los 4 segmentos descubiertos y qué estrategias recomiendan?</div>
        <div class="respuesta">
            <table>
                <thead>
                    <tr>
                        <th>Clúster</th>
                        <th>Clientes (%)</th>
                        <th>Gasto (%)</th>
                        <th>Frec. / Gasto / Recencia</th>
                        <th>Canal Principal</th>
                        <th>Estrategia Comercial</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>C0 · VIP</strong></td>
                        <td>105 (11.7%)</td>
                        <td><strong>45.6%</strong></td>
                        <td>31.6 comp / $44,791 / 11 días</td>
                        <td>App móvil (43%)</td>
                        <td><strong>Retención:</strong> Programa lealtad premium, preventas exclusivas, atención prioritaria.</td>
                    </tr>
                    <tr>
                        <td><strong>C1 · Leales regulares</strong></td>
                        <td>248 (27.6%)</td>
                        <td>31.6%</td>
                        <td>17.3 comp / $13,139 / 23 días</td>
                        <td>Online (40%)</td>
                        <td><strong>Crecimiento:</strong> Venta cruzada (cross-selling) para elevar ticket y convertirlos a VIP.</td>
                    </tr>
                    <tr>
                        <td><strong>C2 · Ocasionales</strong></td>
                        <td>341 (37.9%)</td>
                        <td>9.5%</td>
                        <td>5.5 comp / $2,883 / 73 días</td>
                        <td>Tienda física (56%)</td>
                        <td><strong>Activación:</strong> Cupones de segunda compra y promociones en mostrador.</td>
                    </tr>
                    <tr>
                        <td><strong>C3 · En riesgo</strong></td>
                        <td>206 (22.9%)</td>
                        <td>13.3%</td>
                        <td>8.1 comp / $6,682 / <strong>235 días</strong></td>
                        <td>Tienda física (51%)</td>
                        <td><strong>Reactivación:</strong> Campaña win-back urgente con descuento temporal; $1.37M MXN en juego.</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <div class="tip-box">
        <strong>Detalle metodológico fino para ganar puntos extra:</strong><br>
        Si la maestra pregunta si la <em>Satisfacción</em> valida el modelo: Aclaren que al ser un dataset sintético con distribuciones latentes, la satisfacción actúa como <strong>variable descriptiva complementaria</strong> y no como validación externa formal. No obstante, es sumamente coherente: el segmento VIP tuvo satisfacción promedio de <strong>4.34/5</strong> mientras que el segmento en riesgo cayó a <strong>2.57/5</strong>, respaldando que el alejamiento en compras va de la mano con una mala experiencia de usuario.
    </div>

</body>
</html>
"""

def compilar_pdf():
    HTML_TEMP.write_text(HTML_CONTENIDO, encoding="utf-8")
    print(f"HTML generado en {HTML_TEMP.name}")

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=opts)
    try:
        url = HTML_TEMP.resolve().as_uri()
        print(f"Cargando en Chrome: {url}...")
        driver.get(url)

        print_params = {
            "landscape": False,
            "displayHeaderFooter": False,
            "printBackground": True,
            "preferCSSPageSize": True,
            "marginTop": 0.4,
            "marginBottom": 0.4,
            "marginLeft": 0.4,
            "marginRight": 0.4,
        }

        print("Compilando PDF de la guía de defensa...")
        resultado = driver.execute_cdp_cmd("Page.printToPDF", print_params)
        pdf_bytes = base64.b64decode(resultado["data"])
        PDF_SALIDA.write_bytes(pdf_bytes)
        print(f"  [Guía generada con éxito] {PDF_SALIDA.name} ({len(pdf_bytes):,} bytes)")
    finally:
        driver.quit()
        if HTML_TEMP.exists():
            HTML_TEMP.unlink()

if __name__ == "__main__":
    compilar_pdf()
