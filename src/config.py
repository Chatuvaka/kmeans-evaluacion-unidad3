"""
Configuración central del proyecto: rutas, semilla y parámetros del modelo.

Todos los scripts importan desde aquí para que las rutas sean consistentes
sin importar desde qué carpeta se ejecuten.
"""
from pathlib import Path

# --- Rutas -----------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

DATA_RAW = RAW_DIR / "clientes_segmentacion.csv"
DATA_PROCESSED = PROCESSED_DIR / "clientes_segmentados.csv"
DATA_ENCODED = PROCESSED_DIR / "clientes_limpios_codificados.csv"

OUTPUTS_DIR = ROOT / "outputs"
FIG_DIR = OUTPUTS_DIR / "figures"
TABLE_DIR = OUTPUTS_DIR / "tables"
RESULTS_JSON = OUTPUTS_DIR / "resultados_modelo.json"
CONSOLE_LOG = OUTPUTS_DIR / "salida_pipeline.txt"

# --- Parámetros generales --------------------------------------------------
SEED = 42
N_CLIENTES = 900          # registros base (antes de inyectar duplicados)
N_DUPLICADOS = 15         # filas duplicadas inyectadas a propósito

# Variables numéricas usadas para agrupar (modelo RFM)
VARIABLES_CLUSTER = ["frecuencia_compras", "gasto_total", "recencia_dias"]

# Variables numéricas y categóricas del dataset limpio
VARIABLES_NUMERICAS = [
    "edad",
    "antiguedad_meses",
    "frecuencia_compras",
    "gasto_total",
    "recencia_dias",
    "satisfaccion",
    "ticket_promedio",
]
VARIABLES_CATEGORICAS = ["genero", "region", "canal_preferido"]

# Valores de K a evaluar (mínimo 5 valores)
K_RANGE = list(range(2, 9))

# Factor del rango intercuartílico para tratar atípicos extremos
IQR_FACTOR_DETECCION = 1.5
IQR_FACTOR_TRATAMIENTO = 3.0

# Etiquetas legibles para gráficas y tablas
ETIQUETAS = {
    "frecuencia_compras": "Frecuencia (compras/año)",
    "gasto_total": "Gasto total anual (MXN)",
    "recencia_dias": "Recencia (días desde última compra)",
    "ticket_promedio": "Ticket promedio (MXN)",
    "edad": "Edad (años)",
    "antiguedad_meses": "Antigüedad (meses)",
    "satisfaccion": "Satisfacción (1-5)",
}


def asegurar_directorios() -> None:
    """Crea las carpetas de datos y salidas si no existen."""
    for carpeta in (RAW_DIR, PROCESSED_DIR, FIG_DIR, TABLE_DIR):
        carpeta.mkdir(parents=True, exist_ok=True)
