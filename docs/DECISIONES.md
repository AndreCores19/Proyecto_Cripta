# Decisiones de diseño de la segunda parte

Este documento **complementa** el [Documento de Decisiones de la primera parte](Documento_de_Decisiones.pdf);
no lo reemplaza. Las decisiones de las estructuras base (agenda, historial, inventario, caché, guardado,
bitácora) siguen estando allí. Aquí se justifican las decisiones que traen las funciones de la segunda parte
y que tocan a las estructuras ya decididas. La numeración es la de la sección 5 del enunciado:

| Sección | Tema | Spec |
|---|---|---|
| 5.1 | Ruta del cazador | `specs/002-hunter-enemy/` |
| 5.2 | Invalidación de la ruta | `specs/002-hunter-enemy/` |
| 5.3 (y 5.3.1) | «ir a» y su rendimiento | `specs/003-fog-of-war/` |
| 5.4 | Resolubilidad | `specs/004-crypt-solvability/` |
| 5.5 | Línea de tiempo | `specs/005-timeline/` |
| 5.6 | Revisión de las decisiones de la primera parte | `specs/001-exit-costs/` y `specs/002-hunter-enemy/` |

El razonamiento completo de las secciones 5.3 y 5.4, con las alternativas descartadas, está en
[`specs/003-fog-of-war/research.md`](../specs/003-fog-of-war/research.md) (R2 y R6) y en
[`specs/004-crypt-solvability/research.md`](../specs/004-crypt-solvability/research.md) (R4 y R5).

## 5.1 Ruta del cazador

**Problema.** Las salidas tienen costos distintos, así que contar salas no da la ruta más barata. La decisión de un
cazador de rango pequeño debe costar según la región dentro de su rango, no según el tamaño de la cripta. Habrá
decenas de cazadores a la vez persiguiendo al mismo jugador, y hay que medir si conviene un cálculo por cazador o
uno compartido, y cuándo cambia esa respuesta. Las estructuras auxiliares de la búsqueda son propias, y el
desempate de §3.2 se cumple siempre, también con muchas rutas del mismo costo.

**Decisión.** El cazador decide con una búsqueda de Dijkstra **hacia atrás desde la sala del jugador**, sobre
las salidas entrantes (`Sala.entradas`, cada salida conoce su `origen`), acotada por un límite de costo
(`Busqueda.calcular`, `model/ruta_cazador.py`). Una sola búsqueda da la distancia al jugador de todas las salas
dentro del límite. Con esa distancia `d`, el cazador que no está en la sala del jugador mira sus salidas abiertas
y toma la de menor `(id de la sala destino, dirección)` entre las que cumplen `costo + distancia(destino) == d`;
si `d` no existe o es mayor que su `rango`, espera. Las piezas son:

- **Cola de prioridad propia**, `structures/monticulo.py`: montículo binario de arreglo con `insertar`, `extraer`,
  `proximo`, `vaciar`; a igual prioridad salen por orden de inserción. No tiene `decrease-key`: una sala se vuelve
  a insertar con mejor costo y la entrada vieja se descarta al salir.
- **Marcas por estampa** en dos enteros de `Sala` (`busq_marca`, `busq_dist`). Un contador compartido por todas
  las búsquedas da una estampa nueva a cada una, así que no hay que limpiar nada entre búsquedas.
- **Tres modos de decidir** detrás de una misma clase (`DecisorCazador`): `individual` (una búsqueda por turno de
  cazador, con su propio `rango` como límite), `compartido_sin_reuso` (una búsqueda por turno con el mayor `rango`
  entre los cazadores vivos) y `compartido` (una búsqueda por *estado*, reutilizada mientras el estado no cambie).
  El modo por defecto es `compartido`: `Partida.__init__` crea `DecisorCazador("compartido")` (`model/partida_logica.py`, línea 43) y lo expone como `partida.decisor_cazador`. El argumento por omisión de la propia clase `DecisorCazador` es `"individual"`; solo `Partida` elige `compartido`.

**Por qué se descartaron las alternativas** (`specs/002-hunter-enemy/research.md`, R1, R2, R3, R5, R9):

| Alternativa | Por qué no |
|---|---|
| Búsqueda hacia adelante desde el jugador | Responde «jugador a sala», no «sala a jugador». Una conexión puede tener salida en un solo sentido, y entonces el resultado es incorrecto. |
| Búsqueda hacia adelante desde cada cazador | Es correcta, pero no se puede compartir entre cazadores: el jugador es lo único que todos tienen en común en un instante. |
| Reutilizar o generalizar el montículo de la agenda | La agenda guarda posición en cada evento y registra una función de deshacer en el historial en cada operación; una búsqueda no puede tocar el historial. Generalizarlo pondría un desvío más en la ruta caliente que midió la spec 001 y habría que repetir esa medición. Cuesta tener el código de subir y bajar escrito dos veces (`_subir` y `_bajar` en `structures/agenda.py`; `insertar` y `extraer` en `structures/monticulo.py`, que tiene 76 líneas), cada copia con sus pruebas. |
| `dict` o `set` de salas visitadas | Prohibidos por la constitución (principio I). |
| Lista indexada por id de sala, limpiada en cada búsqueda | Costaría O(cripta) por búsqueda y rompería FR-018. |
| Búsqueda sin límite, o con un límite constante | Sin límite cuesta O(cripta) por cazador; una constante sería un número que no viene del catálogo. |
| Un modo «por cazador con caché» | Necesitaría un arreglo de distancias por cazador; las marcas de `Sala` solo guardan una búsqueda a la vez. Los tres modos ya separan los dos efectos que pide FR-019. |

**Complejidad.**

- `insertar` y `extraer` del montículo: O(log n); `proximo` y `vaciar`: O(1).
- Una búsqueda: O(V_r log V_r + E_r), con V_r y E_r las salas y salidas dentro del límite. Las estampas evitan
  cualquier preparación O(V) de la cripta, así que el trabajo depende de la región alcanzada y no del tamaño de la cripta (FR-018).
- Una decisión en modo `compartido` con el estado sin cambios: O(1) para validar la caché más O(salidas de la sala del cazador).

**Evidencia empírica.**

| Qué se midió | Resultado | Archivo |
|---|---|---|
| p99 del ciclo de eventos, 30 cazadores, 100 salas (modo `compartido`, 3 corridas) | 10.7 / 12.1 / 4.2 ms (peor ciclo 16.1 / 16.6 / 7.7 ms) | `specs/002-hunter-enemy/bench-despues-ciclo.txt` |
| Lo mismo con `rango` que alcanza toda la cripta | p99 8.7 / 9.0 / 3.5 ms (peor ciclo 23.3 / 50.3 / 10.3 ms) | `specs/002-hunter-enemy/bench-despues-ciclo.txt` |
| p99 por modo, 30 cazadores (una corrida por modo) | `individual` 9.5, `compartido_sin_reuso` 13.4, `compartido` 11.9 ms; con `rango` total 10.6, 14.4 y 9.6 ms | `specs/002-hunter-enemy/bench-ciclo-modos.txt` |
| Cripta de referencia cripta-06 (300 salas, 30 cazadores, 3 corridas) | p99 2.166 / 2.181 / 2.098 ms; la cripta sintética de 300 salas: 3.417 / 2.083 / 2.033 ms | `specs/002-hunter-enemy/bench-referencia.txt` |
| Un cazador contra muchos (`compartido`, 100 salas, `rango` sorteado entre 100, 300 y 1000, 3000 acciones, puertas casi fijas) | 1 cazador 39.5 µs por acción; 10 → 273.7; 30 → 672.5; 100 → 3211.4. Las búsquedas se quedan en 751 (729 con un cazador) | `specs/002-hunter-enemy/bench-cazador.txt` |
| `rango` chico contra grande (10 cazadores) | 100 salas: `rango` 200 = 177.1 µs, 5000 = 333.5 µs. 1000 salas: 200 = 195.7 µs, 5000 = 2569.4 µs | `specs/002-hunter-enemy/bench-cazador.txt` |
| Una búsqueda por cazador contra compartida (30 cazadores, 100 salas), µs por acción (búsquedas) | Puertas cambian seguido: `individual` 1820.3 (74147), `compartido_sin_reuso` 5030.9 (74147), `compartido` 1027.6 (2964). Casi nunca: 9042.6 (84482), 17050.1 (84482), 836.1 (751) | `specs/002-hunter-enemy/bench-cazador.txt` |
| Escalado con el tamaño de la cripta (`rango` 200, misma región de salas; modo `individual`, un cazador y la misma decisión repetida 2000 veces; el programa comprueba que la región es la misma) | 81.9 µs por decisión con 100 salas y 117.9 µs con 1000: razón 1.44 (límite de SC-008: ≤ 2) | `specs/002-hunter-enemy/bench-cazador.txt` |

