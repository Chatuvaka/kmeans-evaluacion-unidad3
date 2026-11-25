"""
Script para capturar pantallas reales del dashboard Streamlit y de la consola.
Genera las 8 capturas requeridas por el reporte y las guarda en outputs/figures/.
"""
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "outputs" / "figures"
CONSOLE_LOG = ROOT / "outputs" / "salida_pipeline.txt"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def renderizar_texto_terminal(titulo_ventana: str, lineas: list[str], ruta_salida: Path, ancho: int = 1100) -> None:
    """Renderiza un fragmento de texto como una ventana de consola moderna y profesional."""
    try:
        font = ImageFont.truetype("consola.ttf", 15)
    except IOError:
        font = ImageFont.load_default()

    line_height = 22
    padding = 24
    header_height = 42
    alto = header_height + padding * 2 + len(lineas) * line_height

    img = Image.new("RGB", (ancho, alto), color="#1e1e1e")
    draw = ImageDraw.Draw(img)

    # Barra de título de la ventana
    draw.rectangle([0, 0, ancho, header_height], fill="#2d2d2d")
    # Botones estilo terminal
    draw.ellipse([14, 15, 26, 27], fill="#ff5f56")
    draw.ellipse([34, 15, 46, 27], fill="#ffbd2e")
    draw.ellipse([54, 15, 66, 27], fill="#27c93f")
    # Título
    draw.text((80, 13), titulo_ventana, fill="#cccccc", font=font)

    # Contenido de texto
    y = header_height + padding
    for linea in lineas:
        color = "#e6e6e6"
        if linea.startswith("===") or linea.startswith("---"):
            color = "#61afef"
        elif "CLI-" in linea or "K =" in linea or "K OPTIMO" in linea:
            color = "#98c379"
        elif "Observacion" in linea or "nulos" in linea:
            color = "#e5c07b"
        draw.text((padding, y), linea, fill=color, font=font)
        y += line_height

    img.save(ruta_salida, dpi=(150, 150))
    print(f"  [captura generada] {ruta_salida.name}")


def generar_capturas_consola():
    """Genera Captura 1 y Captura 2 a partir de salida_pipeline.txt."""
    if not CONSOLE_LOG.exists():
        print("No se encontro salida_pipeline.txt")
        return

    texto = CONSOLE_LOG.read_text(encoding="utf-8")
    lineas = texto.splitlines()

    # Captura 1: Primeros 10 registros, shape, dtypes, nulos
    c1_lineas = []
    guardando = False
    for l in lineas:
        if "1. EXPLORACIÓN DE DATOS" in l:
            guardando = True
        if "--- Duplicados ---" in l:
            c1_lineas.append(l)
            break
        if guardando:
            c1_lineas.append(l)

    # Limitar para que sea legible
    c1_clean = [l for l in c1_lineas if not l.startswith("  [figura guardada]")]
    renderizar_texto_terminal(
        "Consola - Exploración del dataset crudo (shape, head, dtypes, nulos)",
        c1_clean[:45],
        FIG_DIR / "captura_01_consola_exploracion.png",
        ancho=1150
    )

    # Captura 2: Centroides y métricas del modelo final K=4
    c2_lineas = []
    guardando_c2 = False
    for l in lineas:
        if "5. MODELO FINAL K-MEANS" in l:
            guardando_c2 = True
        if "6. GRÁFICAS DE AGRUPAMIENTOS" in l:
            break
        if guardando_c2:
            c2_lineas.append(l)

    c2_clean = [l for l in c2_lineas if not l.startswith("  [figura guardada]")]
    renderizar_texto_terminal(
        "Consola - Modelo final K-Means (Centroides escalados, originales y métricas)",
        c2_clean[:42],
        FIG_DIR / "captura_02_consola_centroides.png",
        ancho=1150
    )


