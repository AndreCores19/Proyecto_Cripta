from model.jugador_logica import Jugador
from model.objeto_logica import Objeto
from model.enemigo_logica import Enemigo
from model.partida_logica import Partida
from model.trampa_logica import Trampa

class FabricaModelo:
    def __init__(self, repo_cripta, repo_catalogo):
        self.repo_cripta = repo_cripta
        self.repo_catalogo = repo_catalogo
        self.pobladas = None
        self.siguiente_instancia = 1

    def iniciar(self):
        self.pobladas = [False] * self.repo_cripta.salas.tamano()
        self.siguiente_instancia = 1

    def _ficha(self, id_ficha):
        ficha = self.repo_catalogo.cache.obtener(id_ficha)
        if ficha is None:
            self.repo_catalogo.resolver([id_ficha], con_sueltos=False)
            ficha = self.repo_catalogo.cache.obtener(id_ficha)
        if ficha is None:
            raise ValueError(f"No se encontró la ficha {id_ficha} en la caché")
        return ficha

    def crear_objeto(self, id_instancia, ficha):
        id_catalogo = ficha.id_ficha
        nombre = ficha.nombre
        clase = ficha.clase
        peso = ficha.peso
        valor = ficha.valor

        if ficha.clase == "arma":
            return Objeto(id_instancia, id_catalogo, nombre, clase, peso, valor, ataque_bonus = ficha.ataque_bonus)
        elif ficha.clase == "armadura":
            return Objeto(id_instancia, id_catalogo, nombre, clase, peso, valor, defensa_bonus = ficha.defensa_bonus)
        elif ficha.clase == "pocion":
            return Objeto(id_instancia, id_catalogo, nombre, clase, peso, valor, cura = ficha.cura, duracion = ficha.duracion, modificador_velocidad = ficha.modificador_velocidad)
        elif ficha.clase == "llave":
            return Objeto(id_instancia, id_catalogo, nombre, clase, peso, valor, abre = ficha.abre)
        elif ficha.clase == "antorcha":
            return Objeto(id_instancia, id_catalogo, nombre, clase, peso, valor, duracion = ficha.duracion)
        elif ficha.clase in ("antidoto", "pergamino_retroceso"):
            return Objeto(id_instancia, id_catalogo, nombre, clase, peso, valor)
        else:
            raise ValueError(f"Clase de objeto desconocida: {ficha.clase}")

    def crear_enemigo(self, instancia, ficha, sala):
        if instancia.vida is None:
            vida = ficha.vida_max
        else:
            vida = instancia.vida
        enemigo = Enemigo(
            id_enemigo=instancia.instancia,
            tipo=instancia.tipo,
            nombre=ficha.nombre,
            vida=vida,
            vida_max=ficha.vida_max,
            ataque=ficha.ataque,
            defensa=ficha.defensa,
            velocidad=ficha.velocidad,
            comportamiento=ficha.comportamiento,
            sala=sala,
            suelta=ficha.suelta,
            rango=getattr(ficha, "rango", 0) or 0
        )
        enemigo.regeneracion = getattr(ficha, "regeneracion", 0) or 0  # solo si la ficha lo trae
        return enemigo


    def objeto_desde_id(self, id_ficha):
        #Crea un objeto nuevo a partir de un id de catálogo.
        #Lo usa la partida cuando un enemigo muere y suelta objetos
        if not self.repo_catalogo.cache.contiene(id_ficha):
            self.repo_catalogo.resolver([id_ficha], con_sueltos=False)
        objeto = self.crear_objeto(self.siguiente_instancia, self._ficha(id_ficha))
        self.siguiente_instancia += 1
        return objeto

    def crear_trampa(self, instancia, ficha):
        return Trampa(
            id_instancia=instancia.instancia,
            nombre=ficha.nombre,
            dano=ficha.dano,
            rearme=ficha.rearme,
            id_catalogo=instancia.tipo,
            veneno=getattr(ficha, "veneno", 0) or 0
        )

    def poblar_sala(self, sala):
        pos = self.repo_cripta.salas.posicion(sala.id)
        if self.pobladas[pos]:
            return

        if self.repo_cripta.contenidos[pos] is None:
            nuevos = self.repo_cripta.precargar(sala.id)
            self.repo_catalogo.resolver(self.repo_catalogo.ids_del_contenido(nuevos))
        contenido = self.repo_cripta.contenidos[pos]
        if contenido is None:
            raise ValueError(f"No se pudo cargar el contenido de la sala {sala.id}")

        ids = self.repo_catalogo.ids_del_contenido([contenido])
        self.repo_catalogo.resolver(ids)

        for instancia in contenido.enemigos:
            ficha = self._ficha(instancia.tipo)
            sala.inactivos.append(self.crear_enemigo(instancia, ficha, sala))

        for id_ficha in contenido.objetos:
            ficha = self._ficha(id_ficha)
            sala.objetos.append(self.crear_objeto(self.siguiente_instancia, ficha))
            self.siguiente_instancia += 1

        for instancia in contenido.trampas:
            ficha = self._ficha(instancia.tipo)
            sala.trampas.append(self.crear_trampa(instancia, ficha))

        self.pobladas[pos] = True

    def crear_jugador(self, sala_inicial):
        est = self.repo_cripta.datos.jugador
        return Jugador(vida_max=est.vida_max,
                ataque=est.ataque,
                defensa=est.defensa,
                velocidad=est.velocidad,
                sala=sala_inicial,
                inventario_max=self.repo_cripta.datos.inventario_max)

    def nueva_partida(self, semilla):
        sala_inicial = self.repo_cripta.salas.buscar(self.repo_cripta.datos.sala_inicial)
        sala_salida = self.repo_cripta.salas.buscar(self.repo_cripta.datos.sala_salida)
        self.poblar_sala(sala_inicial)
        jugador = self.crear_jugador(sala_inicial)
        partida = Partida(jugador, semilla, sala_salida)
        partida.creador_objetos = self.objeto_desde_id
        return partida

    def marcar_en_uso(self, ids):
        self.repo_catalogo.marcar_en_uso(ids)

