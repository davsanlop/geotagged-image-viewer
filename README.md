<h1>Introducción - ES</h1>
El objetivo de este proyecto es desarrollar una herramienta ligera, sencilla de usar y rápida para situaciones de diseño coordinado con topografía con un gran volumen de imágenes georreferenciadas, usadas para evaluar y detectar afecciones invisibles sobre el plano pero existentes en la vida real.
<h3>Live demo: https://geotagged-image-viewer.dsanchez-iplan.workers.dev</h3>

<h2>Interfaz de uso</h2>
<img width="1868" height="955" alt="image" src="https://github.com/user-attachments/assets/e9936d44-a327-4614-a51a-b6470eb0b2a6" />

El visor permite cargar imágenes directamente desde el explorador de archivos de Windows, o bien arrastrándolas o bien con una ventana emergente, y permite realizar cargas masivas desde cualquier ubicación, ya sea local o en servidores remotos, como Autodesk Forma o Microsoft SharePoint. La subida de archivos muy rápida gracias a las herramientas empleadas, y mantiene toda la información en el navegador web localmente, sin enviar datos a ningún servidor ni dirección, por lo que no compromete la seguridad corporativa.

Tras realizar la importación de imágenes, se muestran en la barra lateral, pudiendo buscar por nombre o fecha para filtrar. Al pulsar sobre una imagen, el mapa se centrará y escalará automáticamente para visualizarla, resaltando el icono georreferenciado. Dicho icono muestra la orientación de la cámara en el momento de la creación del fichero, lo que permite ver hacia qué elemento se estaba apuntando en campo.
Se pueden eliminar imágenes concretas pulsando en el icono de la papelera dentro de su bloque, y si se pulsa sobre el icono de la barra superior, se eliminarán todas.

Al pasar el cursor sobre un icono, un pequeño desplegable se abre para tener una visualización preliminar de la imagen, y al pulsar sobre el marcador se abre una pestaña con la imagen en mayor tamaño y el resto de atributos de la misma. Incluso se pueden copiar las coordenadas en formato geográfico pulsando sobre ellas. 
Al pulsar de nuevo sobre la imagen, se despliega en pantalla completa para poder analizar todos los detalles en resolución original, permitiendo hacer zoom y desplazarse de una foto a otra. Al salir de esta visualización, el mapa se centra automáticamente para contextualizar geográficamente la imagen que se acaba de consultar.

<h2>Motor de exportación de datos</h2>
En la barra superior de la interfaz, junto a la caja de búsqueda, aparecen dos opciones de exportación:

* **Exportación GeoJSON:** Genera un archivo estándar con las geometrías de los puntos y sus propiedades (nombre, fecha y azimut) listo para sistemas SIG.
* **Exportación DXF (AutoCAD):** Utiliza `proj4` para transformar las coordenadas geográficas a metros $UTM$ reales en el navegador. Construye dinámicamente un archivo vectorial en formato ASCII DXF estructurado en capas profesionales (`FOTOS_PUNTOS`, `FOTOS_AZIMUT`, `FOTOS_TEXTO`), representando cada foto mediante un punto base, una flecha orientada según el azimut y etiquetas de texto con el nombre, fecha y acimut para facilitar el trabajo de delineación en CAD.
<p align="center">
<img width="899" height="157" alt="image" text-align:center src="https://github.com/user-attachments/assets/c5a03183-e955-46f6-b09d-f3dce33ff4a1" />
</p>
Esto permite integrar las imágenes en el flujo de trabajo del equipo de delineación si fuera necesario, y más adelante se estudiará la mejora de la herramienta de exportación en DXF para adaptarse a las necesidades del equipo.

<h2>Estructura del proyecto y tecnologías utilizadas</h2>

El visor está construido como una aplicación web moderna del lado del cliente (Single Page Application puramente frontend), sin necesidad de servidores ni bases de datos externas. Utiliza las siguientes librerías y CDNs:

* **Leaflet (v1.9.4):** Biblioteca de mapas interactivos de código abierto. Se encarga de la renderización del mapa base, la gestión de capas (Topográfico y Satélite), el control de zoom (hasta nivel 22) y el posicionamiento de marcadores.
* **Exifr:** Librería en JavaScript para la extracción de metadatos EXIF directamente en el navegador. Se utiliza para leer de forma asíncrona las coordenadas GPS (`latitude`, `longitude`), la fecha de captura (`DateTimeOriginal`) y el azimut de la cámara (`GPSImgDirection`).
* **Proj4js:** Biblioteca de transformación de sistemas de coordenadas. Se implementa para convertir las coordenadas geográficas estándar ($WGS84$: Latitud/Longitud) a coordenadas métricas planas ($UTM$) según la zona correspondiente, permitiendo la generación precisa de archivos CAD.
* **Tailwind CSS:** Framework de CSS utility-first cargado vía CDN junto con su configuración personalizada de colores (`brand`), utilizado para estructurar toda la interfaz responsiva, el panel lateral, modales y botones.
* **FontAwesome (v6.4.0):** Kit de iconos vectoriales utilizado para enriquecer la interfaz con elementos gráficos intuitivos (flechas de dirección, iconos de cámara, lupas, barras de herramientas y botones de acción).

