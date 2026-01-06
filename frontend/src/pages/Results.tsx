import { useParams, useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { ArrowLeft, Download, TrendingUp, Package, AlertTriangle, Activity, BarChart3, Waves, Battery, Truck, XCircle, MapPin, GitBranch } from "lucide-react"
import { api } from "@/lib/api"
import type { Simulacion, Resultado } from "@/types"
import { toPng } from "html-to-image"
import { useRef, useState } from "react"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ReferenceLine,
} from "recharts"

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

export default function Results() {
  const { simulacionId } = useParams<{ simulacionId: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState("overview")

  const grafico1Ref = useRef<HTMLDivElement>(null)
  const grafico2Ref = useRef<HTMLDivElement>(null)
  const grafico3Ref = useRef<HTMLDivElement>(null)
  const grafico4Ref = useRef<HTMLDivElement>(null)
  const grafico5Ref = useRef<HTMLDivElement>(null)
  const grafico6Ref = useRef<HTMLDivElement>(null)
  const grafico7Ref = useRef<HTMLDivElement>(null)
  const grafico8Ref = useRef<HTMLDivElement>(null)

  const exportarGrafico = async (ref: React.RefObject<HTMLDivElement>, nombre: string) => {
    if (ref.current) {
      const dataUrl = await toPng(ref.current, {
        quality: 1.0,
        pixelRatio: 3,
        backgroundColor: '#ffffff'
      })
      const link = document.createElement('a')
      link.download = `${nombre}.png`
      link.href = dataUrl
      link.click()
    }
  }

  const exportarGraficos = async () => {
    const refs = [grafico1Ref, grafico2Ref, grafico3Ref, grafico4Ref, grafico5Ref, grafico6Ref, grafico7Ref, grafico8Ref]
    const nombres = [
      "inventario_demanda",
      "demanda_satisfecha",
      "autonomia",
      "reabastecimiento",
      "quiebres_stock",
      "ruta_bloqueada",
      "pedidos_transito",
      "distribucion_inventario"
    ]

    for (let i = 0; i < refs.length; i++) {
      if (refs[i].current) {
        const dataUrl = await toPng(refs[i].current, {
          quality: 1.0,
          pixelRatio: 3,
          backgroundColor: '#ffffff'
        })
        const link = document.createElement('a')
        link.download = `grafico${i + 1}_${nombres[i]}.png`
        link.href = dataUrl
        link.click()
        await new Promise(resolve => setTimeout(resolve, 300))
      }
    }
  }

  const { data: simulacion, isLoading: simLoading } = useQuery({
    queryKey: ["simulacion", simulacionId],
    queryFn: async () => {
      const response = await api.get<Simulacion>(`/simulaciones/${simulacionId}`)
      return response.data
    },
    enabled: !!simulacionId,
  })

  const { data: resultados, isLoading: resLoading } = useQuery({
    queryKey: ["resultados", simulacionId],
    queryFn: async () => {
      const response = await api.get<Resultado>(`/simulaciones/${simulacionId}/resultados`)
      return response.data
    },
    enabled: !!simulacionId && simulacion?.estado === "completed",
  })

  const { data: seriesData, isLoading: seriesLoading } = useQuery({
    queryKey: ["series-temporales", simulacionId],
    queryFn: async () => {
      const response = await api.get<{ series_temporales: SeriesTemporal[] }>(
        `/simulaciones/${simulacionId}/series-temporales`
      )
      return response.data.series_temporales
    },
    enabled: !!simulacionId && simulacion?.estado === "completed",
  })

  if (simLoading) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="h-12 w-12 text-neutral-400 animate-spin mx-auto mb-3" />
          <p className="text-neutral-600">Cargando simulación...</p>
        </div>
      </div>
    )
  }

  if (!simulacion) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-neutral-600 mb-4">Simulación no encontrada</p>
          <button onClick={() => navigate("/")} className="btn btn-primary">
            Volver al Dashboard
          </button>
        </div>
      </div>
    )
  }

  if (simulacion.estado === "running") {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="card p-8 max-w-md">
          <Activity className="h-12 w-12 text-slate-600 animate-pulse mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-neutral-900 mb-2 text-center">
            Simulación en Ejecución
          </h2>
          <p className="text-neutral-500 text-center">
            La simulación está procesándose. Por favor espera.
          </p>
        </div>
      </div>
    )
  }

  if (simulacion.estado === "failed") {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="card p-8 max-w-md">
          <AlertTriangle className="h-12 w-12 text-slate-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-neutral-900 mb-2 text-center">
            Simulación Fallida
          </h2>
          <p className="text-slate-600 text-center mb-4">{simulacion.error_mensaje}</p>
          <button onClick={() => navigate("/")} className="btn btn-secondary w-full">
            Volver al Dashboard
          </button>
        </div>
      </div>
    )
  }

  const isLoading = resLoading || seriesLoading

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <header className="h-16 bg-white border-b flex items-center sticky top-0 z-10">
        <div className="w-full max-w-7xl mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate("/")} className="btn btn-secondary text-sm">
              <ArrowLeft className="h-4 w-4" />
              Volver
            </button>
            <div>
              <h1 className="text-base font-semibold text-neutral-900">
                Resultados de Simulación #{simulacionId}
              </h1>
              <p className="text-xs text-neutral-500">
                {new Date(simulacion.ejecutada_en).toLocaleString("es-CL")}
              </p>
            </div>
          </div>
          <button onClick={exportarGraficos} className="btn btn-secondary text-sm">
            <Download className="h-4 w-4" />
            Exportar
          </button>
        </div>
      </header>

      <main className="w-full max-w-7xl mx-auto px-6 py-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Activity className="h-8 w-8 text-neutral-400 animate-spin" />
            <span className="ml-3 text-neutral-600">Cargando datos...</span>
          </div>
        ) : resultados && seriesData ? (
          <>
            {/* KPIs Principales */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="card p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-lg bg-neutral-100 flex items-center justify-center">
                    <TrendingUp className="h-5 w-5 text-neutral-600" />
                  </div>
                  <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wide">
                    Servicio
                  </span>
                </div>
                <div className="text-3xl font-semibold text-neutral-900">
                  {resultados.nivel_servicio_pct.toFixed(2)}%
                </div>
                <div className="text-sm text-neutral-500 mt-1">Nivel de Servicio</div>
              </div>

              <div className="card p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-lg bg-neutral-100 flex items-center justify-center">
                    <AlertTriangle className="h-5 w-5 text-neutral-600" />
                  </div>
                  <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wide">
                    Quiebres
                  </span>
                </div>
                <div className="text-3xl font-semibold text-neutral-900">
                  {resultados.dias_con_quiebre}
                </div>
                <div className="text-sm text-neutral-500 mt-1">Días con Quiebre</div>
              </div>

              <div className="card p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-lg bg-neutral-100 flex items-center justify-center">
                    <Package className="h-5 w-5 text-neutral-600" />
                  </div>
                  <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wide">
                    Inventario
                  </span>
                </div>
                <div className="text-3xl font-semibold text-neutral-900">
                  {resultados.inventario_promedio_tm.toFixed(1)}
                </div>
                <div className="text-sm text-neutral-500 mt-1">TM Promedio</div>
              </div>

              <div className="card p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-lg bg-neutral-100 flex items-center justify-center">
                    <Activity className="h-5 w-5 text-neutral-600" />
                  </div>
                  <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wide">
                    Autonomía
                  </span>
                </div>
                <div className="text-3xl font-semibold text-neutral-900">
                  {resultados.autonomia_promedio_dias.toFixed(1)}
                </div>
                <div className="text-sm text-neutral-500 mt-1">Días Promedio</div>
              </div>
            </div>

            {/* SECCIÓN DE GRÁFICOS PARA TESIS - ORGANIZADOS CON TABS */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-5 mb-6">
                <TabsTrigger value="overview" className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Vista General
                </TabsTrigger>
                <TabsTrigger value="demanda" className="flex items-center gap-2">
                  <Waves className="h-4 w-4" />
                  Demanda
                </TabsTrigger>
                <TabsTrigger value="reabastecimiento" className="flex items-center gap-2">
                  <Truck className="h-4 w-4" />
                  Reabastecimiento
                </TabsTrigger>
                <TabsTrigger value="disrupciones" className="flex items-center gap-2">
                  <XCircle className="h-4 w-4" />
                  Disrupciones
                </TabsTrigger>
                <TabsTrigger value="analisis" className="flex items-center gap-2">
                  <GitBranch className="h-4 w-4" />
                  Análisis
                </TabsTrigger>
              </TabsList>

              {/* TAB: VISTA GENERAL */}
              <TabsContent value="overview" className="space-y-6">
              {/* 1. Serie Temporal de Inventario y Demanda */}
              <div className="card p-6 relative">
                <button
                  onClick={() => exportarGrafico(grafico1Ref, 'grafico1_inventario_demanda')}
                  className="absolute top-4 right-4 p-2 hover:bg-neutral-100 rounded-lg transition-colors z-10"
                  title="Descargar gráfico"
                >
                  <Download className="h-4 w-4 text-neutral-600" />
                </button>
                <div ref={grafico1Ref}>
                  <h3 className="text-base font-semibold text-neutral-900 mb-4">
                    Inventario y Demanda
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={seriesData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                    <XAxis dataKey="dia" stroke="#737373" fontSize={12} />
                    <YAxis stroke="#737373" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#fff",
                        border: "1px solid #e5e5e5",
                        borderRadius: "8px",
                      }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="inventario"
                      stroke="#6366f1"
                      strokeWidth={2}
                      dot={false}
                      name="Inventario (TM)"
                    />
                    <Line
                      type="monotone"
                      dataKey="demanda"
                      stroke="#737373"
                      strokeWidth={2}
                      dot={false}
                      name="Demanda (TM)"
                    />
                  </LineChart>
                </ResponsiveContainer>
                </div>
              </div>
              </TabsContent>

              {/* TAB: DEMANDA */}
              <TabsContent value="demanda" className="space-y-6">
              {/* 2. Demanda Satisfecha vs Insatisfecha */}
              <Card className="relative border-slate-200 shadow-sm">
                <button
                  onClick={() => exportarGrafico(grafico2Ref, 'grafico2_demanda_satisfecha')}
                  className="absolute top-4 right-4 p-2 hover:bg-neutral-100 rounded-lg transition-colors z-10"
                  title="Descargar gráfico"
                >
                  <Download className="h-4 w-4 text-neutral-600" />
                </button>
                <div ref={grafico2Ref}>
                  <h3 className="text-base font-semibold text-neutral-900 mb-4">
                    Demanda Satisfecha vs Insatisfecha
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={seriesData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                    <XAxis dataKey="dia" stroke="#737373" fontSize={12} />
                    <YAxis stroke="#737373" fontSize={12} />
                    <Tooltip />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="demanda_satisfecha"
                      stackId="1"
                      stroke="#22c55e"
                      fill="#22c55e"
                      fillOpacity={0.6}
                      name="Demanda Satisfecha (TM)"
                    />
                    <Area
                      type="monotone"
                      dataKey={(d: SeriesTemporal) => d.demanda - d.demanda_satisfecha}
                      stackId="1"
                      stroke="#ef4444"
                      fill="#ef4444"
                      fillOpacity={0.6}
                      name="Demanda Insatisfecha (TM)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
                </div>
              </Card>

              {/* 3. Autonomía del Sistema */}
              <Card className="relative border-slate-200 shadow-sm">
                <button onClick={() => exportarGrafico(grafico3Ref, 'grafico3_autonomia')} className="absolute top-4 right-4 p-2 hover:bg-neutral-100 rounded-lg transition-colors z-10" title="Descargar"><Download className="h-4 w-4 text-neutral-600" /></button>
                <div ref={grafico3Ref}>
                  <h3 className="text-base font-semibold text-neutral-900 mb-4">Autonomía del Sistema</h3>
                  <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={seriesData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                    <XAxis dataKey="dia" stroke="#737373" fontSize={12} />
                    <YAxis stroke="#737373" fontSize={12} />
                    <Tooltip />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="dias_autonomia"
                      stroke="#f59e0b"
                      fill="#f59e0b"
                      fillOpacity={0.3}
                      name="Días de Autonomía"
                    />
                    <ReferenceLine
                      y={resultados.autonomia_minima_dias}
                      stroke="#ef4444"
                      strokeDasharray="3 3"
                      label="Mínimo"
                    />
                  </AreaChart>
                </ResponsiveContainer>
                </div>
              </Card>
              </TabsContent>

              {/* TAB: REABASTECIMIENTO */}
              <TabsContent value="reabastecimiento" className="space-y-6">
              {/* 4. Suministros Recibidos */}
              <Card className="relative border-slate-200 shadow-sm">
                <button onClick={() => exportarGrafico(grafico4Ref, 'grafico4_reabastecimiento')} className="absolute top-4 right-4 p-2 hover:bg-neutral-100 rounded-lg transition-colors z-10" title="Descargar"><Download className="h-4 w-4 text-neutral-600" /></button>
                <div ref={grafico4Ref}>
                  <h3 className="text-base font-semibold text-neutral-900 mb-4">Eventos de Reabastecimiento</h3>
                  <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={seriesData.filter((d) => d.suministro_recibido > 0).length > 0 ? seriesData.filter((d) => d.suministro_recibido > 0) : []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                    <XAxis dataKey="dia" stroke="#737373" fontSize={12} />
                    <YAxis stroke="#737373" fontSize={12} />
                    <Tooltip />
                    <Legend />
                    <Bar
                      dataKey="suministro_recibido"
                      fill="#6366f1"
                      name="Suministro Recibido (TM)"
                    />
                  </BarChart>
                </ResponsiveContainer>
                {seriesData.filter((d) => d.suministro_recibido > 0).length === 0 && (
                  <p className="text-center text-sm text-neutral-500 mt-4">
                    No hubo eventos de reabastecimiento durante la simulación
                  </p>
                )}
                </div>
              </Card>

              {/* 7. Pedidos en Tránsito */}
              <Card className="relative border-slate-200 shadow-sm">
                <button onClick={() => exportarGrafico(grafico7Ref, 'grafico7_pedidos_transito')} className="absolute top-4 right-4 p-2 hover:bg-neutral-100 rounded-lg transition-colors z-10" title="Descargar"><Download className="h-4 w-4 text-neutral-600" /></button>
                <div ref={grafico7Ref}>
                  <CardHeader>
                    <CardTitle>Pedidos en Tránsito</CardTitle>
                    <CardDescription>Pedidos pendientes de llegada al hub</CardDescription>
                  </CardHeader>
                  <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={seriesData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                    <XAxis dataKey="dia" stroke="#737373" fontSize={12} />
                    <YAxis stroke="#737373" fontSize={12} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="stepAfter"
                      dataKey="pedidos_pendientes"
                      stroke="#8b5cf6"
                      strokeWidth={2}
                      dot={false}
                      name="Pedidos Pendientes"
                    />
                  </LineChart>
                </ResponsiveContainer>
                  </CardContent>
                </div>
              </Card>
              </TabsContent>

              {/* TAB: DISRUPCIONES */}
              <TabsContent value="disrupciones" className="space-y-6">
              {/* 5. Quiebres de Stock y Bloqueos de Ruta */}
              <div className="grid grid-cols-2 gap-4">
                <Card className="relative border-slate-200 shadow-sm">
                  <button onClick={() => exportarGrafico(grafico5Ref, 'grafico5_quiebres_stock')} className="absolute top-4 right-4 p-2 hover:bg-neutral-100 rounded-lg transition-colors z-10" title="Descargar"><Download className="h-3 w-3 text-neutral-600" /></button>
                  <div ref={grafico5Ref}>
                    <h3 className="text-base font-semibold text-neutral-900 mb-4">Quiebres de Stock</h3>
                    <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={seriesData.filter((d) => d.quiebre_stock).length > 0 ? seriesData.filter((d) => d.quiebre_stock) : []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="dia" stroke="#737373" fontSize={12} />
                      <YAxis stroke="#737373" fontSize={12} />
                      <Tooltip />
                      <Bar dataKey={(d) => 1} fill="#ef4444" name="Quiebre" />
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="mt-4 text-center">
                    <p className="text-2xl font-bold text-neutral-900">
                      {resultados.dias_con_quiebre}
                    </p>
                    <p className="text-sm text-neutral-500">
                      {resultados.probabilidad_quiebre_stock_pct.toFixed(1)}% del tiempo
                    </p>
                  </div>
                  </div>
                </Card>

                <Card className="relative border-slate-200 shadow-sm">
                  <button onClick={() => exportarGrafico(grafico6Ref, 'grafico6_ruta_bloqueada')} className="absolute top-4 right-4 p-2 hover:bg-neutral-100 rounded-lg transition-colors z-10" title="Descargar"><Download className="h-3 w-3 text-neutral-600" /></button>
                  <div ref={grafico6Ref}>
                    <h3 className="text-base font-semibold text-neutral-900 mb-4">Ruta Bloqueada</h3>
                    <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={seriesData.filter((d) => d.ruta_bloqueada).length > 0 ? seriesData.filter((d) => d.ruta_bloqueada) : []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="dia" stroke="#737373" fontSize={12} />
                      <YAxis stroke="#737373" fontSize={12} />
                      <Tooltip />
                      <Bar dataKey={(d) => 1} fill="#f59e0b" name="Bloqueado" />
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="mt-4 text-center">
                    <p className="text-2xl font-bold text-neutral-900">
                      {resultados.dias_bloqueados_total}
                    </p>
                    <p className="text-sm text-neutral-500">
                      {resultados.pct_tiempo_bloqueado.toFixed(1)}% del tiempo
                    </p>
                  </div>
                  </div>
                </Card>
              </div>
              </TabsContent>

              {/* TAB: ANÁLISIS */}
              <TabsContent value="analisis" className="space-y-6">
              {/* 8. Distribución de Inventario */}
              <Card className="relative border-slate-200 shadow-sm">
                <button onClick={() => exportarGrafico(grafico8Ref, 'grafico8_distribucion_inventario')} className="absolute top-4 right-4 p-2 hover:bg-neutral-100 rounded-lg transition-colors z-10" title="Descargar"><Download className="h-4 w-4 text-neutral-600" /></button>
                <div ref={grafico8Ref}>
                  <h3 className="text-base font-semibold text-neutral-900 mb-4">Distribución de Inventario</h3>
                  <ResponsiveContainer width="100%" height={250}>
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                    <XAxis dataKey="dia" stroke="#737373" fontSize={12} name="Día" />
                    <YAxis dataKey="inventario" stroke="#737373" fontSize={12} name="Inventario (TM)" />
                    <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                    <Scatter
                      data={seriesData}
                      fill="#6366f1"
                      fillOpacity={0.6}
                      name="Inventario"
                    />
                    <ReferenceLine
                      y={resultados.inventario_promedio_tm}
                      stroke="#22c55e"
                      strokeDasharray="3 3"
                      label="Promedio"
                    />
                    <ReferenceLine
                      y={resultados.inventario_minimo_tm}
                      stroke="#ef4444"
                      strokeDasharray="3 3"
                      label="Mínimo"
                    />
                  </ScatterChart>
                </ResponsiveContainer>
                </div>
              </Card>

              {/* Tabla de Métricas Detalladas */}
              <Card className="border-slate-200 shadow-sm">
                <h3 className="text-base font-semibold text-neutral-900 mb-4">
                  Métricas Detalladas (21 KPIs)
                </h3>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold text-sm text-neutral-700 mb-3">
                      Inventario
                    </h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Promedio:</span>
                        <span className="font-medium text-neutral-900">
                          {resultados.inventario_promedio_tm.toFixed(1)} TM
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Mínimo:</span>
                        <span className="font-medium text-neutral-900">
                          {resultados.inventario_minimo_tm.toFixed(1)} TM
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Máximo:</span>
                        <span className="font-medium text-neutral-900">
                          {resultados.inventario_maximo_tm.toFixed(1)} TM
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Desv. Estándar:</span>
                        <span className="font-medium text-neutral-900">
                          {resultados.inventario_std_tm.toFixed(1)} TM
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-sm text-neutral-700 mb-3">Demanda</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Total:</span>
                        <span className="font-medium text-neutral-900">
                          {resultados.demanda_total_tm.toFixed(1)} TM
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Satisfecha:</span>
                        <span className="font-medium text-neutral-900">
                          {resultados.demanda_satisfecha_tm.toFixed(1)} TM
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Insatisfecha:</span>
                        <span className="font-medium text-neutral-900">
                          {resultados.demanda_insatisfecha_tm.toFixed(1)} TM
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Promedio Diaria:</span>
                        <span className="font-medium text-neutral-900">
                          {resultados.demanda_promedio_diaria_tm.toFixed(1)} TM/día
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-sm text-neutral-700 mb-3">
                      Disrupciones
                    </h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Total Eventos:</span>
                        <span className="font-medium text-neutral-900">
                          {resultados.disrupciones_totales}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Días Bloqueados:</span>
                        <span className="font-medium text-neutral-900">
                          {resultados.dias_bloqueados_total}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-600">% Tiempo Bloqueado:</span>
                        <span className="font-medium text-neutral-900">
                          {resultados.pct_tiempo_bloqueado.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-sm text-neutral-700 mb-3">Flujo</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Total Recibido:</span>
                        <span className="font-medium text-neutral-900">
                          {resultados.total_recibido_tm.toFixed(1)} TM
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Total Despachado:</span>
                        <span className="font-medium text-neutral-900">
                          {resultados.total_despachado_tm.toFixed(1)} TM
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-600">Duración:</span>
                        <span className="font-medium text-neutral-900">
                          {resultados.dias_simulados} días
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
              </TabsContent>
            </Tabs>
          </>
        ) : null}
      </main>
    </div>
  )
}
