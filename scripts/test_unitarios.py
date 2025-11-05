"""
Tests Unitarios del Modelo de Simulacion

Conjunto de pruebas unitarias para verificar correctitud de componentes
individuales del modelo de simulacion.

Compatibilidad: pytest, unittest

Ejecucion:
    pytest test_unitarios.py -v
    python -m unittest test_unitarios.py -v
"""
import sys
from pathlib import Path
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from modelo import (
    ConfiguracionSimulacion,
    HubCoyhaique,
    RutaSuministro,
    SimulacionGlpAysen,
    ejecutarSimulacion
)
import simpy


class TestConfiguracionSimulacion(unittest.TestCase):
    """Tests de la clase ConfiguracionSimulacion."""

    def testConfiguracionPorDefectoValida(self):
        """Configuracion por defecto debe pasar validacion."""
        config = ConfiguracionSimulacion()
        try:
            config.validar()
        except AssertionError as e:
            self.fail(f"Configuracion por defecto invalida: {e}")

    def testCapacidadNegativaFalla(self):
        """Capacidad negativa debe fallar validacion."""
        config = ConfiguracionSimulacion(capacidadHubTm=-100.0)
        with self.assertRaises(AssertionError):
            config.validar()

    def testPuntoReordenMayorQueCapacidadFalla(self):
        """Punto de reorden mayor que capacidad debe fallar."""
        config = ConfiguracionSimulacion(
            capacidadHubTm=100.0,
            puntoReordenTm=200.0
        )
        with self.assertRaises(AssertionError):
            config.validar()

    def testInventarioInicialMayorQueCapacidadFalla(self):
        """Inventario inicial mayor que capacidad debe fallar."""
        config = ConfiguracionSimulacion(
            capacidadHubTm=100.0,
            inventarioInicialTm=150.0
        )
        with self.assertRaises(AssertionError):
            config.validar()

    def testDuracionesDisrupcionInconsistentesFalla(self):
        """Duraciones min > mode > max debe fallar."""
        config = ConfiguracionSimulacion(
            duracionDisrupcionMinDias=20.0,
            duracionDisrupcionModeDias=10.0,
            duracionDisrupcionMaxDias=5.0
        )
        with self.assertRaises(AssertionError):
            config.validar()


class TestHubCoyhaique(unittest.TestCase):
    """Tests de la clase HubCoyhaique."""

    def setUp(self):
        """Configuracion inicial para cada test."""
        self.env = simpy.Environment()
        self.config = ConfiguracionSimulacion(
            capacidadHubTm=500.0,
            inventarioInicialTm=300.0
        )
        self.hub = HubCoyhaique(self.env, self.config)

    def testInventarioInicialCorrecto(self):
        """Inventario inicial debe ser el configurado."""
        self.assertAlmostEqual(self.hub.inventario.level, 300.0, places=2)

    def testCapacidadCorrecto(self):
        """Capacidad debe ser la configurada."""
        self.assertAlmostEqual(self.hub.inventario.capacity, 500.0, places=2)

    def testDespachoNormalSatisfaceCompletamente(self):
        """Despacho con inventario suficiente debe satisfacer demanda completa."""
        despachado = self.hub.despacharAClientes(100.0)
        self.assertAlmostEqual(despachado, 100.0, places=2)
        self.assertAlmostEqual(self.hub.inventario.level, 200.0, places=2)

    def testDespachoParcialCuandoInventarioInsuficiente(self):
        """Despacho con inventario insuficiente debe ser parcial."""
        despachado = self.hub.despacharAClientes(350.0)
        self.assertAlmostEqual(despachado, 300.0, places=2)
        self.assertAlmostEqual(self.hub.inventario.level, 0.0, places=2)

    def testDespachoConInventarioCeroRetornaCero(self):
        """Despacho con inventario cero debe retornar cero."""
        # Vaciar inventario
        self.hub.despacharAClientes(300.0)
        # Intentar despachar de inventario vacio
        despachado = self.hub.despacharAClientes(50.0)
        self.assertAlmostEqual(despachado, 0.0, places=2)

    def testContadorQuiebresIncrementaCorrectamente(self):
        """Contador de quiebres debe incrementar cuando no se satisface demanda completa."""
        self.hub.despacharAClientes(350.0)  # Insuficiente
        self.assertEqual(self.hub.quiebresStock, 1)

    def testRecepcionSuministroIncrementaInventario(self):
        """Recepcion de suministro debe incrementar inventario."""
        def proceso():
            yield self.hub.recibirSuministro(100.0)
            self.assertAlmostEqual(self.hub.inventario.level, 400.0, places=2)

        self.env.process(proceso())
        self.env.run()

    def testRecepcionSuministroNoExcedeCapacidad(self):
        """Recepcion no debe exceder capacidad maxima."""
        def proceso():
            # Intentar agregar mas de la capacidad disponible
            try:
                yield self.hub.recibirSuministro(250.0)  # 300 + 250 > 500
                # Container deberia bloquear hasta que haya espacio
            except:
                pass

        self.env.process(proceso())
        # Ejecutar con timeout corto
        self.env.run(until=1)
        # Verificar que no excede capacidad
        self.assertLessEqual(self.hub.inventario.level, self.hub.inventario.capacity)

    def testNecesitaReabastecimientoCuandoInvBajoPuntoReorden(self):
        """Debe necesitar reabastecimiento cuando Inv <= ROP."""
        self.config.puntoReordenTm = 250.0
        self.hub.despacharAClientes(100.0)  # Inv = 200 < ROP
        self.assertTrue(self.hub.necesitaReabastecimiento())

    def testNoNecesitaReabastecimientoCuandoInvSobrePuntoReorden(self):
        """No debe necesitar reabastecimiento cuando Inv > ROP."""
        self.config.puntoReordenTm = 250.0
        # Inv = 300 > ROP
        self.assertFalse(self.hub.necesitaReabastecimiento())


