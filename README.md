# Cripta

Juego de exploración de criptas por turnos, con tiempo virtual, hecho en Python para el curso
Estructuras de Datos (II ciclo 2026).

Integrantes:
- Emily Benavides Rodríguez.
- Andrea Cordero Espinoza.

## 1. ¿Qué se necesita para ejecutarlo?

- Python 3.11.
- Conexión a internet para consultar la API de criptas (salvo que esté usando el modo `--offline`).
- Instalar las dependencias con `pip install -r requirements.txt`. Estas contienen Requests (lo utilizado para la comunicación HTTP) y Pytest (para las pruebas automáticas). No se usan otras librerías externas.

## 2. Instalación

Desde un entorno limpio, en la carpeta del proyecto:

`python -m venv .venv`

Activar el entorno:

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- pip install -r requirements.txt
- Linux/macOS: `source .venv/bin/activate`

El proyecto también incluye pyproject.toml y uv.lock. 
Si ya está uv instalado, es opcional usarlo en lugar de los pasos anteriores:

`uv sync`

## 3. Comandos principales

Jugar sin indicar cripta (muestra un menú con las criptas del servicio):

`python main.py`

Jugar una cripta específica:

`python main.py <id_de_la_cripta>`

Opciones:

| Opción | Qué hace |
|---|---|
| `--cache-size N` | Fichas máximas guardadas en memoria (por defecto 25). |
| `--replay LOG` | Reproduce una partida grabada en un archivo de bitácora. |
| `--offline` | Lee las respuestas del paquete de la carpeta `offline/` en lugar de la red. No cuenta solicitudes. Para generar el paquete: `python grabar_offline.py`. |
| `--bench` | Ejecuta todos los benchmarks y termina, sin abrir la vista interactiva. |

Comandos del juego:

| Comando | Acción |
|---|---|
| `w` `a` `s` `d` | Moverse al norte, oeste, sur o este, respectivamente. |
| `abrir w/a/s/d` | Abrir la puerta en esa dirección (necesita la llave). |
| `atacar [id]` | Atacar a un enemigo de la sala (el id se puede omitir si hay uno solo). |
| `esperar` | Dejar pasar el tiempo. |
| `recoger [id]` | Recoger un objeto del suelo. |
| `usar`, `equipar`, `soltar` | Actúan sobre el objeto marcado con `>` en el inventario. |
| `inv`, `sig`, `ant` | Ver el inventario y moverse al siguiente o al anterior. |
| `inv peso`, `inv valor`, `inv nombre` | Vista ordenada del inventario (no cambia el orden real). |
| `retroceder` | Usar el pergamino de retroceso (también funciona seleccionando el pergamino en inventario y escribir usar). |
| `guardar [nombre]`, `cargar [nombre]` | Guardar o cargar la partida (nombre por defecto: `partida`). |
| `salir` | Terminar la sesión. |
## 4. Pruebas automáticas

`python -m pytest`

Las pruebas están en `tests/` y cubren: inventario, puertas, efectos (veneno y regeneración),
botín de enemigos, ordenamientos, bitácora, servicio y una prueba aleatoria del retroceso que
compara una foto exacta del estado antes de una acción y después de retroceder.

_**Nota:** La carpeta `pruebas_manuales/` contiene pruebas manuales de las capas de datos,
adaptadores y vista (almacén, caché, catálogo, DTO, estructuras, lector, lista, repositorio y vista).
No son pruebas de pytest. Se ejecutan desde la raíz, por ejemplo:
`python -m pruebas_manuales.prueba_lista`. `prueba_catalogo_red`, `prueba_repositorio` y
`prueba_vista` hacen solicitudes reales al servicio y gastan presupuesto._

## 5. Benchmarks

Cada archivo de `bench/` mide una estructura contra la alternativa que se descartó. Para ejecutarlos
todos, en orden, sin abrir la vista interactiva:

`python main.py --bench`

También se puede correr uno solo, desde la carpeta del proyecto y con `-m`:

| Comando | Qué mide |
|---|---|
| `python -m bench.bench_ciclo` | Ciclo completo del juego (esperar y retroceder) contra el límite de 20 ms. |
| `python -m bench.bench_historial` | Retroceso con funciones de deshacer contra copiar el estado completo. |
| `python -m bench.bench_agenda` | Agenda de eventos (heap) contra listas sin ordenar y ordenada. |
| `python -m bench.bench_inventario` | Lista doblemente enlazada con cursor contra arreglo. |
| `python -m bench.bench_bitacora` | Buffer circular de 20 mensajes contra lista que desplaza y contra guardar todo. |
| `python -m bench.bench_ordenamientos` | Inserción, mergesort y la función híbrida `ordenar`. |
| `python -m bench.bench_rastro` | Rastro con caducidad al consultar contra eventos y barrido de salas. |
| `python -m bench.bench_cache` | Caché de fichas: búsqueda binaria contra lineal, y LRU contra FIFO. |
| `python -m bench.bench_guardado` | Guardado binario contra JSON: tamaño, guardar, cargar todo y cargar una sala. |
| `python -m bench.bench_fichas` | Costo de una ficha desde memoria, disco y red, y costo de marcar las fichas en uso. |
| `python -m bench.bench_precarga` | Solicitudes de contenido de salas: una por sala, anticipar siempre y lote solo si falta. |
| `python -m bench.bench_catalogo` | Solicitudes de fichas del catálogo: una por id, por sala y por lote de salas. |
| `python -m bench.bench_replay` | Bitácora de partida: anotar con y sin flush, leer, reejecutar y copiar el estado. |

