import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  usePerfilesCargo, 
  useEliminarPerfilCargo,
  useReactivarPerfilCargo,
} from '@/hooks/useApi'
import { modulo0Service } from '@/services/modulo0.service'
import type { PerfilCargoListItem } from '@/services/modulo1.service'
import { Card, PageHeader, Badge, Button, Table, TableHeader, TableBody, TableRow, TableHead, TableCell, EmptyState } from '@/components/ui'
import { FormField, Select, Input, LoadingSpinner, ErrorDisplay, Modal } from '@/components/ui/forms'
import { 
  Briefcase, Search, Plus, MapPin, Eye, Edit3, Trash2, 
  AlertTriangle, HelpCircle, Layers, RotateCcw, ShieldAlert
} from 'lucide-react'

export default function PerfilesCargoView() {
  const navigate = useNavigate()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedArea, setSelectedArea] = useState('')
  const [selectedSede, setSelectedSede] = useState('')
  const [errorModalMsg, setErrorModalMsg] = useState<string | null>(null)
  const [incluirInactivos, setIncluirInactivos] = useState(false)
  const [perfilAInhabilitar, setPerfilAInhabilitar] = useState<PerfilCargoListItem | null>(null)

  // Fetch profiles cargo
  const { 
    data: perfiles, 
    isLoading: loadingPerfiles, 
    error: errorPerfiles, 
    refetch 
  } = usePerfilesCargo({
    area: selectedArea || undefined,
    sede_id: selectedSede || undefined,
    incluir_inactivos: incluirInactivos,
  })

  // Fetch sedes for filter
  const { data: sedes } = useQuery({
    queryKey: ['modulo0', 'sedes'],
    queryFn: modulo0Service.listSedes,
  })

  // Delete / reactivate mutations
  const deleteMutation = useEliminarPerfilCargo()
  const reactivarMutation = useReactivarPerfilCargo()

  // Extract unique areas from profiles for the filter dropdown
  const uniqueAreas = perfiles 
    ? Array.from(new Set(perfiles.map(p => p.area).filter(Boolean) as string[]))
    : []

  // Filter profiles by search term (code or cargo name) locally
  const filteredPerfiles = perfiles?.filter(p => {
    const term = searchTerm.toLowerCase()
    return (
      p.nombre_cargo.toLowerCase().includes(term) ||
      p.codigo.toLowerCase().includes(term) ||
      (p.area && p.area.toLowerCase().includes(term))
    )
  })

  const abrirInhabilitar = (perfil: PerfilCargoListItem) => setPerfilAInhabilitar(perfil)

  const confirmarInhabilitar = async () => {
    if (!perfilAInhabilitar) return
    try {
      await deleteMutation.mutateAsync(perfilAInhabilitar.id)
      setPerfilAInhabilitar(null)
    } catch (err: any) {
      setPerfilAInhabilitar(null)
      // 409: trabajadores, vacantes activas o procesos activos
      setErrorModalMsg(err.message || 'No se pudo inhabilitar el perfil de cargo.')
    }
  }

  const handleReactivar = async (perfil: PerfilCargoListItem) => {
    try {
      await reactivarMutation.mutateAsync(perfil.id)
    } catch (err: any) {
      setErrorModalMsg(err.message || 'No se pudo reactivar el perfil de cargo.')
    }
  }

  if (loadingPerfiles) {
    return <LoadingSpinner text="Cargando perfiles de cargo..." />
  }

  if (errorPerfiles) {
    return <ErrorDisplay message={(errorPerfiles as Error).message} onRetry={refetch} />
  }

  return (
    <div className="animate-fade-in space-y-6">
      {/* Page Header */}
      <PageHeader 
        title="Gestión de Perfiles de Cargo" 
        subtitle="Administra los perfiles de cargo de la empresa, define sus requisitos, peligros GTC-45 y genera las actas de perfil."
        actions={
          <Button 
            onClick={() => navigate('/app/responsable/perfiles-cargo/nuevo')} 
            variant="primary" 
            icon={<Plus className="w-4 h-4" />}
          >
            Crear Perfil de Cargo
          </Button>
        }
      />

      {/* KPI/Brief statistics overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-gradient-to-br from-slate-900 to-slate-800 text-white border-none shadow-lg">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Perfiles Activos</p>
              <h3 className="text-4xl font-extrabold mt-1 text-white">{perfiles?.filter(p => p.activo !== false).length || 0}</h3>
            </div>
            <div className="p-3 bg-white/10 rounded-2xl">
              <Briefcase className="w-6 h-6 text-brand-400" />
            </div>
          </div>
          <p className="text-[11px] text-slate-400 mt-4">Perfiles de cargo estructurados en el SG-SST</p>
        </Card>

        <Card className="bg-white border border-surface-2 shadow-sm">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Áreas Funcionales</p>
              <h3 className="text-4xl font-extrabold mt-1 text-primary-500">{uniqueAreas.length}</h3>
            </div>
            <div className="p-3 bg-brand-50 rounded-2xl">
              <Layers className="w-6 h-6 text-brand-600" />
            </div>
          </div>
          <p className="text-[11px] text-slate-500 mt-4">Áreas registradas con cargos correspondientes</p>
        </Card>

        <Card className="bg-white border border-surface-2 shadow-sm">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Personal Vinculado</p>
              <h3 className="text-4xl font-extrabold mt-1 text-green-700">
                {perfiles?.reduce((sum, p) => sum + (p.trabajadores_count || 0), 0) || 0}
              </h3>
            </div>
            <div className="p-3 bg-green-50 rounded-2xl">
              <div className="w-6 h-6 rounded bg-green-600/10 flex items-center justify-center font-bold text-green-700 text-xs">CO</div>
            </div>
          </div>
          <p className="text-[11px] text-slate-500 mt-4">Trabajadores con perfil asignado actualmente</p>
        </Card>
      </div>

      {/* Filters and search panel */}
      <Card title="Filtros de Búsqueda">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <FormField label="Buscar por Cargo o Código">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Ej: Auxiliar, Administrativo, PC-..."
                className="pl-9"
              />
            </div>
          </FormField>

          <FormField label="Filtrar por Área">
            <Select 
              value={selectedArea}
              onChange={(e) => setSelectedArea(e.target.value)}
              options={[
                { value: '', label: 'Todas las áreas' },
                ...uniqueAreas.map(area => ({ value: area, label: area }))
              ]}
            />
          </FormField>

          <FormField label="Filtrar por Sede">
            <Select 
              value={selectedSede}
              onChange={(e) => setSelectedSede(e.target.value)}
              options={[
                { value: '', label: 'Todas las sedes' },
                ...(sedes?.map(s => ({ value: s.id, label: s.nombre })) || [])
              ]}
            />
          </FormField>
        </div>

        <label className="flex items-center gap-2 mt-4 text-xs text-slate-600 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={incluirInactivos}
            onChange={(e) => setIncluirInactivos(e.target.checked)}
            className="rounded text-primary-500"
          />
          Mostrar perfiles inhabilitados
        </label>
      </Card>

      {/* Main Table */}
      <Card>
        {filteredPerfiles && filteredPerfiles.length > 0 ? (
          <div className="overflow-x-auto -mx-5 px-5">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-0">Código</TableHead>
                  <TableHead>Nombre del Cargo</TableHead>
                  <TableHead>Área</TableHead>
                  <TableHead>Sede</TableHead>
                  <TableHead className="text-center">Estado</TableHead>
                  <TableHead className="text-center">Versión</TableHead>
                  <TableHead className="text-center">Trabajadores</TableHead>
                  <TableHead className="text-right pr-0">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPerfiles.map((perfil) => (
                  <TableRow key={perfil.id} className="group">
                    <TableCell className="pl-0 font-bold text-slate-700">
                      <span 
                        onClick={() => navigate(`/app/responsable/perfiles-cargo/${perfil.id}`)}
                        className="cursor-pointer text-brand-600 hover:text-brand-700 hover:underline"
                      >
                        {perfil.codigo}
                      </span>
                    </TableCell>
                    <TableCell className="font-bold text-slate-800 text-sm">
                      {perfil.nombre_cargo}
                    </TableCell>
                    <TableCell className="text-slate-600">
                      {perfil.area || <span className="text-slate-400 italic">No especificada</span>}
                    </TableCell>
                    <TableCell className="text-slate-600">
                      {perfil.sede_nombre || perfil.sede ? (
                        <span className="flex items-center gap-1.5">
                          <MapPin className="w-3.5 h-3.5 text-slate-400" />
                          <span>
                            {perfil.sede_nombre || perfil.sede}
                            {perfil.sede_ciudad && (
                              <span className="block text-[10px] text-slate-400">{perfil.sede_ciudad}</span>
                            )}
                          </span>
                        </span>
                      ) : (
                        <span className="text-slate-400 italic">No especificada</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant={perfil.activo === false ? 'gray' : 'green'}>
                        {perfil.activo === false ? 'Inhabilitado' : 'Activo'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant="blue">v{perfil.version_actual}</Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant={(perfil.trabajadores_count || 0) > 0 ? 'green' : 'gray'}>
                        {perfil.trabajadores_count || 0} {(perfil.trabajadores_count || 0) === 1 ? 'activo' : 'activos'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right pr-0">
                      <div className="flex justify-end gap-1.5 opacity-80 group-hover:opacity-100 transition-opacity">
                        {perfil.activo === false ? (
                          <button
                            onClick={() => handleReactivar(perfil)}
                            disabled={reactivarMutation.isPending}
                            className="px-2.5 py-1.5 rounded-xl text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 transition-all disabled:opacity-50 flex items-center gap-1"
                            title="Reactivar perfil"
                          >
                            <RotateCcw className="w-3.5 h-3.5" />
                            Reactivar
                          </button>
                        ) : (
                          <>
                            <button
                              onClick={() => navigate(`/app/responsable/perfiles-cargo/${perfil.id}`)}
                              className="p-2 rounded-xl text-slate-500 hover:text-brand-600 hover:bg-slate-100 transition-all"
                              title="Ver ficha técnica"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => navigate(`/app/responsable/perfiles-cargo/${perfil.id}/editar`)}
                              className="p-2 rounded-xl text-slate-500 hover:text-brand-600 hover:bg-slate-100 transition-all"
                              title="Editar perfil"
                            >
                              <Edit3 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => abrirInhabilitar(perfil)}
                              className="p-2 rounded-xl text-slate-500 hover:text-red-600 hover:bg-red-50 transition-all"
                              title="Inhabilitar perfil"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          <EmptyState
            icon={<Briefcase className="w-7 h-7" />}
            title="Sin Perfiles de Cargo"
            description={
              searchTerm || selectedArea || selectedSede 
                ? 'Ningún perfil de cargo coincide con los filtros aplicados en la búsqueda.' 
                : 'Aún no se han registrado perfiles de cargo en tu organización. Comienza por crear el primero.'
            }
            action={
              searchTerm || selectedArea || selectedSede ? (
                <Button 
                  onClick={() => {
                    setSearchTerm('')
                    setSelectedArea('')
                    setSelectedSede('')
                  }} 
                  variant="ghost"
                >
                  Limpiar Filtros
                </Button>
              ) : (
                <Button 
                  onClick={() => navigate('/app/responsable/perfiles-cargo/nuevo')} 
                  variant="primary" 
                  icon={<Plus className="w-4 h-4" />}
                >
                  Registrar Cargo
                </Button>
              )
            }
          />
        )}
      </Card>

      {/* Modal de confirmación: inhabilitar perfil (con dependencias) */}
      <Modal
        open={!!perfilAInhabilitar}
        onClose={() => setPerfilAInhabilitar(null)}
        title="Inhabilitar perfil de cargo"
        maxWidth="520px"
        footer={
          <>
            <Button variant="secondary" onClick={() => setPerfilAInhabilitar(null)}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              className="bg-red-600 hover:bg-red-700 border-none text-white"
              disabled={
                !perfilAInhabilitar ||
                deleteMutation.isPending ||
                (perfilAInhabilitar.trabajadores_count || 0) > 0 ||
                (perfilAInhabilitar.vacantes_activas_count || 0) > 0 ||
                (perfilAInhabilitar.procesos_activos_count || 0) > 0
              }
              onClick={confirmarInhabilitar}
            >
              Inhabilitar
            </Button>
          </>
        }
      >
        {perfilAInhabilitar && (() => {
          const trabajadores = perfilAInhabilitar.trabajadores_count || 0
          const vacantes = perfilAInhabilitar.vacantes_activas_count || 0
          const procesos = perfilAInhabilitar.procesos_activos_count || 0
          const bloqueado = trabajadores > 0 || vacantes > 0 || procesos > 0
          return (
            <div className="space-y-4 text-xs">
              <p className="text-slate-600 leading-relaxed">
                El perfil <b>{perfilAInhabilitar.nombre_cargo}</b> ({perfilAInhabilitar.codigo}) quedará <b>inhabilitado</b>.
                No se borran datos: las vacantes, los procesos y el histórico se conservan, y podrás reactivarlo después.
              </p>

              <div className="grid grid-cols-3 gap-2">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
                  <div className="text-lg font-bold text-slate-800">{trabajadores}</div>
                  <div className="text-[10px] text-slate-500">Trabajadores</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
                  <div className="text-lg font-bold text-slate-800">{vacantes}</div>
                  <div className="text-[10px] text-slate-500">Vacantes activas</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
                  <div className="text-lg font-bold text-slate-800">{procesos}</div>
                  <div className="text-[10px] text-slate-500">Procesos activos</div>
                </div>
              </div>

              {bloqueado ? (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 flex gap-2">
                  <ShieldAlert className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <div className="space-y-1">
                    <p className="font-bold">No se puede inhabilitar todavía</p>
                    <p>Reasigna a los trabajadores o cierra las vacantes/procesos activos primero.</p>
                  </div>
                </div>
              ) : (
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 flex gap-2">
                  <RotateCcw className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <p>Sin dependencias activas. Podrás reactivarlo cuando lo necesites.</p>
                </div>
              )}
            </div>
          )
        })()}
      </Modal>

      {/* Error Warning Modal (Conflict 409) */}
      <Modal
        open={!!errorModalMsg}
        onClose={() => setErrorModalMsg(null)}
        title="No se pudo inhabilitar"
        maxWidth="440px"
        footer={
          <Button 
            onClick={() => setErrorModalMsg(null)} 
            variant="primary" 
            className="text-xs px-5 py-2 bg-red-600 hover:bg-red-700 shadow-md shadow-red-500/10 border-none"
          >
            Entendido
          </Button>
        }
      >
        <div className="space-y-3">
          <p className="text-xs text-slate-600 leading-relaxed">
            {errorModalMsg}
          </p>
          <div className="p-3 bg-slate-50 rounded-xl flex gap-2.5 items-start border border-slate-100">
            <HelpCircle className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
            <p className="text-[10px] text-slate-500 leading-tight">
              Para inhabilitar este perfil, primero reasigna a los trabajadores activos y cierra o finaliza las vacantes y procesos de selección asociados. El histórico no se pierde.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  )
}
