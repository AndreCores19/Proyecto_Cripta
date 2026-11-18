# Contract: key query (adapters → service)

## Request

`GET /criptas/{id_cripta}/llaves`, with the same client id header as every other request.

- `ClienteHttp.llaves(id_cripta)` calls it through the same `_get` as every other request: it counts one
  request, refuses past `presupuesto_solicitudes`, retries on 429 and raises `ErrorCliente` on any other error
  (FR-004).
- `ClienteOffline.llaves(id_cripta)` reads `offline/<id_cripta>/llaves.json` and counts nothing; a missing file
  raises `ErrorOffline` ([paquete-offline-llaves.md](./paquete-offline-llaves.md)).

## Answer (observed 2026-11-17)

```json
{"llaves": [
  {"id": "itm_llave_bronce", "sala": 2},
  {"id": "itm_llave_hierro", "sala": 16, "enemigo": "e-cripta-03-8"}
]}
```

- `id`: the key id, as named by `Salida.llave` in the skeleton.
- `sala`: the room where the key is. When `enemigo` is present, it is the room where that enemy starts (FR-003).
- `enemigo`: present only when an enemy carries the key.
- The order of the list means nothing (FR-010).

## Data layer

`RepositorioLlaves.cargar(id_cripta, version)` returns a list of `LlaveUbicacionDTO(id_llave, id_sala,
id_enemigo)`; it first looks at the saved file ([cache-llaves.md](./cache-llaves.md)) and queries only when
the file is missing, damaged or of another version.
