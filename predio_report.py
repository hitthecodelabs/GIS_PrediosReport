# -*- coding: utf-8 -*-

# --- IMPORTACIÓN DE LIBRERÍAS ---
import os
import fitz  # PyMuPDF, usado para manipulación de PDF (aunque no se usa en este script, se mantiene por si es parte del proyecto)
import locale
import telegram # No se usa en este script, pero se mantiene
from glob import glob # No se usa en este script, pero se mantiene
from datetime import datetime
from telegram.error import TelegramError # No se usa en este script, pero se mantiene

# --- LIBRERÍAS REQUERIDAS ---
import pandas as pd
import geopandas as gpd
import plotly.express as px # No se usa en este script, pero se mantiene
import plotly.graph_objects as go # No se usa en este script, pero se mantiene

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, KeepTogether, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.units import cm, inch
from reportlab.lib.colors import navy, black, gray, Color
from PIL import Image as PILImage
from reportlab.lib import colors
from shapely.geometry import Polygon, MultiPolygon # No se usa directamente, pero es dependencia de GeoPandas

# --- CONFIGURACIÓN REGIONAL PARA FECHAS ---
# Intenta establecer el localismo a español para obtener los nombres de los meses.
# Esto es importante para que la fecha en el reporte aparezca como "14 de Julio de 2025".
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252') # Alternativa para Windows
    except locale.Error:
        print("Advertencia: No se pudo establecer el localismo a español. Los meses pueden aparecer en inglés.")


def num_a_letras(numero):
    """Convierte un número a un formato de texto específico.

    Toma un valor numérico y lo formatea en una cadena de texto del tipo
    "Entero con Decimales/100", comúnmente usado en documentos legales
    o técnicos para describir áreas o valores monetarios.

    Args:
        numero (float o int): El número a convertir.

    Returns:
        str: El número formateado como texto (ej: "123 con 45/100") o
             un mensaje de error si la entrada no es válida.
    """
    try:
        # Intenta convertir la entrada a un número flotante.
        numero_float = float(numero)
        # Separa la parte entera y la decimal.
        entero = int(numero_float)
        # Calcula los dos decimales redondeando correctamente.
        decimal = int(round((numero_float - entero) * 100))
        # Devuelve la cadena formateada.
        return f"{entero} con {decimal:02d}/100"
    except (ValueError, TypeError):
        # Si la conversión falla, devuelve un mensaje de error.
        return "Valor inválido"

