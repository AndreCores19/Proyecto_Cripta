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

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt: /speckit-clarify Decisions on the four assumptions:
1. Cost declared on only one side of a connection: keep it, that value applies to both directions.
2. Remove the rule that rejects costo < 1 or non-integer values; the assignment does not define it. As in part one, costo is optional and defaults to 100 (like cerrada defaults to False). If the two sides of a connection declare different costs, treat it as an inconsistent door by extending the existing part-one inconsistent-door validation, not as a new invalid-data rule.
3. How hunters choose their route stays in the hunter spec. Keep it.
4. Confirmed: the assignment states that part-two crypts have new versions, so the existing version check is enough to invalidate part-one persisted data.
- Uso: hacer las aclaraciones para el spec 001

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt: /speckit-plan Python 3.11+, tests with pytest. Reuse the existing layered code: dto/ and adapters/ read the crypt skeleton; model/tiempo.py already has intervalo(costo, velocidad) and nuevo_tiempo_por_velocidad(...), which must be reused unchanged; structures/agenda.py is our own event agenda from part one.

Approach: each exit stores its cost when the skeleton is read (default 100, shared by both sides of the connection). Every move uses intervalo(exit_cost, speed) instead of the fixed COSTO_MOVER. Speed changes keep using nuevo_tiempo_por_velocidad. The existing inconsistent-door validation is extended to compare costs on both sides.

Measurements (section 5.6): re-run the part-one event agenda benchmarks with variable move costs and many active actors, compare with the part-one results, and keep or change the agenda decision based on the data.

