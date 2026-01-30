/**
 * Página de Validación y Verificación del Sistema
 * Presenta las 15 pruebas de validación técnica
 */

import { useState, useRef } from "react"
import { Download, CheckCircle, XCircle, AlertTriangle, Activity, Shield, Beaker, TrendingUp } from "lucide-react"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Separator } from "@/components/ui/separator"
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
  PieChart,
  Pie,
  Cell,
} from "recharts"

// Resultados del protocolo de validación
const validaciones = [
  {
    categoria: "Validación Física",
    pruebas: [
      {
        nombre: "Conservación de masa",
        valorObservado: "< 10⁻⁶ TM",
        valorEsperado: "0.00 TM",
        estado: "PASS",
        criticidad: "CRÍTICA",
      },
      {
        nombre: "No-negatividad inventario",
        valorObservado: "0.00 TM",
        valorEsperado: "≥ 0 TM",
        estado: "PASS",
        criticidad: "CRÍTICA",
      },
    ],
  },
  {
    categoria: "Casos Extremos",
    pruebas: [
      {
        nombre: "Capacidad infinita sin disr.",
        valorObservado: "100.00%",
        valorEsperado: "100%",
        estado: "PASS",
        criticidad: "ALTA",
      },
      {
        nombre: "Inventario cero bloqueado",
        valorObservado: "0.00%",
        valorEsperado: "0%",
        estado: "PASS",
        criticidad: "ALTA",
      },
      {
        nombre: "Sin disrupciones",
        valorObservado: "99.84%",
        valorEsperado: "> 99%",
        estado: "PASS",
        criticidad: "ALTA",
      },
      {
        nombre: "Disrupción permanente",
        valorObservado: "0.00 TM",
        valorEsperado: "0.00 TM",
        estado: "PASS",
        criticidad: "ALTA",
      },
    ],
  },
  {
    categoria: "Validación Estadística",
    pruebas: [
      {
        nombre: "Test Poisson (p-valor)",
        valorObservado: "0.38",
        valorEsperado: "> 0.05",
        estado: "PASS",
        criticidad: "MEDIA-ALTA",
      },
      {
        nombre: "Test independencia (p-valor)",
        valorObservado: "0.42",
        valorEsperado: "> 0.05",
        estado: "PASS",
        criticidad: "MEDIA-ALTA",
      },
      {
        nombre: "Test normalidad (p-valor)",
        valorObservado: "0.18",
        valorEsperado: "> 0.05",
        estado: "PASS",
        criticidad: "MEDIA-ALTA",
      },
    ],
  },
  {
    categoria: "Sensibilidad",
    pruebas: [
      {
        nombre: "Monotonicidad capacidad",
        valorObservado: "Creciente",
        valorEsperado: "Creciente",
        estado: "PASS",
        criticidad: "MEDIA",
      },
      {
        nombre: "Monotonicidad duración",
        valorObservado: "Decreciente",
        valorEsperado: "Decreciente",
        estado: "PASS",
        criticidad: "MEDIA",
      },
    ],
  },
  {
    categoria: "Comparación Analítica",
    pruebas: [
      {
        nombre: "Autonomía teórica",
        valorObservado: "8.05 días",
        valorEsperado: "8.21 días",
        estado: "PASS",
        criticidad: "MEDIA",
      },
      {
        nombre: "Frecuencia disrupciones",
        valorObservado: "3.98/año",
        valorEsperado: "4.00/año",
        estado: "PASS",
        criticidad: "MEDIA",
      },
    ],
  },
  {
    categoria: "Calibración Empírica",
    pruebas: [
      {
        nombre: "Autonomía CNE",
        valorObservado: "8.21 días",
        valorEsperado: "8.20 días",
        estado: "PASS",
        criticidad: "ALTA",
      },
      {
        nombre: "Demanda promedio anual",
        valorObservado: "52.48 TM/d",
        valorEsperado: "52.50 TM/d",
        estado: "PASS",
        criticidad: "ALTA",
      },
    ],
  },
]

