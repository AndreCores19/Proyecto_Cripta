#Bitácora de prompts a LLM

## Emily Benavides

### 16 de Setiembre, 2026
- Herramienta: Claude
- Prompt: estoy trabajando en un proyecto y necesito entender la lógica del reloj virtual,
- me puede explicar cómo se calculan las dos funciones principales de tiempo y la lógica detrás
- del tiempo que tarda una acción según la velocidad del personaje, y cómo reajustar el tiempo
- que le falta a una acción.
- Uso: entender la lógica matemática detrás del reloj virtual y entender cómo funciona.

### 18 de Setiembre, 2026
- Herramienta: Claude
- Prompt: está bien tener Evento y AgendaEventos en el mismo .py, y Salida con Sala juntas también?
- Es que separé las clases de jugadores y enemigos en archivos distintos, pero no sé si estas clases
- más pequeñas también deberían ir separadas o si dejarlas juntas es funcional y correcto.
- Uso: saber si era una buena práctica dejarlas en el mismo archivo o separarlas todas en archivos
- individuales como hice con los personajes.

### 31 de Setiembre, 2026
- Herramienta: Claude
- Prompt: necesito diseñar el módulo de retroceso para el juego, tomando en cuenta que con cada
- decisión del jugador pueden ocurrir múltiples eventos y no sé cómo puedo estructurar el historial
- para registrar estos cambios intermedios y revertirlos en el orden correcto.
- Uso: entender cómo implementar un sistema de retroceso que pueda manejar múltiples eventos y decisiones
- del jugador, asegurando que se pueda revertir al estado anterior de manera coherente.

### 4 de Octubre, 2026
- Herramienta: Claude
- Prompt: ya tengo la estructura básica del historial pero necesito definir las reglas de qué
- datos de la partida deben modificarse a través de él para cumplir con el retroceso y qué
- debo tomar en cuenta al alterar atributos, listas, contadores, el generador aleatorio y la bitácora
- de la interfaz?
- Uso: saber cómo manejar correctamente los cambios en los datos del juego para que el sistema de retroceso
- funcione sin errores y mantenga la coherencia del estado del juego.

### 7 de Octubre, 2026
- Herramienta: Claude
- Prompt: necesito escribir la sección 4.1 del Documento de Decisiones con evidencia y
- tengo tablas de tiempos del heap contra las listas para sacar el siguiente evento y para cancelar un
- evento. Mi texto de la tabla de cancelación es correcto?
- Uso: se detectó que mezclaba cifras de dos tablas y microsegundos con milisegundos y lo corregí

### 10 de Octubre, 2026
- Herramienta: Claude
- Prompt: en el rastro se puede lograr que el costo crezca solo linealmente y cuánto costaría
- hacerlo? Además, cómo funcionan los rastreadores  y el rastro en general
- Uso: entendí cómo funcionan rastreadores y el rastro


### 11 de Octubre, 2026
- Herramienta: Claude
- Prompt: necesito benchmarks y pruebas unitarias para las estructuras que me corresponden
- (inventario, historial, rastro, bitácora y ordenamientos), siguiendo las restricciones del
- enunciado. Me ayuda a crearlos para medir cada estructura contra la alternativa descartada?
- Uso: el LLM generó un pseudocódigo base de los benchmarks y de los tests

### 11 de Octubre, 2026
- Herramienta: Claude
- Prompt: las librerías gc, tracemalloc y copy están permitidas por el enunciado para
- los benchmarks y la lógica del juego?
- Uso: confirmar qué librerías cumplen las restricciones de la sección 7 antes de usarlas

### 11 de Octubre, 2026
- Herramienta: Claude
- Prompt: para la sección 4.5, tiene sentido que yo escriba la parte de qué operaciones
- se usan de verdad, de dónde sale la cifra de operaciones que aparece en el texto y cómo puedo
- comprobarla yo misma en el programa o en el benchmark?
- Uso: ejecuté el benchmark de inventario en mi computadora, comprobé de dónde salía la cifra y
- usé mis propios resultados en el documento.

### 11 de Octubre, 2026
- Herramienta: Claude
- Prompt: en la bitácora, la lista fue más rápida en el benchmark. Por qué aún así es mejor
- buffer circular?
- Uso: entender por qué se justifica la memoria constante del buffer frente a la velocidad en
- tamaños pequeños

