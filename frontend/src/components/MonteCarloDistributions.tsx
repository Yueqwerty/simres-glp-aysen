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
  AreaChart,
  Area,
  LineChart,
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
  const [selectedForTimeSeries, setSelectedForTimeSeries] = useState<number | null>(null)
  const histogramRef = useRef<HTMLDivElement>(null)
  const boxplotRef = useRef<HTMLDivElement>(null)
  const scatterRef = useRef<HTMLDivElement>(null)
  const statsRef = useRef<HTMLDivElement>(null)
  const timeSeriesRef = useRef<HTMLDivElement>(null)
  const autonomiaRef = useRef<HTMLDivElement>(null)
  const probQuiebreRef = useRef<HTMLDivElement>(null)
  const cdfRef = useRef<HTMLDivElement>(null)
  const kpiRef = useRef<HTMLDivElement>(null)
  const icRef = useRef<HTMLDivElement>(null)

  const { data: experiments } = useQuery({
    queryKey: ["experiments"],
    queryFn: async () => {
      const response = await api.get("/monte-carlo/experiments")
      return response.data
    },
  })

  // Query para series temporales agregadas
  const { data: timeSeriesData, isLoading: timeSeriesLoading } = useQuery({
    queryKey: ["mc-time-series", selectedForTimeSeries],
    queryFn: async () => {
      if (!selectedForTimeSeries) return null
      const response = await api.get(`/monte-carlo/experiments/${selectedForTimeSeries}/series-temporales?num_muestras=50`)
      return response.data
    },
    enabled: !!selectedForTimeSeries,
    staleTime: 10 * 60 * 1000, // 10 minutos cache
  })

  // Cargar réplicas de experimentos seleccionados
  const { data: replicasData, isLoading, error, isError } = useQuery({
    queryKey: ["replicas-multiple", selectedExperiments],
    queryFn: async () => {
      if (selectedExperiments.length === 0) return []

      console.log("Cargando réplicas para experimentos:", selectedExperiments)

      const promises = selectedExperiments.map((id) =>
        api.get(`/monte-carlo/experiments/${id}/replicas`)
      )

      const responses = await Promise.all(promises)
      const data = responses.map((r) => r.data) as ExperimentoData[]

      console.log("Datos recibidos:", data.map(d => ({
        id: d.experiment_id,
        nombre: d.experiment_nombre,
        replicas: d.replicas?.length || 0
      })))

      return data
    },
    enabled: selectedExperiments.length > 0,
    retry: 1,
    staleTime: 5 * 60 * 1000, // 5 minutos
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
    const numBins = 6
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

  // Preparar datos para scatter (muestreo para visualización eficiente)
  const prepararScatter = (data: ExperimentoData[]) => {
    if (!data || data.length === 0) return { data: [], colors: [] }

    const colores = ["#7C5BAD", "#4A3666", "#C4B0DC"]
    const scatterData: any[] = []
    const MAX_POINTS_PER_EXPERIMENT = 2000 // Límite para renderizado eficiente

    data.forEach((exp, idx) => {
      // Filtrar réplicas válidas
      const validReplicas = exp.replicas.filter(
        (r) =>
          r.dias_con_quiebre != null &&
          r.nivel_servicio_pct != null &&
          !isNaN(r.dias_con_quiebre) &&
          !isNaN(r.nivel_servicio_pct)
      )

      // Muestrear si hay demasiados puntos
      const replicasToUse =
        validReplicas.length > MAX_POINTS_PER_EXPERIMENT
          ? validReplicas
              .sort(() => Math.random() - 0.5)
              .slice(0, MAX_POINTS_PER_EXPERIMENT)
          : validReplicas

      replicasToUse.forEach((r) => {
        scatterData.push({
          x: r.dias_con_quiebre,
          y: r.nivel_servicio_pct,
          grupo: exp.experiment_nombre,
          color: colores[idx % colores.length],
        })
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
                  <p className="text-slate-600">Cargando réplicas (esto puede tomar unos segundos con 100k+ réplicas)...</p>
                </div>
              </CardContent>
            </Card>
          ) : isError ? (
            <Alert variant="danger">
              <AlertCircle className="h-5 w-5" />
              <AlertTitle>Error al cargar réplicas</AlertTitle>
              <AlertDescription>
                {error instanceof Error ? error.message : "Error desconocido al cargar los datos. Revisa la consola del navegador (F12) para más detalles."}
              </AlertDescription>
            </Alert>
          ) : !replicasData || replicasData.length === 0 ? (
            <Alert variant="warning">
              <AlertCircle className="h-5 w-5" />
              <AlertTitle>Sin datos</AlertTitle>
              <AlertDescription>
                No se encontraron datos para los experimentos seleccionados.
              </AlertDescription>
            </Alert>
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
                <CardContent className="pt-4">
                  <div ref={histogramRef} className="bg-white p-4 max-w-3xl mx-auto">
                    <ResponsiveContainer width="100%" height={280}>
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
                              fill={["#7C5BAD", "#4A3666", "#C4B0DC"][idx % 3]}
                              fillOpacity={0.7}
                              name={exp.experiment_nombre.replace("MC-Autonomia 8.2d - ", "").replace("-100000rep", "").replace("Disrupcion ", "")}
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
                <CardContent className="pt-4">
                  <div ref={boxplotRef} className="bg-white p-4 max-w-3xl mx-auto">
                    <ResponsiveContainer width="100%" height={280}>
                      <ComposedChart data={boxplotData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                        <XAxis dataKey="nombre" stroke="#737373" fontSize={12} />
                        <YAxis stroke="#737373" fontSize={12} domain={[70, 100]} />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="q25" stackId="a" fill="#7C5BAD" fillOpacity={0.3} name="Q25-Q75" />
                        <Bar dataKey={(d: any) => d.q75 - d.q25} stackId="a" fill="#7C5BAD" fillOpacity={0.6} />
                        <Line type="monotone" dataKey="median" stroke="#4A3666" strokeWidth={3} name="Mediana" />
                        <Line type="monotone" dataKey="mean" stroke="#C4B0DC" strokeWidth={2} strokeDasharray="5 5" name="Media" />
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
                <CardContent className="pt-4">
                  <div ref={scatterRef} className="bg-white p-4 max-w-3xl mx-auto">
                    <ResponsiveContainer width="100%" height={300}>
                      <ScatterChart>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                        <XAxis
                          dataKey="x"
                          stroke="#737373"
                          fontSize={11}
                          type="number"
                          domain={['dataMin', 'dataMax']}
                          tickCount={10}
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
                              fill={["#7C5BAD", "#4A3666", "#C4B0DC"][idx % 3]}
                              fillOpacity={0.6}
                              name={exp.experiment_nombre.replace("MC-Autonomia 8.2d - ", "").replace("-100000rep", "").replace("Disrupcion ", "")}
                            />
                          ))}
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* CDF - Función de Distribución Acumulada */}
              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="bg-slate-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Función de Distribución Acumulada (CDF)</CardTitle>
                      <CardDescription>Probabilidad de alcanzar un nivel de servicio dado</CardDescription>
                    </div>
                    <button
                      onClick={() => exportarGrafico(cdfRef, "fig_cdf_nivel_servicio")}
                      className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                      title="Exportar a PNG"
                    >
                      <Download className="h-4 w-4 text-slate-600" />
                    </button>
                  </div>
                </CardHeader>
                <CardContent className="pt-4">
                  <div ref={cdfRef} className="bg-white p-4 max-w-3xl mx-auto">
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart margin={{ top: 20, right: 30, left: 20, bottom: 30 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                        <XAxis
                          type="number"
                          dataKey="x"
                          domain={[70, 100]}
                          stroke="#737373"
                          fontSize={12}
                          label={{ value: "Nivel de Servicio (%)", position: "insideBottom", offset: -10 }}
                        />
                        <YAxis
                          stroke="#737373"
                          fontSize={12}
                          domain={[0, 100]}
                          label={{ value: "Probabilidad Acumulada (%)", angle: -90, position: "insideLeft" }}
                        />
                        <Tooltip formatter={(value: number) => [`${value.toFixed(1)}%`]} />
                        <Legend />
                        <ReferenceLine x={95} stroke="#4A3666" strokeDasharray="5 5" label={{ value: "95%", position: "top", fill: "#4A3666" }} />
                        {replicasData &&
                          replicasData.map((exp, idx) => {
                            const valores = exp.replicas
                              .map((r) => r.nivel_servicio_pct)
                              .filter((v) => v != null && !isNaN(v))
                              .sort((a, b) => a - b)
                            const cdfData = valores.map((v, i) => ({
                              x: v,
                              y: ((i + 1) / valores.length) * 100,
                            }))
                            // Muestrear para rendimiento
                            const sampled = cdfData.filter((_, i) => i % Math.max(1, Math.floor(cdfData.length / 200)) === 0)
                            return (
                              <Line
                                key={exp.experiment_id}
                                data={sampled}
                                type="monotone"
                                dataKey="y"
                                stroke={["#7C5BAD", "#4A3666", "#C4B0DC"][idx % 3]}
                                strokeWidth={2}
                                dot={false}
                                name={exp.experiment_nombre.replace("MC-", "").slice(0, 25)}
                              />
                            )
                          })}
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Comparativo de KPIs */}
              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="bg-slate-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Comparación de Indicadores Clave</CardTitle>
                      <CardDescription>KPIs normalizados por experimento</CardDescription>
                    </div>
                    <button
                      onClick={() => exportarGrafico(kpiRef, "fig_comparativo_kpis")}
                      className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                      title="Exportar a PNG"
                    >
                      <Download className="h-4 w-4 text-slate-600" />
                    </button>
                  </div>
                </CardHeader>
                <CardContent className="pt-4">
                  <div ref={kpiRef} className="bg-white p-4 max-w-3xl mx-auto">
                    <ResponsiveContainer width="100%" height={280}>
                      <BarChart
                        data={estadisticas.map((s) => ({
                          nombre: s.nombre.replace("MC-", "").replace("Autonomia 8.2d - ", "").slice(0, 15),
                          "Nivel Servicio (%)": parseFloat(s.ns_mean),
                          "100 - Quiebres (días)": Math.max(0, 100 - parseFloat(s.quiebres_mean) * 2),
                          "Autonomía (días x10)": parseFloat(s.aut_mean) * 10,
                        }))}
                        margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                        <XAxis
                          dataKey="nombre"
                          stroke="#737373"
                          fontSize={11}
                          angle={-20}
                          textAnchor="end"
                          height={60}
                        />
                        <YAxis stroke="#737373" fontSize={12} domain={[0, 100]} />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="Nivel Servicio (%)" fill="#7C5BAD" />
                        <Bar dataKey="100 - Quiebres (días)" fill="#4A3666" />
                        <Bar dataKey="Autonomía (días x10)" fill="#C4B0DC" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Intervalos de Confianza */}
              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="bg-slate-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Intervalos de Confianza (95%)</CardTitle>
                      <CardDescription>Media ± IC 95% del nivel de servicio</CardDescription>
                    </div>
                    <button
                      onClick={() => exportarGrafico(icRef, "fig_intervalos_confianza")}
                      className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                      title="Exportar a PNG"
                    >
                      <Download className="h-4 w-4 text-slate-600" />
                    </button>
                  </div>
                </CardHeader>
                <CardContent className="pt-4">
                  <div ref={icRef} className="bg-white p-4 max-w-3xl mx-auto">
                    <ResponsiveContainer width="100%" height={260}>
                      <ComposedChart
                        data={replicasData?.map((exp) => {
                          const valores = exp.replicas
                            .map((r) => r.nivel_servicio_pct)
                            .filter((v) => v != null && !isNaN(v))
                          const n = valores.length
                          const mean = valores.reduce((a, b) => a + b, 0) / n
                          const std = Math.sqrt(valores.reduce((a, b) => a + (b - mean) ** 2, 0) / n)
                          const ic95 = 1.96 * (std / Math.sqrt(n))
                          return {
                            nombre: exp.experiment_nombre.replace("MC-", "").replace("Autonomia 8.2d - ", "").slice(0, 15),
                            media: mean,
                            lower: mean - ic95,
                            upper: mean + ic95,
                            ic: ic95,
                          }
                        })}
                        margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                        <XAxis
                          dataKey="nombre"
                          stroke="#737373"
                          fontSize={11}
                          angle={-20}
                          textAnchor="end"
                          height={60}
                        />
                        <YAxis stroke="#737373" fontSize={12} domain={['auto', 'auto']} />
                        <Tooltip
                          formatter={(value: number, name: string) => [
                            `${value.toFixed(3)}%`,
                            name === "media" ? "Media" : name,
                          ]}
                        />
                        <Bar dataKey="lower" stackId="a" fill="transparent" />
                        <Bar dataKey={(d: any) => d.upper - d.lower} stackId="a" fill="#7C5BAD" fillOpacity={0.3} name="IC 95%" />
                        <Line type="monotone" dataKey="media" stroke="#4A3666" strokeWidth={3} dot={{ fill: "#4A3666", r: 6 }} name="Media" />
                      </ComposedChart>
                    </ResponsiveContainer>
                    <p className="text-xs text-center text-slate-500 mt-4">
                      El intervalo de confianza del 95% indica que con 95% de probabilidad, el valor real está dentro del rango mostrado
                    </p>
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
                  <div ref={statsRef} className="bg-white p-4 max-w-3xl mx-auto overflow-x-auto">
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

              {/* Selector de Series Temporales */}
              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="bg-blue-50">
                  <CardTitle>Series Temporales con Bandas de Confianza</CardTitle>
                  <CardDescription>
                    Selecciona un experimento para generar gráficos de series temporales agregadas (50 réplicas)
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="flex flex-wrap gap-2 mb-4">
                    {selectedExperiments.map((expId) => {
                      const exp = experiments?.find((e: any) => e.id === expId)
                      return (
                        <button
                          key={expId}
                          onClick={() => setSelectedForTimeSeries(expId)}
                          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                            selectedForTimeSeries === expId
                              ? "bg-blue-600 text-white"
                              : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                          }`}
                        >
                          {exp?.nombre?.slice(0, 25) || `Exp #${expId}`}
                        </button>
                      )
                    })}
                  </div>

                  {timeSeriesLoading && (
                    <div className="text-center py-12">
                      <div className="animate-spin rounded-full h-12 w-12 border-4 border-slate-300 border-t-blue-600 mx-auto mb-3"></div>
                      <p className="text-slate-600">Generando series temporales (ejecutando 50 réplicas)...</p>
                      <p className="text-sm text-slate-500 mt-1">Esto puede tomar unos segundos</p>
                    </div>
                  )}

                  {timeSeriesData && !timeSeriesLoading && (
                    <div className="space-y-6">
                      {/* Gráfico de Inventario con Bandas - Estilo Tesis */}
                      <div className="bg-white rounded-lg p-6">
                        <div className="flex items-center justify-between mb-6">
                          <h4 className="text-lg font-medium text-gray-900">Nivel de Inventario</h4>
                          <button
                            onClick={() => exportarGrafico(timeSeriesRef, "fig_mc_inventario_bandas")}
                            className="p-2 hover:bg-purple-50 rounded-lg transition-colors"
                          >
                            <Download className="h-4 w-4 text-purple-600" />
                          </button>
                        </div>
                        <div ref={timeSeriesRef} className="bg-white p-4 max-w-3xl mx-auto">
                          <ResponsiveContainer width="100%" height={380}>
                            <AreaChart data={timeSeriesData.series_temporales} margin={{ top: 10, right: 30, left: 10, bottom: 30 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" vertical={false} />
                              <XAxis
                                dataKey="dia"
                                stroke="#1f2937"
                                fontSize={12}
                                tickLine={false}
                                axisLine={{ stroke: '#1f2937' }}
                              />
                              <YAxis
                                stroke="#1f2937"
                                fontSize={12}
                                tickLine={false}
                                axisLine={{ stroke: '#1f2937' }}
                                label={{ value: "Nivel de Inventario", angle: -90, position: "insideLeft", style: { textAnchor: 'middle', fill: '#1f2937' } }}
                              />
                              <Tooltip
                                contentStyle={{
                                  backgroundColor: '#fff',
                                  border: '1px solid #e5e5e5',
                                  borderRadius: '8px',
                                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                                }}
                              />
                              <Legend wrapperStyle={{ paddingTop: '20px' }} />
                              {/* Banda P5-P95 */}
                              <Area
                                type="monotone"
                                dataKey="inventario_p95"
                                stroke="none"
                                fill="#a855f7"
                                fillOpacity={0.15}
                                name="Intervalo P5-P95"
                              />
                              <Area
                                type="monotone"
                                dataKey="inventario_p5"
                                stroke="none"
                                fill="#ffffff"
                                fillOpacity={1}
                                name=""
                                legendType="none"
                              />
                              {/* Línea de punto de reorden */}
                              <ReferenceLine
                                y={391.8}
                                stroke="#a855f7"
                                strokeDasharray="8 4"
                                strokeWidth={2}
                                label={{ value: "R", position: "left", fill: "#a855f7", fontWeight: "bold" }}
                              />
                              {/* Línea media */}
                              <Line
                                type="monotone"
                                dataKey="inventario_mean"
                                stroke="#1f2937"
                                strokeWidth={2}
                                dot={false}
                                name="Inventario Medio"
                              />
                            </AreaChart>
                          </ResponsiveContainer>
                          <div className="flex items-center justify-center gap-8 mt-4 text-sm text-gray-600">
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-0.5 bg-gray-900"></div>
                              <span>Inventario Medio</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-0.5 border-t-2 border-dashed border-purple-500"></div>
                              <span>Punto de Reorden (R)</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="w-4 h-4 bg-purple-200 rounded"></div>
                              <span>Intervalo P5-P95</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Gráfico de Autonomía - Estilo Tesis */}
                      <div className="bg-white rounded-lg p-6">
                        <div className="flex items-center justify-between mb-6">
                          <h4 className="text-lg font-medium text-gray-900">Días de Autonomía</h4>
                          <button
                            onClick={() => exportarGrafico(autonomiaRef, "fig_mc_autonomia_bandas")}
                            className="p-2 hover:bg-purple-50 rounded-lg transition-colors"
                          >
                            <Download className="h-4 w-4 text-purple-600" />
                          </button>
                        </div>
                        <div ref={autonomiaRef} className="bg-white p-4 max-w-3xl mx-auto">
                          <ResponsiveContainer width="100%" height={320}>
                            <AreaChart data={timeSeriesData.series_temporales} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" vertical={false} />
                              <XAxis
                                dataKey="dia"
                                stroke="#1f2937"
                                fontSize={12}
                                tickLine={false}
                                axisLine={{ stroke: '#1f2937' }}
                                label={{ value: "Tiempo", position: "insideBottom", offset: -10, style: { fill: '#1f2937' } }}
                              />
                              <YAxis
                                stroke="#1f2937"
                                fontSize={12}
                                tickLine={false}
                                axisLine={{ stroke: '#1f2937' }}
                                label={{ value: "Días de Autonomía", angle: -90, position: "insideLeft", style: { textAnchor: 'middle', fill: '#1f2937' } }}
                              />
                              <Tooltip
                                contentStyle={{
                                  backgroundColor: '#fff',
                                  border: '1px solid #e5e5e5',
                                  borderRadius: '8px',
                                }}
                              />
                              {/* Banda P5-P95 */}
                              <Area
                                type="monotone"
                                dataKey="dias_autonomia_p95"
                                stroke="none"
                                fill="#c4b5fd"
                                fillOpacity={0.4}
                              />
                              <Area
                                type="monotone"
                                dataKey="dias_autonomia_p5"
                                stroke="none"
                                fill="#ffffff"
                                fillOpacity={1}
                              />
                              {/* Línea media */}
                              <Line
                                type="monotone"
                                dataKey="dias_autonomia_mean"
                                stroke="#1f2937"
                                strokeWidth={2}
                                dot={false}
                              />
                              {/* Línea de autonomía teórica 8.2 */}
                              <ReferenceLine
                                y={8.2}
                                stroke="#a855f7"
                                strokeDasharray="8 4"
                                strokeWidth={2}
                                label={{ value: "8.2d teórico", position: "right", fill: "#a855f7" }}
                              />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      </div>

                      {/* Gráfico de Probabilidad de Quiebre - Estilo Tesis */}
                      <div className="bg-white rounded-lg p-6">
                        <div className="flex items-center justify-between mb-6">
                          <h4 className="text-lg font-medium text-gray-900">Probabilidad de Eventos por Día</h4>
                          <button
                            onClick={() => exportarGrafico(probQuiebreRef, "fig_mc_prob_quiebre")}
                            className="p-2 hover:bg-purple-50 rounded-lg transition-colors"
                          >
                            <Download className="h-4 w-4 text-purple-600" />
                          </button>
                        </div>
                        <div ref={probQuiebreRef} className="bg-white p-4 max-w-3xl mx-auto">
                          <ResponsiveContainer width="100%" height={320}>
                            <AreaChart data={timeSeriesData.series_temporales} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" vertical={false} />
                              <XAxis
                                dataKey="dia"
                                stroke="#1f2937"
                                fontSize={12}
                                tickLine={false}
                                axisLine={{ stroke: '#1f2937' }}
                                label={{ value: "Tiempo", position: "insideBottom", offset: -10, style: { fill: '#1f2937' } }}
                              />
                              <YAxis
                                stroke="#1f2937"
                                fontSize={12}
                                tickLine={false}
                                axisLine={{ stroke: '#1f2937' }}
                                domain={[0, 100]}
                                label={{ value: "Probabilidad (%)", angle: -90, position: "insideLeft", style: { textAnchor: 'middle', fill: '#1f2937' } }}
                              />
                              <Tooltip
                                contentStyle={{
                                  backgroundColor: '#fff',
                                  border: '1px solid #e5e5e5',
                                  borderRadius: '8px',
                                }}
                                formatter={(value: number) => [`${value.toFixed(1)}%`]}
                              />
                              <Legend wrapperStyle={{ paddingTop: '10px' }} />
                              <Area
                                type="monotone"
                                dataKey="prob_quiebre_stock"
                                stroke="#1f2937"
                                fill="#1f2937"
                                fillOpacity={0.2}
                                strokeWidth={2}
                                name="Quiebre de Stock"
                              />
                              <Area
                                type="monotone"
                                dataKey="prob_ruta_bloqueada"
                                stroke="#a855f7"
                                fill="#a855f7"
                                fillOpacity={0.15}
                                strokeWidth={2}
                                strokeDasharray="5 5"
                                name="Ruta Bloqueada"
                              />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      </div>

                      <Alert variant="info">
                        <TrendingUp className="h-5 w-5" />
                        <AlertTitle>Series Temporales Agregadas</AlertTitle>
                        <AlertDescription>
                          Basado en {timeSeriesData.num_muestras} réplicas de la simulación Monte Carlo.
                          Las bandas muestran la variabilidad entre réplicas (percentiles 5-95).
                        </AlertDescription>
                      </Alert>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </>
      )}

      {/* Debug info */}
      {replicasData && replicasData.length > 0 && (
        <div className="text-xs text-slate-500 p-2 bg-slate-100 rounded">
          Debug: {replicasData.map(d => `${d.experiment_nombre}: ${d.replicas?.length || 0} réplicas`).join(", ")}
        </div>
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
