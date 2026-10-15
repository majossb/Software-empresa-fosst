import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { reclutamientoService } from '@/services/reclutamiento.service'
import { PostulacionCandidatoPublica, VacantePublicaListItem, CandidatoPerfilCompleto } from '@/types/reclutamiento.types'
import {
  UserCheck, Mail, KeyRound, ArrowLeft, LogOut, CheckCircle2,
  Building2, Briefcase, MapPin, Zap, FileText, Check, Sparkles, User
} from 'lucide-react'

export default function PortalSeguimientoPage() {
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [step, setStep] = useState<'email' | 'otp' | 'dashboard'>('email')
  const [activeTab, setActiveTab] = useState<'mis_postulaciones' | 'otras_vacantes' | 'mi_perfil'>('mis_postulaciones')
  const [loading, setLoading] = useState(false)
  const [candidateInfo, setCandidateInfo] = useState<{ nombre_completo: string; email: string } | null>(null)
  const [perfilCompleto, setPerfilCompleto] = useState<CandidatoPerfilCompleto | null>(null)
  const [postulaciones, setPostulaciones] = useState<PostulacionCandidatoPublica[]>([])
  const [otrasVacantes, setOtrasVacantes] = useState<VacantePublicaListItem[]>([])
  const [statusMessage, setStatusMessage] = useState('')
  const [applyingVacanteId, setApplyingVacanteId] = useState<string | null>(null)
  const [appliedVacanteIds, setAppliedVacanteIds] = useState<string[]>([])

  useEffect(() => {
    const token = reclutamientoService.getCandidateToken()
    if (token) {
      cargarDashboard()
    }
  }, [])

  const handleSolicitarOTP = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email) return
    setLoading(true)
    setStatusMessage('')
    try {
      const res = await reclutamientoService.solicitarAccesoOTP(email)
      setStep('otp')
      setStatusMessage(res.detail || 'Código OTP enviado a su correo.')
    } catch (err: any) {
      alert(err.message || 'No se encontró ninguna postulación con este correo electrónico.')
    } finally {
      setLoading(false)
    }
  }

  const handleVerificarOTP = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!otp) return
    setLoading(true)
    try {
      const res = await reclutamientoService.verificarOTP(email, otp)
      setCandidateInfo(res.candidato)
      await cargarDashboard()
    } catch (err: any) {
      alert(err.message || 'Código OTP inválido o expirado.')
    } finally {
      setLoading(false)
    }
  }

  const cargarDashboard = async () => {
    setLoading(true)
    try {
      const [posts, vacs, perfil] = await Promise.all([
        reclutamientoService.getMisPostulaciones(),
        reclutamientoService.getVacantesPublicas(),
        reclutamientoService.getMiPerfil(),
      ])
      setPostulaciones(posts)
      setOtrasVacantes(vacs)
      if (perfil) {
        setPerfilCompleto(perfil)
        if (!candidateInfo) {
          setCandidateInfo({
            nombre_completo: `${perfil.nombres} ${perfil.apellidos}`,
            email: perfil.email,
          })
        }
      }
      setStep('dashboard')
    } catch (err) {
      reclutamientoService.logoutCandidato()
      setStep('email')
    } finally {
      setLoading(false)
    }
  }

  const handleQuickApply = async (vacanteIdOrSlug: string, vacanteCodigo: string) => {
    setApplyingVacanteId(vacanteIdOrSlug)
    try {
      const res = await reclutamientoService.postularRapido(vacanteIdOrSlug)
      alert(res.detail || '¡Postulación registrada con éxito!')
      setAppliedVacanteIds(prev => [...prev, vacanteCodigo])
      const updatedPosts = await reclutamientoService.getMisPostulaciones()
      setPostulaciones(updatedPosts)
    } catch (err: any) {
      alert(err.message || 'Error al postularse a la vacante.')
    } finally {
      setApplyingVacanteId(null)
    }
  }

  const handleRetirar = async (postulacionId: string) => {
    const motivo = prompt('Por favor indique el motivo de retiro voluntario:')
    if (!motivo) return

    try {
      await reclutamientoService.retirarMiPostulacion(postulacionId, motivo)
      alert('Su postulación ha sido retirada exitosamente.')
      const updated = await reclutamientoService.getMisPostulaciones()
      setPostulaciones(updated)
    } catch (err: any) {
      alert(err.message || 'Error al retirar la postulación.')
    }
  }

  const handleLogout = () => {
    reclutamientoService.logoutCandidato()
    setCandidateInfo(null)
    setPerfilCompleto(null)
    setPostulaciones([])
    setStep('email')
    setOtp('')
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col justify-between py-8 px-4">
      <div className="max-w-4xl mx-auto w-full space-y-6">
        {/* Topbar navigation */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <Link
            to="/empleos"
            className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-400 hover:text-white transition"
          >
            <ArrowLeft className="w-4 h-4" />
            Catálogo Público de Empleos
          </Link>

          {step === 'dashboard' && (
            <div className="flex items-center gap-4">
              {candidateInfo && (
                <span className="text-xs text-slate-300 font-medium hidden sm:inline-flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-slate-400" /> {candidateInfo.nombre_completo}
                </span>
              )}
              <button
                onClick={handleLogout}
                className="inline-flex items-center gap-1 text-xs font-semibold text-rose-400 hover:text-rose-300 transition"
              >
                <LogOut className="w-3.5 h-3.5" />
                Cerrar Sesión
              </button>
            </div>
          )}
        </div>

        {/* ── PASO 1: Ingreso de Correo ─────────────────────────── */}
        {step === 'email' && (
          <div className="max-w-md mx-auto p-8 rounded-2xl bg-slate-800/80 border border-slate-700 space-y-6 text-center">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
              <UserCheck className="w-6 h-6" />
            </div>

            <div className="space-y-1">
              <h1 className="text-xl font-bold text-white">Portal de Seguimiento del Candidato</h1>
              <p className="text-xs text-slate-400">
                Ingrese el correo electrónico con el que se postuló para recibir su código OTP de acceso.
              </p>
            </div>

            <form onSubmit={handleSolicitarOTP} className="space-y-4 text-xs text-left">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Correo Electrónico:</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="email"
                    required
                    placeholder="ejemplo@correo.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-bold text-xs text-white transition disabled:opacity-50"
              >
                {loading ? 'Enviando código...' : 'Solicitar Código de Acceso'}
              </button>
            </form>
          </div>
        )}

        {/* ── PASO 2: Verificación OTP ──────────────────────────── */}
        {step === 'otp' && (
          <div className="max-w-md mx-auto p-8 rounded-2xl bg-slate-800/80 border border-slate-700 space-y-6 text-center">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
              <KeyRound className="w-6 h-6" />
            </div>

            <div className="space-y-1">
              <h1 className="text-xl font-bold text-white">Ingrese el Código OTP</h1>
              <p className="text-xs text-slate-400">
                Hemos enviado un código de 6 dígitos al correo <strong>{email}</strong>.
              </p>
            </div>

            <form onSubmit={handleVerificarOTP} className="space-y-4 text-xs text-left">
              <div>
                <label className="block text-slate-300 font-medium mb-1 text-center">Código de 6 dígitos:</label>
                <input
                  type="text"
                  maxLength={6}
                  required
                  placeholder="123456"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  className="w-full p-3 text-center text-2xl tracking-[0.4em] font-mono font-bold rounded-xl bg-slate-900 border border-slate-700 text-white focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-bold text-xs text-white transition disabled:opacity-50"
              >
                {loading ? 'Verificando...' : 'Acceder a Mi Panel'}
              </button>

              <button
                type="button"
                onClick={() => setStep('email')}
                className="w-full text-center text-slate-400 hover:text-white text-[11px] pt-2"
              >
                ¿Cambiar de correo?
              </button>
            </form>
          </div>
        )}

        {/* ── PASO 3: Dashboard del Candidato ───────────────────── */}
        {step === 'dashboard' && (
          <div className="space-y-6">
            {/* Pestañas de navegación */}
            <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
              <button
                onClick={() => setActiveTab('mis_postulaciones')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                  activeTab === 'mis_postulaciones'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <Briefcase className="w-4 h-4" />
                Mis Postulaciones ({postulaciones.length})
              </button>

              <button
                onClick={() => setActiveTab('otras_vacantes')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                  activeTab === 'otras_vacantes'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <Zap className="w-4 h-4" />
                Ofertas Laborales Disponibles ({otrasVacantes.length})
              </button>

              <button
                onClick={() => setActiveTab('mi_perfil')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
                  activeTab === 'mi_perfil'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <FileText className="w-4 h-4" />
                Mi Perfil y Hoja de Vida
              </button>
            </div>

            {/* TAB 1: Mis Postulaciones */}
            {activeTab === 'mis_postulaciones' && (
              <div className="space-y-4">
                {postulaciones.length === 0 ? (
                  <div className="p-12 text-center text-slate-500 bg-slate-800/40 rounded-2xl border border-slate-800">
                    No tienes postulaciones activas actualmente. Puedes consultar las ofertas disponibles en la pestaña contigua.
                  </div>
                ) : (
                  postulaciones.map((p) => (
                    <div
                      key={p.id}
                      className="p-6 rounded-2xl bg-slate-800/80 border border-slate-700 space-y-4 hover:border-slate-600 transition"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-700">
                        <div>
                          <span className="text-xs font-mono font-bold text-emerald-400">{p.vacante_codigo}</span>
                          <h3 className="text-lg font-bold text-white">{p.vacante_titulo}</h3>
                          <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                            <Building2 className="w-3.5 h-3.5 text-slate-500" />
                            {p.empresa_nombre}
                          </p>
                        </div>

                        <div className="text-right">
                          <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${
                            p.estado_publico.includes('Seleccionado') ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' :
                            p.estado_publico.includes('Retirada') || p.estado_publico.includes('Concluido') ? 'bg-slate-700 text-slate-400' :
                            'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          }`}>
                            {p.estado_publico}
                          </span>
                          <div className="text-[11px] text-slate-500 mt-1">
                            Postulado el {new Date(p.fecha_postulacion).toLocaleDateString()}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-1 text-xs">
                        <span className="text-slate-400">
                          Etapa actual: <strong className="text-slate-200">{p.etapa_actual}</strong>
                        </span>

                        {p.es_activa && (
                          <button
                            onClick={() => handleRetirar(p.id)}
                            className="text-xs text-rose-400 hover:text-rose-300 font-medium hover:underline"
                          >
                            Retirar candidatura
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* TAB 2: Otras Vacantes Disponibles con 1-Click Apply */}
            {activeTab === 'otras_vacantes' && (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-200 flex items-start gap-2.5">
                  <Sparkles className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold block">Postulación Automática con 1 Clic</span>
                    <span className="text-[11px] text-emerald-300/80">
                      Como ya tienes tus datos verificados en FOSST, puedes postularte a cualquiera de estas vacantes directamente sin tener que volver a llenar el formulario ni cargar tu Hoja de Vida.
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {otrasVacantes.map((v) => {
                    const yaPostulado = postulaciones.some(p => p.vacante_codigo === v.codigo) || appliedVacanteIds.includes(v.codigo)

                    return (
                      <div
                        key={v.id}
                        className="p-5 rounded-2xl bg-slate-800/80 border border-slate-700/80 space-y-4 flex flex-col justify-between hover:border-slate-600 transition"
                      >
                        <div className="space-y-2">
                          <div className="flex justify-between items-start">
                            <span className="text-xs font-mono font-bold text-emerald-400">{v.codigo}</span>
                            <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-700 text-slate-300">
                              {v.modalidad_display}
                            </span>
                          </div>

                          <h3 className="text-base font-bold text-white leading-snug">{v.titulo}</h3>

                          <div className="text-xs text-slate-400 space-y-1">
                            <div className="flex items-center gap-1.5">
                              <Building2 className="w-3.5 h-3.5 text-slate-500" />
                              <span>{v.empresa_nombre}</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <MapPin className="w-3.5 h-3.5 text-slate-500" />
                              <span>{v.sede_ciudad || 'Colombia'}</span>
                            </div>
                            <div className="font-mono text-emerald-300 font-bold pt-1">
                              {v.salario_display}
                            </div>
                          </div>
                        </div>

                        <div className="pt-3 border-t border-slate-700 flex items-center gap-2">
                          {yaPostulado ? (
                            <span className="w-full py-2 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-400 text-center text-xs font-bold flex items-center justify-center gap-1.5">
                              <Check className="w-3.5 h-3.5" />
                              Ya estás postulado
                            </span>
                          ) : (
                            <button
                              onClick={() => handleQuickApply(v.slug || v.id, v.codigo)}
                              disabled={applyingVacanteId === (v.slug || v.id)}
                              className="w-full py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition shadow-md shadow-emerald-600/25 disabled:opacity-50"
                            >
                              <Zap className="w-3.5 h-3.5 fill-white" />
                              {applyingVacanteId === (v.slug || v.id) ? 'Postulando...' : 'Postularme con 1 Clic'}
                            </button>
                          )}
                          <Link
                            to={`/empleos/${v.slug || v.id}`}
                            className="p-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs text-center transition"
                            title="Ver detalles"
                          >
                            Detalle
                          </Link>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* TAB 3: Mi Perfil Registrado */}
            {activeTab === 'mi_perfil' && perfilCompleto && (
              <div className="p-6 rounded-2xl bg-slate-800/80 border border-slate-700 space-y-6 text-xs">
                <div>
                  <h2 className="text-lg font-bold text-white">Información de Perfil Guardada</h2>
                  <p className="text-slate-400 mt-0.5">
                    Estos son los datos con los que el sistema realiza tus postulaciones automáticas.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-slate-300">
                  <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                    <span className="text-slate-500 font-bold uppercase text-[10px] tracking-wider block">Datos Personales</span>
                    <p><strong>Nombre:</strong> {perfilCompleto.nombres} {perfilCompleto.apellidos}</p>
                    <p><strong>Documento:</strong> {perfilCompleto.tipo_documento} {perfilCompleto.documento}</p>
                    <p><strong>Email:</strong> {perfilCompleto.email}</p>
                    <p><strong>Teléfono:</strong> {perfilCompleto.telefono || 'No registrado'}</p>
                    <p><strong>Ciudad:</strong> {perfilCompleto.ciudad || 'Colombia'}</p>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                    <span className="text-slate-500 font-bold uppercase text-[10px] tracking-wider block">Perfil Profesional</span>
                    <p><strong>Profesión / Título:</strong> {perfilCompleto.titulo_profesional || 'No especificado'}</p>
                    <p><strong>Nivel Educativo:</strong> {perfilCompleto.nivel_educativo || 'Universitario'}</p>
                    <p><strong>Años de Experiencia:</strong> {perfilCompleto.anios_experiencia} años</p>
                    <p><strong>Aspiración Salarial:</strong> {perfilCompleto.aspiracion_salarial ? `$${Number(perfilCompleto.aspiracion_salarial).toLocaleString()}` : 'A convenir'}</p>
                  </div>
                </div>

                {perfilCompleto.ultima_hoja_vida && (
                  <div className="p-4 rounded-xl bg-slate-900 border border-emerald-500/30 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                        <FileText className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="text-xs font-bold text-white">{perfilCompleto.ultima_hoja_vida.nombre}</p>
                        <p className="text-[11px] text-slate-400">{perfilCompleto.ultima_hoja_vida.tamanio_kb} KB — Hoja de Vida activa</p>
                      </div>
                    </div>

                    {perfilCompleto.ultima_hoja_vida.url && (
                      <a
                        href={perfilCompleto.ultima_hoja_vida.url}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-400 font-bold text-xs transition"
                      >
                        Ver Documento
                      </a>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <footer className="text-center text-xs text-slate-600 pt-6">
        FOSST V.I.D.A. — Seguimiento transparente y confidencial de postulaciones.
      </footer>
    </div>
  )
}