Antes de medir, el programa comprueba que los tres modos toman las mismas decisiones con 30 cazadores. En las
pruebas, un oráculo independiente (relajación repetida sobre listas) valida los tres modos en criptas
aleatorias con semilla, con puertas que cambian (`tests/test_cazador_equivalencia.py`).

**Coincidencia con el `plan.md` original.** Sí. El diseño (búsqueda hacia atrás, límite por `rango`, estampas,
montículo aparte, tres modos) está igual en el `plan.md` de antes de implementar (commit `472c374`) y en el final;
el único cambio del plan después de medir fue llenar la tabla de resultados. El plan **no** fijaba el modo por
defecto: fijaba de antemano la regla (`compartido` si es el más rápido, o está a menos de 10 % del más rápido, en
cada fila de las comparaciones, y pasan p99 ≤ 20 ms y razón ≤ 2). Las mediciones cumplen la regla, así que el
modo por defecto es `compartido`. Ninguna medición hizo cambiar una decisión.

**Límites conocidos.**

- Todo el costo de las decisiones crece con la cantidad de cazadores, porque cada uno toma un turno por acción
  (39.5 µs con 1 cazador y 3211.4 µs con 100). La caché compartida evita las búsquedas, no los turnos.
- Un `rango` grande en una cripta grande sí cuesta: 2569.4 µs con 1000 salas y `rango` 5000. El peor ciclo con
  `rango` total superó 20 ms en dos de tres corridas (23.3 y 50.3 ms); el criterio es el p99, que sí se cumple, y el
  peor ciclo se imprime solo como información.
- En el ciclo de eventos, con una sola corrida por modo, `individual` (9.5 ms) no salió peor que `compartido`
  (11.9 ms) en p99. La ventaja de `compartido` aparece en el costo por acción (836.1 µs contra 9042.6 µs con puertas casi fijas), no en ese p99; todos los modos cumplen el límite de 20 ms.
- Las corridas varían entre sí en la misma máquina (p99 de 4.2 a 12.1 ms para el mismo escenario), así que las
  comparaciones valen dentro de una misma corrida y no entre corridas.
- Las mediciones de la 002 se hicieron el 2026-11-11 (commit `cafe930`). Después, la spec 003 cambió `structures/monticulo.py` (comparaciones escritas en línea, mismo comportamiento; commit `f429f82`), así que esos µs corresponden a la versión anterior del montículo. Las pruebas del montículo y del cazador pasan con el código actual (77 pruebas en `test_monticulo.py`, `test_cazador_equivalencia.py`, `test_cazador_decision.py` y `test_puertas.py`), pero las mediciones no se repitieron.
- Las criptas de 100 y 1000 salas de las comparaciones son sintéticas; solo la comparación contra cripta-06 usa una cripta publicada.

## 5.2 Invalidación de la ruta del cazador

**Problema.** Entre dos turnos de un cazador pueden abrirse o cerrarse puertas, moverse el jugador, cambiar de sala
otros actores y cambiar velocidades. La decisión tiene que ser siempre la misma que daría un cálculo desde cero:
reutilizar un cálculo anterior solo vale si se demuestra que no cambia la respuesta. Hay que decir qué eventos
invalidan qué información y cuánto trabajo se ahorra de verdad, y medirlo en `--bench` con puertas que cambian
seguido, con puertas que casi nunca cambian y contra recalcular siempre.

**Decisión.** En el modo `compartido` la búsqueda guardada se reutiliza solo mientras se cumplan **las cuatro**
condiciones siguientes (`DecisorCazador`, `model/ruta_cazador.py`):

1. el jugador sigue en el mismo objeto `Sala`;
2. el contador de puertas `Salida.epoca_puertas` vale lo mismo que cuando se guardó la búsqueda;
3. el `rango` del cazador que pregunta no es mayor que el límite con el que se hizo la búsqueda;
4. `Busqueda.ultima_estampa` coincide con la estampa guardada (ninguna otra búsqueda escribió las marcas de `Sala` desde entonces).

`Salida.cerrada` es una propiedad cuyo escritor suma 1 al contador de clase `Salida.epoca_puertas`. Los cambios de
puerta del juego (`Partida._poner_cerrada`) y las escrituras con que `Historial.deshacer` revierte pasan por esa
propiedad, así que ambos suben el contador y ninguna caché sobrevive a un cambio de puerta. Si falla la condición 3,
la búsqueda se **recalcula** con el límite nuevo `max(rango, mayor rango)` y reemplaza la caché; no se extiende.
Además, `decidir` lanza `RuntimeError` si el límite de la búsqueda que usa es menor que el `rango` del cazador.

**Por qué se descartaron las alternativas** (`research.md`, R4):

| Alternativa | Por qué no |
|---|---|
| Subir el contador solo dentro de `Partida._poner_cerrada` | Al deshacer, el historial escribe las puertas sin pasar por ahí, y quedaría una búsqueda vieja. |
| Comparar el estado usado contra el estado actual puerta por puerta | Cuesta O(puertas) por decisión; el contador cuesta O(1). |
| Marcas «sucias» por sala | Más precisa, mucho más código, y no hay evidencia de que haga falta. |
| Extender la búsqueda guardada cuando llega un cazador de mayor `rango` | Obliga a mantener vivos la frontera y las estampas entre turnos. Una búsqueda nueva cuesta O(región) y solo ocurre si llega un `rango` mayor o cambió el estado. |
| Guardar la posición del jugador con un contador en vez de comparar la sala por identidad | No hace falta: la identidad del objeto es exacta. |

**Sobreinvalidación aceptada.** Cualquier cambio de puerta en cualquier lugar invalida todas las cachés. Eso cuesta
búsquedas de más, nunca una decisión equivocada; el contador solo crece y se compara por igualdad, así que otras
`Partida` del mismo proceso solo pueden causar búsquedas extra. La condición 4 existe para la búsqueda de «ir a»
de la spec 003: debe tomar sus estampas del mismo contador (regla A) o usar campos propios (regla B); la sección 5.3 documenta lo elegido.

**Detalle del contador.** `_poner_cerrada` escribe las dos caras de la puerta, así que un cambio de puerta del juego suma 2 al contador (también lo suman la construcción de `Salida` y `Salida.enlazar`); como solo se compara por igualdad, no importa cuánto suba. La memoria que el jugador tiene de una puerta (`Salida.memoria`) no toca el contador.

**Complejidad.** Validar la caché: O(1) (cuatro comparaciones). Escribir una puerta: O(1) extra. Cada invalidación
cuesta una búsqueda de O(V_R log V_R + E_R), con R el mayor `rango`. Los modos `individual` y `compartido_sin_reuso`
buscan en cada decisión, así que ninguna otra búsqueda los afecta.

**Evidencia empírica** (3000 acciones del jugador, 30 cazadores, 100 salas, semilla 1; `specs/002-hunter-enemy/bench-cazador.txt`). «Seguido» es un cambio de puerta
por acción del jugador y «casi nunca» es uno cada 500 acciones.

| Puertas | `compartido` (reusa) | `compartido_sin_reuso` (recalcula) | Razón |
|---|---|---|---|
| Cambian seguido | 1027.6 µs por acción, 2964 búsquedas | 5030.9 µs, 74147 búsquedas | 4.90 veces más lento sin reusar |
| Casi nunca cambian | 836.1 µs por acción, 751 búsquedas | 17050.1 µs, 84482 búsquedas | 20.39 veces más lento sin reusar |

