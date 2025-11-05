"""
Sistema de Validacion Integral del Modelo de Simulacion

Este modulo implementa un conjunto completo de pruebas de validacion
para verificar la correctitud tecnica y consistencia estadistica del
modelo de simulacion de eventos discretos.

Categorias de validacion:
1. Validacion fisica (conservacion de masa, no-negatividad)
2. Validacion de casos extremos (limites teoricos)
3. Validacion estadistica (distribuciones, independencia)
4. Validacion de sensibilidad (monotonicidad, robustez)
5. Validacion analitica (comparacion con modelos teoricos)
6. Validacion empirica (calibracion con datos reales)

Autor: Carlos Subiabre
Institucion: Universidad de Chile / Universidad Austral de Chile
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from scipy import stats
from scipy.stats import chisquare, kstest, poisson, norm
import warnings

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from modelo import ConfiguracionSimulacion, ejecutarSimulacion


@dataclass
class ResultadoValidacion:
    """Resultado de una prueba de validacion individual."""
    nombrePrueba: str
    exitosa: bool
    valorObservado: float
    valorEsperado: float
    tolerancia: float
    detalles: str
    criticidad: str  # CRITICA, ALTA, MEDIA, BAJA


class SistemaValidacion:
    """
    Sistema centralizado de validacion del modelo de simulacion.

    Implementa conjunto exhaustivo de pruebas para verificar:
    - Correctitud matematica
    - Consistencia estadistica
    - Calibracion empirica
    - Robustez numerica
    """

    def __init__(self, verboso: bool = True):
        self.verboso = verboso
        self.resultados: List[ResultadoValidacion] = []
        self.configuracionBase = ConfiguracionSimulacion()

    def ejecutarTodasLasValidaciones(self) -> None:
        """Ejecuta suite completa de validaciones."""
        self.imprimirEncabezado("SISTEMA DE VALIDACION INTEGRAL DEL MODELO")

        # Categoria 1: Validaciones Fisicas
        self.imprimirSeccion("1. VALIDACIONES FISICAS")
        self.validarConservacionMasa()
        self.validarNoNegatividadInventario()

        # Categoria 2: Casos Extremos
        self.imprimirSeccion("2. VALIDACION DE CASOS EXTREMOS")
        self.validarCapacidadInfinita()
        self.validarInventarioInicialCero()
        self.validarDisrupcionPermanente()
        self.validarSinDisrupciones()

        # Categoria 3: Validaciones Estadisticas
        self.imprimirSeccion("3. VALIDACIONES ESTADISTICAS")
        self.validarDistribucionPoisson()
        self.validarIndependenciaReplicas()
        self.validarNormalidadDemanda()

        # Categoria 4: Sensibilidad y Monotonicidad
        self.imprimirSeccion("4. ANALISIS DE SENSIBILIDAD")
        self.validarMonotonicidadCapacidad()
        self.validarMonotonicidadDisrupciones()

        # Categoria 5: Comparacion Analitica
        self.imprimirSeccion("5. COMPARACION CON MODELO ANALITICO")
        self.validarAutonomiaTeoricoVsSimulado()
        self.validarFrecuenciaDisrupcionesEsperada()

        # Categoria 6: Calibracion Empirica
        self.imprimirSeccion("6. CALIBRACION CON DATOS REALES")
        self.validarAutonomiaInformeCne()
        self.validarDemandaPromedioAnual()

        # Reporte Final
        self.generarReporteFinal()

    # ========================================================================
    # CATEGORIA 1: VALIDACIONES FISICAS
    # ========================================================================

    def validarConservacionMasa(self) -> None:
        """
        Verifica principio de conservacion de masa.

        Invariante: Inv_inicial + Total_recibido = Inv_final + Total_despachado

        Tolerancia: 0.01 TM (error numerico de redondeo)
        """
        self.imprimirPrueba("Conservacion de masa (balance de materia)")

        config = ConfiguracionSimulacion(semillaAleatoria=12345)
        resultado = ejecutarSimulacion(config)

        inventarioInicial = resultado['inventario_inicial_tm']
        inventarioFinal = resultado['inventario_final_tm']
        totalRecibido = resultado['total_recibido_tm']
        totalDespachado = resultado['total_despachado_tm']

        # Balance: (Inicial + Entradas) - (Final + Salidas) = 0
        balance = (inventarioInicial + totalRecibido) - (inventarioFinal + totalDespachado)
        balanceAbsoluto = abs(balance)

        tolerancia = 0.01
        exitosa = balanceAbsoluto < tolerancia

        detalles = (f"Inv_inicial={inventarioInicial:.2f}, Recibido={totalRecibido:.2f}, "
                   f"Inv_final={inventarioFinal:.2f}, Despachado={totalDespachado:.2f}, "
                   f"Balance={balance:.4f} TM")

        self.registrarResultado(ResultadoValidacion(
            nombrePrueba="Conservacion de masa",
            exitosa=exitosa,
            valorObservado=balanceAbsoluto,
            valorEsperado=0.0,
            tolerancia=tolerancia,
            detalles=detalles,
            criticidad="CRITICA"
        ))

    def validarNoNegatividadInventario(self) -> None:
        """
        Verifica que inventario nunca sea negativo.

        Restriccion fisica: Inv(t) >= 0 para todo t
        """
        self.imprimirPrueba("No-negatividad del inventario")

        config = ConfiguracionSimulacion(semillaAleatoria=98765)

        # Ejecutar con logging para obtener metricas diarias
        import logging
        logging.basicConfig(level=logging.WARNING)

        from modelo import SimulacionGlpAysen
        sim = SimulacionGlpAysen(config)
        sim.run()

        inventarios = [m.inventarioTm for m in sim.metricasDiarias]
        inventarioMinimo = min(inventarios)

        exitosa = inventarioMinimo >= 0

        detalles = f"Inventario minimo observado: {inventarioMinimo:.2f} TM"

        self.registrarResultado(ResultadoValidacion(
            nombrePrueba="No-negatividad inventario",
            exitosa=exitosa,
            valorObservado=inventarioMinimo,
            valorEsperado=0.0,
            tolerancia=0.0,
            detalles=detalles,
            criticidad="CRITICA"
        ))

    # ========================================================================
    # CATEGORIA 2: CASOS EXTREMOS
    # ========================================================================

    def validarCapacidadInfinita(self) -> None:
        """
        Caso extremo: Capacidad infinita sin disrupciones.

        Prediccion teorica: Nivel de servicio = 100%
        """
        self.imprimirPrueba("Caso extremo: Capacidad infinita sin disrupciones")

        config = ConfiguracionSimulacion(
            capacidadHubTm=100000.0,
            puntoReordenTm=50000.0,
            cantidadPedidoTm=50000.0,
            inventarioInicialTm=60000.0,
            duracionDisrupcionMinDias=0.0,
            duracionDisrupcionModeDias=0.0,
            duracionDisrupcionMaxDias=0.0,
            semillaAleatoria=11111
        )

        resultado = ejecutarSimulacion(config)
        nivelServicio = resultado['nivel_servicio_pct']
        diasConQuiebre = resultado['dias_con_quiebre']

        exitosa = (nivelServicio >= 99.99) and (diasConQuiebre == 0)

        detalles = f"Nivel servicio={nivelServicio:.4f}%, Dias con quiebre={diasConQuiebre}"

        self.registrarResultado(ResultadoValidacion(
            nombrePrueba="Capacidad infinita",
            exitosa=exitosa,
            valorObservado=nivelServicio,
            valorEsperado=100.0,
            tolerancia=0.01,
            detalles=detalles,
            criticidad="ALTA"
        ))

    def validarInventarioInicialCero(self) -> None:
        """
        Caso extremo: Inventario inicial cero y ROP=0 (sin reabastecimiento).

        Prediccion teorica: Nivel de servicio = 0%
        """
        self.imprimirPrueba("Caso extremo: Inventario inicial cero sin reabastecimiento")

        config = ConfiguracionSimulacion(
            inventarioInicialTm=0.0,
            puntoReordenTm=200.0,
            cantidadPedidoTm=200.0,
            duracionDisrupcionMinDias=365.0,
            duracionDisrupcionModeDias=365.0,
            duracionDisrupcionMaxDias=365.0,
            tasaDisrupcionesAnual=1.0,  # Una disrupcion al inicio
            semillaAleatoria=22222
        )

        resultado = ejecutarSimulacion(config)
        nivelServicio = resultado['nivel_servicio_pct']
        demandaSatisfecha = resultado['demanda_satisfecha_tm']

        exitosa = (nivelServicio == 0.0) and (demandaSatisfecha == 0.0)

        detalles = f"Nivel servicio={nivelServicio:.4f}%, Demanda satisfecha={demandaSatisfecha:.2f} TM"

        self.registrarResultado(ResultadoValidacion(
            nombrePrueba="Inventario cero bloqueado",
            exitosa=exitosa,
            valorObservado=nivelServicio,
            valorEsperado=0.0,
            tolerancia=0.0,
            detalles=detalles,
            criticidad="ALTA"
        ))

    def validarDisrupcionPermanente(self) -> None:
        """
        Caso extremo: Ruta bloqueada todo el periodo.

        Prediccion teorica: Sin llegadas de pedidos (solo inventario inicial)
        """
        self.imprimirPrueba("Caso extremo: Disrupcion permanente (ruta bloqueada 365 dias)")

        config = ConfiguracionSimulacion(
            inventarioInicialTm=431.0 * 0.6,
            duracionDisrupcionMinDias=365.0,
            duracionDisrupcionModeDias=365.0,
            duracionDisrupcionMaxDias=365.0,
            tasaDisrupcionesAnual=1.0,  # 1 disrupcion al inicio
            semillaAleatoria=33333
        )

        resultado = ejecutarSimulacion(config)
        totalRecibido = resultado['total_recibido_tm']
        disrupciones = resultado['disrupciones_totales']

        # Con ruta bloqueada 365 dias, no deberian llegar pedidos
        exitosa = totalRecibido == 0.0

        detalles = f"Total recibido={totalRecibido:.2f} TM, Disrupciones={disrupciones}"

        self.registrarResultado(ResultadoValidacion(
            nombrePrueba="Disrupcion permanente",
            exitosa=exitosa,
            valorObservado=totalRecibido,
            valorEsperado=0.0,
            tolerancia=0.0,
            detalles=detalles,
            criticidad="ALTA"
        ))

    def validarSinDisrupciones(self) -> None:
        """
        Caso base: Sistema sin disrupciones.

        Prediccion teorica: Nivel servicio muy alto (>99%)
        """
        self.imprimirPrueba("Caso base: Sistema sin disrupciones")

        config = ConfiguracionSimulacion(
            duracionDisrupcionMinDias=0.0,
            duracionDisrupcionModeDias=0.0,
            duracionDisrupcionMaxDias=0.0,
            semillaAleatoria=44444
        )

        resultado = ejecutarSimulacion(config)
        nivelServicio = resultado['nivel_servicio_pct']
        disrupciones = resultado['disrupciones_totales']

        exitosa = (nivelServicio >= 99.0) and (disrupciones == 0)

        detalles = f"Nivel servicio={nivelServicio:.4f}%, Disrupciones={disrupciones}"

        self.registrarResultado(ResultadoValidacion(
            nombrePrueba="Sistema sin disrupciones",
            exitosa=exitosa,
            valorObservado=nivelServicio,
            valorEsperado=100.0,
            tolerancia=1.0,
            detalles=detalles,
            criticidad="MEDIA"
        ))

    # ========================================================================
    # CATEGORIA 3: VALIDACIONES ESTADISTICAS
    # ========================================================================

    def validarDistribucionPoisson(self) -> None:
        """
        Verifica que disrupciones sigan distribucion Poisson(lambda=4).

        Metodo: Test Chi-cuadrado de bondad de ajuste
        Hipotesis nula: Disrupciones ~ Poisson(4)
        Nivel significancia: alpha = 0.05
        """
        self.imprimirPrueba("Distribucion de Poisson para disrupciones (Chi-cuadrado)")

        numeroReplicas = 500
        lambdaEsperado = 4.0

        config = ConfiguracionSimulacion()
        disrupciones = []

        if self.verboso:
            print(f"    Ejecutando {numeroReplicas} replicas...", end=" ", flush=True)

        for i in range(numeroReplicas):
            config.semillaAleatoria = 50000 + i
            resultado = ejecutarSimulacion(config)
            disrupciones.append(resultado['disrupciones_totales'])

        if self.verboso:
            print("Completado")

        # Histograma observado
        valoresUnicos = np.arange(0, max(disrupciones) + 1)
        frecuenciasObservadas = np.array([disrupciones.count(k) for k in valoresUnicos])

        # Frecuencias esperadas bajo Poisson(4)
        frecuenciasEsperadas = poisson.pmf(valoresUnicos, lambdaEsperado) * numeroReplicas

        # Agrupar colas para evitar frecuencias esperadas muy bajas
        umbral = 5
        if np.any(frecuenciasEsperadas < umbral):
            # Agrupar eventos >= cierto valor
            corte = np.where(frecuenciasEsperadas >= umbral)[0][-1] + 1
            frecuenciasObservadas = np.append(frecuenciasObservadas[:corte],
                                              frecuenciasObservadas[corte:].sum())
            frecuenciasEsperadas = np.append(frecuenciasEsperadas[:corte],
                                            frecuenciasEsperadas[corte:].sum())

        # Normalizar para evitar errores de precision numerica
        frecuenciasEsperadas = frecuenciasEsperadas * (frecuenciasObservadas.sum() / frecuenciasEsperadas.sum())

        # Test Chi-cuadrado
        chiCuadrado, pValor = chisquare(frecuenciasObservadas, frecuenciasEsperadas)

        mediaObservada = np.mean(disrupciones)
        exitosa = pValor >= 0.05

        detalles = (f"Chi2={chiCuadrado:.4f}, p-valor={pValor:.4f}, "
                   f"Media observada={mediaObservada:.2f}, Lambda esperado={lambdaEsperado}")

        self.registrarResultado(ResultadoValidacion(
            nombrePrueba="Distribucion Poisson",
            exitosa=exitosa,
            valorObservado=pValor,
            valorEsperado=0.05,
            tolerancia=0.0,
            detalles=detalles,
            criticidad="MEDIA"
        ))

    def validarIndependenciaReplicas(self) -> None:
        """
        Verifica independencia estadistica entre replicas.

        Metodo: Test de rachas (runs test)
        Hipotesis nula: Replicas son independientes
        """
        self.imprimirPrueba("Independencia entre replicas (Runs test)")

        numeroReplicas = 200
        config = ConfiguracionSimulacion()

        nivelesServicio = []
        for i in range(numeroReplicas):
            config.semillaAleatoria = 60000 + i
            resultado = ejecutarSimulacion(config)
            nivelesServicio.append(resultado['nivel_servicio_pct'])

        # Test de rachas: convierte a secuencia binaria (arriba/abajo de mediana)
        mediana = np.median(nivelesServicio)
        secuenciaBinaria = [1 if x >= mediana else 0 for x in nivelesServicio]

        # Contar rachas
        rachas = 1
        for i in range(1, len(secuenciaBinaria)):
            if secuenciaBinaria[i] != secuenciaBinaria[i-1]:
                rachas += 1

        # Estadistico bajo independencia
        n1 = sum(secuenciaBinaria)
        n2 = len(secuenciaBinaria) - n1
        mediaRachas = (2 * n1 * n2) / (n1 + n2) + 1
        varianzaRachas = (2 * n1 * n2 * (2 * n1 * n2 - n1 - n2)) / ((n1 + n2)**2 * (n1 + n2 - 1))

        zScore = (rachas - mediaRachas) / np.sqrt(varianzaRachas)
        pValor = 2 * (1 - norm.cdf(abs(zScore)))

        exitosa = pValor >= 0.05

        detalles = f"Rachas={rachas}, Esperado={mediaRachas:.1f}, Z={zScore:.3f}, p-valor={pValor:.4f}"

        self.registrarResultado(ResultadoValidacion(
            nombrePrueba="Independencia replicas",
            exitosa=exitosa,
            valorObservado=pValor,
            valorEsperado=0.05,
            tolerancia=0.0,
            detalles=detalles,
            criticidad="ALTA"
        ))

    def validarNormalidadDemanda(self) -> None:
        """
        Verifica que demanda diaria siga distribucion aproximadamente Normal.

        Metodo: Test Kolmogorov-Smirnov
        """
        self.imprimirPrueba("Normalidad de demanda diaria (Kolmogorov-Smirnov)")

        config = ConfiguracionSimulacion(
            usarEstacionalidad=False,  # Sin estacionalidad para aislar ruido
            semillaAleatoria=77777
        )

        from modelo import SimulacionGlpAysen
        sim = SimulacionGlpAysen(config)
        sim.run()

        demandas = [m.demandaTm for m in sim.metricasDiarias]
        media = np.mean(demandas)
        std = np.std(demandas, ddof=1)

        # Normalizar
        demandasNormalizadas = [(d - media) / std for d in demandas]

        # Test KS contra Normal(0,1)
        estadistico, pValor = kstest(demandasNormalizadas, 'norm')

        exitosa = pValor >= 0.05

        detalles = f"KS={estadistico:.4f}, p-valor={pValor:.4f}, Media={media:.2f}, Std={std:.2f}"

        self.registrarResultado(ResultadoValidacion(
            nombrePrueba="Normalidad demanda",
            exitosa=exitosa,
            valorObservado=pValor,
            valorEsperado=0.05,
            tolerancia=0.0,
            detalles=detalles,
            criticidad="BAJA"
        ))

    # ========================================================================
    # CATEGORIA 4: SENSIBILIDAD Y MONOTONICIDAD
    # ========================================================================

    def validarMonotonicidadCapacidad(self) -> None:
        """
        Verifica monotonicidad: Mayor capacidad -> Mayor nivel de servicio.

        Propiedad teorica: dNS/dCap >= 0
        """
        self.imprimirPrueba("Monotonicidad: Capacidad vs Nivel de servicio")

        capacidades = [300, 400, 500, 600, 700]
        nivelesServicio = []

        for cap in capacidades:
            config = ConfiguracionSimulacion(
                capacidadHubTm=cap,
                puntoReordenTm=cap * 0.5,
                cantidadPedidoTm=cap * 0.5,
                inventarioInicialTm=cap * 0.6,
                semillaAleatoria=88888
            )
            resultado = ejecutarSimulacion(config)
            nivelesServicio.append(resultado['nivel_servicio_pct'])

        # Verificar monotonicidad (no-decreciente)
        monotona = all(nivelesServicio[i] <= nivelesServicio[i+1]
                       for i in range(len(nivelesServicio)-1))

        pendientePromedio = (nivelesServicio[-1] - nivelesServicio[0]) / (capacidades[-1] - capacidades[0])

        detalles = f"Niveles: {[f'{ns:.2f}' for ns in nivelesServicio]}, Pendiente={pendientePromedio:.4f}"

        self.registrarResultado(ResultadoValidacion(
            nombrePrueba="Monotonicidad capacidad",
            exitosa=monotona,
            valorObservado=pendientePromedio,
            valorEsperado=0.0,
            tolerancia=0.0,
            detalles=detalles,
            criticidad="MEDIA"
        ))

    def validarMonotonicidadDisrupciones(self) -> None:
        """
        Verifica monotonicidad: Mayor duracion disrupciones -> Menor nivel servicio.

        Propiedad teorica: dNS/dDuracion <= 0
        """
        self.imprimirPrueba("Monotonicidad: Duracion disrupciones vs Nivel servicio")

        duracionesMax = [0, 7, 14, 21, 28]
        nivelesServicio = []

        for durMax in duracionesMax:
            durMode = durMax * 0.5 if durMax > 0 else 0
            durMin = 3.0 if durMax > 0 else 0
            config = ConfiguracionSimulacion(
                duracionDisrupcionMinDias=durMin,
                duracionDisrupcionModeDias=durMode,
                duracionDisrupcionMaxDias=durMax,
                semillaAleatoria=99999
            )
            resultado = ejecutarSimulacion(config)
            nivelesServicio.append(resultado['nivel_servicio_pct'])

        # Verificar monotonicidad decreciente
        monotona = all(nivelesServicio[i] >= nivelesServicio[i+1]
                       for i in range(len(nivelesServicio)-1))

        pendientePromedio = (nivelesServicio[-1] - nivelesServicio[0]) / (duracionesMax[-1] - duracionesMax[0])

        detalles = f"Niveles: {[f'{ns:.2f}' for ns in nivelesServicio]}, Pendiente={pendientePromedio:.4f}"

        self.registrarResultado(ResultadoValidacion(
            nombrePrueba="Monotonicidad disrupciones",
            exitosa=monotona,
            valorObservado=pendientePromedio,
            valorEsperado=0.0,
            tolerancia=0.0,
            detalles=detalles,
            criticidad="MEDIA"
        ))

    # ========================================================================
    # CATEGORIA 5: COMPARACION ANALITICA
    # ========================================================================

    def validarAutonomiaTeoricoVsSimulado(self) -> None:
        """
        Compara autonomia teorica vs simulada (sin disrupciones).

        Formula teorica: A = Capacidad / Demanda_promedio
        """
        self.imprimirPrueba("Autonomia teorica vs simulada")

        config = ConfiguracionSimulacion(
            capacidadHubTm=431.0,
            demandaBaseDiariaTm=52.5,
            duracionDisrupcionMinDias=0.0,
            duracionDisrupcionModeDias=0.0,
            duracionDisrupcionMaxDias=0.0,
            usarEstacionalidad=False,
            semillaAleatoria=111111
        )

        autonomiaTeorica = config.capacidadHubTm / config.demandaBaseDiariaTm

        # Promedio de multiples replicas para reducir varianza
        autonomiasSimuladas = []
        for i in range(20):
            config.semillaAleatoria = 111111 + i
            resultado = ejecutarSimulacion(config)
            autonomiasSimuladas.append(resultado['autonomia_promedio_dias'])

        autonomiaSimuladaPromedio = np.mean(autonomiasSimuladas)
        errorRelativo = abs(autonomiaSimuladaPromedio - autonomiaTeorica) / autonomiaTeorica

        tolerancia = 0.10  # 10% error relativo
        exitosa = errorRelativo < tolerancia

        detalles = (f"Teorica={autonomiaTeorica:.2f} dias, "
                   f"Simulada={autonomiaSimuladaPromedio:.2f} dias, "
                   f"Error relativo={errorRelativo*100:.2f}%")

        self.registrarResultado(ResultadoValidacion(
            nombrePrueba="Autonomia teorica vs simulada",
            exitosa=exitosa,
            valorObservado=autonomiaSimuladaPromedio,
            valorEsperado=autonomiaTeorica,
            tolerancia=autonomiaTeorica * tolerancia,
            detalles=detalles,
            criticidad="MEDIA"
        ))

    def validarFrecuenciaDisrupcionesEsperada(self) -> None:
        """
        Verifica que frecuencia promedio de disrupciones sea lambda = 4/año.

        Metodo: Promedio de multiples replicas con intervalo de confianza
        """
        self.imprimirPrueba("Frecuencia esperada de disrupciones")

        numeroReplicas = 100
        lambdaEsperado = 4.0

        config = ConfiguracionSimulacion()
        disrupciones = []

        for i in range(numeroReplicas):
            config.semillaAleatoria = 222222 + i
            resultado = ejecutarSimulacion(config)
            disrupciones.append(resultado['disrupciones_totales'])

        mediaObservada = np.mean(disrupciones)
        stdObservada = np.std(disrupciones, ddof=1)
        errorEstandar = stdObservada / np.sqrt(numeroReplicas)

        # Intervalo confianza 95%
        zCritico = 1.96
        ic95Inferior = mediaObservada - zCritico * errorEstandar
        ic95Superior = mediaObservada + zCritico * errorEstandar

        exitosa = ic95Inferior <= lambdaEsperado <= ic95Superior

        detalles = (f"Media={mediaObservada:.2f}, IC95%=[{ic95Inferior:.2f}, {ic95Superior:.2f}], "
                   f"Lambda esperado={lambdaEsperado}")

        self.registrarResultado(ResultadoValidacion(
            nombrePrueba="Frecuencia disrupciones",
            exitosa=exitosa,
            valorObservado=mediaObservada,
            valorEsperado=lambdaEsperado,
            tolerancia=zCritico * errorEstandar,
            detalles=detalles,
            criticidad="MEDIA"
        ))

    # ========================================================================
    # CATEGORIA 6: CALIBRACION EMPIRICA
    # ========================================================================

    def validarAutonomiaInformeCne(self) -> None:
        """
        Valida contra dato real del Informe CNE 2024.

        Referencia: Autonomia status quo = 8.2 dias (mes de mayor consumo)
        """
        self.imprimirPrueba("Calibracion: Autonomia Informe CNE (8.2 dias)")

        # Configuracion status quo del informe
        config = ConfiguracionSimulacion(
            capacidadHubTm=431.0,
            demandaBaseDiariaTm=52.5,
            duracionDisrupcionMinDias=0.0,
            duracionDisrupcionModeDias=0.0,
            duracionDisrupcionMaxDias=0.0,  # Sin disrupciones para autonomia base
            semillaAleatoria=333333
        )

        # Promedio de replicas
        autonomias = []
        for i in range(30):
            config.semillaAleatoria = 333333 + i
            resultado = ejecutarSimulacion(config)
            autonomias.append(resultado['autonomia_promedio_dias'])

        autonomiaPromedio = np.mean(autonomias)
        autonomiaInformeCne = 8.2

        errorAbsoluto = abs(autonomiaPromedio - autonomiaInformeCne)
        tolerancia = 1.0  # +/- 1 dia
        exitosa = errorAbsoluto < tolerancia

        detalles = (f"Informe CNE={autonomiaInformeCne:.1f} dias, "
                   f"Simulacion={autonomiaPromedio:.2f} dias, "
                   f"Error={errorAbsoluto:.2f} dias")

        self.registrarResultado(ResultadoValidacion(
            nombrePrueba="Autonomia Informe CNE",
            exitosa=exitosa,
            valorObservado=autonomiaPromedio,
            valorEsperado=autonomiaInformeCne,
            tolerancia=tolerancia,
            detalles=detalles,
            criticidad="ALTA"
        ))

    def validarDemandaPromedioAnual(self) -> None:
        """
        Verifica que demanda promedio anual sea consistente con parametros.

        Demanda base: 52.5 TM/dia (mes pico)
        Con estacionalidad: ~47-48 TM/dia promedio anual
        """
        self.imprimirPrueba("Demanda promedio anual con estacionalidad")

        config = ConfiguracionSimulacion(
            usarEstacionalidad=True,
            semillaAleatoria=444444
        )

        resultado = ejecutarSimulacion(config)
        demandaPromedioObservada = resultado['demanda_promedio_diaria_tm']

        # Con estacionalidad sinusoidal simetrica, promedio deberia ser ~ demanda base
        demandaEsperada = config.demandaBaseDiariaTm

        errorRelativo = abs(demandaPromedioObservada - demandaEsperada) / demandaEsperada
        tolerancia = 0.05  # 5%
        exitosa = errorRelativo < tolerancia

        detalles = (f"Esperada={demandaEsperada:.2f} TM/dia, "
                   f"Observada={demandaPromedioObservada:.2f} TM/dia, "
                   f"Error relativo={errorRelativo*100:.2f}%")

        self.registrarResultado(ResultadoValidacion(
            nombrePrueba="Demanda promedio anual",
            exitosa=exitosa,
            valorObservado=demandaPromedioObservada,
            valorEsperado=demandaEsperada,
            tolerancia=demandaEsperada * tolerancia,
            detalles=detalles,
            criticidad="BAJA"
        ))

    # ========================================================================
    # UTILIDADES
    # ========================================================================

    def registrarResultado(self, resultado: ResultadoValidacion) -> None:
        """Registra resultado de validacion y lo imprime."""
        self.resultados.append(resultado)

        if self.verboso:
            estado = "PASS" if resultado.exitosa else "FAIL"
            simbolo = "[OK]" if resultado.exitosa else "[XX]"

            print(f"    {simbolo} {estado}")
            print(f"        Observado: {resultado.valorObservado:.6f}")
            print(f"        Esperado:  {resultado.valorEsperado:.6f}")
            print(f"        {resultado.detalles}")
            print()

    def generarReporteFinal(self) -> None:
        """Genera reporte consolidado de validaciones."""
        self.imprimirSeccion("REPORTE FINAL DE VALIDACION")

        totalPruebas = len(self.resultados)
        pruebasExitosas = sum(1 for r in self.resultados if r.exitosa)
        pruebasFallidas = totalPruebas - pruebasExitosas

        tasaExito = (pruebasExitosas / totalPruebas * 100) if totalPruebas > 0 else 0

        print(f"Total de pruebas ejecutadas:  {totalPruebas}")
        print(f"Pruebas exitosas:             {pruebasExitosas}")
        print(f"Pruebas fallidas:             {pruebasFallidas}")
        print(f"Tasa de exito:                {tasaExito:.2f}%")
        print()

        # Desglose por criticidad
        criticidades = ["CRITICA", "ALTA", "MEDIA", "BAJA"]
        for crit in criticidades:
            pruebas = [r for r in self.resultados if r.criticidad == crit]
            if pruebas:
                exitosas = sum(1 for r in pruebas if r.exitosa)
                total = len(pruebas)
                print(f"  {crit:8s}: {exitosas}/{total} exitosas")

        print()

        # Listar pruebas fallidas
        fallidas = [r for r in self.resultados if not r.exitosa]
        if fallidas:
            print("PRUEBAS FALLIDAS:")
            for r in fallidas:
                print(f"  - {r.nombrePrueba} ({r.criticidad})")
                print(f"    {r.detalles}")
            print()

        # Veredicto final
        pruebasCriticasFallidas = sum(1 for r in self.resultados
                                      if not r.exitosa and r.criticidad == "CRITICA")

        print("="*70)
        if pruebasCriticasFallidas > 0:
            print("VEREDICTO: MODELO NO VALIDADO")
            print(f"Razon: {pruebasCriticasFallidas} prueba(s) critica(s) fallida(s)")
        elif pruebasFallidas > 0:
            print("VEREDICTO: MODELO VALIDADO CON ADVERTENCIAS")
            print(f"Advertencia: {pruebasFallidas} prueba(s) no critica(s) fallida(s)")
        else:
            print("VEREDICTO: MODELO COMPLETAMENTE VALIDADO")
            print("Todas las pruebas pasaron exitosamente")
        print("="*70)

    def imprimirEncabezado(self, texto: str) -> None:
        """Imprime encabezado principal."""
        if self.verboso:
            print("\n" + "="*70)
            print(texto.center(70))
            print("="*70 + "\n")

    def imprimirSeccion(self, texto: str) -> None:
        """Imprime encabezado de seccion."""
        if self.verboso:
            print("\n" + "-"*70)
            print(texto)
            print("-"*70 + "\n")

    def imprimirPrueba(self, texto: str) -> None:
        """Imprime nombre de prueba."""
        if self.verboso:
            print(f"  Ejecutando: {texto}")


def main():
    """Punto de entrada principal."""
    import warnings
    warnings.filterwarnings('ignore')

    sistema = SistemaValidacion(verboso=True)
    sistema.ejecutarTodasLasValidaciones()


if __name__ == "__main__":
    main()
