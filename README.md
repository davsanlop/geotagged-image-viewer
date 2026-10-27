<h1>Introducción - ES</h1>
Bienvenid@ al repositorio del visor de imágenes geoetiquetadas. El objetivo de este proyecto es poder prestar soporte al equipo de delineación mediante un visor web ligero y sencillo de usar donde puedan
comprobarse las imágenes tomadas en campo para verificar la existencia de afecciones o elementos del suelo en el estudio de tramos subterráneos.
<h3>https://geotagged-image-viewer.dsanchez-iplan.workers.dev</h3>

<h2>Interfaz de uso</h2>
El visor permite cargar imágenes directamente desde el explorador de archivos de Windows, o bien arrastrándolas o bien con una ventana emergente, y permite realizar cargas masivas desde cualquier ubicación, ya sea local o en servidores remotos, como Autodesk Forma o Microsoft SharePoint. La subida de archivos muy rápida gracias a las herramientas empleadas, y mantiene toda la información en el navegador web localmente, sin enviar datos a ningún servidor ni dirección, por lo que no compromete la seguridad corporativa.

Tras realizar la importación de imágenes, se muestran en la barra lateral, pudiendo buscar por nombre o fecha para filtrar. Al pulsar sobre una imagen, el mapa se centrará y escalará automáticamente para visualizarla, resaltando el icono georreferenciado. Dicho icono muestra la orientación de la cámara en el momento de la creación del fichero, lo que permite ver hacia qué elemento se estaba apuntando en campo.
Se pueden eliminar imágenes concretas pulsando en el icono de la papelera dentro de su bloque, y si se pulsa sobre el icono de la barra superior, se eliminarán todas.

Al pasar el cursor sobre un icono, un pequeño desplegable se abre para tener una visualización preliminar de la imagen, y al pulsar sobre el marcador se abre una pestaña con la imagen en mayor tamaño y el resto de atributos de la misma. Incluso se pueden copiar las coordenadas en formato geográfico pulsando sobre ellas. 
Al pulsar de nuevo sobre la imagen, se despliega en pantalla completa para poder analizar todos los detalles en resolución original, permitiendo hacer zoom y desplazarse de una foto a otra. Al salir de esta visualización, el mapa se centra automáticamente para contextualizar geográficamente la imagen que se acaba de consultar.

<h2>Motor de exportación de datos</h2>
En la barra superior de la interfaz, junto a la caja de búsqueda, aparecen dos opciones de exportación:

* **Exportación GeoJSON:** Genera un archivo estándar con las geometrías de los puntos y sus propiedades (nombre, fecha y azimut) listo para sistemas SIG.
* **Exportación DXF (AutoCAD):** Utiliza `proj4` para transformar las coordenadas geográficas a metros $UTM$ reales en el navegador. Construye dinámicamente un archivo vectorial en formato ASCII DXF estructurado en capas profesionales (`FOTOS_PUNTOS`, `FOTOS_AZIMUT`, `FOTOS_TEXTO`), representando cada foto mediante un punto base, una flecha orientada según el azimut y etiquetas de texto con el nombre, fecha y acimut para facilitar el trabajo de delineación en CAD.

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
