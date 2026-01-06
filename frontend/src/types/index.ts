/**
 * Tipos TypeScript para la aplicación.
 */

export interface Parametros {
  capacidad_hub_tm: number
  punto_reorden_tm: number
  cantidad_pedido_tm: number
  inventario_inicial_pct: number
  demanda_base_diaria_tm: number
  variabilidad_demanda: number
  amplitud_estacional: number
  dia_pico_invernal: number
  usar_estacionalidad: boolean
  tasa_disrupciones_anual: number
  duracion_disrupcion_min_dias: number
  duracion_disrupcion_mode_dias: number
  duracion_disrupcion_max_dias: number
  lead_time_nominal_dias: number
  duracion_simulacion_dias: number
  semilla_aleatoria: number | null
}

export interface Configuracion {
  id: number
  nombre: string
  descripcion: string | null
  parametros: Parametros
  creada_en: string
  actualizada_en: string
}

export interface ConfiguracionCreate extends Omit<Parametros, "semilla_aleatoria"> {
  nombre: string
  descripcion?: string
  semilla_aleatoria?: number | null
}

export interface Simulacion {
  id: number
  configuracion_id: number
  estado: "running" | "completed" | "failed"
  ejecutada_en: string
  duracion_segundos: number | null
  error_mensaje: string | null
  // KPIs principales (opcionales porque solo están disponibles cuando estado === "completed")
  nivel_servicio_pct?: number
  probabilidad_quiebre_stock_pct?: number
  dias_con_quiebre?: number
  autonomia_promedio_dias?: number
  inventario_promedio_tm?: number
  inventario_minimo_tm?: number
}

export interface Resultado {
  simulacion_id: number
  nivel_servicio_pct: number
  probabilidad_quiebre_stock_pct: number
  dias_con_quiebre: number
  inventario_promedio_tm: number
  inventario_minimo_tm: number
  inventario_maximo_tm: number
  inventario_final_tm: number
  inventario_inicial_tm: number
  inventario_std_tm: number
  autonomia_promedio_dias: number
  autonomia_minima_dias: number
  demanda_total_tm: number
  demanda_satisfecha_tm: number
  demanda_insatisfecha_tm: number
  demanda_promedio_diaria_tm: number
  demanda_maxima_diaria_tm: number
  demanda_minima_diaria_tm: number
  total_recibido_tm: number
  total_despachado_tm: number
  disrupciones_totales: number
  dias_bloqueados_total: number
  pct_tiempo_bloqueado: number
  dias_simulados: number
}