Con las puertas cambiando seguido la caché sigue ganando: 2964 búsquedas en vez de 74147 (25 veces menos), aunque se pierde parte de la ventaja respecto de puertas casi fijas (1027.6 contra 836.1 µs). La corrección se prueba con el oráculo independiente de las
pruebas, que ejecuta cada modo sobre criptas aleatorias donde las puertas cambian, el jugador se mueve, mueren
enemigos y se deshace (`tests/test_cazador_equivalencia.py`), y con una prueba que corre otra búsqueda entre dos turnos de cazador.

**Coincidencia con el `plan.md` original.** Sí. Las cuatro condiciones, el contador de puertas y el recálculo (no
extensión) ya estaban en el `plan.md` de antes de implementar (commit `472c374`); las mediciones solo confirman que
reutilizar gana en ambas filas (reglas fijadas de antemano) y no cambiaron nada.

**Límites conocidos.**

- La caché guarda una sola búsqueda a la vez, porque las marcas de `Sala` guardan una sola; un cazador de mayor
  `rango` que llega después obliga a recalcular y reemplazarla.
- Con puertas que cambian a cada acción, el modo compartido hace casi una búsqueda por acción (2964 en 3000),
  aunque sigue siendo 25 veces menos que las 74147 de los modos sin reuso.
- La medición cambia las puertas con `Partida._poner_cerrada` y una semilla (una por acción o una por 500), no con las reglas de llaves y cierre automático del juego; es la forma determinista más cercana (`research.md`, R10).
- La invalidación por puerta es global: un cambio lejos del cazador también invalida su búsqueda.

## 5.3 Búsqueda de «ir a» separada de la del cazador

**Problema.** Saber si una sala está explorada, avistada o desconocida, y cómo recuerda el jugador una puerta, se
consulta en cada vista, en cada paso de «ir a» y en cada actualización por antorcha. Explorar debe costar según
las salas que se revelan, no según el tamaño del mapa conocido. El pergamino revierte el mapa conocido y la línea
de tiempo lo reconstruye, así que registrar e invertir sus cambios tiene que ser barato. La ruta de «ir a» se
calcula sobre el subgrafo conocido, y hay que justificar si comparte implementación con la búsqueda del cazador o
si conviene separarlas.

**Alternativas consideradas** (`research.md`, R1, R2 y R6).

| Alternativa | Por qué no |
|---|---|
| Reutilizar `Busqueda.calcular` con un indicador «solo lo conocido» | Añade una rama a la ruta caliente de los cazadores (se ejecuta en cada turno de cada cazador) para servir a una función de uso manual y poco frecuente. Además, las dos búsquedas no recorren lo mismo (abajo). |
| Dijkstra hacia adelante desde el jugador, llevando el primer paso de cada ruta | Los empates entre rutas de igual costo obligan a comparar rutas en cada entrada de la cola: más estado para el mismo costo. |
| Búsqueda en anchura | Incorrecta: los costos de las salidas son distintos. |
| Campos propios de «ir a» en `Sala` (regla B) | Dos enteros más en cada sala sin mejor resultado. Queda como reserva si la medición muestra que la búsqueda extra del cazador pasa del umbral de 10 % del ciclo. |
| El conocimiento en un objeto aparte, indexado por id | Necesitaría un diccionario (prohibido) o una búsqueda, y su propio código de deshacer. |

**Decisión.** El conocimiento del jugador vive en dos enteros de objetos que el modelo ya tiene
(`Sala.conocimiento` y `Salida.memoria`) más una lista de salas descubiertas en `Partida`; toda escritura pasa por
el historial, así que el pergamino y la línea de tiempo lo revierten con el mismo mecanismo que el resto (R1).
«ir a» tiene su propia clase de búsqueda, `RutaConocida` (`model/ruta_conocida.py`): Dijkstra **hacia atrás desde el
destino** sobre el subgrafo que el jugador conoce (salas exploradas y salidas que recuerda abiertas), que se detiene
en cuanto sale del montículo la sala del jugador. **No** reutiliza `Busqueda.calcular`, que recorre el mapa
completo. Lo que sí comparten:

- el **montículo mínimo** escrito a mano (`structures/monticulo.py`): una estructura genérica que no sabe nada del
  grafo. El cazador crea uno local por búsqueda; `RutaConocida` guarda uno y lo vacía (`vaciar()`) al empezar cada
  búsqueda, porque se detiene antes de extraer todo y deja entradas sin sacar; y
- el **contador de estampas** de `Busqueda.nueva_estampa()`, con el que se marcan las salas
  (`busq_marca` / `busq_dist`), de modo que la búsqueda guardada de los cazadores se reconoce como vieja y se
  recalcula.

**Las dos búsquedas no recorren lo mismo.** El cazador mira el mundo real (las puertas tal como están y todas las
salas) y busca desde el jugador hasta un límite de `rango`. «ir a» mira lo que el jugador sabe (solo salas exploradas,
puertas según la memoria, o según el estado en vivo si tocan su sala) y busca desde el destino hasta sacar la sala del
jugador. Buscar hacia atrás da de una vez la distancia de todos los vecinos de la sala del jugador; el desempate
`(id de destino, dirección)` es el mismo que el del cazador, pero se aplica sobre otro grafo.

**Estampas: la regla A.**

- *Qué cuesta:* tras cada paso de «ir a», la búsqueda guardada del cazador queda invalidada y se hace una búsqueda
  más en el siguiente turno del cazador. Solo ocurre mientras haya cazadores activos. La estampa se toma lo primero,
  antes de cualquier retorno temprano, así que incluso un «ir a» sin ruta invalida esa caché (hay una prueba de cada
  caso en `tests/test_ir_a_viaje.py`).
- *Qué se evita:* los dos campos de la regla B.
- Es la condición 4 de la reutilización de la búsqueda guardada de la sección 5.2: ninguna otra búsqueda puede haber
  escrito las marcas de `Sala` desde entonces.

**Complejidad** (`plan.md`, «Complexity (engine)»).

- Un paso de «ir a»: O(V_k log V_k + E_k) sobre la región conocida más cercana al destino que el jugador, más
  O(grado) para el desempate entre las salidas de la sala del jugador.
- Un viaje recalcula la ruta en cada paso y no guarda nada entre pasos (FR-020), así que un viaje de p pasos hace
  p búsquedas.
- Explorar al moverse: O(grado) sin antorcha y O(grado²) con antorcha, más O(grado) para la memoria de puertas.
- Deshacer: las escrituras nuevas van al cuadro del movimiento en el historial, O(grado) u O(grado²) entradas más.

**Evidencia empírica.**

- *Costo de la regla A en el ciclo de eventos:* `bench_ciclo` antes y después de la función
  (`specs/003-fog-of-war/bench-antes-ciclo.txt` y `bench-despues-ciclo.txt`, tres corridas cada una). Comparando la
  mejor de las tres corridas de cada escenario, ningún escenario es más de 10 % más lento, ni en p99 ni en promedio.
  El p99 más alto es el de `extremo` (11.68 ms antes; 9.84 ms después) y todos cumplen el límite de 20 ms.
- *Costo de la ruta:* con 300 salas (el tamaño de cripta-06) el p99 de la ruta es de 2.6 a 3.0 ms contra el límite de
  5 ms (`specs/003-fog-of-war/bench-ir-a.txt`). El detalle y la optimización que hizo falta están en 5.3.1.

**Coincidencia con el `plan.md` original.** La decisión de esta sección, sí. El `plan.md` de antes de implementar
(commit `6166666`) ya tenía la búsqueda hacia atrás desde el destino en una clase propia, la regla A de estampas
(tomada lo primero, antes de cualquier retorno), el montículo compartido con `vaciar()` y el veredicto de p99 ≤ 5 ms
de la ruta. Lo que cambió durante la implementación fue la medición, no la decisión: el tamaño del veredicto pasó de
100 salas a 300, y se optimizó el montículo y el bucle de la ruta (5.3.1; código en `f429f82`, plan sincronizado en
`8243510`).

**Límites conocidos.**

