# Contract: key locations in the offline package (FR-006)

## Files

`offline/<id_cripta>/llaves.json`: the body of the key query for that crypt, exactly as the service answers
(see [consulta-llaves.md](./consulta-llaves.md)).

## Recording

`grabar_offline.py` makes one key query per crypt on that crypt's own client (one extra request within the
crypt's budget, as the other recorded requests) and writes the answer. The recording step is the only thing that
changes; no game code reads the package directly.

## Reading

`ClienteOffline.llaves(id_cripta)` returns the parsed file. A missing file raises the existing "falta en el
paquete sin conexión" error, so a package recorded before this feature fails clearly instead of giving a
wrong verdict.

## Notes

The package holds only the crypts the service serves (today `cripta-02` to `cripta-06`); `cripta-01`, which the
service does not serve, is removed (FR-006, plan point 8).
