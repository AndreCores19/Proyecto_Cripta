
def direccionar(tecla):
    tecla = tecla.lower()
    if tecla == "w":
        return "N"
    elif tecla == "s":
        return "S"
    elif tecla == "a":
        return "O"
    elif tecla == "d":
        return "E"

class Controlador:
    def __init__(self, servicio, vista, bitacora, persistencia):
        self.servicio = servicio
        self.vista = vista
        self.bitacora = bitacora
        self.activo = True
        self.comandos = []
        self.persistencia = persistencia
        self.ruta_carga = None

    def jugar(self):
        partida = self.servicio.partida
        while self.activo and not partida.terminada:
            self.vista.mostrar_estado(self.servicio.estado_vista())
            texto = self.vista.pedir_comando()
            self.ejecutar(texto)
        if self.ruta_carga is None:
            self.vista.mostrar_final(partida)
            if (partida.victoria or partida.terminada) and self.persistencia is not None:
                puntajes = self.persistencia.registrar_puntaje(partida)
                self.vista.mostrar_puntajes(puntajes)

    def _enemigos_en_sala(self):
        partida = self.servicio.partida
        resultado = []
        for enemigo in partida.enemigos:
            if enemigo.sala is partida.jugador.sala and enemigo.esta_vivo():
                resultado.append(enemigo)
        return resultado

    def _avisar_si_falla(self, resultado, mensaje):
        if not resultado:
            self.vista.mostrar_mensaje(mensaje)

    def ejecutar(self, texto):
        palabras = texto.lower().split()
        if not palabras:
            return
        comando = palabras[0]
        direccion = direccionar(comando)

        if comando not in ("salir", "guardar", "cargar"):  # ← cambia esta condición
            self.comandos.append(" ".join(palabras))  # ← nuevo: siempre
            if self.bitacora is not None:
                self.bitacora.anotar(" ".join(palabras))

        if comando == "salir":
            self.activo = False
        elif comando == "guardar":  # ← nuevo
            self._cmd_guardar(palabras)
        elif comando == "cargar":
            self._cmd_cargar(palabras)
        elif direccion is not None:
            self._avisar_si_falla(self.servicio.mover(direccion),
                                  "No puedes moverte en esa dirección.")
        elif comando == "esperar":
            self.servicio.esperar()
        elif comando == "atacar":
            self._cmd_atacar(palabras)
        elif comando == "recoger":
            self._cmd_recoger(palabras)
        elif comando == "abrir":
            self._cmd_abrir(palabras)
        elif comando in ("equipar", "usar", "soltar", "retroceder"):
            self._cmd_simple(comando)
        elif comando in ("inv", "sig", "ant"):
            self._cmd_inventario(palabras)
        else:
            self.vista.mostrar_mensaje("Comando no reconocido.")

    def _cmd_recoger(self, palabras):
        objetos = self.servicio.partida.jugador.sala.objetos
        if len(palabras) > 1:
            try:
                id_instancia = int(palabras[1])
            except ValueError:
                self.vista.mostrar_mensaje("El id del objeto debe ser un número.")
                return
        elif len(objetos) == 1:
            id_instancia = objetos[0].id_instancia
        else:
            self.vista.mostrar_mensaje("Indica qué recoger: recoger <id>.")
            return
        self._avisar_si_falla(self.servicio.recoger_objeto(id_instancia),"No se pudo recoger (¿inventario lleno o el id no existe?).")

    def _cmd_abrir(self, palabras):
        if len(palabras) < 2 or direccionar(palabras[1]) is None:
            self.vista.mostrar_mensaje("Indica la dirección: abrir w/a/s/d.")
        else:
            self._avisar_si_falla(self.servicio.abrir_puerta(direccionar(palabras[1])),"No se pudo abrir (¿no hay puerta cerrada o falta la llave?).")

    def _cmd_inventario(self, palabras):
        comando = palabras[0]
        if comando == "sig":
            self.servicio.siguiente_objeto()
        elif comando == "ant":
            self.servicio.anterior_objeto()
        elif len(palabras) > 1:
            criterio = palabras[1]
            if criterio not in ("peso", "valor", "nombre"):
                self.vista.mostrar_mensaje("Usa: inv peso|valor|nombre")
                return
            objetos = self.servicio.vista_ordenada(criterio)
            self.vista.mostrar_inventario_ordenado(objetos, criterio)
            return
        self.vista.mostrar_inventario(self.servicio.partida)

    def _cmd_atacar(self, palabras):
        objetivo = self._elegir_enemigo(palabras)
        if objetivo is not None:
            self._avisar_si_falla(self.servicio.atacar(objetivo), "No se pudo atacar.")

    def _elegir_enemigo(self, palabras):
        enemigos = self._enemigos_en_sala()
        if not enemigos:
            self.vista.mostrar_mensaje("No hay enemigos aquí.")
            return None
        if len(palabras) > 1:
            for enemigo in enemigos:
                if str(enemigo.id_enemigo).lower() == palabras[1]:
                    return enemigo
            self.vista.mostrar_mensaje("Ese enemigo no está en la sala.")
            return None
        if len(enemigos) == 1:
            return enemigos[0]
        self.vista.mostrar_mensaje("Hay varios enemigos: usa atacar <id>.")
        return None

    def _cmd_simple(self, comando):
        if comando == "equipar":
            self._avisar_si_falla(self.servicio.equipar_objeto(), "Ese objeto no se puede equipar.")
        elif comando == "usar":
            self._avisar_si_falla(self.servicio.usar_objeto(), "No se puede usar ese objeto.")
        elif comando == "soltar":
            self._avisar_si_falla(self.servicio.soltar_objeto(), "No tienes nada que soltar.")
        else:
            self._avisar_si_falla(self.servicio.retroceder(), "No hay nada que retroceder.")

    def _cmd_guardar(self, palabras):
        if self.persistencia is None:
            return
        nombre = palabras[1] if len(palabras) > 1 else "partida"
        ruta = self.persistencia.guardar_partida(
            self.servicio.partida, self.comandos, nombre)
        self.vista.mostrar_mensaje(f"Partida guardada en {ruta}")

    def _cmd_cargar(self, palabras):
        nombre = palabras[1] if len(palabras) > 1 else "partida"
        ruta = self.persistencia.ruta_guardado(nombre)
        if not ruta.exists():
            self.vista.mostrar_mensaje("No existe esa partida.")
            return
        error = self.persistencia.validar_guardado(ruta)
        if error is not None:
            self.vista.mostrar_mensaje(error)
            return
        self.ruta_carga = ruta
        self.activo = False
