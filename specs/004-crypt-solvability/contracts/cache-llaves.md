# Contract: saved key locations (data ↔ disk)

## File

`cache/llaves/<id_cripta>.json`

```json
{"version": "fd58f7743b9e", "llaves": [{"id": "itm_llave_bronce", "sala": 2}]}
```

## Reading

`AlmacenLlaves.leer(id_cripta)` returns `(version, llaves)` or `None` if the file is missing, is not valid
JSON, or lacks a field. A damaged file is treated as missing (as `AlmacenFichas` does).

## Rule (FR-005)

- `version` equal to the crypt version of this run (the `version` of the `datos` answer): use the saved list;
  no request.
- Otherwise (different version, or no valid file): make the query (one request) and overwrite the file with the
  new version.
- Nothing is ever deleted by hand (Constitution V): the stored version is the only invalidation.

## Limits

One file per crypt id. The file holds the answer exactly as the service gave it, with no derived data.
