"""
Generador de PDF profesional para el reporte del proyecto K-Means.
Transforma docs/reporte_base.md en un HTML estructurado y genera el PDF
utilizando Selenium y Chrome en modo headless con fidelidad de imprenta.
"""
import base64
import re
from pathlib import Path
from markdown_it import MarkdownIt
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
REPORTE_MD = DOCS_DIR / "reporte_base.md"
PDF_SALIDA = DOCS_DIR / "reporte_segmentacion_kmeans.pdf"
HTML_TEMP = DOCS_DIR / "reporte_impresion.html"
PORTADA_IMG = DOCS_DIR / "portada.png"


CSS_ESTILOS = """
@page {
    size: letter;
    margin: 18mm 16mm 18mm 16mm;
    @bottom-right {
        content: counter(page);
    }
}

@page :first {
    margin: 0;
    size: letter;
}

*, *:before, *:after {
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #24292e;
    line-height: 1.55;
    font-size: 10.5pt;
    margin: 0;
    padding: 0;
    background-color: #ffffff;
}

/* Portada de página completa */
.portada-wrapper {
    page-break-after: always;
    break-after: page;
    width: 100vw;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 0;
    padding: 0;
    background: #ffffff;
}

.portada-wrapper img {
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
}

/* Contenedor del contenido principal */
.contenido-reporte {
    padding: 0;
}

/* Encabezados */
h1 {
    font-size: 19pt;
    font-weight: 700;
    color: #1a365d;
    border-bottom: 2.5px solid #2b6cb0;
    padding-bottom: 6px;
    margin-top: 24px;
    margin-bottom: 14px;
    page-break-before: always;
    break-before: page;
}

/* Evitar salto de página en el primer encabezado tras la portada */
.contenido-reporte > h1:first-of-type {
    page-break-before: avoid;
    break-before: avoid;
    margin-top: 0;
}

h2 {
    font-size: 14pt;
    font-weight: 600;
    color: #2c5282;
    margin-top: 20px;
    margin-bottom: 10px;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 4px;
    page-break-after: avoid;
    break-after: avoid;
}

h3 {
    font-size: 12pt;
    font-weight: 600;
    color: #2d3748;
    margin-top: 16px;
    margin-bottom: 8px;
    page-break-after: avoid;
    break-after: avoid;
}

p {
    margin-top: 0;
    margin-bottom: 10px;
    text-align: justify;
}

ul, ol {
    margin-top: 0;
    margin-bottom: 12px;
    padding-left: 24px;
}

li {
    margin-bottom: 4px;
}

strong {
    color: #1a202c;
    font-weight: 600;
}

/* Tablas profesionales */
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 12px;
    margin-bottom: 16px;
    font-size: 9pt;
    page-break-inside: avoid;
    break-inside: avoid;
}

th, td {
    padding: 7px 10px;
    border: 1px solid #cbd5e0;
    text-align: left;
}

th {
    background-color: #2b6cb0;
    color: #ffffff;
    font-weight: 600;
    letter-spacing: 0.3px;
    text-align: center;
}

tbody tr:nth-child(even) {
    background-color: #f7fafc;
}

tbody tr:hover {
    background-color: #edf2f7;
}

/* Figuras e imágenes */
p:has(img), .figura-container {
    text-align: center;
    margin-top: 12px;
    margin-bottom: 14px;
    page-break-inside: avoid;
    break-inside: avoid;
}

img {
    max-width: 95%;
    max-height: 460px;
    width: auto;
    height: auto;
    object-fit: contain;
    display: block;
    margin: 8px auto;
    border-radius: 4px;
    border: 1px solid #cbd5e0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* Cajas de notas y códigos */
blockquote {
    border-left: 4px solid #3182ce;
    background-color: #ebf8ff;
    color: #2b6cb0;
    padding: 10px 14px;
    margin: 12px 0;
    border-radius: 0 4px 4px 0;
}

code {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
    font-size: 9pt;
    background-color: #edf2f7;
    color: #c53030;
    padding: 2px 5px;
    border-radius: 3px;
}

pre {
    background-color: #2d3748;
    color: #f7fafc;
    padding: 12px;
    border-radius: 5px;
    overflow-x: auto;
    font-size: 8.5pt;
    page-break-inside: avoid;
    break-inside: avoid;
}

pre code {
    background-color: transparent;
    color: inherit;
    padding: 0;
}

hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 22px 0;
}
"""


