import { useState, useEffect } from 'react'
import { Card, Button } from '@/components/ui'
import { BACKEND_URL } from '@/services/api.client'

import {
  gestionHumanaService,
  Trabajador,
  ExpedienteConsolidado,
  NovedadLaboral,
  ExamenMedico,
} from '@/services/gestion-humana.service'
import {
  Users, Stethoscope, FileText, Calendar, Plus,
  CheckCircle2, AlertCircle, ArrowRight, X, ShieldAlert
} from 'lucide-react'

export default function GestionHumanaView() {
  const [trabajadores, setTrabajadores] = useState<Trabajador[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTrabajador, setSelectedTrabajador] = useState<Trabajador | null>(null)
  const [expediente, setExpediente] = useState<ExpedienteConsolidado | null>(null)
  const [loadingExpediente, setLoadingExpediente] = useState(false)

  // Modals state
  const [showNovedadModal, setShowNovedadModal] = useState(false)
  const [showExamenModal, setShowExamenModal] = useState(false)

  useEffect(() => {
    cargarTrabajadores()
  }, [])

  const cargarTrabajadores = async () => {
    setLoading(true)
    try {
      const res = await gestionHumanaService.getTrabajadores()
      setTrabajadores(Array.isArray(res) ? res : res.results || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const verExpediente = async (trabajador: Trabajador) => {
    setSelectedTrabajador(trabajador)
    setLoadingExpediente(true)
    try {
      const exp = await gestionHumanaService.getExpediente(trabajador.id)
      setExpediente(exp)
    } catch (e) {
      console.error(e)
    } finally {
      setLoadingExpediente(false)
    }
  }

  // Bulk Import state
  const [showImportModal, setShowImportModal] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState<any>(null)

  const handleImportSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!importFile) return
    setImporting(true)
    setImportResult(null)
    try {
      const data = await gestionHumanaService.importarMasivo(importFile)
      setImportResult(data)
      if (data.creadas > 0) {
        cargarTrabajadores()
      }
    } catch (err: any) {
      setImportResult({ error: err?.friendlyMessage || err?.message || 'Error al procesar la importación.' })
    } finally {
      setImporting(false)
    }
  }

  const descargarPlantilla = () => {
    const token = localStorage.getItem('token') || ''
    window.open(`${BACKEND_URL}/api/gestion-humana/plantilla-importacion/?token=${token}`, '_blank')
  }


  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Gestión Humana y Administración Laboral
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Expediente consolidado del trabajador: contratación, novedades laborales, exámenes médicos y licencias.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            onClick={descargarPlantilla}
            className="flex items-center gap-1.5"
          >
            <FileText className="w-4 h-4 text-slate-500" />
            Plantilla Excel
          </Button>
          <Button
            variant="secondary"
            onClick={() => { setShowImportModal(true); setImportResult(null); setImportFile(null); }}
            className="flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" />
            Carga Masiva (Excel/CSV)
          </Button>
        </div>
      </div>

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary-500" />
                Carga Masiva de Trabajadores (RF-RH-11)
              </h3>
              <button onClick={() => setShowImportModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleImportSubmit} className="space-y-4">
              <div className="p-4 border-2 border-dashed border-slate-200 rounded-lg text-center space-y-2">
                <input
                  type="file"
                  accept=".xlsx, .csv"
                  onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                  className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
                />
                <p className="text-xs text-slate-400">Archivos soportados: Excel (.xlsx) y CSV (.csv)</p>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <Button type="button" variant="ghost" onClick={() => setShowImportModal(false)}>
                  Cancelar
                </Button>
                <Button type="submit" variant="secondary" disabled={!importFile || importing}>
                  {importing ? "Procesando importación..." : "Iniciar Importación"}
                </Button>
              </div>
            </form>

            {importResult && (
              <div className="space-y-3 pt-3 border-t border-slate-100 max-h-60 overflow-y-auto">
                {importResult.error ? (
                  <p className="text-xs text-rose-600 font-semibold">{importResult.error}</p>
                ) : (
                  <>
                    <div className="flex items-center justify-between text-xs font-bold p-2.5 bg-slate-50 rounded-lg">
                      <span>Total Filas: {importResult.total_filas}</span>
                      <span className="text-emerald-600">Creados: {importResult.creadas}</span>
                      <span className="text-rose-600">Fallidas: {importResult.fallidas}</span>
                    </div>

                    <div className="space-y-1">
                      {importResult.reporte?.map((item: any, idx: number) => (
                        <div
                          key={idx}
                          className={`text-xs p-2 rounded flex items-center justify-between ${
                            item.estado === 'exito' ? 'bg-emerald-50 text-emerald-800' : 'bg-rose-50 text-rose-800'
                          }`}
                        >
                          <span>Fila {item.fila} (Doc: {item.documento})</span>
                          <span className="font-medium">{item.mensaje}</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Grid: Directory & Dossier */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Workers Directory */}
        <div className={selectedTrabajador ? "lg:col-span-1 space-y-4" : "lg:col-span-3 space-y-4"}>
          <Card className="p-4">
            <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
              <Users className="w-4 h-4 text-primary-500" />
              Directorio de Trabajadores ({trabajadores.length})
            </h3>

            {loading ? (
              <div className="py-12 text-center text-slate-400 text-sm">Cargando directorio...</div>
            ) : trabajadores.length === 0 ? (
              <div className="py-12 text-center text-slate-400 text-sm">No se registran trabajadores activos.</div>
            ) : (
              <div className="divide-y divide-slate-100 max-h-[600px] overflow-y-auto pr-1">
                {trabajadores.map((t) => (
                  <div
                    key={t.id}
                    onClick={() => verExpediente(t)}
                    className={`p-3.5 hover:bg-slate-50 transition cursor-pointer flex items-center justify-between rounded-lg ${
                      selectedTrabajador?.id === t.id ? 'bg-primary-50 border border-primary-200' : ''
                    }`}
                  >
                    <div className="space-y-0.5">
                      <p className="text-sm font-semibold text-slate-900">{t.nombre}</p>
                      <p className="text-xs text-slate-500">{t.cargo || 'Sin cargo'} • Doc: {t.documento}</p>
                      <div className="flex items-center gap-2 pt-1">
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600 capitalize">
                          {t.estado_contractual || 'Activo'}
                        </span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded capitalize ${
                          t.estado_operativo === 'habilitado' ? 'bg-emerald-100 text-emerald-700' :
                          t.estado_operativo === 'no_apto' ? 'bg-rose-100 text-rose-700' :
                          'bg-amber-100 text-amber-700'
                        }`}>
                          {t.estado_operativo || 'Pendiente'}
                        </span>
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 text-slate-300" />
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Dossier Viewer */}
        {selectedTrabajador && (
          <div className="lg:col-span-2 space-y-4">
            <Card className="p-5 space-y-6">
              {/* Top Dossier Header */}
              <div className="flex items-start justify-between pb-4 border-b border-slate-100">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">{selectedTrabajador.nombre}</h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Documento: <span className="font-mono text-slate-700 font-medium">{selectedTrabajador.documento}</span> •
                    Cargo: <span className="font-medium text-slate-700">{selectedTrabajador.cargo || 'No asignado'}</span> •
                    Vinculación: <span className="font-medium text-slate-700 capitalize">{selectedTrabajador.tipo_contrato || 'Fijo'}</span>
                  </p>
                </div>
                <button
                  onClick={() => setSelectedTrabajador(null)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {loadingExpediente ? (
                <div className="py-12 text-center text-slate-400 text-sm">Cargando expediente consolidado...</div>
              ) : expediente && (
                <div className="space-y-6">
                  {/* Medical Exams Section */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                        <Stethoscope className="w-4 h-4 text-primary-500" />
                        Historial de Exámenes Médicos Ocupacionales ({expediente.examenes_medicos.length})
                      </h4>
                    </div>

                    {expediente.examenes_medicos.length === 0 ? (
                      <div className="p-3 text-center text-xs text-slate-400 bg-slate-50 rounded-lg">
                        No registra exámenes médicos.
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {expediente.examenes_medicos.map((ex) => (
                          <div key={ex.id} className="p-3 rounded-lg bg-slate-50 border border-slate-100 flex items-start justify-between">
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-semibold text-slate-800 capitalize">
                                  Examen {ex.tipo_display || ex.tipo}
                                </span>
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded capitalize ${
                                  ex.concepto_aptitud === 'apto' ? 'bg-emerald-100 text-emerald-700' :
                                  ex.concepto_aptitud === 'no_apto' ? 'bg-rose-100 text-rose-700' :
                                  'bg-amber-100 text-amber-700'
                                }`}>
                                  {ex.concepto_aptitud_display || ex.concepto_aptitud}
                                </span>
                              </div>
                              <p className="text-xs text-slate-500">
                                Fecha: {ex.fecha_examen} {ex.fecha_vencimiento && `• Vence: ${ex.fecha_vencimiento}`}
                              </p>
                              {ex.presenta_restricciones && (
                                <p className="text-xs text-rose-600 font-medium pt-0.5 flex items-center gap-1">
                                  <AlertCircle className="w-3.5 h-3.5 shrink-0" /> Restricciones: {ex.descripcion_restricciones}
                                </p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Labor Novelties Section */}
                  <div className="space-y-3 pt-4 border-t border-slate-100">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                        <Calendar className="w-4 h-4 text-primary-500" />
                        Novedades Laborales (Vacaciones, Incapacidades, Licencias)
                      </h4>
                    </div>

                    {expediente.novedades.length === 0 ? (
                      <div className="p-3 text-center text-xs text-slate-400 bg-slate-50 rounded-lg">
                        No registra novedades laborales en el periodo.
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {expediente.novedades.map((nov) => (
                          <div key={nov.id} className="p-3 rounded-lg bg-slate-50 border border-slate-100 flex items-start justify-between">
                            <div>
                              <span className="text-xs font-semibold text-slate-800 capitalize">
                                {nov.tipo_display || nov.tipo}
                              </span>
                              <p className="text-xs text-slate-500 mt-0.5">
                                Periodo: {nov.fecha_inicio} al {nov.fecha_fin || 'Vigente'} {nov.dias ? `(${nov.dias} días)` : ''}
                              </p>
                              {nov.observaciones && (
                                <p className="text-xs text-slate-600 mt-1">{nov.observaciones}</p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Driver Licenses Section */}
                  {expediente.licencias_conduccion.length > 0 && (
                    <div className="space-y-3 pt-4 border-t border-slate-100">
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                        Licencias de Conducción
                      </h4>
                      <div className="space-y-2">
                        {expediente.licencias_conduccion.map((lic) => (
                          <div key={lic.id} className="p-3 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-between text-xs">
                            <div>
                              <span className="font-bold text-slate-800">Categoría {lic.categoria}</span>
                              <p className="text-slate-500">Vencimiento: {lic.fecha_vencimiento}</p>
                            </div>
                            {lic.presenta_restricciones && (
                              <span className="text-rose-600 font-medium">Con restricciones</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
