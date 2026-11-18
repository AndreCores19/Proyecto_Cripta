import struct

from dto.contenido_sala_dto import (ContenidoSalaDTO, InstanciaEnemigoDTO,InstanciaTrampaDTO)
from structures.vector_busqueda import VectorBusqueda

MAGIC = b"CRPT"
VERSION_FORMATO = 2
PREFIJO = "<4sH"                ## magic, versión: se lee primero y solo (6 bytes)
FORMATO_FIJO = "<QIIQQI"        ## v2: semilla, n_salas, n_comandos, off_indice, off_comandos, k
FORMATO_INDICE = "<IQI"         ## id_sala, offset, largo


class ErrorGuardado(Exception):
    """Error al leer o escribir un archivo de guardado."""

class GuardadoBinario:
    def _leer(self, archivo, formato):
        tamano = struct.calcsize(formato)
        datos = archivo.read(tamano)
        if len(datos) < tamano:
            raise ErrorGuardado("El archivo está truncado")
        return struct.unpack(formato, datos)

    def escribir_cadena(self, archivo, texto):
        datos = texto.encode("utf-8")
        archivo.write(struct.pack("<H", len(datos)))
        archivo.write(datos)

    def leer_cadena(self, archivo):
        (longitud,) = self._leer(archivo, "<H")
        datos = archivo.read(longitud)
        if len(datos) < longitud:
            raise ErrorGuardado("El archivo está truncado")
        return datos.decode("utf-8")

    def escribir_sala(self, archivo, dto):
        archivo.write(struct.pack("<I", dto.id_sala))

        archivo.write(struct.pack("<H", len(dto.enemigos)))
        for enemigo in dto.enemigos:
            self.escribir_cadena(archivo, enemigo.instancia)
            self.escribir_cadena(archivo, enemigo.tipo)
            vida = -1 if enemigo.vida is None else enemigo.vida
            archivo.write(struct.pack("<i", vida))

        archivo.write(struct.pack("<H", len(dto.objetos)))
        for id_objeto in dto.objetos:
            self.escribir_cadena(archivo, id_objeto)

        archivo.write(struct.pack("<H", len(dto.trampas)))
        for trampa in dto.trampas:
            self.escribir_cadena(archivo, trampa.instancia)
            self.escribir_cadena(archivo, trampa.tipo)

    def leer_sala(self, archivo):
        (id_sala,) = self._leer(archivo, "<I")

        enemigos = []
        (n_enemigos,) = self._leer(archivo, "<H")
        for _ in range(n_enemigos):
            instancia = self.leer_cadena(archivo)
            tipo = self.leer_cadena(archivo)
            (vida,) = self._leer(archivo, "<i")
            if vida == -1:
                vida = None
            enemigos.append(InstanciaEnemigoDTO(instancia, tipo, vida))

        objetos = []
        (n_objetos,) = self._leer(archivo, "<H")
        for _ in range(n_objetos):
            objetos.append(self.leer_cadena(archivo))

        trampas = []
        (n_trampas,) = self._leer(archivo, "<H")
        for _ in range(n_trampas):
            instancia = self.leer_cadena(archivo)
            tipo = self.leer_cadena(archivo)
            trampas.append(InstanciaTrampaDTO(instancia, tipo))

        return ContenidoSalaDTO(id_sala, enemigos, objetos, trampas)

    ## Encabezado

    def _escribir_cabecera(self, archivo, cab):
        archivo.write(struct.pack(PREFIJO, MAGIC, VERSION_FORMATO))
        archivo.write(struct.pack(FORMATO_FIJO, cab.semilla, cab.n_salas, cab.n_comandos,
                                  cab.off_indice, cab.off_comandos, cab.k))
        self.escribir_cadena(archivo, cab.id_cripta)
        self.escribir_cadena(archivo, cab.version_cripta)
        self.escribir_cadena(archivo, cab.version_catalogo)

    def leer_cabecera(self, archivo):
        #primero magic y versión: un v1 (aunque sea más corto que la cabecera v2) es incompatible, no truncado
        magic, version = self._leer(archivo, PREFIJO)
        if magic != MAGIC:
            raise ErrorGuardado("No es un archivo de guardado de Cripta")
        if version != VERSION_FORMATO:
            raise ErrorGuardado(
                f"Formato de guardado incompatible: el archivo es v{version} "
                f"y este programa usa v{VERSION_FORMATO}")
        (semilla, n_salas, n_comandos, off_indice, off_comandos, k) = self._leer(archivo, FORMATO_FIJO)
        if k < 1:
            raise ErrorGuardado(f"El archivo no se puede leer: K={k} no es un entero positivo")
        id_cripta = self.leer_cadena(archivo)
        version_cripta = self.leer_cadena(archivo)
        version_catalogo = self.leer_cadena(archivo)
        return CabeceraGuardado(id_cripta, version_cripta, version_catalogo,
                                semilla, n_salas, n_comandos,
                                off_indice, off_comandos, k)

    ## guardar

    def guardar(self, ruta, cabecera, contenidos, comandos):
        with open(ruta, "wb") as archivo:
            self._escribir_cabecera(archivo, cabecera)  # marcadores en 0

            entradas = []
            for dto in contenidos:
                if dto is None:
                    continue
                inicio = archivo.tell()
                self.escribir_sala(archivo, dto)
                entradas.append((dto.id_sala, inicio, archivo.tell() - inicio))

            cabecera.off_comandos = archivo.tell()
            for comando in comandos:
                self.escribir_cadena(archivo, comando)

            cabecera.off_indice = archivo.tell()
            for id_sala, offset, largo in entradas:
                archivo.write(struct.pack(FORMATO_INDICE, id_sala, offset, largo))

            cabecera.n_salas = len(entradas)
            cabecera.n_comandos = len(comandos)
            archivo.seek(0)
            self._escribir_cabecera(archivo, cabecera)  # valores reales

    ## leer

    def leer_indice(self, archivo, cabecera):
        archivo.seek(cabecera.off_indice)
        indice = VectorBusqueda()
        for _ in range(cabecera.n_salas):
            id_sala, offset, largo = self._leer(archivo, FORMATO_INDICE)
            indice.agregar(id_sala, (offset, largo))
        indice.preparar()
        return indice

    def leer_sala_de(self, ruta, id_sala):
        with open(ruta, "rb") as archivo:
            cabecera = self.leer_cabecera(archivo)
            indice = self.leer_indice(archivo, cabecera)
            entrada = indice.buscar(id_sala)
            if entrada is None:
                return None
            archivo.seek(entrada[0])
            return self.leer_sala(archivo)

    def validar(self, ruta):
        """Lee la cabecera, el índice, cada sala y los comandos sin guardar nada; devuelve la cabecera.

        Lanza ErrorGuardado si algo falta o no se puede leer. No abre el archivo para escribir."""
        with open(ruta, "rb") as archivo:
            cabecera = self.leer_cabecera(archivo)
            try:
                indice = self.leer_indice(archivo, cabecera)
            except ValueError as error:                   #índice desordenado: el archivo está dañado
                raise ErrorGuardado(f"El índice de salas está dañado: {error}")
            for offset, _ in indice.valores:
                archivo.seek(offset)
                self.leer_sala(archivo)
            archivo.seek(cabecera.off_comandos)
            for _ in range(cabecera.n_comandos):
                self.leer_cadena(archivo)
        return cabecera

    def leer_comandos(self, ruta):
        with open(ruta, "rb") as archivo:
            cabecera = self.leer_cabecera(archivo)
            archivo.seek(cabecera.off_comandos)
            comandos = []
            for _ in range(cabecera.n_comandos):
                comandos.append(self.leer_cadena(archivo))
            return comandos

## guarda los datos
class CabeceraGuardado:
    def __init__(self, id_cripta, version_cripta, version_catalogo, semilla,
                 n_salas=0, n_comandos=0, off_indice=0, off_comandos=0, k=1):
        self.id_cripta = id_cripta
        self.version_cripta = version_cripta
        self.version_catalogo = version_catalogo
        self.semilla = semilla
        self.n_salas = n_salas
        self.n_comandos = n_comandos
        self.off_indice = off_indice
        self.off_comandos = off_comandos
        self.k = k                      #el K de la línea de tiempo con que se jugó (v2, FR-017)