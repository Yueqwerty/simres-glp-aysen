import { useRef } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { GitCompare, ArrowLeft, Download } from "lucide-react"
import { toPng } from "html-to-image"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts"

const COLORS = ["#7C5BAD", "#2563eb", "#059669", "#d97706", "#dc2626"]

export default function Compare() {
  const { ids } = useParams<{ ids: string }>()
  const navigate = useNavigate()
  const invRef = useRef<HTMLDivElement>(null)
  const autRef = useRef<HTMLDivElement>(null)
  const kpiRef = useRef<HTMLDivElement>(null)
  const simIds = ids?.split(",").map(Number) || []

  const { data: sims, isLoading } = useQuery({
    queryKey: ["compare", simIds],
    queryFn: async () => {
      const results = await Promise.all(simIds.map(async (id) => {
        const [sim, series] = await Promise.all([
          api.get(`/simulaciones/${id}`),
          api.get(`/simulaciones/${id}/series-temporales`)
        ])
        return { id, sim: sim.data, series: series.data.series_temporales }
      }))
      return results
    },
    enabled: simIds.length > 0
  })

  const getSimLabel = (sim: any, idx: number) => {
    const configName = sim.sim.configuracion_nombre || `Config ${sim.id}`
    return `${configName}`
  }

  const exportar = async (ref: React.RefObject<HTMLDivElement>, name: string) => {
    if (ref.current) {
      const url = await toPng(ref.current, { quality: 1, pixelRatio: 3, backgroundColor: "#fff" })
      const a = document.createElement("a"); a.download = `${name}.png`; a.href = url; a.click()
    }
  }

  if (isLoading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin h-10 w-10 border-4 border-[#7C5BAD] border-t-transparent rounded-full"></div>
    </div>
  )

  if (!sims?.length) return <div className="p-8">No se encontraron simulaciones</div>

  const invData = sims[0].series.map((s: any, i: number) => {
    const p: any = { dia: s.day }
    sims.forEach((sim, idx) => { p[getSimLabel(sim, idx)] = sim.series[i]?.inventory || 0 })
    return p
  })

  const autData = sims[0].series.map((s: any, i: number) => {
    const p: any = { dia: s.day }
    sims.forEach((sim, idx) => { p[getSimLabel(sim, idx)] = sim.series[i]?.autonomy_days || 0 })
    return p
  })

  const kpiData = sims.map((s, i) => ({
    name: getSimLabel(s, i),
    ns: s.sim.nivel_servicio_pct,
    quiebre: s.sim.dias_con_quiebre,
    aut: s.sim.autonomia_promedio_dias
  }))

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto p-8 max-w-5xl">
        <Button variant="ghost" onClick={() => navigate("/historial")} className="mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />Volver
        </Button>
        <div className="flex items-center gap-3 mb-8">
          <div className="p-3 bg-[#7C5BAD]/10 rounded-xl">
            <GitCompare className="h-6 w-6 text-[#7C5BAD]" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Comparación</h1>
            <p className="text-slate-500 text-sm">Simulaciones: {simIds.map(id => `#${id}`).join(", ")}</p>
          </div>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between bg-slate-50">
              <CardTitle className="text-base">Inventario</CardTitle>
              <button onClick={() => exportar(invRef, "comp_inventario")} className="p-2 hover:bg-slate-200 rounded"><Download className="h-4 w-4" /></button>
            </CardHeader>
            <CardContent className="pt-4">
              <div ref={invRef} className="bg-white p-4 max-w-3xl mx-auto">
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={invData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                    <XAxis dataKey="dia" fontSize={10} label={{ value: "Día", position: "bottom", fontSize: 10 }} />
                    <YAxis fontSize={10} label={{ value: "TM", angle: -90, position: "insideLeft", fontSize: 10 }} />
                    <Tooltip formatter={(v: number) => `${v.toFixed(1)} TM`} />
                    <Legend />
                    {sims.map((s, i) => <Line key={s.id} type="monotone" dataKey={getSimLabel(s, i)} stroke={COLORS[i]} strokeWidth={2} dot={false} />)}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between bg-slate-50">
              <CardTitle className="text-base">Autonomía</CardTitle>
              <button onClick={() => exportar(autRef, "comp_autonomia")} className="p-2 hover:bg-slate-200 rounded"><Download className="h-4 w-4" /></button>
            </CardHeader>
            <CardContent className="pt-4">
              <div ref={autRef} className="bg-white p-4 max-w-3xl mx-auto">
                <ResponsiveContainer width="100%" height={260}>
                  <AreaChart data={autData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                    <XAxis dataKey="dia" fontSize={10} label={{ value: "Día", position: "bottom", fontSize: 10 }} />
                    <YAxis fontSize={10} label={{ value: "Días", angle: -90, position: "insideLeft", fontSize: 10 }} />
                    <Tooltip formatter={(v: number) => `${v.toFixed(1)} días`} />
                    <Legend />
                    {sims.map((s, i) => <Area key={s.id} type="monotone" dataKey={getSimLabel(s, i)} stroke={COLORS[i]} fill={COLORS[i]} fillOpacity={0.15} strokeWidth={2} />)}
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between bg-slate-50">
              <CardTitle className="text-base">KPIs</CardTitle>
              <button onClick={() => exportar(kpiRef, "comp_kpis")} className="p-2 hover:bg-slate-200 rounded"><Download className="h-4 w-4" /></button>
            </CardHeader>
            <CardContent className="pt-4">
              <div ref={kpiRef} className="bg-white p-4 max-w-3xl mx-auto">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={kpiData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                    <XAxis dataKey="name" fontSize={10} />
                    <YAxis fontSize={10} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="ns" fill="#7C5BAD" name="Nivel Servicio (%)" />
                    <Bar dataKey="quiebre" fill="#4A3666" name="Días Quiebre" />
                    <Bar dataKey="aut" fill="#C4B0DC" name="Autonomía (d)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="bg-slate-50"><CardTitle className="text-base">Tabla</CardTitle></CardHeader>
            <CardContent className="pt-4">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-2 bg-slate-50">
                    <th className="text-left py-3 px-3">Simulación</th>
                    <th className="text-right py-3 px-3">NS (%)</th>
                    <th className="text-right py-3 px-3">Quiebres</th>
                    <th className="text-right py-3 px-3">Inv Prom</th>
                    <th className="text-right py-3 px-3">Autonomía</th>
                    <th className="text-right py-3 px-3">Disrupciones</th>
                  </tr>
                </thead>
                <tbody>
                  {sims.map((s, i) => (
                    <tr key={s.id} className="border-b hover:bg-slate-50">
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-2">
                          <span className="inline-block w-3 h-3 rounded-full" style={{backgroundColor: COLORS[i]}}></span>
                          <span className="font-medium">{getSimLabel(s, i)}</span>
                          <span className="text-slate-400 text-xs">#{s.id}</span>
                        </div>
                      </td>
                      <td className="text-right py-3 px-3 font-semibold">{s.sim.nivel_servicio_pct?.toFixed(2)}%</td>
                      <td className="text-right py-3 px-3">{s.sim.dias_con_quiebre}</td>
                      <td className="text-right py-3 px-3">{s.sim.inventario_promedio_tm?.toFixed(1)} TM</td>
                      <td className="text-right py-3 px-3">{s.sim.autonomia_promedio_dias?.toFixed(2)} d</td>
                      <td className="text-right py-3 px-3">{s.sim.disrupciones_totales}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
