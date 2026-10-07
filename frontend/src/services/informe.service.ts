import { apiClient } from './api.client'
import type { Informe } from '@/types'

export const informeService = {
  listar: () => apiClient.get<Informe[]>('/informes'),

  generar: (data: {
    evaluacion_id: string; tipo: 'auditoria' | 'revision_alta_direccion' | 'ejecutivo'
  }) => apiClient.post<Informe>('/informes/generar', data),

  obtener: (id: string) => apiClient.get<Informe>(`/informes/${id}`),

  guardarBorrador: (id: string, data: { conclusiones?: string; recomendaciones?: string; observaciones_finales?: string }) =>
    apiClient.post<{ success: boolean; message: string; data: Informe }>(`/informes/${id}/guardar-borrador`, data),

  finalizar: (id: string, data: { conclusiones?: string; recomendaciones?: string; observaciones_finales?: string }) =>
    apiClient.post<{ success: boolean; message: string; data: Informe }>(`/informes/${id}/finalizar`, data),

  descartarBorrador: (id: string) =>
    apiClient.delete<{ success: boolean; message: string }>(`/informes/${id}/descartar-borrador`),
}
