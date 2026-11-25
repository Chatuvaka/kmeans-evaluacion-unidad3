# Proyecto tercer unidad: Segmentación de clientes con K-Means

Segmentación de clientes por comportamiento de compra (**recencia, frecuencia y monto de gasto – RFM**) con el algoritmo **K-Means**, y un **dashboard interactivo en Streamlit** para explorar los resultados y apoyar estrategias de retención y promoción basadas en datos.

| | |
|---|---|
| **Institución** | Universidad Tecnológica de San Luis Río Colorado (UTSLRC BIS) |
| **Carrera** | Ingeniería en Desarrollo y Gestión de Software ({idgs}) |
| **Materia** | Extracción de Conocimiento en Base de Datos |
| **Docente** | Prof. Julia Elizabeth García Herrera |
| **Integrantes** | Jesus Rodolfo Lopez Gamez · Josue Misraim Valenzuela Verdugo · Axel Alan Jimenez Jaramillo |
| **Grupo:** | IDGS 9 - 3 |
| **Fecha** | 24/11/2026 |
| **Repositorio GitHub** | https://github.com/Chatuvaka/kmeans-evaluacion-unidad3 |

## Descripción

La empresa trata a todos sus clientes por igual y no sabe quiénes generan la mayor parte del ingreso, quiénes dejaron de comprar ni quiénes podrían crecer. Este proyecto:

1. **Genera** un dataset de 900 clientes con 10 variables (+15 duplicados) que incluye errores reales a propósito: nulos, duplicados, categorías mal escritas, montos guardados como texto, edades imposibles y gastos extremos.
2. **Explora y limpia** los datos, trata atípicos, codifica categorías y escala las variables con `StandardScaler`.
3. **Evalúa K = 2 a 8** con el método del codo, el coeficiente de silhouette y Davies-Bouldin, y entrena el modelo final.
4. **Interpreta** los clústeres, les asigna nombres descriptivos, compara dos configuraciones del modelo y redacta hallazgos, recomendaciones y limitaciones.
5. **Presenta** todo en un dashboard de dos páginas con KPI, filtros y gráficas interactivas.

### Resultado principal (K = 4, silhouette = 0.585)

| Clúster | Segmento | Clientes | % del gasto |
|---|---|---|---|
| C0 | Clientes VIP de alto valor | 105 (11.7 %) | 45.6 % |
| C1 | Clientes leales regulares | 248 (27.6 %) | 31.6 % |
| C2 | Clientes ocasionales de bajo gasto | 341 (37.9 %) | 9.5 % |
| C3 | Clientes en riesgo de abandono | 206 (22.9 %) | 13.3 % |

## Herramientas

- **Python 3.10+**
- **Pandas** y **NumPy**: carga, limpieza y transformación de datos
- **Scikit-learn**: `StandardScaler`, `KMeans`, métricas de silhouette, Davies-Bouldin, Calinski-Harabasz, ARI y PCA
- **Matplotlib** y **Seaborn**: gráficas estáticas del análisis (`outputs/figures/`)
- **Streamlit**: dashboard interactivo
- **Plotly**: gráficas interactivas dentro del dashboard

## Estructura de carpetas

```
proyecto_tercer_unidad_kmeans/
├── app.py                          # Dashboard interactivo Streamlit (2 páginas)
├── requirements.txt                # Dependencias del proyecto
├── README.md                       # Documentación principal e instrucciones
├── .gitignore
├── data/
│   ├── raw/
│   │   └── clientes_segmentacion.csv        # Dataset crudo (915 registros, 10 variables)
│   └── processed/
│       ├── clientes_segmentados.csv         # Dataset limpio + cluster + cluster_nombre
│       └── clientes_limpios_codificados.csv # Dataset limpio con One-Hot Encoding
├── src/
│   ├── __init__.py
│   ├── config.py                   # Rutas, semilla y parámetros generales
│   ├── generar_dataset.py          # Generador de datos sintéticos (np.random.seed(42))
│   ├── analisis_kmeans.py          # Exploración, limpieza, escalado, selección K y K-Means
│   ├── interpretacion.py           # Perfiles, nombres, hallazgos y recomendaciones
│   └── main.py                     # Pipeline automatizado de ejecución completa
├── scripts/
│   ├── tomar_capturas.py           # Captura automatizada de pantallas con Selenium
│   └── generar_pdf.py              # Compilador a PDF profesional vía Chrome DevTools
├── outputs/
│   ├── figures/                    # 15 gráficas PNG de análisis + capturas del dashboard
│   ├── tables/                     # Tablas CSV de resultados, métricas y bitácoras
│   ├── resultados_modelo.json      # Resultados consumidos por el dashboard
│   └── salida_pipeline.txt         # Bitácora textual de salida de consola
└── docs/
    ├── portada.png                 # Portada institucional oficial UTSLRC
    ├── reporte_base.md             # Reporte técnico completo (8 apartados)
    └── reporte_segmentacion_kmeans.pdf # Documento final para entrega universitaria
```

