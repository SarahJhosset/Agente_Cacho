from AgenteCacho import AgenteCacho, ElEstado, probabilidad_tirada, puntuar
from funcion_evaluacion import evaluar, evaluar_base


class AgenteCachoIA(AgenteCacho):
    """Expectiminimax con memoización, profundidad adaptativa y evaluación configurable.

    Configuración del agente BASE:      evaluacion='base', umbral=20, memo=False, adaptativa=False
    Configuración del agente MEJORADO:  evaluacion='mejorada' (umbral=None por defecto)
    """

    def __init__(self, nombre="IA", altura=1, evaluacion='mejorada', pesos=None,
                 umbral=None, memo=True, adaptativa=True):
        AgenteCacho.__init__(self, nombre=nombre, altura=altura)
        self.evaluacion = evaluacion
        self.pesos = pesos
        self.umbral = umbral
        self.memo = memo
        self.adaptativa = adaptativa
        self._cache = {}

    def funcion_evaluacion(self, estado):
        if self.evaluacion == 'base':
            return evaluar_base(estado.tablero)
        return evaluar(estado.tablero, estado.jugador, self.pesos)

    # ---------------- Expectiminimax ----------------
    def expectiminimax(self, estado, prof):
        t = estado.tablero
        if (self.testTerminal(estado) or prof >= self.max_profundidad
                or not t['dados_reales']):                  # frontera de turno: se evalúa
            return self.funcion_evaluacion(estado)

        clave = None
        if self.memo:
            clave = (t['dados'], t['tiradas_restantes'], t['puntajes'][0], t['puntajes'][1],
                     frozenset(t['usadas'][0]), frozenset(t['usadas'][1]),
                     estado.jugador, self.max_profundidad - prof)
            if clave in self._cache:
                return self._cache[clave]

        valores = [self._valor_accion(estado, a, prof) for a in self.jugadas(estado)]
        if not valores:
            v = self.funcion_evaluacion(estado)
        elif estado.jugador == self.yo:
            v = max(valores)                                # nodo MAX
        else:
            v = min(valores)                                # nodo MIN

        if clave is not None:
            self._cache[clave] = v
        return v

    def _valor_accion(self, estado, accion, prof):
        if accion[0] == 'anotar':                           # nodo determinista
            return self.expectiminimax(self.getResultado(estado, accion), prof + 1)
        t = estado.tablero                                  # nodo de AZAR
        v = 0.0
        for nuevos, p in probabilidad_tirada(t['dados'], accion[1]).items():
            h = self._copiar_tablero(t)
            h['dados'] = nuevos
            h['tiradas_restantes'] -= 1
            v += p * self.expectiminimax(ElEstado(estado.jugador, 0, h, None), prof + 1)
        return v

    # ---------------- Selección de acción ----------------
    def elegir_accion(self, estado):
        t = estado.tablero
        self.yo = estado.jugador
        self._cache = {}
        r = t['tiradas_restantes']
        # profundidad adaptativa: mirada completa hasta el final del turno si queda <= 1 relance
        self.max_profundidad = self.altura + (1 if self.adaptativa and r <= 1 else 0)
        acciones = self.jugadas(estado)
        anotar = [a for a in acciones if a[0] == 'anotar']

        # política heredada del código base (solo si umbral is not None)
        if self.umbral is not None and r == 0:
            return max(anotar, key=lambda a: puntuar(a[1], t['dados']))

        mejor, mejor_v = None, float('-inf')
        for a in acciones:
            v = self._valor_accion(estado, a, 0)
            if v > mejor_v:
                mejor, mejor_v = a, v

        if self.umbral is not None and mejor[0] == 'tirar' and anotar:
            ma = max(anotar, key=lambda a: puntuar(a[1], t['dados']))
            if puntuar(ma[1], t['dados']) >= self.umbral:
                mejor = ma
        return mejor

    def programa(self):
        self.set_acciones([])
        accion = self.elegir_accion(self.estado)
        if accion is not None:
            self.set_acciones(accion)