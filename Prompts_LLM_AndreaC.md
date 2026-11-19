# Bitácora de prompts a LLM

## Andrea Cordero

### 20 de Setiembre, 2026
- **Herramienta:** Claude
- **Prompt:** No comprendo bien cómo funcionan las solicitudes al servicio ni el presupuesto de solicitudes. Puedes explicármelo paso a paso?
- **Uso:** comprender las solicitudes HTTP, el formato JSON y el presupuesto de solicitudes para diseñar el cliente de red.

### 20 de Setiembre, 2026
- **Herramienta:** Claude
- **Prompt:** Antes de escribir los métodos públicos del cliente, puedes explicarme con un lenguaje muy sencillo qué hace cada uno?
- **Uso:** entender el propósito de cada uno de los siete métodos públicos del cliente.

### 23 de Setiembre, 2026
- **Herramienta:** Claude
- **Prompt:** Quiero continuar con la conversión de las respuestas JSON a objetos. Puedes explicarme como aplicar los DTOs en este proyecto?
- **Uso:** entender cómo convertir las respuestas del servicio a objetos.

### 26 de Setiembre, 2026
- **Herramienta:** Claude
- **Prompt:** Podemos usar diccionarios en el proyecto? Recuerdo que el enunciado mencionaba algo al respecto.
- **Uso:** verificar qué permite y qué prohíbe el enunciado sobre el uso de `dict`.

### 3 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** Para las fichas del catálogo, sería muy inconveniente usar una clase por cada tipo de ficha?
- **Uso:** decidir cómo representar las fichas del catálogo (una clase por tipo o una sola clase).

### 3 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** Para el algoritmo de búsqueda, sería mejor la versión iterativa o la recursiva?
- **Uso:** decidir entre las dos versiones de la búsqueda binaria y justificarlo en el documento.

### 6 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** Para la caché del catálogo, qué estructura conviene usar si no puedo usar un diccionario? Necesito buscar rápido por id y saber cuál ficha usé hace más tiempo.
- **Uso:** decidir que la caché (CacheFichas) combine un vector ordenado por id con búsqueda binaria y una lista doblemente enlazada para el orden de uso (LRU). La búsqueda lineal y FIFO quedan como alternativas para medir en el benchmark.

### 10 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** Para precargar el contenido de las salas, cómo recorro el esqueleto de la cripta para pedir las salas por lotes y gastar pocas solicitudes?
- **Uso:** diseñar la precarga por lotes con recorrido por niveles usando una Cola propia, para pedir el contenido de varias salas por solicitud y cuidar el presupuesto.

### 10 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** Para construir los objetos del modelo desde las fichas del catálogo, ¿debo comparar la clase de la ficha (fichaObjetoDTO.clase) con los tipos de objeto?
- **Uso:** decidir que la fábrica del modelo (data/fabrica_modelo.py) elija qué objeto crear con un if/elif sobre la clase de la ficha, sin diccionario de funciones, para respetar la restricción de no usar dict como tabla de búsqueda.

### 12 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** ¿Por qué usar n, s, e, o para moverse? ¿No es mejor el tradicional w, a, s, d? Y mostrar_estado, ¿dónde debería vivir?
- **Uso:** decidir que el movimiento use WASD traducido a direcciones N/S/E/O en el controlador, y que `mostrar_estado` viva en la vista (VistaConsola), de modo que el controlador solo lea comandos y el modelo no imprima nada.

### 12 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** En la sala 2 de cripta-01 pierdo siempre aunque ataque. ¿Es un error del motor o está bien?
- **Uso:** verificar el motor contra el enunciado y con una simulación: la sala está casi perdida por aritmética y no por un bug. Se decidió no cambiar el motor y consultar al profesor si cripta-01 debe poder ganarse.

### 12 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** Quedé encerrada: la sala 19 solo va a la 20 y la puerta hacia la sala 5 aparece cerrada. ¿Es un error?
- **Uso:** comprender el cierre automático de puertas (la puerta se cierra sola tras cierto tiempo, en ambas caras) y decidir mostrar en la vista qué llave requiere cada puerta cerrada como mejora futura.

### 15 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** ¿Cómo diseño la bitácora de comandos para que --replay reproduzca la partida de forma fiel? ¿Qué debe llevar el encabezado y qué pasa si cambia la versión de la cripta?
- **Uso:** definir un log de texto con encabezado (cripta, versiones, semilla) y un comando por línea con flush; validar versiones antes de reproducir y medir el costo en bench_replay.

### 15 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** Descubrimos que veneno va en las trampas y regeneración en los enemigos, y Emily ya lo añadió y lo probó. Eso afecta lo que ya hicimos (caché, guardado, benchmarks)? Además, en las fichas reales de trp_dardos y ent_rata_gigante no aparece ninguno de los dos campos, ¿es un problema?
- **Uso:** comprobar que los campos nuevos no rompen la caché ni el guardado, y entender que los nombres `veneno` y `regeneracion` son una suposición nuestra porque el enunciado no nombra los campos de la ficha.

### 15 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** Revisa los benchmarks de Emily en bench/ y dime cómo agrego la opción --bench a main.py sin romper el resto de los flags.
- **Uso:** entender qué mide cada benchmark contra lo que pide la sección 5.3 del enunciado (agenda, caché, fichas expulsadas, inventario, historial, ordenamientos, guardado y carga) y agregar --bench con argparse.


### 16 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** Necesito un formato de guardado binario para la partida: ¿qué debe llevar el encabezado, cómo valido que la cripta y las versiones coinciden, y por qué es mejor que JSON?
- **Uso:** diseñar GuardadoBinario (magic, versión de formato, índice de salas al final) y compararlo con JSON midiendo tamaño y tiempos de guardar, cargar todo y leer una sola sala (bench_guardado).

