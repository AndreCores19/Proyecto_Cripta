from dto.contenido_sala_dto import ContenidoSalaDTO
from dto.datos_cripta_dto import DatosCriptaDTO
from dto.sala_dto import SalaDTO
from structures.cola import Cola
from structures.vector_busqueda import VectorBusqueda
from model.sala_logica import Sala, Salida

## funcion auxiliar de direccion opuesta
def direccion_opuesta(direccion):
    if direccion == "N":
        return "S"
    if direccion == "S":
        return "N"
    if direccion == "E":
        return "O"
    if direccion == "O":
        return "E"
    return None

class RepositorioCripta:
    def __init__(self, fuente):
        self.fuente = fuente
        self.datos = None
        self.salas = None
        self.contenidos = None

    def cargar_datos(self, id_cripta):
        datos = DatosCriptaDTO.desde_json(self.fuente.datos_cripta(id_cripta))
        self.datos = datos
        self.fuente.asignar_presupuesto(datos.presupuesto_solicitudes)

    def cargar_esqueleto(self, id_cripta):
        if self.datos is None or self.datos.id_cripta != id_cripta:
            self.cargar_datos(id_cripta)

        salas = []
        for pagina in range(1, self.datos.paginas + 1):
            respuesta = self.fuente.pagina_esqueleto(id_cripta, pagina)
            for sala_json in respuesta["salas"]:
                salas.append(SalaDTO.desde_json(sala_json))

        return salas

    def construir_salas(self, dtos):
        vector = VectorBusqueda()
        creadas = []

        ## Primer ciclo crea las salas
        for dto in dtos:
            sala = Sala(dto.id_sala, dto.nombre)
            vector.agregar(dto.id_sala, sala)
            creadas.append(sala)

        vector.preparar()
        self.contenidos = [None] * vector.tamano()

        ## Segundo ciclo enlaza las salidas
        for i in range(len(dtos)):
            dto = dtos[i]
            origen = creadas[i]
            for salida_dto in dto.salidas:
                destino = vector.buscar(salida_dto.id_destino)
                if destino is None:
                    raise ValueError(
                        f"La sala {dto.id_sala} tiene una salida {salida_dto.direccion} "
                        f"hacia la sala {salida_dto.id_destino}, que no existe"
                    )
                origen.agregar_salida(Salida(
                    direccion=salida_dto.direccion,
                    destino=destino,
                    cerrada=salida_dto.cerrada,
                    llave=salida_dto.llave,
                    cierre_automatico=salida_dto.cierre_automatico,
                    costo=salida_dto.costo,
                ))
        ## tercer ciclo enlaza las salidas opuestas
        for sala in creadas:
            for salida in sala.salidas:
                if salida.opuesta is not None:
                    continue
                otra = salida.destino.salida(direccion_opuesta(salida.direccion))
                if otra is None:
                    continue
                if otra.destino is not sala:
                    raise ValueError(
                        f"Puerta inconsistente: la salida {salida.direccion} de la sala "
                        f"{sala.id} va a la sala {salida.destino.id}, pero la salida "
                        f"{otra.direccion} de esa sala va a la sala {otra.destino.id}"
                    )
                if (salida.costo_declarado is not None
                        and otra.costo_declarado is not None
                        and salida.costo_declarado != otra.costo_declarado):
                    raise ValueError(
                        f"Puerta inconsistente: la salida {salida.direccion} de la sala "
                        f"{sala.id} cuesta {salida.costo_declarado}, pero la salida "
                        f"{otra.direccion} de la sala {salida.destino.id} "
                        f"cuesta {otra.costo_declarado}"
                    )
                salida.enlazar(otra)
        self.salas = vector

    def precargar(self, id_sala):
        if self.contenidos is None:
            raise ValueError("No se han construido las salas")

        sala_actual = self.salas.buscar(id_sala)
        if sala_actual is None:
            raise ValueError(f"La sala {id_sala} no existe")

        visto = [False] * self.salas.tamano()
        cola = Cola()
        lote = []

        visto[self.salas.posicion(id_sala)] = True
        cola.encolar(sala_actual)

        while not cola.esta_vacia() and len(lote) < 10:
            sala = cola.desencolar()
            pos = self.salas.posicion(sala.id)
            if self.contenidos[pos] is None:
                lote.append(sala.id)

            for salida in sala.salidas:
                if salida.destino is not None:
                    pos_destino = self.salas.posicion(salida.destino.id)
                    if not visto[pos_destino]:
                        visto[pos_destino] = True
                        cola.encolar(salida.destino)

        nuevos = []
        if lote:
            respuesta = self.fuente.contenido_salas(self.datos.id_cripta, lote)
            for elemento in respuesta["contenido"]:
                dto = ContenidoSalaDTO.desde_json(elemento)
                self.contenidos[self.salas.posicion(dto.id_sala)] = dto
                nuevos.append(dto)
        return nuevos