import { useState, useEffect, useRef } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { reclutamientoService } from '@/services/reclutamiento.service'
import { VacantePublicaDetail } from '@/types/reclutamiento.types'
import {
  Briefcase, MapPin, Building2, CheckCircle2,
  ArrowLeft, Send, Check, FileText,
  UploadCloud, X, Zap, Sparkles
} from 'lucide-react'

const PROFILE_STORAGE_KEY = 'fosst_candidato_profile'

export default function PortalVacanteDetailPage() {
  const { slugOrId } = useParams<{ slugOrId: string }>()
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [vacante, setVacante] = useState<VacantePublicaDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [quickApplying, setQuickApplying] = useState(false)
  const [isAutoFilled, setIsAutoFilled] = useState(false)
  const [hasCandidateSession, setHasCandidateSession] = useState(false)

  // Archivo Hoja de Vida
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [savedResumeName, setSavedResumeName] = useState<string | null>(null)

  const [successData, setSuccessData] = useState<{
    codigo_otp: string
    token_acceso: string
  } | null>(null)

  // Form de postulación
  const [form, setForm] = useState({
    tipo_documento: 'CC',
    documento: '',
    nombres: '',
    apellidos: '',
    email: '',
    telefono: '',
    ciudad: '',
    direccion: '',
    titulo_profesional: '',
    nivel_educativo: 'universitario',
    anios_experiencia: 1,
    aspiracion_salarial: '',
    resumen_profesional: '',
    autoriza_tratamiento_datos: false,
  })

  useEffect(() => {
    if (slugOrId) {
      cargarDetalle(slugOrId)
    }
    cargarDatosPrevios()
  }, [slugOrId])

  const cargarDetalle = async (idOrSlug: string) => {
    setLoading(true)
    try {
      const data = await reclutamientoService.getVacantePublicaDetail(idOrSlug)
      setVacante(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const cargarDatosPrevios = async () => {
    // 1. Verificar si hay token de sesión activa del candidato
    const token = reclutamientoService.getCandidateToken()
    if (token) {
      setHasCandidateSession(true)
      try {
        const perfil = await reclutamientoService.getMiPerfil()
        if (perfil) {
          aplicarPerfil(perfil)
          return
        }
      } catch (err) {
        console.warn('No se pudo cargar sesión de candidato:', err)
      }
    }

    // 2. Fallback a perfil guardado en LocalStorage
    try {
      const stored = localStorage.getItem(PROFILE_STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        aplicarPerfil(parsed)
      }
    } catch (err) {
      console.warn('Error leyendo localStorage de candidato:', err)
    }
  }

  const aplicarPerfil = (data: any) => {
    setForm(prev => ({
      ...prev,
      tipo_documento: data.tipo_documento || prev.tipo_documento,
      documento: data.documento || prev.documento,
      nombres: data.nombres || prev.nombres,
      apellidos: data.apellidos || prev.apellidos,
      email: data.email || prev.email,
      telefono: data.telefono || prev.telefono,
      ciudad: data.ciudad || prev.ciudad,
      direccion: data.direccion || prev.direccion,
      titulo_profesional: data.titulo_profesional || prev.titulo_profesional,
      nivel_educativo: data.nivel_educativo || prev.nivel_educativo,
      anios_experiencia: data.anios_experiencia !== undefined ? data.anios_experiencia : prev.anios_experiencia,
      aspiracion_salarial: data.aspiracion_salarial ? String(data.aspiracion_salarial) : prev.aspiracion_salarial,
      resumen_profesional: data.resumen_profesional || prev.resumen_profesional,
      autoriza_tratamiento_datos: true,
    }))

    if (data.ultima_hoja_vida?.nombre) {
      setSavedResumeName(data.ultima_hoja_vida.nombre)
    } else if (data.saved_cv_name) {
      setSavedResumeName(data.saved_cv_name)
    }

    setIsAutoFilled(true)
  }

  const handleBlurDocumentoOEmail = async () => {
    if (!form.email && !form.documento) return
    if (form.nombres && form.apellidos) return // Ya tiene datos

    try {
      const res = await reclutamientoService.buscarPerfilPrevio(form.email, form.documento)
      if (res.encontrado && res.datos) {
        aplicarPerfil(res.datos)
      }
    } catch (err) {
      // Silencioso
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      if (file.size > 15 * 1024 * 1024) {
        alert('El archivo no debe superar 15 MB.')
        return
      }
      setSelectedFile(file)
    }
  }

  const handleQuickApply = async () => {
    if (!slugOrId) return
    setQuickApplying(true)
    try {
      const res = await reclutamientoService.postularRapido(slugOrId)
      setSuccessData({
        codigo_otp: res.codigo_otp,
        token_acceso: res.token_acceso,
      })
    } catch (err: any) {
      alert(err.message || 'Error en postulación rápida.')
    } finally {
      setQuickApplying(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.autoriza_tratamiento_datos) {
      alert('Debe autorizar el tratamiento de datos personales (Habeas Data Ley 1581 de 2012).')
      return
    }
    if (!slugOrId) return

    setSubmitting(true)
    try {
      const formData = new FormData()
      formData.append('tipo_documento', form.tipo_documento)
      formData.append('documento', form.documento)
      formData.append('nombres', form.nombres)
      formData.append('apellidos', form.apellidos)
      formData.append('email', form.email)
      formData.append('telefono', form.telefono || '')
      formData.append('ciudad', form.ciudad || '')
      formData.append('direccion', form.direccion || '')
      formData.append('titulo_profesional', form.titulo_profesional || '')
      formData.append('nivel_educativo', form.nivel_educativo || 'universitario')
      formData.append('anios_experiencia', String(Number(form.anios_experiencia) || 0))
      if (form.aspiracion_salarial) {
        formData.append('aspiracion_salarial', String(Number(form.aspiracion_salarial)))
      }
      formData.append('resumen_profesional', form.resumen_profesional || '')
      formData.append('autoriza_tratamiento_datos', 'true')

      if (selectedFile) {
        formData.append('archivo_cv', selectedFile)
      }

      const res = await reclutamientoService.postularPublicamente(slugOrId, formData)

      // Guardar perfil en LocalStorage para futuras postulaciones
      localStorage.setItem(
        PROFILE_STORAGE_KEY,
        JSON.stringify({
          ...form,
          saved_cv_name: selectedFile ? selectedFile.name : savedResumeName,
        })
      )

      setSuccessData({
        codigo_otp: res.codigo_otp,
        token_acceso: res.token_acceso,
      })
    } catch (err: any) {
      alert(err.message || 'Ocurrió un error al enviar su postulación.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 text-slate-400 flex items-center justify-center text-sm">
        Cargando detalles de la vacante...
      </div>
    )
  }

  if (!vacante) {
    return (
      <div className="min-h-screen bg-slate-900 text-slate-400 flex flex-col items-center justify-center space-y-4">
        <p className="text-base text-white">La vacante no existe o ya no está disponible.</p>
        <Link to="/empleos" className="text-xs text-emerald-400 font-bold hover:underline">
          Volver al catálogo de empleos
        </Link>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 py-10 px-4">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* ── Botón Volver ──────────────────────────────────────── */}
        <Link
          to="/empleos"
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-400 hover:text-white transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver a todas las vacantes
        </Link>

        {/* ── Mensaje de Éxito al Postular ──────────────────────── */}
        {successData ? (
          <div className="p-8 rounded-2xl bg-emerald-950/40 border border-emerald-500/40 text-center space-y-4 max-w-xl mx-auto">
            <div className="w-14 h-14 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
              <Check className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-extrabold text-white">¡Postulación Enviada con Éxito!</h2>
            <p className="text-sm text-slate-300">
              Hemos recibido tus datos correctamente para la vacante <strong>{vacante.titulo}</strong>.
            </p>

            <div className="p-4 bg-slate-900/80 rounded-xl border border-emerald-500/20 text-xs space-y-2 text-left">
              <div className="flex justify-between items-center font-mono">
                <span className="text-slate-400">Tu código OTP de acceso:</span>
                <span className="text-lg font-bold text-emerald-400 tracking-widest">{successData.codigo_otp}</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Guarda este código o usa tu correo electrónico para consultar el avance de tus postulaciones en cualquier momento.
              </p>
            </div>

            <div className="pt-2 flex justify-center gap-3">
              <button
                onClick={() => navigate('/portal/seguimiento')}
                className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-bold text-xs text-white transition"
              >
                Ir a Consultar Mis Procesos
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* ── Columna Izquierda: Información de la Vacante ─── */}
            <div className="lg:col-span-1 space-y-6">
              <div className="p-6 rounded-2xl bg-slate-800/80 border border-slate-700/80 space-y-4">
                <div className="space-y-1">
                  <span className="text-xs font-mono font-bold text-emerald-400">{vacante.codigo}</span>
                  <h1 className="text-xl font-bold text-white leading-tight">{vacante.titulo}</h1>
                  <p className="text-xs text-slate-400 flex items-center gap-1">
                    <Building2 className="w-3.5 h-3.5 text-slate-500" />
                    {vacante.empresa_nombre}
                  </p>
                </div>

                <div className="space-y-2 pt-3 border-t border-slate-700 text-xs text-slate-300">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-emerald-400" />
                    <span>{vacante.sede_ciudad || 'Colombia'} ({vacante.modalidad_display})</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Briefcase className="w-4 h-4 text-emerald-400" />
                    <span>{vacante.tipo_contrato || 'Contrato laboral'}</span>
                  </div>
                  <div className="flex items-center gap-2 font-mono font-bold text-emerald-300">
                    <span>{vacante.salario_display}</span>
                  </div>
                </div>

                {vacante.descripcion_publica && (
                  <div className="pt-3 border-t border-slate-700 text-xs text-slate-300 space-y-1.5">
                    <span className="font-bold text-white block">Descripción del Cargo:</span>
                    <p className="leading-relaxed whitespace-pre-line text-slate-400">{vacante.descripcion_publica}</p>
                  </div>
                )}

                {vacante.requisitos_obligatorios?.length > 0 && (
                  <div className="pt-3 border-t border-slate-700 text-xs space-y-2">
                    <span className="font-bold text-white block">Requisitos Obligatorios:</span>
                    <ul className="space-y-1.5 text-slate-300">
                      {vacante.requisitos_obligatorios.map((req, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                          <span>{req}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Botón de Postulación Rápida si tiene sesión activa */}
              {hasCandidateSession && (
                <div className="p-5 rounded-2xl bg-gradient-to-br from-amber-500/10 via-orange-500/10 to-transparent border border-emerald-500/30 space-y-3">
                  <div className="flex items-center gap-2 text-emerald-400">
                    <Zap className="w-4 h-4 fill-orange-400" />
                    <span className="font-bold text-xs uppercase tracking-wider">Postulación Rápida (1 Clic)</span>
                  </div>
                  <p className="text-[11px] text-slate-300 leading-relaxed">
                    Tienes una sesión activa. Puedes postularte a esta vacante de inmediato con tus datos y tu Hoja de Vida guardados.
                  </p>
                  <button
                    onClick={handleQuickApply}
                    disabled={quickApplying}
                    className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center justify-center gap-2 transition shadow-lg shadow-emerald-600/25 disabled:opacity-50"
                  >
                    <Zap className="w-3.5 h-3.5 fill-white" />
                    {quickApplying ? 'Postulando...' : 'Postularme con 1 Clic'}
                  </button>
                </div>
              )}
            </div>

            {/* ── Columna Derecha: Formulario de Postulación ────── */}
            <div className="lg:col-span-2">
              <div className="p-6 sm:p-8 rounded-2xl bg-slate-800/80 border border-slate-700/80 space-y-6">
                <div>
                  <h2 className="text-xl font-bold text-white">Formulario de Postulación</h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Diligencie su información personal, profesional y adjunte su Hoja de Vida.
                  </p>
                </div>

                {/* Banner de Autocompletado */}
                {isAutoFilled && (
                  <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-200 flex items-start gap-2.5">
                    <Sparkles className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold block">Datos precargados automáticamente</span>
                      <span className="text-[11px] text-amber-300/80">
                        Hemos recuperado tu información de tu postulación anterior para que no tengas que escribirla de nuevo. Puedes editar cualquier campo si lo necesitas.
                      </span>
                    </div>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4 text-xs">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Tipo de Documento *</label>
                      <select
                        value={form.tipo_documento}
                        onChange={(e) => setForm(p => ({ ...p, tipo_documento: e.target.value }))}
                        className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none"
                        required
                      >
                        <option value="CC">Cédula de Ciudadanía (CC)</option>
                        <option value="CE">Cédula de Extranjería (CE)</option>
                        <option value="PA">Pasaporte</option>
                        <option value="PPT">Permiso Protección Temporal (PPT)</option>
                      </select>
                    </div>

                    <div className="sm:col-span-2">
                      <label className="block text-slate-300 font-medium mb-1">Número de Documento *</label>
                      <input
                        type="text"
                        value={form.documento}
                        onChange={(e) => setForm(p => ({ ...p, documento: e.target.value }))}
                        onBlur={handleBlurDocumentoOEmail}
                        placeholder="Ej: 1020304050"
                        className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Nombres *</label>
                      <input
                        type="text"
                        value={form.nombres}
                        onChange={(e) => setForm(p => ({ ...p, nombres: e.target.value }))}
                        className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Apellidos *</label>
                      <input
                        type="text"
                        value={form.apellidos}
                        onChange={(e) => setForm(p => ({ ...p, apellidos: e.target.value }))}
                        className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Correo Electrónico *</label>
                      <input
                        type="email"
                        value={form.email}
                        onChange={(e) => setForm(p => ({ ...p, email: e.target.value }))}
                        onBlur={handleBlurDocumentoOEmail}
                        placeholder="tu-correo@ejemplo.com"
                        className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Teléfono / Celular</label>
                      <input
                        type="tel"
                        value={form.telefono}
                        onChange={(e) => setForm(p => ({ ...p, telefono: e.target.value }))}
                        placeholder="Ej: 300 123 4567"
                        className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Ciudad de Residencia</label>
                      <input
                        type="text"
                        value={form.ciudad}
                        onChange={(e) => setForm(p => ({ ...p, ciudad: e.target.value }))}
                        placeholder="Ej: Bogotá, Medellín, Cali"
                        className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none"
                      />
                    </div>

                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Años de Experiencia Laboral</label>
                      <input
                        type="number"
                        step="0.5"
                        min="0"
                        value={form.anios_experiencia}
                        onChange={(e) => setForm(p => ({ ...p, anios_experiencia: Number(e.target.value) }))}
                        className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Título / Profesión</label>
                      <input
                        type="text"
                        placeholder="Ej: Ingeniero SST, Psicólogo, Tecnólogo"
                        value={form.titulo_profesional}
                        onChange={(e) => setForm(p => ({ ...p, titulo_profesional: e.target.value }))}
                        className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none"
                      />
                    </div>

                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Nivel Educativo</label>
                      <select
                        value={form.nivel_educativo}
                        onChange={(e) => setForm(p => ({ ...p, nivel_educativo: e.target.value }))}
                        className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none"
                      >
                        <option value="bachiller">Bachiller</option>
                        <option value="tecnico">Técnico</option>
                        <option value="tecnologo">Tecnólogo</option>
                        <option value="universitario">Profesional Universitario</option>
                        <option value="especializacion">Especialización</option>
                        <option value="maestria">Maestría</option>
                        <option value="doctorado">Doctorado</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Aspiración Salarial Mensual (COP)</label>
                    <input
                      type="number"
                      placeholder="Ej: 3500000"
                      value={form.aspiracion_salarial}
                      onChange={(e) => setForm(p => ({ ...p, aspiracion_salarial: e.target.value }))}
                      className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Resumen Profesional / Presentación</label>
                    <textarea
                      rows={3}
                      placeholder="Describe brevemente tu trayectoria, logros y fortalezas..."
                      value={form.resumen_profesional}
                      onChange={(e) => setForm(p => ({ ...p, resumen_profesional: e.target.value }))}
                      className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none"
                    />
                  </div>

                  {/* ── Carga de Hoja de Vida (Adjunto) ─────────────────── */}
                  <div className="space-y-2">
                    <label className="block text-slate-300 font-medium">
                      Adjuntar Hoja de Vida (CV) <span className="text-slate-500">(PDF, DOC, DOCX - Máx 15MB)</span>
                    </label>

                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileChange}
                      accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                      className="hidden"
                    />

                    {selectedFile ? (
                      <div className="p-3.5 rounded-xl bg-slate-900 border border-emerald-500/40 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                            <FileText className="w-5 h-5" />
                          </div>
                          <div>
                            <p className="text-xs font-bold text-white truncate max-w-xs">{selectedFile.name}</p>
                            <p className="text-[11px] text-slate-400">{(selectedFile.size / 1024).toFixed(1)} KB — Listo para subir</p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => setSelectedFile(null)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-800 transition"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ) : savedResumeName ? (
                      <div className="p-3.5 rounded-xl bg-slate-900 border border-emerald-500/30 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                            <FileText className="w-5 h-5" />
                          </div>
                          <div>
                            <p className="text-xs font-bold text-white truncate max-w-xs">{savedResumeName}</p>
                            <p className="text-[11px] text-emerald-400 flex items-center gap-1">
                              <Check className="w-3 h-3" /> Hoja de Vida guardada de tu postulación anterior
                            </p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => fileInputRef.current?.click()}
                          className="text-[11px] text-emerald-400 hover:text-emerald-300 font-bold underline px-2"
                        >
                          Cambiar archivo
                        </button>
                      </div>
                    ) : (
                      <div
                        onClick={() => fileInputRef.current?.click()}
                        className="p-5 rounded-xl bg-slate-900/60 border-2 border-dashed border-slate-700 hover:border-emerald-500/60 text-center cursor-pointer transition group"
                      >
                        <UploadCloud className="w-8 h-8 text-slate-500 group-hover:text-emerald-400 mx-auto transition mb-2" />
                        <p className="text-xs font-bold text-slate-300 group-hover:text-white">
                          Haz clic para seleccionar tu Hoja de Vida
                        </p>
                        <p className="text-[11px] text-slate-500 mt-0.5">Formatos aceptados: PDF, Word (.docx, .doc)</p>
                      </div>
                    )}
                  </div>

                  {/* Habeas Data Obligatorio */}
                  <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-700 space-y-2">
                    <label className="flex items-start gap-2.5 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={form.autoriza_tratamiento_datos}
                        onChange={(e) => setForm(p => ({ ...p, autoriza_tratamiento_datos: e.target.checked }))}
                        className="rounded text-orange-600 mt-0.5 focus:ring-emerald-500"
                        required
                      />
                      <span className="text-slate-300 leading-relaxed text-[11px]">
                        Autorizo de manera libre, previa, expresa e informada a <strong>{vacante.empresa_nombre}</strong> para recolectar, almacenar y tratar mis datos personales con fines de este y futuros procesos de selección laboral, conforme a la <strong>Ley 1581 de 2012 (Habeas Data)</strong>.
                      </span>
                    </label>
                  </div>

                  <div className="pt-2">
                    <button
                      type="submit"
                      disabled={submitting}
                      className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-bold text-sm text-white transition flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/25 disabled:opacity-50"
                    >
                      <Send className="w-4 h-4" />
                      {submitting ? 'Enviando postulación...' : 'Enviar Postulación'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