### 16 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** Quiero medir cuánto cuesta una ficha según venga de memoria, de disco o de la red, y cuánto cuesta marcar las fichas en uso en cada acción del jugador. Cómo armo ese benchmark sin usar la red real?
- **Uso:** escribir bench_fichas con una fuente falsa y una cita de 400 ms por solicitud; comprobar que marcar las fichas en uso es una fracción pequeña del límite de 20 ms por ciclo.

### 17 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** Al jugar cripta-04 el programa gasta muchas solicitudes. ¿Estamos pidiendo el contenido de las salas y las fichas del catálogo de la forma más eficiente? Mide cuántas solicitudes gasta cada estrategia.
- **Uso:** descubrir que se pedía contenido en cada sala y fichas una por una; cambiar a pedir un lote de salas solo cuando falta la sala de destino y resolver las fichas de todo el lote juntas. Medimos con bench_precarga y bench_catalogo (por ejemplo, de 83,5 a 9,9 solicitudes en una cripta de 100 salas).

### 18 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** El benchmark de precarga me da el doble de solicitudes que a ti. Aquí está mi función precargar y la salida de una prueba mínima. Por qué da diferente?
- **Uso:** encontrar con una prueba mínima que `precargar` hacía la solicitud dos veces porque quedó el bloque viejo junto al nuevo; borrar el duplicado y verificar con prueba_precarga y --bench que los conteos coinciden.

### 18 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** Cada partida de cripta-04 es distinta, así que no puedo comparar caché fría y caliente. ¿Cómo mido la misma partida?
- **Uso:** usar --replay con el mismo log para comparar la caché fría y la caliente con --cache-size 3, y agregar mostrar_reporte a VistaReplay y llamar a _reportar al final de reproducir.

### 18 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** Revisa mi vista y mi controlador contra la sección 10.2 del enunciado y dime qué falta.
- **Uso:** detectar que faltaban el menú para elegir cripta, la vista ordenada del inventario, las estadísticas, el estado de efectos, los 20 mensajes y la tabla de puntajes, y hacerlos uno por uno probando cada paso.

### 18 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** ¿Cómo implemento --offline para que el modelo no sepa si los datos vienen de HTTP o de archivos?
- **Uso:** crear ClienteOffline con la misma interfaz que ClienteHttp, un script que descarga el paquete de respuestas a offline/ y un solo if en main.py para elegir el cliente. Se comprobó que una partida completa cuenta 0 solicitudes.

### 18 de Octubre, 2026
- **Herramienta:** Claude
- **Prompt:** Revisa mi README, pyproject.toml y .gitignore y dime qué falta para que funcione en un entorno limpio.
- **Uso:** detectar que requests faltaba en las dependencias, completar las partes pendientes del README (opciones, controles, benchmarks y archivos generados) y agregar .idea/ y .pytest_cache/ al .gitignore.

### 11 de Noviembre, 2026
- **Herramienta:** Claude
- **Prompt:** /speckit-specify Fog of war and automatic travel ("ir a") for the Cripta game.

Why: until now the player sees the whole map. We want the player to know only what they have explored, for the game to remember what they saw, and for them to be able to travel automatically within that knowledge without cheating.

Room states from the player's point of view:
- Explored: the player has entered it at least once (the starting room is explored from time 0). The player knows its name, its exits, the cost of each exit, and the state of its doors as of the last observation.
- Sighted: not explored, but it is the destination of an exit of an explored room. The player only knows that a room exists behind that exit.
- Unknown: none of the above. The player knows nothing.

Rules:
- Door memory: the player observes a door when they are in either of the two rooms it connects. The player's map remembers each door's state as it was at the last observation, even if it has changed since (for example, a door with automatic closing may appear open on the map while actually being closed).
- Lit torch (antorcha): while it is lit, entering a room also explores all of its neighbors, through any exit, open or closed. Exploring a neighbor this way reveals its name and exits, not its contents, and does not activate its enemies or traps.
- Everything the view shows and everything the "ir a" command uses must be derived only from the player's knowledge. Downloading the full skeleton is infrastructure and does not count as knowledge.
- The player's knowledge is game state: it is saved in the save file, it is reverted by the rollback scroll (pergamino de retroceso), and it is part of the timeline.
- The interface offers a command to view the known map: explored rooms, their exits, and sighted rooms.

Command "ir a <room>":
- Takes the player to an explored room through ordinary moves. If the room is not explored, the command is rejected and consumes no time.
- The route uses only explored rooms and only exits the map remembers as open. It minimizes the sum of costs; ties are broken the same way as the hunter (first step toward the neighbor with the lowest id), as defined in spec 002.
- Each step is a complete player action: it consumes time according to the exit cost (spec 001), and clock events happen normally between steps.
- The route is recomputed before every step with the current knowledge.
- It never opens doors, even if the player has the key.
- The trip stops when: the player reaches the destination; enters a room containing enemies (active or asleep); takes damage; or no known route exists anymore. The view shows the reason.
- In the game log (partida.log) each step is recorded as an individual move, and the "ir a" order is also recorded as a comment.
- The rollback scroll reverts only the last step, and the trip does not continue.

Performance requirement: computing one step of "ir a" with the full known map of the reference crypt takes at most 5 ms.

Mandatory acceptance scenarios:
1. "ir a" toward an unexplored room: it is rejected and consumes no time.
2. The map remembers a door as open that is actually closed: when the player observes it, the map is updated and the route is recomputed; if no route remains, the trip stops without consuming extra time.
3. "ir a" enters a room with sleeping enemies: the enemies activate according to the first-part rules and the trip stops.
4. With the torch lit, entering a room explores its neighbors without activating their enemies or traps.
5. A scroll reverts an entry made with the torch lit: the rooms explored by the torch return to their previous state.
6. A scroll during a trip: it reverts only the last step and the trip does not continue.
Every functional requirement must have a stable FR-xxx identifier. Do not include names of data structures, classes or modules. If something is ambiguous, flag it for /speckit-clarify instead of deciding it yourself. Follow the same structure, style, language and conventions as the existing specs (specs/001-* and specs/002-hunter-enemy/spec.md): read them first and match their section layout, how requirements (FR-xxx) and acceptance scenarios are written, and their level of detail.