class TestRutaSuministro(unittest.TestCase):
    """Tests de la clase RutaSuministro."""

    def setUp(self):
        """Configuracion inicial para cada test."""
        self.env = simpy.Environment()
        self.config = ConfiguracionSimulacion(leadTimeNominalDias=6.0)
        self.rng = np.random.default_rng(12345)
        self.ruta = RutaSuministro(self.env, self.config, self.rng)

    def testRutaOperativaInicial(self):
        """Ruta debe estar operativa inicialmente."""
        self.assertTrue(self.ruta.estaOperativa())

    def testBloqueoRuta(self):
        """Bloqueo de ruta debe marcarla como bloqueada."""
        self.ruta.bloquearPorDisrupcion(10.0)
        self.assertTrue(self.ruta.bloqueada)
        self.assertFalse(self.ruta.estaOperativa())

    def testTiempoDesbloqueoCalculadoCorrectamente(self):
        """Tiempo de desbloqueo debe ser tiempo actual + duracion."""
        def proceso():
            yield self.env.timeout(5.0)
            self.ruta.bloquearPorDisrupcion(10.0)
            self.assertAlmostEqual(self.ruta.tiempoDesbloqueo, 15.0, places=2)

        self.env.process(proceso())
        self.env.run()

    def testContadorDisrupcionesIncrementa(self):
        """Contador de disrupciones debe incrementar."""
        self.ruta.bloquearPorDisrupcion(5.0)
        self.assertEqual(self.ruta.disrupcionesTotales, 1)
        self.ruta.bloquearPorDisrupcion(3.0)
        self.assertEqual(self.ruta.disrupcionesTotales, 2)

    def testDiasBloqueadosAcumula(self):
        """Dias bloqueados debe acumular correctamente."""
        self.ruta.bloquearPorDisrupcion(5.0)
        self.ruta.bloquearPorDisrupcion(3.0)
        self.assertAlmostEqual(self.ruta.diasBloqueadosAcumulados, 8.0, places=2)

    def testDesbloqueoAutomatico(self):
        """Ruta debe desbloquearse automaticamente al alcanzar tiempo."""
        def proceso():
            self.ruta.bloquearPorDisrupcion(10.0)
            yield self.env.timeout(15.0)
            # Al verificar, debe desbloquearse
            operativa = self.ruta.estaOperativa()
            self.assertTrue(operativa)

        self.env.process(proceso())
        self.env.run()

    def testLeadTimeNominalCuandoRutaOperativa(self):
        """Lead time debe ser nominal cuando ruta operativa."""
        lt = self.ruta.calcularLeadTime()
        self.assertAlmostEqual(lt, 6.0, places=2)

    def testLeadTimeExtendidoCuandoRutaBloqueada(self):
        """Lead time debe extenderse cuando ruta bloqueada."""
        self.ruta.bloquearPorDisrupcion(10.0)
        lt = self.ruta.calcularLeadTime()
        self.assertGreater(lt, 6.0)

    def testLeadTimeExtensionCalculadoCorrectamente(self):
        """Extension de lead time debe ser nominal + tiempo restante."""
        def proceso():
            yield self.env.timeout(5.0)
            self.ruta.bloquearPorDisrupcion(10.0)  # Desbloqueo en t=15
            # Tiempo restante = 15 - 5 = 10
            lt = self.ruta.calcularLeadTime()
            self.assertAlmostEqual(lt, 16.0, places=2)  # 6 + 10

        self.env.process(proceso())
        self.env.run()


