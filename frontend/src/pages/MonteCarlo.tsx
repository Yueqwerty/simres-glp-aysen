/**
 * Página de experimentos Monte Carlo.
 */

import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useQuery, useMutation } from "@tanstack/react-query"
import { Play, Loader2, TrendingUp, BarChart3, AlertCircle, X } from "lucide-react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type { Configuracion } from "@/types"

interface MonteCarloExperiment {
  id: number
  configuracion_id: number
  nombre: string
  num_replicas: number
  max_workers: number
  estado: "pending" | "running" | "completed" | "failed"
  progreso: number
  iniciado_en?: string
  completado_en?: string
  duracion_segundos?: number
  resultados_agregados?: {
    nivel_servicio_mean: number
    nivel_servicio_std: number
    nivel_servicio_p50: number
    nivel_servicio_p95: number
    probabilidad_quiebre_stock_mean: number
    inventario_promedio_mean: number
  }
}

export default function MonteCarlo() {
  const navigate = useNavigate()
  const [selectedConfig, setSelectedConfig] = useState<number | null>(null)
  const [numReplicas, setNumReplicas] = useState(1000)
  const [maxWorkers, setMaxWorkers] = useState(11)

  const { data: configuraciones } = useQuery({
    queryKey: ["configuraciones"],
    queryFn: async () => {
      const response = await api.get<Configuracion[]>("/configuraciones/")
      return response.data
    },
  })

  const { data: experiments, refetch: refetchExperiments } = useQuery<MonteCarloExperiment[]>({
    queryKey: ["monte-carlo-experiments"],
    queryFn: async () => {
      const response = await api.get("/monte-carlo/experiments")
      return response.data
    },
  })

  // Polling automático cuando hay experimentos en ejecución
  useEffect(() => {
    const runningExps = experiments?.filter((e) => e.estado === "running") || []

    if (runningExps.length > 0) {
      const interval = setInterval(() => {
        refetchExperiments()
      }, 2000) // Actualizar cada 2 segundos

      return () => clearInterval(interval)
    }
  }, [experiments, refetchExperiments])

  const startExperimentMutation = useMutation({
    mutationFn: async () => {
      if (!selectedConfig) throw new Error("No config selected")
      const response = await api.post("/monte-carlo/start", {
        configuracion_id: selectedConfig,
        num_replicas: numReplicas,
        max_workers: maxWorkers,
      })
      return response.data
    },
    onSuccess: () => {
      refetchExperiments()
    },
  })

  const cancelExperimentMutation = useMutation({
    mutationFn: async (experimentId: number) => {
      await api.delete(`/monte-carlo/experiments/${experimentId}`)
    },
    onSuccess: () => {
      refetchExperiments()
    },
  })

  const handleStartExperiment = () => {
    startExperimentMutation.mutate()
  }

  const runningExperiments = experiments?.filter((e) => e.estado === "running") || []
  const completedExperiments = experiments?.filter((e) => e.estado === "completed") || []

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto p-8 max-w-7xl">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 bg-slate-100 rounded-xl">
              <BarChart3 className="h-6 w-6 text-slate-700" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-slate-900">Experimentos Monte Carlo</h1>
              <p className="text-slate-600 mt-1">
                Ejecute múltiples réplicas en paralelo para análisis estadístico robusto
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-1 border-slate-200 shadow-sm">
            <CardHeader className="bg-slate-50">
              <CardTitle>Nuevo Experimento</CardTitle>
              <CardDescription>Configure y ejecute un experimento Monte Carlo</CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2">Configuración Base</label>
                <select
                  value={selectedConfig || ""}
                  onChange={(e) => setSelectedConfig(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-500"
                >
                  <option value="">Seleccione una configuración...</option>
                  {configuraciones?.map((config) => (
                    <option key={config.id} value={config.id}>
                      {config.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Número de Réplicas: {numReplicas.toLocaleString()}
                </label>
                <input
                  type="range"
                  value={numReplicas}
                  onChange={(e) => setNumReplicas(Number(e.target.value))}
                  min={100}
                  max={100000}
                  step={100}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>100</span>
                  <span>100,000</span>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  Mayor número = mayor precisión estadística, pero toma más tiempo
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Trabajadores Paralelos: {maxWorkers}</label>
                <input
                  type="range"
                  value={maxWorkers}
                  onChange={(e) => setMaxWorkers(Number(e.target.value))}
                  min={1}
                  max={16}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>1</span>
                  <span>16</span>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  Más trabajadores = ejecución más rápida (depende de CPU disponibles)
                </p>
              </div>

              <div className="pt-4 border-t border-slate-200">
                <p className="text-sm text-slate-600 mb-4">
                  Tiempo estimado:{" "}
                  <span className="font-semibold">
                    {(() => {
                      const segundos = (numReplicas * 0.02) / maxWorkers
                      if (segundos < 60) return `~${Math.ceil(segundos)} seg`
                      return `~${Math.ceil(segundos / 60)} min`
                    })()}
                  </span>
                </p>
                <Button
                  onClick={handleStartExperiment}
                  disabled={!selectedConfig || startExperimentMutation.isPending}
                  className="w-full bg-slate-900 hover:bg-slate-800"
                  size="lg"
                >
                  {startExperimentMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Iniciando...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Iniciar Experimento
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="lg:col-span-2 border-slate-200 shadow-sm">
            <CardHeader className="bg-slate-50">
              <CardTitle>Experimentos en Ejecución</CardTitle>
              <CardDescription>
                {runningExperiments.length > 0
                  ? `${runningExperiments.length} experimento(s) en progreso`
                  : "No hay experimentos ejecutándose"}
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {runningExperiments.length === 0 ? (
                <div className="text-center py-12">
                  <AlertCircle className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">No hay experimentos en ejecución</p>
                  <p className="text-sm text-slate-400 mt-1">Configure y ejecute un nuevo experimento</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {runningExperiments.map((exp) => {
                    const replicasCompletadas = Math.floor((exp.progreso / 100) * exp.num_replicas)

                    let tiempoTranscurrido = 0
                    if (exp.iniciado_en) {
                      const iniciado = new Date(exp.iniciado_en + 'Z').getTime()
                      tiempoTranscurrido = Math.max(0, Math.floor((Date.now() - iniciado) / 1000))
                    }

                    let tiempoEstimado: number | null = null
                    if (exp.progreso > 5 && tiempoTranscurrido > 0) {
                      const estimado = Math.floor((tiempoTranscurrido / exp.progreso) * (100 - exp.progreso))
                      if (estimado > 0 && estimado < 86400) {
                        tiempoEstimado = estimado
                      }
                    }

                    return (
                      <Card key={exp.id} className="border-slate-300 bg-slate-50">
                        <CardContent className="pt-6">
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-semibold text-slate-900">{exp.nombre || `Experimento #${exp.id}`}</h4>
                            <div className="flex items-center gap-3">
                              <span className="text-sm text-slate-700 font-medium flex items-center gap-2">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                {exp.progreso}%
                              </span>
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => {
                                  if (window.confirm(`¿Cancelar el experimento "${exp.nombre || `#${exp.id}`}"?`)) {
                                    cancelExperimentMutation.mutate(exp.id)
                                  }
                                }}
                                disabled={cancelExperimentMutation.isPending}
                                className="h-8 w-8 p-0"
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                          <div className="w-full bg-slate-200 rounded-full h-2 mb-3">
                            <div
                              className="bg-slate-700 h-2 rounded-full transition-all duration-500"
                              style={{ width: `${exp.progreso}%` }}
                            />
                          </div>
                          <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                            <div>
                              <span className="text-slate-500">Réplicas:</span>{" "}
                              <span className="font-medium">{replicasCompletadas.toLocaleString()} / {exp.num_replicas.toLocaleString()}</span>
                            </div>
                            <div>
                              <span className="text-slate-500">Trabajadores:</span>{" "}
                              <span className="font-medium">{exp.max_workers}</span>
                            </div>
                            <div>
                              <span className="text-slate-500">Transcurrido:</span>{" "}
                              <span className="font-medium">{Math.floor(tiempoTranscurrido / 60)}m {tiempoTranscurrido % 60}s</span>
                            </div>
                            <div>
                              <span className="text-slate-500">Estimado restante:</span>{" "}
                              <span className="font-medium">
                                {tiempoEstimado !== null
                                  ? `${Math.floor(tiempoEstimado / 60)}m ${tiempoEstimado % 60}s`
                                  : "Calculando..."}
                              </span>
                            </div>
                          </div>
                          <div className="text-xs text-slate-500 text-center">
                            Actualizando en tiempo real...
                          </div>
                        </CardContent>
                      </Card>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="mt-6 border-slate-200 shadow-sm">
          <CardHeader className="bg-slate-50">
            <CardTitle>Experimentos Completados</CardTitle>
            <CardDescription>
              {completedExperiments.length > 0
                ? `${completedExperiments.length} experimento(s) finalizado(s)`
                : "No hay experimentos completados"}
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            {completedExperiments.length === 0 ? (
              <div className="text-center py-12">
                <TrendingUp className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-500">No hay experimentos completados</p>
                <p className="text-sm text-slate-400 mt-1">Los resultados aparecerán aquí al finalizar</p>
              </div>
            ) : (
              <div className="space-y-4">
                {completedExperiments.map((exp) => (
                  <Card
                    key={exp.id}
                    className="border-slate-200 bg-white hover:shadow-md transition-shadow"
                  >
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h4 className="font-semibold text-slate-900">{exp.nombre}</h4>
                          <p className="text-sm text-slate-500">
                            Completado {new Date(exp.completado_en || "").toLocaleString()}
                          </p>
                        </div>
                        <span className="px-3 py-1 bg-slate-100 text-slate-700 text-sm font-medium rounded-full">
                          Completado
                        </span>
                      </div>

                      {exp.resultados_agregados && exp.resultados_agregados.nivel_servicio_mean !== undefined ? (
                        <>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                              <p className="text-slate-500 text-xs mb-1">Nivel de Servicio</p>
                              <p className="text-lg font-bold text-slate-900">
                                {exp.resultados_agregados.nivel_servicio_mean?.toFixed(2) ?? 'N/A'}%
                              </p>
                              <p className="text-xs text-slate-500">
                                ±{exp.resultados_agregados.nivel_servicio_std?.toFixed(2) ?? 'N/A'}%
                              </p>
                            </div>
                            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                              <p className="text-slate-500 text-xs mb-1">Prob. Quiebre</p>
                              <p className="text-lg font-bold text-slate-900">
                                {exp.resultados_agregados.probabilidad_quiebre_stock_mean?.toFixed(2) ?? 'N/A'}%
                              </p>
                              <p className="text-xs text-slate-500">
                                σ={exp.resultados_agregados.probabilidad_quiebre_stock_std?.toFixed(2) ?? 'N/A'}%
                              </p>
                            </div>
                            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                              <p className="text-slate-500 text-xs mb-1">Inv. Promedio</p>
                              <p className="text-lg font-bold text-slate-900">
                                {exp.resultados_agregados.inventario_promedio_mean?.toFixed(1) ?? 'N/A'} TM
                              </p>
                              <p className="text-xs text-slate-500">
                                ±{exp.resultados_agregados.inventario_promedio_std?.toFixed(1) ?? 'N/A'} TM
                              </p>
                            </div>
                            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                              <p className="text-slate-500 text-xs mb-1">Réplicas</p>
                              <p className="text-lg font-bold text-slate-900">{exp.num_replicas?.toLocaleString() ?? 'N/A'}</p>
                              <p className="text-xs text-slate-500">{exp.duracion_segundos?.toFixed(0) ?? 'N/A'}s</p>
                            </div>
                          </div>

                          <details className="mt-4">
                            <summary className="cursor-pointer text-sm text-slate-600 hover:text-slate-900 font-medium flex items-center gap-2">
                              <TrendingUp className="h-4 w-4" />
                              Ver todas las estadísticas
                            </summary>
                            <div className="mt-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
                              <div className="grid grid-cols-2 gap-4 text-xs">
                                <div>
                                  <h5 className="font-semibold text-slate-700 mb-2">Nivel de Servicio (%)</h5>
                                  <div className="space-y-1">
                                    <div className="flex justify-between">
                                      <span className="text-slate-600">Media:</span>
                                      <span className="font-mono font-semibold">{exp.resultados_agregados.nivel_servicio_mean?.toFixed(2) ?? 'N/A'}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-slate-600">Desv. Est:</span>
                                      <span className="font-mono">{exp.resultados_agregados.nivel_servicio_std?.toFixed(2) ?? 'N/A'}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-slate-600">Mín - Máx:</span>
                                      <span className="font-mono">{exp.resultados_agregados.nivel_servicio_min?.toFixed(2) ?? 'N/A'} - {exp.resultados_agregados.nivel_servicio_max?.toFixed(2) ?? 'N/A'}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-slate-600">P50:</span>
                                      <span className="font-mono">{exp.resultados_agregados.nivel_servicio_p50?.toFixed(2) ?? 'N/A'}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-slate-600">P95:</span>
                                      <span className="font-mono">{exp.resultados_agregados.nivel_servicio_p95?.toFixed(2) ?? 'N/A'}</span>
                                    </div>
                                  </div>
                                </div>

                                <div>
                                  <h5 className="font-semibold text-slate-700 mb-2">Días con Quiebre</h5>
                                  <div className="space-y-1">
                                    <div className="flex justify-between">
                                      <span className="text-slate-600">Media:</span>
                                      <span className="font-mono font-semibold">{exp.resultados_agregados.dias_con_quiebre_mean?.toFixed(1) ?? 'N/A'}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-slate-600">Desv. Est:</span>
                                      <span className="font-mono">{exp.resultados_agregados.dias_con_quiebre_std?.toFixed(1) ?? 'N/A'}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-slate-600">P50:</span>
                                      <span className="font-mono">{exp.resultados_agregados.dias_con_quiebre_p50?.toFixed(1) ?? 'N/A'}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-slate-600">P95:</span>
                                      <span className="font-mono">{exp.resultados_agregados.dias_con_quiebre_p95?.toFixed(1) ?? 'N/A'}</span>
                                    </div>
                                  </div>
                                </div>

                                <div>
                                  <h5 className="font-semibold text-slate-700 mb-2">Inventario (TM)</h5>
                                  <div className="space-y-1">
                                    <div className="flex justify-between">
                                      <span className="text-slate-600">Promedio:</span>
                                      <span className="font-mono font-semibold">{exp.resultados_agregados.inventario_promedio_mean?.toFixed(1) ?? 'N/A'}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-slate-600">Desv. Est:</span>
                                      <span className="font-mono">{exp.resultados_agregados.inventario_promedio_std?.toFixed(1) ?? 'N/A'}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-slate-600">Mínimo:</span>
                                      <span className="font-mono">{exp.resultados_agregados.inventario_minimo_mean?.toFixed(1) ?? 'N/A'}</span>
                                    </div>
                                  </div>
                                </div>

                                <div>
                                  <h5 className="font-semibold text-slate-700 mb-2">Autonomía (días)</h5>
                                  <div className="space-y-1">
                                    <div className="flex justify-between">
                                      <span className="text-slate-600">Media:</span>
                                      <span className="font-mono font-semibold">{exp.resultados_agregados.autonomia_promedio_mean?.toFixed(2) ?? 'N/A'}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-slate-600">Desv. Est:</span>
                                      <span className="font-mono">{exp.resultados_agregados.autonomia_promedio_std?.toFixed(2) ?? 'N/A'}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-slate-600">P50:</span>
                                      <span className="font-mono">{exp.resultados_agregados.autonomia_promedio_p50?.toFixed(2) ?? 'N/A'}</span>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </details>
                        </>
                      ) : (
                        <div className="text-center py-4">
                          <AlertCircle className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                          <p className="text-sm font-medium text-slate-700">
                            Experimento completado sin resultados agregados
                          </p>
                          <p className="text-xs text-slate-500 mt-1">
                            Los resultados pueden no haberse calculado correctamente
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
