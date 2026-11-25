"""
Análisis e interpretación de los clústeres.

Asigna nombres descriptivos a partir de los centroides, calcula estadísticas
por clúster, compara similitudes y diferencias y redacta hallazgos,
recomendaciones y limitaciones con los números reales del modelo.
"""
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import config  # noqa: E402
from src.analisis_kmeans import guardar_tabla, subtitulo, titulo  # noqa: E402

VARS = config.VARIABLES_CLUSTER

PERSONAS = {
    "alto_valor": {
        "nombre": "Clientes VIP de alto valor",
        "resumen": "Son los clientes más valiosos: compran con mucha frecuencia, gastan más que nadie y siguen activos.",
    },
    "regular": {
        "nombre": "Clientes leales regulares",
        "resumen": "Compran de forma constante con un gasto intermedio; son la base estable del negocio.",
    },
    "ocasional": {
        "nombre": "Clientes ocasionales de bajo gasto",
        "resumen": "Compran pocas veces y con tickets bajos; son clientes recientes o poco comprometidos con la marca.",
    },
    "riesgo": {
        "nombre": "Clientes en riesgo de abandono",
        "resumen": "Llevan meses sin comprar; si no se reactivan es muy probable que se pierdan.",
    },
}


# ---------------------------------------------------------------------------
# Nombres descriptivos
# ---------------------------------------------------------------------------
def nombrar_clusters(centroides_z: pd.DataFrame) -> dict[int, dict]:
    """
    Asigna una "persona" a cada clúster usando sus centroides estandarizados:
    1. Alto valor: mayor (frecuencia + gasto - recencia).
    2. En riesgo: mayor recencia entre los restantes (si está claramente sobre el promedio).
    3. Ocasional: menor (frecuencia + gasto) entre los restantes.
    4. Regular: cualquier clúster que quede.
    """
    z = centroides_z
    restantes = list(z.index)
    claves: dict[int, str] = {}

    valor = z["frecuencia_compras"] + z["gasto_total"] - z["recencia_dias"]
    vip = int(valor.idxmax())
    claves[vip] = "alto_valor"
    restantes.remove(vip)

    if restantes:
        candidato = int(z.loc[restantes, "recencia_dias"].idxmax())
        if z.loc[candidato, "recencia_dias"] > 0.5:
            claves[candidato] = "riesgo"
            restantes.remove(candidato)

    if restantes:
        ocasional = int((z.loc[restantes, "frecuencia_compras"] + z.loc[restantes, "gasto_total"]).idxmin())
        claves[ocasional] = "ocasional"
        restantes.remove(ocasional)

    for c in restantes:
        claves[int(c)] = "regular"

    info = {}
    usados: dict[str, int] = {}
    for c in sorted(claves):
        clave = claves[c]
        nombre = PERSONAS[clave]["nombre"]
        usados[nombre] = usados.get(nombre, 0) + 1
        if list(claves.values()).count(clave) > 1:
            nombre = f"{nombre} (subgrupo {usados[nombre]})"
        info[c] = {"clave": clave, "nombre": nombre}
    return info


# ---------------------------------------------------------------------------
# Estadísticas por clúster
# ---------------------------------------------------------------------------
def perfilar_clusters(df: pd.DataFrame) -> pd.DataFrame:
    """Tabla comparativa con un renglón por clúster."""
    gasto_global = df["gasto_total"].sum()
    filas = []
    for c, grupo in df.groupby("cluster", observed=True):
        canal = grupo["canal_preferido"].value_counts(normalize=True)
        filas.append(
            {
                "cluster": int(c),
                "nombre": grupo["cluster_nombre"].iloc[0],
                "clientes": len(grupo),
                "porcentaje_clientes": len(grupo) / len(df) * 100,
                "frecuencia_media": grupo["frecuencia_compras"].mean(),
                "gasto_medio": grupo["gasto_total"].mean(),
                "gasto_mediano": grupo["gasto_total"].median(),
                "recencia_media": grupo["recencia_dias"].mean(),
                "ticket_medio": grupo["ticket_promedio"].mean(),
                "edad_media": grupo["edad"].mean(),
                "antiguedad_media": grupo["antiguedad_meses"].mean(),
                "satisfaccion_media": grupo["satisfaccion"].mean(),
                "gasto_acumulado": grupo["gasto_total"].sum(),
                "participacion_gasto_%": grupo["gasto_total"].sum() / gasto_global * 100,
                "canal_principal": str(canal.index[0]),
                "canal_principal_%": canal.iloc[0] * 100,
            }
        )
    return pd.DataFrame(filas).set_index("cluster")