## Desglose de la Arquitectura y el Código

El código está estructurado en un único archivo modularizado mediante JavaScript nativo (Vanilla JS), organizado en las siguientes secciones lógicas:

### 1. Estado Global y Capas del Mapa (`#map`)
* Gestiona la colección global de fotografías (`photosData`), los grupos de capas de marcadores (`markersGroup`) y el índice activo del visor.
* Configura dos mapas base independientes intercambiables desde la interfaz: **OpenStreetMap (Topográfico)** e **Esri World Imagery (Satélite)**, ambos optimizados para permitir altos niveles de zoom detallado.

### 2. Ingesta y Procesamiento de Archivos EXIF
* **Drag & Drop y Selector:** Escucha eventos de arrastre o selección múltiple de archivos de imagen (`image/jpeg`).
* **Control de Duplicados:** Implementa una validación por nombre de archivo para omitir automáticamente la importación de fotografías repetidas.
* **Extracción de Metadatos:** Utiliza promesas con `exifr` para extraer las coordenadas GPS y el **Azimut** (`GPSImgDirection`). Si la imagen carece de fecha EXIF, aplica un *parser* regular al nombre del archivo bajo la sintaxis estándar `YYYYMMDD_HHMMSS`.

### 3. Marcadores Personalizados y Azimut
* Los marcadores sobre el mapa se generan mediante `L.divIcon` utilizando vectores estilizados con CSS. 
* El icono muestra **únicamente una flecha direccional** en color blanco con un contorno fino azul, la cual rota dinámicamente en función de los grados de azimut extraídos del EXIF de la foto.

### 4. Paneles Interactivos (Tooltips y Popups)
* **Hover (Menú Preliminar):** Al pasar el ratón sobre un punto del mapa, despliega un *tooltip* flotante con una previsualización de la imagen y su nombre.
* **Clic (Popup Detallado):** Muestra una tarjeta flotante con una imagen ampliada (respetando su relación de aspecto original mediante `object-contain`), fecha, azimut y un botón interactivo para **copiar las coordenadas al portapapeles** (el cual cambia dinámicamente a color verde e informa *"Coordenadas copiadas al portapapeles"* al presionarlo).

### 5. Panel Lateral (Sidebar) y Sincronización Bidireccional
* Muestra la lista de fotos cargadas con tarjetas interactivas que incluyen miniaturas, metadatos, un botón de centrado rápido (*crosshairs*) y un **botón de eliminación individual** para borrar fotos de forma selectiva.
* Incluye un **buscador en tiempo real** que filtra las fotografías por nombre o fecha de manera instantánea.
* **Hover Bidireccional:** Al interactuar con una tarjeta en la lista lateral, se resalta automáticamente el marcador correspondiente en el mapa, y viceversa.

### 6. Visor a Pantalla Completa (Lightbox con Lupa)
* Permite inspeccionar las fotografías a gran escala con navegación por teclado (`Esc`, flechas izquierda/derecha).
* Integra controles de **Lupa / Zoom interactivo** (+, -, Reset o clic directo sobre la imagen) que permiten ampliar la imagen hasta un 500% y desplazarla (*drag & drop*) para examinar detalles técnicos.
* Al cerrar el lightbox tras navegar entre fotos, la aplicación centra y despliega automáticamente el popup de la última foto visualizada.


# Introduction - EN

The goal of this project is to develop a lightweight, user-friendly, and fast tool for scenarios involving design coordinated with topography with a large volume of georeferenced images, used to evaluate and detect utilities or conflicts that are invisible on the plan but exist in real life.
<h3>Live demo: https://geotagged-image-viewer.dsanchez-iplan.workers.dev</h3>

## User Interface
<img width="1868" height="955" alt="image" src="https://github.com/user-attachments/assets/e9936d44-a327-4614-a51a-b6470eb0b2a6" />

The viewer allows loading images directly from the Windows file explorer, either by dragging and dropping them or via a pop-up window, and supports bulk uploads from any location, whether local or on remote servers such as Autodesk Forma or Microsoft SharePoint. File uploading is very fast thanks to the tools used, and it keeps all information locally within the web browser, without sending data to any server or address, thus avoiding any compromise to corporate security.

After importing the images, they are displayed in the sidebar, allowing you to search by name or date to filter them. By clicking on an image, the map will automatically center and scale to display it, highlighting the georeferenced icon. This icon shows the camera's orientation at the time the file was created, allowing you to see which element was being pointed at in the field.
Specific images can be deleted by clicking on the trash can icon within their block, and clicking on the icon in the top bar will delete all of them.

