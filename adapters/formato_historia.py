"""Texto del resumen de `historia` (spec 005, FR-004, FR-014).

Funciones puras: reciben DTOs y devuelven listas de líneas; no imprimen ni importan nada de model/ ni
de view/. La vista de consola y la salida de --replay imprimen estas mismas líneas, así el texto es
idéntico en los dos caminos.
"""


def lineas_mapa(mapa):
    """El mapa conocido, en el mismo formato que el comando `mapa`."""
    lineas = ["Mapa conocido:"]
    for sala in mapa.salas:
        aqui = "  (tú estás aquí)" if sala.id_sala == mapa.id_sala_actual else ""
        lineas.append(f"  Sala {sala.id_sala}: {sala.nombre}{aqui}")
        for s in sala.salidas:
            if s.id_destino is None:
                destino = "sin explorar"
            else:
                destino = f"Sala {s.id_destino}: {s.nombre_destino}"
            lineas.append(f"    {s.direccion} -> {destino} ({s.puerta}, costo {s.costo})")
    return lineas


def lineas_historia(resumen):
    """Las líneas del resumen de un instante pasado (`ResumenHistoriaDTO`)."""
    j = resumen.jugador
    efectos = ", ".join(j.efectos)
    lineas = [
        "-" * 40,
        f"Historia en el instante {resumen.reloj}",
        f"Sala {resumen.id_sala}: {resumen.nombre_sala}",
        f"Jugador: {j.nombre} (Vida: {j.vida}/{j.vida_max})",
        f"  Ataque: {j.ataque}  Defensa: {j.defensa}  Velocidad: {j.velocidad}",
        f"  Arma: {j.arma if j.arma is not None else 'ninguna'}",
        f"  Armadura: {j.armadura if j.armadura is not None else 'ninguna'}",
        f"  Efectos: {efectos if efectos else 'ninguno'}",
        "Inventario:",
    ]
    if not resumen.inventario:
        lineas.append("  (vacío)")
    for objeto in resumen.inventario:
        equipo = " (equipado)" if objeto.equipado else ""
        lineas.append(f"  [{objeto.id_instancia}] {objeto.nombre}{equipo}")
    lineas.append("Enemigos en la sala:")
    if not resumen.enemigos:
        lineas.append("  (ninguno)")
    for enemigo in resumen.enemigos:
        marca = " (cazador)" if enemigo.cazador else ""
        linea = (f"  {enemigo.nombre}{marca} [{enemigo.id_enemigo}] "
                 f"(Vida: {enemigo.vida}/{enemigo.vida_max})")
        if enemigo.efectos:
            linea += f" [{', '.join(enemigo.efectos)}]"
        lineas.append(linea)
    lineas.extend(lineas_mapa(resumen.mapa))
    lineas.append("-" * 40)
    return lineas
