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
| 5.5 | Línea de tiempo | `specs/005-*` |
| 5.6 | Revisión de las decisiones de la primera parte | `specs/001-exit-costs/` y `specs/002-hunter-enemy/` |

El razonamiento completo de las secciones 5.3 y 5.4, con las alternativas descartadas, está en
[`specs/003-fog-of-war/research.md`](../specs/003-fog-of-war/research.md) (R2 y R6) y en
[`specs/004-crypt-solvability/research.md`](../specs/004-crypt-solvability/research.md) (R4 y R5).

## 5.1 Ruta del cazador

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

**Decisión.** «ir a» tiene su propia clase de búsqueda, `RutaConocida` (`model/ruta_conocida.py`), que
recorre el subgrafo que el jugador conoce: las salas exploradas y las salidas que recuerda abiertas.
**No** reutiliza la búsqueda del cazador (`Busqueda.calcular`), que recorre el mapa completo. Lo que sí
comparten:

- el **montículo mínimo** escrito a mano (`structures/monticulo.py`), y
- el **contador de estampas** de `Busqueda.nueva_estampa()`, con el que se marcan las salas
  (`busq_marca` / `busq_dist`), de modo que la búsqueda guardada de los cazadores se reconoce como
  vieja y se recalcula.

**Por qué no se reutiliza `Busqueda.calcular`** (research R2):

1. Pasarle un indicador («solo lo conocido») añadiría una rama a la ruta caliente de los cazadores,
   que se ejecuta en cada turno de cada cazador, solo para servir a una función que se usa a mano y
   poco. Una clase aparte son unas pocas líneas y deja intacto el camino de los cazadores.
2. Las dos búsquedas **no recorren lo mismo**. El cazador mira el mundo real (las puertas tal como están
   y todas las salas) y busca desde el jugador hasta un límite de rango. «ir a» mira lo que el jugador
   sabe (solo salas exploradas, puertas según la memoria o según el estado en vivo si tocan su sala) y busca
   desde el destino hasta sacar del montículo la sala del jugador. Con una sola clase habría dos
   conjuntos de reglas de recorrido dentro del mismo bucle.
3. La búsqueda hacia atrás desde el destino da, de una vez, la distancia de todos los vecinos de la
   sala del jugador; el desempate (`(id de destino, dirección)`) es el mismo que usa el cazador, pero
   se aplica sobre otro grafo.

**Estampas: la regla A** (research R6). La alternativa era darle a «ir a» campos propios en `Sala`
(regla B). Se eligió que tome su estampa del mismo contador que el cazador:

- *Qué cuesta:* tras cada paso de «ir a», la búsqueda guardada del cazador queda invalidada y se hace
  una búsqueda más en el siguiente turno del cazador. Solo ocurre mientras haya cazadores activos.
  La estampa se toma lo primero, antes de cualquier retorno temprano, así que incluso un «ir a» sin ruta
  invalida esa caché (hay una prueba de cada caso en `tests/test_ir_a_viaje.py`).
- *Qué se evita:* dos campos enteros más en cada sala para ningún resultado mejor. La regla B queda como
  alternativa si la medición mostrara que esa búsqueda extra pasa del umbral de 10 % del ciclo.
- *Qué la respalda:* la medición del ciclo antes y después (`specs/003-fog-of-war/bench-antes-ciclo.txt`
  y `specs/003-fog-of-war/bench-despues-ciclo.txt`) no muestra ninguna lentitud mayor al 10 %, y el benchmark propio
  (`specs/003-fog-of-war/bench-ir-a.txt`) da un p99 de la ruta con 100 salas muy por debajo de 5 ms.

**Por qué el montículo sí se comparte.** Es una estructura genérica (prioridad y valor) que no sabe nada
del grafo. Reutilizarlo evita una segunda implementación y se vacía (`vaciar()`) al comenzar cada
búsqueda, porque la búsqueda se detiene en cuanto sale la sala del jugador y deja entradas sin extraer.

### 5.3.1 Rendimiento de «ir a» con 300 salas

