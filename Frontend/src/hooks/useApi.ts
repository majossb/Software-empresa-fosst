import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dashboardService } from '@/services/dashboard.service'
import { estandarService } from '@/services/estandar.service'
import { evidenciaService } from '@/services/evidencia.service'
import { hallazgoService } from '@/services/hallazgo.service'
import { planMejoraService } from '@/services/plan-mejora.service'
import { capacitacionService } from '@/services/capacitacion.service'
import { informeService } from '@/services/informe.service'
import { modulo1Service } from '@/services/modulo1.service'
import type { TipoHallazgo, PrioridadPlan, EstadoPlan } from '@/types'

// ── Dashboards ────────────────────────────────────────────────────
export function useDashboardAD() {
  return useQuery({
    queryKey: ['dashboard', 'alta-direccion'],
    queryFn: dashboardService.altaDireccion,
    staleTime: 60000, // Datos frescos por 1 minuto
  })
}

export function useDashboardResp() {
  return useQuery({
    queryKey: ['dashboard', 'responsable'],
    queryFn: dashboardService.responsable,
    staleTime: 60000,
  })
}

export function useDashboardAud() {
  return useQuery({
    queryKey: ['dashboard', 'auditor'],
    queryFn: dashboardService.auditor,
    staleTime: 60000,
  })
}

// ── Estándares ────────────────────────────────────────────────────
export function useEstandaresConRespuestas() {
  return useQuery({
    queryKey: ['estandares', 'respuestas'],
    queryFn: estandarService.conRespuestas,
  })
}

export function useActualizarRespuesta() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ estandarId, data }: { estandarId: string; data: { estado: string; observacion?: string; puntaje?: number } }) =>
      estandarService.actualizarRespuesta(estandarId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['estandares'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

// ── Evidencias ────────────────────────────────────────────────────
export function useEvidencias() {
  return useQuery({
    queryKey: ['evidencias'],
    queryFn: evidenciaService.listar,
  })
}

export function useCrearEvidencia() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: evidenciaService.crear,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['evidencias'] })
      qc.invalidateQueries({ queryKey: ['estandares'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useEliminarEvidencia() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: evidenciaService.eliminar,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['evidencias'] })
      qc.invalidateQueries({ queryKey: ['estandares'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

// ── Hallazgos ─────────────────────────────────────────────────────
export function useHallazgos() {
  return useQuery({
    queryKey: ['hallazgos'],
    queryFn: hallazgoService.listar,
  })
}

export function useCrearHallazgo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Parameters<typeof hallazgoService.crear>[0]) =>
      hallazgoService.crear(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['hallazgos'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['notificaciones'] })
    },
  })
}

export function useActualizarHallazgo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { descripcion?: string; tipo?: TipoHallazgo } }) =>
      hallazgoService.actualizar(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['hallazgos'] })
    },
  })
}

export function useEliminarHallazgo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: hallazgoService.eliminar,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['hallazgos'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

// ── Plan de Mejora ────────────────────────────────────────────────
export function usePlanMejora() {
  return useQuery({
    queryKey: ['plan-mejora'],
    queryFn: planMejoraService.listar,
  })
}

export function useCrearPlanMejora() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { accion: string; responsable: string; prioridad: PrioridadPlan; evaluacion_id?: string }) =>
      planMejoraService.crear(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['plan-mejora'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useActualizarPlanMejora() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { accion?: string; responsable?: string; prioridad?: PrioridadPlan; estado?: EstadoPlan } }) =>
      planMejoraService.actualizar(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['plan-mejora'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

// ── Capacitaciones ────────────────────────────────────────────────
export function useCapacitaciones(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['capacitaciones', params],
    queryFn: () => capacitacionService.listar(params),
  })
}

export function useCapacitacion(id: string | null) {
  return useQuery({
    queryKey: ['capacitaciones', id],
    queryFn: () => capacitacionService.obtener(id!),
    enabled: !!id,
  })
}

export function useCrearCapacitacion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: capacitacionService.crear,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['capacitaciones'] })
    },
  })
}

export function useActualizarCapacitacion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      capacitacionService.actualizar(id, data),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['capacitaciones'] })
      qc.invalidateQueries({ queryKey: ['capacitaciones', variables.id] })
    },
  })
}