Hovering over an icon opens a small dropdown menu for a preliminary preview of the image, and clicking on the marker opens a tab with a larger version of the image and its remaining attributes. You can even copy the coordinates in geographic format by clicking on them.
Clicking on the image again opens it in full screen to analyze all details at original resolution, allowing you to zoom in and navigate from one photo to another. Upon exiting this view, the map automatically centers to geographically contextualize the image just viewed.

## Data Export Engine

In the top bar of the interface, next to the search box, two export options appear:

* **GeoJSON Export:** Generates a standard file with point geometries and their properties (name, date, and azimuth), ready for GIS systems.
* **DXF Export (AutoCAD):** Uses `proj4` to transform geographic coordinates into real $UTM$ meters in the browser. It dynamically builds a vector file in ASCII DXF format structured in professional layers (`FOTOS_PUNTOS`, `FOTOS_AZIMUT`, `FOTOS_TEXTO`), representing each photo via a base point, an arrow oriented according to the azimuth, and text labels with the name, date, and azimuth to facilitate drafting work in CAD.
<p align="center">
<img width="899" height="157" alt="image" text-align:center src="https://github.com/user-attachments/assets/c5a03183-e955-46f6-b09d-f3dce33ff4a1" />
</p>
This allows the images to be integrated into the detailing team's workflow if necessary, and improvements to the DXF export tool will be studied later to adapt to the team's needs.

## Project Structure and Technologies Used

The viewer is built as a modern client-side web application (purely frontend Single Page Application), without the need for servers or external databases. It uses the following libraries and CDNs:

* **Leaflet (v1.9.4):** Open-source interactive map library. It handles base map rendering, layer management (Topographic and Satellite), zoom control (up to level 22), and marker placement.
* **Exifr:** JavaScript library for extracting EXIF metadata directly in the browser. It is used to asynchronously read GPS coordinates (`latitude`, `longitude`), capture date (`DateTimeOriginal`), and camera azimuth (`GPSImgDirection`).
* **Proj4js:** Coordinate system transformation library. It is implemented to convert standard geographic coordinates ($WGS84$: Latitude/Longitude) into flat metric coordinates ($UTM$) according to the corresponding zone, enabling precise CAD file generation.
* **Tailwind CSS:** Utility-first CSS framework loaded via CDN along with its custom color configuration (`brand`), used to structure the entire responsive interface, sidebar, modals, and buttons.
* **FontAwesome (v6.4.0):** Vector icon kit used to enrich the interface with intuitive graphical elements (directional arrows, camera icons, magnifiers, toolbars, and action buttons).

## Architecture and Code Breakdown

The code is structured in a single file modularized using native JavaScript (Vanilla JS), organized into the following logical sections:

### 1. Global State and Map Layers (`#map`)

* Manages the global collection of photographs (`photosData`), marker layer groups (`markersGroup`), and the viewer's active index.
* Configures two independent base maps switchable from the interface: **OpenStreetMap (Topographic)** and **Esri World Imagery (Satellite)**, both optimized to allow high levels of detailed zoom.

### 2. EXIF File Ingestion and Processing

* **Drag & Drop and Selector:** Listens for drag events or multiple image file selections (`image/jpeg`).
* **Duplicate Control:** Implements filename validation to automatically skip importing previously uploaded photographs.
* **Metadata Extraction:** Uses promises with `exifr` to extract GPS coordinates and the **Azimuth** (`GPSImgDirection`). If the image lacks an EXIF date, it applies a regular expression parser to the filename under the standard `YYYYMMDD_HHMMSS` syntax.

### 3. Custom Markers and Azimuth

* Markers on the map are generated via `L.divIcon` using CSS-styled vectors.
* The icon shows **only a directional arrow** in white with a thin blue outline, which dynamically rotates based on the azimuth degrees extracted from the photo's EXIF data.

### 4. Interactive Panels (Tooltips and Popups)

* **Hover (Preliminary Menu):** When hovering over a point on the map, it displays a floating *tooltip* with a preview of the image and its name.
* **Click (Detailed Popup):** Displays a floating card with an enlarged image (respecting its original aspect ratio via `object-contain`), date, azimuth, and an interactive button to **copy coordinates to the clipboard** (which dynamically changes to green and displays *"Coordinates copied to clipboard"* when pressed).

### 5. Sidebar and Bidirectional Synchronization

* Displays the list of loaded photos with interactive cards including thumbnails, metadata, a quick-centering button (*crosshairs*), and an **individual delete button** to selectively remove photos.
* Includes a **real-time search bar** that instantly filters photographs by name or date.
* **Bidirectional Hover:** Interacting with a card in the side list automatically highlights the corresponding marker on the map, and vice versa.

### 6. Full-Screen Viewer (Lightbox with Magnifier)

* Allows inspecting photographs at a large scale with keyboard navigation (`Esc`, left/right arrows).
* Integrates **Interactive Magnifier / Zoom** controls (+, -, Reset, or direct click on the image) that allow enlarging the image up to 500% and panning (*drag & drop*) to examine technical details.
* Upon closing the lightbox after navigating between photos, the application automatically centers and displays the popup of the last viewed photo.