## Instrucciones de ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/Chatuvaka/kmeans-evaluacion-unidad3.git
cd proyecto_tercer_unidad_kmeans
```

### 2. Crear y activar un entorno virtual (recomendado)

Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. (Opcional) Regenerar el dataset crudo

El repositorio ya incluye `data/raw/clientes_segmentacion.csv`. Para volver a generarlo (siempre produce los mismos datos gracias a la semilla fija):

```bash
python src/generar_dataset.py
```

### 5. Ejecutar el pipeline de análisis

```bash
python src/main.py
```

Esto ejecuta la exploración, limpieza, escalado, selección de K, modelo final, comparación e interpretación. Muestra todo en consola, lo guarda en `outputs/salida_pipeline.txt` y genera las figuras, tablas, `data/processed/clientes_segmentados.csv` y `outputs/resultados_modelo.json`.

> Usa `python src/main.py --regenerar` para generar el dataset crudo y ejecutar el pipeline en un solo paso.

### 6. Lanzar el dashboard

Desde la carpeta raíz del proyecto:

```bash
streamlit run app.py
```

Se abrirá en el navegador en `http://localhost:8501`.

## Contenido del dashboard

**Barra lateral:** selector de página y 4 filtros interactivos (clúster, canal preferido, rango de gasto y rango de frecuencia), que aplican a ambas páginas.

**Página 1 – Análisis general:** 4 KPI (clientes, gasto total, frecuencia promedio y recencia promedio), histograma de la variable elegida, clientes por canal y región, mapa de correlación, dispersión frecuencia-gasto, estadísticas descriptivas, registros descargables y resumen de la limpieza.

**Página 2 – Segmentación mediante K-Means:** 4 KPI del modelo, distribución de registros por clúster, dispersión 2D con centroides y vista 3D, boxplot por clúster, perfil comparativo, canal por clúster, tabla de estadísticas descriptivas por clúster, gráficas del codo y silhouette, comparación de configuraciones, descripción de cada grupo, hallazgos, recomendaciones y limitaciones.

## Metodología resumida

| Etapa | Detalle |
|---|---|
| Variables de agrupamiento | `recencia_dias`, `frecuencia_compras`, `gasto_total` (RFM) |
| Limpieza | Estandarización de texto, conversión de tipos, eliminación de duplicados, valores inválidos a nulos, imputación (mediana/moda), recorte de atípicos extremos (3×IQR y percentil 99) |
| Escalado | `StandardScaler` (media 0, desviación 1) |
| Selección de K | K = 2…8 con inercia (codo), silhouette y Davies-Bouldin → **K = 4** |
| Modelo | `KMeans(n_clusters=4, n_init=10, random_state=42).fit_predict()` |
| Comparación | A) K=4 escalado vs. B) K=3 escalado vs. C) K=4 sin escalar |

## Reporte y Entrega

- `docs/reporte_segmentacion_kmeans.pdf`: Documento PDF profesional listo para entrega universitaria con la portada institucional oficial de UTSLRC, estructurado exactamente en los 8 apartados de la rúbrica y con todas las capturas reales integradas.
- `docs/reporte_base.md`: Documento Markdown fuente que contiene el texto completo, tablas y referencias visuales.
- `scripts/generar_pdf.py`: Script reproducible para compilar el reporte a PDF mediante Chrome DevTools Protocol.
