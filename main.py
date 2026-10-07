from EntornoCacho import EntornoCacho
from AgenteCachoIA import AgenteCachoIA
from AgenteCachoHumano import AgenteCachoHumano
from VistaCacho import VistaCacho
from funcion_evaluacion import precalcular


if __name__ == "__main__":
    print("Precalculando tablas de valor esperado (unos segundos)...")
    precalcular()

    entorno = EntornoCacho()
    ia = AgenteCachoIA(nombre="IA", altura=1, evaluacion='mejorada')
    humano = AgenteCachoHumano(nombre="Tú")
    entorno.insertar(ia)
    entorno.insertar(humano)

    VistaCacho(entorno).loop()