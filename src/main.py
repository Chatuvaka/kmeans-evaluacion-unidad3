"""
Punto de entrada del pipeline completo.

Ejecuta en orden: generación del dataset (si no existe), exploración,
limpieza, codificación, escalado, selección de K, modelo final, gráficas,
comparación de configuraciones e interpretación. Guarda:

* data/processed/clientes_segmentados.csv   (dataset limpio + cluster + nombre)
* outputs/figures/*.png                      (15 gráficas)
* outputs/tables/*.csv                       (tablas de resultados)
* outputs/resultados_modelo.json             (resultados que consume el dashboard)
* outputs/salida_pipeline.txt                (copia de toda la salida de consola)

Uso:
    python src/main.py              # usa el CSV crudo existente (o lo genera)
    python src/main.py --regenerar  # vuelve a generar el dataset crudo
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import analisis_kmeans as ak  # noqa: E402
from src import config  # noqa: E402
from src.generar_dataset import generar_dataset  # noqa: E402
from src.interpretacion import interpretar, nombrar_clusters  # noqa: E402


class Duplicador:
    """Escribe la salida en consola y en un archivo de texto al mismo tiempo."""

    def __init__(self, *flujos):
        self.flujos = flujos

    def write(self, texto):
        for flujo in self.flujos:
            flujo.write(texto)

    def flush(self):
        for flujo in self.flujos:
            flujo.flush()


def _a_serializable(valor):
    if hasattr(valor, "item"):
        return valor.item()
    raise TypeError(f"Tipo no serializable: {type(valor)}")


def ejecutar_pipeline(regenerar: bool = False) -> dict:
    config.asegurar_directorios()

    if regenerar or not config.DATA_RAW.exists():
        generar_dataset()
        print(f"Dataset crudo generado en {config.DATA_RAW.relative_to(config.ROOT).as_posix()}")

    # 1. Exploración
    crudo = ak.cargar_datos()
    resumen_crudo = ak.explorar_datos(crudo)

    # 2. Limpieza, codificación y escalado
    limpio, bitacora = ak.limpiar_datos(crudo)
    ak.codificar_categoricas(limpio)
    X_esc, escalador, tabla_escalado = ak.escalar_variables(limpio)

    # 3. Selección de K y modelo final
    metricas_k, decision = ak.evaluar_valores_k(X_esc)
    resultado = ak.entrenar_modelo_final(X_esc, escalador, decision["k_optimo"])
    limpio["cluster"] = resultado["etiquetas"]

    # 4. Gráficas de agrupamiento y comparación de configuraciones
    nombres = {c: datos["nombre"] for c, datos in nombrar_clusters(resultado["centroides_escalados"]).items()}
    con_nombres = limpio.assign(cluster_nombre=limpio["cluster"].map(nombres))
    ak.graficar_clusters(con_nombres, X_esc, resultado, nombres)
    tabla_comp, textos_comp = ak.comparar_configuraciones(
        con_nombres, X_esc, decision["k_optimo"], resultado["etiquetas"], nombres
    )

    # 5. Interpretación (nombres descriptivos, perfiles, hallazgos)
    n_imputados = int(bitacora.loc[bitacora["paso"].str.startswith("Imputar"), "registros_afectados"].sum())
    interpretacion = interpretar(limpio, resultado, decision, n_imputados)
    segmentado = interpretacion["df"]

    # 6. Guardar dataset final
    columnas = ["id_cliente", "edad", "genero", "region", "canal_preferido", "antiguedad_meses",
                "frecuencia_compras", "gasto_total", "recencia_dias", "ticket_promedio", "satisfaccion",
                "cluster", "cluster_nombre"]
    segmentado[columnas].to_csv(config.DATA_PROCESSED, index=False, encoding="utf-8")

    # 7. Guardar resultados para el dashboard
    perfil = interpretacion["perfil"]
    clusters_json = []
    for c in range(decision["k_optimo"]):
        clusters_json.append(
            {
                "cluster": c,
                "clave": interpretacion["info"][c]["clave"],
                "nombre": nombres[c],
                "descripcion": interpretacion["descripciones"][c],
                "clientes": int(perfil.loc[c, "clientes"]),
                "porcentaje": round(float(perfil.loc[c, "porcentaje_clientes"]), 2),
                "centroide_original": resultado["centroides_originales"].loc[c].round(2).to_dict(),
                "centroide_escalado": resultado["centroides_escalados"].loc[c].round(4).to_dict(),
            }
        )

    resultados = {
        "proyecto": "Proyecto tercer unidad - Segmentación de clientes con K-Means",
        "fecha_ejecucion": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "dataset_crudo": resumen_crudo,
        "registros_limpios": int(len(segmentado)),
        "variables_cluster": config.VARIABLES_CLUSTER,
        "k_evaluados": config.K_RANGE,
        "seleccion_k": decision,
        "metricas_modelo_final": resultado["metricas"],
        "escalado": tabla_escalado.round(4).to_dict(orient="records"),
        "bitacora_limpieza": bitacora.to_dict(orient="records"),
        "clusters": clusters_json,
        "comparacion_configuraciones": tabla_comp.round(4).to_dict(orient="records"),
        "comparacion_texto": textos_comp,
        "hallazgos": interpretacion["hallazgos"],
        "recomendaciones": interpretacion["recomendaciones"],
        "limitaciones": interpretacion["limitaciones"],
    }
    with open(config.RESULTS_JSON, "w", encoding="utf-8") as archivo:
        json.dump(resultados, archivo, ensure_ascii=False, indent=2, default=_a_serializable)

    ak.titulo("PIPELINE TERMINADO")
    print(f"Dataset segmentado: {config.DATA_PROCESSED.relative_to(config.ROOT).as_posix()}")
    print(f"Resultados del modelo: {config.RESULTS_JSON.relative_to(config.ROOT).as_posix()}")
    print(f"Figuras: {config.FIG_DIR.relative_to(config.ROOT).as_posix()}/ ({len(list(config.FIG_DIR.glob('*.png')))} archivos)")
    print("Siguiente paso: streamlit run app.py")
    return resultados


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline de segmentación de clientes con K-Means")
    parser.add_argument("--regenerar", action="store_true", help="vuelve a generar el dataset crudo")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    config.asegurar_directorios()
    with open(config.CONSOLE_LOG, "w", encoding="utf-8") as log:
        salida_original = sys.stdout
        sys.stdout = Duplicador(salida_original, log)
        try:
            ejecutar_pipeline(regenerar=args.regenerar)
        finally:
            sys.stdout = salida_original


if __name__ == "__main__":
    main()