def portada_canvas(canvas, doc):
    """Dibuja la portada del documento PDF.

    Esta función es utilizada como un 'callback' por ReportLab durante la
    creación del PDF. Se invoca únicamente para la primera página del documento
    para dibujar elementos gráficos como bordes, títulos, y logos.

    Args:
        canvas (reportlab.pdfgen.canvas.Canvas): El objeto canvas sobre el que se dibuja.
        doc (reportlab.platypus.SimpleDocTemplate): El objeto del documento. Se usa para
            acceder a las dimensiones de la página y a parámetros personalizados
            (como el código catastral) que se le hayan adjuntado.
    """
    canvas.saveState()

    ancho, alto = doc.pagesize
    margen = 2 * cm

    # --- DIBUJAR BORDES DE PÁGINA ---
    # Se dibuja un marco doble para un aspecto más profesional.
    canvas.setStrokeColor(navy)
    canvas.setLineWidth(3) # Borde exterior grueso
    canvas.rect(margen, margen, ancho - 2 * margen, alto - 2 * margen)

    canvas.setLineWidth(1) # Borde interior más fino
    margen_interior = margen + 0.2 * cm
    canvas.rect(margen_interior, margen_interior, ancho - 2 * margen_interior, alto - 2 * margen_interior)

    # --- TÍTULOS ---
    canvas.setFont('Helvetica-Bold', 24)
    canvas.setFillColor(navy)
    canvas.drawCentredString(ancho / 2, alto * 0.65, "FICHA TÉCNICA CATASTRAL")

    canvas.setFont('Helvetica', 16)
    canvas.drawCentredString(ancho / 2, alto * 0.60, "Informe Geométrico y Documental de Predio Urbano")

    # --- LÍNEA SEPARADORA ---
    canvas.setStrokeColor(gray)
    canvas.line(ancho * 0.3, alto * 0.55, ancho * 0.7, alto * 0.55)

    # --- INFORMACIÓN DEL PREDIO (CÓDIGO CATASTRAL) ---
    # Accede a atributos personalizados adjuntados al objeto 'doc' en la función principal.
    # Esta es la manera de pasar datos dinámicos a las funciones de callback de ReportLab.
    canvas.setFont('Helvetica-Oblique', 12)
    canvas.drawCentredString(ancho / 2, alto * 0.45, "Referente al Predio con Código Catastral:")
    canvas.setFont('Helvetica-Bold', 20)
    canvas.setFillColor(black)
    canvas.drawCentredString(ancho / 2, alto * 0.40, doc.codcat_param)

    # --- INFORMACIÓN DEL AUTOR Y FECHA ---
    canvas.setFont('Helvetica', 12)
    canvas.setFillColor(black)
    canvas.drawCentredString(ancho / 2, margen + 2 * cm, "Elaborado por:")
    canvas.setFont('Helvetica-Bold', 14)
    canvas.setFillColor(navy)
    canvas.drawCentredString(ancho / 2, margen + 1.5 * cm, "Cartography Hub")
    canvas.setFont('Helvetica', 10)
    canvas.setFillColor(gray)
    canvas.drawCentredString(ancho / 2, margen + 0.5 * cm, doc.fecha_param)

    # --- LOGO (OPCIONAL) ---
    # Dibuja un logo en la parte superior si la ruta es válida.
    if doc.logo_path_param and os.path.exists(doc.logo_path_param):
        try:
            logo = Image(doc.logo_path_param, width=4*cm, height=2*cm)
            logo.hAlign = 'CENTER'
            # Dibuja el logo directamente en el canvas en una posición específica.
            logo.drawOn(canvas, ancho/2 - logo.width/2, alto - margen - logo.height - 0.5*cm)
        except Exception as e:
            print(f"Advertencia: No se pudo dibujar el logo en la portada: {e}")

    canvas.restoreState()

def footer_canvas(canvas, doc):
    """Dibuja el pie de página en cada página del documento.

    Esta función es utilizada como un 'callback' por ReportLab y se invoca
    para todas las páginas después de la primera ('onLaterPages'). Dibuja
    el número de página y un texto informativo.

    Args:
        canvas (reportlab.pdfgen.canvas.Canvas): El objeto canvas sobre el que se dibuja.
        doc (reportlab.platypus.SimpleDocTemplate): El objeto del documento, usado para
            obtener el número de página actual (`doc.page`).
    """
    canvas.saveState()
    canvas.setFont('Helvetica', 9)

    # Dibuja el número de página en la esquina inferior derecha.
    page_num_text = f"Página {doc.page}"
    canvas.drawRightString(doc.pagesize[0] - 0.75 * inch, 0.75 * inch, page_num_text)

    # Dibuja el texto informativo en la esquina inferior izquierda.
    canvas.drawString(0.75 * inch, 0.75 * inch, "Informe Confidencial - Cartography Hub")
    canvas.restoreState()