- **Uso:** especificar el comportamiento de la vista y del comando "ir a" para que el jugador solo vea lo que ha explorado, pueda viajar automáticamente dentro de ese conocimiento y no haga trampa.

### 11 de Noviembre, 2026
- **Herramienta:** Claude
- **Prompt:** /speckit-analyze Re-run the analysis for specs/003-fog-of-war with this specific focus. Do not modify any file; only report. Also read the real code on the current branch (structures/monticulo.py, model/ruta_cazador.py, Busqueda.nueva_estampa, the Sala fields busq_marca/busq_dist, dto/estado_vista_dto.py, the torch, scroll and partida.log handling) and tell me whether the plan's assumptions match how the code actually works today.

Verify that each of these decisions is correctly reflected in plan.md and tasks.md (and that nothing in spec.md contradicts them):

1. Shared min-heap: "ir a" reuses the existing MonticuloMinimo (insertar, extraer, proximo, vaciar, len). It is emptied before every search. There is no "decrease priority": a better path is reinserted and the stale copy is ignored when extracted. No heapq, bisect, collections, dict or set anywhere in the plan or tasks.
2. Separate search: "ir a" has its own search class over the player's KNOWN subgraph only (explored rooms, exits the map remembers as open). It must not reuse the hunter's full-map search. The plan records the justification for DECISIONES.md section 5.3.
3. Shared stamp counter: every "ir a" search takes a NEW stamp from Busqueda.nueva_estampa() at the very start, always, even if it finds no route or ends early. There is a task and a test for the case "ir a finds no route, the player does not move, and the hunter must recompute on its next turn" (mirror the existing hunter test that inserts a foreign search between two turns).
4. Explicit tie-break: the route is computed backwards from the destination; the first step is chosen among the player's neighbors that satisfy cost + dist = d, taking the lowest room id. It must not depend on the heap's insertion order. There is a test with several equal-cost routes.
5. Read-only DTO for the known map: the view receives a snapshot made of plain values (no references to model objects), built outside the view and the controller. Everything the view shows about the map derives only from the player's knowledge. The tasks cover all three views (console, replay, silent).
6. Clarify answers are in the spec and covered by tasks and tests: (a) doors of torch-explored neighbors that lead to third rooms are "never observed" and "ir a" cannot use them; (b) doors are observed continuously while the player is in either of the two rooms they connect; (c) a rejected "ir a" is still written to partida.log as a comment, and moves are written only for steps actually taken.
7. Traceability and constitution: every FR-xxx has a task, every acceptance scenario has a test citing its FR, the six mandatory scenarios from the brief are covered, the 5 ms performance requirement has a --bench task, the plan adds no rule that is not in spec.md, and spec.md names no data structures, classes or modules.

Report as a table: item, status (OK / missing / contradicts), file and requirement or task id, and the proposed fix. End with a one-line verdict.

- **Uso:** analizar la implementación actual de "ir a" y la vista del mapa conocido, y verificar que el plan y las tareas reflejan correctamente las decisiones de diseño y los requisitos de la especificación.

### 12 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:** /speckit-implement Implement ONLY Phase 1 (the baseline) of specs/003-fog-of-war/tasks.md, then stop. Do not start Phase 2 or any later phase.

Rules for this run:
- Work through the tasks of this phase in order, respecting the dependencies in tasks.md, and mark each task as done in tasks.md as you complete it.
- Follow the constitution: no dict, set, heapq, bisect, collections or graph libraries in the evaluated problems; no data of a specific crypt hard-coded; the view never modifies the model; --replay, --bench and --verificar never instantiate the view.
- Make one git commit per task (or per small group of closely related tasks). Each commit message must cite the task id (T0xx) and the FR-xxx requirements it serves.
- Run the full test suite when the phase is finished and show me the result (passed, failed, new tests added).
- If a task cannot be done as written, or the code contradicts the spec or the plan, STOP and tell me what you found. Do not edit spec.md, plan.md or tasks.md to make the code fit; I will decide first and the spec must be corrected and committed before the code.
- When you finish, report: tasks completed, files changed, tests run, anything skipped or unclear, and the id of the first task of the next phase.

  - **Uso:** implementar la primera fase de la especificación de "ir a" y la vista del mapa conocido, siguiendo las reglas de constitución y reportando cualquier contradicción o tarea que no pueda completarse.
  - Nota: Se utilizó el mismo prompt para la segunda fase, y así sucesivamente hasta completar todas las fases de la especificación.

### 16 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:** /speckit-implement Implement ALL the remaining tasks of specs/003-fog-of-war/tasks.md, in order. Skip the tasks already marked as done and continue from the first unchecked one, respecting the dependencies and phase order in tasks.md.

Rules for this run:
- Mark each task as done in tasks.md as you complete it.
- Follow the constitution: no dict, set, heapq, bisect, collections or graph libraries in the evaluated problems; no data of a specific crypt hard-coded; the view never modifies the model; --replay, --bench and --verificar never instantiate the view.
- Make one git commit per task (or per small group of closely related tasks). Each commit message must cite the task id (T0xx) and the FR-xxx requirements it serves.
- Run the full test suite at the end of every phase. If tests that passed before now fail, fix the cause before moving on.
- For the decisions document task (T052): the first part already has docs/Documento_de_Decisiones.pdf, so the new DECISIONES.md must complement it and link to it, not ignore it.
- If a task cannot be done as written, or the code contradicts the spec or the plan, STOP and tell me what you found. Do not edit spec.md, plan.md or tasks.md to make the code fit.
- When you finish, report: tasks completed, tasks skipped or blocked (with the reason), files changed, final test results, the --bench scenarios added and their measured times against the 5 ms limit, and anything the manual check (T053) still needs from me.


  - **Uso:** implementar todas las fases restantes de la especificación de "ir a" y la vista del mapa conocido, siguiendo las reglas de constitución y reportando cualquier contradicción o tarea que no pueda completarse.

