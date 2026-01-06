/**
 * Componente de distribuciones Monte Carlo para análisis avanzado
 * Muestra histogramas, boxplots, violin plots y scatter plots
 */

import { useState, useRef } from "react"
import { useQuery } from "@tanstack/react-query"
import { Download, AlertCircle, TrendingUp } from "lucide-react"
import { api } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { toPng } from "html-to-image"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ReferenceLine,
  ComposedChart,
  Line,
  Cell,
} from "recharts"

interface Replica {
  replica_id: number
  nivel_servicio_pct: number
  dias_con_quiebre: number
  inventario_promedio_tm: number
  autonomia_promedio_dias: number
  probabilidad_quiebre_stock_pct: number
}

interface ExperimentoData {
  experiment_id: number
  experiment_nombre: string
  num_replicas: number
  replicas: Replica[]
}

export function MonteCarloDistributions() {
  const [selectedExperiments, setSelectedExperiments] = useState<number[]>([])
  const histogramRef = useRef<HTMLDivElement>(null)
  const boxplotRef = useRef<HTMLDivElement>(null)
  const scatterRef = useRef<HTMLDivElement>(null)
  const statsRef = useRef<HTMLDivElement>(null)

  const { data: experiments } = useQuery({
    queryKey: ["experiments"],
    queryFn: async () => {
      const response = await api.get("/monte-carlo/experiments")
      return response.data
    },
  })

  // Cargar réplicas de experimentos seleccionados
  const { data: replicasData, isLoading } = useQuery({
    queryKey: ["replicas-multiple", selectedExperiments],
    queryFn: async () => {
      if (selectedExperiments.length === 0) return []

      const promises = selectedExperiments.map((id) =>
        api.get(`/monte-carlo/experiments/${id}/replicas`)
      )

      const responses = await Promise.all(promises)
      return responses.map((r) => r.data) as ExperimentoData[]
    },
    enabled: selectedExperiments.length > 0,
  })

  const toggleExperiment = (id: number) => {
    if (selectedExperiments.includes(id)) {
      setSelectedExperiments(selectedExperiments.filter((e) => e !== id))
    } else if (selectedExperiments.length < 3) {
      setSelectedExperiments([...selectedExperiments, id])
    }
  }

  const exportarGrafico = async (ref: React.RefObject<HTMLDivElement>, nombre: string) => {
    if (ref.current) {
      const dataUrl = await toPng(ref.current, {
        quality: 1.0,
        pixelRatio: 3,
        backgroundColor: "#ffffff",
      })
      const link = document.createElement("a")
      link.download = `${nombre}.png`
      link.href = dataUrl
      link.click()
    }
  }

  // Preparar datos para histograma
  const prepararHistograma = (data: ExperimentoData[]) => {
    if (!data || data.length === 0) return []

    // Crear bins para histograma
    const bins: any[] = []
    const numBins = 20
    const minVal = 70
    const maxVal = 100
    const binWidth = (maxVal - minVal) / numBins

    for (let i = 0; i < numBins; i++) {
      const binStart = minVal + i * binWidth
      const binEnd = binStart + binWidth
      const binCenter = (binStart + binEnd) / 2

      const bin: any = { bin: binCenter.toFixed(1) }

      data.forEach((exp) => {
        const count = exp.replicas.filter(
          (r) =>
            r.nivel_servicio_pct != null &&
            !isNaN(r.nivel_servicio_pct) &&
            r.nivel_servicio_pct >= binStart &&
            r.nivel_servicio_pct < binEnd
        ).length

        bin[exp.experiment_nombre] = count
      })

      bins.push(bin)
    }

    return bins
  }

  // Preparar datos para boxplot (simulado con barras)
  const prepararBoxplot = (data: ExperimentoData[]) => {
    if (!data || data.length === 0) return []

    return data.map((exp) => {
      const valores = exp.replicas
        .map((r) => r.nivel_servicio_pct)
        .filter((v) => v != null && !isNaN(v))
        .sort((a, b) => a - b)
      const n = valores.length

      if (n === 0) {
        return {
          nombre: exp.experiment_nombre.replace("MC-", "").slice(0, 15),
          min: 0,
          q25: 0,
          median: 0,
          q75: 0,
          max: 0,
          mean: 0,
        }
      }

      return {
        nombre: exp.experiment_nombre.replace("MC-", "").slice(0, 15),
        min: valores[0],
        q25: valores[Math.floor(n * 0.25)],
        median: valores[Math.floor(n * 0.5)],
        q75: valores[Math.floor(n * 0.75)],
        max: valores[n - 1],
        mean: valores.reduce((a, b) => a + b, 0) / n,
      }
    })
  }

  // Preparar datos para scatter
  const prepararScatter = (data: ExperimentoData[]) => {
    if (!data || data.length === 0) return { data: [], colors: [] }

    const colores = ["#3b82f6", "#10b981", "#f59e0b"]
    const scatterData: any[] = []

    data.forEach((exp, idx) => {
      exp.replicas.forEach((r) => {
        // Solo añadir puntos con valores válidos
        if (
          r.dias_con_quiebre != null &&
          r.nivel_servicio_pct != null &&
          !isNaN(r.dias_con_quiebre) &&
          !isNaN(r.nivel_servicio_pct)
        ) {
          scatterData.push({
            x: r.dias_con_quiebre,
            y: r.nivel_servicio_pct,
            grupo: exp.experiment_nombre,
            color: colores[idx % colores.length],
          })
        }
      })
    })

    return { data: scatterData, colors: colores }
  }

  // Calcular estadísticas
  const calcularEstadisticas = (data: ExperimentoData[]) => {
    if (!data || data.length === 0) return []

    return data.map((exp) => {
      // Filtrar valores válidos (no null, no undefined)
      const ns = exp.replicas
        .map((r) => r.nivel_servicio_pct)
        .filter((v) => v != null && !isNaN(v))
      const quiebres = exp.replicas
        .map((r) => r.dias_con_quiebre)
        .filter((v) => v != null && !isNaN(v))
      const inv = exp.replicas
        .map((r) => r.inventario_promedio_tm)
        .filter((v) => v != null && !isNaN(v))
      const aut = exp.replicas
        .map((r) => r.autonomia_promedio_dias)
        .filter((v) => v != null && !isNaN(v))

      const mean = (arr: number[]) => {
        if (arr.length === 0) return 0
        return arr.reduce((a, b) => a + b, 0) / arr.length
      }
      const std = (arr: number[]) => {
        if (arr.length === 0) return 0
        const m = mean(arr)
        return Math.sqrt(arr.reduce((a, b) => a + (b - m) ** 2, 0) / arr.length)
      }
      const percentile = (arr: number[], p: number) => {
        if (arr.length === 0) return 0
        const sorted = [...arr].sort((a, b) => a - b)
        return sorted[Math.floor(sorted.length * p)]
      }

      return {
        nombre: exp.experiment_nombre,
        n: exp.num_replicas,
        ns_mean: mean(ns).toFixed(2),
        ns_std: std(ns).toFixed(2),
        ns_p5: percentile(ns, 0.05).toFixed(2),
        ns_p95: percentile(ns, 0.95).toFixed(2),
        quiebres_mean: mean(quiebres).toFixed(1),
        inv_mean: mean(inv).toFixed(1),
        aut_mean: mean(aut).toFixed(2),
      }
    })
  }

  const histogramData = replicasData ? prepararHistograma(replicasData) : []
  const boxplotData = replicasData ? prepararBoxplot(replicasData) : []
  const scatterData = replicasData ? prepararScatter(replicasData) : { data: [], colors: [] }
  const estadisticas = replicasData ? calcularEstadisticas(replicasData) : []

  return (
    <div className="space-y-6">
      {/* Selector de experimentos */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="bg-slate-50">
          <CardTitle>Seleccionar Experimentos (máx. 3)</CardTitle>
          <CardDescription>
            Elige hasta 3 experimentos completados para comparar distribuciones
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          {experiments && experiments.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {experiments
                .filter((exp: any) => exp.estado === "completed")
                .map((exp: any) => (
                  <button
                    key={exp.id}
                    onClick={() => toggleExperiment(exp.id)}
                    disabled={
                      !selectedExperiments.includes(exp.id) && selectedExperiments.length >= 3
                    }
                    className={`p-4 border-2 rounded-lg text-left transition-all ${
                      selectedExperiments.includes(exp.id)
                        ? "border-blue-500 bg-blue-50"
                        : "border-slate-200 hover:border-slate-300 bg-white disabled:opacity-50 disabled:cursor-not-allowed"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <Badge variant="success">Completado</Badge>
                      <span className="text-xs text-slate-500">#{exp.id}</span>
                    </div>
                    <h4 className="font-semibold text-slate-900 mb-1 text-sm">{exp.nombre}</h4>
                    <p className="text-xs text-slate-600">
                      {exp.num_replicas?.toLocaleString() || 0} réplicas
                    </p>
                  </button>
                ))}
            </div>
          ) : (
            <Alert variant="warning">
              <AlertCircle className="h-5 w-5" />
              <AlertTitle>No hay experimentos disponibles</AlertTitle>
              <AlertDescription>
                Ejecuta primero un experimento Monte Carlo desde la página Monte Carlo.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Gráficos */}
      {selectedExperiments.length > 0 && (
        <>
          {isLoading ? (
            <Card className="border-slate-200 shadow-sm">
              <CardContent className="pt-12 pb-12 text-center">
                <div className="flex flex-col items-center gap-3">
                  <div className="animate-spin rounded-full h-12 w-12 border-4 border-slate-300 border-t-blue-600"></div>
                  <p className="text-slate-600">Cargando réplicas...</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Histograma */}
              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="bg-slate-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Distribución del Nivel de Servicio</CardTitle>
                      <CardDescription>Histogramas comparativos</CardDescription>
                    </div>
                    <button
                      onClick={() => exportarGrafico(histogramRef, "fig_histograma_nivel_servicio")}
                      className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                      title="Exportar a PNG"
                    >
                      <Download className="h-4 w-4 text-slate-600" />
                    </button>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  <div ref={histogramRef} className="bg-white p-6">
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={histogramData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                        <XAxis
                          dataKey="bin"
                          stroke="#737373"
                          fontSize={12}
                          label={{ value: "Nivel de Servicio (%)", position: "insideBottom", offset: -5 }}
                        />
                        <YAxis
                          stroke="#737373"
                          fontSize={12}
                          label={{ value: "Frecuencia", angle: -90, position: "insideLeft" }}
                        />
                        <Tooltip />
                        <Legend />
                        {replicasData &&
                          replicasData.map((exp, idx) => (
                            <Bar
                              key={exp.experiment_id}
                              dataKey={exp.experiment_nombre}
                              fill={["#3b82f6", "#10b981", "#f59e0b"][idx % 3]}
                              fillOpacity={0.7}
                            />
                          ))}
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Boxplot Stats */}
              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="bg-slate-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Estadísticas de Nivel de Servicio</CardTitle>
                      <CardDescription>Métricas de dispersión por experimento</CardDescription>
                    </div>
                    <button
                      onClick={() => exportarGrafico(boxplotRef, "fig_boxplot_nivel_servicio")}
                      className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                      title="Exportar a PNG"
                    >
                      <Download className="h-4 w-4 text-slate-600" />
                    </button>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  <div ref={boxplotRef} className="bg-white p-6">
                    <ResponsiveContainer width="100%" height={400}>
                      <ComposedChart data={boxplotData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                        <XAxis dataKey="nombre" stroke="#737373" fontSize={12} />
                        <YAxis stroke="#737373" fontSize={12} domain={[70, 100]} />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="q25" stackId="a" fill="#3b82f6" fillOpacity={0.3} name="Q25-Q75" />
                        <Bar dataKey={(d: any) => d.q75 - d.q25} stackId="a" fill="#3b82f6" fillOpacity={0.6} />
                        <Line type="monotone" dataKey="median" stroke="#ef4444" strokeWidth={3} name="Mediana" />
                        <Line type="monotone" dataKey="mean" stroke="#10b981" strokeWidth={2} strokeDasharray="5 5" name="Media" />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Scatter Plot */}
              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="bg-slate-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Relación: Nivel de Servicio vs Quiebres</CardTitle>
                      <CardDescription>Scatter plot de todas las réplicas</CardDescription>
                    </div>
                    <button
                      onClick={() => exportarGrafico(scatterRef, "fig_scatter_ns_quiebres")}
                      className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                      title="Exportar a PNG"
                    >
                      <Download className="h-4 w-4 text-slate-600" />
                    </button>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  <div ref={scatterRef} className="bg-white p-6">
                    <ResponsiveContainer width="100%" height={400}>
                      <ScatterChart>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                        <XAxis
                          dataKey="x"
                          stroke="#737373"
                          fontSize={12}
                          label={{ value: "Días con Quiebre", position: "insideBottom", offset: -5 }}
                        />
                        <YAxis
                          dataKey="y"
                          stroke="#737373"
                          fontSize={12}
                          label={{ value: "Nivel de Servicio (%)", angle: -90, position: "insideLeft" }}
                        />
                        <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                        <Legend />
                        {replicasData &&
                          replicasData.map((exp, idx) => (
                            <Scatter
                              key={exp.experiment_id}
                              data={scatterData.data.filter((d: any) => d.grupo === exp.experiment_nombre)}
                              fill={scatterData.colors[idx % 3]}
                              fillOpacity={0.6}
                              name={exp.experiment_nombre}
                            />
                          ))}
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Tabla de Estadísticas */}
              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="bg-slate-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Estadísticas Descriptivas</CardTitle>
                      <CardDescription>Métricas resumidas por experimento</CardDescription>
                    </div>
                    <button
                      onClick={() => exportarGrafico(statsRef, "tabla_estadisticas_mc")}
                      className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                      title="Exportar a PNG"
                    >
                      <Download className="h-4 w-4 text-slate-600" />
                    </button>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  <div ref={statsRef} className="bg-white p-6 overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b-2 border-slate-300">
                          <th className="text-left py-2 px-3">Experimento</th>
                          <th className="text-right py-2 px-3">n</th>
                          <th className="text-right py-2 px-3">NS Media (%)</th>
                          <th className="text-right py-2 px-3">NS Desv.</th>
                          <th className="text-right py-2 px-3">NS P5 (%)</th>
                          <th className="text-right py-2 px-3">NS P95 (%)</th>
                          <th className="text-right py-2 px-3">Quiebres Med.</th>
                          <th className="text-right py-2 px-3">Inv. Med. (TM)</th>
                          <th className="text-right py-2 px-3">Aut. Med. (d)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {estadisticas.map((stat, idx) => (
                          <tr key={idx} className="border-b border-slate-200">
                            <td className="py-2 px-3 font-medium">{stat.nombre.slice(0, 20)}...</td>
                            <td className="text-right py-2 px-3">{stat.n.toLocaleString()}</td>
                            <td className="text-right py-2 px-3 font-semibold">{stat.ns_mean}</td>
                            <td className="text-right py-2 px-3">{stat.ns_std}</td>
                            <td className="text-right py-2 px-3">{stat.ns_p5}</td>
                            <td className="text-right py-2 px-3">{stat.ns_p95}</td>
                            <td className="text-right py-2 px-3">{stat.quiebres_mean}</td>
                            <td className="text-right py-2 px-3">{stat.inv_mean}</td>
                            <td className="text-right py-2 px-3">{stat.aut_mean}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </>
      )}

      {selectedExperiments.length === 0 && (
        <Alert variant="info">
          <TrendingUp className="h-5 w-5" />
          <AlertTitle>Selecciona experimentos para comenzar</AlertTitle>
          <AlertDescription>
            Elige hasta 3 experimentos Monte Carlo completados arriba para ver sus distribuciones y
            estadísticas comparativas.
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}
