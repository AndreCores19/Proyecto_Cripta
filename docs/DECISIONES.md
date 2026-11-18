# Decisiones de diseño: niebla de guerra y viaje automático

Este documento **complementa** el [Documento de Decisiones de la primera parte](Documento_de_Decisiones.pdf);
no lo reemplaza. Las decisiones de las estructuras base (agenda, historial, inventario, caché, guardado,
bitácora) siguen estando allí. Aquí solo se justifican las decisiones que trae la niebla de guerra
(`specs/003-fog-of-war/`) y que tocan a otra de las estructuras ya decididas.

La numeración de la sección que sigue es la pedida en `specs/003-fog-of-war/tasks.md` (T052).
El razonamiento completo, con las alternativas descartadas, está en
[`specs/003-fog-of-war/research.md`](../specs/003-fog-of-war/research.md) (R2 y R6).

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
  y `bench-despues-ciclo.txt`) no muestra ninguna lentitud mayor al 10 %, y el benchmark propio
  (`specs/003-fog-of-war/bench-ir-a.txt`) da un p99 de la ruta con 100 salas muy por debajo de 5 ms.

**Por qué el montículo sí se comparte.** Es una estructura genérica (prioridad y valor) que no sabe nada
del grafo. Reutilizarlo evita una segunda implementación y se vacía (`vaciar()`) al comenzar cada
búsqueda, porque la búsqueda se detiene en cuanto sale la sala del jugador y deja entradas sin extraer.

## 5.4 Rendimiento de «ir a» con 300 salas

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
