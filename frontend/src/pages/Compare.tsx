/**
 * Página de comparación de escenarios.
 */

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { GitCompare, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type { Simulacion } from "@/types"

export default function Compare() {
  const [selectedSims, setSelectedSims] = useState<number[]>([])

  const { data: simulaciones } = useQuery({
    queryKey: ["simulaciones-all"],
    queryFn: async () => {
      const response = await api.get<Simulacion[]>("/simulaciones/")
      return response.data.filter((s) => s.estado === "completed")
    },
  })

  const toggleSimulation = (id: number) => {
    if (selectedSims.includes(id)) {
      setSelectedSims(selectedSims.filter((s) => s !== id))
    } else if (selectedSims.length < 4) {
      setSelectedSims([...selectedSims, id])
    }
  }

  const selectedSimulations = simulaciones?.filter((s) => selectedSims.includes(s.id)) || []

  const getComparisonIcon = (val1: number, val2: number, higher_is_better: boolean) => {
    if (Math.abs(val1 - val2) < 0.1) return <Minus className="h-4 w-4 text-slate-400" />
    const isHigher = val1 > val2
    if ((isHigher && higher_is_better) || (!isHigher && !higher_is_better)) {
      return <TrendingUp className="h-4 w-4 text-slate-700" />
    }
    return <TrendingDown className="h-4 w-4 text-slate-500" />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto p-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 bg-slate-100 rounded-xl">
              <GitCompare className="h-6 w-6 text-slate-700" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-slate-900">Comparar Escenarios</h1>
              <p className="text-slate-600 mt-1">Análisis comparativo de simulaciones para toma de decisiones</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Selector de Simulaciones */}
          <Card className="lg:col-span-1 border-slate-200 shadow-sm">
            <CardHeader className="bg-slate-50">
              <CardTitle>Seleccionar Simulaciones</CardTitle>
              <CardDescription>
                Seleccione hasta 4 simulaciones para comparar ({selectedSims.length}/4)
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {simulaciones?.map((sim) => (
                  <div
                    key={sim.id}
                    onClick={() => toggleSimulation(sim.id)}
                    className={`p-3 border rounded-lg cursor-pointer transition-all ${
                      selectedSims.includes(sim.id)
                        ? "border-slate-700 bg-slate-100"
                        : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"
                    }`}
                  >
                    <p className="font-medium text-sm">Simulación #{sim.id}</p>
                    <p className="text-xs text-slate-500">
                      {new Date(sim.ejecutada_en).toLocaleDateString()}
                    </p>
                    <p className="text-xs text-slate-600 mt-1">
                      NS: {sim.nivel_servicio_pct?.toFixed(1)}%
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Tabla Comparativa */}
          <Card className="lg:col-span-3 border-slate-200 shadow-sm">
            <CardHeader className="bg-slate-50">
              <CardTitle>Comparación de KPIs</CardTitle>
              <CardDescription>Análisis lado a lado de métricas clave de rendimiento</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {selectedSimulations.length === 0 ? (
                <div className="text-center py-20">
                  <GitCompare className="h-16 w-16 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-500 text-lg">Seleccione al menos una simulación para comparar</p>
                  <p className="text-sm text-slate-400 mt-2">
                    Use el panel izquierdo para elegir las simulaciones
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-200">
                        <th className="text-left py-3 px-4 font-semibold text-slate-700">Métrica</th>
                        {selectedSimulations.map((sim, idx) => (
                          <th key={sim.id} className="text-center py-3 px-4 font-semibold text-slate-700">
                            <div className="flex flex-col items-center">
                              <span>Sim #{sim.id}</span>
                              {idx > 0 && <span className="text-xs text-slate-500 font-normal">vs Base</span>}
                            </div>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {[
                        {
                          name: "Nivel de Servicio (%)",
                          key: "nivel_servicio_pct",
                          higher_better: true,
                          decimals: 1,
                        },
                        {
                          name: "Prob. Quiebre de Stock (%)",
                          key: "probabilidad_quiebre_stock_pct",
                          higher_better: false,
                          decimals: 1,
                        },
                        { name: "Días con Quiebre", key: "dias_con_quiebre", higher_better: false, decimals: 0 },
                        {
                          name: "Inventario Promedio (TM)",
                          key: "inventario_promedio_tm",
                          higher_better: false,
                          decimals: 1,
                        },
                        {
                          name: "Inventario Mínimo (TM)",
                          key: "inventario_minimo_tm",
                          higher_better: true,
                          decimals: 1,
                        },
                        {
                          name: "Autonomía Promedio (días)",
                          key: "autonomia_promedio_dias",
                          higher_better: true,
                          decimals: 1,
                        },
                        {
                          name: "Demanda Insatisfecha (TM)",
                          key: "demanda_insatisfecha_tm",
                          higher_better: false,
                          decimals: 1,
                        },
                        {
                          name: "Disrupciones Totales",
                          key: "disrupciones_totales",
                          higher_better: false,
                          decimals: 0,
                        },
                      ].map((metric) => (
                        <tr key={metric.key} className="hover:bg-slate-50">
                          <td className="py-3 px-4 font-medium text-slate-700">{metric.name}</td>
                          {selectedSimulations.map((sim, idx) => {
                            const value = (sim as any)[metric.key] as number
                            const baseValue = (selectedSimulations[0] as any)[metric.key] as number
                            return (
                              <td key={sim.id} className="text-center py-3 px-4">
                                <div className="flex items-center justify-center gap-2">
                                  <span className="font-semibold">
                                    {value?.toFixed(metric.decimals) || "N/A"}
                                  </span>
                                  {idx > 0 && getComparisonIcon(value, baseValue, metric.higher_better)}
                                </div>
                                {idx > 0 && baseValue && baseValue !== 0 && (
                                  <span className="text-xs text-slate-500">
                                    {((value - baseValue) / baseValue * 100).toFixed(1)}%
                                  </span>
                                )}
                                {idx > 0 && baseValue === 0 && value !== 0 && (
                                  <span className="text-xs text-slate-500">∞</span>
                                )}
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {selectedSimulations.length >= 2 && (
          <Card className="mt-6 border-slate-200 shadow-sm">
            <CardHeader className="bg-slate-50">
              <CardTitle>Resumen de Diferencias Clave</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white p-4 rounded-lg border border-slate-200">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-2">Mejor Nivel de Servicio</p>
                  <p className="text-3xl font-semibold text-slate-900">
                    Sim #
                    {
                      selectedSimulations.reduce((prev, curr) =>
                        (curr.nivel_servicio_pct || 0) > (prev.nivel_servicio_pct || 0) ? curr : prev
                      ).id
                    }
                  </p>
                  <p className="text-sm text-slate-500 mt-1">
                    {Math.max(...selectedSimulations.map((s) => s.nivel_servicio_pct || 0)).toFixed(1)}%
                  </p>
                </div>

                <div className="bg-white p-4 rounded-lg border border-slate-200">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-2">Menor Quiebre de Stock</p>
                  <p className="text-3xl font-semibold text-slate-900">
                    Sim #
                    {
                      selectedSimulations.reduce((prev, curr) =>
                        (curr.dias_con_quiebre || Infinity) < (prev.dias_con_quiebre || Infinity) ? curr : prev
                      ).id
                    }
                  </p>
                  <p className="text-sm text-slate-500 mt-1">
                    {Math.min(...selectedSimulations.map((s) => s.dias_con_quiebre || 0))} días
                  </p>
                </div>

                <div className="bg-white p-4 rounded-lg border border-slate-200">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-2">Mayor Autonomía</p>
                  <p className="text-3xl font-semibold text-slate-900">
                    Sim #
                    {
                      selectedSimulations.reduce((prev, curr) =>
                        (curr.autonomia_promedio_dias || 0) > (prev.autonomia_promedio_dias || 0) ? curr : prev
                      ).id
                    }
                  </p>
                  <p className="text-sm text-slate-500 mt-1">
                    {Math.max(...selectedSimulations.map((s) => s.autonomia_promedio_dias || 0)).toFixed(1)} días
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
