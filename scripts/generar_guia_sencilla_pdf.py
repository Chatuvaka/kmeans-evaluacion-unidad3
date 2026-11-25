"""
Generador del PDF con la Explicación Sencilla y Didáctica del Proyecto K-Means.
Crea un documento de estudio muy visual y claro en docs/guia_explicacion_sencilla_kmeans.pdf.
"""
import base64
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
PDF_SALIDA = DOCS_DIR / "guia_explicacion_sencilla_kmeans.pdf"
HTML_TEMP = DOCS_DIR / "guia_sencilla_temp.html"

HTML_CONTENIDO = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Explicación Sencilla del Proyecto K-Means</title>
    <style>
        @page {
            size: letter;
            margin: 15mm 16mm 15mm 16mm;
            @bottom-right {
                content: "Página " counter(page);
            }
        }
        *, *:before, *:after { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            color: #2d3748;
            line-height: 1.5;
            font-size: 9.8pt;
            background: #ffffff;
            margin: 0;
            padding: 0;
        }
        .header {
            border-bottom: 3px solid #319795;
            padding-bottom: 8px;
            margin-bottom: 14px;
        }
        .header h1 {
            font-size: 17pt;
            color: #234e52;
            margin: 0 0 4px 0;
            font-weight: 700;
        }
        .header .subtitulo {
            font-size: 10pt;
            color: #4a5568;
            margin: 0 0 6px 0;
            font-weight: 500;
        }
        .meta-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 4px 10px;
            background: #e6fffa;
            border: 1px solid #b2f5ea;
            border-radius: 6px;
            padding: 7px 12px;
            font-size: 8.5pt;
            color: #234e52;
        }
        .meta-item strong { color: #1d4044; }

        h2 {
            font-size: 12pt;
            color: #285e61;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 3px;
            margin-top: 14px;
            margin-bottom: 8px;
            page-break-after: avoid;
        }

        .card-historia {
            background-color: #f7fafc;
            border-left: 4px solid #319795;
            padding: 9px 12px;
            border-radius: 0 6px 6px 0;
            margin-bottom: 12px;
            font-size: 9.5pt;
            page-break-inside: avoid;
        }

        .rfm-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 12px;
            page-break-inside: avoid;
        }
        .rfm-card {
            background: #ffffff;
            border: 1px solid #cbd5e0;
            border-top: 3px solid #3182ce;
            border-radius: 4px;
            padding: 8px 10px;
            text-align: center;
        }
        .rfm-letra {
            font-size: 14pt;
            font-weight: 700;
            color: #2b6cb0;
        }
        .rfm-nombre {
            font-weight: 600;
            color: #1a202c;
            font-size: 9pt;
            margin-bottom: 4px;
        }
        .rfm-desc {
            font-size: 8pt;
            color: #4a5568;
        }

        .pasos-container {
            display: grid;
            grid-template-columns: 1fr;
            gap: 8px;
            margin-bottom: 12px;
        }
        .paso-box {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #4299e1;
            padding: 8px 12px;
            border-radius: 0 5px 5px 0;
            page-break-inside: avoid;
        }
        .paso-titulo {
            font-weight: 700;
            color: #2b6cb0;
            font-size: 9.5pt;
            margin-bottom: 3px;
        }
        .paso-texto {
            font-size: 9pt;
            color: #2d3748;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 8.5pt;
            margin: 8px 0 12px 0;
            page-break-inside: avoid;
        }
        th, td {
            padding: 6px 8px;
            border: 1px solid #cbd5e0;
            text-align: left;
        }
        th {
            background: #285e61;
            color: #ffffff;
            font-weight: 600;
            text-align: center;
        }
        tbody tr:nth-child(even) { background: #f7fafc; }

        .guion-box {
            background: #feebc8;
            border-left: 4px solid #dd6b20;
            padding: 10px 14px;
            border-radius: 0 6px 6px 0;
            color: #7b341e;
            font-size: 9.5pt;
            margin-top: 10px;
            page-break-inside: avoid;
        }
        .guion-box strong { color: #9c4221; }

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
        <h1>Explicación Sencilla del Proyecto K-Means</h1>
        <div class="subtitulo">Guía Rápida para Entender y Explicar el Proyecto con Palabras Claras y Cotidianas</div>
        <div class="meta-grid">
            <div class="meta-item"><strong>Materia:</strong> Extracción de Conocimiento en Base de Datos</div>
            <div class="meta-item"><strong>Docente:</strong> Prof. Julia Elizabeth García Herrera</div>
            <div class="meta-item"><strong>Integrantes:</strong> Jesus Rodolfo Lopez Gamez · Josue Misraim Valenzuela Verdugo · Axel Alan Jimenez Jaramillo</div>
            <div class="meta-item"><strong>Grupo:</strong> IDGS 9 - 3 | <strong>Fecha:</strong> 24 / Noviembre / 2026</div>
        </div>
    </div>

    <h2>1. ¿Qué problema resuelve el proyecto? (La historia detrás de los datos)</h2>
    <div class="card-historia">
        Imagina que eres dueño de una tienda con <strong>900 clientes</strong>. Si tratas a todos exactamente igual (mandándoles la misma promoción o el mismo correo de <em>"20% de descuento"</em>), pierdes dinero:
        <ul>
            <li>Al cliente que te compra cada 3 días y gasta mucho, no necesitas regalarle descuento; él ya es fiel.</li>
            <li>Al cliente que hace 8 meses no compra porque tuvo una mala experiencia, un cupón simple no le interesa.</li>
            <li>Al cliente esporádico que compra de vez en cuando, a ese sí le sirve una promoción para que vuelva pronto.</li>
        </ul>
        <strong>El objetivo del proyecto:</strong> Agrupar a los clientes automáticamente con inteligencia artificial (K-Means) para saber quién es quién y aplicar la estrategia comercial correcta.
    </div>

    <h2>2. La Regla Mágica: ¿Qué es el modelo RFM?</h2>
    <div class="rfm-grid">
        <div class="rfm-card">
            <div class="rfm-letra">R</div>
            <div class="rfm-nombre">Recencia</div>
            <div class="rfm-desc">¿Hace cuántos días compró por última vez?<br><em>(Mide si el cliente sigue activo o ya nos abandonó)</em></div>
        </div>
        <div class="rfm-card">
            <div class="rfm-letra">F</div>
            <div class="rfm-nombre">Frecuencia</div>
            <div class="rfm-desc">¿Cuántas veces al año compra?<br><em>(Mide la lealtad y el hábito de compra)</em></div>
        </div>
        <div class="rfm-card">
            <div class="rfm-letra">M</div>
            <div class="rfm-nombre">Monto (Gasto)</div>
            <div class="rfm-desc">¿Cuánto dinero gastó en el año?<br><em>(Mide el valor económico para la empresa)</em></div>
        </div>
    </div>

    <h2>3. El Viaje del Proyecto: ¿Cómo funciona el código paso a paso?</h2>
    <div class="pasos-container">
        <div class="paso-box">
            <div class="paso-titulo">Paso 1: La Limpieza de Datos (Preparar los ingredientes)</div>
            <div class="paso-texto">
                Los datos reales vienen con errores: categorías mal escritas (<em>"Online"</em> vs <em>"online"</em>), montos guardados como texto (<em>"$12,345.50"</em>), filas duplicadas y celdas vacías. Corregimos los formatos, eliminamos duplicados e imputamos los valores nulos con la mediana. Dejamos <strong>900 clientes listos</strong> para el algoritmo.
            </div>
        </div>

        <div class="paso-box">
            <div class="paso-titulo">Paso 2: La Báscula Justa (StandardScaler)</div>
            <div class="paso-texto">
                Si comparas $40,000 pesos con 15 compras, la computadora creerá que el dinero es millones de veces más importante solo porque el número es más grande. <code>StandardScaler</code> pone a las 3 variables (días, compras y pesos) en una misma escala justa (media 0 y desviación 1), para que ninguna domine por error.
            </div>
        </div>

        <div class="paso-box">
            <div class="paso-titulo">Paso 3: ¿En cuántos grupos dividir? (K-Means con K = 4)</div>
            <div class="paso-texto">
                Le dijimos al algoritmo que probara desde 2 hasta 8 grupos. Con dos pruebas matemáticas (<strong>el método del Codo</strong> y el <strong>Silhouette</strong>), descubrimos que en <strong>K = 4 grupos</strong> los clientes quedaban perfectamente agrupados y con sentido comercial.
            </div>
        </div>

        <div class="paso-box">
            <div class="paso-titulo">Paso 4: El Dashboard Interactivo en Streamlit</div>
            <div class="paso-texto">
                En lugar de entregar código o tablas aburridas de Excel, creamos una aplicación web interactiva donde cualquiera puede mover filtros, ver gráficas en 2D y 3D, y analizar las métricas en tiempo real.
            </div>
        </div>
    </div>

    <h2>4. ¿Quiénes son los 4 tipos de clientes que encontramos?</h2>
    <table>
        <thead>
            <tr>
                <th>Segmento</th>
                <th>¿Quiénes son?</th>
                <th>Cifras Clave</th>
                <th>Canal Favorito</th>
                <th>Estrategia Recomendada</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><span class="badge badge-vip">C0 · Clientes VIP</span></td>
                <td>Compran seguido, gastan mucho y están super activos.</td>
                <td><strong>11.7%</strong> clientes<br><strong>45.6%</strong> del dinero</td>
                <td>App móvil (43%)</td>
                <td><strong>Cuidarlos como oro:</strong> Preventas exclusivas, atención VIP y programa de lealtad.</td>
            </tr>
            <tr>
                <td><span class="badge badge-regular">C1 · Leales regulares</span></td>
                <td>Compran de forma constante con gasto medio; la base fiel.</td>
                <td><strong>27.6%</strong> clientes<br><strong>31.6%</strong> del dinero</td>
                <td>Online (40%)</td>
                <td><strong>Hacerlos crecer:</strong> Ventas cruzadas (paquetes) para que suban a VIP.</td>
            </tr>
            <tr>
                <td><span class="badge badge-ocasional">C2 · Ocasionales</span></td>
                <td>Compran poco y con tickets bajos; entran y salen.</td>
                <td><strong>37.9%</strong> clientes<br><strong>9.5%</strong> del dinero</td>
                <td>Tienda física (56%)</td>
                <td><strong>Activarlos:</strong> Cupones de segunda compra y promociones en mostrador.</td>
            </tr>
            <tr>
                <td><span class="badge badge-riesgo">C3 · En riesgo</span></td>
                <td>Llevan casi <strong>8 meses sin comprar</strong> (235 días).</td>
                <td><strong>22.9%</strong> clientes<br><strong>$1.37M MXN</strong> en riesgo</td>
                <td>Tienda física (51%)</td>
                <td><strong>Reactivación urgente:</strong> Campaña <em>win-back</em> con 30% de descuento antes de perderlos.</td>
            </tr>
        </tbody>
    </table>

    <h2>5. Tu Guion de 30 Segundos (Para responder con seguridad si te preguntan)</h2>
    <div class="guion-box">
        <strong>"Lo que hicimos fue tomar los datos de 900 clientes, limpiarlos y aplicar el algoritmo K-Means con las variables RFM (Recencia, Frecuencia y Monto de gasto). Escalamos las variables para que el dinero no opacara a las compras y demostramos matemáticamente que el número ideal de grupos era 4.<br><br>
        Así descubrimos que un grupo pequeño de clientes VIP (11%) genera casi la mitad de todo el dinero de la empresa, y que hay un 23% de clientes que están a punto de abandonarnos con más de 1.3 millones de pesos en juego. Al final montamos una aplicación web interactiva en Streamlit para que la empresa pueda filtrar clientes y tomar decisiones comerciales basadas en datos."</strong>
    </div>

</body>
</html>
"""

def compilar():
    HTML_TEMP.write_text(HTML_CONTENIDO, encoding="utf-8")
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=opts)
    try:
        url = HTML_TEMP.resolve().as_uri()
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

        print("Compilando PDF de explicación sencilla...")
        resultado = driver.execute_cdp_cmd("Page.printToPDF", print_params)
        pdf_bytes = base64.b64decode(resultado["data"])
        PDF_SALIDA.write_bytes(pdf_bytes)
        print(f"  [PDF generado con éxito] {PDF_SALIDA.name} ({len(pdf_bytes):,} bytes)")
    finally:
        driver.quit()
        if HTML_TEMP.exists():
            HTML_TEMP.unlink()

if __name__ == "__main__":
    compilar()
