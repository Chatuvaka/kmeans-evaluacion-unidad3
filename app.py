"""
Dashboard interactivo: Segmentación de clientes con K-Means.

Páginas:
    1. Análisis general        -> indicadores, estadísticas y visualizaciones del dataset.
    2. Segmentación K-Means    -> agrupamientos, perfiles, comparaciones y resultados del modelo.

Ejecutar desde la carpeta raíz del proyecto (después de `python src/main.py`):
    streamlit run app.py
"""
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import config

st.set_page_config(
    page_title="Segmentación de clientes | K-Means",
    page_icon=":bar_chart:",
    layout="wide",
)

COLORES = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e", "#e6ab02", "#a6761d", "#666666"]
RFM = config.VARIABLES_CLUSTER
ETQ = config.ETIQUETAS
NUMERICAS = ["frecuencia_compras", "gasto_total", "recencia_dias", "ticket_promedio", "edad",
             "antiguedad_meses", "satisfaccion"]


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv(config.DATA_PROCESSED)
    with open(config.RESULTS_JSON, encoding="utf-8") as archivo:
        resultados = json.load(archivo)
    metricas_k = pd.read_csv(config.TABLE_DIR / "metricas_por_k.csv")
    return df, resultados, metricas_k


faltantes = [p for p in (config.DATA_PROCESSED, config.RESULTS_JSON, config.TABLE_DIR / "metricas_por_k.csv")
             if not p.exists()]
if faltantes:
    st.error(
        "No se encontraron los resultados del modelo. Ejecuta primero el pipeline desde la raíz del "
        "proyecto:\n\n`python src/main.py`\n\nArchivos faltantes: "
        + ", ".join(p.relative_to(config.ROOT).as_posix() for p in faltantes)
    )
    st.stop()

df, res, metricas_k = cargar_datos()
clusters_info = sorted(res["clusters"], key=lambda c: c["cluster"])
ORDEN = [c["nombre"] for c in clusters_info]
MAPA_COLOR = {c["nombre"]: COLORES[c["cluster"] % len(COLORES)] for c in clusters_info}
CLAVE_POR_NOMBRE = {c["nombre"]: c["clave"] for c in clusters_info}


def moneda(valor: float) -> str:
    return f"${valor:,.0f}"


# ---------------------------------------------------------------------------
# Barra lateral: navegación y filtros
# ---------------------------------------------------------------------------
st.sidebar.title("Navegación")
pagina = st.sidebar.radio(
    "Selecciona una página",
    ["Página 1: Análisis general", "Página 2: Segmentación K-Means"],
)

st.sidebar.header("Filtros")
f_clusters = st.sidebar.multiselect("Clúster", options=ORDEN, default=ORDEN)
canales = sorted(df["canal_preferido"].unique())
f_canales = st.sidebar.multiselect("Canal preferido", options=canales, default=canales)
gasto_min, gasto_max = int(df["gasto_total"].min()), int(df["gasto_total"].max()) + 1
f_gasto = st.sidebar.slider("Rango de gasto anual (MXN)", gasto_min, gasto_max, (gasto_min, gasto_max), step=500)
frec_min, frec_max = int(df["frecuencia_compras"].min()), int(df["frecuencia_compras"].max())
f_frec = st.sidebar.slider("Rango de frecuencia (compras/año)", frec_min, frec_max, (frec_min, frec_max))

filtrado = df[
    df["cluster_nombre"].isin(f_clusters)
    & df["canal_preferido"].isin(f_canales)
    & df["gasto_total"].between(*f_gasto)
    & df["frecuencia_compras"].between(*f_frec)
]
st.sidebar.markdown(f"**Clientes seleccionados:** {len(filtrado):,} de {len(df):,}")
st.sidebar.divider()
st.sidebar.caption(
    "Proyecto tercer unidad · IDGS 9 - 3\n\n"
    "Jesus Rodolfo Lopez Gamez · Josue Misraim Valenzuela Verdugo · Axel Alan Jimenez Jaramillo\n\n"
    "24/11/2026"
)

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
st.title("Segmentación de clientes por comportamiento de compra con K-Means")
st.markdown(
    "Agrupamos a los clientes según **recencia, frecuencia y monto de gasto (RFM)** para diseñar "
    "estrategias de retención y promoción basadas en datos."
)