- Por la regla A, cada paso de «ir a» invalida la búsqueda guardada de los cazadores y cuesta una búsqueda más en el
  siguiente turno de un cazador, mientras haya cazadores activos.
- Un viaje no reutiliza la búsqueda entre pasos: cada paso paga la búsqueda completa sobre la región conocida.
- El costo crece con la región conocida; los números por tamaño están en 5.3.1.
- La medición del ciclo con la regla A (`bench-despues-ciclo.txt`, commit `edca9b8`) es anterior a la optimización del
  montículo de `f429f82`, que el cazador también usa. No se volvió a medir `bench_ciclo` después de ese cambio; solo
  están las pruebas de equivalencia del cazador (`tests/test_cazador_equivalencia.py`) y las del montículo.

**Enlaces.** Spec: [`specs/003-fog-of-war/spec.md`](../specs/003-fog-of-war/spec.md). Plan:
[`specs/003-fog-of-war/plan.md`](../specs/003-fog-of-war/plan.md) («The route search» y «Complexity (engine)»).
Investigación: [`research.md`](../specs/003-fog-of-war/research.md), R1, R2, R6 y R7.

### 5.3.1 Rendimiento de «ir a» con 300 salas

**Problema.** FR-026 exige que el cálculo de la ruta de un paso de «ir a» tome a lo sumo 5 ms en el p99, sobre el
mapa conocido completo de la cripta de referencia. La mayor publicada (cripta-06) tiene 300 salas, así que el
veredicto de `bench_ir_a` se mide con una cripta sintética sembrada de **300 salas**, todas exploradas y con todas las
puertas recordadas abiertas; 100, 500 y 1000 salas son solo información (R7). Se imprimen promedio, p99 y máximo de la
ruta sola y del paso completo (ruta, movimiento y ciclo de eventos). Además se quería un margen propio, que no está en
la spec: p99 del paso completo ≤ 3 ms. La primera medición con 300 salas no lo dejaba (ver «Evidencia»).

**Alternativas consideradas.**

- *Cambiar el algoritmo.* No hacía falta. Antes de optimizar se revisó que la búsqueda ya se detiene en cuanto sale la
  sala del jugador, y que no hay trabajo proporcional a todo el mapa conocido en cada paso: no se limpian marcas (las
  estampas lo evitan), no se reconstruye ningún subgrafo y no se guarda nada entre pasos (FR-020). El trabajo es el de
  la región conocida más cercana al destino que el jugador; con pares lejanos en 300 salas es casi todo el mapa, y por
  eso el costo se nota.
- *Guardar la ruta entre pasos.* Lo prohíbe FR-020: la ruta se recalcula con el conocimiento de cada momento.
- *Bajar el costo por operación sin cambiar el comportamiento.* Es lo que se hizo. El perfil con `cProfile` mostró
  que el tiempo se iba sobre todo en las llamadas a `_antes` del montículo (el resto, en el bucle de `siguiente_paso`,
  `partida.puerta_recordada` y la propiedad `Salida.costo`); la salida de ese perfil no se guardó.

**Decisión** (detalle de implementación, sin cambiar la especificación).

1. `structures/monticulo.py`: `insertar` y `extraer` comparan en línea, con la misma regla que `_antes` (prioridad y
   luego secuencia), en vez de llamar a un método por cada comparación. El comportamiento es idéntico (lo cubren
   `tests/test_monticulo.py` y las pruebas de equivalencia del cazador, que lo comparte).
2. `model/ruta_conocida.py`: la puerta recordada se lee en línea (en vivo si toca la sala del jugador, si no `memoria`),
   se lee `costo_declarado` con el mismo valor por defecto que `Salida.costo`, y no se inserta en el montículo una sala
   cuya distancia ya no puede dar una ruta mejor que la hallada hasta el jugador (`nd >= dist(jugador)`). Una vecina
   útil tiene `dist < d`, así que el desempate no cambia.

**Complejidad.** Sin cambio asintótico: sigue siendo O(V_k log V_k + E_k) por paso. Bajan las constantes; la poda
de salas no mejora el peor caso.

**Evidencia empírica** (300 salas, semilla 1, tres corridas guardadas en `specs/003-fog-of-war/bench-ir-a.txt`).

| | Antes (sin archivo guardado) | Después |
|---|---|---|
| p99 de la ruta | 5.965 / 4.469 ms | 2.740 / 2.991 / 2.645 ms |
| máximo de la ruta | 9.757 / 5.775 ms | 9.626 / 5.896 / 4.106 ms |
| p99 del paso completo | 6.131 / 4.712 ms | 2.472 / 2.982 / 2.622 ms |
| máximo del paso completo | 8.890 / 7.888 ms | 3.784 / 4.517 / 3.891 ms |

Cumple el límite de 5 ms en las tres corridas, con margen. El paso completo queda bajo 3 ms en las tres, pero por poco
(2.472 a 2.982 ms): el margen de 3 ms es justo, no holgado. Por tamaño (p99 de la ruta, en las tres corridas):
100 salas, 0.95 a 1.74 ms; 500 salas, 4.11 a 4.82 ms; 1000 salas, 8.58 a 9.29 ms.

**Límites conocidos.**

- Con 1000 salas una cripta así no cumpliría 5 ms (8.58 a 9.29 ms); con 500 queda cerca (4.11 a 4.82 ms). Esos tamaños
  no son el veredicto de la spec.
- Los máximos tienen picos ocasionales: el máximo de la ruta con 300 salas llega a 9.6 ms en una corrida, y hay picos
  de hasta 17.8 ms en el paso completo con 100 salas. No entran en el veredicto, que es el p99. Que vengan de la
  máquina y no del algoritmo es lo más probable, pero no se comprobó.
- La columna «Antes» y el perfil con `cProfile` salen de corridas hechas durante la optimización cuya salida no se
  guardó (el `bench-ir-a.txt` guardado solo tiene las corridas posteriores), así que no se pueden verificar con los
  archivos del repositorio. El mensaje del commit `f429f82` las resume como «de 5.0-6.0 ms a 2.6-3.0 ms» (ruta) y «de
  4.7-6.1 ms a 2.5-3.0 ms» (paso completo). Tampoco se guardó una serie aparte de siete repeticiones, de la que se
  recuerda una mediana del p99 de 2.7 ms (ruta) y 2.8 ms (paso completo), con máximos de 3.4 y 3.3 ms entre
  repeticiones; no está verificada.
- La medición usa una cripta sintética de 300 salas, toda explorada y con todas las puertas abiertas, no cripta-06
  misma. Si el curso publica otra cripta de referencia, la medición se repite con ella (R7).
- Antes de este cambio, `bench-ir-a.txt` (commit `d393573`) medía con 100 salas: 1.053 ms de p99 de la ruta. Ese
  tamaño no revelaba el problema.

**Coincidencia con el `plan.md` original.** El plan de antes de implementar (`6166666`) pedía el veredicto con 100 salas;
la decisión de separar las búsquedas, la regla A y el límite de 5 ms no cambiaron. Lo que cambió: el tamaño del
veredicto (100 a 300 salas, según la cripta publicada más grande), y la optimización del montículo y de la ruta, que
el plan no preveía. El plan se sincronizó con el programa entregado en `8243510`.

**Enlaces.** Spec: FR-026, FR-027 y SC-007 de [`specs/003-fog-of-war/spec.md`](../specs/003-fog-of-war/spec.md). Plan:
[«Measurements»](../specs/003-fog-of-war/plan.md). Investigación: R7 de
[`research.md`](../specs/003-fog-of-war/research.md). Código: `bench/bench_ir_a.py`.

## 5.4 Verificación de resolubilidad: una pasada y no una por llave

**Problema.** Obtener una llave puede abrir una región entera, y repetir el recorrido completo por cada llave no
cumple: el costo total debe crecer de forma aproximadamente lineal con salas, salidas y llaves (FR-019). El reporte
de una cripta no resoluble necesita la frontera bloqueada y las dependencias entre llaves, y eso debe salir del mismo
recorrido (FR-013). Los ciclos de dependencia se detectan de forma determinista y se reporta el ciclo concreto. El
`--bench` mide la alternativa ingenua de un recorrido por llave con criptas sintéticas de muchas llaves encadenadas.

