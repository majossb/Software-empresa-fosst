import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { reclutamientoService } from '@/services/reclutamiento.service'
import { VacantePublicaListItem } from '@/types/reclutamiento.types'
import {
  Briefcase, MapPin, Building2, Search, ArrowRight,
  Clock, ShieldCheck, CheckCircle2, UserCheck
} from 'lucide-react'
import { Button, EmptyState } from '@/components/ui'

export default function PortalVacantesPage() {
  const [vacantes, setVacantes] = useState<VacantePublicaListItem[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    cargarVacantes()
  }, [])

  const cargarVacantes = async () => {
    setLoading(true)
    try {
      const data = await reclutamientoService.getVacantesPublicas({ search })
      setVacantes(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col justify-between">
      {/* ── Topbar ────────────────────────────────────────────── */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-20">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center font-bold text-white shadow-lg shadow-emerald-600/25">
              F
            </div>
            <span className="font-bold text-lg text-white tracking-tight">
              FOSST <span className="text-emerald-400 font-light">Empleos</span>
            </span>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/portal/seguimiento"
              className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 transition flex items-center gap-1.5"
            >
              <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
              Consultar Mi Postulación
            </Link>
            <Link
              to="/login"
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition"
            >
              Acceso Empresa
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero & Search ──────────────────────────────────────── */}
      <main className="max-w-6xl mx-auto px-4 py-10 flex-1 w-full space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <ShieldCheck className="w-3.5 h-3.5" />
            Oportunidades Laborales en Seguridad y Salud en el Trabajo (SST)
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Únete a las mejores empresas del sector
          </h1>
          <p className="text-sm text-slate-400">
            Postúlate de forma ágil, segura y realiza el seguimiento a tu proceso de selección en tiempo real.
          </p>

          <div className="pt-4 flex gap-2 max-w-lg mx-auto">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
              <input
                type="text"
                placeholder="Buscar por cargo, palabra clave o ciudad..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && cargarVacantes()}
                className="w-full text-sm pl-9 pr-3 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <button
              onClick={cargarVacantes}
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-semibold text-white text-sm transition shadow-lg shadow-emerald-600/20"
            >
              Buscar
            </button>
          </div>
        </div>

        {/* ── Listado de Vacantes ────────────────────────────────── */}
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-2">
            <span>{vacantes.length} convocatoria(s) disponible(s)</span>
          </div>

          {loading ? (
            <div className="py-20 text-center text-slate-500 text-sm">Cargando oportunidades...</div>
          ) : vacantes.length === 0 ? (
            <div className="py-16 text-center rounded-2xl border border-dashed border-slate-700 bg-slate-800/30 my-4 p-8">
              <Briefcase className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-300 mb-1">No hay vacantes disponibles</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">No se encontraron vacantes abiertas en este momento.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {vacantes.map((v) => (
                <div
                  key={v.id}
                  className="p-5 rounded-2xl bg-slate-800/60 border border-slate-700/60 hover:border-emerald-500/50 hover:bg-slate-800 transition flex flex-col justify-between space-y-4 group"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="flex items-center gap-1 font-semibold text-slate-300">
                        <Building2 className="w-3.5 h-3.5 text-emerald-400" />
                        {v.empresa_nombre}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-slate-700 text-slate-300 font-mono text-[11px]">
                        {v.codigo}
                      </span>
                    </div>

                    <h3 className="text-lg font-bold text-white group-hover:text-emerald-400 transition">
                      {v.titulo}
                    </h3>

                    <div className="flex items-center gap-4 text-xs text-slate-400 pt-1 flex-wrap">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-500" />
                        {v.sede_ciudad || 'Colombia'} ({v.modalidad_display})
                      </span>
                      <span className="flex items-center gap-1">
                        <Briefcase className="w-3.5 h-3.5 text-slate-500" />
                        {v.tipo_contrato || 'Contrato Laboral'}
                      </span>
                      <span className="font-semibold text-emerald-300 font-mono">
                        {v.salario_display}
                      </span>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-700/60 flex items-center justify-between">
                    <span className="text-[11px] text-slate-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {v.numero_cupos} cupo(s) disponible(s)
                    </span>

                    <Link
                      to={`/empleos/${v.slug || v.id}`}
                      className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-400 hover:text-emerald-300 transition"
                    >
                      Ver Oferta y Postular
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* ── Footer ────────────────────────────────────────────── */}
      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        FOSST V.I.D.A. — Plataforma Integral de Seguridad, Salud en el Trabajo y Talento Humano.
      </footer>
    </div>
  )
}