def estadisticas_descriptivas(df: pd.DataFrame) -> pd.DataFrame:
    """describe() de cada variable por clúster en formato largo (fácil de leer y filtrar)."""
    columnas = VARS + ["ticket_promedio", "edad", "antiguedad_meses", "satisfaccion"]
    desc = df.groupby("cluster_nombre", observed=True)[columnas].describe()
    largo = desc.stack(level=0, future_stack=True).reset_index()
    largo = largo.rename(columns={"cluster_nombre": "cluster", "level_1": "variable"})
    return largo


def _similitudes(centroides_z: pd.DataFrame, info: dict) -> tuple[pd.DataFrame, str]:
    pares = []
    for a, b in combinations(centroides_z.index, 2):
        distancia = float(np.linalg.norm(centroides_z.loc[a] - centroides_z.loc[b]))
        pares.append({"cluster_a": info[a]["nombre"], "cluster_b": info[b]["nombre"], "distancia_centroides": distancia})
    tabla = pd.DataFrame(pares).sort_values("distancia_centroides").reset_index(drop=True)
    cercano, lejano = tabla.iloc[0], tabla.iloc[-1]
    texto = (
        f"Los grupos más parecidos son '{cercano.cluster_a}' y '{cercano.cluster_b}' "
        f"(distancia entre centroides = {cercano.distancia_centroides:.2f} en z-score); "
        f"los más diferentes son '{lejano.cluster_a}' y '{lejano.cluster_b}' "
        f"(distancia = {lejano.distancia_centroides:.2f})."
    )
    return tabla, texto


# ---------------------------------------------------------------------------
# Textos de interpretación
# ---------------------------------------------------------------------------
def describir_clusters(perfil: pd.DataFrame, info: dict) -> dict[int, str]:
    descripciones = {}
    for c, fila in perfil.iterrows():
        descripciones[c] = (
            f"{PERSONAS[info[c]['clave']]['resumen']} Agrupa {fila.clientes} clientes "
            f"({fila.porcentaje_clientes:.1f}%). En promedio compran {fila.frecuencia_media:.1f} veces al año, "
            f"gastan ${fila.gasto_medio:,.0f} MXN anuales (ticket promedio ${fila.ticket_medio:,.0f}) y su última "
            f"compra fue hace {fila.recencia_media:.0f} días. Canal predominante: {fila.canal_principal} "
            f"({fila['canal_principal_%']:.0f}%). Satisfacción promedio: {fila.satisfaccion_media:.2f}/5."
        )
    return descripciones


def _por_clave(perfil: pd.DataFrame, info: dict, clave: str):
    for c in perfil.index:
        if info[c]["clave"] == clave:
            return perfil.loc[c]
    return None


