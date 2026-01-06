/**
 * Página de configuración de simulación.
 */

import { useState, useEffect } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { ArrowLeft, Play, Save } from "lucide-react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type { ConfiguracionCreate, Configuracion, Simulacion } from "@/types"

const formSchema = z.object({
  nombre: z.string().min(1, "Nombre requerido").max(100),
  descripcion: z.string().optional(),
  capacidad_hub_tm: z.number().positive().max(2000),
  punto_reorden_tm: z.number().positive().max(2000),
  cantidad_pedido_tm: z.number().positive().max(1000),
  inventario_inicial_pct: z.number().min(0).max(100),
  demanda_base_diaria_tm: z.number().positive(),
  variabilidad_demanda: z.number().min(0).max(1),
  amplitud_estacional: z.number().min(0).max(1),
  dia_pico_invernal: z.number().min(1).max(365),
  usar_estacionalidad: z.boolean(),
  tasa_disrupciones_anual: z.number().min(0).max(50),
  duracion_disrupcion_min_dias: z.number().positive(),
  duracion_disrupcion_mode_dias: z.number().positive(),
  duracion_disrupcion_max_dias: z.number().positive(),
  lead_time_nominal_dias: z.number().positive(),
  duracion_simulacion_dias: z.number().min(1).max(3650),
  semilla_aleatoria: z.number().nullable().optional(),
}).refine((data) => data.punto_reorden_tm <= data.capacidad_hub_tm, {
  message: "El punto de reorden no puede exceder la capacidad del hub",
  path: ["punto_reorden_tm"],
}).refine((data) => data.cantidad_pedido_tm <= data.capacidad_hub_tm, {
  message: "La cantidad de pedido no puede exceder la capacidad del hub",
  path: ["cantidad_pedido_tm"],
}).refine((data) => data.duracion_disrupcion_min_dias <= data.duracion_disrupcion_mode_dias, {
  message: "La duración mínima debe ser menor o igual a la más probable",
  path: ["duracion_disrupcion_mode_dias"],
}).refine((data) => data.duracion_disrupcion_mode_dias <= data.duracion_disrupcion_max_dias, {
  message: "La duración más probable debe ser menor o igual a la máxima",
  path: ["duracion_disrupcion_max_dias"],
})

const DEFAULT_VALUES = {
  nombre: "Configuración Base",
  descripcion: "",
  capacidad_hub_tm: 500,
  punto_reorden_tm: 200,
  cantidad_pedido_tm: 180,
  inventario_inicial_pct: 100,
  demanda_base_diaria_tm: 5.0,
  variabilidad_demanda: 0.15,
  amplitud_estacional: 0.25,
  dia_pico_invernal: 196,
  usar_estacionalidad: true,
  tasa_disrupciones_anual: 6.0,
  duracion_disrupcion_min_dias: 1,
  duracion_disrupcion_mode_dias: 3,
  duracion_disrupcion_max_dias: 21,
  lead_time_nominal_dias: 3,
  duracion_simulacion_dias: 730,
  semilla_aleatoria: null,
}

