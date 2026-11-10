# Contract: exit in a skeleton page (input)

Source: `GET` skeleton page (`pagina_esqueleto`), or the offline `esqueleto_<n>.json` file.

```json
"salidas": {
  "N": { "sala": 12, "cerrada": true, "llave": "itm_llave_bronce", "costo": 300 },
  "S": { "sala": 10 }
}
```

| Field | Required | Default | Meaning |
|---|---|---|---|
| sala | yes | — | destination room id |
| cerrada | no | false | part one |
| llave | no | null | part one |
| cierre_automatico | no | null | part one |
| costo | no | 100 (after linking) | base cost of moving through this exit, same in both directions |

Rejection: only the inconsistent-door case, where the two sides of a connection both declare
`costo` and the values differ. It is reported with the same `ValueError("Puerta inconsistente: …")`
as a part-one inconsistent door.