def capturar_dashboard():
    """Captura las pantallas reales del dashboard Streamlit mediante Selenium."""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1600,1100")
    opts.add_argument("--force-device-scale-factor=1")

    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, 15)

    try:
        url = "http://localhost:8501"
        print(f"Navegando a {url}...")
        driver.get(url)

        # Esperar a que cargue Streamlit (las métricas o el sidebar)
        time.sleep(5)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stMetric']")))

        def scroll_to(y: int):
            driver.execute_script(f"""
                const el = document.getElementById('stMain') || document.querySelector('.stMain') || document.querySelector('section.main');
                if (el) el.scrollTop = {y};
            """)
            time.sleep(2)

        # --- CAPTURA 3: Página 1 - Encabezado, filtros y 4 KPI ---
        scroll_to(0)
        time.sleep(2)
        driver.save_screenshot(str(FIG_DIR / "captura_03_pagina1_kpi.png"))
        print("  [captura generada] captura_03_pagina1_kpi.png")

        # --- CAPTURA 4: Página 1 - Gráficas de distribución y estadísticas descriptivas ---
        scroll_to(650)
        time.sleep(2)
        driver.save_screenshot(str(FIG_DIR / "captura_04_pagina1_graficas.png"))
        print("  [captura generada] captura_04_pagina1_graficas.png")

        # --- CAPTURA 5: Página 2 - K-Means: KPI, distribución y dispersión 2D ---
        # Seleccionar Página 2 en el radio button del sidebar
        radios = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stRadio'] label")
        p2_radio = None
        for r in radios:
            if "Página 2" in r.text or "Segmentación K-Means" in r.text:
                p2_radio = r
                break
        if p2_radio:
            p2_radio.click()
            time.sleep(4)
        else:
            inputs = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stRadio'] input")
            if len(inputs) >= 2:
                driver.execute_script("arguments[0].click();", inputs[1])
                time.sleep(4)

        scroll_to(0)
        time.sleep(2)
        driver.save_screenshot(str(FIG_DIR / "captura_05_pagina2_kpi_dispersion.png"))
        print("  [captura generada] captura_05_pagina2_kpi_dispersion.png")

        # --- CAPTURA 6: Página 2 - Comparativas y estadísticas por clúster ---
        scroll_to(800)
        time.sleep(2)
        driver.save_screenshot(str(FIG_DIR / "captura_06_pagina2_comparativas.png"))
        print("  [captura generada] captura_06_pagina2_comparativas.png")

        # --- CAPTURA 7: Página 2 - Descripción de grupos, hallazgos y recomendaciones ---
        scroll_to(1800)
        time.sleep(2)
        driver.save_screenshot(str(FIG_DIR / "captura_07_pagina2_descripcion_hallazgos.png"))
        print("  [captura generada] captura_07_pagina2_descripcion_hallazgos.png")

        # --- CAPTURA 8: Dashboard con filtros interactivos aplicados ---
        scroll_to(0)
        time.sleep(1)
        try:
            multis = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stSidebar'] [data-testid='stMultiSelect']")
            if len(multis) >= 2:
                m1 = multis[1]  # Canal preferido
                icons = m1.find_elements(By.CSS_SELECTOR, "svg")
                if len(icons) >= 2:
                    driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", icons[0])
                    time.sleep(2)
                    # Volver a buscar tras re-renderizado
                    m1 = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stSidebar'] [data-testid='stMultiSelect']")[1]
                    icons = m1.find_elements(By.CSS_SELECTOR, "svg")
                    if len(icons) >= 2:
                        driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", icons[0])
                        time.sleep(2)
        except Exception as e:
            print(f"Aviso al interactuar con filtro: {e}")

        scroll_to(0)
        time.sleep(3)
        driver.save_screenshot(str(FIG_DIR / "captura_08_dashboard_filtros_aplicados.png"))
        print("  [captura generada] captura_08_dashboard_filtros_aplicados.png")

    finally:
        driver.quit()


if __name__ == "__main__":
    print("Iniciando generación de capturas...")
    generar_capturas_consola()
    capturar_dashboard()
    print("Capturas completadas con exito.")