### 15 de Octubre, 2026
- Herramienta: Claude
- Prompt: quiero que los enemigos suelten objetos al morir, pero "fabrica_modelo.py" es de
- mi compañera y no puedo editarlo sin su permiso, qué cambio habría que hacer y cuánto le afecta a ella?
- Uso: se evaluaron dos diseños en el servicio o en la fábrica. Lo hablé con mi compañera y
- decidimos aplicar el cambio en la fábrica y en "Enemigo"

### 15 de Octubre, 2026
- Herramienta: Claude
- Prompt: en el benchmark de ordenamientos, con claves costosas el cruce entre inserción y mergesort
- baja a unos 32-48 elementos. Me explica por qué pasa? Además cómo debería decidir "ordenar" entre los
- dos algoritmos sin usar sort ni sorted?
- Uso: entender por qué el cruce baja con claves costosas y aplicar el criterio de "ordenar"

### 15 de Octubre, 2026
- Herramienta: Claude
- Prompt: revisa el proyecto completo (zip) junto con el enunciado y ayúdeme a arreglar
- el servicio "juego_service.py" para que no falle
- Uso: corrí las pruebas con los cambios, apliqué las correcciones en mis archivos

### 15 de Octubre, 2026
- Herramienta: Claude
- Prompt: necesito que me pase estas tablas del readme a un formato de texto que funcione en el readme.md
- porque no sé hacerlo y ocupo que se vea bien
- Uso: usé las tablas en un formato de texto que funciona en markdown y se ve bien en el readme

### 09 de Noviembre, 2026
- Herramienta: Claude
- Prompt: /speckit-constitution Cripta project, part two. Python 3.11+. Principles:

1. Own data structures. The data structures for the evaluated problems are hand-written: hunter pathfinding, route invalidation, known map, solvability, timeline, and the part-one structures we are re-evaluating (event agenda and undo history). In those problems, dict and set are forbidden as an index or cache, as are heapq, bisect, collections and any graph or pathfinding library. A plan that proposes any of them is wrong: it must be caught in /speckit-plan and checked again in /speckit-analyze, before implementation. Reason: the course grades our structures, not Python's.

2. Determinism. Same crypt, same seed and same actions always produce the same game. Every tie is broken by a fixed rule (e.g. lowest id), never by data order.

3. Layered architecture. Keep the project's layers (data, logic, service, controller and view, with DTOs between them). The model never prints or knows the view. --replay, --bench and --verificar never instantiate the view.

4. No hardcoded data. No data from a specific crypt (room, key or enemy ids) is written in the code; everything comes from the web service, or from data recorded or cached from it (--offline mode and persistent cache).

5. Network budget and versions. Every service request, including /llaves, counts toward presupuesto_solicitudes and is always respected. Data persisted by part one is invalidated through the existing version check, never by deleting files by hand.

6. Evidence-backed performance. No performance claim is accepted without a reproducible --bench measurement. Synthetic bench crypts are deterministic by seed.

7. Spec before code. Each capability's spec is committed to Git before its code. If the spec was wrong, fix the spec first, then the code, in separate commits.

8. What goes where. spec.md holds rules, scenarios and numbered requirements (FR-xxx), with no data structure or class names. plan.md holds structures, alternatives, complexity and measurements, with no new rules.

9. Traceability. Every task cites the FR it addresses, every acceptance scenario has a test that cites its FR, and every case in Appendix B appears as an acceptance scenario in some spec.
- Uso: se crea la constitción del proyecto


### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt: /speckit-specify Terrain: exit costs. Each exit may declare a "costo" field, an integer >= 1. If it is not declared, its cost is 100. The cost is the same in both directions.

Moving through an exit is an action whose base cost is that exit's cost, instead of the fixed value 100 from part one. The interval is still computed with the part-one formula: interval = max(1, exit_cost * 100 // speed). The rule applies to all actors (player, wanderers, trackers and hunters). The cost of attacking, waiting and every other action does not change. Wanderers and trackers keep their behavior; only the duration of their movement changes.

Data: exit costs come from the crypt skeleton and are valid while the crypt version matches. Data persisted by part one must be invalidated through the existing version check.

View: the view shows the cost of each exit of the current room.

Required scenarios:
- A high-speed actor crosses an exit of cost 1: the interval is at least 1.
- An actor's speed changes while crossing an expensive exit: the remaining time is rescaled as remaining = max(1, (end_time - now) * old_speed // new_speed), and the action now ends at now + remaining.
- Uso: hacer el spec de terreno y costos de salida, con escenarios de prueba y reglas de juego