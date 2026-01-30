import { useRef, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { GitCompare, ArrowLeft, Download, BarChart3, Waves, Truck, XCircle, GitBranch } from "lucide-react"
import { toPng } from "html-to-image"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, ReferenceLine
} from "recharts"

const COLORS = ["#7C5BAD", "#E85D75", "#2D9CDB", "#F2994A", "#27AE60"]

interface SeriesTemporal {
  dia: number
  inventario: number
  demanda: number
  demanda_satisfecha: number
  suministro_recibido: number
  quiebre_stock: boolean
  ruta_bloqueada: boolean
  pedidos_pendientes: number
  dias_autonomia: number
}

export default function Compare() {
  const { ids } = useParams<{ ids: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState("overview")
  const simIds = ids?.split(",").map(Number) || []

  const invQ1Ref = useRef<HTMLDivElement>(null)
  const invQ2Ref = useRef<HTMLDivElement>(null)
  const invQ3Ref = useRef<HTMLDivElement>(null)
  const invQ4Ref = useRef<HTMLDivElement>(null)
  const demandaRef = useRef<HTMLDivElement>(null)
  const demandaSatRef = useRef<HTMLDivElement>(null)
  const autRef = useRef<HTMLDivElement>(null)
  const reabastRef = useRef<HTMLDivElement>(null)
  const pedidosRef = useRef<HTMLDivElement>(null)
  const disrupcionesRef = useRef<HTMLDivElement>(null)
  const kpiRef = useRef<HTMLDivElement>(null)
  const scatterRef = useRef<HTMLDivElement>(null)
  const resumenRef = useRef<HTMLDivElement>(null)

  const invRefs = [invQ1Ref, invQ2Ref, invQ3Ref, invQ4Ref]

  const { data: sims, isLoading } = useQuery({
    queryKey: ["compare", simIds],
    queryFn: async () => {
      const results = await Promise.all(simIds.map(async (id) => {
        const [sim, series] = await Promise.all([
          api.get(`/simulaciones/${id}`),
          api.get(`/simulaciones/${id}/series-temporales`)
        ])
        const seriesTransformed = series.data.series_temporales.map((item: any) => ({
          dia: item.day ?? item.dia,
          inventario: item.inventory ?? item.inventario,
          demanda: item.demand ?? item.demanda,
          demanda_satisfecha: item.satisfied_demand ?? item.demanda_satisfecha,
          suministro_recibido: item.supply_received ?? item.suministro_recibido,
          quiebre_stock: item.stockout ?? item.quiebre_stock,
          ruta_bloqueada: item.route_blocked ?? item.ruta_bloqueada,
          pedidos_pendientes: item.pending_orders ?? item.pedidos_pendientes,
          dias_autonomia: item.autonomy_days ?? item.dias_autonomia,
        })) as SeriesTemporal[]
        return { id, sim: sim.data, series: seriesTransformed }
      }))
      return results
    },
    enabled: simIds.length > 0
  })

  const CONFIG_NAMES: Record<number, string> = {
    29: "Disrupción 7d",
    30: "Disrupción 14d",
    31: "Disrupción 21d",
  }

  const getSimLabel = (sim: any) => {
    const configId = sim.sim.configuracion_id
    return CONFIG_NAMES[configId] || sim.sim.configuracion_nombre || `Sim #${sim.id}`
  }

  const exportar = async (ref: React.RefObject<HTMLDivElement>, name: string) => {
    if (ref.current) {
      const url = await toPng(ref.current, { quality: 1, pixelRatio: 3, backgroundColor: "#fff" })
      const a = document.createElement("a")
      a.download = `comparacion_${name}.png`
      a.href = url
      a.click()
    }
  }

  if (isLoading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin h-10 w-10 border-4 border-[#7C5BAD] border-t-transparent rounded-full"></div>
    </div>
  )

  if (!sims?.length) return <div className="p-8">No se encontraron simulaciones</div>

  const maxDays = Math.max(...sims.map(s => s.series.length))

  const buildOverlayData = (getValue: (s: SeriesTemporal) => number) => {
    return Array.from({ length: maxDays }, (_, i) => {
      const point: any = { dia: i + 1 }
      sims.forEach((sim) => {
        point[getSimLabel(sim)] = sim.series[i] ? getValue(sim.series[i]) : null
      })
      return point
    })
  }

  const invData = buildOverlayData(s => s.inventario)
  const demandaData = buildOverlayData(s => s.demanda)
  const demandaSatData = buildOverlayData(s => s.demanda_satisfecha)
  const autData = buildOverlayData(s => s.dias_autonomia)
  const pedidosData = buildOverlayData(s => s.pedidos_pendientes)

  const reabastData = Array.from({ length: maxDays }, (_, i) => {
    const point: any = { dia: i + 1 }
    let hasData = false
    sims.forEach((sim) => {
      const val = sim.series[i]?.suministro_recibido || 0
      point[getSimLabel(sim)] = val
      if (val > 0) hasData = true
    })
    return hasData ? point : null
  }).filter(Boolean)

  const kpiData = sims.map((s) => ({
    name: getSimLabel(s),
    "Nivel Servicio (%)": s.sim.nivel_servicio_pct,
    "Días Quiebre": s.sim.dias_con_quiebre,
    "Autonomía (días)": s.sim.autonomia_promedio_dias
  }))

  const disrupcionData = sims.map((s) => ({
    name: getSimLabel(s),
    "Días Bloqueados": s.sim.dias_bloqueados_total,
    "Disrupciones": s.sim.disrupciones_totales,
  }))

  const ChartHeader = ({ title, onExport }: { title: string; onExport: () => void }) => (
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
      <button onClick={onExport} className="flex items-center gap-2 px-3 py-1.5 text-sm bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors">
        <Download className="h-4 w-4" />
        Exportar
      </button>
    </div>
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto p-6 max-w-6xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate("/historial")}>
              <ArrowLeft className="h-4 w-4 mr-2" />Volver
            </Button>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[#7C5BAD]/10 rounded-lg">
                <GitCompare className="h-5 w-5 text-[#7C5BAD]" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">Comparación de Simulaciones</h1>
                <div className="flex items-center gap-3 mt-1">
                  {sims.map((s, i) => (
                    <span key={s.id} className="inline-flex items-center gap-1.5 text-sm text-slate-600">
                      <span className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i] }}></span>
                      {getSimLabel(s)}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5 mb-6">
            <TabsTrigger value="overview" className="gap-2">
              <BarChart3 className="h-4 w-4" />General
            </TabsTrigger>
            <TabsTrigger value="demanda" className="gap-2">
              <Waves className="h-4 w-4" />Demanda
            </TabsTrigger>
            <TabsTrigger value="reabastecimiento" className="gap-2">
              <Truck className="h-4 w-4" />Reabast.
            </TabsTrigger>
            <TabsTrigger value="disrupciones" className="gap-2">
              <XCircle className="h-4 w-4" />Disrupciones
            </TabsTrigger>
            <TabsTrigger value="analisis" className="gap-2">
              <GitBranch className="h-4 w-4" />Análisis
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {[0, 1, 2, 3].map((quarter) => {
              const quarterSize = Math.ceil(maxDays / 4)
              const start = quarter * quarterSize
              const end = Math.min((quarter + 1) * quarterSize, maxDays)
              const quarterData = invData.slice(start, end)

              return (
                <Card key={quarter} className="border-slate-200 shadow-sm max-w-3xl mx-auto">
                  <CardContent className="p-8">
                    <div ref={invRefs[quarter]} className="bg-white p-4">
                      <ChartHeader
                        title={`Comparación de Niveles de Inventario (Días ${start + 1}-${end})`}
                        onExport={() => exportar(invRefs[quarter], `inventario_dias_${start + 1}_${end}`)}
                      />
                      <ResponsiveContainer width="100%" height={380}>
                        <AreaChart data={quarterData} margin={{ top: 20, right: 30, left: 20, bottom: 25 }}>
                          <defs>
                            {sims.map((s, i) => (
                              <linearGradient key={`grad-q${quarter}-${s.id}`} id={`colorInvQ${quarter}_${i}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={COLORS[i]} stopOpacity={0.5}/>
                                <stop offset="95%" stopColor={COLORS[i]} stopOpacity={0.1}/>
                              </linearGradient>
                            ))}
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                          <XAxis dataKey="dia" fontSize={13} stroke="#666" label={{ value: "Día de Simulación", position: "insideBottom", offset: -5, fontSize: 14 }} />
                          <YAxis fontSize={13} stroke="#666" label={{ value: "Toneladas Métricas", angle: -90, position: "insideLeft", fontSize: 14 }} />
                          <Tooltip formatter={(v: number) => v != null ? `${v.toFixed(1)} TM` : "N/A"} contentStyle={{ fontSize: 13 }} />
                          <Legend wrapperStyle={{ fontSize: 14, paddingTop: 15 }} />
                          {sims.map((s, i) => (
                            <Area key={s.id} type="monotone" dataKey={getSimLabel(s)} stroke={COLORS[i]} strokeWidth={2.5} fill={`url(#colorInvQ${quarter}_${i})`} connectNulls />
                          ))}
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              )
            })}

            <Card className="border-slate-200 shadow-sm max-w-4xl mx-auto">
              <CardContent className="p-8">
                <div ref={kpiRef} className="bg-white p-4">
                  <ChartHeader title="Comparación de KPIs Principales" onExport={() => exportar(kpiRef, "kpis")} />
                  <ResponsiveContainer width="100%" height={420}>
                    <BarChart data={kpiData} margin={{ top: 20, right: 30, left: 20, bottom: 25 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                      <XAxis dataKey="name" fontSize={13} stroke="#666" />
                      <YAxis fontSize={13} stroke="#666" />
                      <Tooltip contentStyle={{ fontSize: 13 }} />
                      <Legend wrapperStyle={{ fontSize: 14, paddingTop: 15 }} />
                      <Bar dataKey="Nivel Servicio (%)" fill="#7C5BAD" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="Días Quiebre" fill="#E85D75" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="Autonomía (días)" fill="#2D9CDB" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 shadow-sm max-w-4xl mx-auto">
              <CardContent className="p-8">
                <div ref={resumenRef} className="bg-white p-4">
                  <ChartHeader title="Resumen Comparativo" onExport={() => exportar(resumenRef, "resumen_comparativo")} />
                  <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b-2 bg-slate-50">
                      <th className="text-left py-3 px-4">Simulación</th>
                      <th className="text-right py-3 px-4">Nivel Servicio</th>
                      <th className="text-right py-3 px-4">Días Quiebre</th>
                      <th className="text-right py-3 px-4">Inv. Promedio</th>
                      <th className="text-right py-3 px-4">Autonomía</th>
                      <th className="text-right py-3 px-4">Disrupciones</th>
                      <th className="text-right py-3 px-4">% Bloqueado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sims.map((s, i) => (
                      <tr key={s.id} className="border-b hover:bg-slate-50">
                        <td className="py-3 px-4">
                          <span className="inline-flex items-center gap-2">
                            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i] }}></span>
                            <span className="font-medium">{getSimLabel(s)}</span>
                          </span>
                        </td>
                        <td className="text-right py-3 px-4 font-semibold">{s.sim.nivel_servicio_pct?.toFixed(2)}%</td>
                        <td className="text-right py-3 px-4">{s.sim.dias_con_quiebre}</td>
                        <td className="text-right py-3 px-4">{s.sim.inventario_promedio_tm?.toFixed(1)} TM</td>
                        <td className="text-right py-3 px-4">{s.sim.autonomia_promedio_dias?.toFixed(1)} días</td>
                        <td className="text-right py-3 px-4">{s.sim.disrupciones_totales}</td>
                        <td className="text-right py-3 px-4">{s.sim.pct_tiempo_bloqueado?.toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="demanda" className="space-y-6">
            <Card className="border-slate-200 shadow-sm max-w-4xl mx-auto">
              <CardContent className="p-8">
                <div ref={demandaRef} className="bg-white p-4">
                  <ChartHeader title="Comparación de Demanda Diaria (TM)" onExport={() => exportar(demandaRef, "demanda")} />
                  <ResponsiveContainer width="100%" height={420}>
                    <LineChart data={demandaData} margin={{ top: 20, right: 30, left: 20, bottom: 25 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                      <XAxis dataKey="dia" fontSize={13} stroke="#666" label={{ value: "Día de Simulación", position: "insideBottom", offset: -5, fontSize: 14 }} />
                      <YAxis fontSize={13} stroke="#666" label={{ value: "Toneladas Métricas", angle: -90, position: "insideLeft", fontSize: 14 }} />
                      <Tooltip formatter={(v: number) => v != null ? `${v.toFixed(1)} TM` : "N/A"} contentStyle={{ fontSize: 13 }} />
                      <Legend wrapperStyle={{ fontSize: 14, paddingTop: 15 }} />
                      {sims.map((s, i) => (
                        <Line key={s.id} type="monotone" dataKey={getSimLabel(s)} stroke={COLORS[i]} strokeWidth={2.5} dot={false} connectNulls />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 shadow-sm max-w-4xl mx-auto">
              <CardContent className="p-8">
                <div ref={demandaSatRef} className="bg-white p-4">
                  <ChartHeader title="Comparación de Demanda Satisfecha (TM)" onExport={() => exportar(demandaSatRef, "demanda_satisfecha")} />
                  <ResponsiveContainer width="100%" height={420}>
                    <AreaChart data={demandaSatData} margin={{ top: 20, right: 30, left: 20, bottom: 25 }}>
                      <defs>
                        {sims.map((s, i) => (
                          <linearGradient key={`gradSat-${s.id}`} id={`colorSat${i}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={COLORS[i]} stopOpacity={0.35}/>
                            <stop offset="95%" stopColor={COLORS[i]} stopOpacity={0.05}/>
                          </linearGradient>
                        ))}
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                      <XAxis dataKey="dia" fontSize={13} stroke="#666" label={{ value: "Día de Simulación", position: "insideBottom", offset: -5, fontSize: 14 }} />
                      <YAxis fontSize={13} stroke="#666" label={{ value: "Toneladas Métricas", angle: -90, position: "insideLeft", fontSize: 14 }} />
                      <Tooltip formatter={(v: number) => v != null ? `${v.toFixed(1)} TM` : "N/A"} contentStyle={{ fontSize: 13 }} />
                      <Legend wrapperStyle={{ fontSize: 14, paddingTop: 15 }} />
                      {sims.map((s, i) => (
                        <Area key={s.id} type="monotone" dataKey={getSimLabel(s)} stroke={COLORS[i]} strokeWidth={2.5} fill={`url(#colorSat${i})`} connectNulls />
                      ))}
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 shadow-sm max-w-4xl mx-auto">
              <CardContent className="p-8">
                <div ref={autRef} className="bg-white p-4">
                  <ChartHeader title="Comparación de Autonomía del Sistema (días)" onExport={() => exportar(autRef, "autonomia")} />
                  <ResponsiveContainer width="100%" height={420}>
                    <AreaChart data={autData} margin={{ top: 20, right: 30, left: 20, bottom: 25 }}>
                      <defs>
                        {sims.map((s, i) => (
                          <linearGradient key={`gradAut-${s.id}`} id={`colorAut${i}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={COLORS[i]} stopOpacity={0.35}/>
                            <stop offset="95%" stopColor={COLORS[i]} stopOpacity={0.05}/>
                          </linearGradient>
                        ))}
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                      <XAxis dataKey="dia" fontSize={13} stroke="#666" label={{ value: "Día de Simulación", position: "insideBottom", offset: -5, fontSize: 14 }} />
                      <YAxis fontSize={13} stroke="#666" label={{ value: "Días de Autonomía", angle: -90, position: "insideLeft", fontSize: 14 }} />
                      <Tooltip formatter={(v: number) => v ? `${v.toFixed(1)} días` : "N/A"} contentStyle={{ fontSize: 13 }} />
                      <Legend wrapperStyle={{ fontSize: 14, paddingTop: 15 }} />
                      {sims.map((s, i) => (
                        <Area key={s.id} type="monotone" dataKey={getSimLabel(s)} stroke={COLORS[i]} strokeWidth={2.5} fill={`url(#colorAut${i})`} connectNulls />
                      ))}
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="reabastecimiento" className="space-y-6">
            <Card className="border-slate-200 shadow-sm max-w-4xl mx-auto">
              <CardContent className="p-8">
                <div ref={reabastRef} className="bg-white p-4">
                  <ChartHeader title="Comparación de Eventos de Reabastecimiento (TM)" onExport={() => exportar(reabastRef, "reabastecimiento")} />
                  {reabastData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={420}>
                      <BarChart data={reabastData} margin={{ top: 20, right: 30, left: 20, bottom: 25 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                        <XAxis dataKey="dia" fontSize={13} stroke="#666" label={{ value: "Día de Simulación", position: "insideBottom", offset: -5, fontSize: 14 }} />
                        <YAxis fontSize={13} stroke="#666" label={{ value: "Toneladas Métricas", angle: -90, position: "insideLeft", fontSize: 14 }} />
                        <Tooltip formatter={(v: number) => `${v.toFixed(1)} TM`} contentStyle={{ fontSize: 13 }} />
                        <Legend wrapperStyle={{ fontSize: 14, paddingTop: 15 }} />
                        {sims.map((s, i) => (
                          <Bar key={s.id} dataKey={getSimLabel(s)} fill={COLORS[i]} radius={[4, 4, 0, 0]} />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[420px] flex items-center justify-center text-slate-500 text-lg">
                      No hubo eventos de reabastecimiento durante las simulaciones
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 shadow-sm max-w-4xl mx-auto">
              <CardContent className="p-8">
                <div ref={pedidosRef} className="bg-white p-4">
                  <ChartHeader title="Comparación de Pedidos en Tránsito" onExport={() => exportar(pedidosRef, "pedidos_transito")} />
                  <ResponsiveContainer width="100%" height={420}>
                    <LineChart data={pedidosData} margin={{ top: 20, right: 30, left: 20, bottom: 25 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                      <XAxis dataKey="dia" fontSize={13} stroke="#666" label={{ value: "Día de Simulación", position: "insideBottom", offset: -5, fontSize: 14 }} />
                      <YAxis fontSize={13} stroke="#666" label={{ value: "Número de Pedidos", angle: -90, position: "insideLeft", fontSize: 14 }} />
                      <Tooltip contentStyle={{ fontSize: 13 }} />
                      <Legend wrapperStyle={{ fontSize: 14, paddingTop: 15 }} />
                      {sims.map((s, i) => (
                        <Line key={s.id} type="stepAfter" dataKey={getSimLabel(s)} stroke={COLORS[i]} strokeWidth={2.5} dot={false} connectNulls />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="disrupciones" className="space-y-6">
            <Card className="border-slate-200 shadow-sm max-w-4xl mx-auto">
              <CardContent className="p-8">
                <div ref={disrupcionesRef} className="bg-white p-4">
                  <ChartHeader title="Comparación de Disrupciones por Simulación" onExport={() => exportar(disrupcionesRef, "disrupciones")} />
                  <ResponsiveContainer width="100%" height={420}>
                    <BarChart data={disrupcionData} margin={{ top: 20, right: 30, left: 20, bottom: 25 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                      <XAxis dataKey="name" fontSize={13} stroke="#666" />
                      <YAxis fontSize={13} stroke="#666" label={{ value: "Cantidad", angle: -90, position: "insideLeft", fontSize: 14 }} />
                      <Tooltip contentStyle={{ fontSize: 13 }} />
                      <Legend wrapperStyle={{ fontSize: 14, paddingTop: 15 }} />
                      <Bar dataKey="Días Bloqueados" fill="#7C5BAD" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="Disrupciones" fill="#E85D75" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {sims.map((s, i) => (
                <Card key={s.id} className="border-slate-200 shadow-sm">
                  <CardContent className="p-8">
                    <div className="flex items-center gap-3 mb-6">
                      <span className="w-5 h-5 rounded-full" style={{ backgroundColor: COLORS[i] }}></span>
                      <span className="text-xl font-semibold">{getSimLabel(s)}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <p className="text-sm text-slate-500 uppercase tracking-wide">Nivel Servicio</p>
                        <p className="text-3xl font-bold" style={{ color: COLORS[i] }}>{s.sim.nivel_servicio_pct?.toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-500 uppercase tracking-wide">Días Quiebre</p>
                        <p className="text-3xl font-bold text-slate-900">{s.sim.dias_con_quiebre}</p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-500 uppercase tracking-wide">Días Bloqueados</p>
                        <p className="text-3xl font-bold text-slate-900">{s.sim.dias_bloqueados_total}</p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-500 uppercase tracking-wide">% Bloqueado</p>
                        <p className="text-3xl font-bold text-slate-900">{s.sim.pct_tiempo_bloqueado?.toFixed(1)}%</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="analisis" className="space-y-6">
            <Card className="border-slate-200 shadow-sm max-w-4xl mx-auto">
              <CardContent className="p-8">
                <div ref={scatterRef} className="bg-white p-4">
                  <ChartHeader title="Distribución de Niveles de Inventario" onExport={() => exportar(scatterRef, "distribucion")} />
                  <ResponsiveContainer width="100%" height={450}>
                    <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 25 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                      <XAxis dataKey="dia" name="Día" fontSize={13} stroke="#666" label={{ value: "Día de Simulación", position: "insideBottom", offset: -5, fontSize: 14 }} />
                      <YAxis dataKey="inventario" name="Inventario" fontSize={13} stroke="#666" label={{ value: "Toneladas Métricas", angle: -90, position: "insideLeft", fontSize: 14 }} />
                      <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={{ fontSize: 13 }} />
                      <Legend wrapperStyle={{ fontSize: 14, paddingTop: 15 }} />
                      {sims.map((s, i) => (
                        <Scatter
                          key={s.id}
                          name={getSimLabel(s)}
                          data={s.series.map((d, j) => ({ dia: j + 1, inventario: d.inventario }))}
                          fill={COLORS[i]}
                          fillOpacity={0.7}
                        />
                      ))}
                      {sims.map((s, i) => (
                        <ReferenceLine key={`ref-${s.id}`} y={s.sim.inventario_promedio_tm} stroke={COLORS[i]} strokeDasharray="8 4" strokeWidth={2} />
                      ))}
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 shadow-sm max-w-4xl mx-auto">
              <CardHeader className="px-8 pt-6">
                <CardTitle className="text-lg">Métricas Detalladas</CardTitle>
              </CardHeader>
              <CardContent className="px-8 pb-8">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b-2 bg-slate-50">
                      <th className="text-left py-3 px-4">Métrica</th>
                      {sims.map((s, i) => (
                        <th key={s.id} className="text-right py-3 px-4">
                          <span className="inline-flex items-center gap-2">
                            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[i] }}></span>
                            {getSimLabel(s)}
                          </span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="bg-[#7C5BAD]/5"><td colSpan={sims.length + 1} className="py-2 px-4 font-semibold text-[#7C5BAD]">Inventario</td></tr>
                    <tr className="border-b hover:bg-slate-50"><td className="py-2 px-4">Promedio</td>{sims.map((s) => <td key={s.id} className="text-right py-2 px-4">{s.sim.inventario_promedio_tm?.toFixed(1)} TM</td>)}</tr>
                    <tr className="border-b hover:bg-slate-50"><td className="py-2 px-4">Mínimo</td>{sims.map((s) => <td key={s.id} className="text-right py-2 px-4">{s.sim.inventario_minimo_tm?.toFixed(1)} TM</td>)}</tr>
                    <tr className="border-b hover:bg-slate-50"><td className="py-2 px-4">Máximo</td>{sims.map((s) => <td key={s.id} className="text-right py-2 px-4">{s.sim.inventario_maximo_tm?.toFixed(1)} TM</td>)}</tr>
                    <tr className="border-b hover:bg-slate-50"><td className="py-2 px-4">Desv. Estándar</td>{sims.map((s) => <td key={s.id} className="text-right py-2 px-4">{s.sim.inventario_std_tm?.toFixed(1)} TM</td>)}</tr>

                    <tr className="bg-[#7C5BAD]/5"><td colSpan={sims.length + 1} className="py-2 px-4 font-semibold text-[#7C5BAD]">Demanda</td></tr>
                    <tr className="border-b hover:bg-slate-50"><td className="py-2 px-4">Total</td>{sims.map((s) => <td key={s.id} className="text-right py-2 px-4">{s.sim.demanda_total_tm?.toFixed(1)} TM</td>)}</tr>
                    <tr className="border-b hover:bg-slate-50"><td className="py-2 px-4">Satisfecha</td>{sims.map((s) => <td key={s.id} className="text-right py-2 px-4">{s.sim.demanda_satisfecha_tm?.toFixed(1)} TM</td>)}</tr>
                    <tr className="border-b hover:bg-slate-50"><td className="py-2 px-4">Insatisfecha</td>{sims.map((s) => <td key={s.id} className="text-right py-2 px-4">{s.sim.demanda_insatisfecha_tm?.toFixed(1)} TM</td>)}</tr>
                    <tr className="border-b hover:bg-slate-50"><td className="py-2 px-4">Promedio Diaria</td>{sims.map((s) => <td key={s.id} className="text-right py-2 px-4">{s.sim.demanda_promedio_diaria_tm?.toFixed(2)} TM/día</td>)}</tr>

                    <tr className="bg-[#7C5BAD]/5"><td colSpan={sims.length + 1} className="py-2 px-4 font-semibold text-[#7C5BAD]">Autonomía</td></tr>
                    <tr className="border-b hover:bg-slate-50"><td className="py-2 px-4">Promedio</td>{sims.map((s) => <td key={s.id} className="text-right py-2 px-4">{s.sim.autonomia_promedio_dias?.toFixed(2)} días</td>)}</tr>
                    <tr className="border-b hover:bg-slate-50"><td className="py-2 px-4">Mínima</td>{sims.map((s) => <td key={s.id} className="text-right py-2 px-4">{s.sim.autonomia_minima_dias?.toFixed(2)} días</td>)}</tr>

                    <tr className="bg-[#7C5BAD]/5"><td colSpan={sims.length + 1} className="py-2 px-4 font-semibold text-[#7C5BAD]">Flujo</td></tr>
                    <tr className="border-b hover:bg-slate-50"><td className="py-2 px-4">Total Recibido</td>{sims.map((s) => <td key={s.id} className="text-right py-2 px-4">{s.sim.total_recibido_tm?.toFixed(1)} TM</td>)}</tr>
                    <tr className="border-b hover:bg-slate-50"><td className="py-2 px-4">Total Despachado</td>{sims.map((s) => <td key={s.id} className="text-right py-2 px-4">{s.sim.total_despachado_tm?.toFixed(1)} TM</td>)}</tr>
                    <tr className="border-b hover:bg-slate-50"><td className="py-2 px-4">Días Simulados</td>{sims.map((s) => <td key={s.id} className="text-right py-2 px-4">{s.sim.dias_simulados}</td>)}</tr>
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