### 16 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:** Here is the text of Appendix B (fog of war and "ir a") for T051:

- "ir a" toward an unexplored room: it is rejected and consumes no time.
- The map remembers as open a door that is actually closed: when the player observes it, the map is updated and the route is recomputed; if no route remains, the trip stops without consuming any extra time.
- "ir a" enters a room with sleeping enemies: the enemies activate according to first-part §2.4 and the trip stops.
- With the torch lit, entering a room explores its neighbors without activating their enemies or their traps.
- A scroll reverts an entry made with the torch lit: the rooms explored by the torch return to their previous state.
- A scroll during a trip: it reverts only the last step and the trip does not continue.


  - **Uso:** verificar que los escenarios de aceptación obligatorios de la sección 5.3 del enunciado estén cubiertos por pruebas automáticas y que cada prueba cite su FR correspondiente.

### 16 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:** The largest published crypt (cripta-06) has 300 rooms, so the 5 ms verdict in bench_ir_a must be measured with a synthetic crypt of 300 rooms, not 100 (keep the 100, 500 and 1000 scenarios as informational). Add the 300-room scenario as the verdict, run it, and report p99 and max for both the route alone and the full step.
If the full step p99 is above 3 ms (we want margin), optimize before anything else. First check whether the search already stops as soon as the player's room is extracted from the heap. That early exit is safe for the tie-break: any neighbor v with cost(v) + dist(v) = d has dist(v) < d, so it is already final when the player's room comes out. Also check that no work proportional to the whole known map is done on every step (clearing marks, rebuilding the subgraph). Keep every existing test green, and do not change the spec: this is an implementation detail covered by the plan. Update specs/003-fog-of-war/bench-ir-a.txt and the performance section of docs/DECISIONES.md with the before and after numbers.

- **Uso:** medir el tiempo de "ir a" con una cripta sintética de 300 salas y optimizar la implementación si el p99 del paso completo supera los 3 ms, sin cambiar la especificación ni romper las pruebas existentes.

### 16 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:** Synchronize the documents of specs/003-fog-of-war with the program as delivered. Do NOT change any code. Make separate commits: first all changes to spec.md, then plan.md, tasks.md and research.md, each message explaining why.

spec.md:
1. Rollback order: the code checks the rewind counter at the start of every paso(), before any other check. Amend FR-022 so that the order "end of the game, arrival, enemies in the room, damage, no route, scroll" applies to the reasons met by a step, while a rewind that happened since the previous step is detected before the next step is taken and takes precedence. Do not delete the earlier clarification entries; add a new "Session 2026-11-17" entry that records this correction.
2. Extra guard: when the route says a step exists but the move cannot be performed (mover returns False), the trip stops with the reason "no known route" instead of looping. Add it as an edge case and as a new requirement FR-028, with a matching acceptance scenario.
3. Known map in the log: the assumption "Reading the known map (FR-015) ... is not recorded in the game log as a move" must match the program. The "mapa" command is written to the game log as an ordinary command line (like "inv"), changes no state, and replay executes it with no effect. Rewrite the assumption to say that.
4. Change "Status: Draft" to the real status of the feature.

plan.md, tasks.md, research.md:
5. Make plan.md (Trips section) and T036 say the same as the amended FR-022 (rewind check first, then the ordered reasons after a step).
6. Describe the guard of point 2 in plan.md, and add a task and a test that cover it with FR-028 (new task at the end of the polish phase, update the dependency graph and the scenario-coverage list).
7. Reference crypt size: spec.md delegates it to spec 002 FR-017, so leave spec.md as it is on this point. The largest published crypt (cripta-06) has 300 rooms and bench_ir_a now measures the 5 ms verdict with 300 rooms (100, 500 and 1000 are informational). Update plan.md (Technical Context "Scale/Scope" and Measurements section 1) and tasks.md (T042 and T043). Then read spec 002 FR-017 and the reference crypt of bench_ciclo/bench_cazador: if spec 002 states a size that is not 300 rooms, do NOT edit spec 002; report it to me instead.
8. Stale text: make the spec commit hashes consistent between plan.md and tasks.md (T001), set the two PENDING rows of the Process Gate to PASS, replace "PASS (pending data)" by PASS with a reference to specs/003-fog-of-war/bench-ir-a.txt, and remove "not created here" from the tasks.md line of the plan tree.

When done, run /speckit.analyze and report any remaining inconsistency.

  - **Uso:** sincronizar los documentos de la especificación de "ir a" con el programa entregado, sin cambiar código, y reportar cualquier inconsistencia restante.

### 16 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:** Yes. Apply X2, X3, X4 and X7. Skip X6 and do not touch spec 002 or the spec 002 benchmarks (X1 is for Emily).

For X5, add a new task at the end of the polish phase (update the dependency graph and the scenario-coverage list) citing FR-012 and SC-005, and implement it: a test that plays a game with exploration, a lit torch, a door observation and one "ir a" trip, saves it through GuardadoBinario, loads it through the same path Aplicacion uses (_sesion), and checks that the knowledge snapshot (room levels, door memory, discovered rooms) equals the original, and that the saved commands hold the steps of the trip as moves and not the order. Use the fake factory; no network.

Make two commits: the documentation fixes first, then the new task with its test, citing the task id and FR-012. Do not change production code unless the test reveals a real bug: in that case stop and tell me what you found.

  - **Uso:** aplicar los cambios de documentación X2, X3, X4 y X7, agregar un nuevo test de guardado y carga de la partida con conocimiento del mapa, y reportar cualquier bug encontrado.

### 17 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:** /speckit.specify Solvability verification of a crypt for the Cripta game.

Why: the service publishes crypts that cannot be won. Before a game starts, the program must decide whether the crypt can be won and, if it cannot, explain exactly why, so the player is never sent into an impossible game without knowing it.

