"""Funciones de evaluación del Cacho: base (ec. 1 del PDF) y mejorada (ec. 2)."""
from collections import Counter
from functools import lru_cache
from itertools import combinations, combinations_with_replacement
from math import factorial, sqrt, tanh

TIRADAS_POR_TURNO = 3        # tirada inicial + 2 relances
ANOTACIONES_TOTALES = 20     # 10 categorías x 2 jugadores
CATEGORIAS = ['1', '2', '3', '4', '5', '6', 'escalera', 'full', 'poker', 'grande']
ESTADOS = list(combinations_with_replacement(range(1, 7), 5))


def puntuar(cat, dados):
    c = Counter(dados)
    v = sorted(c.values(), reverse=True)
    if cat in '123456':
        return dados.count(int(cat)) * int(cat)
    if cat == 'escalera':
        return 25 if set(dados) in ({1, 2, 3, 4, 5}, {2, 3, 4, 5, 6}) else 0
    if cat == 'full':
        return 30 if v == [3, 2] else 0
    if cat == 'poker':
        return 40 if v[0] >= 4 else 0
    if cat == 'grande':
        return 50 if v[0] == 5 else 0
    return 0


@lru_cache(None)
def tiradas(n):
    """((resultado ordenado, probabilidad), ...) al tirar n dados."""
    out = []
    for combo in combinations_with_replacement(range(1, 7), n):
        f = factorial(n)
        for k in Counter(combo).values():
            f //= factorial(k)
        out.append((combo, f / 6 ** n))
    return tuple(out)


@lru_cache(None)
def reservas(dados):
    """Multiconjuntos distintos de dados que se pueden reservar (0 a 5 dados)."""
    return tuple({tuple(sorted(s)) for k in range(6) for s in combinations(dados, k)})


@lru_cache(None)
def tabla_valor(cat, r):
    """{dados: (media, E[X^2])} de la categoría con r relances restantes y política óptima."""
    if r == 0:
        return {d: (puntuar(cat, d), puntuar(cat, d) ** 2) for d in ESTADOS}
    prev = tabla_valor(cat, r - 1)
    tabla = {}
    for d in ESTADOS:
        mejor = None
        for k in reservas(d):
            m = s = 0.0
            for combo, p in tiradas(5 - len(k)):
                mu, m2 = prev[tuple(sorted(k + combo))]
                m += p * mu
                s += p * m2
            if mejor is None or m > mejor[0]:
                mejor = (m, s)
        tabla[d] = mejor
    return tabla


@lru_cache(None)
def potencial(cat):
    """(media, desv. estándar) de la categoría al empezar un turno (tirada inicial + 2 relances)."""
    t = tabla_valor(cat, 2)
    m = sum(p * t[c][0] for c, p in tiradas(5))
    m2 = sum(p * t[c][1] for c, p in tiradas(5))
    return m, sqrt(max(m2 - m * m, 0.0))


def precalcular():
    """Llamar una vez al arrancar: construye las tablas (tarda unos segundos)."""
    for c in CATEGORIAS:
        potencial(c)


# ---------------- Función BASE (ec. 1 del PDF) ----------------
@lru_cache(None)
def _ve_base(cat):
    return sum(puntuar(cat, e) for e in ESTADOS) / len(ESTADOS)


def evaluar_base(tablero, alpha=0.6):
    p, usadas = tablero['puntajes'], tablero['usadas']
    fut = [sum(_ve_base(c) for c in CATEGORIAS if c not in usadas[j]) for j in (0, 1)]
    return (p[0] + alpha * fut[0]) - (p[1] + alpha * fut[1])


# ---------------- Función MEJORADA (ec. 2 del PDF) ----------------
# pesos por etapa: (w_puntaje, w_futuro, w_turno, w_varianza)
PESOS = {'inicio': (1.0, 1.0, 1.0, 0.5),
         'medio':  (1.0, 1.0, 1.0, 0.5),
         'final':  (1.0, 1.0, 1.0, 0.5)}


def etapa(categorias_usadas):
    return 'inicio' if categorias_usadas < 3 else ('medio' if categorias_usadas < 7 else 'final')


def evaluar(tablero, jugador_turno, pesos=None):
    """E(s) = sum w_i f_i(s), siempre desde la perspectiva del jugador 0."""
    p, usadas = tablero['puntajes'], tablero['usadas']
    w1, w2, w3, w4 = (pesos or PESOS)[etapa(len(usadas[0]))]
    rest = [[c for c in CATEGORIAS if c not in usadas[j]] for j in (0, 1)]

    f1 = p[0] - p[1]
    fut = [sum(potencial(c)[0] for c in rest[j]) for j in (0, 1)]
    f2 = fut[0] - fut[1]

    f3 = 0.0   # ganancia del turno en curso (solo si hay dados reales)
    if tablero.get('dados_reales', True) and rest[jugador_turno]:
        r, d = tablero['tiradas_restantes'], tuple(tablero['dados'])
        g = max(tabla_valor(c, r)[d][0] - potencial(c)[0] for c in rest[jugador_turno])
        f3 = g if jugador_turno == 0 else -g

    sd = [sum(potencial(c)[1] for c in rest[j]) for j in (0, 1)]
    f4 = -(sd[0] - sd[1]) * tanh(f1 / 50)
    return w1 * f1 + w2 * f2 + w3 * f3 + w4 * f4