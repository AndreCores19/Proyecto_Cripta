"""Texto del reporte de verificación, para el juego y para --verificar (FR-012, FR-014, FR-017).

Funciones simples sobre el DTO del reporte; no importa nada de model/ ni de view/.
"""


def _ubicacion(llave):
    if llave.id_sala is None:
        return f"{llave.id_llave} (sin ubicación)"
    if llave.id_enemigo is not None:
        return f"{llave.id_llave} (sala {llave.id_sala}, la lleva el enemigo {llave.id_enemigo})"
    return f"{llave.id_llave} (sala {llave.id_sala})"


def _exige(puerta):
    return "no tiene llave" if puerta.id_llave is None else f"exige {puerta.id_llave}"


def lineas_reporte(reporte):
    """Líneas del reporte, con el formato de contracts/reporte-verificacion.md."""
    if reporte.resoluble:
        lineas = [f"Verificación de {reporte.id_cripta}: se puede ganar.", "Orden de llaves:"]
        for i, id_llave in enumerate(reporte.orden, 1):
            lineas.append(f"  {i}. {id_llave}")
        return lineas
    lineas = [f"Verificación de {reporte.id_cripta}: NO se puede ganar."]
    if reporte.llaves_inalcanzables:
        lineas.append("Llaves que no se pueden conseguir:")
        for llave in reporte.llaves_inalcanzables:
            lineas.append(f"  {_ubicacion(llave)}")
    if reporte.puertas_frontera:
        lineas.append("Puertas de la frontera bloqueada:")
        for p in reporte.puertas_frontera:
            lineas.append(f"  sala {p.id_sala}, {p.direccion} -> sala {p.id_destino}: {_exige(p)}")
    for ciclo in reporte.ciclos:
        lineas.append("Ciclo:")
        for e in ciclo:
            lineas.append(f"  {e.id_llave} (sala {e.id_sala}) está tras la puerta de la sala {e.puerta.id_sala}, "
                          f"{e.puerta.direccion}, que exige {e.id_llave_guardia}")
    return lineas


def imprimir_reporte_verificacion(reporte):
    for linea in lineas_reporte(reporte):
        print(linea)