if filtrado.empty:
    st.warning("Ningún cliente cumple con los filtros seleccionados. Ajusta los filtros de la barra lateral.")
    st.stop()


# ===========================================================================
# PÁGINA 1: ANÁLISIS GENERAL
# ===========================================================================
def pagina_analisis_general(datos: pd.DataFrame) -> None:
    st.header("Página 1 · Análisis general del dataset")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Clientes analizados", f"{len(datos):,}", f"{len(datos) / len(df) * 100:.0f}% del total",
              delta_color="off", border=True)
    k2.metric("Gasto total acumulado", moneda(datos["gasto_total"].sum()),
              f"{datos['gasto_total'].sum() / df['gasto_total'].sum() * 100:.0f}% del ingreso", delta_color="off",
              border=True)
    k3.metric("Frecuencia promedio (compras/año)", f"{datos['frecuencia_compras'].mean():.1f}",
              f"{datos['frecuencia_compras'].mean() - df['frecuencia_compras'].mean():+.1f} vs. general",
              border=True)
    k4.metric("Recencia promedio", f"{datos['recencia_dias'].mean():.0f} días",
              f"{datos['recencia_dias'].mean() - df['recencia_dias'].mean():+.0f} vs. general",
              delta_color="inverse", border=True)

    st.subheader("Distribución de variables")
    c1, c2 = st.columns([3, 2])
    with c1:
        variable = st.selectbox("Variable a visualizar", NUMERICAS, format_func=lambda v: ETQ.get(v, v))
        fig = px.histogram(datos, x=variable, nbins=40, marginal="box", color_discrete_sequence=["#2c7fb8"],
                           labels={variable: ETQ.get(variable, variable)})
        fig.update_layout(yaxis_title="Clientes", bargap=0.05, height=420)
        st.plotly_chart(fig)
    with c2:
        canal = datos["canal_preferido"].value_counts().reset_index()
        fig = px.pie(canal, names="canal_preferido", values="count", hole=0.45,
                     title="Clientes por canal preferido", color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=470)
        st.plotly_chart(fig)

    c3, c4 = st.columns(2)
    with c3:
        region = datos.groupby(["region", "canal_preferido"]).size().reset_index(name="clientes")
        fig = px.bar(region, x="region", y="clientes", color="canal_preferido", barmode="group",
                     title="Clientes por región y canal", color_discrete_sequence=px.colors.qualitative.Set2,
                     labels={"region": "Región", "canal_preferido": "Canal"})
        st.plotly_chart(fig)
    with c4:
        corr = datos[NUMERICAS].corr().round(2)
        corr.index = corr.columns = [ETQ.get(c, c).split(" (")[0] for c in corr.columns]
        fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                        title="Correlación entre variables numéricas")
        st.plotly_chart(fig)

    fig = px.scatter(datos, x="frecuencia_compras", y="gasto_total", color="recencia_dias",
                     color_continuous_scale="Viridis_r", opacity=0.75, hover_data=["id_cliente", "canal_preferido"],
                     labels={c: ETQ.get(c, c) for c in NUMERICAS},
                     title="Relación frecuencia-gasto (color = días desde la última compra)")
    st.plotly_chart(fig)

    st.subheader("Estadísticas descriptivas del dataset (clientes filtrados)")
    descripcion = datos[NUMERICAS].describe().T.rename(index=ETQ)
    st.dataframe(descripcion.style.format("{:,.2f}"))

    with st.expander("Ver registros del dataset limpio"):
        st.dataframe(datos.drop(columns=["cluster"]), hide_index=True)
        st.download_button("Descargar CSV filtrado", datos.to_csv(index=False).encode("utf-8"),
                           file_name="clientes_filtrados.csv", mime="text/csv")

    with st.expander("Limpieza aplicada al dataset crudo"):
        crudo = res["dataset_crudo"]
        st.markdown(
            f"El archivo crudo tenía **{crudo['filas']} registros**, **{crudo['nulos_totales']} celdas nulas**, "
            f"**{crudo['duplicados_exactos']} duplicados** y **{crudo['montos_como_texto']} montos guardados como "
            f"texto**. Tras la limpieza quedaron **{res['registros_limpios']} clientes** sin nulos ni duplicados."
        )
        st.dataframe(pd.DataFrame(res["bitacora_limpieza"]), hide_index=True)