What is checked:
- The verification uses the full crypt skeleton (rooms, exits, closed exits and the key each one requires) and the location of every key. The fog of war does not apply: this is infrastructure, not the player's knowledge.
- Key locations come from a new service query, which returns for each key the room where it is and, when an enemy carries it, the enemy; in that case the room is the one where that enemy starts and the key is in what that enemy drops. This query counts within the request budget of the crypt like every other request. Its answer is valid while the crypt version is the same, and a new version invalidates it.

Assumptions of the verification:
- The player can cross any open exit, and any closed exit whose key the player already has.
- Keys are never consumed.
- Every enemy can be defeated, so a key an enemy drops is obtainable in the room where that enemy starts (also when the enemy wanders).
- Traps and automatic door closings never block: a door that closes again can be opened again with the same key.

Solvable: starting from the initial room, under those assumptions, the player can obtain the exit key and reach the exit room through a door that requires it.

Result:
- If solvable: an order in which to obtain the keys such that every key appears after all the keys needed to reach it. If several orders are valid, any is accepted, but the result must be deterministic: the same crypt always gives the same order, whatever the order in which the service lists rooms or keys.
- If not solvable: (a) the keys that cannot be obtained; (b) the doors of the blocked frontier, that is, the closed doors adjacent to the region the player can reach, each with the key it requires; (c) where each of those keys is located; (d) when a key is located behind doors that only it opens, directly or through a chain of keys, the concrete cycle, reported deterministically.
- The information for the report of a non-solvable crypt must come from the same pass over the crypt that decides solvability, not from extra passes per key.

Commands:
- Before a game starts, the program runs the verification and the interface lets the player see the report. If the crypt is not solvable the game does not start, and the report is shown, unless the option --forzar is used.
- The option --verificar <crypt> runs only the verification and prints the report, without creating the view.

Performance requirements:
- Verification of the largest published crypt takes at most 200 ms, measured locally without network or rendering.
- Obtaining a key can make a whole region reachable, so the verification must not repeat a full pass over the crypt each time a key is obtained: its total cost grows approximately linearly with the number of rooms, exits and keys.
- Synthetic crypts used for measuring are deterministic by seed, and --bench measures the naive alternative (a full pass per key) with synthetic crypts of many chained keys.

Mandatory acceptance scenarios:
1. The exit key is behind the only door that it opens itself: the crypt is not solvable and the report points out the cycle.
2. A key is in what a wandering enemy drops: the verification places it in the enemy's initial room.
3. Several valid orders of obtaining keys exist: two runs give the same order.
4. A non-solvable crypt without --forzar: the game does not start and the report is shown.
Add scenarios for: a solvable crypt with chained keys (the order respects every dependency); a non-solvable crypt whose report lists unobtainable keys, frontier doors and key locations; --forzar starts the game of a non-solvable crypt; --verificar creates no view; and the key query counting within the request budget.

Every functional requirement must have a stable FR-xxx identifier. Do not include names of data structures, classes or modules. Do not invent rules that are not in this brief. Flag for /speckit.clarify, instead of deciding them: (1) where key locations come from in --offline mode, since the recorded offline package has no key locations; (2) whether the order of keys is shown at the start of a game for a solvable crypt, or only the verdict; (3) whether the key locations are stored between runs while the crypt version is unchanged; (4) the exact tie-break that makes the order of keys deterministic. Follow the same structure, style, language and conventions as the existing specs (specs/001-*, specs/002-hunter-enemy/spec.md and specs/003-fog-of-war/spec.md): read them first and match their section layout, how requirements and acceptance scenarios are written, and their level of detail.

- **Uso:** especificar la verificación de resolubilidad de una cripta para que el jugador nunca se encuentre en un juego imposible sin saberlo, y definir los comandos y escenarios de aceptación obligatorios.

### 17 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:** /speckit-clarify Resolve only the open points listed under "Points for the spec" in specs/004-crypt-solvability/plan.md. Do not ask about anything else.

- **Uso:** aclarar los puntos abiertos de la especificación de verificación de resolubilidad de una cripta, sin preguntar sobre otros temas.

### 17 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:** /speckit-clarify Resolve only the four points deferred with a provisional treatment in specs/004-crypt-solvability/plan.md ("Points for the spec": replay and load not verifying again, cripta-01 and the offline package, a key listed twice, and the exit status of --verificar). Do not ask about anything else.

- **Uso:** aclarar los cuatro puntos pendientes de la especificación de verificación de resolubilidad de una cripta, sin preguntar sobre otros temas.

### 17 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:** /speckit-analyze Read-only. Check specs/004-crypt-solvability (spec, plan, tasks) with this focus, and read the real code on the branch where it matters:
1. One pass: the reachable region grows, keys are taken by lowest id from the shared min-heap (structures/monticulo.py), stored closed doors are reactivated when their key is obtained, no pass per key, and a single linear sweep over the rooms the pass did not reach finds the cycles. All cycles are reported, each from its lowest key id, ordered by that id.
2. Determinism: the order does not depend on the order in which the service lists rooms and keys (there is a test with shuffled lists); a key listed twice counts at its lowest room id.
3. A closed door whose key is missing or absent from the key list goes to the frontier with unknown location; a missing exit key makes the crypt not solvable.
4. Network: the key query counts within the request budget; the skeleton is downloaded ONCE and shared by the verification and the game (no second download); the key locations are stored by crypt version and invalidated by a new version; a failed query shows the usual communication error with no verdict.
5. Commands: --verificar creates no view and its exit status is 0 if solvable and 1 if not; --forzar starts a non-solvable crypt; --replay and loading a saved game do not verify again.
6. The view receives only plain-value DTOs; the report text is built outside the view; --replay, --bench and --verificar instantiate no view class.
7. Offline: cripta-01 is dropped, the package is recorded from the published crypts with their key locations, and grabar_offline.py never deletes anything unless the listing succeeded and every recording finished.
8. Performance: the 200 ms limit is measured on the largest published crypt (300 rooms) as the worst of the repeated runs; the benchmark compares the naive pass-per-key alternative on chained keys and shows linear growth.
9. Traceability and constitution: every FR has a task, every scenario has a test citing its FR, the four mandatory Appendix B cases are covered, and no dict, set, heapq, bisect, collections or graph library is planned.
Report as a table: item, status (OK / missing / contradicts), file and requirement or task id, proposed fix, and a one-line verdict.

