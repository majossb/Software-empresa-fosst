import { createBrowserRouter, RouterProvider, useRouteError } from 'react-router-dom'
import { RequireAuth, RequireRole, RoleRedirect } from './guards'
import { lazy, Suspense } from 'react'

const LoginPage            = lazy(() => import('@/pages/auth/LoginPage'))
const ActivarCuentaPage    = lazy(() => import('@/pages/auth/ActivarCuentaPage'))
const RecuperarPasswordPage = lazy(() => import('@/pages/auth/RecuperarPasswordPage'))
const ResetearPasswordPage = lazy(() => import('@/pages/auth/ResetearPasswordPage'))
const OTPPage              = lazy(() => import('@/pages/auth/OTPPage'))
const RegistroEmpresaPage  = lazy(() => import('@/pages/auth/RegistroEmpresaPage'))

// Alta Dirección
const AltaDireccionShell = lazy(() => import('@/pages/altadireccion/AltaDireccionShell'))
const AltaDireccionDash  = lazy(() => import('@/pages/altadireccion/views/Dashboard'))
const CumplimientoView   = lazy(() => import('@/pages/altadireccion/views/CumplimientoView'))
const SancionesView      = lazy(() => import('@/pages/altadireccion/views/SancionesView'))
const PlanMejoraADView   = lazy(() => import('@/pages/altadireccion/views/PlanMejoraView'))
const InformesADView     = lazy(() => import('@/pages/altadireccion/views/InformesView'))
const HistorialADView    = lazy(() => import('@/pages/altadireccion/views/HistorialView'))

// Responsable
const ResponsableShell       = lazy(() => import('@/pages/responsable/ResponsableShell'))
const ResponsableDash        = lazy(() => import('@/pages/responsable/views/Dashboard'))
const EstandaresView         = lazy(() => import('@/pages/responsable/views/EstandaresView'))
const AutoevaluacionView     = lazy(() => import('@/pages/responsable/views/AutoevaluacionView'))
const EvidenciasRespView     = lazy(() => import('@/pages/responsable/views/EvidenciasView'))
const CapacitacionesView     = lazy(() => import('@/pages/responsable/views/CapacitacionesView'))
const PerfilesCargoView      = lazy(() => import('@/pages/responsable/views/PerfilesCargoView'))
const PerfilCargoFormView    = lazy(() => import('@/pages/responsable/views/PerfilCargoFormView'))
const PerfilCargoDetailView  = lazy(() => import('@/pages/responsable/views/PerfilCargoDetailView'))
const ConfiguracionShell     = lazy(() => import('@/pages/responsable/views/configuracion/ConfiguracionShell'))
const EmpresaContextoView    = lazy(() => import('@/pages/responsable/views/configuracion/EmpresaContextoView'))
const SedesView              = lazy(() => import('@/pages/responsable/views/configuracion/SedesView'))
const OrganigramaView        = lazy(() => import('@/pages/responsable/views/configuracion/OrganigramaView'))
const ProcesosView           = lazy(() => import('@/pages/responsable/views/configuracion/ProcesosView'))
const IdentidadView          = lazy(() => import('@/pages/responsable/views/configuracion/IdentidadView'))

// FOSST V.I.D.A. — Fases 2-5 Views & Reclutamiento
const HbseoView              = lazy(() => import('@/pages/responsable/views/HbseoView'))
const MichcView              = lazy(() => import('@/pages/responsable/views/MichcView'))
const GestionHumanaView      = lazy(() => import('@/pages/responsable/views/GestionHumanaView'))
const FormacionView          = lazy(() => import('@/pages/responsable/views/FormacionView'))
const AlertasView            = lazy(() => import('@/pages/responsable/views/AlertasView'))
const ReclutamientoView      = lazy(() => import('@/pages/responsable/views/ReclutamientoView'))

// Portal Público del Candidato (Fase E)
const PortalVacantesPage      = lazy(() => import('@/pages/portal/PortalVacantesPage'))
const PortalVacanteDetailPage = lazy(() => import('@/pages/portal/PortalVacanteDetailPage'))
const PortalSeguimientoPage   = lazy(() => import('@/pages/portal/PortalSeguimientoPage'))