**Qué se mide.** La cripta publicada más grande (cripta-06) tiene 300 salas, así que el veredicto de
`bench_ir_a` (p99 de un cálculo de ruta <= 5 ms) se mide con una cripta sintética sembrada de **300 salas**,
todas exploradas y con todas las puertas recordadas abiertas. Los tamaños de 100, 500 y 1000 salas quedan
como información. Se imprimen promedio, p99 y máximo de la ruta sola y del paso completo (ruta, movimiento y
ciclo de eventos). Se pidió además un margen: p99 del paso completo <= 3 ms.

**Antes de optimizar (300 salas, dos corridas).** p99 de la ruta 5.965 y 4.469 ms (máximo 9.757 y 5.775 ms);
p99 del paso completo 6.131 y 4.712 ms. Pasaba o no el límite de 5 ms según la corrida y el margen de 3 ms no se cumplía.

**Qué se revisó primero (sin cambios).**

- La búsqueda ya se detiene en cuanto sale del montículo la sala del jugador. Es seguro para el desempate:
  cualquier vecina `v` con `costo(v) + dist(v) = d` tiene `dist(v) < d`, así que ya es definitiva.
- No hay trabajo proporcional a todo el mapa conocido en cada paso: no se limpian marcas (las estampas lo
  evitan), no se reconstruye ningún subgrafo y no se guarda nada entre pasos (FR-020). El trabajo es el de la
  región conocida más cercana al destino que el jugador; con pares lejanos en una cripta de 300 salas esa región
  es casi todo el mapa, y por eso el costo se nota.

**Dónde se iba el tiempo** (perfil con `cProfile`): cerca del 60 % en el montículo (`extraer`, `insertar` y
unos 9 millones de llamadas a `_antes`) y el resto en el bucle de `siguiente_paso`, la llamada a
`partida.puerta_recordada` y la propiedad `Salida.costo`.

**Qué se cambió (detalle de implementación, sin cambiar la especificación).**

1. `structures/monticulo.py`: `insertar` y `extraer` comparan en línea, con la misma regla que `_antes`
   (prioridad y luego secuencia), en vez de llamar a un método por cada comparación. El comportamiento es
   idéntico (lo cubren `tests/test_monticulo.py` y las pruebas de equivalencia del cazador, que lo comparten).
2. `model/ruta_conocida.py`: la lectura de la puerta recordada se hace en línea (en vivo si toca la sala del jugador, si no
   `memoria`), se lee `costo_declarado` con el mismo valor por defecto que `Salida.costo`, y no se inserta en el montículo
   una sala cuya distancia ya no puede dar una ruta mejor que la hallada hasta el jugador (`nd >= dist(jugador)`; una
   vecina útil tiene `dist < d`, así que el desempate no cambia).

**Después (300 salas, tres corridas, `specs/003-fog-of-war/bench-ir-a.txt`).**

| | Antes | Después |
|---|---|---|
| p99 de la ruta | 5.965 / 4.469 ms | 2.740 / 2.991 / 2.645 ms |
| máximo de la ruta | 9.757 / 5.775 ms | 9.626 / 5.896 / 4.106 ms |
| p99 del paso completo | 6.131 / 4.712 ms | 2.472 / 2.982 / 2.622 ms |
| máximo del paso completo | 8.890 / 7.888 ms | 3.784 / 4.517 / 3.891 ms |

En siete repeticiones aparte de la misma medición, la mediana del p99 fue 2.7 ms (ruta) y 2.8 ms (paso completo),
con un máximo de 3.4 y 3.3 ms entre repeticiones. Cumple el límite de 5 ms con margen y el paso completo queda cerca
de 3 ms: el margen de 3 ms es justo, no holgado. Los máximos tienen picos ocasionales (hasta decenas de ms en
algunas corridas) que vienen de la máquina y no del algoritmo; no entran en el veredicto, que es el p99.
`bench_ciclo` no cambia: todos sus p99 siguen por debajo de 20 ms.

## 5.4 Verificación de resolubilidad: una pasada y no una por llave

Esto complementa el [Documento de Decisiones de la primera parte](Documento_de_Decisiones.pdf). El razonamiento
completo, con las alternativas, está en [`specs/004-crypt-solvability/research.md`](../specs/004-crypt-solvability/research.md)
(R4 y R5) y los números en `specs/004-crypt-solvability/bench-solvabilidad.txt`.

