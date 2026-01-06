/**
 * Componente para visualizar resultados del análisis ANOVA
 * Muestra tabla ANOVA, efectos principales, tamaños del efecto y tests post-hoc
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Separator } from "@/components/ui/separator"
import { CheckCircle2, TrendingUp, TrendingDown, AlertCircle, BarChart3 } from "lucide-react"

interface ANOVAData {
  tabla_anova: Array<{
    SC: number
    gl: number
    MC: number
    F: number
    "p-valor": number
  }>
  efectos_principales: {
    capacidad: number
    duracion: number
    interaccion: number
  }
  tamanos_efecto: {
    eta_cuadrado_capacidad: number
    eta_cuadrado_duracion: number
    eta_cuadrado_interaccion: number
  }
  r_cuadrado_ajustado: number
  medias_por_configuracion: Array<{
    capacidad_cat: string
    duracion_cat: string
    mean: number
    std: number
    count: number
    ci_lower: number
    ci_upper: number
  }>
  tukey_capacidad: Array<any> | null
  tukey_duracion: Array<any> | null
}

interface ANOVATableProps {
  data: ANOVAData
  experimentId: number
}

export function ANOVATable({ data, experimentId }: ANOVATableProps) {
  const formatNumber = (num: number, decimals: number = 4): string => {
    if (num < 0.0001 && num > 0) return "< 0.0001"
    return num.toFixed(decimals)
  }

  const getSignificanceColor = (pValue: number): string => {
    if (pValue < 0.001) return "text-green-700 font-bold"
    if (pValue < 0.01) return "text-green-600 font-semibold"
    if (pValue < 0.05) return "text-yellow-600"
    return "text-slate-500"
  }

  const getSignificanceBadge = (pValue: number) => {
    if (pValue < 0.001) return <Badge variant="success">p &lt; 0.001 ***</Badge>
    if (pValue < 0.01) return <Badge variant="warning">p &lt; 0.01 **</Badge>
    if (pValue < 0.05) return <Badge variant="info">p &lt; 0.05 *</Badge>
    return <Badge variant="secondary">n.s.</Badge>
  }

  const getEffectSizeBadge = (etaSquared: number) => {
    if (etaSquared >= 0.14) return <Badge variant="success">Grande (η² = {etaSquared.toFixed(3)})</Badge>
    if (etaSquared >= 0.06) return <Badge variant="warning">Mediano (η² = {etaSquared.toFixed(3)})</Badge>
    if (etaSquared >= 0.01) return <Badge variant="info">Pequeño (η² = {etaSquared.toFixed(3)})</Badge>
    return <Badge variant="secondary">Despreciable (η² = {etaSquared.toFixed(3)})</Badge>
  }

  return (
    <div className="space-y-6">
      {/* Header con información del experimento */}
      <Alert variant="info">
        <BarChart3 className="h-5 w-5" />
        <AlertTitle>Análisis ANOVA de Dos Vías</AlertTitle>
        <AlertDescription>
          Experimento #{experimentId} | Modelo: Nivel de Servicio ~ Capacidad + Duración + Capacidad × Duración
        </AlertDescription>
      </Alert>

      {/* Tabla ANOVA Principal */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="bg-slate-50">
          <CardTitle className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
            Tabla ANOVA (Tipo II)
          </CardTitle>
          <CardDescription>
            Análisis de varianza de dos factores con interacción
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-slate-300">
                  <th className="text-left py-3 px-4 font-semibold text-slate-700">Fuente</th>
                  <th className="text-right py-3 px-4 font-semibold text-slate-700">SC</th>
                  <th className="text-right py-3 px-4 font-semibold text-slate-700">gl</th>
                  <th className="text-right py-3 px-4 font-semibold text-slate-700">MC</th>
                  <th className="text-right py-3 px-4 font-semibold text-slate-700">F</th>
                  <th className="text-right py-3 px-4 font-semibold text-slate-700">p-valor</th>
                  <th className="text-center py-3 px-4 font-semibold text-slate-700">Significancia</th>
                </tr>
              </thead>
              <tbody>
                {data.tabla_anova.map((row, idx) => {
                  const rowKey = Object.keys(row)[0]  // Primera key es el nombre de la fila
                  const rowName = ["Capacidad", "Duración", "Capacidad × Duración", "Residual"][idx] || "Unknown"

                  return (
                    <tr key={idx} className={`border-b border-slate-200 ${idx % 2 === 0 ? "bg-white" : "bg-slate-50"}`}>
                      <td className="py-3 px-4 font-medium text-slate-900">{rowName}</td>
                      <td className="py-3 px-4 text-right font-mono">{formatNumber(row.SC, 2)}</td>
                      <td className="py-3 px-4 text-right font-mono">{row.gl}</td>
                      <td className="py-3 px-4 text-right font-mono">{formatNumber(row.MC, 2)}</td>
                      <td className="py-3 px-4 text-right font-mono">{row.F ? formatNumber(row.F, 2) : "—"}</td>
                      <td className={`py-3 px-4 text-right font-mono ${getSignificanceColor(row["p-valor"] || 1)}`}>
                        {row["p-valor"] ? formatNumber(row["p-valor"], 4) : "—"}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {row["p-valor"] ? getSignificanceBadge(row["p-valor"]) : "—"}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <p className="text-sm text-blue-900 font-medium">Interpretación:</p>
                <p className="text-xs text-blue-800 mt-1">
                  *** p &lt; 0.001 (altamente significativo) | ** p &lt; 0.01 (muy significativo) | * p &lt; 0.05 (significativo) | n.s. = no significativo
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Efectos Principales y Tamaños del Efecto */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="bg-green-50">
            <CardTitle className="flex items-center gap-2 text-green-900">
              <TrendingUp className="h-5 w-5" />
              Efectos Principales
            </CardTitle>
            <CardDescription className="text-green-700">
              Cambio en nivel de servicio entre niveles extremos
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-white border-2 border-green-200 rounded-lg">
                <div>
                  <span className="text-sm font-medium text-slate-700">Capacidad</span>
                  <p className="text-xs text-slate-500">Status Quo → Propuesta</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-green-700">
                    +{data.efectos_principales.capacidad.toFixed(2)}%
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-white border-2 border-red-200 rounded-lg">
                <div>
                  <span className="text-sm font-medium text-slate-700">Duración</span>
                  <p className="text-xs text-slate-500">Corta → Larga</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-red-700">
                    {data.efectos_principales.duracion.toFixed(2)}%
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-white border-2 border-blue-200 rounded-lg">
                <div>
                  <span className="text-sm font-medium text-slate-700">Interacción</span>
                  <p className="text-xs text-slate-500">Cap. × Duración</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-700">
                    {data.efectos_principales.interaccion.toFixed(2)}%
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="bg-purple-50">
            <CardTitle className="flex items-center gap-2 text-purple-900">
              <BarChart3 className="h-5 w-5" />
              Tamaños del Efecto (η²)
            </CardTitle>
            <CardDescription className="text-purple-700">
              Proporción de varianza explicada
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-700">Capacidad</span>
                  {getEffectSizeBadge(data.tamanos_efecto.eta_cuadrado_capacidad)}
                </div>
                <div className="w-full bg-slate-200 rounded-full h-3">
                  <div
                    className="bg-green-600 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${data.tamanos_efecto.eta_cuadrado_capacidad * 100}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-700">Duración</span>
                  {getEffectSizeBadge(data.tamanos_efecto.eta_cuadrado_duracion)}
                </div>
                <div className="w-full bg-slate-200 rounded-full h-3">
                  <div
                    className="bg-red-600 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${data.tamanos_efecto.eta_cuadrado_duracion * 100}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-700">Interacción</span>
                  {getEffectSizeBadge(data.tamanos_efecto.eta_cuadrado_interaccion)}
                </div>
                <div className="w-full bg-slate-200 rounded-full h-3">
                  <div
                    className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${data.tamanos_efecto.eta_cuadrado_interaccion * 100}%` }}
                  />
                </div>
              </div>

              <Separator />

              <div className="p-3 bg-purple-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-purple-900">R² Ajustado</span>
                  <span className="text-lg font-bold text-purple-700">
                    {(data.r_cuadrado_ajustado * 100).toFixed(2)}%
                  </span>
                </div>
                <p className="text-xs text-purple-700 mt-1">
                  Varianza total explicada por el modelo
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Medias por Configuración */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="bg-slate-50">
          <CardTitle>Medias por Configuración</CardTitle>
          <CardDescription>
            Nivel de servicio promedio con intervalos de confianza al 95%
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {data.medias_por_configuracion.map((config, idx) => (
              <div key={idx} className="p-4 bg-white border-2 border-slate-200 rounded-lg hover:shadow-md transition-shadow">
                <div className="mb-2">
                  <Badge variant={config.capacidad_cat === "Propuesta" ? "success" : "secondary"}>
                    {config.capacidad_cat}
                  </Badge>
                  <Badge variant="outline" className="ml-2">
                    {config.duracion_cat}
                  </Badge>
                </div>
                <div className="text-3xl font-bold text-slate-900 mb-1">
                  {config.mean.toFixed(2)}%
                </div>
                <div className="text-xs text-slate-600">
                  σ = {config.std.toFixed(2)}% | n = {config.count}
                </div>
                <div className="text-xs text-slate-500 mt-2">
                  IC 95%: [{config.ci_lower.toFixed(2)}, {config.ci_upper.toFixed(2)}]
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