class TestSimulacionGlpAysen(unittest.TestCase):
    """Tests de la clase SimulacionGlpAysen."""

    def testCreacionSimulacionExitosa(self):
        """Creacion de simulacion debe ser exitosa."""
        config = ConfiguracionSimulacion()
        sim = SimulacionGlpAysen(config)
        self.assertIsNotNone(sim.env)
        self.assertIsNotNone(sim.hub)
        self.assertIsNotNone(sim.ruta)

    def testCalculoDemandaSinEstacionalidad(self):
        """Demanda sin estacionalidad debe estar cerca de demanda base."""
        config = ConfiguracionSimulacion(
            usarEstacionalidad=False,
            demandaBaseDiariaTm=50.0,
            variabilidadDemanda=0.0,  # Sin ruido
            semillaAleatoria=123
        )
        sim = SimulacionGlpAysen(config)

        demanda = sim.calcularDemandaDia(100)
        self.assertAlmostEqual(demanda, 50.0, places=1)

    def testCalculoDemandaConEstacionalidad(self):
        """Demanda con estacionalidad debe variar segun ciclo anual."""
        config = ConfiguracionSimulacion(
            usarEstacionalidad=True,
            demandaBaseDiariaTm=50.0,
            amplitudEstacional=0.30,
            diaPicoInvernal=200,
            variabilidadDemanda=0.01,  # Variabilidad muy pequeña para test determinista
            semillaAleatoria=12345
        )
        sim = SimulacionGlpAysen(config)

        # Calcular demandas en varios dias del ciclo
        demandas = [sim.calcularDemandaDia(dia) for dia in range(365)]
        demandaMaxima = max(demandas)
        demandaMinima = min(demandas)

        # Con estacionalidad de 30%, debe haber variacion significativa
        rangoDemanda = demandaMaxima - demandaMinima
        self.assertGreater(rangoDemanda, 10.0)  # Rango > 10 TM

    def testDemandaNuncaNegativa(self):
        """Demanda nunca debe ser negativa."""
        config = ConfiguracionSimulacion(semillaAleatoria=999)
        sim = SimulacionGlpAysen(config)

        for dia in range(365):
            demanda = sim.calcularDemandaDia(dia)
            self.assertGreaterEqual(demanda, 0.0)

    def testSimulacionCompletaSinErrores(self):
        """Simulacion completa debe ejecutarse sin errores."""
        config = ConfiguracionSimulacion(
            duracionSimulacionDias=30,
            semillaAleatoria=555
        )
        try:
            resultado = ejecutarSimulacion(config)
            self.assertIsNotNone(resultado)
        except Exception as e:
            self.fail(f"Simulacion fallo: {e}")

    def testMetricasDiariasGeneradas(self):
        """Simulacion debe generar metricas diarias."""
        config = ConfiguracionSimulacion(
            duracionSimulacionDias=30,
            semillaAleatoria=777
        )
        sim = SimulacionGlpAysen(config)
        sim.run()

        self.assertEqual(len(sim.metricasDiarias), 30)

    def testInventarioNuncaNegativo(self):
        """Inventario nunca debe ser negativo durante simulacion."""
        config = ConfiguracionSimulacion(
            duracionSimulacionDias=365,
            semillaAleatoria=888
        )
        sim = SimulacionGlpAysen(config)
        sim.run()

        for metrica in sim.metricasDiarias:
            self.assertGreaterEqual(metrica.inventarioTm, 0.0,
                                   f"Inventario negativo en dia {metrica.dia}")

    def testDemandaSatisfechaMenorOIgualDemandaTotal(self):
        """Demanda satisfecha nunca puede exceder demanda total."""
        config = ConfiguracionSimulacion(semillaAleatoria=999)
        sim = SimulacionGlpAysen(config)
        sim.run()

        self.assertLessEqual(sim.demandaSatisfechaTm, sim.demandaTotalTm)


