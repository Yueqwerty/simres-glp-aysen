import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { Play, TrendingUp, Package, AlertTriangle, BarChart3, GitCompare, Clock } from "lucide-react"
import { api } from "@/lib/api"
import type { Configuracion, Simulacion } from "@/types"

export default function Dashboard() {
  const navigate = useNavigate()

  const { data: configuraciones } = useQuery({
    queryKey: ["configuraciones"],
    queryFn: async () => {
      const response = await api.get<Configuracion[]>("/configuraciones/")
      return response.data
    },
  })

  const { data: simulaciones } = useQuery({
    queryKey: ["simulaciones-recent"],
    queryFn: async () => {
      const response = await api.get<Simulacion[]>("/simulaciones/")
      return response.data
        .filter((s) => s.estado === "completed")
        .sort((a, b) => new Date(b.ejecutada_en).getTime() - new Date(a.ejecutada_en).getTime())
    },
  })

  const totalSimulaciones = simulaciones?.length || 0
  const nivelServicioPromedio =
    simulaciones && simulaciones.length > 0
      ? simulaciones.reduce((sum, s) => sum + (s.nivel_servicio_pct || 0), 0) / simulaciones.length
      : 0
  const diasQuiebrePromedio =
    simulaciones && simulaciones.length > 0
      ? simulaciones.reduce((sum, s) => sum + (s.dias_con_quiebre || 0), 0) / simulaciones.length
      : 0

  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="h-16 bg-white border-b flex items-center">
        <div className="w-full max-w-7xl mx-auto px-6 flex items-center justify-between">
          <h1 className="text-base font-semibold text-neutral-900">Dashboard</h1>
          <button onClick={() => navigate("/configurar")} className="btn btn-primary text-sm">
            <Play className="h-4 w-4" />
            Nueva Simulación
          </button>
        </div>
      </header>

      <main className="w-full max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-5">
              <div className="w-10 h-10 rounded-lg bg-neutral-100 flex items-center justify-center">
                <Package className="h-5 w-5 text-neutral-600" />
              </div>
              <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wide">Total</span>
            </div>
            <div className="text-3xl font-semibold text-neutral-900">{totalSimulaciones}</div>
            <div className="text-sm text-neutral-500 mt-1">Simulaciones</div>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between mb-5">
              <div className="w-10 h-10 rounded-lg bg-neutral-100 flex items-center justify-center">
                <TrendingUp className="h-5 w-5 text-neutral-600" />
              </div>
              <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wide">Servicio</span>
            </div>
            <div className="text-3xl font-semibold text-neutral-900">{nivelServicioPromedio.toFixed(1)}%</div>
            <div className="text-sm text-neutral-500 mt-1">Nivel promedio</div>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between mb-5">
              <div className="w-10 h-10 rounded-lg bg-neutral-100 flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-neutral-600" />
              </div>
              <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wide">Quiebres</span>
            </div>
            <div className="text-3xl font-semibold text-neutral-900">{diasQuiebrePromedio.toFixed(0)}</div>
            <div className="text-sm text-neutral-500 mt-1">Días promedio</div>
          </div>
        </div>

        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-8">
            <div className="mb-5">
              <h2 className="text-base font-semibold text-neutral-900">Herramientas</h2>
              <p className="text-sm text-neutral-500 mt-0.5">Ejecutar análisis y experimentos</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <button onClick={() => navigate("/configurar")} className="group card card-hover p-5 text-left">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-lg bg-neutral-100 group-hover:bg-neutral-200 flex items-center justify-center transition-colors">
                    <Play className="h-[18px] w-[18px] text-neutral-700" />
                  </div>
                  <h3 className="font-semibold text-neutral-900">Simulación Simple</h3>
                </div>
                <p className="text-sm text-neutral-500 leading-relaxed">Ejecutar análisis con parámetros personalizados</p>
              </button>

              <button onClick={() => navigate("/monte-carlo")} className="group card card-hover p-5 text-left">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-lg bg-neutral-100 group-hover:bg-neutral-200 flex items-center justify-center transition-colors">
                    <BarChart3 className="h-[18px] w-[18px] text-neutral-700" />
                  </div>
                  <h3 className="font-semibold text-neutral-900">Monte Carlo</h3>
                </div>
                <p className="text-sm text-neutral-500 leading-relaxed">Análisis probabilístico con múltiples réplicas</p>
              </button>

              <button onClick={() => navigate("/comparar")} className="group card card-hover p-5 text-left">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-lg bg-neutral-100 group-hover:bg-neutral-200 flex items-center justify-center transition-colors">
                    <GitCompare className="h-[18px] w-[18px] text-neutral-700" />
                  </div>
                  <h3 className="font-semibold text-neutral-900">Comparar</h3>
                </div>
                <p className="text-sm text-neutral-500 leading-relaxed">Análisis comparativo de escenarios</p>
              </button>

              <button onClick={() => navigate("/historial")} className="group card card-hover p-5 text-left">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-lg bg-neutral-100 group-hover:bg-neutral-200 flex items-center justify-center transition-colors">
                    <Clock className="h-[18px] w-[18px] text-neutral-700" />
                  </div>
                  <h3 className="font-semibold text-neutral-900">Historial</h3>
                </div>
                <p className="text-sm text-neutral-500 leading-relaxed">Registro completo de ejecuciones</p>
              </button>
            </div>
          </div>

          <div className="col-span-4 space-y-4">
            <div className="card p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-neutral-900">Configuraciones</h3>
                <span className="text-xs font-medium text-neutral-400">{configuraciones?.length || 0}</span>
              </div>
              {configuraciones && configuraciones.length > 0 ? (
                <div className="space-y-1.5">
                  {configuraciones.slice(0, 5).map((config) => (
                    <button
                      key={config.id}
                      onClick={() => navigate("/configurar", { state: { config } })}
                      className="w-full text-left px-3 py-2 rounded-lg bg-neutral-50 hover:bg-neutral-100 transition-colors"
                    >
                      <div className="font-medium text-sm text-neutral-900 truncate">{config.nombre}</div>
                      <div className="text-xs text-neutral-500 mt-0.5">{config.parametros.capacidad_hub_tm} TM</div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-center py-10 text-sm text-neutral-400">Sin configuraciones</div>
              )}
            </div>

            <div className="card p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-neutral-900">Recientes</h3>
                <span className="text-xs font-medium text-neutral-400">{simulaciones?.slice(0, 5).length || 0}</span>
              </div>
              {simulaciones && simulaciones.length > 0 ? (
                <div className="space-y-1.5">
                  {simulaciones.slice(0, 5).map((sim) => (
                    <button
                      key={sim.id}
                      onClick={() => navigate(`/resultados/${sim.id}`)}
                      className="w-full text-left px-3 py-2 rounded-lg bg-neutral-50 hover:bg-neutral-100 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm text-neutral-900">#{sim.id}</span>
                        <span className="text-xs font-semibold text-neutral-700">{sim.nivel_servicio_pct?.toFixed(1)}%</span>
                      </div>
                      <div className="text-xs text-neutral-500 mt-0.5">
                        {new Date(sim.ejecutada_en).toLocaleDateString('es-CL', { day: 'numeric', month: 'short' })}
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-center py-10 text-sm text-neutral-400">Sin simulaciones</div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