export function useInscribirParticipantes() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ capacitacionId, trabajadoresIds }: { capacitacionId: string; trabajadoresIds: string[] }) =>
      capacitacionService.inscribirParticipantes(capacitacionId, trabajadoresIds),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['capacitaciones'] })
      qc.invalidateQueries({ queryKey: ['capacitaciones', variables.capacitacionId] })
    },
  })
}

export function useRegistrarAsistencia() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      capacitacionId,
      participantes,
    }: {
      capacitacionId: string
      participantes: Array<{
        trabajador_id: string
        asistio: boolean
        certificado_url?: string
        soporte_id?: string
        nota_evaluacion?: number | null
        nivel_alcanzado?: number | null
        observaciones?: string
      }>
    }) => capacitacionService.registrarAsistencia(capacitacionId, participantes),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['capacitaciones'] })
      qc.invalidateQueries({ queryKey: ['capacitaciones', variables.capacitacionId] })
    },
  })
}

export function useFinalizarCapacitacion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (capacitacionId: string) => capacitacionService.finalizar(capacitacionId),
    onSuccess: (_data, capacitacionId) => {
      qc.invalidateQueries({ queryKey: ['capacitaciones'] })
      qc.invalidateQueries({ queryKey: ['capacitaciones', capacitacionId] })
      qc.invalidateQueries({ queryKey: ['brechas'] })
      qc.invalidateQueries({ queryKey: ['michc'] })
      qc.invalidateQueries({ queryKey: ['formacion'] })
    },
  })
}

// ── Informes ──────────────────────────────────────────────────────
export function useInformes() {
  return useQuery({
    queryKey: ['informes'],
    queryFn: informeService.listar,
  })
}

export function useGenerarInforme() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: informeService.generar,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['informes'] })
    },
  })
}

export function useInforme(id: string | null) {
  return useQuery({
    queryKey: ['informes', id],
    queryFn: () => informeService.obtener(id!),
    enabled: !!id,
  })
}

// ── Módulo 1: Perfiles de Cargo ──────────────────────────────────────────
export function usePerfilesCargo(filters?: { area?: string; sede_id?: string; incluir_inactivos?: boolean }) {
  return useQuery({
    queryKey: ['perfiles-cargo', filters],
    queryFn: () => modulo1Service.listPerfiles(filters),
  })
}

export function usePerfilCargo(id: string | null) {
  return useQuery({
    queryKey: ['perfil-cargo', id],
    queryFn: () => modulo1Service.getPerfil(id!),
    enabled: !!id,
  })
}

export function useCrearPerfilCargo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: modulo1Service.createPerfil,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['perfiles-cargo'] })
    },
  })
}

export function useActualizarPerfilCargo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => modulo1Service.updatePerfil(id, data),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['perfiles-cargo'] })
      qc.invalidateQueries({ queryKey: ['perfil-cargo', variables.id] })
      qc.invalidateQueries({ queryKey: ['perfil-cargo-versiones', variables.id] })
    },
  })
}

export function useEliminarPerfilCargo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: modulo1Service.deletePerfil,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['perfiles-cargo'] })
    },
  })
}

export function useReactivarPerfilCargo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: modulo1Service.reactivarPerfil,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['perfiles-cargo'] })
    },
  })
}

export function useVersionesPerfilCargo(id: string) {
  return useQuery({
    queryKey: ['perfil-cargo-versiones', id],
    queryFn: () => modulo1Service.getVersiones(id),
    enabled: !!id,
  })
}

export function usePeligrosGTC45() {
  return useQuery({
    queryKey: ['catalogo-peligros-gtc45-v2'],
    queryFn: modulo1Service.listPeligros,
    staleTime: 1000 * 60 * 5,
  })
}

export function useEPPsCatalog() {
  return useQuery({
    queryKey: ['catalogo-epps-v2'],
    queryFn: modulo1Service.listEPPs,
    staleTime: 1000 * 60 * 5,
  })
}

export function useHistorialEvaluaciones() {
  return useQuery({
    queryKey: ['historial-evaluaciones'],
    queryFn: estandarService.getHistorial,
  })
}

