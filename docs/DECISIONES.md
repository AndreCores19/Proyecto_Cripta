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
