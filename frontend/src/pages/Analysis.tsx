/**
 * Página de Análisis de Sensibilidad y Límites del Sistema
 * Genera visualizaciones exportables para la tesis
 */

import { useState, useRef } from "react"
import { useQuery } from "@tanstack/react-query"
import { Download, TrendingUp, TrendingDown, AlertCircle, Activity, BarChart3, Zap, Table2 } from "lucide-react"
import { api } from "@/lib/api"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Separator } from "@/components/ui/separator"
import { ANOVATable } from "@/components/ANOVATable"
import { MonteCarloDistributions } from "@/components/MonteCarloDistributions"
import { toPng } from "html-to-image"
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts"

// Datos de análisis de sensibilidad (basados en la tesis)
const sensibilidadCapacidad = [
  { capacidad: 300, nivelServicio: 76.23, quiebres: 86.5 },
  { capacidad: 400, nivelServicio: 83.45, quiebres: 60.4 },
  { capacidad: 500, nivelServicio: 91.67, quiebres: 30.4 },
  { capacidad: 600, nivelServicio: 96.12, quiebres: 14.2 },
  { capacidad: 700, nivelServicio: 98.54, quiebres: 5.3 },
]

const sensibilidadDisrupciones = [
  { duracion: 0, nivelServicio: 99.84, quiebres: 0.58, label: "Sin disr." },
  { duracion: 7, nivelServicio: 84.19, quiebres: 13, label: "Corta" },
  { duracion: 14, nivelServicio: 81.03, quiebres: 24, label: "Media" },
  { duracion: 21, nivelServicio: 78.21, quiebres: 32, label: "Larga" },
  { duracion: 28, nivelServicio: 75.67, quiebres: 42, label: "Muy larga" },
]

const casosExtremos = [
  {
    nombre: "Capacidad Infinita",
    descripcion: "Sin disrupciones, capacidad 100,000 TM",
    nivelServicio: 100.0,
    quiebres: 0,
    estado: "ideal",
    color: "success",
  },
  {
    nombre: "Inventario Cero Bloqueado",
    descripcion: "Sin inventario, ruta bloqueada 365 días",
    nivelServicio: 0.0,
    quiebres: 365,
    estado: "crítico",
    color: "danger",
  },
  {
    nombre: "Sin Disrupciones",
    descripcion: "Configuración base, duración máx = 0 días",
    nivelServicio: 99.84,
    quiebres: 0.58,
    estado: "óptimo",
    color: "success",
  },
  {
    nombre: "Disrupción Permanente",
    descripcion: "Ruta bloqueada todo el año",
    nivelServicio: 0.0,
    quiebres: 365,
    estado: "falla total",
    color: "danger",
  },
]

const escenarios = [
  {
    nombre: "Corta (7 días)",
    nivelServicio: 97.3,
    quiebres: 13,
    autonomia: 4.8,
    disrupciones: 4.0,
    diasBloqueados: 18.5,
  },
  {
    nombre: "Media (14 días)",
    nivelServicio: 94.7,
    quiebres: 24,
    autonomia: 4.8,
    disrupciones: 4.0,
    diasBloqueados: 33.8,
  },
  {
    nombre: "Larga (21 días)",
    nivelServicio: 92.7,
    quiebres: 32,
    autonomia: 4.8,
    disrupciones: 4.0,
    diasBloqueados: 49.7,
  },
]