**Alternativas consideradas** (`research.md`, R4, R5 y R7).

| Alternativa | Por qué no |
|---|---|
| Una pasada completa por llave: tomar una llave, recorrer otra vez toda la cripta con las llaves que se tienen, repetir | Es lo primero que se escribe, pero cuesta `O(K (V + E))` y se vuelve cuadrática cuando cada llave abre una región (llaves encadenadas). Se dejó solo como alternativa medida en el benchmark y como oráculo de las pruebas. |
| Ordenamiento topológico de un grafo de dependencias entre llaves | Para armarlo hay que saber de qué llaves depende cada una, que es justo lo que calcula la pasada: haría falta otra pasada. |
| Una cola de prioridad ordenada por otra cosa (id de sala, orden de descubrimiento) | No cumple FR-011: gana la llave de menor id, comparada como texto. |
| Una búsqueda de ciclos por llave | Sería otra pasada por llave. |
| Buscar la llave por id con un diccionario | Prohibido; se usa el vector ordenado con búsqueda binaria que ya existía (R7). |

**Decisión.** Decidir si una cripta se puede ganar con **una sola pasada** que hace crecer a la vez la región
alcanzable y las llaves tomadas (`Verificador.verificar`, `model/solvabilidad_logica.py`): llegar a una sala vuelve
obtenibles las llaves que hay en ella (van a un montículo ordenado por id, el de `structures/monticulo.py`), se toma
la de menor id, se liberan las puertas que esperaban esa llave y la región vuelve a crecer. El orden en que salen las
llaves del montículo es el orden de llaves, y no depende del orden en que el servicio lista las llaves ni las salidas
(FR-010).

**El informe sale de lo que deja la pasada.** Las llaves que no se tomaron, las salidas que quedaron esperando (que son
justo la frontera bloqueada) y dónde está cada llave ya están en el estado final de la pasada. Los ciclos salen de un
barrido lineal sobre las únicas salas que la pasada no alcanzó: cada llave de la frontera, en orden de id, inunda esas
salas ignorando las cerraduras y las etiqueta si no tenían etiqueta, así que cada sala queda con la menor llave que
llega a ella (la guardiana); seguir guardianas da cada ciclo una vez.

**Complejidad** (`plan.md`, «Complexity (engine)»). Verificación: `O((V + E) log V + K log K)` en tiempo y `O(V + E + K)`
en espacio. Cada sala entra una vez, cada salida se examina una vez desde su origen y cada llave entra y sale del
montículo una vez; el `log V` es buscar la posición de una sala en el vector ordenado. El barrido de ciclos suma
`O(V_U + E_U)`, con U la parte de la cripta que la pasada no alcanzó. La alternativa ingenua cuesta `O(K (V + E))`.

**Evidencia empírica** (tres corridas, semilla 1, `specs/004-crypt-solvability/bench-solvabilidad.txt`;
`python -m bench.bench_solvabilidad` dura entre 10 y 20 s según la máquina).

| | Resultado |
|---|---|
| Cripta con la forma de la mayor publicada (300 salas, 4 llaves), con y sin llave de salida alcanzable | máximo de la verificación 5.628, 22.793 y 3.924 ms por corrida (límite 200 ms, FR-018) |
| Llaves encadenadas, cada ×10 salas | la verificación tarda de 13.2 a 22.0 veces más; la alternativa de una pasada por llave, de 66.9 a 143.2 veces más |
| 9 849 salas y 200 llaves (el «10 000 y 200» del benchmark) | verificación 68.5 a 71.8 ms; una pasada por llave, 7.4 a 8.5 s |
| 98 049 salas y 2 000 llaves (el «100 000 y 2 000») | verificación 1.13 a 1.51 s; la alternativa no se mide |

Las salas y las salidas visitadas son siempre las de la cripta, sin importar las llaves (por ejemplo 98 049 salas y
196 096 salidas con 2 000 llaves). El crecimiento de la verificación es un poco más que lineal por el `log V` de la
búsqueda binaria y por la memoria.

**Límites conocidos.**

- La cripta de 300 salas es sintética, con la forma de cripta-06 (300 salas, 4 llaves), no cripta-06 misma.
- El máximo con 300 salas varía bastante entre corridas (3.9 a 22.8 ms); sigue muy por debajo de 200 ms.
- La alternativa de una pasada por llave no se mide con 98 049 salas: serían unos 2×10⁸ recorridos de sala, muchos
  minutos en Python.
- Cuando varias llaves de la frontera llegan a la misma región, la guardiana es la de menor id: es una elección fija,
  no una prueba de que la región solo se pueda abrir con esa llave (`research.md`, R5).
- `--replay` y cargar una partida guardada dentro de una sesión ya abierta no vuelven a verificar (FR-014).

**Coincidencia con el `plan.md` original.** Sí. El `plan.md` de antes de implementar es el de la versión corregida
tras el análisis (commit `6bb5d63`, que corrigió el de `0698354`) y no cambió durante la implementación. La
corrección de `6bb5d63`, todavía antes de implementar, cambió el costo escrito de `O(V + E log K + K log K)` a
`O((V + E) log V + K log K)` (por buscar la posición de cada sala en el vector ordenado) y limitó la alternativa de
una pasada por llave a 10 000 salas y 200 llaves. Las mediciones no hicieron cambiar nada.

**Enlaces.** Spec: [`specs/004-crypt-solvability/spec.md`](../specs/004-crypt-solvability/spec.md) (FR-008 a FR-013,
FR-018, FR-019). Plan: [`specs/004-crypt-solvability/plan.md`](../specs/004-crypt-solvability/plan.md) («The pass»,
«Complexity (engine)» y «Measurements»). Investigación:
[`research.md`](../specs/004-crypt-solvability/research.md), R4, R5 y R7. Esto complementa el
[Documento de Decisiones de la primera parte](Documento_de_Decisiones.pdf).

## 5.5 Línea de tiempo

**Problema.** Consultar cualquier instante no debe obligar a aplicar o deshacer los cambios de más de K acciones
del jugador. La memoria debe crecer con los cambios ocurridos más un punto de control cada K acciones, nunca con
acciones por tamaño del estado. Ubicar el punto de control más cercano a un instante es una búsqueda frecuente
cuyo costo pesa en partidas largas, y un pergamino debe recortar la línea sin recorrer toda la historia. Hay que
mostrar con mediciones cómo cambian la memoria y el tiempo de consulta con al menos tres valores de K, justificar
el K por defecto y documentar con evidencia si se reconstruye hacia adelante o hacia atrás.

Especificación: [`specs/005-timeline/spec.md`](../specs/005-timeline/spec.md). Plan:
[`specs/005-timeline/plan.md`](../specs/005-timeline/plan.md). Razonamiento completo, con las alternativas:
[`specs/005-timeline/research.md`](../specs/005-timeline/research.md) (R1 a R12).

**Decisión.** La línea de tiempo guarda, por cada acción del jugador que sigue en la partida, un registro pequeño
(número, reloj de la decisión y la acción ya resuelta: tipo y objetivo; `research.md`, R3) y, cada K acciones, un
**punto de control**: un registro escrito a mano con solo los campos que cambian, con las entidades por id,
incluido el estado del generador aleatorio y el mapa conocido (`model/registro_estado.py`, R2). Para responder
`historia t` o `historia #k` toma el punto de control anterior, arma con él un mundo aparte y **reproduce hacia
adelante** a lo más K acciones del jugador con los métodos reales de `Partida`, deteniéndose según la regla del
instante t (R7). El mundo aparte es otro grafo de objetos: la consulta no toca la partida en vivo, su historial de
deshacer, `partida.log`, el reloj, la red ni el presupuesto de peticiones (R5, R8). Además:

