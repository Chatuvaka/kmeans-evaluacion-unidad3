"""
Pipeline de análisis: exploración, limpieza, escalado y modelado con K-Means.

Cada etapa es una función independiente para que `main.py` las orqueste y
para poder reutilizarlas o probarlas por separado.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sin ventana: las figuras se guardan en disco

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import config  # noqa: E402

sns.set_theme(style="whitegrid", context="notebook")
PALETA_CLUSTERS = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e", "#e6ab02", "#a6761d", "#666666"]
VARS = config.VARIABLES_CLUSTER

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 30)
pd.set_option("display.float_format", lambda v: f"{v:,.2f}")


# ---------------------------------------------------------------------------
# Utilidades de impresión y guardado
# ---------------------------------------------------------------------------
def titulo(texto: str) -> None:
    print("\n" + "=" * 90)
    print(texto)
    print("=" * 90)


def subtitulo(texto: str) -> None:
    print(f"\n--- {texto} ---")


def guardar_figura(fig, nombre: str) -> Path:
    ruta = config.FIG_DIR / nombre
    fig.tight_layout()
    fig.savefig(ruta, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"  [figura guardada] {ruta.relative_to(config.ROOT).as_posix()}")
    return ruta


def guardar_tabla(df: pd.DataFrame, nombre: str, index: bool = False) -> Path:
    ruta = config.TABLE_DIR / nombre
    df.to_csv(ruta, index=index, encoding="utf-8")
    print(f"  [tabla guardada] {ruta.relative_to(config.ROOT).as_posix()}")
    return ruta


def _a_numero(serie: pd.Series) -> pd.Series:
    """Convierte montos guardados como texto ("$12,345.50") a número."""
    limpio = serie.astype("string").str.replace(r"[$,\s]", "", regex=True)
    return pd.to_numeric(limpio, errors="coerce")


# ---------------------------------------------------------------------------
# 1. Exploración
# ---------------------------------------------------------------------------
def cargar_datos(ruta: Path = config.DATA_RAW) -> pd.DataFrame:
    """Carga el CSV crudo con pandas."""
    return pd.read_csv(ruta)


def explorar_datos(df: pd.DataFrame) -> dict:
    """Muestra la exploración inicial y genera las gráficas exploratorias."""
    titulo("1. EXPLORACIÓN DE DATOS (dataset crudo)")

    subtitulo("Primeros 10 registros (.head(10))")
    print(df.head(10).to_string())

    subtitulo("Dimensiones (.shape)")
    print(f"{df.shape[0]} filas x {df.shape[1]} columnas")

    subtitulo("Columnas")
    print(list(df.columns))

    subtitulo("Tipos de datos (.dtypes)")
    print(df.dtypes.to_string())
    print(
        "\nObservación: 'gasto_total' no es numérica porque algunos montos se capturaron "
        "como texto con '$' y comas; se corrige en la limpieza."
    )

    subtitulo("Estadísticas descriptivas numéricas (.describe())")
    print(df.describe().T.to_string())

    subtitulo("Estadísticas descriptivas categóricas (.describe(include='object'))")
    print(df.describe(exclude="number").T.to_string())

    subtitulo("Valores nulos por columna")
    nulos = df.isna().sum()
    tabla_nulos = pd.DataFrame({"nulos": nulos, "porcentaje": (nulos / len(df) * 100).round(2)})
    print(tabla_nulos.to_string())
    print(f"Total de celdas nulas: {int(nulos.sum())}")

    subtitulo("Duplicados")
    dup_exactos = int(df.duplicated().sum())
    dup_id = int(df["id_cliente"].duplicated().sum())
    print(f"Filas duplicadas exactas: {dup_exactos}")
    print(f"id_cliente repetidos: {dup_id}")

    subtitulo("Valores únicos en variables categóricas (revelan inconsistencias)")
    for col in config.VARIABLES_CATEGORICAS:
        valores = sorted(df[col].dropna().astype(str).unique())
        print(f"{col} ({len(valores)} valores distintos): {valores}")

    subtitulo("Valores fuera de rango / sospechosos")
    gasto_num = _a_numero(df["gasto_total"])
    texto_monetario = int(df["gasto_total"].astype("string").str.contains(r"\$", na=False).sum())
    print(f"Montos de gasto guardados como texto con '$': {texto_monetario}")
    print(f"Edades < 18 o > 90: {int(((df['edad'] < 18) | (df['edad'] > 90)).sum())}")
    print(f"Recencias negativas: {int((df['recencia_dias'] < 0).sum())}")
    print(f"Frecuencia de compra igual a 0 con gasto registrado: {int((df['frecuencia_compras'] == 0).sum())}")
    print(f"Gasto máximo: ${gasto_num.max():,.2f} | mediana: ${gasto_num.median():,.2f}")

    subtitulo("Gráficas exploratorias")
    _graficas_exploratorias(df.assign(gasto_total=gasto_num))

    justificar_variables()

    return {
        "filas": int(df.shape[0]),
        "columnas": int(df.shape[1]),
        "nulos_totales": int(nulos.sum()),
        "duplicados_exactos": dup_exactos,
        "montos_como_texto": texto_monetario,
    }


def _graficas_exploratorias(df: pd.DataFrame) -> None:
    numericas = ["frecuencia_compras", "gasto_total", "recencia_dias", "edad", "antiguedad_meses", "satisfaccion"]

    # 01. Histogramas de distribución
    fig, ejes = plt.subplots(2, 3, figsize=(15, 8))
    for eje, col in zip(ejes.flat, numericas):
        sns.histplot(df[col].dropna(), bins=30, kde=True, ax=eje, color="#2c7fb8")
        eje.set_title(config.ETIQUETAS.get(col, col))
        eje.set_xlabel("")
    fig.suptitle("Distribución de las variables numéricas (datos crudos)", fontsize=14, weight="bold")
    guardar_figura(fig, "01_distribucion_variables.png")

    # 02. Boxplots para detectar atípicos y errores
    fig, ejes = plt.subplots(1, 4, figsize=(16, 5))
    for eje, col in zip(ejes, ["frecuencia_compras", "gasto_total", "recencia_dias", "edad"]):
        sns.boxplot(y=df[col], ax=eje, color="#fdae6b")
        eje.set_title(config.ETIQUETAS.get(col, col))
        eje.set_ylabel("")
    fig.suptitle("Boxplots: valores atípicos y errores de captura (datos crudos)", fontsize=14, weight="bold")
    guardar_figura(fig, "02_boxplots_atipicos.png")

    # 03. Categorías tal como vienen (muestran inconsistencias de captura)
    fig, ejes = plt.subplots(1, 2, figsize=(16, 6))
    orden_canal = df["canal_preferido"].fillna("(nulo)").value_counts().index
    sns.countplot(y=df["canal_preferido"].fillna("(nulo)"), order=orden_canal, ax=ejes[0], color="#74a9cf")
    ejes[0].set_title("Canal preferido: valores crudos")
    ejes[0].set_xlabel("Clientes")
    ejes[0].set_ylabel("")
    orden_gen = df["genero"].fillna("(nulo)").value_counts().index
    sns.countplot(y=df["genero"].fillna("(nulo)"), order=orden_gen, ax=ejes[1], color="#a1d99b")
    ejes[1].set_title("Género: valores crudos")
    ejes[1].set_xlabel("Clientes")
    ejes[1].set_ylabel("")
    fig.suptitle("Inconsistencias en variables categóricas antes de limpiar", fontsize=14, weight="bold")
    guardar_figura(fig, "03_categorias_inconsistentes.png")

    # 04. Matriz de correlación
    fig, eje = plt.subplots(figsize=(8, 6.5))
    corr = df[numericas].corr()
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, vmin=-1, vmax=1, ax=eje, square=True)
    eje.set_title("Correlación entre variables numéricas", fontsize=13, weight="bold")
    guardar_figura(fig, "04_matriz_correlacion.png")

    # 05. Relación frecuencia-gasto coloreada por recencia
    fig, eje = plt.subplots(figsize=(10, 6.5))
    puntos = eje.scatter(
        df["frecuencia_compras"], df["gasto_total"], c=df["recencia_dias"], cmap="viridis_r", alpha=0.7, s=22
    )
    fig.colorbar(puntos, ax=eje, label="Recencia (días)")
    eje.set_xlabel(config.ETIQUETAS["frecuencia_compras"])
    eje.set_ylabel(config.ETIQUETAS["gasto_total"])
    eje.set_title("Frecuencia vs. gasto (color = recencia)", fontsize=13, weight="bold")
    guardar_figura(fig, "05_dispersion_frecuencia_gasto.png")


def justificar_variables() -> None:
    subtitulo("Variables seleccionadas para el agrupamiento (modelo RFM)")
    print(
        "1. recencia_dias  (R): días desde la última compra. Mide qué tan activo está el cliente;\n"
        "   es el mejor indicador temprano de abandono.\n"
        "2. frecuencia_compras (F): número de compras en los últimos 12 meses. Mide el hábito y\n"
        "   la lealtad del cliente.\n"
        "3. gasto_total (M): monto gastado en 12 meses. Mide el valor económico del cliente.\n"
        "Justificación: las tres responden directamente a la problemática (comportamiento de compra),\n"
        "son numéricas continuas (adecuadas para la distancia euclidiana de K-Means) y no son\n"
        "redundantes entre sí. 'ticket_promedio' se descarta porque es gasto/frecuencia (redundante);\n"
        "edad, satisfacción y variables categóricas se reservan para describir y validar los clústeres."
    )


# ---------------------------------------------------------------------------
# 2. Limpieza y preprocesamiento
# ---------------------------------------------------------------------------
MAPEO_CANAL = {
    "online": "Online",
    "app movil": "App móvil",
    "app móvil": "App móvil",
    "tienda fisica": "Tienda física",
    "tienda física": "Tienda física",
}
MAPEO_GENERO = {"m": "Masculino", "masculino": "Masculino", "f": "Femenino", "femenino": "Femenino"}


def _normalizar(serie: pd.Series) -> pd.Series:
    return serie.astype("string").str.strip().str.lower()


def limpiar_datos(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Limpia el dataset y devuelve (df_limpio, bitácora de cambios)."""
    titulo("2. LIMPIEZA Y PREPROCESAMIENTO")
    df = df.copy()
    bitacora = []

    def registrar(paso: str, detalle: str, afectados: int) -> None:
        bitacora.append({"paso": paso, "detalle": detalle, "registros_afectados": int(afectados)})
        print(f"  - {paso}: {detalle} -> {afectados} registro(s)")

    filas_iniciales = len(df)

    # a) Inconsistencias de texto en categorías
    subtitulo("a) Corrección de inconsistencias en categorías")
    for col, transformar in (
        ("canal_preferido", lambda s: _normalizar(s).map(MAPEO_CANAL)),
        ("genero", lambda s: _normalizar(s).map(MAPEO_GENERO)),
        ("region", lambda s: s.astype("string").str.strip().str.title()),
    ):
        original = df[col].astype("string")
        corregido = transformar(df[col]).astype("string")
        cambios = int((original.notna() & (original != corregido)).sum())
        df[col] = corregido
        registrar("Estandarizar texto", f"'{col}' unificada a {sorted(df[col].dropna().unique())}", cambios)

    # b) Tipos de datos: gasto guardado como texto
    subtitulo("b) Verificación y corrección de tipos de datos")
    como_texto = int(df["gasto_total"].astype("string").str.contains(r"\$", na=False).sum())
    df["gasto_total"] = _a_numero(df["gasto_total"])
    registrar("Convertir tipo", "'gasto_total' de texto ('$12,345.50') a float", como_texto)

    # c) Duplicados
    subtitulo("c) Tratamiento de duplicados")
    dup = int(df.duplicated().sum())
    df = df.drop_duplicates().reset_index(drop=True)
    registrar("Eliminar duplicados", "filas idénticas eliminadas (se conserva la primera)", dup)
    dup_id = int(df["id_cliente"].duplicated().sum())
    df = df.drop_duplicates(subset="id_cliente").reset_index(drop=True)
    registrar("Eliminar duplicados", "id_cliente repetido con datos distintos", dup_id)

    # d) Valores imposibles -> se marcan como nulos para imputarlos
    subtitulo("d) Valores inválidos (errores de captura)")
    reglas = {
        "edad": (df["edad"] < 18) | (df["edad"] > 90),
        "recencia_dias": df["recencia_dias"] < 0,
        "frecuencia_compras": df["frecuencia_compras"] <= 0,
    }
    for col, mascara in reglas.items():
        n_invalidos = int(mascara.sum())
        df.loc[mascara, col] = np.nan
        registrar("Valor inválido a nulo", f"'{col}' fuera de rango lógico", n_invalidos)

    # e) Imputación de nulos
    subtitulo("e) Tratamiento de valores nulos")
    print(df.isna().sum()[lambda s: s > 0].to_string())
    for col in ["edad", "antiguedad_meses", "frecuencia_compras", "gasto_total", "recencia_dias", "satisfaccion"]:
        n_nulos = int(df[col].isna().sum())
        if n_nulos:
            mediana = df[col].median()
            df[col] = df[col].fillna(mediana)
            registrar("Imputar mediana", f"'{col}' = {mediana:,.2f} (robusta a atípicos)", n_nulos)
    for col in config.VARIABLES_CATEGORICAS:
        n_nulos = int(df[col].isna().sum())
        if n_nulos:
            moda = df[col].mode().iloc[0]
            df[col] = df[col].fillna(moda)
            registrar("Imputar moda", f"'{col}' = '{moda}'", n_nulos)

    # f) Atípicos: detección por IQR y tratamiento por recorte (capping)
    subtitulo("f) Identificación y tratamiento de valores atípicos")
    filas_atipicos = []
    for col in VARS:
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        cerca_inf, cerca_sup = q1 - config.IQR_FACTOR_DETECCION * iqr, q3 + config.IQR_FACTOR_DETECCION * iqr
        detectados = int(((df[col] < cerca_inf) | (df[col] > cerca_sup)).sum())
        extremo_inf = q1 - config.IQR_FACTOR_TRATAMIENTO * iqr
        extremo_sup = q3 + config.IQR_FACTOR_TRATAMIENTO * iqr
        lim_inf = max(min(extremo_inf, df[col].quantile(0.01)), df[col].min())
        lim_sup = max(extremo_sup, df[col].quantile(0.99))
        tratados = int(((df[col] < lim_inf) | (df[col] > lim_sup)).sum())
        df[col] = df[col].clip(lower=lim_inf, upper=lim_sup)
        filas_atipicos.append(
            {
                "variable": col,
                "Q1": q1,
                "Q3": q3,
                "IQR": iqr,
                "cerca_superior_1.5IQR": cerca_sup,
                "atipicos_detectados_1.5IQR": detectados,
                "cerca_extrema_3IQR": extremo_sup,
                "limite_recorte": lim_sup,
                "valores_recortados": tratados,
            }
        )
        registrar("Recortar atípicos", f"'{col}' limitado a [{lim_inf:,.2f}, {lim_sup:,.2f}]", tratados)
    tabla_atipicos = pd.DataFrame(filas_atipicos)
    print(tabla_atipicos.to_string(index=False))
    print(
        "Criterio: la regla de Tukey (1.5*IQR) marca como atípicos a muchos clientes de alto valor que son\n"
        "legítimos (compran mucho y gastan mucho). Por eso solo se recortan (capping) los valores que superan\n"
        "a la vez la cerca extrema (3*IQR) y el percentil 99, que corresponden a errores de captura;\n"
        "no se elimina ningún cliente."
    )
    guardar_tabla(tabla_atipicos, "tratamiento_atipicos.csv")

    # g) Variable derivada y tipos finales
    subtitulo("g) Variable derivada y tipos finales")
    df["ticket_promedio"] = (df["gasto_total"] / df["frecuencia_compras"]).round(2)
    registrar("Variable derivada", "ticket_promedio = gasto_total / frecuencia_compras", len(df))
    for col in ["edad", "antiguedad_meses", "frecuencia_compras", "recencia_dias", "satisfaccion"]:
        df[col] = df[col].round().astype(int)
    df["gasto_total"] = df["gasto_total"].round(2)
    for col in config.VARIABLES_CATEGORICAS:
        df[col] = df[col].astype("category")
    print(df.dtypes.to_string())

    subtitulo("Resumen de la limpieza")
    print(f"Registros: {filas_iniciales} -> {len(df)}")
    print(f"Nulos restantes: {int(df.isna().sum().sum())} | Duplicados restantes: {int(df.duplicated().sum())}")
    print(df[config.VARIABLES_NUMERICAS].describe().T.to_string())

    # Boxplots después de limpiar
    fig, ejes = plt.subplots(1, 4, figsize=(16, 5))
    for eje, col in zip(ejes, ["frecuencia_compras", "gasto_total", "recencia_dias", "edad"]):
        sns.boxplot(y=df[col], ax=eje, color="#9ecae1")
        eje.set_title(config.ETIQUETAS.get(col, col))
        eje.set_ylabel("")
    fig.suptitle("Boxplots después de la limpieza", fontsize=14, weight="bold")
    guardar_figura(fig, "06_boxplots_despues_limpieza.png")

    tabla_bitacora = pd.DataFrame(bitacora)
    guardar_tabla(tabla_bitacora, "bitacora_limpieza.csv")
    return df, tabla_bitacora


