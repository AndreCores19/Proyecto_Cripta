"""El libro de efectos omitidos (spec 005, investigación R6).

El deshacer de la parte uno deja afuera, a propósito, algunos efectos (el pergamino gastado, los
pergaminos que una acción revertida movió, el contador de instancias, las salas que un movimiento
revertido pobló). Después de un pergamino, reproducir las acciones que sobrevivieron no da el estado
vivo si no se aplican también esos efectos; cada uno queda aquí, con la frontera en que hay que aplicarlo.

Los datos son tuplas simples de enteros y textos: nada apunta a objetos vivos.
"""

POBLAR = "poblar"                  #(id_sala, contador_inicial)
SUELO_QUITAR = "suelo_quitar"      #(id_sala, id_instancia)
SUELO_PONER = "suelo_poner"        #(id_sala, id_instancia, id_catalogo)
INV_AGREGAR = "inv_agregar"        #(id_instancia, id_catalogo)
INV_QUITAR = "inv_quitar"          #(id_instancia,)
CONTADOR = "contador"              #(valor,)


class EfectoOmitido:
    """`etiqueta`: cuántas acciones hechas hay cuando se aplica (la frontera). `reaplicar` es falso mientras
    solo es candidato (la acción que lo causó aún puede revertirse) y verdadero cuando un pergamino lo guardó."""
    __slots__ = ("etiqueta", "reaplicar", "tipo", "datos")

    def __init__(self, etiqueta, reaplicar, tipo, datos):
        self.etiqueta = etiqueta
        self.reaplicar = reaplicar
        self.tipo = tipo
        self.datos = datos


def aplicar(entrada, mundo, partida):
    """Aplica una entrada al mundo aparte de una consulta. Lo que ya no está o ya está se deja como está."""
    tipo = entrada.tipo
    datos = entrada.datos
    fabrica = mundo.fabrica
    if tipo == POBLAR:
        if fabrica is None:
            return
        sala = mundo.salas.buscar(datos[0])
        if not fabrica.esta_poblada(sala):
            fabrica.siguiente_instancia = datos[1]       #la población sale con los ids de cuando ocurrió
            fabrica.poblar_sala(sala)
    elif tipo == CONTADOR:
        if fabrica is not None:
            fabrica.siguiente_instancia = datos[0]
    elif tipo == SUELO_QUITAR:
        objetos = mundo.salas.buscar(datos[0]).objetos
        for i in range(len(objetos)):
            if objetos[i].id_instancia == datos[1]:
                del objetos[i]
                break
    elif tipo == SUELO_PONER:
        mundo.salas.buscar(datos[0]).objetos.append(mundo.crear_objeto(datos[1], datos[2]))
    elif tipo == INV_AGREGAR:
        partida.jugador.inventario.agregar(mundo.crear_objeto(datos[0], datos[1]))
    elif tipo == INV_QUITAR:
        inventario = partida.jugador.inventario
        nodo = inventario.cabeza
        while nodo is not None:
            if nodo.objeto.id_instancia == datos[0]:
                inventario.quitar_nodo(nodo)
                break
            nodo = nodo.siguiente
    else:
        raise ValueError(f"Tipo de efecto omitido desconocido: {tipo}")