- **Pergamino** (R6). Leer un pergamino recorta la línea desde el final: borra los registros de acción con número
  mayor que n (las acciones que quedan) y los puntos de control de límite mayor que n. No toma ni reemplaza ningún
  punto de control, así que sigue habiendo a lo más uno cada K acciones (FR-019). Lo que el deshacer de la parte
  uno deja fuera a propósito (el pergamino consumido, los pergaminos que entran o salen del suelo o del
  inventario, el contador de instancias de la fábrica y las salas pobladas por movimientos revertidos) se guarda
  en el **libro de efectos que el deshacer omite**, etiquetado con el punto de retroceso; una consulta aplica esas
  entradas cuando la reproducción pasa por ese punto.
- **Guardado** (R9). El formato pasa a la versión 2: la cabecera agrega K y el archivo sigue guardando los
  comandos, no la línea de tiempo. Cargar reejecuta los comandos, como en la parte uno, y eso reconstruye la
  partida, el historial, los registros de acción, los puntos de control y el libro. Al cargar manda el K
  guardado; un `--checkpoint-cada` distinto se ignora con un aviso. Un archivo de la versión 1 se rechaza como
  incompatible.
- **K por defecto**: 10, elegido con las mediciones (5.5.1).

**Por qué se descartaron las alternativas** (`research.md`, R1, R6 y R9):

| Alternativa | Por qué no |
|---|---|
| Invertir hacia atrás con el historial de deshacer | Los cierres del historial escriben sobre los objetos de la partida en vivo, y una consulta no puede modificar la partida (FR-006, FR-008). Los cierres no se pueden escribir en el archivo binario (FR-017). La parte uno guarda solo 5 cuadros; guardarlos todos dejaría 83.0 cierres por acción, unos 178 115 KB a 5 000 acciones (tamaño superficial de los cierres). El deshacer omite a propósito efectos de los pergaminos (§2.11), así que invertir miles de acciones acumularía esa diferencia. Invertir sí es más barato por acción (157.9 µs contra 635.7 µs de reproducir hacia adelante, `specs/005-timeline/bench-linea-tiempo.txt`), pero lo que lo descarta es lo anterior, no el tiempo. |
| Sin puntos de control (solo el estado inicial; reproducir desde el comienzo) | Rompe FR-020: una consulta reproduce hasta toda la partida. Medido en `referencia`: hasta 5 000 acciones reproducidas y p99 2777.59 ms. |
| Una copia completa en cada acción | FR-021 lo prohíbe: la memoria crecería con acciones por tamaño del estado. «Copiar todo» cuesta de 588.5 a 12 650.6 µs por copia (`specs/005-timeline/bench-antes.txt`); por 5 000 acciones son entre 2.9 y 63 s (calculado con esas cifras). Además `deepcopy` copiaría los cierres del historial por referencia (la copia desharía la partida en vivo) y, a través de `creador_objetos`, el catálogo, la caché y el cliente HTTP (R2). |
| Un punto de control extra en el punto de retroceso de un pergamino | Es exacto, pero agrega una copia fuera de la cuadrícula de K, que FR-019 no permite (R6). |
| Guardar los registros y los puntos de control en el archivo | Duplica lo que la carga ya recalcula al reejecutar los comandos y necesitaría un formato para el registro de estado (R9). |

**Complejidad** (`specs/005-timeline/plan.md`, «Data Structures and Complexity»). A = acciones del jugador que
quedan, K = separación de los puntos de control, R y E = salas y salidas, S = tamaño del estado que cambia, c =
costo de una acción, r = acciones que revierte un pergamino.

- Registrar una acción: O(1) amortizado (agregar a tres vectores paralelos).
- Tomar un punto de control: O(S), una vez cada K acciones.
- Ubicar el punto de control de un límite b (acciones ya hechas): O(1), la casilla `b // K`.
- Ubicar la acción de un instante t: O(log A), búsqueda binaria propia sobre el vector de relojes
  (`ultimo_menor_o_igual`, R4); los relojes crecen estrictamente porque el intervalo del jugador es al menos 1.
- Recortar tras un pergamino: O(r + puntos de control descartados + entradas del libro reetiquetadas); no depende
  de A (FR-011).
- Una consulta: O(R + E) para limpiar el grafo reutilizado, O(S) para restaurar el punto y a lo más K·c para
  reproducir (FR-020).
- Memoria: A registros de acción + (A/K)·S de puntos de control + el libro (los efectos omitidos de las últimas 5
  acciones y los que guardó cada pergamino). Nunca A·S (FR-021). Medido: la memoria crece con razón 2.05 de
  A = 5 000 a 2A (K = 50).

**¿Se cumple el límite de 50 ms del enunciado?** FR-024 pide p99 ≤ 50 ms con el K por defecto, en una partida de
al menos 5 000 acciones.

- **Se cumple** en el mundo `referencia` (esqueleto de cripta-06 y 30 cazadores) con K = 5 (p99 7.41 ms), K = 10
  (16.54 ms en la corrida de T068, 14.54 ms en la prueba de tamaño completo T069 y 15.35 ms en la corrida
  completa de `python main.py --bench`) y K = 50 (27.85 ms). El peor caso con K = 10 fue 19.36 ms (T068) y
  36.33 ms (T069).
- **No se cumple** en `referencia` con K = 200 (97.55 ms) ni sin puntos de control (2777.59 ms).
- **No se cumple** en el mundo de esfuerzo `grande` (100 salas, 100 enemigos) con K = 10, el K por defecto: en la
  corrida completa de `--bench` el p99 fue **54.31 ms**, por encima de 50 ms. En la corrida de T068 había dado
  47.64 ms. Con K = 50 en `grande` el p99 es 123.13 ms. El veredicto de FR-024 se toma en `referencia` (plan.md),
  pero con el K por defecto una consulta en una cripta como `grande` puede pasar de 50 ms.

Fuentes: `specs/005-timeline/bench-linea-tiempo.txt` (T068), `specs/005-timeline/tasks.md` (T069) y
`specs/005-timeline/quickstart.md` (corrida completa de `--bench`). Las tablas completas están en 5.5.1 y en 5.6.2.
La corrección se prueba con un oráculo que es la propia partida: una partida sembrada guarda el resumen en vivo en
cada decisión y después se consulta cada instante y cada `#k` (`tests/test_linea_tiempo_oraculo.py`, R12).

**Coincidencia con el `plan.md` original.** En lo principal, sí. El `plan.md` de antes de implementar (commit
`21f70fd`) ya tenía la reproducción hacia adelante desde puntos de control, los registros de estado escritos a mano,
el libro de efectos omitidos, el formato v2 con los comandos y K, y la regla para elegir K (el mayor K con p99 ≤ 25
ms en `referencia`), que se mantuvo sin cambios. Lo que cambió:

- **Después de la primera medición** se agregó el grafo de salas reutilizable (`data/grafo_reutilizable.py`), que
  el plan dejaba como alternativa en R5 si armar el grafo pasaba de un tercio de la consulta: era el 50.9 % con
  K = 10 (p99 23.88 ms). Con el grafo reutilizado bajó a 6.3 % y el p99 a 16.54 ms. A diferencia de R5, la limpieza
  no sigue qué salas tocó la consulta anterior: limpia todas las salas y salidas.
- K = 5 se agregó al conjunto medido, y el K provisional de 50 del plan se reemplazó por el medido, 10.
- **Antes de implementar** se descartaron dos ideas de un borrador anterior, y el plan del commit `21f70fd` ya no
  las tiene: volver a anclar la línea en el pergamino con un punto de control extra en el punto de retroceso
  (decisión 2 del grupo, por FR-019) y guardar los puntos de control en el archivo de guardado (decisión 3).

**Límites conocidos.**

- En `grande` con K = 10 el límite de 50 ms no se cumple (54.31 ms en la corrida completa de `--bench`), como se
  dice arriba. Bajar K lo mejoraría a cambio de memoria, pero no se midió K < 10 en `grande`.
- Las corridas varían en la misma máquina: `grande` con K = 10 dio 47.64 y 54.31 ms; `referencia` con K = 10, 16.54,
  14.54 y 15.35 ms.
- La memoria es el precio de K = 10: 23 261.6 KB de puntos de control a 5 000 acciones en `referencia` (24 061.5 KB
  en `grande`), contra 4 676.4 KB con K = 50.