- **Uso:** analizar la implementación actual de la verificación de resolubilidad de una cripta y verificar que la especificación, el plan y las tareas reflejan correctamente las decisiones de diseño y los requisitos, reportando cualquier inconsistencia.


### 17 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:** /speckit-implement Implement Phases 1 to 7 of specs/004-crypt-solvability/tasks.md, in order, then stop. Do not start Phase 8.

Rules:
- Mark each task as done in tasks.md as you complete it.
- Follow the constitution: no dict, set, heapq, bisect, collections or graph libraries; no data of a specific crypt hard-coded; the view never modifies the model; --replay, --bench and --verificar never instantiate the view.
- One git commit per task (or per small group of closely related tasks), citing the task id (T0xx) and the FR-xxx requirements.
- Run the full test suite at the end of every phase; fix any regression before moving on.
- In grabar_offline.py (T017), delete nothing unless the crypt listing succeeded, was not empty, and every recording finished.
- Do not run any task that needs the network or deletes real data (the real re-recording): stop and tell me instead.
- If a task cannot be done as written, or the code contradicts the spec or the plan, STOP and tell me. Do not edit spec.md, plan.md or tasks.md to make the code fit.
- When you finish, report: tasks completed, files changed, test results, and anything skipped or blocked.


  - **Uso:** implementar las fases 1 a 7 de la especificación de verificación de resolubilidad de una cripta, siguiendo las reglas de constitución y reportando cualquier contradicción o tarea que no pueda completarse.

### 17 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:**  /speckit-implement Implement Phases 8 to 11 of specs/004-crypt-solvability/tasks.md, in order, then stop.

  Rules:
  - Mark each task as done in tasks.md as you complete it.
  - Follow the constitution: no dict, set, heapq, bisect, collections or graph libraries; no data of a specific crypt hard-coded; the view never modifies the model; --replay, --bench and --verificar never instantiate the view.
  - One git commit per task (or per small group of closely related tasks), citing the task id (T0xx) and the FR-xxx requirements.
  - Run the full test suite at the end of every phase; fix any regression before moving on.
  - In grabar_offline.py (T017), delete nothing unless the crypt listing succeeded, was not empty, and every recording finished.
  - Do not run any task that needs the network or deletes real data (the real re-recording): stop and tell me instead.
  - If a task cannot be done as written, or the code contradicts the spec or the plan, STOP and tell me. Do not edit spec.md, plan.md or tasks.md to make the code fit.
  - When you finish, report: tasks completed, files changed, test results, and anything skipped or blocked.

  Here is the text of Appendix B (solvability) for T037:
  - The exit key is behind the single door that it itself opens: not solvable; the report points out the cycle.
  - A key is in the "suelta" field of a wandering enemy: thee enemy's initial room.
  - Several valid orders of obtaining keys exist: two executions produce the same order.
  - A non-solvable crypt without --forzar: the game does notn.


  - **Uso:** implementar las fases 8 a 11 de la especificación de verificación de resolubilidad de una cripta, siguiendo las reglas de constitución y reportando cualquier contradicción o tarea que no pueda completarse.


### 17 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:** Yes, apply them directly (no need to propose first). Apply HIGH 4b, 7b and 8b; MEDIUM 1d, 1e, 2b, 4 and 8d; LOW 1c and 9c. Skip 9 (SC ids), 7c and 7d.
- 4b: state in T020, T022 and T028 that the game path uses self.repo_cripta and the verification reuses the skeleton the game already downloaded; add the test in T019 that counts pagina_esqueleto calls.
- 7b: in T017, delete only if the crypt listing succeeded and was not empty and every crypt was recorded without error; add tests for an empty listing and for a failure halfway.
- 8b: cap the naive pass-per-key benchmark at 10 000 rooms and 200 keys and the fast verification at 100 000 rooms; this benchmark must finish in about a minute.
- 1d: add to T007 the construction of a never-obtainable entry (id_sala None) for each key named by a door or the exit that is not in the key list.
- 1c: state that doors with a missing key start no flood, so the rooms behind them have no guard.
- 4: state in T022 and T028 that the key query uses the same client as the game, so it shares the request counter.
- 1e (spec change): reword FR-012(d) to describe exactly what the program reports (when several keys guard the same region, the lowest key id is chosen), keeping the phrase "doors that only it opens, directly or through a chain of keys" for the pure case. Note it in plan R5.
- 2b (spec change): narrow FR-010 to "the order in which the service lists keys and exits"; rooms are assumed sorted by id as in part one.
- 8d: state in the plan, R6 and T007 the complexity O((V+E) log V + K log K), since the position of each room in the sorted vector costs O(log V). Say it is still near-linear and that the benchmark shows it with operation counters.
- 9c: the four cases are the whole solvability section of Appendix B, so T037 only records the mapping. The cases are: (1) the exit key is behind the single door that it itself opens: not solvable and the report points out the cycle; (2) a key is in the "suelta" field of a wandering enemy: the verification places it in the enemy's initial room; (3) several valid orders: two executions give the same order; (4) a non-solvable crypt without --forzar: the game does not start and the report is shown.
Make two commits: first the spec.md changes (1e and 2b) alone, then the edits to plan.md, research.md and tasks.md. Change no code. When done, tell me the commit ids and whether anything still contradicts.


  - **Uso:** aplicar los cambios de documentación de la verificación de resolubilidad de una cripta, sin cambiar código, y reportar cualquier contradicción restante.