export default function Configuration() {
  const navigate = useNavigate()
  const location = useLocation()
  const [isExecuting, setIsExecuting] = useState(false)

  const existingConfig = (location.state as { config?: Configuracion })?.config

  const { data: defaults } = useQuery({
    queryKey: ["defaults"],
    queryFn: async () => {
      const response = await api.get("/configuraciones/defaults")
      return response.data
    },
  })

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: DEFAULT_VALUES,
  })

  // Actualizar valores cuando lleguen los defaults del servidor
  useEffect(() => {
    if (existingConfig) {
      form.reset({
        ...existingConfig,
        ...existingConfig.parametros,
      })
    } else if (defaults) {
      form.reset(defaults)
    }
  }, [existingConfig, defaults, form])

  const createConfigMutation = useMutation({
    mutationFn: async (data: ConfiguracionCreate) => {
      const response = await api.post<Configuracion>("/configuraciones/", data)
      return response.data
    },
  })

  const executeSimulationMutation = useMutation({
    mutationFn: async (configuracion_id: number) => {
      const response = await api.post<Simulacion>("/simulaciones/execute", {
        configuracion_id,
      })
      return response.data
    },
  })

  const onSaveOnly = async (values: z.infer<typeof formSchema>) => {
    try {
      const configData: ConfiguracionCreate = {
        nombre: values.nombre,
        descripcion: values.descripcion,
        capacidad_hub_tm: values.capacidad_hub_tm,
        punto_reorden_tm: values.punto_reorden_tm,
        cantidad_pedido_tm: values.cantidad_pedido_tm,
        inventario_inicial_pct: values.inventario_inicial_pct,
        demanda_base_diaria_tm: values.demanda_base_diaria_tm,
        variabilidad_demanda: values.variabilidad_demanda,
        amplitud_estacional: values.amplitud_estacional,
        dia_pico_invernal: values.dia_pico_invernal,
        usar_estacionalidad: values.usar_estacionalidad,
        tasa_disrupciones_anual: values.tasa_disrupciones_anual,
        duracion_disrupcion_min_dias: values.duracion_disrupcion_min_dias,
        duracion_disrupcion_mode_dias: values.duracion_disrupcion_mode_dias,
        duracion_disrupcion_max_dias: values.duracion_disrupcion_max_dias,
        lead_time_nominal_dias: values.lead_time_nominal_dias,
        duracion_simulacion_dias: values.duracion_simulacion_dias,
        semilla_aleatoria: values.semilla_aleatoria,
      }

      await createConfigMutation.mutateAsync(configData)
      alert("Configuración guardada exitosamente")
      navigate("/")
    } catch (error) {
      console.error("Error al guardar configuración:", error)
      alert("Error al guardar configuración")
    }
  }

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    setIsExecuting(true)
    try {
      // Crear configuración
      const configData: ConfiguracionCreate = {
        nombre: values.nombre,
        descripcion: values.descripcion,
        capacidad_hub_tm: values.capacidad_hub_tm,
        punto_reorden_tm: values.punto_reorden_tm,
        cantidad_pedido_tm: values.cantidad_pedido_tm,
        inventario_inicial_pct: values.inventario_inicial_pct,
        demanda_base_diaria_tm: values.demanda_base_diaria_tm,
        variabilidad_demanda: values.variabilidad_demanda,
        amplitud_estacional: values.amplitud_estacional,
        dia_pico_invernal: values.dia_pico_invernal,
        usar_estacionalidad: values.usar_estacionalidad,
        tasa_disrupciones_anual: values.tasa_disrupciones_anual,
        duracion_disrupcion_min_dias: values.duracion_disrupcion_min_dias,
        duracion_disrupcion_mode_dias: values.duracion_disrupcion_mode_dias,
        duracion_disrupcion_max_dias: values.duracion_disrupcion_max_dias,
        lead_time_nominal_dias: values.lead_time_nominal_dias,
        duracion_simulacion_dias: values.duracion_simulacion_dias,
        semilla_aleatoria: values.semilla_aleatoria,
      }

      const config = await createConfigMutation.mutateAsync(configData)

      // Ejecutar simulación
      const simulation = await executeSimulationMutation.mutateAsync(config.id)

      // Navegar a resultados
      navigate(`/resultados/${simulation.id}`)
    } catch (error) {
      console.error("Error al ejecutar simulación:", error)
      alert("Error al ejecutar simulación")
    } finally {
      setIsExecuting(false)
    }
  }

  const watchedValues = form.watch()

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto p-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <Button variant="outline" size="sm" onClick={() => navigate("/")} className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Volver al Dashboard
          </Button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Configurar Simulación</h1>
              <p className="text-slate-600 mt-1">
                Configure los parámetros para ejecutar una simulación única
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={form.handleSubmit(onSaveOnly)}
                disabled={isExecuting || createConfigMutation.isPending}
              >
                <Save className="h-4 w-4 mr-2" />
                {createConfigMutation.isPending ? "Guardando..." : "Guardar Config"}
              </Button>
              <Button onClick={form.handleSubmit(onSubmit)} disabled={isExecuting} size="lg">
                <Play className="h-4 w-4 mr-2" />
                {isExecuting ? "Ejecutando..." : "Ejecutar Simulación"}
              </Button>
            </div>
          </div>
        </div>

        <form className="space-y-6">
          {/* Información General */}
          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="bg-slate-50">
              <CardTitle>Información General</CardTitle>
              <CardDescription>Identificación y descripción de la configuración</CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Nombre de la configuración</label>
                <input
                  {...form.register("nombre")}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-500"
                  placeholder="Ej: Escenario Base - Verano 2024"
                />
                {form.formState.errors.nombre && (
                  <p className="text-slate-600 text-sm mt-1">{form.formState.errors.nombre.message}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Descripción (opcional)</label>
                <textarea
                  {...form.register("descripcion")}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-500"
                  rows={2}
                  placeholder="Ej: Configuración con estacionalidad invernal moderada y disrupciones típicas"
                />
              </div>
            </CardContent>
          </Card>

          {/* Hub y Política de Inventario */}
          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="bg-slate-50">
              <CardTitle>Hub y Política de Inventario</CardTitle>
              <CardDescription>Configuración del hub de Coyhaique y reglas de reabastecimiento</CardDescription>
            </CardHeader>
            <CardContent className="pt-6 grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Capacidad Hub: {watchedValues.capacidad_hub_tm ?? 0} TM
                </label>
                <input
                  type="range"
                  {...form.register("capacidad_hub_tm", { valueAsNumber: true })}
                  min={100}
                  max={1500}
                  step={10}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>100 TM</span>
                  <span>1500 TM</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Punto de Reorden: {watchedValues.punto_reorden_tm ?? 0} TM
                </label>
                <input
                  type="range"
                  {...form.register("punto_reorden_tm", { valueAsNumber: true })}
                  min={50}
                  max={800}
                  step={5}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>50 TM</span>
                  <span>800 TM</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Cantidad de Pedido: {watchedValues.cantidad_pedido_tm ?? 0} TM
                </label>
                <input
                  type="range"
                  {...form.register("cantidad_pedido_tm", { valueAsNumber: true })}
                  min={50}
                  max={500}
                  step={5}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>50 TM</span>
                  <span>500 TM</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Inventario Inicial: {watchedValues.inventario_inicial_pct ?? 0}% de capacidad
                </label>
                <input
                  type="range"
                  {...form.register("inventario_inicial_pct", { valueAsNumber: true })}
                  min={30}
                  max={100}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>30%</span>
                  <span>100%</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Demanda */}
          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="bg-slate-50">
              <CardTitle>Parámetros de Demanda</CardTitle>
              <CardDescription>Configuración de la demanda diaria y estacionalidad</CardDescription>
            </CardHeader>
            <CardContent className="pt-6 grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Demanda Base Diaria: {(watchedValues.demanda_base_diaria_tm ?? 0).toFixed(1)} TM/día
                </label>
                <input
                  type="range"
                  {...form.register("demanda_base_diaria_tm", { valueAsNumber: true })}
                  min={1}
                  max={20}
                  step={0.1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>1 TM</span>
                  <span>20 TM</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Variabilidad: ±{((watchedValues.variabilidad_demanda ?? 0) * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  {...form.register("variabilidad_demanda", { valueAsNumber: true })}
                  min={0}
                  max={0.5}
                  step={0.01}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>0%</span>
                  <span>50%</span>
                </div>
              </div>

              <div className="col-span-2 border-t border-slate-200 pt-4">
                <div className="flex items-center gap-3 mb-4">
                  <input
                    type="checkbox"
                    {...form.register("usar_estacionalidad")}
                    className="w-4 h-4 text-slate-700 rounded focus:ring-2 focus:ring-slate-500"
                  />
                  <label className="text-sm font-medium">Usar Estacionalidad Invernal</label>
                </div>

                {watchedValues.usar_estacionalidad && (
                  <div className="grid grid-cols-2 gap-6 pl-7">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Amplitud Estacional: ±{((watchedValues.amplitud_estacional ?? 0) * 100).toFixed(0)}%
                      </label>
                      <input
                        type="range"
                        {...form.register("amplitud_estacional", { valueAsNumber: true })}
                        min={0}
                        max={0.5}
                        step={0.01}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-slate-500 mt-1">
                        <span>0%</span>
                        <span>50%</span>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Día Pico Invernal: {watchedValues.dia_pico_invernal ?? 0} (día del año)
                      </label>
                      <input
                        type="range"
                        {...form.register("dia_pico_invernal", { valueAsNumber: true })}
                        min={150}
                        max={250}
                        step={1}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-slate-500 mt-1">
                        <span>Mayo</span>
                        <span>Sept</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Disrupciones */}
          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="bg-slate-50">
              <CardTitle>Disrupciones de la Ruta</CardTitle>
              <CardDescription>Configuración de eventos que bloquean el transporte</CardDescription>
            </CardHeader>
            <CardContent className="pt-6 grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Tasa Anual: {(watchedValues.tasa_disrupciones_anual ?? 0).toFixed(1)} eventos/año
                </label>
                <input
                  type="range"
                  {...form.register("tasa_disrupciones_anual", { valueAsNumber: true })}
                  min={0}
                  max={20}
                  step={0.1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>0</span>
                  <span>20</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Duración Mínima: {watchedValues.duracion_disrupcion_min_dias ?? 0} días
                </label>
                <input
                  type="range"
                  {...form.register("duracion_disrupcion_min_dias", { valueAsNumber: true })}
                  min={1}
                  max={7}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>1 día</span>
                  <span>7 días</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Duración Más Probable: {watchedValues.duracion_disrupcion_mode_dias ?? 0} días
                </label>
                <input
                  type="range"
                  {...form.register("duracion_disrupcion_mode_dias", { valueAsNumber: true })}
                  min={1}
                  max={14}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>1 día</span>
                  <span>14 días</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Duración Máxima: {watchedValues.duracion_disrupcion_max_dias ?? 0} días
                </label>
                <input
                  type="range"
                  {...form.register("duracion_disrupcion_max_dias", { valueAsNumber: true })}
                  min={7}
                  max={60}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>7 días</span>
                  <span>60 días</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Logística y Simulación */}
          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="bg-slate-50">
              <CardTitle>Logística y Simulación</CardTitle>
              <CardDescription>Configuración de tiempos de entrega y horizonte de simulación</CardDescription>
            </CardHeader>
            <CardContent className="pt-6 grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Lead Time Nominal: {watchedValues.lead_time_nominal_dias ?? 0} días
                </label>
                <input
                  type="range"
                  {...form.register("lead_time_nominal_dias", { valueAsNumber: true })}
                  min={1}
                  max={14}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>1 día</span>
                  <span>14 días</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Duración Simulación: {watchedValues.duracion_simulacion_dias ?? 0} días
                </label>
                <input
                  type="range"
                  {...form.register("duracion_simulacion_dias", { valueAsNumber: true })}
                  min={365}
                  max={3650}
                  step={30}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>1 año</span>
                  <span>10 años</span>
                </div>
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium mb-2">
                  Semilla Aleatoria (opcional, dejar vacío para aleatoria)
                </label>
                <input
                  type="number"
                  {...form.register("semilla_aleatoria", { valueAsNumber: true })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Ej: 42"
                />
              </div>
            </CardContent>
          </Card>
        </form>
      </div>
    </div>
  )
}