Los benchmarks usan `time`, `gc`, `tracemalloc`, `copy`, `json` y `tempfile` únicamente para medir
o para construir la alternativa descartada; el modelo del juego no los usa. Los benchmarks de red
(`bench_fichas`, `bench_precarga`, `bench_catalogo`) usan una fuente falsa y no hacen solicitudes
reales. Los tiempos dependen de la computadora: lo que se mantiene entre equipos es la forma de las
curvas y los conteos de solicitudes, no los números exactos.

## 6. Archivos generados

El programa crea estas carpetas y archivos al ejecutarse (todos se pueden borrar sin romper nada):

| Ruta | Qué contiene |
|---|---|
| `saves/<nombre>.sav` | Partida guardada con `guardar [nombre]`, en el formato binario propio. |
| `saves/partida_<cripta>_<semilla>.log` | Bitácora de la partida (texto, un comando por línea) para `--replay`. |
| `saves/puntajes.txt` | Tabla de puntajes local, una línea por partida terminada. |
| `cache/catalogo/` | Fichas del catálogo descargadas (un `.json` por ficha) y `version.txt`. Si cambia la versión del catálogo, se borra y se vuelve a descargar. |
| `offline/` | Paquete de respuestas para `--offline`. Se genera con `python grabar_offline.py`. Está incluido en el repositorio. |

Para probar `--replay` sin jugar antes, se incluye una partida de ejemplo:

`python main.py --replay docs/ejemplo_partida.txt`

## 7. Estructura del proyecto

| Carpeta | Contenido |
|---|---|
| `model/` | Lógica del juego: partida, jugador, enemigos, salas, objetos, trampas, efectos, inventario y reloj. No conoce la red ni los archivos. |
| `structures/` | Estructuras de datos propias: agenda (heap), historial (buffer circular de cuadros), bitácora (buffer circular), lista doblemente enlazada, ordenamientos, caché y cola. |
| `service/` | `JuegoService`: fachada entre los controladores y el modelo. |
| `data/`, `dto/`, `adapters/` | Acceso a la API, lectura de fichas y archivos. |
| `controller/`, `view/` | Entrada del usuario y pantalla. |
| `bench/` | Benchmarks. |
| `tests/` | Pruebas automáticas. |

## 8. Documentación

- **Documento de Decisiones de Diseño:** [docs/Documento_de_Decisiones.pdf](docs/Documento_de_Decisiones.pdf)
- **Bitácora de prompts a LLM:** `Prompts_LLM_EmilyB.md` y `Prompts_LLM_AndreaC.md`.

## 9. Decisiones de diseño resumidas 

- **Agenda:** min heap propio con número de secuencia para desempatar y posición guardada en cada
  evento para cancelar o reprogramar en O(log n).
- **Inventario:** lista doblemente enlazada con cursor; soltar, equipar y recorrer en O(1).
- **Historial:** un cuadro por acción en un buffer circular de 5; cada cambio guarda cómo
  deshacerse. El uso del pergamino no se registra.
- **Rastro:** un instante por sala; la caducidad (400) se revisa al consultar.
- **Bitácora:** buffer circular de 20 mensajes; no forma parte del historial de retroceso.
- **Ordenamientos:** `ordenar` escoge inserción (listas de hasta 48 o casi ordenadas, con un límite
  de trabajo) o mergesort; ambos son estables.
- **Veneno y regeneración:** opcionales; solo se aplican si la ficha de la cripta los trae.
- **Botín:** lo que suelta un enemigo queda en el suelo y se registra en el historial, de modo que
  retroceder lo quita y revive al enemigo.
- **Caché de fichas:** vector ordenado de ids (búsqueda binaria) y lista doblemente enlazada con el
  orden de uso; expulsa la menos usada recientemente que no esté en uso, y lo expulsado se recupera
  del disco, no de la red.
- **Contenido de salas:** al entrar a una sala cuyo contenido falta, se pide en una sola solicitud
  un lote de hasta 10 salas cercanas (recorrido en anchura); si ya está, no se pide nada.
- **Catálogo:** las fichas de todas las salas de un lote se resuelven juntas, en lotes de 10 ids;
  se guardan en `cache/catalogo` y se invalidan si cambia la versión del catálogo.
- **Guardado:** archivo binario propio con encabezado, versión del formato, índice de salas al
  final para leer una sala sin leer el resto, y los comandos del jugador. Al cargar se valida la
  cripta, su versión y la del catálogo.
- **Bitácora de partida:** archivo de texto de solo anexado, con flush en cada comando; el
  encabezado lleva cripta, versiones y semilla. `--replay` se niega a reproducir si las versiones
  no coinciden.
- **Modo sin conexión:** `ClienteOffline` ofrece los mismos métodos que `ClienteHttp` y lee JSON
  del paquete `offline/`; la elección se hace en un solo lugar de `main.py` y el modelo no se entera.
- **Puntajes:** archivo de texto; al mostrarse se ordenan con `ordenar` (victorias primero, luego
  más enemigos derrotados y menos tiempo).