Respect the constitution: no dict, set, heapq, bisect or collections in evaluated structures.
- Uso: hacer el plan para el spec 001, con mediciones y decisiones de diseño

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt: Fix spec.md: the crypt skeleton is never persisted; it is downloaded from the service every time a game starts. Only catalog entries are cached, and saved games and replay logs store the crypt version. Rewrite FR-011, FR-012, User Story 5 and SC-007 accordingly: exit costs are read from the skeleton on every start; a saved game or replay log whose crypt version differs (for example, from part one) is rejected by the existing version check, with no other invalidation mechanism. Remove the scenario where persisted exit costs are reused without a new request. Record this correction in the Clarifications section.
- Uso: arreglar el spec.md para que quede claro que los costos de salida se leen del esqueleto de la cripta en cada inicio y que los guardados y logs de replay con versión distinta son rechazados por la verificación de versión existente

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt: Update plan.md: remove the bucket-queue candidate. The section 5.6 measurements must only repeat the part-one candidates with the new load. Update the constitution check, measurement item 4, the decision rule, the results table and the bench file description accordingly. Also align the Storage and FR-011/FR-012 wording with the corrected spec.
- Uso: quitar la opción de bucket-queue del plan.md y actualizar las mediciones, la constitución, la regla de decisión, la tabla de resultados y la descripción del archivo de bench para que solo repita los candidatos de parte uno con la nueva carga

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt: /speckit-tasks Mark the owner of every task. Andrea (data and view): reading costo in SalidaDTO and RepositorioCripta, the inconsistent-door cost check in the repository, and the console view. Emily (engine): Salida.costo and enlazar in the model, _programar_movimiento for player and enemy moves, and the section 5.6 agenda measurements. Andrea's DTO and repository tasks come first because the rest depends on them. Each owner writes the tests for her own tasks, and every task and test cites its FR.
- Uso: hacer la asignación de tareas para el spec 001, con dueños y dependencias, y que cada tarea y prueba cite su FR correspondiente

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt: Fix spec.md per the analysis report:
- I1: rewrite US2-2 to test the rule, not the outcome: given the same state (room, trails, clock, open exits), a tracker chooses the same exit as the part-one rule. The identical-sequence check only holds when every exit costs 100 (SC-004).
- U1: add an FR: an actor enters the destination room when the move starts (traps, victory and trail marks apply immediately), and its next action is scheduled at start + interval. Reword scenarios that say "the move ends at" as "the actor's next action is at".
- G3: add an assumption that the hunter spec must include a scenario equivalent to US2-3.
- I3: in Key Entities, say the cost is an integer, >= 1 per the assignment, and not validated.
- D1: make US1-3 the case where both sides declare 250.
- A1: rewrite the offline assumption: in --offline mode the skeleton, with its costs, is read from the recording of that crypt version.
Record these corrections in the Clarifications section.
- Uso: corregir el spec.md según el informe de análisis

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt: /speckit-plan Update plan.md per the analysis report and the corrected spec:
- C1: Andrea will add a view DTO. The service builds it from the game state and the controller passes it to the view, so the view never receives the game model. For this feature it carries what the console view shows today plus, for each exit of the current room: direction, destination name, open/closed state and cost. Later specs extend it. Fix the Constitution Check row III accordingly.
- Align the plan with the new FR-016 (the actor enters the destination room when the move starts; its next action is at start + interval) and the reworded US2-2 and FR-009.
- I4: mark Constitution Check row VII as PASS; the spec and plan are already committed.
- Uso: actualizar el plan.md según el informe de análisis y el spec.md corregido

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt: /speckit-tasks Regenerate tasks.md from the updated spec and plan. Keep the same owners: Andrea (data, DTOs, service view method, controller, view, replay and version tests) and Emily (engine model, move scheduling, section 5.6 measurements). Also:
- Add Andrea's tasks for EstadoVistaDTO, JuegoService.estado_vista() and the controller and view changes.
- Mark T001 as done; the spec and plan are committed. Keep the part-one benchmark baseline as the first task before any code change.
- U2: make the speed-change test setup concrete, following the plan's Timing semantics section.
- G1: add a task (Emily) that runs a seeded game with costs and checks that every scheduled move follows the interval formula and no action lasts 0 (SC-002, SC-003).
- G2: add a task (Andrea) that records a log on a crypt with costs, replays it and compares the final state (FR-014).
- I2: the two determinism tests edit the same file, so they are not parallel.
- A2: limit the constitution check to new attributes or fields used as an index or cache in the changed files.
- Add tests for FR-016 (the actor is in the destination room at T and its next action is at T + interval).
- Uso: actualizar tasks.md con las tareas de los dueños, las pruebas y los cambios de código según el spec y plan actualizados

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt: /speckit-plan Update plan.md to resolve C1 completely, as Andrea will finish the DTO work in this feature:
- mostrar_final, mostrar_inventario and mostrar_inventario_ordenado receive DTOs built by the service instead of model objects.
- The controller never reads the game model: no servicio.partida, no room objects. Everything it needs (enemies and objects in the room, end-of-game data, score data for persistence) comes from service methods that return DTOs.
- Remove the Complexity Tracking entry for these items and mark Constitution Check row III as PASS without exceptions.
- All of this work is Andrea's (dto, service, controller, view).
- Uso: cubre completamente la C1 del plan.md, con el trabajo de Andrea en DTOs, servicio, controlador y vista, y marca la fila III de la constitución como PASS sin excepciones

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt: /speckit-tasks Regenerate tasks.md from the updated plan. Keep the same owners; all DTO, service, controller, view, aplicacion.py and boundary-test work is Andrea's. Keep T001 and T002 as done. Also:
- U3: in T014 and T016, put the player in another room and remove the enemy's pending activation turn from the agenda before calling the method under test.
- U4: in T032, build the rooms with a helper function called once for the recording and once for the replay, with the same seed.
- U5: the fake view in T019 also needs mostrar_final.
- U6: in T024 (US5-4), name the load path in aplicacion.py or test it at the repository level.
- A3: in T029, write "no speed effects are applied" instead of "disabled".
- A4: state in T029 that a fixed seed and action sequence is a replayed game in the sense of SC-002.
- I5: accept that T029 imports the room builder from bench/bench_ciclo.py and say so in the task.
- Uso: regenerar tasks.md con los dueños, las pruebas y los cambios de código según el plan actualizado, con detalles de cada tarea y prueba

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt:
- Uso: 

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt:
- Uso: 

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt:
- Uso: 

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt:
- Uso: 

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt:
- Uso: 

### 10 de Noviembre, 2026
- Herramienta: Claude
- Prompt:
- Uso: 