- Reproducir hacia adelante cuesta unas 4 veces más por acción que invertir (635.7 contra 157.9 µs). Lo que queda
  del tiempo de una consulta es sobre todo reproducir las acciones, en especial los turnos de los cazadores.
- La limpieza del grafo reutilizado recorre todas las salas y salidas en cada consulta, O(R + E), aunque solo sean
  asignaciones.
- Cargar una partida reejecuta todos los comandos con la grabación activa, así que el tiempo de carga crece con la
  partida; no se midió por separado (R9).
- Las entradas que guarda un pergamino en el libro se quedan para siempre: el libro crece con los pergaminos leídos
  (en la medición, 6 lecturas y 6 entradas guardadas).
- La posición de un objeto dentro de la lista del suelo puede diferir de la partida en vivo después de un
  pergamino (R6, riesgo residual). El suelo no está en el resumen de FR-004 y `recoger` busca por id, así que no
  cambia una respuesta.
- El mundo `extremo` (100 salas, 300 enemigos) no tiene cifras de la línea de tiempo en
  `specs/005-timeline/bench-linea-tiempo.txt`.

### 5.5.1 K por defecto (un punto de control cada K acciones)

**Decisión.** `K_POR_DEFECTO = 10` (`model/linea_tiempo_logica.py`). La regla se fijó en
`specs/005-timeline/plan.md` («Default K») antes de medir: el **mayor** K medido cuyo p99 de `historia` en el mundo
`referencia` sea ≤ 25 ms (la mitad del límite de 50 ms de FR-024, para dejar margen a máquinas más lentas); la
memoria de cada K se informa al lado y no se usa para elegir.

**Evidencia empírica** (`specs/005-timeline/bench-linea-tiempo.txt`; 2026-11-18, Intel Core i5-1155G7 @ 2.50 GHz,
Windows 11, Python 3.14.6, sin otra carga; 5 000 acciones del jugador, semilla 7, 200 consultas por fila y 20 en
`none`):

| K (`referencia`) | Puntos | Memoria de puntos | Memoria de acciones + libro | Máx. reproducidas | p99 (ms) | Promedio (ms) | Peor (ms) |
|---|---|---|---|---|---|---|---|
| 5 | 1001 | 46 491.1 KB | 131.9 KB | 5 | 7.41 | 2.94 | 8.33 |
| **10** | **501** | **23 261.6 KB** | **127.3 KB** | **10** | **16.54** | **5.13** | **19.36** |
| 50 | 101 | 4 676.4 KB | 124.1 KB | 50 | 27.85 | 11.94 | 32.76 |
| 200 | 26 | 1 189.2 KB | 123.5 KB | 199 | 97.55 | 43.28 | 131.30 |
| none (solo el punto 0) | 1 | 14.2 KB | 123.3 KB | 5000 | 2777.59 | 1147.43 | 2777.59 |

K = 10 es el mayor con p99 ≤ 25 ms; K = 50 queda en 27.85 ms. En el mundo de esfuerzo `grande` (solo información)
K = 10 da p99 47.64 ms y K = 50, 123.13 ms. La prueba de tamaño completo (T069: K = 10, 5 000 acciones en
`referencia`) dio p99 14.54 ms, peor 36.33 ms, promedio 5.11 ms. La memoria crece lineal con las acciones (razón
2.05 de A = 5 000 a 2A, medida con K = 50).

**Lo que cuesta.** Unos 23 MB de puntos de control a 5 000 acciones, contra 4.7 MB con K = 50: el precio de
consultas más rápidas.

**Cambio necesario para llegar.** Armar el grafo aparte en cada consulta era el 50.9 % del tiempo con K = 10 (p99
23.88 ms). Como prevé la investigación R5 de la spec, la consulta ahora reusa un solo grafo por servicio y lo limpia
entre consultas (`data/grafo_reutilizable.py`): devuelve a su valor del esqueleto los campos que un punto
restaurado o una acción reproducida pueden cambiar (de cada sala, conocimiento, rastro, objetos, inactivos, trampas y
marcas de búsqueda; de cada salida, cerrada y memoria). Con eso el armado bajó a 6.3 % del tiempo y el p99 de K = 10,
a 16.54 ms. Lo que queda es reproducir las acciones (sobre todo los turnos de los cazadores).

## 5.6 Revisión de las decisiones de la primera parte

**Problema.** Los cazadores, los costos variables de movimiento y la línea de tiempo cambian la carga sobre
estructuras que ya existían, sobre todo la agenda de eventos y el historial de retroceso. Hay que repetir las
mediciones de la primera parte con esa carga nueva: si una decisión deja de servir, se cambia y se documenta el
antes y el después; si sigue sirviendo, se muestra con datos.

### 5.6.1 Agenda de eventos

**Decisión.** La agenda se queda como el **montículo binario** de la primera parte (`structures/agenda.py`).
Sin cambios de código en ninguna de las dos specs. Se revisó dos veces, en cada ocasión con la regla de decisión de
la spec 001, fijada antes de medir: se mantiene el montículo si es el más rápido, o está a menos de 10 % del más
rápido, en cada tamaño ≥ 300 de eventos pendientes. Se repitió la comparación de la primera parte (montículo, lista
sin ordenar, lista ordenada) con la carga que trajo cada spec: costos de salida variables (001) y decenas de
cazadores (002). No se agregó ningún candidato nuevo.

**Por qué se descartaron las listas** (`specs/001-exit-costs/research.md`, R6, y `plan.md` de la 002, R12):

| Alternativa | Costo | Por qué no |
|---|---|---|
| Lista sin ordenar | `extraer` O(n), `programar` O(1) | La agenda extrae un evento por cada uno que programa; el recorrido completo en cada extracción domina. |
| Lista ordenada | `programar` O(n), `extraer` O(1) | Insertar en orden cuesta O(n) por evento. |
| Montículo binario | `programar`, `extraer`, `cancelar` y `reprogramar` O(log n) | El costo no depende de los intervalos, así que no le afectan los costos variables. |

**Complejidad.** Las operaciones de la agenda no cambiaron con ninguna spec. Lo que cambia es *cuántas* se piden
por acción del jugador; eso está medido abajo.

**Evidencia empírica.**

*Spec 001: costos de salida variables* (`specs/001-exit-costs/bench-parte1.txt` y `specs/001-exit-costs/bench-parte2.txt`; en la primera parte, las filas de operaciones por acción usaron salidas de costo 100 y las filas de µs usaron un incremento aleatorio, como se explica debajo de la tabla):

| Medición | Primera parte (`specs/001-exit-costs/bench-parte1.txt`) | Spec 001 (`specs/001-exit-costs/bench-parte2.txt`: costos variables) |
|---|---|---|
| `programar` (= `extraer`) por acción, 300 / 1000 / 3000 enemigos | 301.0 / 1001.0 / 3001.0 | 123.0 / 414.8 / 1237.4 |
| Eventos pendientes a la vez (máximo) | 300 / 1000 / 3000 | 300 / 1000 / 3000 |
| `cancelar` y `reprogramar` por acción | 0.0 | 0.0 |
| µs por extraer y programar, 3000 pendientes (montículo / lista sin ordenar / lista ordenada) | 4.6 / 180.2 / 131.5 | 7.1 / 538.4 / 294.2 |
| µs por cancelar y programar, 3000 pendientes (montículo / sin ordenar / ordenada) | 2.5 / 37.3 / 249.3 | 7.4 / 118.9 / 555.0 |

Las filas de µs usan un incremento aleatorio `randint(1, 200)` en la primera parte y `intervalo(costo, velocidad)` con costos de {1, 10, 50, 100, 250, 500, 1000} y velocidades en [50, 200] en la 001 (`bench/bench_agenda.py`); «cancelar y programar» es una re-corrida del mismo método. Los candidatos son `AgendaHeap` (envuelve `AgendaEventos` de `structures/agenda.py`), `AgendaListaSinOrdenar` y `AgendaListaOrdenada`, estas dos definidas en el propio benchmark.