const resumenCategorias = [
  { nombre: "Validación Física", pruebas: 2, passed: 2, criticidad: "CRÍTICA", color: "#ef4444" },
  { nombre: "Casos Extremos", pruebas: 4, passed: 4, criticidad: "ALTA", color: "#f59e0b" },
  { nombre: "Validación Estadística", pruebas: 3, passed: 3, criticidad: "MEDIA-ALTA", color: "#3b82f6" },
  { nombre: "Sensibilidad", pruebas: 2, passed: 2, criticidad: "MEDIA", color: "#8b5cf6" },
  { nombre: "Comparación Analítica", pruebas: 2, passed: 2, criticidad: "MEDIA", color: "#06b6d4" },
  { nombre: "Calibración Empírica", pruebas: 2, passed: 2, criticidad: "ALTA", color: "#10b981" },
]

export default function Validation() {
  const [activeTab, setActiveTab] = useState("resumen")
  const tablaValidacionRef = useRef<HTMLDivElement>(null)
  const graficoResumenRef = useRef<HTMLDivElement>(null)

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

  const totalPruebas = validaciones.reduce((acc, cat) => acc + cat.pruebas.length, 0)
  const pruebasPasadas = validaciones.reduce(
    (acc, cat) => acc + cat.pruebas.filter((p) => p.estado === "PASS").length,
    0
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto p-8 max-w-7xl">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 bg-slate-100 rounded-xl">
              <Shield className="h-6 w-6 text-slate-700" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-slate-900">Validación y Verificación del Sistema</h1>
              <p className="text-slate-600 mt-1">
                Protocolo exhaustivo de 15 pruebas de validación técnica
              </p>
            </div>
          </div>
        </div>

        <Alert variant="success" className="mb-6">
          <CheckCircle className="h-5 w-5" />
          <AlertTitle className="text-lg">Sistema Validado Exitosamente</AlertTitle>
          <AlertDescription>
            <div className="mt-2 flex items-center gap-6">
              <div className="text-2xl font-bold text-green-900">
                {pruebasPasadas}/{totalPruebas}
              </div>
              <div>
                <p className="font-semibold">Pruebas exitosas (100%)</p>
                <p className="text-sm">
                  Todas las validaciones críticas y de alta prioridad han sido superadas
                </p>
              </div>
            </div>
          </AlertDescription>
        </Alert>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5 mb-6">
            <TabsTrigger value="resumen" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Resumen
            </TabsTrigger>
            <TabsTrigger value="fisica" className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              Física
            </TabsTrigger>
            <TabsTrigger value="extremos" className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Extremos
            </TabsTrigger>
            <TabsTrigger value="estadistica" className="flex items-center gap-2">
              <Beaker className="h-4 w-4" />
              Estadística
            </TabsTrigger>
            <TabsTrigger value="completo" className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              Tabla Completa
            </TabsTrigger>
          </TabsList>

          <TabsContent value="resumen" className="space-y-6">
            <Card className="border-slate-200 shadow-sm">
              <CardHeader className="bg-slate-50">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Resumen por Categoría</CardTitle>
                    <CardDescription>
                      Distribución de pruebas por tipo de validación
                    </CardDescription>
                  </div>
                  <button
                    onClick={() => exportarGrafico(graficoResumenRef, "fig_validacion_resumen")}
                    className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                    title="Exportar a PNG"
                  >
                    <Download className="h-4 w-4 text-slate-600" />
                  </button>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                <div ref={graficoResumenRef} className="bg-white p-6">
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={resumenCategorias}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="nombre" stroke="#737373" fontSize={11} angle={-15} textAnchor="end" height={80} />
                      <YAxis stroke="#737373" fontSize={12} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#fff",
                          border: "1px solid #e5e5e5",
                          borderRadius: "8px",
                        }}
                      />
                      <Legend />
                      <Bar dataKey="pruebas" fill="#6366f1" name="Total Pruebas" />
                      <Bar dataKey="passed" fill="#10b981" name="Pruebas Pasadas" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-3 gap-4">
              <Card className="border-green-200 bg-green-50/50">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                      <CheckCircle className="h-6 w-6 text-green-600" />
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-green-900">100%</div>
                  <div className="text-sm text-green-700 mt-1">Tasa de Éxito</div>
                </CardContent>
              </Card>

              <Card className="border-blue-200 bg-blue-50/50">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                      <Beaker className="h-6 w-6 text-blue-600" />
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-blue-900">{totalPruebas}</div>
                  <div className="text-sm text-blue-700 mt-1">Pruebas Ejecutadas</div>
                </CardContent>
              </Card>

              <Card className="border-purple-200 bg-purple-50/50">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
                      <Shield className="h-6 w-6 text-purple-600" />
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-purple-900">2</div>
                  <div className="text-sm text-purple-700 mt-1">Pruebas Críticas</div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

                    <TabsContent value="fisica" className="space-y-6">
            <Alert variant="danger">
              <Shield className="h-5 w-5" />
              <AlertTitle>Pruebas Críticas - Máxima Prioridad</AlertTitle>
              <AlertDescription>
                Las validaciones físicas verifican invariantes matemáticos fundamentales. Su falla
                invalidaría completamente los resultados del simulador.
              </AlertDescription>
            </Alert>

            {validaciones[0].pruebas.map((prueba, idx) => (
              <Card key={idx} className="border-slate-200 shadow-sm">
                <CardHeader className="bg-red-50/30">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      {prueba.nombre}
                    </CardTitle>
                    <Badge variant="danger">CRÍTICA</Badge>
                  </div>
                  <CardDescription>
                    {idx === 0 && "Principio de conservación de masa: I_inicial + Σ Recibido = I_final + Σ Despachado"}
                    {idx === 1 && "Restricción física: Inventario(t) ≥ 0 para todo t ∈ [0, 365]"}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-slate-600 mb-1">Valor Observado</p>
                      <p className="text-xl font-bold text-slate-900">{prueba.valorObservado}</p>
                    </div>
                    <div className="p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-slate-600 mb-1">Valor Esperado</p>
                      <p className="text-xl font-bold text-slate-900">{prueba.valorEsperado}</p>
                    </div>
                    <div className="p-4 bg-green-50 rounded-lg border-2 border-green-200">
                      <p className="text-sm text-green-700 mb-1">Estado</p>
                      <p className="text-xl font-bold text-green-900">{prueba.estado}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

                    <TabsContent value="extremos" className="space-y-6">
            <Alert variant="warning">
              <AlertTriangle className="h-5 w-5" />
              <AlertTitle>Validación en Condiciones Límite</AlertTitle>
              <AlertDescription>
                Evalúa el comportamiento del simulador en los bordes del espacio de parámetros.
                Aunque improbables en operación real, estos casos verifican la corrección lógica.
              </AlertDescription>
            </Alert>

            <div className="grid grid-cols-2 gap-4">
              {validaciones[1].pruebas.map((prueba, idx) => (
                <Card key={idx} className="border-slate-200 shadow-sm">
                  <CardHeader className="bg-yellow-50/30">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">{prueba.nombre}</CardTitle>
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    </div>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600">Observado:</span>
                        <span className="font-semibold text-slate-900">{prueba.valorObservado}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Esperado:</span>
                        <span className="font-semibold text-slate-900">{prueba.valorEsperado}</span>
                      </div>
                      <Separator />
                      <div className="flex justify-between items-center pt-2">
                        <Badge variant="warning">{prueba.criticidad}</Badge>
                        <Badge variant="success">{prueba.estado}</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

                    <TabsContent value="estadistica" className="space-y-6">
            <Alert variant="info">
              <Beaker className="h-5 w-5" />
              <AlertTitle>Tests de Bondad de Ajuste</AlertTitle>
              <AlertDescription>
                Verifica que los procesos estocásticos implementados generan efectivamente las
                distribuciones de probabilidad especificadas (Poisson, Normal, independencia).
              </AlertDescription>
            </Alert>

            {validaciones[2].pruebas.map((prueba, idx) => (
              <Card key={idx} className="border-slate-200 shadow-sm">
                <CardHeader className="bg-blue-50/30">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        {prueba.nombre}
                      </CardTitle>
                      <CardDescription className="mt-1">
                        {idx === 0 && "Hipótesis nula: Disrupciones siguen Poisson(λ=4)"}
                        {idx === 1 && "Hipótesis nula: Réplicas son estadísticamente independientes"}
                        {idx === 2 && "Hipótesis nula: Demanda diaria sigue distribución Normal"}
                      </CardDescription>
                    </div>
                    <Badge variant="success">{prueba.estado}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-white border border-slate-200 rounded-lg">
                      <p className="text-sm text-slate-600 mb-2">Valor p observado</p>
                      <p className="text-3xl font-bold text-slate-900">{prueba.valorObservado}</p>
                      <p className="text-xs text-slate-500 mt-2">
                        {idx === 0 && "Test Chi-cuadrado, 500 réplicas"}
                        {idx === 1 && "Test de rachas, 200 réplicas"}
                        {idx === 2 && "Test Kolmogorov-Smirnov"}
                      </p>
                    </div>
                    <div className="p-4 bg-green-50 border-2 border-green-200 rounded-lg">
                      <p className="text-sm text-green-700 mb-2">Criterio de aceptación</p>
                      <p className="text-3xl font-bold text-green-900">{prueba.valorEsperado}</p>
                      <p className="text-sm text-green-700 mt-2">
                        No se rechaza H0 (a=0.05)
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

                    <TabsContent value="completo" className="space-y-6">
            <Card className="border-slate-200 shadow-sm">
              <CardHeader className="bg-slate-50">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Protocolo Completo de Validación</CardTitle>
                    <CardDescription>
                      15 pruebas organizadas en 6 categorías jerárquicas
                    </CardDescription>
                  </div>
                  <button
                    onClick={() => exportarGrafico(tablaValidacionRef, "tabla_validacion_completa")}
                    className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                    title="Exportar a PNG"
                  >
                    <Download className="h-4 w-4 text-slate-600" />
                  </button>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                <div ref={tablaValidacionRef} className="bg-white p-6">
                  <div className="space-y-6">
                    {validaciones.map((categoria, catIdx) => (
                      <div key={catIdx} className="border-2 border-slate-200 rounded-lg overflow-hidden">
                        <div className="bg-slate-100 px-4 py-3 border-b-2 border-slate-200">
                          <div className="flex items-center justify-between">
                            <h3 className="font-bold text-slate-900">{categoria.categoria}</h3>
                            <Badge variant="secondary">{categoria.pruebas.length} pruebas</Badge>
                          </div>
                        </div>
                        <div className="divide-y divide-slate-200">
                          {categoria.pruebas.map((prueba, idx) => (
                            <div key={idx} className="p-4 hover:bg-slate-50 transition-colors">
                              <div className="grid grid-cols-5 gap-4 items-center">
                                <div className="col-span-2">
                                  <p className="font-semibold text-slate-900">{prueba.nombre}</p>
                                </div>
                                <div className="text-center">
                                  <p className="text-sm text-slate-600">Observado</p>
                                  <p className="font-mono text-sm font-semibold">{prueba.valorObservado}</p>
                                </div>
                                <div className="text-center">
                                  <p className="text-sm text-slate-600">Esperado</p>
                                  <p className="font-mono text-sm font-semibold">{prueba.valorEsperado}</p>
                                </div>
                                <div className="flex items-center justify-end gap-2">
                                  <Badge variant={
                                    prueba.criticidad === "CRÍTICA" ? "danger" :
                                    prueba.criticidad === "ALTA" ? "warning" :
                                    "secondary"
                                  }>
                                    {prueba.criticidad}
                                  </Badge>
                                  <Badge variant="success">{prueba.estado}</Badge>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-6 p-4 bg-green-50 border-2 border-green-200 rounded-lg">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="h-6 w-6 text-green-600" />
                      <div>
                        <p className="font-bold text-green-900">
                          Tasa de éxito: {pruebasPasadas}/{totalPruebas} (100%)
                        </p>
                        <p className="text-sm text-green-700">
                          Modelo técnicamente válido, estadísticamente consistente y empíricamente calibrado
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
