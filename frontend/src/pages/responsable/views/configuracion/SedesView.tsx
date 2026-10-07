import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { modulo0Service, Sede } from '@/services/modulo0.service'
import { Card, Button, EmptyState } from '@/components/ui'
import { FormField, Input, Modal, LoadingSpinner } from '@/components/ui/forms'
import { MapPin, Phone, User, Trash2, Edit2, Star, AlertTriangle, Plus, Landmark } from 'lucide-react'
import { MUNICIPIOS_POR_DEPARTAMENTO } from '@/data/colombiaData'

export default function SedesView() {
  const queryClient = useQueryClient()
  const [modalOpen, setModalOpen] = useState(false)
  const [editingSede, setEditingSede] = useState<Sede | null>(null)
  
  // Form state
  const [nombre, setNombre] = useState('')
  const [departamento, setDepartamento] = useState('')
  const [municipio, setMunicipio] = useState('')
  const [direccion, setDireccion] = useState('')
  const [telefono, setTelefono] = useState('')
  const [responsable, setResponsable] = useState('')
  const [esPrincipal, setEsPrincipal] = useState(false)
  
  const [errorMsg, setErrorMsg] = useState('')

  const { data: sedes, isLoading, error, refetch } = useQuery({
    queryKey: ['modulo0', 'sedes'],
    queryFn: modulo0Service.listSedes,
  })

  const createMutation = useMutation({
    mutationFn: modulo0Service.createSede,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      closeModal()
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Error al crear la sede.')
    }
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Sede> }) => modulo0Service.updateSede(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
      closeModal()
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Error al actualizar la sede.')
    }
  })

  const deleteMutation = useMutation({
    mutationFn: modulo0Service.deleteSede,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modulo0'] })
    },
    onError: (err: any) => {
      alert(err.message || 'No se pudo eliminar la sede.')
    }
  })

  const openAddModal = () => {
    setEditingSede(null)
    setNombre('')
    setDepartamento('')
    setMunicipio('')
    setDireccion('')
    setTelefono('')
    setResponsable('')
    setEsPrincipal(false)
    setErrorMsg('')
    setModalOpen(true)
  }

  const openEditModal = (sede: Sede) => {
    setEditingSede(sede)
    setNombre(sede.nombre)
    if (sede.ciudad && sede.ciudad.includes(' - ')) {
      const [dep, mun] = sede.ciudad.split(' - ')
      setDepartamento(dep)
      setMunicipio(mun)
    } else {
      setDepartamento('')
      setMunicipio(sede.ciudad || '')
    }
    setDireccion(sede.direccion || '')
    setTelefono(sede.telefono || '')
    setResponsable(sede.responsable || '')
    setEsPrincipal(sede.es_principal)
    setErrorMsg('')
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    setEditingSede(null)
    setErrorMsg('')
  }

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!nombre.trim() || !departamento.trim() || !municipio.trim()) {
      setErrorMsg('El nombre de la sede, el departamento y el municipio son requeridos.')
      return
    }

    const payload = {
      nombre: nombre.trim(),
      ciudad: `${departamento} - ${municipio}`,
      direccion: direccion.trim() || null,
      telefono: telefono.trim() || null,
      responsable: responsable.trim() || null,
      es_principal: esPrincipal,
    }

    if (editingSede) {
      updateMutation.mutate({ id: editingSede.id, data: payload })
    } else {
      createMutation.mutate(payload)
    }
  }

  const handleDelete = (sede: Sede) => {
    const workersCount = sede._count?.trabajadores ?? 0
    if (workersCount > 0) {
      alert(`Acción bloqueada: La sede "${sede.nombre}" tiene ${workersCount} trabajadores asignados. Reasígnelos antes de eliminarla.`)
      return
    }
    if (confirm(`¿Está seguro de que desea eliminar la sede "${sede.nombre}"?`)) {
      deleteMutation.mutate(sede.id)
    }
  }

  if (isLoading) {
    return <LoadingSpinner text="Cargando sedes operativas..." />
  }

  return (
    <div className="space-y-6">
      {/* Cabecera */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-md font-bold text-slate-800 flex items-center gap-2">
            <Landmark className="w-5 h-5 text-brand-500" />
            Sedes Operativas
          </h2>
          <p className="text-xs text-slate-500">
            Administra las ubicaciones físicas de tu empresa y el personal asignado a cada una.
          </p>
        </div>
        <Button onClick={openAddModal} variant="primary" icon={<Plus className="w-4 h-4" />} className="text-xs py-2 px-3">
          Agregar Sede
        </Button>
      </div>

      {/* Grid de Sedes */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sedes?.map((sede) => {
          const workersCount = sede._count?.trabajadores ?? 0
          return (
            <div
              key={sede.id}
              className={`
                relative p-5 rounded-2xl border transition-all duration-300 overflow-hidden bg-white group
                ${sede.es_principal 
                  ? 'border-brand-300 shadow-md shadow-brand-500/5 hover:border-brand-400' 
                  : 'border-surface-2 hover:border-slate-300 hover:shadow-lg hover:shadow-slate-100'
                }
              `}
            >
              {/* Esquina superior con badge o estrella */}
              {sede.es_principal && (
                <div className="absolute top-0 right-0 bg-gradient-to-l from-brand-500 to-brand-400 text-white text-[10px] font-black px-3.5 py-1 rounded-bl-xl flex items-center gap-1">
                  <Star className="w-3 h-3 fill-white" /> Principal
                </div>
              )}

              {/* Información */}
              <div className="space-y-3">
                <div>
                  <h3 className="font-bold text-slate-800 pr-16 group-hover:text-brand-700 transition-colors">
                    {sede.nombre}
                  </h3>
                  <span className="inline-block text-[10px] font-semibold text-slate-400 bg-surface px-2 py-0.5 rounded-md mt-1">
                    {sede.ciudad}
                  </span>
                </div>

                <div className="space-y-1.5 text-xs text-slate-500">
                  {sede.direccion && (
                    <div className="flex items-center gap-2">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      <span>{sede.direccion}</span>
                    </div>
                  )}
                  {sede.telefono && (
                    <div className="flex items-center gap-2">
                      <Phone className="w-3.5 h-3.5 text-slate-400" />
                      <span>{sede.telefono}</span>
                    </div>
                  )}
                  {sede.responsable && (
                    <div className="flex items-center gap-2">
                      <User className="w-3.5 h-3.5 text-slate-400" />
                      <span className="font-semibold text-slate-600">Resp: {sede.responsable}</span>
                    </div>
                  )}
                </div>

                <hr className="border-surface-2 my-2" />

                {/* Footer Tarjeta */}
                <div className="flex justify-between items-center">
                  <span className={`text-[11px] font-bold ${workersCount > 0 ? 'text-brand-600 bg-brand-50' : 'text-slate-400 bg-surface'} px-2.5 py-1 rounded-lg`}>
                    {workersCount} {workersCount === 1 ? 'trabajador' : 'trabajadores'}
                  </span>

                  <div className="flex gap-1">
                    <button
                      onClick={() => openEditModal(sede)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-brand-600 hover:bg-slate-50 transition-colors"
                      title="Editar sede"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(sede)}
                      disabled={workersCount > 0}
                      className={`
                        p-1.5 rounded-lg transition-colors
                        ${workersCount > 0 
                          ? 'text-slate-300 cursor-not-allowed' 
                          : 'text-slate-400 hover:text-red-500 hover:bg-red-50'
                        }
                      `}
                      title={workersCount > 0 ? 'No se puede eliminar: tiene trabajadores vinculados' : 'Eliminar sede'}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )
        })}

        {(!sedes || sedes.length === 0) && (
          <div className="col-span-full">
            <EmptyState
              icon={<MapPin className="w-7 h-7" />}
              title="Sin Sedes Registradas"
              description="Para estructurar adecuadamente el SG-SST, registra al menos la sede operativa principal de tu organización."
              action={
                <Button onClick={openAddModal} variant="primary" icon={<Plus className="w-4 h-4" />} className="text-xs">
                  Registrar primera sede
                </Button>
              }
            />
          </div>
        )}
      </div>

      {/* Modal */}
      <Modal 
        open={modalOpen} 
        onClose={closeModal} 
        title={editingSede ? 'Editar Sede Operativa' : 'Agregar Nueva Sede'}
        footer={
          <>
            <Button type="button" onClick={closeModal} variant="secondary" className="text-xs py-2 px-4">
              Cancelar
            </Button>
            <Button
              onClick={handleSubmit}
              variant="primary"
              className="text-xs py-2 px-5"
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              {editingSede ? 'Guardar Cambios' : 'Registrar Sede'}
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {errorMsg && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <FormField label="Nombre de la Sede" required>
            <Input
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Ej: Sede Norte, Planta Principal"
              required
            />
          </FormField>

          <FormField label="Departamento" required>
            <select
              value={departamento}
              onChange={(e) => {
                setDepartamento(e.target.value)
                setMunicipio('')
              }}
              required
              className="w-full text-sm border border-surface-2 rounded-xl px-3 py-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-400 disabled:bg-slate-50 disabled:text-slate-400"
            >
              <option value="">Selecciona un departamento…</option>
              {Object.keys(MUNICIPIOS_POR_DEPARTAMENTO).sort().map((dep) => (
                <option key={dep} value={dep}>{dep}</option>
              ))}
            </select>
          </FormField>

          <FormField label="Municipio" required>
            <select
              value={municipio}
              onChange={(e) => setMunicipio(e.target.value)}
              required
              disabled={!departamento}
              className="w-full text-sm border border-surface-2 rounded-xl px-3 py-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-400 disabled:bg-slate-50 disabled:text-slate-400 disabled:cursor-not-allowed"
            >
              <option value="">
                {departamento ? 'Selecciona un municipio…' : 'Primero selecciona un departamento'}
              </option>
              {departamento &&
                MUNICIPIOS_POR_DEPARTAMENTO[departamento]?.map((mun) => (
                  <option key={mun} value={mun}>{mun}</option>
                ))}
            </select>
          </FormField>

          <FormField label="Dirección de la Sede">
            <Input
              value={direccion}
              onChange={(e) => setDireccion(e.target.value)}
              placeholder="Ej: Calle 100 # 15-30"
            />
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField label="Teléfono de Contacto">
              <Input
                value={telefono}
                onChange={(e) => setTelefono(e.target.value)}
                placeholder="Ej: 3001234567"
              />
            </FormField>

            <FormField label="Responsable de Sede">
              <Input
                value={responsable}
                onChange={(e) => setResponsable(e.target.value)}
                placeholder="Ej: Juan Pérez"
              />
            </FormField>
          </div>

          <div className="pt-2">
            <label className="flex items-center gap-2.5 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={esPrincipal}
                onChange={(e) => setEsPrincipal(e.target.checked)}
                className="w-4 h-4 rounded text-brand-500 focus:ring-brand-500 border-surface-2"
              />
              <div>
                <span className="text-xs font-bold text-slate-800 flex items-center gap-1">
                  <Star className={`w-3.5 h-3.5 ${esPrincipal ? 'text-brand-500 fill-brand-500' : 'text-slate-400'}`} />
                  Establecer como Sede Principal
                </span>
                <p className="text-[10px] text-slate-400 leading-tight">
                  Al activar esta opción, las demás sedes dejarán de ser consideradas como la sede principal.
                </p>
              </div>
            </label>
          </div>
        </form>
      </Modal>
    </div>
  )
}