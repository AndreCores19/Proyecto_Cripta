from pathlib import Path

VERSION_FORMATO = 1

class BitacoraPartida:
    def __init__(self, carpeta):
        self.carpeta = Path(carpeta)
        self.carpeta.mkdir(parents=True, exist_ok=True)
        self.archivo = None

    def abrir(self, id_cripta, version_cripta, version_catalogo, semilla):
        ruta = self.carpeta / f"partida_{id_cripta}_{semilla}.log"
        self.archivo = open(ruta, "w", encoding="utf-8")
        self.archivo.write(f"CRIPTA-LOG {VERSION_FORMATO}\n")
        self.archivo.write(f"cripta: {id_cripta}\n")
        self.archivo.write(f"version_cripta: {version_cripta}\n")
        self.archivo.write(f"version_catalogo: {version_catalogo}\n")
        self.archivo.write(f"semilla: {semilla}\n")
        self.archivo.write("---\n")
        self.archivo.flush()

    def cerrar(self):
        if self.archivo is not None:
            self.archivo.close()
            self.archivo = None

    def anotar(self, comando):
        if self.archivo is not None:
            self.archivo.write(f"{comando}\n")
            self.archivo.flush()

    def comentar(self, texto):
        #línea de comentario: el lector la omite y nunca llega a la lista de comandos
        if self.archivo is not None:
            self.archivo.write(f"# {texto}\n")
            self.archivo.flush()