// Auditor
const AuditorShell           = lazy(() => import('@/pages/auditor/AuditorShell'))
const AuditorDash            = lazy(() => import('@/pages/auditor/views/Dashboard'))
const EvidenciasAuditorView  = lazy(() => import('@/pages/auditor/views/EvidenciasAuditorView'))
const HallazgosView          = lazy(() => import('@/pages/auditor/views/HallazgosView'))
const InformeAuditoriaView   = lazy(() => import('@/pages/auditor/views/InformeAuditoriaView'))
const HistorialAuditorView   = lazy(() => import('@/pages/auditor/views/HistorialAuditorView'))
const ApelacionesAuditorView = lazy(() => import('@/pages/auditor/views/ApelacionesAuditorView'))

const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))

function PageLoader() {
  return (
    <div style={{
      minHeight: '100vh', background: '#001227',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <div style={{
        width: 32, height: 32,
        border: '3px solid rgba(245, 168, 0, 0.2)', borderTopColor: '#F5A800',
        borderRadius: '50%', animation: 'spin 0.8s linear infinite',
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

function Lazy({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>
}

function RouteErrorFallback() {
  const error = useRouteError() as any
  console.error('[RouteError]', error)
  return (
    <div style={{
      minHeight: '100vh', background: '#0f172a',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24,
    }}>
      <div style={{
        background: '#1e293b', border: '1px solid rgba(239,68,68,0.2)',
        borderRadius: 16, padding: 32, maxWidth: 480, width: '100%',
      }}>
        <h2 style={{ color: '#fff', marginBottom: 8, fontSize: 18 }}>
          Error al cargar la vista
        </h2>
        <p style={{ color: '#94a3b8', fontSize: 14, marginBottom: 24 }}>
          {error?.message || error?.statusText || 'No se pudo conectar con el servidor.'}
        </p>
        {error?.stack && (
          <pre style={{
            background: '#0f172a', color: '#fca5a5', fontSize: 11,
            padding: 12, borderRadius: 8, overflowX: 'auto', marginBottom: 24,
          }}>
            {error.stack}
          </pre>
        )}
        <div style={{ display: 'flex', gap: 12 }}>
          <button onClick={() => window.location.reload()}
            style={{ flex: 1, background: '#F5A800', color: '#001227', border: 'none',
              borderRadius: 10, padding: '10px 16px', cursor: 'pointer', fontWeight: 700 }}>
            Reintentar
          </button>
          <button onClick={() => window.location.href = '/'}
            style={{ flex: 1, background: '#334155', color: '#cbd5e1', border: 'none',
              borderRadius: 10, padding: '10px 16px', cursor: 'pointer', fontWeight: 600 }}>
            Volver al inicio
          </button>
        </div>
      </div>
    </div>
  )
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <RoleRedirect />,
    errorElement: <RouteErrorFallback />,
  },
  {
    path: '/login',
    element: <Lazy><LoginPage /></Lazy>,
    errorElement: <RouteErrorFallback />,
  },
  {
    path: '/registro-empresa',
    element: <Lazy><RegistroEmpresaPage /></Lazy>,
    errorElement: <RouteErrorFallback />,
  },
  {
    path: '/auth/otp',
    element: <Lazy><OTPPage /></Lazy>,
    errorElement: <RouteErrorFallback />,
  },
  {
    path: '/activar-cuenta',
    element: <Lazy><ActivarCuentaPage /></Lazy>,
    errorElement: <RouteErrorFallback />,
  },
  {
    path: '/recuperar-password',
    element: <Lazy><RecuperarPasswordPage /></Lazy>,
    errorElement: <RouteErrorFallback />,
  },
  {
    path: '/reset-password',
    element: <Lazy><ResetearPasswordPage /></Lazy>,
    errorElement: <RouteErrorFallback />,
  },
  {
    path: '/empleos',
    element: <Lazy><PortalVacantesPage /></Lazy>,
    errorElement: <RouteErrorFallback />,
  },
  {
    path: '/empleos/:slugOrId',
    element: <Lazy><PortalVacanteDetailPage /></Lazy>,
    errorElement: <RouteErrorFallback />,
  },
  {
    path: '/portal/seguimiento',
    element: <Lazy><PortalSeguimientoPage /></Lazy>,
    errorElement: <RouteErrorFallback />,
  },
  {
    path: '/app',
    element: <RequireAuth />,
    errorElement: <RouteErrorFallback />,
    children: [

      // ── Alta Dirección ──────────────────────────────────────
      {
        path: 'alta-direccion',
        element: <RequireRole roles={['alta_direccion']} />,
        errorElement: <RouteErrorFallback />,
        children: [{
          element: <Lazy><AltaDireccionShell /></Lazy>,
          children: [
            { index: true,              element: <Lazy><AltaDireccionDash /></Lazy> },
            { path: 'cumplimiento',     element: <Lazy><CumplimientoView /></Lazy> },
            { path: 'sanciones',        element: <Lazy><SancionesView /></Lazy> },
            { path: 'plan',             element: <Lazy><PlanMejoraADView /></Lazy> },
            { path: 'informes',         element: <Lazy><InformesADView /></Lazy> },
            { path: 'historial',        element: <Lazy><HistorialADView /></Lazy> },
          ],
        }],
      },

      // ── Responsable ─────────────────────────────────────────
      {
        path: 'responsable',
        element: <RequireRole roles={['responsable']} />,
        errorElement: <RouteErrorFallback />,
        children: [{
          element: <Lazy><ResponsableShell /></Lazy>,
          children: [
            { index: true,                          element: <Lazy><ResponsableDash /></Lazy> },
            { path: 'estandares',                   element: <Lazy><EstandaresView /></Lazy> },
            { path: 'autoevaluacion',               element: <Lazy><AutoevaluacionView /></Lazy> },
            { path: 'evidencias',                   element: <Lazy><EvidenciasRespView /></Lazy> },
            { path: 'plan',                         element: <Lazy><PlanMejoraADView /></Lazy> },
            { path: 'capacitaciones',               element: <Lazy><CapacitacionesView /></Lazy> },
            { path: 'perfiles-cargo',               element: <Lazy><PerfilesCargoView /></Lazy> },
            { path: 'perfiles-cargo/nuevo',         element: <Lazy><PerfilCargoFormView /></Lazy> },
            { path: 'perfiles-cargo/:id/editar',    element: <Lazy><PerfilCargoFormView /></Lazy> },
            { path: 'perfiles-cargo/:id',           element: <Lazy><PerfilCargoDetailView /></Lazy> },
            {
              path: 'configuracion',
              element: <Lazy><ConfiguracionShell /></Lazy>,
              children: [
                { index: true,          element: <Lazy><EmpresaContextoView /></Lazy> },
                { path: 'sedes',        element: <Lazy><SedesView /></Lazy> },
                { path: 'organigrama',  element: <Lazy><OrganigramaView /></Lazy> },
                { path: 'procesos',     element: <Lazy><ProcesosView /></Lazy> },
                { path: 'identidad',    element: <Lazy><IdentidadView /></Lazy> },
              ],
            },
            // FOSST V.I.D.A. — Gestión Integral
            { path: 'michc',            element: <Lazy><MichcView /></Lazy> },
            { path: 'hbseo',            element: <Lazy><HbseoView /></Lazy> },
            { path: 'gestion-humana',   element: <Lazy><GestionHumanaView /></Lazy> },
            { path: 'formacion',        element: <Lazy><FormacionView /></Lazy> },
            { path: 'alertas',          element: <Lazy><AlertasView /></Lazy> },
            { path: 'reclutamiento',    element: <Lazy><ReclutamientoView /></Lazy> },
          ],
        }],
      },

      // ── Auditor ─────────────────────────────────────────────
      {
        path: 'auditor',
        element: <RequireRole roles={['auditor']} />,
        errorElement: <RouteErrorFallback />,
        children: [{
          element: <Lazy><AuditorShell /></Lazy>,
          children: [
            { index: true,              element: <Lazy><AuditorDash /></Lazy> },
            { path: 'evidencias',       element: <Lazy><EvidenciasAuditorView /></Lazy> },
            { path: 'autoevaluacion',   element: <Lazy><AutoevaluacionView /></Lazy> },
            { path: 'hallazgos',        element: <Lazy><HallazgosView /></Lazy> },
            { path: 'informe',          element: <Lazy><InformeAuditoriaView /></Lazy> },
            { path: 'historial',        element: <Lazy><HistorialAuditorView /></Lazy> },
            { path: 'apelaciones',      element: <Lazy><ApelacionesAuditorView /></Lazy> },
          ],
        }],
      },
    ],
  },
  {
    path: '*',
    element: <Lazy><NotFoundPage /></Lazy>,
    errorElement: <RouteErrorFallback />,
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}