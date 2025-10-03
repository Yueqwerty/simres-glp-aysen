"""
Sistema de monitoreo y logging para la simulación de la cadena de suministro.
Registra métricas diarias en formato Parquet para análisis temporal.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import pandas as pd
from pathlib import Path


@dataclass
class RegistroDiario:
    """Registro de métricas del sistema para un día específico."""
    dia: int

    # Inventarios Hub
    inv_hub_granel: float
    inv_hub_envasado: float

    # Inventarios Red CDEs
    inv_cdes: float

    # Flujos diarios
    flujo_recepcion_hub: float
    flujo_despacho_granel: float
    flujo_despacho_envasado: float
    flujo_envasado_procesado: float
    flujo_reabastecimiento_cdes: float

    # Demanda y satisfacción
    demanda_granel: float
    demanda_envasado: float
    satisfaccion_granel: float
    satisfaccion_envasado: float

    # Transporte
    camiones_en_ruta: int
    viajes_completados: int

    # Eventos
    desabastecimiento_granel: bool
    desabastecimiento_envasado: bool
    quiebre_stock_hub_granel: bool
    quiebre_stock_hub_envasado: bool
    quiebre_stock_cdes: bool


class MonitorSimulacion:
    """Monitor para recolectar y almacenar métricas de la simulación."""

    def __init__(self):
        self.registros: List[RegistroDiario] = []

    def registrar_dia(self, registro: RegistroDiario) -> None:
        """Agrega un registro diario a la colección."""
        self.registros.append(registro)

    def guardar_parquet(self, ruta: Path) -> None:
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
        print(f"OK - Datos guardados en: {ruta}")
        print(f"     Registros: {len(df)} dias, Columnas: {len(df.columns)}")

    def obtener_dataframe(self) -> pd.DataFrame:
        """Retorna los registros como DataFrame de pandas."""
        if not self.registros:
            return pd.DataFrame()

        datos = [asdict(r) for r in self.registros]
        return pd.DataFrame(datos)

    def resumen_estadistico(self) -> Dict[str, Any]:
        """Genera un resumen estadístico de las métricas."""
        df = self.obtener_dataframe()

        if df.empty:
            return {}

        resumen = {
            'periodo': {
                'dias_totales': len(df),
                'dia_inicial': int(df['dia'].min()),
                'dia_final': int(df['dia'].max())
            },
            'inventarios': {
                'hub_granel_promedio': float(df['inv_hub_granel'].mean()),
                'hub_granel_min': float(df['inv_hub_granel'].min()),
                'hub_granel_max': float(df['inv_hub_granel'].max()),
                'hub_envasado_promedio': float(df['inv_hub_envasado'].mean()),
                'hub_envasado_min': float(df['inv_hub_envasado'].min()),
                'hub_envasado_max': float(df['inv_hub_envasado'].max()),
                'cdes_promedio': float(df['inv_cdes'].mean()),
                'cdes_min': float(df['inv_cdes'].min()),
                'cdes_max': float(df['inv_cdes'].max())
            },
            'satisfaccion': {
                'granel_promedio_pct': float(df['satisfaccion_granel'].mean() * 100),
                'envasado_promedio_pct': float(df['satisfaccion_envasado'].mean() * 100),
                'global_promedio_pct': float(
                    ((df['satisfaccion_granel'] + df['satisfaccion_envasado']) / 2).mean() * 100
                )
            },
            'desabastecimientos': {
                'dias_desabastecimiento_granel': int(df['desabastecimiento_granel'].sum()),
                'dias_desabastecimiento_envasado': int(df['desabastecimiento_envasado'].sum()),
                'dias_con_algun_desabastecimiento': int(
                    (df['desabastecimiento_granel'] | df['desabastecimiento_envasado']).sum()
                )
            },
            'quiebres_stock': {
                'hub_granel': int(df['quiebre_stock_hub_granel'].sum()),
                'hub_envasado': int(df['quiebre_stock_hub_envasado'].sum()),
                'cdes': int(df['quiebre_stock_cdes'].sum())
            },
            'transporte': {
                'viajes_totales': int(df['viajes_completados'].sum()),
                'camiones_promedio_en_ruta': float(df['camiones_en_ruta'].mean())
            }
        }

        return resumen