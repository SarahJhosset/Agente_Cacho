import contextlib
import csv
import io
import random
import time

from EntornoCacho import EntornoCacho
from AgenteCachoIA import AgenteCachoIA
from funcion_evaluacion import precalcular

CFG_BASE = dict(evaluacion='base', umbral=20, memo=False, adaptativa=False)
CFG_MEJORADA = dict(evaluacion='mejorada', umbral=None, memo=True, adaptativa=True)


def jugar_partida(ag0, ag1, semilla):
    """ag0 juega como jugador 0 (empieza), ag1 como jugador 1."""
    random.seed(semilla)
    ags = (ag0, ag1)
    tiempos, evals = [[], []], [[], []]
    with contextlib.redirect_stdout(io.StringIO()):          # silencia los print del entorno
        env = EntornoCacho()
        env.insertar(ag0)
        env.insertar(ag1)
        while not env.es_fin():
            turno = env.juegoActual.jugador
            ag = ags[turno]
            n0, t0 = ag.n_evals, time.perf_counter()
            accion = ag.elegir_accion(env.juegoActual)
            tiempos[turno].append(time.perf_counter() - t0)
            evals[turno].append(ag.n_evals - n0)
            env._aplicar_accion(accion)
    p = env.juegoActual.tablero['puntajes']
    media = lambda xs: sum(xs) / len(xs) if xs else 0.0
    return p[0], p[1], [media(tiempos[0]), media(tiempos[1])], [media(evals[0]), media(evals[1])]


def torneo(n_partidas=100, archivo='resultados_cacho.csv'):
    precalcular()
    filas = []
    for i in range(n_partidas):
        base = AgenteCachoIA('Base', **CFG_BASE)
        mej = AgenteCachoIA('Mejorada', **CFG_MEJORADA)
        base_primero = (i % 2 == 0)
        ag0, ag1 = (base, mej) if base_primero else (mej, base)
        p0, p1, t, e = jugar_partida(ag0, ag1, semilla=i)
        ib, im = (0, 1) if base_primero else (1, 0)          # índice de cada agente
        pb, pm = (p0, p1) if base_primero else (p1, p0)
        filas.append({
            'agente_a': 'Base', 'agente_b': 'Mejorada',
            'puntaje_a': pb, 'puntaje_b': pm,
            'version_funcion': 'base_vs_mejorada',
            'tiempo_decision_promedio': round((t[0] + t[1]) / 2, 5),
            'tiempo_a': round(t[ib], 5), 'tiempo_b': round(t[im], 5),
            'evals_a': round(e[ib], 1), 'evals_b': round(e[im], 1),
            'semilla': i, 'a_juega_primero': base_primero,
        })
        print(f"Partida {i + 1}/{n_partidas}: Base {pb} - Mejorada {pm}")

    with open(archivo, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)

    gb = sum(r['puntaje_a'] > r['puntaje_b'] for r in filas)
    gm = sum(r['puntaje_b'] > r['puntaje_a'] for r in filas)
    print(f"\nBase gana {gb} | Mejorada gana {gm} | Empates {n_partidas - gb - gm}")
    print(f"Puntaje medio: Base {sum(r['puntaje_a'] for r in filas) / n_partidas:.1f}"
          f" | Mejorada {sum(r['puntaje_b'] for r in filas) / n_partidas:.1f}")


if __name__ == "__main__":
    torneo(n_partidas=100)