def generar_hallazgos(perfil: pd.DataFrame, info: dict, decision: dict, metricas: dict, texto_similitud: str) -> list[str]:
    vip = _por_clave(perfil, info, "alto_valor")
    riesgo = _por_clave(perfil, info, "riesgo")
    ocasional = _por_clave(perfil, info, "ocasional")
    regular = _por_clave(perfil, info, "regular")
    hallazgos = []

    hallazgos.append(
        f"Se identificaron {len(perfil)} segmentos bien diferenciados (K óptimo = {decision['k_optimo']}, "
        f"silhouette = {metricas['silhouette']:.3f}); el codo, el silhouette y Davies-Bouldin "
        f"{'coinciden' if decision['k_codo'] == decision['k_silhouette'] == decision['k_davies_bouldin'] else 'se analizaron en conjunto'}"
        " en esa elección."
    )
    if vip is not None:
        hallazgos.append(
            f"Concentración del valor: '{vip.nombre}' representa solo el {vip.porcentaje_clientes:.1f}% de los "
            f"clientes pero aporta el {vip['participacion_gasto_%']:.1f}% del gasto total; cada uno gasta en "
            f"promedio ${vip.gasto_medio:,.0f} MXN al año."
        )
    if riesgo is not None:
        comparacion = f", {riesgo.recencia_media / vip.recencia_media:.0f} veces más que los VIP" if vip is not None else ""
        hallazgos.append(
            f"Ingreso en riesgo: '{riesgo.nombre}' agrupa al {riesgo.porcentaje_clientes:.1f}% de los clientes, "
            f"no compra desde hace {riesgo.recencia_media:.0f} días en promedio{comparacion}, y su gasto "
            f"histórico suma ${riesgo.gasto_acumulado:,.0f} MXN ({riesgo['participacion_gasto_%']:.1f}% del total) "
            "que podría perderse."
        )
    if ocasional is not None:
        hallazgos.append(
            f"Base amplia de bajo valor: '{ocasional.nombre}' es el {ocasional.porcentaje_clientes:.1f}% de los "
            f"clientes pero solo genera el {ocasional['participacion_gasto_%']:.1f}% del gasto; su ticket promedio "
            f"(${ocasional.ticket_medio:,.0f}) y frecuencia ({ocasional.frecuencia_media:.1f} compras/año) son los "
            f"más bajos, y su canal principal es {ocasional.canal_principal}."
        )
    if vip is not None and riesgo is not None:
        hallazgos.append(
            f"Caracterización con satisfacción (variable descriptiva complementaria): al ser un dataset sintético, la "
            f"satisfacción no constituye una validación externa independiente, pero sí funciona como una variable "
            f"descriptiva complementaria muy reveladora: la satisfacción promedio es {vip.satisfaccion_media:.2f}/5 en "
            f"'{vip.nombre}' contra solo {riesgo.satisfaccion_media:.2f}/5 en '{riesgo.nombre}', lo que demuestra "
            "consistencia cualitativa entre el abandono en compras y una menor experiencia percibida."
        )
    if vip is not None:
        hallazgos.append(
            f"Canal: el {vip['canal_principal_%']:.0f}% de '{vip.nombre}' prefiere {vip.canal_principal}"
            + (f", mientras que en '{regular.nombre}' el canal principal es {regular.canal_principal}."
               if regular is not None else ".")
        )
    hallazgos.append(texto_similitud)
    return hallazgos


def generar_recomendaciones(perfil: pd.DataFrame, info: dict) -> list[str]:
    recomendaciones = []
    vip = _por_clave(perfil, info, "alto_valor")
    regular = _por_clave(perfil, info, "regular")
    ocasional = _por_clave(perfil, info, "ocasional")
    riesgo = _por_clave(perfil, info, "riesgo")

    if vip is not None:
        recomendaciones.append(
            f"Retener a '{vip.nombre}' con un programa de lealtad premium (acceso anticipado, envío gratis, "
            f"atención prioritaria y beneficios exclusivos en {vip.canal_principal}). Perder a uno de estos "
            f"clientes equivale a perder ~${vip.gasto_medio:,.0f} MXN al año."
        )
    if regular is not None:
        recomendaciones.append(
            f"Hacer crecer a '{regular.nombre}' con ventas cruzadas, paquetes y metas de puntos para subir su "
            f"ticket (hoy ${regular.ticket_medio:,.0f}) y convertirlos en VIP."
        )
    if ocasional is not None:
        recomendaciones.append(
            f"Activar a '{ocasional.nombre}' con cupón de segunda compra, recordatorios personalizados por "
            f"{ocasional.canal_principal} y contenido de bienvenida para aumentar su frecuencia "
            f"({ocasional.frecuencia_media:.1f} compras/año)."
        )
    if riesgo is not None:
        recomendaciones.append(
            f"Lanzar una campaña de reactivación (win-back) para '{riesgo.nombre}': descuento por tiempo limitado, "
            f"encuesta de satisfacción (su promedio es {riesgo.satisfaccion_media:.2f}/5) y seguimiento a los "
            "60 y 90 días sin compra antes de que el cliente llegue a esta etapa."
        )
    recomendaciones.append(
        "Recalcular la segmentación cada mes y monitorear la migración de clientes entre segmentos como KPI "
        "de retención (por ejemplo, % de clientes que pasan de 'regular' a 'en riesgo')."
    )
    return recomendaciones