def markdown_a_html():
    texto_md = REPORTE_MD.read_text(encoding="utf-8")

    # Separar la sección 1 (Portada) del resto
    # En el reporte, la portada es la sección 1. La reemplazamos por el contenedor de imagen full-page
    partes = re.split(r"(?m)^# 1\. Portada\s*", texto_md, maxsplit=1)
    if len(partes) > 1:
        resto = partes[1]
        # Cortar hasta "# 2. Introducción"
        subpartes = re.split(r"(?m)^(?=# 2\. Introducción)", resto, maxsplit=1)
        cuerpo_md = subpartes[1] if len(subpartes) > 1 else resto
    else:
        cuerpo_md = texto_md

    # Renderizar el cuerpo con markdown_it
    md = MarkdownIt().enable("table")
    cuerpo_html = md.render(cuerpo_md)

    # Ajustar rutas de imágenes relativas para que apunten al archivo local
    def corregir_ruta_img(match):
        src = match.group(1)
        # Si es ruta relativa como ../outputs/figures/ o portada.png
        if src.startswith("../"):
            ruta_absoluta = (DOCS_DIR / src).resolve().as_uri()
        elif not src.startswith("http") and not src.startswith("file:"):
            ruta_absoluta = (DOCS_DIR / src).resolve().as_uri()
        else:
            ruta_absoluta = src
        return f'src="{ruta_absoluta}"'

    cuerpo_html = re.sub(r'src=["\']([^"\']+)["\']', corregir_ruta_img, cuerpo_html)

    # Ruta absoluta de la portada
    portada_uri = PORTADA_IMG.resolve().as_uri()

    html_completo = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte de Evaluación - Tercer Unidad (K-Means)</title>
    <style>
        {CSS_ESTILOS}
    </style>
</head>
<body>
    <div class="portada-wrapper">
        <img src="{portada_uri}" alt="Portada Oficial UTSLRC IDGS">
    </div>
    <div class="contenido-reporte">
        {cuerpo_html}
    </div>
</body>
</html>
"""
    HTML_TEMP.write_text(html_completo, encoding="utf-8")
    print(f"HTML intermedio generado en {HTML_TEMP.name}")
    return HTML_TEMP


def compilar_pdf_con_selenium(html_path: Path, pdf_salida: Path):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=opts)
    try:
        url = html_path.resolve().as_uri()
        print(f"Cargando HTML en Chrome headless: {url}...")
        driver.get(url)

        # Configuración de impresión CDP (Page.printToPDF)
        print_params = {
            "landscape": False,
            "displayHeaderFooter": False,
            "printBackground": True,
            "preferCSSPageSize": True,
            "marginTop": 0.5,
            "marginBottom": 0.5,
            "marginLeft": 0.5,
            "marginRight": 0.5,
        }

        print("Generando PDF mediante Chrome DevTools Protocol...")
        resultado = driver.execute_cdp_cmd("Page.printToPDF", print_params)
        pdf_bytes = base64.b64decode(resultado["data"])
        pdf_salida.write_bytes(pdf_bytes)
        print(f"  [PDF generado exitosamente] {pdf_salida.name} ({len(pdf_bytes):,} bytes)")

        # Guardar también una copia como reporte_proyecto.pdf
        copia_pdf = DOCS_DIR / "reporte_proyecto.pdf"
        copia_pdf.write_bytes(pdf_bytes)
        print(f"  [Copia guardada] {copia_pdf.name}")

    finally:
        driver.quit()


if __name__ == "__main__":
    html_file = markdown_a_html()
    compilar_pdf_con_selenium(html_file, PDF_SALIDA)
    print("Proceso de generación de PDF terminado.")
