"""
Sistema de monitoreo y logging para simulacion de cadena de suministro.
Registra metricas diarias en formato Parquet para analisis temporal.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import pandas as pd
from pathlib import Path


@dataclass
class RegistroDiario:
    """Registro de metricas del sistema para un dia especifico."""
    dia: int

    # Inventarios Hub
    invHubGranel: float
    invHubEnvasado: float

    # Inventarios Red CDEs
    invCdes: float

    # Flujos diarios
    flujoRecepcionHub: float
    flujoDespachoGranel: float
    flujoDespachoEnvasado: float
    flujoEnvasadoProcesado: float
    flujoReabastecimientoCdes: float

    # Demanda y satisfaccion
    demandaGranel: float
    demandaEnvasado: float
    satisfaccionGranel: float
    satisfaccionEnvasado: float

    # Transporte
    camionesEnRuta: int
    viajesCompletados: int

    # Eventos
    desabastecimientoGranel: bool
    desabastecimientoEnvasado: bool
    quiebreStockHubGranel: bool
    quiebreStockHubEnvasado: bool
    quiebreStockCdes: bool


class MonitorSimulacion:
    """Monitor para recolectar y almacenar metricas de la simulacion."""

    def __init__(self):
        self.registros: List[RegistroDiario] = []

    def registrarDia(self, registro: RegistroDiario) -> None:
        """Agrega un registro diario a la coleccion."""
        self.registros.append(registro)

    def guardarParquet(self, ruta: Path) -> None:
        """Guarda los registros en formato Parquet."""
        if not self.registros:
            print("Advertencia: No hay registros para guardar")
            return

        # Convertir registros a DataFrame
        datos = [asdict(r) for r in self.registros]
        df = pd.DataFrame(datos)

        # Asegurar que el directorio existe
        ruta.parent.mkdir(parents=True, exist_ok=True)

        # Guardar como Parquet
        df.to_parquet(ruta, engine='pyarrow', compression='snappy', index=False)
        print(f"Datos guardados en: {ruta}")
        print(f"Registros: {len(df)} dias, Columnas: {len(df.columns)}")

    def obtenerDataframe(self) -> pd.DataFrame:
        """Retorna los registros como DataFrame de pandas."""
        if not self.registros:
            return pd.DataFrame()

        datos = [asdict(r) for r in self.registros]
        return pd.DataFrame(datos)

    def resumenEstadistico(self) -> Dict[str, Any]:
        """Genera un resumen estadistico de las metricas."""
        df = self.obtenerDataframe()

        if df.empty:
            return {}

        resumen = {
            'periodo': {
                'diasTotales': len(df),
                'diaInicial': int(df['dia'].min()),
                'diaFinal': int(df['dia'].max())
            },
            'inventarios': {
                'hubGranelPromedio': float(df['invHubGranel'].mean()),
                'hubGranelMin': float(df['invHubGranel'].min()),
                'hubGranelMax': float(df['invHubGranel'].max()),
                'hubEnvasadoPromedio': float(df['invHubEnvasado'].mean()),
                'hubEnvasadoMin': float(df['invHubEnvasado'].min()),
                'hubEnvasadoMax': float(df['invHubEnvasado'].max()),
                'cdesPromedio': float(df['invCdes'].mean()),
                'cdesMin': float(df['invCdes'].min()),
                'cdesMax': float(df['invCdes'].max())
            },
            'satisfaccion': {
                'granelPromedioPct': float(df['satisfaccionGranel'].mean() * 100),
                'envasadoPromedioPct': float(df['satisfaccionEnvasado'].mean() * 100),
                'globalPromedioPct': float(
                    ((df['satisfaccionGranel'] + df['satisfaccionEnvasado']) / 2).mean() * 100
                )
            },
            'desabastecimientos': {
                'diasDesabastecimientoGranel': int(df['desabastecimientoGranel'].sum()),
                'diasDesabastecimientoEnvasado': int(df['desabastecimientoEnvasado'].sum()),
                'diasConAlgunDesabastecimiento': int(
                    (df['desabastecimientoGranel'] | df['desabastecimientoEnvasado']).sum()
                )
            },
            'quiebresStock': {
                'hubGranel': int(df['quiebreStockHubGranel'].sum()),
                'hubEnvasado': int(df['quiebreStockHubEnvasado'].sum()),
                'cdes': int(df['quiebreStockCdes'].sum())
            },
            'transporte': {
                'viajesTotales': int(df['viajesCompletados'].sum()),
                'camionesPromedioEnRuta': float(df['camionesEnRuta'].mean())
            }
        }

        return resumen