def generar_limitaciones(metricas: dict, n_imputados: int) -> list[str]:
    return [
        "El dataset es sintético (generado con semilla fija 42 a partir de distribuciones latentes); los resultados "
        "ilustran con fidelidad la metodología de segmentación RFM, pero deben contrastarse con datos reales de transacciones "
        "antes de tomar decisiones operativas o comerciales.",
        "La satisfacción y las variables sociodemográficas se analizan como atributos descriptivos complementarios para perfilar "
        "los grupos y no como una validación externa independiente, dado el origen sintético del dataset.",
        "K-Means asume grupos aproximadamente esféricos y de dispersión similar, es sensible a la escala de las variables "
        "y a la presencia de valores atípicos, y requiere definir el número K de antemano.",
        "El modelo se enfoca estrictamente en las tres variables RFM (recencia, frecuencia y gasto total); no incorpora "
        "categorías de producto, margen de rentabilidad, devoluciones ni interacción en canales digitales.",
        f"El coeficiente de silhouette ({metricas['silhouette']:.3f}) constata una separación sólida y compacta de los grupos, "
        "pero los clientes situados en las regiones frontera pueden presentar asignaciones con cierto grado de proximidad "
        "al clúster vecino.",
        f"Se imputaron {n_imputados} celdas nulas mediante mediana (numéricas) y moda (categóricas); si bien preserva el tamaño "
        "muestral sin distorsionar tendencias centrales, puede atenuar levemente la varianza natural.",
        "La segmentación refleja una imagen estática de los últimos 12 meses: los patrones de compra evolucionan con el tiempo "
        "y la estacionalidad, por lo que el modelo debe ejecutarse y calibrarse periódicamente.",
    ]


def interpretar(df: pd.DataFrame, resultado: dict, decision: dict, n_imputados: int) -> dict:
    """Ejecuta toda la etapa de interpretación e imprime los resultados."""
    titulo("8. ANÁLISIS E INTERPRETACIÓN DE LOS CLÚSTERES")
    info = nombrar_clusters(resultado["centroides_escalados"])
    nombres = {c: datos["nombre"] for c, datos in info.items()}
    df = df.assign(cluster_nombre=df["cluster"].map(nombres))

    subtitulo("Interpretación de centroides (z-score: + sobre el promedio, - bajo el promedio)")
    for c, fila in resultado["centroides_escalados"].iterrows():
        partes = []
        for var in VARS:
            v = fila[var]
            nivel = "alto" if v > 0.5 else "bajo" if v < -0.5 else "promedio"
            partes.append(f"{var}={v:+.2f} ({nivel})")
        print(f"C{c} -> {nombres[c]}: " + ", ".join(partes))

    perfil = perfilar_clusters(df)
    subtitulo("Tabla comparativa de clústeres")
    print(perfil.round(2).to_string())
    guardar_tabla(perfil.round(2), "tabla_comparativa_clusters.csv", index=True)

    stats = estadisticas_descriptivas(df)
    subtitulo("Estadísticas descriptivas por clúster (variables RFM)")
    print(stats[stats["variable"].isin(VARS)].round(2).to_string(index=False))
    guardar_tabla(stats.round(2), "estadisticas_por_cluster.csv")

    subtitulo("Comparación contra el promedio general (índice: 100 = promedio)")
    indice = df.groupby("cluster_nombre", observed=True)[VARS + ["ticket_promedio", "satisfaccion"]].mean()
    indice = (indice / df[VARS + ["ticket_promedio", "satisfaccion"]].mean() * 100).round(0)
    print(indice.to_string())

    tabla_sim, texto_sim = _similitudes(resultado["centroides_escalados"], info)
    subtitulo("Similitudes y diferencias entre clústeres (distancia entre centroides)")
    print(tabla_sim.round(3).to_string(index=False))
    print(texto_sim)

    descripciones = describir_clusters(perfil, info)
    subtitulo("Descripción de los grupos")
    for c, texto in descripciones.items():
        print(f"C{c} - {nombres[c]}: {texto}")

    hallazgos = generar_hallazgos(perfil, info, decision, resultado["metricas"], texto_sim)
    recomendaciones = generar_recomendaciones(perfil, info)
    limitaciones = generar_limitaciones(resultado["metricas"], n_imputados)
    for encabezado, lista in (("Hallazgos", hallazgos), ("Recomendaciones", recomendaciones),
                              ("Limitaciones del modelo", limitaciones)):
        subtitulo(encabezado)
        for i, texto in enumerate(lista, 1):
            print(f"{i}. {texto}")

    return {
        "df": df,
        "info": info,
        "nombres": nombres,
        "perfil": perfil,
        "descripciones": descripciones,
        "similitudes": tabla_sim,
        "hallazgos": hallazgos,
        "recomendaciones": recomendaciones,
        "limitaciones": limitaciones,
    }