### 17 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:** Authorized: run T039 now (python grabar_offline.py against the real service), then T040 and T041. While recording, check that the request count of each crypt stays within its budget (cripta-06 has 63). If the whole offline/ folder is under about 5 MB, commit it in its own commit. Then run "python main.py --verificar <crypt>" on each of the five published crypts and report, for each one, whether it is solvable, the exit status and the report. Finally start cripta-02 online and tell me what the player sees at the start.
 - **Uso:** verificar la grabación offline de las criptas publicadas, comprobar que el conteo de solicitudes se mantiene dentro del presupuesto, ejecutar la verificación de resolubilidad en cada cripta y reportar los resultados, y finalmente iniciar cripta-02 en línea y describir lo que ve el jugador al inicio.

### 18 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:**  Task: bring docs/DECISIONS-style file docs/DECISIONES.md up to date and correct, WITHOUT touching anything Emily wrote.

  Context
  - docs/DECISIONES.md is the Part 2 decisions document, written in Spanish. Its numbering must match section 5 of the course statement: 5.1 hunter route, 5.2 route invalidation, 5.3 (and 5.3.1) "ir a" + its performance, 5.4 solvability, 5.5 timeline, 5.6 review of Part 1 decisions (5.6.1 event agenda, 5.6.2 undo history). Keep Spanish and the current voice.
  - Required fields per section (statement §7.1): problem, alternatives considered, decision, complexity, empirical evidence, known limits, links to spec and plan, and whether the decision matches the original plan.md (with before/after where something changed).
  - Andrea owns sections 5.3, 5.3.1 and 5.4 (specs 003-fog-of-war and 004-crypt-solvability). Emily owns 5.1, 5.2, 5.5 and 5.6 (specs 001, 002, 005). Do NOT edit, reword, reflow, renumber or reformat Emily's sections or the header table, and do not change any number in them. If you think something in her sections is wrong, list it in your final report and leave it as is.

  What to do (Andrea's sections only: 5.3, 5.3.1, 5.4)
  1. Read the real project, not just the docs: specs/003-fog-of-war/{spec,plan,tasks,research}.md, specs/004-crypt-solvability/{spec,plan,tasks,research}.md, the bench files (bench-ir-a.txt, bench-antes-ciclo.txt, bench-despues-ciclo.txt, bench-solvabilidad.txt), bench/bench_ir_a.py, bench/bench_solvabilidad.py, model/ruta_conocida.py, model/viaje_logica.py, structures/monticulo.py, the solvability module, and git log for the commits cited in the text.
  2. Check every claim in 5.3, 5.3.1 and 5.4 against code, specs and bench files: file names, function names, numbers (p99, max, ratios, ms), commit hashes, counts of tests, FR/R numbers, complexity formulas. Fix whatever does not match. Do not invent numbers: if a figure is not in a bench file or the code, remove it or mark it as not measured.
  3. Known problem to fix: in 5.3, the bullet "Qué la respalda" says the own benchmark "da un p99 de la ruta con 100 salas muy por debajo de 5 ms". The verdict is measured with 300 salas (cripta-06 size): p99 about 2.6-3.0 ms vs the 5 ms limit. Make 5.3 consistent with 5.3.1.
  4. Make sure each of the three sections has all the §7.1 fields, with links to its spec and plan, a clear "matches plan.md" paragraph (with commit hashes verified in git), and honest limits. Keep each section tight; remove repetition between 5.3 and 5.3.1.
  5. Check cross-references: the header table, the links to research.md and bench files must point to files that exist. Report broken links; fix only the ones in Andrea's sections.
  6. Check that nothing in Andrea's sections contradicts Emily's 5.1 and 5.2 (shared heap, shared stamp counter, rule A). If it does, report it.

  Constraints
  - Constitution applies: no dict/set/heapq/bisect/collections in evaluated code; this task only edits documentation, so do not change any source file, spec or bench file.
  - Make a single commit with message "docs: correct DECISIONES 5.3, 5.3.1 and 5.4 against specs 003 and 004" and show git diff --stat plus git diff for docs/DECISIONES.md. Confirm that the diff touches no line outside Andrea's sections (5.3, 5.3.1, 5.4).
  - Final report (short, in Spanish): what you changed and why, anything wrong you found in Emily's sections or elsewhere but did not touch, and any claim you could not verify.

 - **Uso:** actualizar y corregir la sección 5 del documento DECISIONES.md (apartados 5.3, 5.3.1 y 5.4) para reflejar correctamente la implementación real de las especificaciones 003-fog-of-war y 004-crypt-solvability, asegurando consistencia con el código, los benchmarks y los planes, sin modificar secciones de Emily ni código fuente.

### 18 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:** Task: fix a confusing crypt-selection menu in the console view (main.py / the console view that prints "Criptas disponibles").

Problem
The menu lists the crypts numbered 1..N by position, but the crypt ids are cripta-02 … cripta-06 (cripta-01 is no longer served). Example of what is printed today:
  1. Catacumbas menores (cripta-02) - 20 salas, dificultad 2
  2. Catacumbas medias (cripta-03) ...
  5. Cripta de referencia (cripta-06) ...
If the player types "02" (or "2") expecting cripta-02, the game starts cripta-03, because the typed number is treated as the list position. This is confusing.

Desired behavior
- The number shown in the menu must be the crypt's own number, taken from its id (cripta-02 -> 2, cripta-06 -> 6), so what the player sees is what the player types. Example:
  2. Catacumbas menores (cripta-02) - 20 salas, dificultad 2
  3. Catacumbas medias (cripta-03) - ...
  6. Cripta de referencia (cripta-06) - ...
- Derive the number from the id returned by the service (the numeric suffix of "cripta-NN"); do NOT hardcode 2..6, because the catalog can change. If an id does not follow the "cripta-NN" pattern, fall back to its list position and keep the menu consistent for that entry.
- Input handling: accept "2", "02" and "cripta-02" (case and surrounding spaces ignored) as the same choice; "salir" still exits. If the input matches no listed crypt, print a clear message ("No existe esa cripta. Elegí un número de la lista.") and ask again; never start a different crypt than the one typed.
- The prompt text stays in Spanish and should say that the number is the crypt's number, e.g. "Elige una cripta (número, o 'salir'):".
- Keep the existing layering: the choice logic lives where the current menu logic lives (view/controller); do not move service or data-layer code, and do not change the DTOs unless strictly necessary. Do not add dict, set, heapq, bisect or collections if the constitution forbids them for evaluated code; a simple loop over the list is enough.

Also do
1. Find every place that prints or parses this menu (main.py, console view, controller, README examples, any test or script that feeds a choice) and make them consistent.
2. Add or update tests: (a) typing "2", "02" and "cripta-02" selects cripta-02; (b) typing "6" selects cripta-06; (c) an unlisted number ("1", "7", "abc") re-prompts and starts nothing; (d) "salir" exits; (e) ids not matching the pattern fall back to list position. All existing tests must still pass.
3. Follow the project's spec-kit rules from the constitution for a small fix (read it first). If it requires a spec/tasks entry for any behavior change, add the smallest one; otherwise just reference this fix in the commit message.
4. Update README if it shows the menu or says how to choose a crypt.

Constraints and report
- Touch only what this fix needs. Show `git diff --stat`, then commit with a clear message ("fix: crypt menu shows the crypt's own number and accepts 2, 02 or cripta-02").
- Final report (short, in Spanish): files changed, the new menu output, and the test results.

 - **Uso:** arreglar el menú de selección de cripta en la vista de consola para que muestre el número propio de la cripta y acepte entradas como "2", "02" o "cripta-02", asegurando consistencia en todas las partes del código y pruebas, y reportando los cambios realizados.

### 18 de Noviembre, 2026
- **Herramienta:** Claude Code
- **Prompt:** Task: fix the broken replay example and clean up the repository before the final submission. Work in small, separate commits.

Problem
`python main.py --replay docs/ejemplo_partida.txt` (documented in README section 6) no longer works. The log header was recorded on 2026-10-18 with cripta-04 version d6727c7f4950 and catalog version be68d322d2f5, but the service and the offline package now report different versions (cripta-04 7074a17814ad, catalog 4b9e75a42be5), so the program correctly refuses: "No se puede garantizar una reproducción fiel...". The example must be re-recorded.

1. Re-record docs/ejemplo_partida.txt
- Use a published crypt (prefer cripta-02, the small one) against the real service (online), with a fixed seed if main.py/aplicacion.py supports choosing one; otherwise use whatever seed the game produces.
- Produce the log by driving the real game with scripted input (pipe commands to `python main.py <crypt>` or call the same application entry point used by main.py). Do NOT hand-write the log lines. The scripted session must be short (about 15 to 30 commands) and show the main features: movement, `mapa`, `ir a <id>` to an explored room, picking up and using or equipping an item, one `historia <t>` or `historia #k` query (these are not logged, that is fine), and ending with `salir`. If a command in the script is rejected by the game, adjust the script until the log is clean.
- Copy the resulting saves/partida_<crypt>_<seed>.log to docs/ejemplo_partida.txt (overwrite). Keep the header format exactly as produced by the program.
- Verify, and show the output of each: 
  a) `python main.py --replay docs/ejemplo_partida.txt` (online) runs to the end without errors and without asking for input;
  b) `python main.py --offline --replay docs/ejemplo_partida.txt` also works, which requires that the header versions match the versions in the offline/ package. If they do not match, re-run `python grabar_offline.py` (it is allowed, it records from the real service and keeps only listed crypts) and re-record the log so that both a) and b) pass;
  c) `python main.py --replay docs/ejemplo_partida.txt --hasta 20` prints the summary of that instant.