export default function Analysis() {
  const [activeTab, setActiveTab] = useState("sensibilidad")
  const [selectedExperimentId, setSelectedExperimentId] = useState<number | null>(null)

  // Query para obtener lista de experimentos
  const { data: experiments } = useQuery({
    queryKey: ["experiments"],
    queryFn: async () => {
      const response = await api.get("/monte-carlo/experiments")
      return response.data
    },
  })

  // Query para obtener ANOVA del experimento seleccionado
  const { data: anovaData, isLoading: anovaLoading } = useQuery({
    queryKey: ["anova", selectedExperimentId],
    queryFn: async () => {
      if (!selectedExperimentId) return null
      const response = await api.get(`/monte-carlo/experiments/${selectedExperimentId}/anova`)
      return response.data
    },
    enabled: !!selectedExperimentId,
  })

  const graficoCapacidadRef = useRef<HTMLDivElement>(null)
  const graficoDisrupcionesRef = useRef<HTMLDivElement>(null)
  const graficoCasosExtremosRef = useRef<HTMLDivElement>(null)
  const graficoEscenariosRef = useRef<HTMLDivElement>(null)

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

  const exportarTodos = async () => {
    const refs = [
      { ref: graficoCapacidadRef, nombre: "fig_sensibilidad_capacidad" },
      { ref: graficoDisrupcionesRef, nombre: "fig_sensibilidad_disrupciones" },
      { ref: graficoCasosExtremosRef, nombre: "fig_casos_extremos" },
      { ref: graficoEscenariosRef, nombre: "fig_comparacion_escenarios" },
    ]

    for (const { ref, nombre } of refs) {
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
        await new Promise((resolve) => setTimeout(resolve, 300))
      }
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto p-8 max-w-7xl">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-slate-100 rounded-xl">
                <BarChart3 className="h-6 w-6 text-slate-700" />
              </div>
              <div>
                <h1 className="text-4xl font-bold text-slate-900">Análisis de Sensibilidad</h1>
                <p className="text-slate-600 mt-1">
                  Visualizaciones y gráficos exportables para tesis
                </p>
              </div>
            </div>
            <button
              onClick={exportarTodos}
              className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
            >
              <Download className="h-4 w-4" />
              Exportar Todos
            </button>
          </div>
        </div>

        <Alert variant="info" className="mb-6">
          <Activity className="h-5 w-5" />
          <AlertTitle>Visualizaciones para Tesis</AlertTitle>
          <AlertDescription>
            Todos los gráficos son exportables a PNG de alta calidad (3x) para incluir en el
            documento LaTeX. Haz clic en el botón de descarga en cada gráfico individual o usa
            "Exportar Todos" arriba.
          </AlertDescription>
        </Alert>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-6 mb-6">
            <TabsTrigger value="anova" className="flex items-center gap-2">
              <Table2 className="h-4 w-4" />
              ANOVA
            </TabsTrigger>
            <TabsTrigger value="montecarlo" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Monte Carlo
            </TabsTrigger>
            <TabsTrigger value="sensibilidad" className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Sensibilidad
            </TabsTrigger>
            <TabsTrigger value="limites" className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Límites
            </TabsTrigger>
            <TabsTrigger value="escenarios" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Escenarios
            </TabsTrigger>
            <TabsTrigger value="monotonicidad" className="flex items-center gap-2">
              <TrendingDown className="h-4 w-4" />
              Monotonicidad
            </TabsTrigger>
          </TabsList>

          <TabsContent value="anova" className="space-y-6">
            <Card className="border-slate-200 shadow-sm">
              <CardHeader className="bg-slate-50">
                <CardTitle>Seleccionar Experimento Monte Carlo</CardTitle>
                <CardDescription>
                  Elige un experimento completado para ver su análisis ANOVA
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
                          onClick={() => setSelectedExperimentId(exp.id)}
                          className={`p-4 border-2 rounded-lg text-left transition-all ${
                            selectedExperimentId === exp.id
                              ? "border-blue-500 bg-blue-50"
                              : "border-slate-200 hover:border-slate-300 bg-white"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <Badge variant="success">Completado</Badge>
                            <span className="text-xs text-slate-500">#{exp.id}</span>
                          </div>
                          <h4 className="font-semibold text-slate-900 mb-1">{exp.nombre}</h4>
                          <p className="text-xs text-slate-600">
                            {exp.num_replicas.toLocaleString()} réplicas
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

            {selectedExperimentId && (
              <>
                {anovaLoading ? (
                  <Card className="border-slate-200 shadow-sm">
                    <CardContent className="pt-12 pb-12 text-center">
                      <div className="flex flex-col items-center gap-3">
                        <div className="animate-spin rounded-full h-12 w-12 border-4 border-slate-300 border-t-blue-600"></div>
                        <p className="text-slate-600">Calculando ANOVA...</p>
                      </div>
                    </CardContent>
                  </Card>
                ) : anovaData ? (
                  <ANOVATable data={anovaData} experimentId={selectedExperimentId} />
                ) : (
                  <Alert variant="danger">
                    <AlertCircle className="h-5 w-5" />
                    <AlertTitle>Error al calcular ANOVA</AlertTitle>
                    <AlertDescription>
                      No se pudo calcular el análisis ANOVA para este experimento.
                    </AlertDescription>
                  </Alert>
                )}
              </>
            )}
          </TabsContent>

          <TabsContent value="montecarlo" className="space-y-6">
            <MonteCarloDistributions />
          </TabsContent>

          <TabsContent value="sensibilidad" className="space-y-6">
            <Card className="border-slate-200 shadow-sm">
              <CardHeader className="bg-slate-50">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Sensibilidad a la Capacidad de Almacenamiento</CardTitle>
                    <CardDescription>
                      Cómo varía el nivel de servicio al incrementar la capacidad del hub
                    </CardDescription>
                  </div>
                  <button
                    onClick={() => exportarGrafico(graficoCapacidadRef, "fig_sensibilidad_capacidad")}
                    className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                    title="Exportar a PNG"
                  >
                    <Download className="h-4 w-4 text-slate-600" />
                  </button>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                <div ref={graficoCapacidadRef} className="bg-white p-6">
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={sensibilidadCapacidad}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis
                        dataKey="capacidad"
                        stroke="#737373"
                        fontSize={12}
                        label={{ value: "Capacidad (TM)", position: "insideBottom", offset: -5 }}
                      />
                      <YAxis
                        stroke="#737373"
                        fontSize={12}
                        label={{ value: "Nivel de Servicio (%)", angle: -90, position: "insideLeft" }}
                      />
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
                        dataKey="nivelServicio"
                        stroke="#6366f1"
                        strokeWidth={3}
                        dot={{ fill: "#6366f1", r: 6 }}
                        name="Nivel de Servicio (%)"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                  <div className="mt-4 p-4 bg-slate-50 rounded-lg">
                    <p className="text-sm text-slate-700">
                      <strong>Sensibilidad:</strong> +0.056 puntos porcentuales por TM adicional
                    </p>
                    <p className="text-sm text-slate-600 mt-1">
                      La relación es monotónica creciente: mayor capacidad → mejor nivel de servicio
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 shadow-sm">
              <CardHeader className="bg-slate-50">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Sensibilidad a la Duración de Disrupciones</CardTitle>
                    <CardDescription>
                      Degradación del servicio ante disrupciones de mayor severidad
                    </CardDescription>
                  </div>
                  <button
                    onClick={() => exportarGrafico(graficoDisrupcionesRef, "fig_sensibilidad_disrupciones")}
                    className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                    title="Exportar a PNG"
                  >
                    <Download className="h-4 w-4 text-slate-600" />
                  </button>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                <div ref={graficoDisrupcionesRef} className="bg-white p-6">
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={sensibilidadDisrupciones}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis
                        dataKey="duracion"
                        stroke="#737373"
                        fontSize={12}
                        label={{ value: "Duración Máxima Disrupciones (días)", position: "insideBottom", offset: -5 }}
                      />
                      <YAxis
                        stroke="#737373"
                        fontSize={12}
                        label={{ value: "Nivel de Servicio (%)", angle: -90, position: "insideLeft" }}
                      />
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
                        dataKey="nivelServicio"
                        stroke="#ef4444"
                        strokeWidth={3}
                        dot={{ fill: "#ef4444", r: 6 }}
                        name="Nivel de Servicio (%)"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                  <div className="mt-4 p-4 bg-red-50 rounded-lg">
                    <p className="text-sm text-red-900">
                      <strong>Sensibilidad:</strong> -0.83 puntos porcentuales por día adicional
                    </p>
                    <p className="text-sm text-red-800 mt-1">
                      La relación es monotónica decreciente: disrupciones más largas → peor servicio
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="limites" className="space-y-6">
            <Card className="border-slate-200 shadow-sm">
              <CardHeader className="bg-slate-50">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Casos Extremos y Límites del Sistema</CardTitle>
                    <CardDescription>
                      Validación del comportamiento en condiciones límite
                    </CardDescription>
                  </div>
                  <button
                    onClick={() => exportarGrafico(graficoCasosExtremosRef, "fig_casos_extremos")}
                    className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                    title="Exportar a PNG"
                  >
                    <Download className="h-4 w-4 text-slate-600" />
                  </button>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                <div ref={graficoCasosExtremosRef} className="bg-white p-6">
                  <div className="grid grid-cols-2 gap-4">
                    {casosExtremos.map((caso, idx) => (
                      <div key={idx} className="border-2 border-slate-200 rounded-lg p-5 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-3">
                          <h4 className="font-semibold text-slate-900">{caso.nombre}</h4>
                          <Badge variant={caso.color as any}>{caso.estado}</Badge>
                        </div>
                        <p className="text-sm text-slate-600 mb-4">{caso.descripcion}</p>
                        <Separator className="mb-4" />
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-500">Nivel de Servicio:</span>
                            <span className="font-bold text-slate-900">
                              {caso.nivelServicio.toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-500">Días con Quiebre:</span>
                            <span className="font-bold text-slate-900">{caso.quiebres}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <Alert variant="info" className="mt-6">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Validación Técnica</AlertTitle>
                    <AlertDescription>
                      Estos casos extremos confirman que el simulador se comporta correctamente en
                      los límites del espacio de parámetros. 15/15 pruebas de validación pasadas.
                    </AlertDescription>
                  </Alert>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="escenarios" className="space-y-6">
            <Card className="border-slate-200 shadow-sm">
              <CardHeader className="bg-slate-50">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Comparación de Escenarios de Disrupciones</CardTitle>
                    <CardDescription>
                      Análisis comparativo bajo diferentes niveles de severidad
                    </CardDescription>
                  </div>
                  <button
                    onClick={() => exportarGrafico(graficoEscenariosRef, "fig_comparacion_escenarios")}
                    className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                    title="Exportar a PNG"
                  >
                    <Download className="h-4 w-4 text-slate-600" />
                  </button>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                <div ref={graficoEscenariosRef} className="bg-white p-6">
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={escenarios}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="nombre" stroke="#737373" fontSize={12} />
                      <YAxis stroke="#737373" fontSize={12} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#fff",
                          border: "1px solid #e5e5e5",
                          borderRadius: "8px",
                        }}
                      />
                      <Legend />
                      <Bar dataKey="nivelServicio" fill="#6366f1" name="Nivel de Servicio (%)" />
                      <Bar dataKey="quiebres" fill="#ef4444" name="Días con Quiebre" />
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="mt-6 grid grid-cols-3 gap-4">
                    {escenarios.map((esc, idx) => (
                      <div key={idx} className="p-4 bg-slate-50 rounded-lg">
                        <h5 className="font-semibold text-slate-900 mb-2">{esc.nombre}</h5>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span className="text-slate-600">Servicio:</span>
                            <span className="font-medium">{esc.nivelServicio}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-600">Quiebres:</span>
                            <span className="font-medium">{esc.quiebres} días</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-600">Bloqueados:</span>
                            <span className="font-medium">{esc.diasBloqueados} días</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="monotonicidad" className="space-y-6">
            <Alert variant="info">
              <Activity className="h-5 w-5" />
              <AlertTitle>Validación de Monotonicidad</AlertTitle>
              <AlertDescription>
                Las pruebas de monotonicidad confirman que el sistema exhibe comportamientos
                esperados teóricamente: monotonicidad creciente con respecto a la capacidad, y
                monotonicidad decreciente con respecto a la duración de disrupciones.
              </AlertDescription>
            </Alert>

            <div className="grid grid-cols-2 gap-6">
              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="bg-green-50">
                  <CardTitle className="flex items-center gap-2 text-green-900">
                    <TrendingUp className="h-5 w-5" />
                    Monotonicidad Creciente
                  </CardTitle>
                  <CardDescription className="text-green-700">
                    Respecto a la capacidad
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    {sensibilidadCapacidad.map((punto, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-white border border-slate-200 rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                            <span className="font-bold text-green-700">{punto.capacidad}</span>
                          </div>
                          <span className="text-sm font-medium text-slate-700">TM</span>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-slate-900">
                            {punto.nivelServicio.toFixed(1)}%
                          </div>
                          {idx > 0 && (
                            <div className="text-xs text-green-600 flex items-center gap-1">
                              <TrendingUp className="h-3 w-3" />
                              +{(punto.nivelServicio - sensibilidadCapacidad[idx - 1].nivelServicio).toFixed(2)}%
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="text-sm text-slate-600 mt-4 p-3 bg-slate-50 rounded-lg">
                    Propiedad confirmada: Cada incremento de capacidad mejora el nivel de servicio
                  </p>
                </CardContent>
              </Card>

              <Card className="border-slate-200 shadow-sm">
                <CardHeader className="bg-red-50">
                  <CardTitle className="flex items-center gap-2 text-red-900">
                    <TrendingDown className="h-5 w-5" />
                    Monotonicidad Decreciente
                  </CardTitle>
                  <CardDescription className="text-red-700">
                    Respecto a duración de disrupciones
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    {sensibilidadDisrupciones.map((punto, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-white border border-slate-200 rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                            <span className="font-bold text-red-700">{punto.duracion}</span>
                          </div>
                          <span className="text-sm font-medium text-slate-700">días</span>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-slate-900">
                            {punto.nivelServicio.toFixed(1)}%
                          </div>
                          {idx > 0 && (
                            <div className="text-xs text-red-600 flex items-center gap-1">
                              <TrendingDown className="h-3 w-3" />
                              {(punto.nivelServicio - sensibilidadDisrupciones[idx - 1].nivelServicio).toFixed(2)}%
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="text-sm text-slate-600 mt-4 p-3 bg-slate-50 rounded-lg">
                    Propiedad confirmada: Cada dia adicional de disrupcion degrada el servicio
                  </p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