**Decisión.** Decidir si una cripta se puede ganar con **una sola pasada** que hace crecer a la vez la región alcanzable
y las llaves tomadas: llegar a una sala vuelve obtenibles las llaves que hay en ella (van a un montículo ordenado por
id, el de `structures/monticulo.py`), se toma la de menor id, se liberan las puertas que esperaban esa llave y la región
vuelve a crecer. Cada sala entra una vez, cada salida se examina una vez desde su origen y cada llave entra y sale del
montículo una vez: `O((V + E) log V + K log K)`, donde el `log V` es buscar la posición de una sala en el vector ordenado.
El orden en que salen las llaves del montículo es el orden de llaves, y no depende del orden en que el servicio lista las
llaves ni las salidas.

**Por qué no una pasada completa por llave.** Es lo primero que se escribe: tomar una llave, recorrer otra vez toda la
cripta con las llaves que se tienen, y repetir. Cuesta `O(K (V + E))`. Cuando obtener una llave abre una región entera, como
en las criptas de llaves encadenadas, ese costo se vuelve cuadrático. Se dejó solo como alternativa medida en el benchmark y
como oráculo independiente de las pruebas (que comprueba que ambas dan el mismo orden de llaves).

**Por qué el informe sale de lo que deja la pasada.** Las llaves que no se tomaron, las salidas que quedaron esperando (que
son justo la frontera bloqueada) y dónde está cada llave ya están en el estado final de la pasada. Los ciclos salen de un
barrido lineal sobre las únicas salas que la pasada no alcanzó: cada llave de la frontera, en orden de id, inunda esas salas
ignorando las cerraduras y las etiqueta si no tenían etiqueta, así que cada sala queda con la menor llave que llega a ella
(la guardiana); seguir guardianas da cada ciclo una vez. No hay una búsqueda de ciclos por llave, que sería otra pasada por llave.

**Medición** (tres corridas, semilla 1; `python -m bench.bench_solvabilidad` dura unos 20 s):

| | Resultado |
|---|---|
| Cripta con la forma de la mayor publicada (300 salas, 4 llaves) | máximo de la verificación 5.6, 22.8 y 3.9 ms por corrida (límite 200 ms), con y sin llave de salida alcanzable |
| Llaves encadenadas, ×10 salas | la verificación tarda 13 a 22 veces más; la alternativa de una pasada por llave, 57 a 143 veces más |
| 10 000 salas y 200 llaves | verificación 69 a 79 ms; una pasada por llave, 7.4 a 8.5 s |
| 100 000 salas y 2 000 llaves | verificación 1.1 a 1.5 s (la alternativa ya no se mide: serían unos 2×10⁸ recorridos de sala) |

El crecimiento de la verificación es un poco más que lineal (13 a 22 veces por cada ×10), por el `log V` de la búsqueda
binaria y por la memoria, y el trabajo visto no depende de las llaves: las salas y las salidas visitadas son siempre las de la
cripta (por ejemplo 98 049 salas y 196 096 salidas con 2 000 llaves).

## 5.5 Línea de tiempo

*Pendiente: se completa cuando se termine la spec 005.*

## 5.6 Revisión de las decisiones de la primera parte

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

*Spec 001: costos de salida variables* (`specs/001-exit-costs/bench-parte1.txt` y `specs/001-exit-costs/bench-parte2.txt`; la medición de la primera parte usaba costo fijo 100):

| Medición | Primera parte (`specs/001-exit-costs/bench-parte1.txt`: salidas de costo 100) | Spec 001 (`specs/001-exit-costs/bench-parte2.txt`: costos variables) |
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
acción (cálculo mío con las cifras de la tabla: 142.1 / 123.0 con 300 enemigos y 30 cazadores; 1260.7 / 1237.4 con 3000 y 30; con 100 y 300 cazadores, 14.6 % y 14.1 %; el `plan.md` de la 002 redondea a «2 % y 15 %»); la forma de la carga no cambia, porque
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

*Pendiente: se revisa en la spec 005.*