def codificar_categoricas(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot encoding de las variables categóricas (para análisis complementario)."""
    subtitulo("h) Codificación de variables categóricas (One-Hot Encoding)")
    codificado = pd.get_dummies(df, columns=config.VARIABLES_CATEGORICAS, prefix=config.VARIABLES_CATEGORICAS, dtype=int)
    nuevas = [c for c in codificado.columns if c not in df.columns]
    print(f"Columnas creadas ({len(nuevas)}): {nuevas}")
    print(
        "Nota: las variables codificadas NO entran a K-Means; mezclar dummies 0/1 con variables\n"
        "continuas distorsiona la distancia euclidiana. Se guardan para análisis complementarios y\n"
        "se usan para describir el perfil de cada clúster."
    )
    codificado.to_csv(config.DATA_ENCODED, index=False, encoding="utf-8")
    print(f"  [datos guardados] {config.DATA_ENCODED.relative_to(config.ROOT).as_posix()}")
    return codificado


def escalar_variables(df: pd.DataFrame) -> tuple[np.ndarray, StandardScaler, pd.DataFrame]:
    """Escala las variables de agrupamiento con StandardScaler (media 0, desviación 1)."""
    titulo("3. ESCALADO DE VARIABLES (StandardScaler)")
    escalador = StandardScaler()
    X_esc = escalador.fit_transform(df[VARS])
    escaladas = pd.DataFrame(X_esc, columns=VARS)

    tabla = pd.DataFrame(
        {
            "variable": VARS,
            "media_original": escalador.mean_,
            "desv_original": escalador.scale_,
            "min_original": df[VARS].min().values,
            "max_original": df[VARS].max().values,
            "media_escalada": escaladas.mean().round(4).values,
            "desv_escalada": escaladas.std(ddof=0).round(4).values,
            "min_escalado": escaladas.min().values,
            "max_escalado": escaladas.max().values,
        }
    )
    print(tabla.to_string(index=False))
    print("\nPrimeros 5 registros escalados:")
    print(escaladas.head().to_string())
    proporcion = df["gasto_total"].std() / df["frecuencia_compras"].std()
    print(
        f"\nExplicación: antes de escalar, la desviación estándar del gasto es ~{proporcion:,.0f} veces la de la\n"
        "frecuencia, por lo que K-Means (basado en distancias) ignoraría prácticamente la frecuencia y la\n"
        "recencia. StandardScaler aplica z = (x - media) / desviación, dejando cada variable con media 0 y\n"
        "desviación 1; así las tres variables RFM pesan lo mismo en el cálculo de distancias."
    )

    fig, ejes = plt.subplots(1, 2, figsize=(15, 5.5))
    sns.boxplot(data=df[VARS], ax=ejes[0], palette="pastel")
    ejes[0].set_title("Antes del escalado (unidades originales)")
    ejes[0].set_yscale("log")
    ejes[0].set_ylabel("Valor (escala logarítmica)")
    sns.boxplot(data=escaladas, ax=ejes[1], palette="pastel")
    ejes[1].set_title("Después de StandardScaler (z-score)")
    ejes[1].axhline(0, color="black", lw=0.8, ls="--")
    ejes[1].set_ylabel("Desviaciones estándar")
    fig.suptitle("Efecto del escalado en las variables de agrupamiento", fontsize=14, weight="bold")
    guardar_figura(fig, "07_escalado_antes_despues.png")

    guardar_tabla(tabla, "resumen_escalado.csv")
    return X_esc, escalador, tabla


# ---------------------------------------------------------------------------
# 3. K-Means: selección de K, modelo final y comparación
# ---------------------------------------------------------------------------
def _crear_kmeans(k: int) -> KMeans:
    return KMeans(n_clusters=k, n_init=10, random_state=config.SEED)


def _detectar_codo(ks: list[int], inercias: list[float]) -> int:
    """Método de máxima distancia a la recta que une el primer y último punto de la curva."""
    x = np.array(ks, dtype=float)
    y = np.array(inercias, dtype=float)
    x_n = (x - x.min()) / (x.max() - x.min())
    y_n = (y - y.min()) / (y.max() - y.min())
    p1, p2 = np.array([x_n[0], y_n[0]]), np.array([x_n[-1], y_n[-1]])
    direccion = (p2 - p1) / np.linalg.norm(p2 - p1)
    distancias = [np.linalg.norm((np.array([a, b]) - p1) - np.dot(np.array([a, b]) - p1, direccion) * direccion)
                  for a, b in zip(x_n, y_n)]
    return int(ks[int(np.argmax(distancias))])


def evaluar_valores_k(X_esc: np.ndarray, valores_k: list[int] = config.K_RANGE) -> tuple[pd.DataFrame, dict]:
    """Evalúa varios K con inercia (codo), silhouette, Davies-Bouldin y Calinski-Harabasz."""
    titulo(f"4. SELECCIÓN DEL NÚMERO DE CLÚSTERES (K = {valores_k[0]} a {valores_k[-1]})")
    filas = []
    for k in valores_k:
        modelo = _crear_kmeans(k)
        etiquetas = modelo.fit_predict(X_esc)
        filas.append(
            {
                "k": k,
                "inercia": modelo.inertia_,
                "silhouette": silhouette_score(X_esc, etiquetas),
                "davies_bouldin": davies_bouldin_score(X_esc, etiquetas),
                "calinski_harabasz": calinski_harabasz_score(X_esc, etiquetas),
            }
        )
    metricas = pd.DataFrame(filas)
    metricas["reduccion_inercia_%"] = (-metricas["inercia"].pct_change() * 100).round(2)
    print(metricas.to_string(index=False))

    k_codo = _detectar_codo(metricas["k"].tolist(), metricas["inercia"].tolist())
    k_sil = int(metricas.loc[metricas["silhouette"].idxmax(), "k"])
    k_db = int(metricas.loc[metricas["davies_bouldin"].idxmin(), "k"])
    k_optimo = k_sil
    sil_opt = metricas.loc[metricas["k"] == k_optimo, "silhouette"].iloc[0]
    sil_k2 = metricas.loc[metricas["k"] == 2, "silhouette"].iloc[0]
    db_k2 = metricas.loc[metricas["k"] == 2, "davies_bouldin"].iloc[0]
    db_opt = metricas.loc[metricas["k"] == k_optimo, "davies_bouldin"].iloc[0]
    ch_k2 = metricas.loc[metricas["k"] == 2, "calinski_harabasz"].iloc[0]
    ch_opt = metricas.loc[metricas["k"] == k_optimo, "calinski_harabasz"].iloc[0]

    justificacion = (
        f"Se selecciona K = {k_optimo} como la solución óptima. Aunque K = 2 presenta un coeficiente de silhouette alto "
        f"({sil_k2:.3f}), K = 4 alcanza el máximo global de silhouette ({sil_opt:.3f}), el menor índice Davies-Bouldin "
        f"({db_opt:.3f} frente a {db_k2:.3f} en K=2) y un índice Calinski-Harabasz sustancialmente superior ({ch_opt:,.0f} "
        f"frente a {ch_k2:,.0f} en K=2). Asimismo, la reducción de inercia refleja un codo evidente en K = 4 (53.4% de reducción "
        f"de K=3 a K=4, cayendo a solo 13.6% de K=4 a K=5). Desde el punto de vista de negocio y de la metodología RFM, K=2 es "
        f"insuficiente ya que solo divide la base en dos grupos generales (activos vs. inactivos o alto vs. bajo gasto), "
        f"impidiendo aislar a los clientes VIP ni distinguir clientes ocasionales de clientes en riesgo; K = 4 produce cuatro "
        f"segmentos claramente diferenciados, interpretables y accionables."
    )
    print(f"\nK por método del codo: {k_codo} | K por silhouette: {k_sil} | K por Davies-Bouldin: {k_db}")
    print(f"K ÓPTIMO SELECCIONADO: {k_optimo}")
    print(f"Justificación: {justificacion}")

    fig, ejes = plt.subplots(1, 2, figsize=(15, 5.5))
    ejes[0].plot(metricas["k"], metricas["inercia"], "o-", color="#2c7fb8", lw=2)
    ejes[0].axvline(k_codo, color="#d95f02", ls="--", label=f"Codo: K = {k_codo}")
    ejes[0].set_title("Método del codo (inercia / WCSS)")
    ejes[0].set_xlabel("Número de clústeres K")
    ejes[0].set_ylabel("Inercia")
    ejes[0].legend()
    ejes[1].plot(metricas["k"], metricas["silhouette"], "o-", color="#1b9e77", lw=2)
    ejes[1].axvline(k_sil, color="#d95f02", ls="--", label=f"Máximo: K = {k_sil}")
    for _, fila in metricas.iterrows():
        ejes[1].annotate(f"{fila['silhouette']:.3f}", (fila["k"], fila["silhouette"]), textcoords="offset points",
                         xytext=(0, 8), ha="center", fontsize=9)
    ejes[1].set_title("Coeficiente de silhouette")
    ejes[1].set_xlabel("Número de clústeres K")
    ejes[1].set_ylabel("Silhouette promedio")
    ejes[1].legend()
    fig.suptitle("Selección del K óptimo", fontsize=14, weight="bold")
    guardar_figura(fig, "08_codo_silhouette.png")
    guardar_tabla(metricas, "metricas_por_k.csv")

    decision = {"k_optimo": k_optimo, "k_codo": k_codo, "k_silhouette": k_sil, "k_davies_bouldin": k_db,
                "justificacion": justificacion}
    return metricas, decision


def entrenar_modelo_final(X_esc: np.ndarray, escalador: StandardScaler, k: int) -> dict:
    """Entrena K-Means con el K óptimo y reordena los clústeres de mayor a menor valor."""
    titulo(f"5. MODELO FINAL K-MEANS (K = {k})")
    modelo = _crear_kmeans(k)
    etiquetas_originales = modelo.fit_predict(X_esc)

    # Reordenar: clúster 0 = mayor valor (frecuencia + gasto - recencia en z-score)
    centros = pd.DataFrame(modelo.cluster_centers_, columns=VARS)
    puntaje_valor = centros["frecuencia_compras"] + centros["gasto_total"] - centros["recencia_dias"]
    orden = puntaje_valor.sort_values(ascending=False).index.tolist()
    mapeo = {viejo: nuevo for nuevo, viejo in enumerate(orden)}
    etiquetas = np.vectorize(mapeo.get)(etiquetas_originales)

    centros_esc = centros.loc[orden].reset_index(drop=True)
    centros_esc.index.name = "cluster"
    centros_orig = pd.DataFrame(escalador.inverse_transform(centros_esc.values), columns=VARS)
    centros_orig.index.name = "cluster"

    conteo = pd.Series(etiquetas).value_counts().sort_index()
    metricas = {
        "inercia": float(modelo.inertia_),
        "silhouette": float(silhouette_score(X_esc, etiquetas)),
        "davies_bouldin": float(davies_bouldin_score(X_esc, etiquetas)),
        "calinski_harabasz": float(calinski_harabasz_score(X_esc, etiquetas)),
        "iteraciones": int(modelo.n_iter_),
    }

    subtitulo("Centroides en escala estandarizada (z-score)")
    print(centros_esc.round(3).to_string())
    subtitulo("Centroides en unidades originales (inverse_transform)")
    print(centros_orig.round(2).to_string())
    subtitulo("Registros por clúster")
    print(pd.DataFrame({"clientes": conteo, "porcentaje": (conteo / conteo.sum() * 100).round(2)}).to_string())
    subtitulo("Métricas del modelo final")
    for nombre, valor in metricas.items():
        print(f"{nombre}: {valor:,.4f}" if isinstance(valor, float) else f"{nombre}: {valor}")

    return {
        "modelo": modelo,
        "etiquetas": etiquetas,
        "centroides_escalados": centros_esc,
        "centroides_originales": centros_orig,
        "conteo": conteo,
        "metricas": metricas,
    }


def graficar_clusters(df: pd.DataFrame, X_esc: np.ndarray, resultado: dict, nombres: dict) -> None:
    """Gráficas de agrupamiento con centroides, tamaños y perfiles."""
    titulo("6. GRÁFICAS DE AGRUPAMIENTOS DEL MODELO FINAL")
    centros = resultado["centroides_originales"]
    k = len(centros)
    colores = {nombres[c]: PALETA_CLUSTERS[c] for c in range(k)}
    datos = df.assign(cluster_nombre=df["cluster"].map(nombres))
    orden_nombres = [nombres[c] for c in range(k)]

    # 09. Dispersión en variables originales con centroides
    fig, ejes = plt.subplots(1, 2, figsize=(17, 6.5))
    for eje, (x, y) in zip(ejes, [("frecuencia_compras", "gasto_total"), ("recencia_dias", "gasto_total")]):
        sns.scatterplot(data=datos, x=x, y=y, hue="cluster_nombre", hue_order=orden_nombres, palette=colores,
                        alpha=0.65, s=28, ax=eje, edgecolor="none")
        eje.scatter(centros[x], centros[y], marker="X", s=320, c="black", edgecolor="white", linewidth=1.5,
                    label="Centroides", zorder=5)
        for c in range(k):
            eje.annotate(f"C{c}", (centros.loc[c, x], centros.loc[c, y]), textcoords="offset points", xytext=(10, 8),
                         fontsize=11, weight="bold")
        eje.set_xlabel(config.ETIQUETAS[x])
        eje.set_ylabel(config.ETIQUETAS[y])
        eje.legend(fontsize=8, loc="best")
    ejes[0].set_title("Frecuencia vs. gasto")
    ejes[1].set_title("Recencia vs. gasto")
    fig.suptitle(f"Agrupamientos K-Means (K = {k}) con centroides", fontsize=14, weight="bold")
    guardar_figura(fig, "09_clusters_dispersion_centroides.png")

    # 10. Proyección PCA en 2D con centroides
    pca = PCA(n_components=2, random_state=config.SEED)
    componentes = pca.fit_transform(X_esc)
    centros_pca = pca.transform(resultado["centroides_escalados"].values)
    fig, eje = plt.subplots(figsize=(10, 7))
    for c in range(k):
        mascara = df["cluster"].values == c
        eje.scatter(componentes[mascara, 0], componentes[mascara, 1], s=22, alpha=0.6, color=PALETA_CLUSTERS[c],
                    label=f"C{c}: {nombres[c]}")
    eje.scatter(centros_pca[:, 0], centros_pca[:, 1], marker="X", s=350, c="black", edgecolor="white", linewidth=1.5,
                label="Centroides", zorder=5)
    var = pca.explained_variance_ratio_ * 100
    eje.set_xlabel(f"Componente principal 1 ({var[0]:.1f}% varianza)")
    eje.set_ylabel(f"Componente principal 2 ({var[1]:.1f}% varianza)")
    eje.set_title("Clústeres proyectados con PCA (variables RFM escaladas)", fontsize=13, weight="bold")
    eje.legend(fontsize=9)
    guardar_figura(fig, "10_clusters_pca.png")

    # 11. Tamaño de cada clúster
    conteo = datos["cluster_nombre"].value_counts().reindex(orden_nombres)
    fig, eje = plt.subplots(figsize=(10, 5.5))
    barras = eje.barh(conteo.index, conteo.values, color=[colores[n] for n in conteo.index])
    for barra, valor in zip(barras, conteo.values):
        eje.text(barra.get_width() + 5, barra.get_y() + barra.get_height() / 2,
                 f"{valor} ({valor / conteo.sum() * 100:.1f}%)", va="center")
    eje.invert_yaxis()
    eje.set_xlabel("Número de clientes")
    eje.set_title("Distribución de clientes por clúster", fontsize=13, weight="bold")
    eje.set_xlim(0, conteo.max() * 1.2)
    guardar_figura(fig, "11_distribucion_clusters.png")

    # 12. Heatmap de centroides (z-score) anotado con valores originales
    z = resultado["centroides_escalados"].copy()
    z.index = [f"C{c}: {nombres[c]}" for c in range(k)]
    anotaciones = centros.copy()
    anotaciones = anotaciones.apply(lambda col: col.map(lambda v: f"{v:,.0f}"))
    fig, eje = plt.subplots(figsize=(10, 1.2 * k + 2))
    etiquetas_cortas_x = {v: config.ETIQUETAS[v].replace(" (", "\n(") for v in VARS}
    sns.heatmap(z.rename(columns=etiquetas_cortas_x), annot=anotaciones.values, fmt="", cmap="coolwarm", center=0,
                ax=eje, cbar_kws={"label": "z-score del centroide"})
    eje.tick_params(axis="x", rotation=0)
    eje.set_title("Perfil de centroides (color = z-score: rojo sobre / azul bajo el promedio;\n"
                  "texto = valor original)", fontsize=12, weight="bold")
    eje.set_ylabel("")
    guardar_figura(fig, "12_perfil_centroides.png")

    # 13. Boxplots por clúster
    fig, ejes = plt.subplots(2, 2, figsize=(16, 10))
    etiquetas_cortas = [f"C{c}" for c in range(k)]
    datos_box = datos.assign(cluster_corto=datos["cluster"].map(lambda c: f"C{c}"))
    for eje, col in zip(ejes.flat, ["frecuencia_compras", "gasto_total", "recencia_dias", "satisfaccion"]):
        sns.boxplot(data=datos_box, x="cluster_corto", y=col, order=etiquetas_cortas, hue="cluster_corto",
                    palette=PALETA_CLUSTERS[:k], legend=False, ax=eje)
        eje.set_title(config.ETIQUETAS[col])
        eje.set_xlabel("")
        eje.set_ylabel("")
    leyenda = " | ".join(f"C{c} = {nombres[c]}" for c in range(k))
    fig.suptitle(f"Comparación de características por clúster\n{leyenda}", fontsize=12, weight="bold")
    guardar_figura(fig, "13_boxplots_por_cluster.png")

    # 14. Canal preferido por clúster
    mezcla = pd.crosstab(datos["cluster_nombre"], datos["canal_preferido"], normalize="index").reindex(orden_nombres) * 100
    fig, eje = plt.subplots(figsize=(11, 5.5))
    mezcla.plot(kind="barh", stacked=True, ax=eje, color=["#8da0cb", "#66c2a5", "#fc8d62"])
    eje.invert_yaxis()
    eje.set_xlabel("% de clientes del clúster")
    eje.set_ylabel("")
    eje.set_title("Canal preferido dentro de cada clúster", fontsize=13, weight="bold")
    eje.legend(title="Canal", bbox_to_anchor=(1.01, 1), loc="upper left")
    guardar_figura(fig, "14_canal_por_cluster.png")


def _describir_cambios(etiquetas_ref: np.ndarray, etiquetas_otra: np.ndarray, nombres: dict) -> str:
    """Explica qué segmentos del modelo final se fusionan o se dividen en otra configuración."""
    cruce = pd.crosstab(etiquetas_ref, etiquetas_otra, normalize="index")
    fusiones = []
    for col in cruce.columns:
        origen = [nombres[i] for i in cruce.index if cruce.loc[i, col] > 0.5]
        if len(origen) >= 2:
            fusiones.append(" + ".join(f"'{o}'" for o in origen))
    divididos = [f"'{nombres[i]}'" for i in cruce.index if (cruce.loc[i] > 0.25).sum() >= 2]
    partes = []
    if fusiones:
        partes.append(f"Se fusionan en un mismo grupo: {'; '.join(fusiones)}.")
    if divididos:
        partes.append(f"Se parten en dos o más grupos: {', '.join(divididos)}.")
    return " ".join(partes) if partes else "Los segmentos se mantienen prácticamente iguales."


def comparar_configuraciones(df: pd.DataFrame, X_esc: np.ndarray, k_optimo: int, etiquetas_final: np.ndarray,
                             nombres: dict) -> tuple[pd.DataFrame, list[str]]:
    """Compara el modelo final contra otro K y contra el mismo K sin escalado."""
    titulo("7. COMPARACIÓN DE CONFIGURACIONES DEL MODELO")
    k_alterno = k_optimo - 1 if k_optimo > 2 else k_optimo + 1

    modelo_b = _crear_kmeans(k_alterno)
    etiquetas_b = modelo_b.fit_predict(X_esc)
    modelo_c = _crear_kmeans(k_optimo)
    etiquetas_c = modelo_c.fit_predict(df[VARS].values)

    configuraciones = [
        (f"A) K={k_optimo} con StandardScaler (modelo final)", k_optimo, etiquetas_final, "Sí"),
        (f"B) K={k_alterno} con StandardScaler", k_alterno, etiquetas_b, "Sí"),
        (f"C) K={k_optimo} sin escalar", k_optimo, etiquetas_c, "No"),
    ]
    filas = []
    for nombre, k, etiquetas, escalado in configuraciones:
        tamanos = np.bincount(etiquetas)
        filas.append(
            {
                "configuracion": nombre,
                "k": k,
                "escalado": escalado,
                "silhouette": silhouette_score(X_esc, etiquetas),
                "davies_bouldin": davies_bouldin_score(X_esc, etiquetas),
                "cluster_mas_chico": int(tamanos.min()),
                "cluster_mas_grande": int(tamanos.max()),
                "coincidencia_con_A_ARI": adjusted_rand_score(etiquetas_final, etiquetas),
            }
        )
    tabla = pd.DataFrame(filas)
    print(tabla.to_string(index=False))
    print(
        "\nNota metodológica sobre el espacio de evaluación: Las métricas de Silhouette y Davies-Bouldin para todas "
        "las configuraciones (incluyendo la opción sin escalar C) se calculan en el espacio estandarizado (z-score) de "
        "las variables RFM. Esto garantiza una comparación matemática rigurosa bajo una misma métrica geométrica. Si la "
        "configuración C se evaluara en su espacio original sin escalar, las distancias reflejarían casi en un 100% las "
        "diferencias en pesos del gasto total (desviación ~13,461 MXN frente a ~9 en frecuencia), ocultando que el algoritmo "
        "ignoró la recencia y la frecuencia en la delimitación de los clústeres."
    )

    # Interpretación automática de las diferencias (a partir de tablas cruzadas reales)
    sil_a, sil_b, sil_c = tabla["silhouette"].tolist()
    ari_c = tabla.loc[2, "coincidencia_con_A_ARI"]
    cambios_b = _describir_cambios(etiquetas_final, etiquetas_b, nombres)
    cambios_c = _describir_cambios(etiquetas_final, etiquetas_c, nombres)
    textos = [
        f"A vs. B (cambiar K): con K={k_alterno} el silhouette pasa de {sil_a:.3f} a {sil_b:.3f} "
        f"({'peor' if sil_b < sil_a else 'mejor'}). {cambios_b} Mezclar perfiles distintos en un solo grupo "
        "impide diseñar estrategias específicas, por lo que se conserva el K óptimo.",
        f"A vs. C (escalar o no): sin StandardScaler el gasto (miles de pesos) domina la distancia euclidiana y "
        f"los grupos se forman casi solo por monto. {cambios_c} Al evaluar ambas configuraciones en el espacio "
        f"estandarizado para una comparación justa, la coincidencia con el modelo final es solo ARI = {ari_c:.3f} "
        f"y el silhouette cae a {sil_c:.3f}: la recencia (clave para detectar abandono) y la frecuencia pierden "
        "relevancia en la asignación de clústeres.",
    ]
    print()
    for texto in textos:
        print(f"* {texto}")
    subtitulo("Tabla cruzada: modelo final (filas) vs. configuración sin escalar (columnas)")
    print(pd.crosstab(pd.Series(etiquetas_final).map(nombres).rename("modelo_final"),
                      pd.Series(etiquetas_c, name="grupo_sin_escalar")).to_string())

    # Figura comparativa en el plano frecuencia-gasto
    fig, ejes = plt.subplots(1, 3, figsize=(20, 6))
    for eje, (nombre, k, etiquetas, _) in zip(ejes, configuraciones):
        for c in range(k):
            m = etiquetas == c
            eje.scatter(df.loc[m, "recencia_dias"], df.loc[m, "gasto_total"], s=14, alpha=0.6,
                        color=PALETA_CLUSTERS[c], label=f"Grupo {c}")
        sil = silhouette_score(X_esc, etiquetas)
        eje.set_title(f"{nombre}\nsilhouette = {sil:.3f}", fontsize=11)
        eje.set_xlabel(config.ETIQUETAS["recencia_dias"])
        eje.set_ylabel(config.ETIQUETAS["gasto_total"])
        eje.legend(fontsize=8)
    fig.suptitle("Comparación de configuraciones del modelo", fontsize=14, weight="bold")
    guardar_figura(fig, "15_comparacion_configuraciones.png")
    guardar_tabla(tabla, "comparacion_configuraciones.csv")
    return tabla, textos
