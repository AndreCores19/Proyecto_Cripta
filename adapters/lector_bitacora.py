from pathlib import Path
from adapters.bitacora_partida import VERSION_FORMATO

class ErrorBitacora(Exception):
    """Error al leer una bitácora de partida."""

class LectorBitacora:
    def __init__(self, ruta):
        self.ruta = Path(ruta)
        # los cuatro datos todavía no se conocen:
        self.cripta = None
        self.version_cripta = None
        self.version_catalogo = None
        self.semilla = None
        self.comandos = []

    def leer(self):
        with open(self.ruta, "r", encoding="utf-8") as archivo:
            lineas = archivo.readlines()

        if not lineas or lineas[0].strip() != f"CRIPTA-LOG {VERSION_FORMATO}":
            raise ErrorBitacora("Archivo de bitácora inválido o de un formato incompatible")

        self.comandos = []
        en_cuerpo = False
        for linea in lineas[1:]:
            linea = linea.strip()
            if not linea:
                continue
            if en_cuerpo:
                if linea.startswith("#"):
                    continue                 #comentario (p. ej. «# ir a 7»): no es un comando
                self.comandos.append(linea)
            elif linea == "---":
                en_cuerpo = True
            else:
                clave, _, valor = linea.partition(":")
                valor = valor.strip()
                if clave == "cripta":
                    self.cripta = valor
                elif clave == "version_cripta":
                    self.version_cripta = valor
                elif clave == "version_catalogo":
                    self.version_catalogo = valor
                elif clave == "semilla":
                    self.semilla = int(valor)

        if (not en_cuerpo or self.cripta is None or self.version_cripta is None
                or self.version_catalogo is None or self.semilla is None):
            raise ErrorBitacora("El encabezado de la bitácora está incompleto")

