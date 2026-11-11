# Contract: generic min-heap (`structures/monticulo.py`)

Used by the hunter search; reused unchanged by the "ir a" travel of spec 003. It does not depend on
anything else in the project.

## Interface

| Call | Returns | Cost | Notes |
|---|---|---|---|
| `MonticuloMinimo()` | heap | O(1) | empty |
| `insertar(prioridad, valor)` | None | O(log n) | `prioridad` is any value that supports `<` (numbers, tuples of numbers) |
| `extraer()` | `(prioridad, valor)` or `None` | O(log n) | the smallest priority; `None` when empty |
| `proximo()` | `(prioridad, valor)` or `None` | O(1) | does not remove |
| `vaciar()` | None | O(1) | empties the heap and restarts the insertion counter |
| `len(heap)` | int | O(1) | |

## Order

- An entry `a` comes out before `b` when `a.prioridad < b.prioridad`.
- If neither `a.prioridad < b.prioridad` nor `b.prioridad < a.prioridad`, the entry inserted first comes out first.
- Only `<` is used on priorities; `==` is never needed.

## Ties and reuse

The insertion-order rule for equal priorities makes the heap itself deterministic, but it follows the order in which the caller inserts, which usually comes from data order (for example the order of a room's exits). **Anyone who reuses the heap must break ties with an explicit rule of their own** (for example the lowest room id) wherever a tie can change a result, and must not rely on the heap's insertion order for that. The hunter search does not need it: it keeps minimum distances (the same in any order) and chooses the exit with the rule `(room id, direction)`.

## Not offered

- No decrease-key and no cancel by position. A user re-inserts a value with a better priority and skips the stale entry when it comes out (the search does: `d > sala.busq_dist`).
- No undo registration: it never touches `Historial`.

## Tests (tests/test_monticulo.py)

- Extraction order equals a sorted list for 1000 seeded random priorities.
- Equal priorities come out in insertion order (FIFO).
- Tuple priorities.
- A user that needs a tie-break puts it in the priority (for example `(cost, room id)`), not in the insertion order.
- `extraer` and `proximo` on an empty heap return `None`.
- `vaciar` then reuse gives the same order as a new heap.