- Check that no test depends on the old docs/ejemplo_partida.txt (grep tests/, README, specs/, docs/). Update any reference (README section 6, tests, quickstart files) to the new crypt/seed if needed. Run the whole suite (`python -m pytest`) and report the count; it must stay green (617 passed at last check).
- Commit: "docs: re-record ejemplo_partida with current crypt and catalog versions".

2. Prompts log
- In Prompts_LLM_AndreaC.md there are 57 uncommitted lines. The two newest entries (the DECISIONES.md correction prompt and the crypt menu prompt) are dated "17 de Noviembre, 2026" but were made on 18 de Noviembre; fix those two dates only. Do not edit any other entry. Add one entry (same format: date / Herramienta / Prompt / Uso) for this very task, dated 18 de Noviembre, 2026. Commit: "docs: update Andrea's prompt log".

3. Repository hygiene
- Add `.claude/settings.local.json` to .gitignore (it is untracked and must not be committed).
- There is an untracked file prueba_criptas.py in the project root. Move it to pruebas_manuales/ as prueba_criptas.py, fix its docstring (it says probar_criptas.py), and add one line for it in the README note about pruebas_manuales (it queries the real service but does not spend the player's request budget). Do not commit it if you find it cannot run from pruebas_manuales with `python -m pruebas_manuales.prueba_criptas`; in that case delete it and say so.
- Commit: "chore: ignore local Claude settings; move prueba_criptas to pruebas_manuales".

4. README documentation links (only if the files exist)
- If docs/Documento_de_Decisiones.docx exists, add it to README section 8 next to the PDF link ("Documento de Decisiones de la primera parte, versión mejorada"). If it does not exist, do nothing and say so. Do not touch docs/DECISIONES.md.

Constraints
- Do not change source code under model/, structures/, data/, service/, adapters/, controller/ or view/. Do not change any spec, bench or tests except to update a reference to the example log.
- Do not run `git push`; I will push myself after reviewing.
- Final report (short, in Spanish): the new log header, the output of checks a), b), c), the test result, `git log --oneline -5`, and anything you could not do.

- **Uso:** arreglar el ejemplo de reproducción de partida en docs/ejemplo_partida.txt, actualizar el registro de prompts de Andrea, limpiar el repositorio y verificar que todo funciona correctamente, sin cambiar código fuente ni especificaciones.