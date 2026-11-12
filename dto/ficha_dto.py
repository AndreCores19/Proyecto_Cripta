class FichaDTO:
    def __init__(self, id_ficha, nombre, clase):
        self.id_ficha = id_ficha
        self.nombre = nombre
        self.clase = clase


class FichaEnemigoDTO(FichaDTO):
    def __init__(self, id_ficha, nombre, clase, vida_max, ataque, defensa, velocidad, comportamiento, suelta, regeneracion=0, rango=None):
        super().__init__(id_ficha, nombre, clase)
        self.vida_max = vida_max
        self.ataque = ataque
        self.defensa = defensa
        self.velocidad = velocidad
        self.comportamiento = comportamiento
        self.suelta = list(suelta) if suelta is not None else []
        self.regeneracion = regeneracion or 0  #si la ficha no lo trae, no se regenera
        self.rango = rango if rango is not None else 0  #solo importa a los cazadores; sin chequeo de tipo ni rango

    @classmethod
    def desde_json(cls, datos):
        return cls(
            id_ficha=datos['id'],
            nombre=datos['nombre'],
            clase=datos['clase'],
            vida_max=datos['vida_max'],
            ataque=datos['ataque'],
            defensa=datos['defensa'],
            velocidad=datos['velocidad'],
            comportamiento=datos['comportamiento'],
            suelta=datos.get('suelta', []),
            regeneracion=datos.get('regeneracion', 0),
            rango=datos.get('rango')
        )

class FichaObjetoDTO(FichaDTO):
    def __init__(self, id_ficha, nombre, clase, peso, valor):
        super().__init__(id_ficha, nombre, clase)
        self.peso = peso
        self.valor = valor

class FichaArmaDTO(FichaObjetoDTO):
    def __init__(self, id_ficha, nombre, clase, peso, valor, ataque_bonus):
        super().__init__(id_ficha, nombre, clase, peso, valor)
        self.ataque_bonus = ataque_bonus

    @classmethod
    def desde_json(cls, datos):
        return cls(
            id_ficha=datos['id'],
            nombre=datos['nombre'],
            clase=datos['clase'],
            peso=datos['peso'],
            valor=datos['valor'],
            ataque_bonus=datos['ataque_bonus']
        )

class FichaArmaduraDTO(FichaObjetoDTO):
    def __init__(self, id_ficha, nombre, clase, peso, valor, defensa_bonus):
        super().__init__(id_ficha, nombre, clase, peso, valor)
        self.defensa_bonus = defensa_bonus

    @classmethod
    def desde_json(cls, datos):
        return cls(
            id_ficha=datos['id'],
            nombre=datos['nombre'],
            clase=datos['clase'],
            peso=datos['peso'],
            valor=datos['valor'],
            defensa_bonus=datos['defensa_bonus']
        )

class FichaPocionDTO(FichaObjetoDTO):
    def __init__(self, id_ficha, nombre, clase, peso, valor, cura, duracion, modificador_velocidad):
        super().__init__(id_ficha, nombre, clase, peso, valor)
        self.cura = cura
        self.duracion = duracion
        self.modificador_velocidad = modificador_velocidad

    @classmethod
    def desde_json(cls, datos):
        return cls(
            id_ficha=datos['id'],
            nombre=datos['nombre'],
            clase=datos['clase'],
            peso=datos['peso'],
            valor=datos['valor'],
            cura=datos.get('cura'),
            duracion=datos.get('duracion'),
            modificador_velocidad=datos.get('modificador_velocidad')
        )

class FichaAntidotoDTO(FichaObjetoDTO):
    @classmethod
    def desde_json(cls, datos):
        return cls(
            id_ficha=datos['id'],
            nombre=datos['nombre'],
            clase=datos['clase'],
            peso=datos['peso'],
            valor=datos['valor']
        )

class FichaLlaveDTO(FichaObjetoDTO):
    def __init__(self, id_ficha, nombre, clase, peso, valor, abre):
        super().__init__(id_ficha, nombre, clase, peso, valor)
        self.abre = abre

    @classmethod
    def desde_json(cls, datos):
        return cls(
            id_ficha=datos['id'],
            nombre=datos['nombre'],
            clase=datos['clase'],
            peso=datos['peso'],
            valor=datos['valor'],
            abre=datos.get('abre')
        )

class FichaAntorchaDTO(FichaObjetoDTO):
    def __init__(self, id_ficha, nombre, clase, peso, valor, duracion):
        super().__init__(id_ficha, nombre, clase, peso, valor)
        self.duracion = duracion

    @classmethod
    def desde_json(cls, datos):
        return cls(
            id_ficha=datos['id'],
            nombre=datos['nombre'],
            clase=datos['clase'],
            peso=datos['peso'],
            valor=datos['valor'],
            duracion=datos['duracion']
        )

class FichaPergaminoRetrocesoDTO(FichaObjetoDTO):
    @classmethod
    def desde_json(cls, datos):
        return cls(
            id_ficha=datos['id'],
            nombre=datos['nombre'],
            clase=datos['clase'],
            peso=datos['peso'],
            valor=datos['valor'],
        )

class FichaTrampaDTO(FichaDTO):
    def __init__(self, id_ficha, nombre, clase, dano, rearme, veneno=0):
        super().__init__(id_ficha, nombre, clase)
        self.dano = dano
        self.rearme = rearme
        self.veneno = veneno or 0 #si la ficha no lo trae, no envenena

    @classmethod
    def desde_json(cls, datos):
        return cls(
            id_ficha=datos['id'],
            nombre=datos['nombre'],
            clase=datos['clase'],
            dano=datos['daño'],
            rearme=datos.get('rearme'),
            veneno=datos.get('veneno', 0)
        )


##funcion para clasificar clase de las fichas:

def ficha_desde_json(datos):
    clase = datos['clase']

    if clase == 'enemigo':
        return FichaEnemigoDTO.desde_json(datos)
    elif clase == 'arma':
        return FichaArmaDTO.desde_json(datos)
    elif clase == 'armadura':
        return FichaArmaduraDTO.desde_json(datos)
    elif clase == 'pocion':
        return FichaPocionDTO.desde_json(datos)
    elif clase == 'antidoto':
        return FichaAntidotoDTO.desde_json(datos)
    elif clase == 'llave':
        return FichaLlaveDTO.desde_json(datos)
    elif clase == 'antorcha':
        return FichaAntorchaDTO.desde_json(datos)
    elif clase == 'pergamino_retroceso':
        return FichaPergaminoRetrocesoDTO.desde_json(datos)
    elif clase == 'trampa':
        return FichaTrampaDTO.desde_json(datos)
    else:
        raise ValueError(f"Clase desconocida: {clase} (id {datos.get('id')})")