Con costos variables hay menos operaciones por acción, porque las salidas caras demoran a los enemigos. Con el
modelo de incremento variable de `specs/001-exit-costs/bench-parte2.txt` (tamaño 300 / 1000 / 3000), el montículo marca 6.7 / 9.4 / 7.1 µs contra
44.8 / 154.6 / 538.4 µs de la lista sin ordenar y 23.8 / 116.3 / 294.2 µs de la ordenada. A 300 pendientes el montículo es 3.6 veces más rápido que la mejor alternativa (23.8 µs de la lista ordenada).

*Spec 002: cazadores* (`specs/002-hunter-enemy/bench-agenda-cazadores.txt`, tres corridas):

| Enemigos | Cazadores | `programar` = `extraer` por acción | Máx. pendientes | Solo errantes, costos variables |
|---|---|---|---|---|
| 300 | 30 | 142.1 | 300 | 123.0 |
| 1000 | 30 | 435.7 | 1000 | 414.8 |
| 1000 | 100 | 475.4 | 1000 | 414.8 |
| 3000 | 30 | 1260.7 | 3000 | 1237.4 |
| 3000 | 300 | 1412.2 | 3000 | 1237.4 |

`cancelar` y `reprogramar` valen 0.0 en todas las filas. Los cazadores agregan entre 1.9 % y 15.5 % de operaciones por
acción (calculado con las cifras de la tabla: 142.1 / 123.0 con 300 enemigos y 30 cazadores; 1260.7 / 1237.4 con 3000 y 30; con 100 y 300 cazadores, 14.6 % y 14.1 %; el `plan.md` de la 002 redondea a «2 % y 15 %»); la forma de la carga no cambia, porque
sigue habiendo un evento pendiente por actor.

| µs por extraer y programar, modelo de incremento variable (tres corridas) | 300 pendientes | 1000 | 3000 |
|---|---|---|---|
| Montículo | 5.6 – 9.3 | 7.5 – 13.2 | 6.7 – 14.2 |
| Lista sin ordenar | 32 – 44 | 90 – 147 | 325 – 462 |
| Lista ordenada | 24 – 37 | 79 – 114 | 212 – 377 |

**Coincidencia con los `plan.md` originales.** Sí, en las dos specs. Ambos planes (001, commit `955acb5`; 002,
commit `472c374`) dejaron la agenda como «montículo, a confirmar con la medición», con la regla escrita antes de medir. En las dos specs el montículo
fue el más rápido en todos los tamaños ≥ 300 (en la 002, en las tres corridas), así que la regla se cumple y
`structures/agenda.py` no cambió. Ninguna medición cambió la decisión.

**Límites conocidos.**

- La máquina es ruidosa: en la 001 todas las columnas, incluido el control de incremento fijo, salieron más lentas que en la primera parte y el
  tiempo del propio montículo varía hasta 2 veces entre corridas. Por eso las comparaciones valen dentro de una corrida, no contra los µs absolutos de otra.
- Con 100 pendientes, que está fuera de la regla (que cuenta desde 300), el montículo no siempre gana: en la 002, corrida 1, con incremento variable
  el montículo marca 11.3 µs y la lista ordenada 6.9 µs; en la 001, 6.9 µs contra 7.0 µs. En «cancelar y programar» con 100 pendientes la lista sin ordenar también le gana al montículo en varias corridas (2.4 contra 3.3 µs en `specs/001-exit-costs/bench-parte2.txt`).
- En estas cargas (el jugador solo espera: `esperar_jugador`) `cancelar` y `reprogramar` valen 0.0 por acción, así que la tabla de «cancelar y programar» solo pesa como control y la decisión se apoya en extraer y programar. El juego sí las usa en otras situaciones (`model/efectos_logica.py` cancela y reprograma eventos por efectos de velocidad; `model/partida_logica.py` cancela el turno de activación de un enemigo), que estas mediciones no cubren.
- Las cargas son sintéticas (100 salas, enemigos errantes y cazadores con semilla): no se midió la cripta publicada para la agenda.

### 5.6.2 Historial de deshacer

**Decisión.** El historial de deshacer se queda como en la primera parte (`structures/historial.py`: cierres en un
anillo de 5 cuadros). La línea de tiempo de la spec 005 no lo reemplaza ni lo agranda: el pergamino sigue
deshaciendo con él, y la consulta del pasado reproduce hacia adelante desde un punto de control
(`specs/005-timeline/research.md`, R1). La columna «copiar todo» de la primera parte (copia completa con
`deepcopy`, que no se usa en el juego) se reemplazó por «capturar punto», que es lo que la línea de tiempo copia de verdad.

**Evidencia empírica** (`specs/005-timeline/bench-despues.txt`: tres corridas seguidas de `bench_historial`,
K = 10; antes: `specs/005-timeline/bench-antes.txt`). µs por operación; «parte uno» se mide en vivo en la misma
corrida, sin línea de tiempo:

| Escenario (salas, enemigos) | Acción antes | Acción parte uno | Acción con línea | Deshacer antes | Deshacer parte uno | Deshacer con línea | Copiar todo antes | Capturar punto | Cierres guardados |
|---|---|---|---|---|---|---|---|---|---|
| pequeño (10, 10) | 84.3 | 85.9 – 122.5 | 87.2 – 210.5 | 55.7 | 61.5 – 88.2 | 52.6 – 123.1 | 588.5 | 36.0 – 77.9 | 240 en 5 (igual) |
| larga (300, 10) | 120.8 | 82.1 – 204.8 | 96.0 – 155.8 | 106.0 | 50.3 – 90.9 | 57.5 – 75.2 | 12 650.6 | 32.7 – 80.5 | 240 en 5 (igual) |
| normal (20, 30) | 236.7 | 240.2 – 472.6 | 254.1 – 428.3 | 163.0 | 138.2 – 277.5 | 141.8 – 174.8 | 1 441.5 | 51.4 – 91.7 | 640 en 5 (igual) |
| grande (100, 100) | 865.0 | 1 239.7 – 1 498.6 | 1 481.2 – 2 002.4 | 609.4 | 835.6 – 986.7 | 691.3 – 1 022.9 | 5 929.6 | 93.3 – 222.9 | 2 040 en 5 (igual) |
| extremo (100, 300) | 3 158.9 | 3 568.7 – 4 374.1 | 4 284.3 – 5 249.2 | 2 327.8 | 2 503.1 – 3 333.0 | 2 897.5 – 3 581.4 | 11 528.2 | 235.2 – 687.8 | 6 040 en 5 (igual) |

*Adelante contra atrás* (`specs/005-timeline/bench-linea-tiempo.txt`, `referencia`, 1 000 acciones): reproducir
hacia adelante cuesta 635.7 µs por acción e invertir hacia atrás con el historial, 157.9 µs; una acción deja 83.0
cierres en el historial, que serían unos 178 115 KB (tamaño superficial) si se guardaran las 5 000 acciones en vez de
5 cuadros.

**Lectura.**

- Los cierres guardados son los mismos con y sin línea de tiempo (el benchmark lo comprueba en cada escenario): la
  línea no cambia lo que guarda el historial.
- Lo que la línea agrega por acción es anotar un registro y, cada K = 10 acciones, capturar un punto: entre 3.3 y 69
  µs por acción repartidos (la décima parte de «capturar punto»). Eso queda por debajo de la diferencia entre
  corridas: la misma columna cambia hasta 2 veces de una corrida a otra (acción parte uno en `larga`: 82.1 a 204.8
  µs), y en algunas filas la columna con línea sale más rápida que la de la parte uno. Por eso estas cifras no
  permiten dar un porcentaje de sobrecosto; solo muestran que está dentro del ruido de la máquina.
- La columna «parte uno» de hoy está entre 0.47 y 2.0 veces la de `bench-antes.txt` (máquina ruidosa y el código de
  `Partida` que la spec 005 editó); la comparación vale dentro de una corrida, no contra los µs de otra.
- Invertir hacia atrás es unas 4 veces más barato por acción que reproducir hacia adelante, pero solo cubre 5 cuadros
  y no se puede guardar en el archivo; para leer cualquier instante, la línea de tiempo reproduce a lo más K = 10
  acciones desde un punto, y para deshacer se sigue usando el historial.