class TestEjecutarSimulacion(unittest.TestCase):
    """Tests de la funcion ejecutarSimulacion."""

    def testRetornaDiccionarioConKpis(self):
        """Debe retornar diccionario con todos los KPIs."""
        config = ConfiguracionSimulacion(duracionSimulacionDias=30)
        resultado = ejecutarSimulacion(config)

        kpisEsperados = [
            'nivel_servicio_pct',
            'probabilidad_quiebre_stock_pct',
            'dias_con_quiebre',
            'inventario_promedio_tm',
            'autonomia_promedio_dias',
            'demanda_total_tm',
            'demanda_satisfecha_tm',
            'disrupciones_totales',
            'total_recibido_tm',
            'total_despachado_tm',
            'inventario_final_tm',
            'inventario_inicial_tm'
        ]

        for kpi in kpisEsperados:
            self.assertIn(kpi, resultado, f"KPI faltante: {kpi}")

    def testNivelServicioEntre0y100(self):
        """Nivel de servicio debe estar entre 0 y 100%."""
        config = ConfiguracionSimulacion(semillaAleatoria=123)
        resultado = ejecutarSimulacion(config)

        nivelServicio = resultado['nivel_servicio_pct']
        self.assertGreaterEqual(nivelServicio, 0.0)
        self.assertLessEqual(nivelServicio, 100.0)

    def testAutonomiaPromedioPositiva(self):
        """Autonomia promedio debe ser positiva."""
        config = ConfiguracionSimulacion(semillaAleatoria=456)
        resultado = ejecutarSimulacion(config)

        autonomia = resultado['autonomia_promedio_dias']
        self.assertGreater(autonomia, 0.0)

    def testDisrupcionesNoNegativas(self):
        """Numero de disrupciones debe ser no negativo."""
        config = ConfiguracionSimulacion(semillaAleatoria=789)
        resultado = ejecutarSimulacion(config)

        disrupciones = resultado['disrupciones_totales']
        self.assertGreaterEqual(disrupciones, 0)

    def testReproducibilidadConMismaSemilla(self):
        """Misma semilla debe generar mismos resultados."""
        config1 = ConfiguracionSimulacion(semillaAleatoria=12345)
        config2 = ConfiguracionSimulacion(semillaAleatoria=12345)

        resultado1 = ejecutarSimulacion(config1)
        resultado2 = ejecutarSimulacion(config2)

        self.assertAlmostEqual(resultado1['nivel_servicio_pct'],
                              resultado2['nivel_servicio_pct'],
                              places=4)

    def testDiferentesSemillasGeneranResultadosDiferentes(self):
        """Diferentes semillas deben generar resultados diferentes."""
        config1 = ConfiguracionSimulacion(semillaAleatoria=111)
        config2 = ConfiguracionSimulacion(semillaAleatoria=999)

        resultado1 = ejecutarSimulacion(config1)
        resultado2 = ejecutarSimulacion(config2)

        # Con alta probabilidad, los resultados seran diferentes
        # (podrian ser iguales por coincidencia, pero muy improbable)
        self.assertNotAlmostEqual(resultado1['disrupciones_totales'],
                                 resultado2['disrupciones_totales'],
                                 delta=0)


class TestBalanceMasa(unittest.TestCase):
    """Tests de conservacion de masa."""

    def testConservacionMasaSimulacionCorta(self):
        """Balance de masa debe conservarse en simulacion corta."""
        config = ConfiguracionSimulacion(
            duracionSimulacionDias=30,
            semillaAleatoria=111
        )
        resultado = ejecutarSimulacion(config)

        inicial = resultado['inventario_inicial_tm']
        final = resultado['inventario_final_tm']
        recibido = resultado['total_recibido_tm']
        despachado = resultado['total_despachado_tm']

        balance = abs((inicial + recibido) - (final + despachado))
        self.assertLess(balance, 0.01, f"Balance de masa violado: {balance} TM")

    def testConservacionMasaSimulacionLarga(self):
        """Balance de masa debe conservarse en simulacion completa."""
        config = ConfiguracionSimulacion(
            duracionSimulacionDias=365,
            semillaAleatoria=222
        )
        resultado = ejecutarSimulacion(config)

        inicial = resultado['inventario_inicial_tm']
        final = resultado['inventario_final_tm']
        recibido = resultado['total_recibido_tm']
        despachado = resultado['total_despachado_tm']

        balance = abs((inicial + recibido) - (final + despachado))
        self.assertLess(balance, 0.01, f"Balance de masa violado: {balance} TM")

    def testDemandaSatisfechaMenorOIgualRecibidoMasInicial(self):
        """Demanda satisfecha no puede exceder lo disponible."""
        config = ConfiguracionSimulacion(semillaAleatoria=333)
        resultado = ejecutarSimulacion(config)

        disponible = resultado['inventario_inicial_tm'] + resultado['total_recibido_tm']
        satisfecha = resultado['demanda_satisfecha_tm']

        self.assertLessEqual(satisfecha, disponible + 0.01)


def suite():
    """Crea suite de tests."""
    loader = unittest.TestLoader()
    testSuite = unittest.TestSuite()
    testSuite.addTests(loader.loadTestsFromTestCase(TestConfiguracionSimulacion))
    testSuite.addTests(loader.loadTestsFromTestCase(TestHubCoyhaique))
    testSuite.addTests(loader.loadTestsFromTestCase(TestRutaSuministro))
    testSuite.addTests(loader.loadTestsFromTestCase(TestSimulacionGlpAysen))
    testSuite.addTests(loader.loadTestsFromTestCase(TestEjecutarSimulacion))
    testSuite.addTests(loader.loadTestsFromTestCase(TestBalanceMasa))
    return testSuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