# ===========================================================================
# PÁGINA 2: SEGMENTACIÓN K-MEANS
# ===========================================================================
def pagina_segmentacion(datos: pd.DataFrame) -> None:
    st.header("Página 2 · Segmentación mediante K-Means")
    sel = res["seleccion_k"]
    met = res["metricas_modelo_final"]

    vip = next((c["nombre"] for c in clusters_info if c["clave"] == "alto_valor"), ORDEN[0])
    riesgo = next((c["nombre"] for c in clusters_info if c["clave"] == "riesgo"), None)
    conteo = datos["cluster_nombre"].value_counts()
    gasto_vip = datos.loc[datos["cluster_nombre"] == vip, "gasto_total"].sum() / datos["gasto_total"].sum() * 100

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Clústeres (K óptimo)", sel["k_optimo"], f"silhouette = {met['silhouette']:.3f}", delta_color="off",
              border=True)
    mayor = conteo.idxmax()
    id_mayor = next(c["cluster"] for c in clusters_info if c["nombre"] == mayor)
    k2.metric("Segmento más numeroso", f"{conteo.max():,} clientes",
              f"C{id_mayor} · {conteo.max() / conteo.sum() * 100:.1f}% del filtro", delta_color="off",
              help=mayor, border=True)
    k3.metric("Gasto generado por VIP", f"{gasto_vip:.1f}%",
              f"{(datos['cluster_nombre'] == vip).mean() * 100:.1f}% de los clientes", delta_color="off", border=True)
    if riesgo:
        en_riesgo = datos[datos["cluster_nombre"] == riesgo]
        k4.metric("Clientes en riesgo", f"{len(en_riesgo):,}", f"{moneda(en_riesgo['gasto_total'].sum())} en juego",
                  delta_color="inverse", border=True)
    else:
        k4.metric("Recencia promedio", f"{datos['recencia_dias'].mean():.0f} días", border=True)

    # --- Distribución y dispersión ---------------------------------------------
    c1, c2 = st.columns([2, 3])
    with c1:
        dist = conteo.reindex([n for n in ORDEN if n in conteo.index]).reset_index()
        dist.columns = ["cluster_nombre", "clientes"]
        dist["porcentaje"] = dist["clientes"] / dist["clientes"].sum() * 100
        fig = px.bar(dist, x="clientes", y="cluster_nombre", orientation="h", color="cluster_nombre",
                     color_discrete_map=MAPA_COLOR, text=dist.apply(
                         lambda r: f"{r.clientes} ({r.porcentaje:.1f}%)", axis=1),
                     title="Distribución de registros por clúster",
                     labels={"cluster_nombre": "", "clientes": "Clientes"})
        fig.update_layout(showlegend=False, height=470, yaxis={"categoryorder": "array", "categoryarray": ORDEN[::-1]})
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(fig)
    with c2:
        tab2d, tab3d = st.tabs(["Dispersión 2D con centroides", "Vista 3D (RFM)"])
        with tab2d:
            ejes = RFM + ["ticket_promedio"]
            a, b = st.columns(2)
            eje_x = a.selectbox("Eje X", ejes, index=0, format_func=lambda v: ETQ[v])
            eje_y = b.selectbox("Eje Y", ejes, index=1, format_func=lambda v: ETQ[v])
            fig = px.scatter(datos, x=eje_x, y=eje_y, color="cluster_nombre", color_discrete_map=MAPA_COLOR,
                             category_orders={"cluster_nombre": ORDEN}, opacity=0.65,
                             hover_data=["id_cliente", "canal_preferido"], labels={**ETQ, "cluster_nombre": "Clúster"})
            first_centroid = True
            for info in clusters_info:
                if info["nombre"] not in f_clusters:
                    continue
                centro = info["centroide_original"]
                cx = centro.get(eje_x, df.loc[df["cluster"] == info["cluster"], eje_x].mean())
                cy = centro.get(eje_y, df.loc[df["cluster"] == info["cluster"], eje_y].mean())
                fig.add_trace(go.Scatter(x=[cx], y=[cy], mode="markers+text", text=[f"C{info['cluster']}"],
                                         textposition="top right", name="Centroides (modelo completo)",
                                         legendgroup="centroides_completos", showlegend=first_centroid,
                                         marker=dict(symbol="x", size=18, color="black",
                                                     line=dict(width=2, color="white")),
                                         hovertext=f"Centroide C{info['cluster']} (modelo completo): {info['nombre']}",
                                         hoverinfo="text"))
                first_centroid = False
            fig.update_layout(height=430, legend=dict(orientation="h", y=-0.25))
            st.plotly_chart(fig)
            st.caption("Nota: Las 'X' negras son los centroides del modelo completo (900 clientes) y permanecen fijos como referencia teórica aunque se apliquen filtros a los registros.")
        with tab3d:
            fig = px.scatter_3d(datos, x="recencia_dias", y="frecuencia_compras", z="gasto_total",
                                color="cluster_nombre", color_discrete_map=MAPA_COLOR, opacity=0.7,
                                category_orders={"cluster_nombre": ORDEN}, labels={**ETQ, "cluster_nombre": "Clúster"})
            fig.update_traces(marker_size=3)
            first_centroid_3d = True
            for info in clusters_info:
                if info["nombre"] not in f_clusters:
                    continue
                centro = info["centroide_original"]
                cx = centro.get("recencia_dias", df.loc[df["cluster"] == info["cluster"], "recencia_dias"].mean())
                cy = centro.get("frecuencia_compras", df.loc[df["cluster"] == info["cluster"], "frecuencia_compras"].mean())
                cz = centro.get("gasto_total", df.loc[df["cluster"] == info["cluster"], "gasto_total"].mean())
                fig.add_trace(go.Scatter3d(x=[cx], y=[cy], z=[cz], mode="markers+text", text=[f"C{info['cluster']}"],
                                           textposition="top center", name="Centroides (modelo completo)",
                                           legendgroup="centroides_completos_3d", showlegend=first_centroid_3d,
                                           marker=dict(symbol="x", size=8, color="black",
                                                       line=dict(width=3, color="white")),
                                           hovertext=f"Centroide C{info['cluster']} (modelo completo): {info['nombre']}",
                                           hoverinfo="text"))
                first_centroid_3d = False
            fig.update_layout(height=520, legend=dict(orientation="h", y=-0.05))
            st.plotly_chart(fig)
            st.caption("Nota: Las marcas 'X' negras en la vista 3D corresponden a los centroides del modelo completo.")

    # --- Comparación de características -----------------------------------------
    st.subheader("Comparación de características entre grupos")
    c3, c4 = st.columns(2)
    with c3:
        variable = st.selectbox("Variable para comparar", NUMERICAS, index=1, format_func=lambda v: ETQ.get(v, v))
        fig = px.box(datos, x="cluster_nombre", y=variable, color="cluster_nombre", color_discrete_map=MAPA_COLOR,
                     category_orders={"cluster_nombre": ORDEN}, labels={**ETQ, "cluster_nombre": ""},
                     title=f"{ETQ.get(variable, variable)} por clúster")
        fig.update_layout(showlegend=False, height=450)
        st.plotly_chart(fig)
    with c4:
        perfil = datos.groupby("cluster_nombre")[RFM + ["ticket_promedio", "satisfaccion"]].mean()
        indice = (perfil / df[RFM + ["ticket_promedio", "satisfaccion"]].mean() * 100).round(0)
        indice = indice.reindex([n for n in ORDEN if n in indice.index]).reset_index().melt(
            id_vars="cluster_nombre", var_name="variable", value_name="indice")
        indice["variable"] = indice["variable"].map(lambda v: ETQ[v].split(" (")[0])
        fig = px.bar(indice, x="variable", y="indice", color="cluster_nombre", barmode="group",
                     color_discrete_map=MAPA_COLOR, title="Perfil promedio por clúster (100 = promedio general)",
                     labels={"indice": "Índice vs. promedio", "variable": "", "cluster_nombre": "Clúster"})
        fig.add_hline(y=100, line_dash="dash", line_color="gray")
        fig.update_layout(height=450, legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig)

    mezcla = (pd.crosstab(datos["cluster_nombre"], datos["canal_preferido"], normalize="index") * 100).round(1)
    mezcla = mezcla.reindex([n for n in ORDEN if n in mezcla.index]).reset_index().melt(
        id_vars="cluster_nombre", var_name="canal", value_name="porcentaje")
    fig = px.bar(mezcla, y="cluster_nombre", x="porcentaje", color="canal", orientation="h", text_auto=".0f",
                 title="Canal preferido dentro de cada clúster (%)", color_discrete_sequence=px.colors.qualitative.Set2,
                 labels={"cluster_nombre": "", "porcentaje": "% de clientes", "canal": "Canal"})
    fig.update_layout(height=330, yaxis={"categoryorder": "array", "categoryarray": ORDEN[::-1]})
    st.plotly_chart(fig)

    # --- Tabla de estadísticas descriptivas -------------------------------------
    st.subheader("Estadísticas descriptivas por clúster")
    agregados = {
        "Clientes": ("id_cliente", "count"),
        "Frecuencia media": ("frecuencia_compras", "mean"),
        "Frecuencia desv.": ("frecuencia_compras", "std"),
        "Gasto medio": ("gasto_total", "mean"),
        "Gasto mediano": ("gasto_total", "median"),
        "Gasto desv.": ("gasto_total", "std"),
        "Recencia media": ("recencia_dias", "mean"),
        "Recencia desv.": ("recencia_dias", "std"),
        "Ticket medio": ("ticket_promedio", "mean"),
        "Edad media": ("edad", "mean"),
        "Satisfacción media": ("satisfaccion", "mean"),
        "Gasto acumulado": ("gasto_total", "sum"),
    }
    tabla = datos.groupby("cluster_nombre").agg(**agregados).reindex([n for n in ORDEN if n in conteo.index])
    tabla.insert(1, "% clientes", tabla["Clientes"] / tabla["Clientes"].sum() * 100)
    tabla["% del gasto"] = tabla["Gasto acumulado"] / tabla["Gasto acumulado"].sum() * 100
    formatos = {c: "{:,.2f}" for c in tabla.columns}
    formatos.update({"Clientes": "{:,.0f}", "% clientes": "{:.1f}%", "% del gasto": "{:.1f}%",
                     "Gasto medio": "${:,.0f}", "Gasto mediano": "${:,.0f}", "Gasto desv.": "${:,.0f}",
                     "Ticket medio": "${:,.0f}", "Gasto acumulado": "${:,.0f}"})
    st.dataframe(tabla.style.format(formatos))

    with st.expander("Ver describe() completo de una variable por clúster"):
        var_desc = st.selectbox("Variable", NUMERICAS, format_func=lambda v: ETQ.get(v, v), key="desc")
        st.dataframe(datos.groupby("cluster_nombre")[var_desc].describe().reindex(tabla.index).style.format("{:,.2f}"))

    # --- Resultados del modelo -----------------------------------------------------
    st.subheader("Resultados del modelo")
    c5, c6 = st.columns(2)
    with c5:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=metricas_k["k"], y=metricas_k["inercia"], mode="lines+markers", name="Inercia",
                                 line=dict(color="#2c7fb8", width=3)))
        fig.add_vline(x=sel["k_codo"], line_dash="dash", line_color="#d95f02", annotation_text=f"Codo K={sel['k_codo']}")
        fig.update_layout(title="Método del codo", xaxis_title="K", yaxis_title="Inercia", height=360)
        st.plotly_chart(fig)
    with c6:
        fig = px.bar(metricas_k, x="k", y="silhouette", text_auto=".3f", title="Silhouette por número de clústeres",
                     color=metricas_k["k"].eq(sel["k_silhouette"]).map({True: "K óptimo", False: "Otros K"}),
                     color_discrete_map={"K óptimo": "#1b9e77", "Otros K": "#bdbdbd"},
                     labels={"k": "K", "silhouette": "Silhouette", "color": ""})
        fig.update_layout(height=360)
        st.plotly_chart(fig)
    st.info(f"**Justificación del K óptimo:** {sel['justificacion']}")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Silhouette", f"{met['silhouette']:.3f}", help="De -1 a 1; más alto = grupos mejor separados.")
    m2.metric("Davies-Bouldin", f"{met['davies_bouldin']:.3f}", help="Más bajo = grupos más compactos y separados.")
    m3.metric("Calinski-Harabasz", f"{met['calinski_harabasz']:,.0f}", help="Más alto = mejor definición.")
    m4.metric("Inercia (WCSS)", f"{met['inercia']:,.1f}", help="Suma de distancias al cuadrado a su centroide.")

    with st.expander("Centroides del modelo final", expanded=False):
        centros = pd.DataFrame([{"Clúster": f"C{c['cluster']} - {c['nombre']}", **c["centroide_original"]}
                                for c in clusters_info]).rename(columns=ETQ)
        st.dataframe(centros.style.format({ETQ[v]: "{:,.2f}" for v in RFM}), hide_index=True)

    st.markdown("**Comparación de configuraciones del modelo**")
    comp = pd.DataFrame(res["comparacion_configuraciones"]).rename(columns={
        "configuracion": "Configuración", "k": "K", "escalado": "Escalado", "silhouette": "Silhouette",
        "davies_bouldin": "Davies-Bouldin", "cluster_mas_chico": "Clúster más chico",
        "cluster_mas_grande": "Clúster más grande", "coincidencia_con_A_ARI": "Coincidencia con A (ARI)"})
    st.dataframe(comp.style.format({"Silhouette": "{:.3f}", "Davies-Bouldin": "{:.3f}",
                                    "Coincidencia con A (ARI)": "{:.3f}"}), hide_index=True)
    for texto in res["comparacion_texto"]:
        st.markdown(f"- {texto}")
    imagen_comp = config.FIG_DIR / "15_comparacion_configuraciones.png"
    if imagen_comp.exists():
        with st.expander("Ver gráfica de comparación de configuraciones"):
            st.image(str(imagen_comp))

    # --- Descripción de los grupos -------------------------------------------------
    st.subheader("Descripción de los grupos")
    columnas = st.columns(2)
    for i, info in enumerate(clusters_info):
        with columnas[i % 2]:
            with st.container(border=True):
                st.markdown(
                    f"<h4 style='margin-bottom:0;color:{MAPA_COLOR[info['nombre']]}'>"
                    f"C{info['cluster']} · {info['nombre']}</h4>",
                    unsafe_allow_html=True,
                )
                st.caption(f"{info['clientes']} clientes · {info['porcentaje']:.1f}% del total")
                st.write(info["descripcion"])

    # --- Hallazgos y recomendaciones ---------------------------------------------
    st.subheader("Principales hallazgos y recomendaciones")
    h, r = st.columns(2)
    with h:
        st.markdown("#### Hallazgos")
        for i, texto in enumerate(res["hallazgos"], 1):
            st.markdown(f"{i}. {texto}")
    with r:
        st.markdown("#### Recomendaciones")
        for i, texto in enumerate(res["recomendaciones"], 1):
            st.markdown(f"{i}. {texto}")
    with st.expander("Limitaciones del modelo"):
        for texto in res["limitaciones"]:
            st.markdown(f"- {texto}")


if pagina.startswith("Página 1"):
    pagina_analisis_general(filtrado)
else:
    pagina_segmentacion(filtrado)