def generar_informe_predio_pdf(gdf, codcat, output_filename, autor="Cartography Hub", fecha_reporte=None, logo_path=None, map_image_path=None):
    """Genera un informe técnico completo de un predio en formato PDF.

    Esta función toma un GeoDataFrame, filtra un predio específico por su código
    catastral y crea un informe PDF profesional de varias páginas que incluye:
    una portada, datos de identificación, linderos, tabla de coordenadas,
    mapa del predio y observaciones.

    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame que contiene los datos de los predios.
            Debe tener una columna 'Codigo_Cat' y una geometría válida.
        codcat (str): El código catastral del predio a buscar en el GeoDataFrame.
        output_filename (str): La ruta y nombre del archivo PDF a generar (ej: "informe.pdf").
        autor (str, optional): Nombre del autor del informe. Defaults to "Cartography Hub".
        fecha_reporte (datetime.date or str, optional): La fecha para el informe.
            Si es una cadena, debe estar en formato 'YYYY-MM-DD'. Si es None, se
            usa la fecha actual. Defaults to None.
        logo_path (str, optional): Ruta al archivo de imagen del logo para la portada
            y el encabezado. Defaults to None.
        map_image_path (str, optional): Ruta a una imagen del mapa del predio para
            incluir en el informe. Defaults to None.

    Returns:
        tuple[bool, str]: Una tupla donde el primer elemento es True si la
                         generación fue exitosa y False en caso contrario. El segundo
                         elemento es un mensaje descriptivo del resultado.
    """
    # --- 1. VALIDACIÓN DE DATOS Y EXTRACCIÓN DEL PREDIO ---
    # Asegura que los datos de entrada sean correctos antes de procesar.
    if not isinstance(gdf, gpd.GeoDataFrame):
        return False, "Error: El primer argumento debe ser un GeoDataFrame."
    if 'Codigo_Cat' not in gdf.columns:
        return False, "Error: El GeoDataFrame no contiene la columna 'Codigo_Cat'."

    # Filtra el GeoDataFrame para obtener solo la fila del predio de interés.
    gdf_filtrado = gdf[gdf['Codigo_Cat'] == codcat].copy()
    if gdf_filtrado.empty:
        return False, f"Error: No se encontró ningún predio con el Código Catastral: {codcat}"

    # Extrae la primera (y única) fila de datos del predio.
    predio_data = gdf_filtrado.iloc[0]

    # --- 2. FORMATEO DE FECHA ---
    # Procesa la fecha de entrada para mostrarla en un formato legible.
    if fecha_reporte is None:
        fecha_dt = datetime.now()
    elif isinstance(fecha_reporte, str):
        try:
            fecha_dt = datetime.strptime(fecha_reporte, "%Y-%m-%d")
        except ValueError:
            print("Advertencia: Formato de fecha no reconocido (se esperaba YYYY-MM-DD). Usando fecha actual.")
            fecha_dt = datetime.now()
    elif hasattr(fecha_reporte, 'strftime'): # Comprueba si es un objeto de fecha/datetime
         fecha_dt = fecha_reporte
    else:
         print("Advertencia: Tipo de fecha no reconocido. Usando fecha actual.")
         fecha_dt = datetime.now()
    # Formatea la fecha al español ("dd de Mes de YYYY").
    fecha_str = fecha_dt.strftime("%d de %B de %Y").capitalize()

    # --- 3. EXTRACCIÓN DE ATRIBUTOS DEL PREDIO ---
    # Obtiene cada valor de las columnas del GeoDataFrame con manejo de errores y valores por defecto.
    uso_edi = predio_data.get('Uso_de_Edi', 'No especificado')
    lindero_n = predio_data.get('Lindero_No', 'No especificado')
    lindero_s = predio_data.get('Lindero_Su', 'No especificado')
    lindero_e = predio_data.get('Lindero_Es', 'No especificado')
    lindero_o = predio_data.get('Lindero_Oe', 'No especificado')
    try: long_n = float(predio_data.get('Longitud_N', 0.0))
    except (ValueError, TypeError): long_n = 0.0
    try: long_s = float(predio_data.get('Longitud_S', 0.0))
    except (ValueError, TypeError): long_s = 0.0
    try: long_e = float(predio_data.get('Longitud_E', 0.0))
    except (ValueError, TypeError): long_e = 0.0
    try: long_o = float(predio_data.get('Longitud_O', 0.0))
    except (ValueError, TypeError): long_o = 0.0
    try: area_esc = float(predio_data.get('Area_Escri', 0.0))
    except (ValueError, TypeError): area_esc = 0.0
    calle = predio_data.get('Calle', 'No especificada')
    try: shape_area = float(predio_data.get('Shape__Area', 0.0))
    except (ValueError, TypeError): shape_area = 0.0
    try: shape_len = float(predio_data.get('Shape__Length', 0.0))
    except (ValueError, TypeError): shape_len = 0.0

    # --- 4. MANEJO DEL SISTEMA DE COORDENADAS (CRS) ---
    try:
        crs_info = f"{gdf.crs.name} (EPSG:{gdf.crs.to_epsg()})" if gdf.crs else "No definido"
    except Exception:
        crs_info = str(gdf.crs) if gdf.crs else "No definido"

    try:
        # --- 5. CONFIGURACIÓN DEL DOCUMENTO PDF ---
        doc = SimpleDocTemplate(output_filename,
                                pagesize=(21*cm, 21*cm), # Formato cuadrado personalizado
                                leftMargin=1.5*cm, rightMargin=1.5*cm,
                                topMargin=2.0*cm, bottomMargin=2.5*cm)

        # Se añaden parámetros personalizados al objeto 'doc' para que estén
        # disponibles en la función de la portada (portada_canvas).
        doc.codcat_param = codcat
        doc.fecha_param = fecha_str
        doc.logo_path_param = logo_path

        # --- 6. DEFINICIÓN DE ESTILOS DE PÁRRAFO ---
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(name='TitleStyle', parent=styles['h1'], fontSize=18, alignment=TA_CENTER, textColor=navy, spaceAfter=14)
        heading1_style = ParagraphStyle(name='Heading1Style', parent=styles['h2'], fontSize=14, textColor=navy, leftIndent=0, spaceBefore=12, spaceAfter=6)
        heading2_style = ParagraphStyle(name='Heading2Style', parent=styles['h3'], fontSize=11, textColor=black, leftIndent=0, spaceBefore=8, spaceAfter=4)
        body_style = ParagraphStyle(name='BodyStyle', parent=styles['Normal'], fontSize=10, alignment=TA_JUSTIFY, spaceAfter=6, leading=14)
        list_item_style = ParagraphStyle(name='ListItemStyle', parent=body_style, leftIndent=1*cm, spaceAfter=2)
        code_style = ParagraphStyle(name='CodeStyle', parent=styles['Code'], fontSize=9, textColor=gray, leftIndent=0, spaceBefore=0, spaceAfter=6)
        caption_style = ParagraphStyle(name='CaptionStyle', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=gray, fontName='Helvetica-Oblique')
        table_header_style = ParagraphStyle(name='TableHeader', parent=body_style, fontName='Helvetica-Bold', alignment=TA_CENTER)
        table_cell_style = ParagraphStyle(name='TableCell', parent=body_style, alignment=TA_RIGHT)

        # --- 7. CONSTRUCCIÓN DEL CONTENIDO DEL PDF ('story') ---
        # 'story' es una lista de objetos de ReportLab (párrafos, imágenes, etc.) que se dibujarán en el PDF.
        story = []

        # Se inserta un salto de página al principio. Esto asegura que el contenido
        # del informe comience en la página 2, dejando la página 1 vacía para
        # que sea dibujada por la función `portada_canvas`.
        story.append(PageBreak())

        # --- Sección de Encabezado (Página 2 en adelante) ---
        if logo_path and os.path.exists(logo_path):
             try:
                 img = Image(logo_path, width=4*cm, height=2*cm)
                 img.hAlign = 'CENTER'
                 story.append(img)
                 story.append(Spacer(1, 0.5*cm))
             except Exception as img_err:
                 print(f"Advertencia: No se pudo cargar el logo '{logo_path}': {img_err}")
        story.append(Paragraph("INFORME TÉCNICO DE PREDIO URBANO", title_style))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"<b>Ciudad:</b> Guayaquil", body_style))
        story.append(Paragraph(f"<b>Fecha:</b> {fecha_str}", body_style))
        story.append(Paragraph(f"<b>Código Catastral:</b> {codcat}", body_style))
        story.append(Spacer(1, 0.7*cm))

        # --- Sección 1: Identificación ---
        story.append(Paragraph("1. Identificación del Predio", heading1_style))
        story.append(Paragraph(f"<b>Código Catastral:</b> {codcat}", body_style))
        story.append(Paragraph(f"<b>Ubicación:</b> Frente a la Calle {calle}", body_style))
        story.append(Spacer(1, 0.3*cm))

        # --- Sección 2: Características ---
        story.append(Paragraph("2. Características Generales", heading1_style))
        story.append(Paragraph(f"<b>Uso Principal:</b> {uso_edi}", body_style))
        story.append(Paragraph(f"<b>Área según Escritura:</b> {area_esc:.2f} m² ({num_a_letras(area_esc)} metros cuadrados)", body_style))
        story.append(Spacer(1, 0.3*cm))

        # --- Sección 3: Linderos ---
        story.append(Paragraph("3. Linderos y Dimensiones", heading1_style))
        story.append(Paragraph("Se detallan los colindantes y las longitudes aproximadas de cada lindero:", body_style))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph("<b>Lindero Norte:</b>", heading2_style))
        story.append(Paragraph(f"Colinda con: {lindero_n}", list_item_style))
        story.append(Paragraph(f"Longitud: {long_n:.2f} metros", list_item_style))
        # (Se repite para Sur, Este y Oeste)
        story.append(Paragraph("<b>Lindero Sur:</b>", heading2_style))
        story.append(Paragraph(f"Colinda con: {lindero_s}", list_item_style))
        story.append(Paragraph(f"Longitud: {long_s:.2f} metros", list_item_style))
        story.append(Paragraph("<b>Lindero Este:</b>", heading2_style))
        story.append(Paragraph(f"Colinda con: {lindero_e}", list_item_style))
        story.append(Paragraph(f"Longitud: {long_e:.2f} metros", list_item_style))
        story.append(Paragraph("<b>Lindero Oeste:</b>", heading2_style))
        story.append(Paragraph(f"Colinda con: {lindero_o}", list_item_style))
        story.append(Paragraph(f"Longitud: {long_o:.2f} metros", list_item_style))
        story.append(Spacer(1, 0.3*cm))

        # --- Sección 4: Cuadro de Coordenadas ---
        story.append(Paragraph("4. Cuadro de Coordenadas", heading1_style))
        story.append(Paragraph(
            "A continuación se presentan las coordenadas de los vértices del predio. Las coordenadas geográficas "
            "(Latitud/Longitud) corresponden al sistema de origen de los datos, y las coordenadas proyectadas "
            "(Este/Norte) han sido calculadas en la zona UTM correspondiente.",
            body_style
        ))
        story.append(Spacer(1, 0.5 * cm))

        try:
            # Validación del CRS de entrada.
            if not gdf_filtrado.crs:
                raise ValueError("El GeoDataFrame de entrada no tiene un Sistema de Coordenadas (CRS) definido.")
            if not gdf_filtrado.crs.is_geographic:
                raise ValueError(f"El CRS de entrada '{gdf_filtrado.crs.name}' no es geográfico. Se esperaba WGS 84 (EPSG:4326).")

            # Lógica para determinar la zona UTM correcta y reproyectar.
            predio_geom_wgs84 = gdf_filtrado.iloc[0].geometry
            centroid = predio_geom_wgs84.centroid
            utm_zone = int((centroid.x + 180) // 6) + 1
            target_epsg_code = 32600 + utm_zone if centroid.y >= 0 else 32700 + utm_zone
            utm_system_name = f"WGS 84 / UTM zone {utm_zone}{'N' if centroid.y >= 0 else 'S'}"
            gdf_utm = gdf_filtrado.to_crs(epsg=target_epsg_code)
            predio_geom_utm = gdf_utm.iloc[0].geometry

            # Extracción de coordenadas de los vértices del polígono.
            if predio_geom_wgs84.geom_type == 'Polygon':
                wgs_coords = list(predio_geom_wgs84.exterior.coords)
                utm_coords = list(predio_geom_utm.exterior.coords)
            elif predio_geom_wgs84.geom_type == 'MultiPolygon':
                # Si es un multipolígono, se usa el polígono más grande.
                largest_poly_wgs84 = max(predio_geom_wgs84.geoms, key=lambda p: p.area)
                largest_poly_utm = max(predio_geom_utm.geoms, key=lambda p: p.area)
                wgs_coords = list(largest_poly_wgs84.exterior.coords)
                utm_coords = list(largest_poly_utm.exterior.coords)
            else:
                utm_coords, wgs_coords = [], []
                story.append(Paragraph(f"Advertencia: Tipo de geometría no soportado ({predio_geom_wgs84.geom_type}).", body_style))

            # Creación y estilización de la tabla de coordenadas.
            if utm_coords:
                table_data = [[Paragraph("<b>Punto</b>", table_header_style), Paragraph("<b>Este (UTM)</b>", table_header_style), Paragraph("<b>Norte (UTM)</b>", table_header_style), Paragraph("<b>Longitud (°)</b>", table_header_style), Paragraph("<b>Latitud (°)</b>", table_header_style)]]
                for i, (utm, wgs) in enumerate(zip(utm_coords[:-1], wgs_coords[:-1])): # Excluye el último punto que es igual al primero.
                    table_data.append([f"V-{i+1}", f"{utm[0]:.2f}", f"{utm[1]:.2f}", f"{wgs[0]:.6f}", f"{wgs[1]:.6f}"])
                coord_table = Table(table_data, colWidths=[1.5*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
                coord_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), Color(0.9,0.9,0.9)),
                    ('GRID', (0,0), (-1,-1), 1, colors.black),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
                ]))
                story.append(KeepTogether([coord_table])) # Evita que la tabla se divida entre páginas.
                story.append(Spacer(1, 0.2*cm))
                note_style = ParagraphStyle(name='NoteStyle', parent=styles['Normal'], fontSize=8, alignment=TA_JUSTIFY, textColor=gray)
                story.append(Paragraph(f"<b>Nota:</b> Las coordenadas UTM fueron calculadas en el sistema <b>{utm_system_name} (EPSG:{target_epsg_code})</b>.", note_style))

        except Exception as coord_err:
            story.append(Paragraph(f"<i>No se pudo generar el cuadro de coordenadas. Error: {coord_err}</i>", caption_style))
        story.append(Spacer(1, 0.5*cm))

        # --- Sección 5: Información Geométrica y Mapa ---
        story.append(Paragraph("5. Información Geométrica (Calculada)", heading1_style))

        # Inserta la imagen del mapa si se proporciona.
        if map_image_path and os.path.exists(map_image_path):
            try:
                # Lógica para escalar la imagen para que encaje en la página sin distorsión.
                pil_img = PILImage.open(map_image_path)
                aspect_ratio = pil_img.height / float(pil_img.width)
                display_width = doc.width * 0.95
                display_height = display_width * aspect_ratio
                img = Image(map_image_path, width=display_width, height=display_height)
                img.hAlign = 'CENTER'
                # Agrupa la imagen y su pie de foto para evitar que se separen entre páginas.
                image_group = [Spacer(1, 0.5*cm), img, Spacer(1, 0.2*cm), Paragraph("<i>Figura 1: Representación gráfica del predio.</i>", caption_style)]
                story.append(KeepTogether(image_group))
                story.append(Spacer(1, 0.5*cm))
            except Exception as img_err:
                 print(f"Advertencia: No se pudo procesar la imagen del mapa '{map_image_path}': {img_err}")

        story.append(Paragraph(f"<b>Área Calculada (GIS):</b> {shape_area:.2f} m² ({num_a_letras(shape_area)} metros cuadrados)", body_style))
        story.append(Paragraph(f"<b>Perímetro Calculado (GIS):</b> {shape_len:.2f} metros", body_style))
        story.append(Paragraph(f"<b>Sistema de Coordenadas de Origen:</b> {crs_info}", code_style))
        story.append(Spacer(1, 0.3*cm))

        # --- Sección 6: Observaciones ---
        story.append(Paragraph("6. Observaciones", heading1_style))
        story.append(Paragraph(f"Se constata una diferencia entre el área registrada en la escritura ({area_esc:.2f} m²) y el área calculada ({shape_area:.2f} m²). Esta discrepancia puede deberse a métodos de medición históricos o actualizaciones catastrales. Se recomienda una verificación.", body_style))
        story.append(Spacer(1, 0.3*cm))

        # --- Sección 7: Fuente y Autoría ---
        story.append(Paragraph("7. Fuente de Datos", heading1_style))
        story.append(Paragraph(f"Información extraída del registro con Código Catastral {codcat}.", body_style))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"<b>Elaborado por:</b><br/>{autor}", body_style))

        # --- 8. GENERACIÓN FINAL DEL PDF ---
        # El método build() toma el 'story' y lo renderiza en el archivo PDF.
        # onFirstPage y onLaterPages asignan las funciones de callback para la portada y el pie de página.
        doc.build(story, onFirstPage=portada_canvas, onLaterPages=footer_canvas)

        return True, f"Informe PDF generado exitosamente como: {output_filename}"

    except Exception as e:
        # Captura cualquier error inesperado durante la creación del PDF.
        return False, f"Error al generar el informe PDF: {e}"
