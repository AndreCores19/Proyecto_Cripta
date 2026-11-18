# Research: Crypt Solvability Verification

Each entry: decision, rationale, alternatives considered. No open `NEEDS CLARIFICATION`; the points
that need the spec are in `plan.md` ("Points for the spec").

## R1. What the key query returns and what the pass needs from it

**Decision**: `GET /criptas/{id}/llaves` answers `{"llaves": [{"id": ..., "sala": ...}, ...]}`; a key carried
by an enemy also has `"enemigo": "<enemy id>"`. The pass uses `id` and `sala` only; `enemigo` is kept in the
DTO to show it in the report (FR-012 c).

**Rationale**: Read from the live service on 2026-11-17 for `cripta-02`, `cripta-03` and `cripta-06`
(for example `{"id": "itm_llave_hierro", "sala": 16, "enemigo": "e-cripta-03-8"}`). The service already gives,
for an enemy-carried key, the room where the enemy starts (the brief's FR-003), so no enemy lookup and no
content download is needed, and the query is one request per crypt.

**Alternatives**: (a) Derive locations from the room contents and the catalog (items on the floor, what each
enemy type drops): needs the content of every room (many requests) and the catalog; the brief asks for the
query. (b) Ask once per key: more requests for the same answer.

## R2. Saving the key locations between runs

**Decision**: `cache/llaves/<id_cripta>.json` with `{"version": "<crypt version>", "llaves": [...]}`. On
`cargar`, if the file exists, parses, and its version equals the crypt's version, use it without a request;
otherwise query and overwrite the file.

**Rationale**: Same rule as the item catalog (`cache/catalogo`, `version.txt`): the version check is the
only invalidation (Constitution V), a damaged file is treated as missing, and the answer can never outlive
its version. The crypt's version comes from the `datos` request the program already makes. A new version
changes the stored version and the file is rewritten; nothing is deleted by hand.

**Alternatives**: (a) Query every run: spends one of the 23 to 63 requests of each crypt every time.
(b) Keep it only in memory: same cost per run. (c) Key the file name by version and keep old files: leaves
stale files behind.

## R3. Key locations offline

**Decision**: `grabar_offline.py` records `offline/<id>/llaves.json` for each crypt (one extra request on that
crypt's own client, within its budget); `ClienteOffline.llaves(id)` reads it and, like every offline call,
counts no request.

**Rationale**: `ClienteOffline` is meant to answer exactly like `ClienteHttp`, from recorded files; the
model and the services do not know which one they have (spec clarification 2026-11-17, FR-006). A missing
file raises the existing "falta en el paquete sin conexión" error.

**Alternatives**: deriving the locations from the recorded contents and catalog (rejected in the
clarification); skipping the verification offline (rejected).

## R4. The pass and the order of keys

**Decision**: One traversal that interleaves two things: growing the reached region with a queue, and taking
keys from a min-heap ordered by key id (text). A closed exit that needs a key not yet taken waits in that
key's list and is released when the key is taken.

**Rationale**: Each exit is handled once when its origin is reached and at most once more when released, so
there is no repeated pass per key (FR-019). Taking the lowest id from the heap is FR-011 literally, and
because the heap only holds keys located in reached rooms, every key comes after the keys that open its way
(FR-009). The result does not depend on the order of the queue, of `Sala.salidas` or of the key list: the
reached set after growing is a fixed point, and the heap order is by id.

**Alternatives**: (a) Repeat a full reachability pass after each key (the naive alternative, kept only in
the benchmark and as the test oracle): `O(K(V + E))`. (b) Topological sort of a key-dependency graph built
first: needs a way to say which keys each key depends on, which is what the pass computes anyway; building it
would take its own pass. (c) A priority queue ordered by something else (room id, discovery order): fails
FR-011.

## R5. The report of a non-solvable crypt

**Decision**: (a)–(c) come straight from the state the pass leaves (keys not taken, exits still waiting,
key records). (d): one flood over the rooms the pass did not reach, ignoring locks, starting from the
frontier doors grouped by key in increasing key id, labelling each room with the first (lowest) key that
reaches it; the guard of an unobtainable key is the label of its room; cycles are found by following guards.

**Rationale**: Every route from the reached region to a room not reached starts with a frontier door, so "the
keys that guard a room" are among the frontier keys that can reach it; taking the lowest one makes the guard
unique and the result independent of listing order (Constitution II). Each room is labelled once (a room
labelled by a lower key is not entered by a higher one: whatever is behind it is reachable from the lower
key too), so the sweep is linear in the part of the crypt the pass left, whatever the number of keys. With one
outgoing guard per key, a walk that marks keys with the starting key finds each cycle once. The case of the
spec scenario (the exit key behind the only door that it opens itself) is a cycle of length one.

**Cost of the other reading of "the same pass"**: folding the sweep into the traversal would mean flooding
beyond a closed door at the moment it is found, ignoring its lock, and undoing the flood for the doors that
open later; that makes the traversal visit rooms behind locks that will open, which is the quadratic
behaviour FR-019 forbids. The sweep after the pass visits only rooms that stay locked.

**Alternatives**: (a) A search for a cycle per unobtainable key: a pass per key, FR-013 forbids it.
(b) Report only the first cycle: loses information when there are several.

## R6. Where each part lives, and why not in the existing model

**Decision**: A new model file (`model/solvabilidad_logica.py`); the player's knowledge fields
(`Sala.conocimiento`, `Salida.memoria`) are not read, and no field is added to `Sala` or `Salida`. Per-room
state is lists indexed by the room's position in `RepositorioCripta.salas` (a binary-search vector the data
layer already builds), so the verification can run on the freshly built rooms before any game exists.

**Rationale**: The brief says the fog of war does not apply (FR-001). Using lists indexed by position keeps
the verification free of the search stamps used by the hunters and by "ir a", so it cannot disturb their
saved searches. A closed exit whose destination is already reached is skipped without looking at its key.

**Alternatives**: stamping fields in `Sala` (adds fields used by one feature only and couples it to the
hunters' stamp counter).

## R7. Finding a key by id without `dict`

**Decision**: Keys are put in the existing binary-search vector sorted by id (text), built once per
verification: `O(K log K)` to sort the listing (with `ordenar`) and `O(log K)` per lookup.

**Rationale**: The service lists keys in any order (FR-010), so the vector is built by sorting, not by trusting
the listing. The vector only needs `==` and `<` on ids, which hold for text.

**Alternatives**: a linear search per door (`O(E K)`): breaks FR-019; a hash index: forbidden (Constitution I).

## R8. Where verification runs in the program

**Decision**: `Aplicacion.jugar` verifies once, before asking for the player's name and before the first
session; loading a saved game inside the session loop does not verify again. `--verificar` calls
`verificar_cripta`, which builds only the crypt repository, the key repository and the service, and prints
with `adapters/salida_verificacion.py`. `--forzar` is a flag of `jugar` only.

**Rationale**: `Aplicacion.__init__` builds the whole game (catalog included, which makes requests);
`--verificar` does not need any of it and must not spend requests on it. Printing with plain functions is the
`--replay` pattern, which already shows that a headless command creates no view class (Constitution III).

**Alternatives**: verifying inside `_sesion` (repeats at every load); running the verification in the
controller (the controller starts after the game exists).

## R9. The benchmark and its naive alternative

**Decision**: `bench/bench_solvabilidad.py` builds synthetic crypts directly as rooms, with a seeded builder
for (a) the size of the largest published crypt and (b) chained-key crypts where key `i` lies in the region
that key `i-1` opens. The naive alternative (one reachability pass from scratch per key taken, picking the lowest
id obtainable) lives in the benchmark and, as an independent implementation, in the test oracle; the
benchmark checks both give the same order of keys.

**Rationale**: FR-021 asks `--bench` to measure the naive alternative with many chained keys, which is the
shape on which it is quadratic. Equal orders prove that the fast pass is the same function, only faster.
