"""
Generador del dataset sintético de clientes.

Crea `data/raw/clientes_segmentacion.csv` con 900 clientes (+15 duplicados)
y 10 variables. Los datos se construyen a partir de cuatro perfiles de
comportamiento de compra "ocultos" (el modelo nunca ve esa etiqueta) y se
ensucian a propósito con:

* valores nulos en varias columnas,
* filas duplicadas,
* inconsistencias de texto (mayúsculas, acentos, espacios, abreviaturas),
* montos guardados como texto con símbolo "$" y comas,
* valores imposibles (edades de 150 años, recencias negativas, frecuencia 0),
* atípicos leves y extremos en el gasto.

Así la etapa de limpieza del pipeline trabaja sobre problemas reales.

Uso:
    python src/generar_dataset.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import config  # noqa: E402

# Perfiles base (proporción y parámetros de cada grupo latente)
PERFILES = {
    "alto_valor": {
        "proporcion": 0.12,
        "frecuencia": (32, 5, 15, 60),       # media, desv, mínimo, máximo
        "ticket": (1400, 250, 700, 2600),
        "recencia": ("exp", 8, 1, 45),        # exponencial: escala, mín, máx
        "edad": (42, 8),
        "antiguedad": (60, 18),
        "satisfaccion": [0.02, 0.03, 0.10, 0.35, 0.50],
        "canal": [0.30, 0.50, 0.20],          # Online, App móvil, Tienda física
    },
    "regular": {
        "proporcion": 0.30,
        "frecuencia": (16, 4, 6, 30),
        "ticket": (750, 150, 350, 1300),
        "recencia": ("exp", 22, 2, 90),
        "edad": (38, 10),
        "antiguedad": (36, 15),
        "satisfaccion": [0.03, 0.07, 0.25, 0.40, 0.25],
        "canal": [0.40, 0.30, 0.30],
    },
    "ocasional": {
        "proporcion": 0.33,
        "frecuencia": (5, 2, 1, 12),
        "ticket": (450, 120, 150, 900),
        "recencia": ("normal", 75, 25, 20, 160),  # media, desv, mín, máx
        "edad": (30, 9),
        "antiguedad": (14, 8),
        "satisfaccion": [0.08, 0.15, 0.37, 0.28, 0.12],
        "canal": [0.25, 0.20, 0.55],
    },
    "inactivo": {
        "proporcion": 0.25,
        "frecuencia": (8, 3, 1, 18),
        "ticket": (800, 200, 300, 1500),
        "recencia": ("normal", 230, 50, 130, 365),
        "edad": (45, 12),
        "antiguedad": (40, 20),
        "satisfaccion": [0.20, 0.30, 0.30, 0.15, 0.05],
        "canal": [0.35, 0.15, 0.50],
    },
}

CANALES = ["Online", "App móvil", "Tienda física"]
REGIONES = ["Norte", "Centro", "Sur", "Occidente"]
GENEROS = ["Masculino", "Femenino"]


def _normal_recortada(media, desv, minimo, maximo, n):
    return np.clip(np.random.normal(media, desv, n), minimo, maximo)


def _generar_perfil(nombre: str, params: dict, n: int) -> pd.DataFrame:
    frecuencia = np.round(_normal_recortada(*params["frecuencia"], n)).astype(int)
    ticket = _normal_recortada(*params["ticket"], n)
    gasto = frecuencia * ticket * np.random.uniform(0.92, 1.08, n)

    tipo_rec = params["recencia"][0]
    if tipo_rec == "exp":
        _, escala, minimo, maximo = params["recencia"]
        recencia = np.clip(np.random.exponential(escala, n) + minimo, minimo, maximo)
    else:
        _, media, desv, minimo, maximo = params["recencia"]
        recencia = _normal_recortada(media, desv, minimo, maximo, n)

    edad = np.round(_normal_recortada(*params["edad"], 18, 80, n)).astype(int)
    antiguedad = np.round(_normal_recortada(*params["antiguedad"], 1, 120, n)).astype(int)

    return pd.DataFrame(
        {
            "edad": edad,
            "genero": np.random.choice(GENEROS, n, p=[0.48, 0.52]),
            "region": np.random.choice(REGIONES, n, p=[0.25, 0.35, 0.20, 0.20]),
            "canal_preferido": np.random.choice(CANALES, n, p=params["canal"]),
            "antiguedad_meses": antiguedad,
            "frecuencia_compras": frecuencia,
            "gasto_total": np.round(gasto, 2),
            "recencia_dias": np.round(recencia).astype(int),
            "satisfaccion": np.random.choice([1, 2, 3, 4, 5], n, p=params["satisfaccion"]),
            "_perfil_real": nombre,  # solo para construir datos; se elimina antes de guardar
        }
    )


def _ensuciar(df: pd.DataFrame) -> pd.DataFrame:
    """Introduce nulos, inconsistencias, errores y atípicos de forma controlada."""
    df = df.copy()
    n = len(df)
    df["gasto_total"] = df["gasto_total"].astype(object)
    df["edad"] = df["edad"].astype(float)
    df["recencia_dias"] = df["recencia_dias"].astype(float)
    df["frecuencia_compras"] = df["frecuencia_compras"].astype(float)
    df["satisfaccion"] = df["satisfaccion"].astype(float)

    def idx(k):
        return np.random.choice(n, k, replace=False)

    # 1) Valores nulos
    df.loc[idx(25), "edad"] = np.nan
    df.loc[idx(18), "gasto_total"] = np.nan
    df.loc[idx(10), "recencia_dias"] = np.nan
    df.loc[idx(15), "canal_preferido"] = np.nan
    df.loc[idx(20), "satisfaccion"] = np.nan
    df.loc[idx(8), "region"] = np.nan

    # 2) Inconsistencias de texto en categorías
    variantes_canal = {
        "Online": ["online", "ONLINE", " Online "],
        "App móvil": ["App movil", "app móvil", "APP MOVIL"],
        "Tienda física": ["Tienda Fisica", "tienda física", "TIENDA FISICA "],
    }
    for i in idx(60):
        valor = df.at[i, "canal_preferido"]
        if isinstance(valor, str):
            df.at[i, "canal_preferido"] = np.random.choice(variantes_canal[valor])

    variantes_genero = {"Masculino": ["M", "masculino", "MASCULINO "], "Femenino": ["F", "femenino", " FEMENINO"]}
    for i in idx(50):
        df.at[i, "genero"] = np.random.choice(variantes_genero[df.at[i, "genero"]])

    for i in idx(30):
        valor = df.at[i, "region"]
        if isinstance(valor, str):
            df.at[i, "region"] = np.random.choice([valor.upper(), valor.lower(), f" {valor}"])

    # 3) Valores imposibles / errores de captura
    df.loc[idx(4), "edad"] = 150
    df.loc[idx(3), "edad"] = 2
    df.loc[idx(3), "recencia_dias"] = -7
    df.loc[idx(3), "frecuencia_compras"] = 0

    # 4) Atípicos en gasto (algunos leves, algunos extremos por error de captura)
    numericos = df["gasto_total"].dropna().index.to_numpy()
    for i in np.random.choice(numericos, 6, replace=False):
        df.at[i, "gasto_total"] = round(float(df.at[i, "gasto_total"]) * np.random.uniform(3.0, 4.5), 2)

    # 5) Montos guardados como texto ("$12,345.50")
    numericos = df["gasto_total"].dropna().index.to_numpy()
    for i in np.random.choice(numericos, 12, replace=False):
        df.at[i, "gasto_total"] = f"${float(df.at[i, 'gasto_total']):,.2f}"

    return df


def generar_dataset(ruta_salida: Path = config.DATA_RAW) -> pd.DataFrame:
    """Genera el dataset crudo, lo guarda en CSV y lo devuelve."""
    np.random.seed(42)  # semilla fija para reproducibilidad
    config.asegurar_directorios()

    tamanos = {k: int(round(v["proporcion"] * config.N_CLIENTES)) for k, v in PERFILES.items()}
    ajuste = config.N_CLIENTES - sum(tamanos.values())
    tamanos["ocasional"] += ajuste

    partes = [_generar_perfil(nombre, PERFILES[nombre], n) for nombre, n in tamanos.items()]
    df = pd.concat(partes, ignore_index=True)
    df = df.sample(frac=1, random_state=config.SEED).reset_index(drop=True)
    df.insert(0, "id_cliente", [f"CLI-{i:04d}" for i in range(1, len(df) + 1)])

    df = _ensuciar(df)
    df = df.drop(columns="_perfil_real")

    # 6) Duplicados exactos
    duplicados = df.sample(config.N_DUPLICADOS, random_state=config.SEED)
    df = pd.concat([df, duplicados], ignore_index=True)
    df = df.sample(frac=1, random_state=7).reset_index(drop=True)

    df.to_csv(ruta_salida, index=False, encoding="utf-8")
    return df


if __name__ == "__main__":
    datos = generar_dataset()
    print(f"Dataset generado en: {config.DATA_RAW}")
    print(f"Registros: {datos.shape[0]} | Variables: {datos.shape[1]}")
    print(f"Nulos totales: {int(datos.isna().sum().sum())} | Duplicados: {int(datos.duplicated().sum())}")
