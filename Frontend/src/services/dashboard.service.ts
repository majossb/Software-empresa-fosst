import { apiClient } from './api.client'
import type { DashboardAD, DashboardResp, DashboardAud } from '@/types'

export const dashboardService = {
  altaDireccion: () => apiClient.get<DashboardAD>('/dashboard/alta-direccion'),
  responsable:   () => apiClient.get<DashboardResp>('/dashboard/responsable'),
  auditor:       () => apiClient.get<DashboardAud>('/dashboard/auditor'),
}
