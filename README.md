# GIS_PrediosReport: Generador de Fichas Catastrales en PDF

Este repositorio contiene un script de Python (`predio_report.py`) diseñado para automatizar la generación de informes técnicos o fichas catastrales para predios urbanos. A partir de un archivo de datos geoespaciales (como un Shapefile o GeoJSON), el script extrae la información de un predio específico y crea un informe profesional en formato PDF de varias páginas.

El proyecto soluciona la necesidad de crear documentación técnica estandarizada de manera rápida y eficiente, reduciendo el trabajo manual y asegurando la consistencia de los datos.

## 🌟 Características Principales

*   **Generación de PDF Profesional:** Crea documentos PDF con una estructura clara, incluyendo portada, encabezados y pies de página.
*   **Portada Dinámica:** Incluye una portada profesional con título, código catastral, fecha y un logo personalizable.
*   **Datos del Predio:** Extrae y presenta información clave como la ubicación, el uso de la edificación, el área según escritura y los datos de linderos y colindantes.
*   **Tabla de Coordenadas:** Genera automáticamente una tabla con los vértices del polígono del predio, mostrando coordenadas tanto geográficas (Lat/Lon) como proyectadas (UTM). El script calcula la zona UTM apropiada de forma automática.
*   **Información Geométrica:** Muestra el área y perímetro calculados directamente desde la geometría del dato GIS.
*   **Integración de Mapa:** Permite incrustar fácilmente una imagen de un mapa o plano de ubicación del predio.
*   **Personalización:** El contenido, los títulos y la información del autor son fácilmente modificables dentro del script.

## 📄 Ejemplo de Resultado

El script genera un documento PDF como el que se muestra a continuación.

*(Recomendación: Genera un informe de ejemplo, haz una captura de pantalla y reemplaza la siguiente línea con la imagen para que los visitantes puedan ver el resultado final).*

![Ejemplo de Reporte](assets/report_example.png)

## ⚙️ Instalación

Para utilizar este script, necesitarás Python 3.7 o superior. Se recomienda encarecidamente trabajar dentro de un entorno virtual.

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/tu-usuario/GIS_PrediosReport.git
    cd GIS_PrediosReport
    ```
    *(Reemplaza `tu-usuario` con tu nombre de usuario de GitHub)*

2.  **Crea y activa un entorno virtual (recomendado):**
    ```bash
    # En Windows
    python -m venv venv
    .\venv\Scripts\activate

    # En macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instala las dependencias:**
    El archivo `requirements.txt` contiene todas las librerías necesarias.
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Uso

El uso principal se realiza a través de la función `generar_informe_predio_pdf` dentro del script `predio_report.py`.

1.  Asegúrate de tener tus datos de predios en un formato compatible con GeoPandas (Shapefile, GeoJSON, etc.). Los datos deben estar en un sistema de coordenadas geográficas (WGS 84, EPSG:4326).
2.  Crea un script de Python (por ejemplo, `ejecutar_reporte.py`) para llamar a la función.

### Ejemplo de script `ejecutar_reporte.py`:

```python
import geopandas as gpd
from predio_report import generar_informe_predio_pdf
from datetime import datetime

print("Iniciando la generación del informe...")

# 1. Cargar los datos geoespaciales
try:
    ruta_datos = "data/predios.shp" # <-- CAMBIA ESTO
    gdf = gpd.read_file(ruta_datos)
    print(f"Datos cargados desde {ruta_datos}. CRS original: {gdf.crs}")
except Exception as e:
    print(f"Error al cargar los datos: {e}")
    exit()

# 2. Definir los parámetros del informe
codigo_catastral_a_buscar = "0901-0101-001-01" # <-- CAMBIA ESTO
archivo_salida_pdf = "Ficha_Tecnica_Predio.pdf"
ruta_logo = "assets/logo.png" # (Opcional)
ruta_mapa = "assets/mapa_predio.png" # (Opcional)
fecha_actual = datetime.now()
autor_informe = "Tu Nombre o Empresa"

# 3. Llamar a la función para generar el informe
success, message = generar_informe_predio_pdf(
    gdf=gdf,
    codcat=codigo_catastral_a_buscar,
    output_filename=archivo_salida_pdf,
    autor=autor_informe,
    fecha_reporte=fecha_actual,
    logo_path=ruta_logo,
    map_image_path=ruta_mapa
)
```

## Parámetros de la función generar_informe_predio_pdf:
*   `gdf` (GeoDataFrame): El GeoDataFrame cargado con los datos de los predios.
*   `codcat` (str): El código catastral exacto del predio a reportar.
*   `output_filename` (str): El nombre del archivo PDF que se generará.
*   `autor` (str, opcional): El nombre del autor o la compañía que elabora el informe.
*   `fecha_reporte` (datetime/str, opcional): La fecha para el informe. Si se omite, se usa la fecha actual.
*   `logo_path` (str, opcional): La ruta a una imagen de logo para la portada.
*   `map_image_path` (str, opcional): La ruta a una imagen del mapa o plano del predio.

```python
# 4. Imprimir el resultado
if success:
    print(f"Éxito: {message}")
else:
    print(f"Fallo: {message}")
```
## 📚 Dependencias
Las librerías principales utilizadas en este proyecto son:
*   `geopandas`: Para leer y manipular datos geoespaciales.
*   `pandas`: Dependencia de GeoPandas para el manejo de datos tabulares.
*   `reportlab`: Para la generación de los documentos PDF.
*   `Pillow`: Para el manejo de imágenes.
*   `PyMuPDF` (fitz): Requerido para ciertas operaciones con PDF.
*   `shapely`: Para las operaciones geométricas.
