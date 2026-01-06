/**
 * Página de historial de simulaciones.
 */

import { useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { Activity, Calendar, CheckCircle, XCircle, Clock, TrendingUp } from "lucide-react"
import { api } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import type { Simulacion } from "@/types"

export default function History() {
  const navigate = useNavigate()

  const { data: simulaciones, isLoading } = useQuery({
    queryKey: ["simulaciones-all"],
    queryFn: async () => {
      const response = await api.get<Simulacion[]>("/simulaciones/")
      return response.data.sort((a, b) =>
        new Date(b.ejecutada_en).getTime() - new Date(a.ejecutada_en).getTime()
      )
    },
  })

  const getStatusIcon = (estado: string) => {
    switch (estado) {
      case "completed":
        return <CheckCircle className="h-5 w-5 text-slate-700" />
      case "failed":
        return <XCircle className="h-5 w-5 text-slate-600" />
      case "running":
        return <Clock className="h-5 w-5 text-slate-600 animate-pulse" />
      default:
        return <Clock className="h-5 w-5 text-slate-400" />
    }
  }

  const getStatusColor = (estado: string) => {
    switch (estado) {
      case "completed":
        return "bg-white border-slate-200"
      case "failed":
        return "bg-slate-50 border-slate-200"
      case "running":
        return "bg-slate-100 border-slate-300"
      default:
        return "bg-slate-50 border-slate-200"
    }
  }

  const completadas = simulaciones?.filter((s) => s.estado === "completed") || []
  const fallidas = simulaciones?.filter((s) => s.estado === "failed") || []
  const ejecutando = simulaciones?.filter((s) => s.estado === "running") || []

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto p-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 bg-slate-100 rounded-xl">
              <Activity className="h-6 w-6 text-slate-700" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-slate-900">Historial de Simulaciones</h1>
              <p className="text-slate-600 mt-1">Registro completo de todas las ejecuciones realizadas</p>
            </div>
          </div>
        </div>

        {/* Estadísticas */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="border-slate-200 shadow-sm">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Total Simulaciones</p>
                  <p className="text-3xl font-bold text-slate-900">{simulaciones?.length || 0}</p>
                </div>
                <Activity className="h-10 w-10 text-slate-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 shadow-sm">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">Completadas</p>
                  <p className="text-3xl font-semibold text-slate-900">{completadas.length}</p>
                </div>
                <CheckCircle className="h-10 w-10 text-slate-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 shadow-sm">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">En Ejecución</p>
                  <p className="text-3xl font-semibold text-slate-900">{ejecutando.length}</p>
                </div>
                <Clock className="h-10 w-10 text-slate-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 shadow-sm">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">Fallidas</p>
                  <p className="text-3xl font-semibold text-slate-900">{fallidas.length}</p>
                </div>
                <XCircle className="h-10 w-10 text-slate-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Lista de Simulaciones */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="bg-slate-50">
            <CardTitle>Todas las Simulaciones</CardTitle>
            <CardDescription>
              Haga clic en una simulación para ver los resultados detallados
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            {isLoading ? (
              <div className="text-center py-12">
                <Clock className="h-12 w-12 text-slate-300 mx-auto mb-3 animate-pulse" />
                <p className="text-slate-500">Cargando historial...</p>
              </div>
            ) : simulaciones && simulaciones.length > 0 ? (
              <div className="space-y-3">
                {simulaciones.map((sim) => (
                  <Card
                    key={sim.id}
                    className={`${getStatusColor(sim.estado)} hover:shadow-md transition-all cursor-pointer`}
                    onClick={() => sim.estado === "completed" && navigate(`/resultados/${sim.id}`)}
                  >
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          {getStatusIcon(sim.estado)}
                          <div>
                            <h4 className="font-semibold text-slate-900">Simulación #{sim.id}</h4>
                            <div className="flex items-center gap-2 text-sm text-slate-600 mt-1">
                              <Calendar className="h-3 w-3" />
                              <span>{new Date(sim.ejecutada_en).toLocaleString()}</span>
                              {sim.duracion_segundos && (
                                <span className="text-slate-400">
                                  • {sim.duracion_segundos.toFixed(1)}s
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-6">
                          {sim.estado === "completed" && (
                            <>
                              <div className="text-right">
                                <p className="text-xs text-slate-500">Nivel de Servicio</p>
                                <p className="text-lg font-bold text-slate-900">
                                  {sim.nivel_servicio_pct?.toFixed(1)}%
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="text-xs text-slate-500">Días con Quiebre</p>
                                <p className="text-lg font-bold text-slate-900">
                                  {sim.dias_con_quiebre || 0}
                                </p>
                              </div>
                              <Button variant="outline" size="sm">
                                <TrendingUp className="h-4 w-4 mr-2" />
                                Ver Detalles
                              </Button>
                            </>
                          )}
                          {sim.estado === "failed" && sim.error_mensaje && (
                            <p className="text-sm text-slate-600 max-w-md truncate">{sim.error_mensaje}</p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Activity className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-500">No hay simulaciones en el historial</p>
                <p className="text-sm text-slate-400 mt-1">Ejecute su primera simulación para comenzar</p>
                <Button className="mt-4" onClick={() => navigate("/configurar")}>
                  Nueva Simulación
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
