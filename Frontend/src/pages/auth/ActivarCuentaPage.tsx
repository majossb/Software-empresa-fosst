import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { authService } from '@/services/auth.service'

export default function ActivarCuentaPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [loading, setLoading] = useState(true)
  const [statusMsg, setStatusMsg] = useState({ success: false, text: '' })

  useEffect(() => {
    const activar = async () => {
      if (!token) {
        setStatusMsg({ success: false, text: 'Enlace de activación inválido. Falta el token de seguridad.' })
        setLoading(false)
        return
      }
      try {
        const response = await authService.activarCuenta(token)
        setStatusMsg({ success: true, text: response.message || 'Cuenta activada correctamente.' })
      } catch (err: any) {
        setStatusMsg({ 
          success: false, 
          text: err?.message || 'El enlace de activación es inválido o ha expirado.' 
        })
      } finally {
        setLoading(false)
      }
    }
    activar()
  }, [token])

  return (
    <>
      <style>{CSS}</style>
      <div className="lr">
        <div className="bg-wrapper" />
        <main className="l-page">
          <div className="l-card-narrow">
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              marginBottom: '32px'
            }}>
              <div style={{
                width: '52px',
                height: '52px',
                backgroundColor: '#f0f2f5',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '6px'
              }}>
                <img src="/assets/logo-fosst-icon.png" alt="FOSST Logo" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
              </div>
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: '20px', fontWeight: '700', color: '#1a2f6e' }}>Fosst</div>
                <div style={{ fontSize: '11px', color: '#6b7280', letterSpacing: '0.05em' }}>DIAGNÓSTICO SG-SST</div>
              </div>
            </div>

            <h1 className="form-title" style={{ textAlign: 'center' }}>Activación de Cuenta</h1>

            {loading ? (
              <div className="loading-container">
                <div className="spinner" />
                <p className="form-subtitle" style={{ marginTop: '16px' }}>Procesando tu solicitud de activación...</p>
              </div>
            ) : (
              <div style={{ marginTop: '20px', textAlign: 'center' }}>
                {statusMsg.success ? (
                  <div className="success-box">
                    <svg className="status-icon success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="status-text">{statusMsg.text}</p>
                  </div>
                ) : (
                  <div className="error-box">
                    <svg className="status-icon error" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="status-text">{statusMsg.text}</p>
                  </div>
                )}

                <Link to="/login" className="btn-action" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginTop: '24px' }}>
                  Ir al inicio de sesión →
                </Link>
              </div>
            )}
            
            <p className="version-tag" style={{ marginTop: '32px' }}>DiagnostiSST v1.0 · Res. 0312 de 2019</p>
          </div>
        </main>
      </div>
    </>
  )
}

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  :root{--azul-oscuro:#1A3A6B;--azul-medio:#1A3A6B;--azul-claro:#2C5AA0;--naranja:#F5A800;--naranja-claro:#FFB81C;--blanco:#FFFFFF;--gris-claro:#F4F5F7;--gris-texto:#4A5568;--sombra:0 20px 60px rgba(26,58,107,0.18);}
  .lr{font-family:'Inter',sans-serif;background:var(--azul-oscuro);min-height:100vh;overflow:hidden;}
  .bg-wrapper{position:fixed;inset:0;background:linear-gradient(135deg,#1A3A6B 0%,#2C5AA0 50%,#1A3A6B 100%);z-index:0;}
  .l-page{position:relative;z-index:1;display:flex;align-items:center;justify-content:center;height:100vh;padding:20px;}
  .l-card-narrow{background:var(--blanco);padding:52px 48px;border-radius:24px;box-shadow:var(--sombra);width:100%;max-width:480px;position:relative;animation:cardIn 0.6s cubic-bezier(0.22,1,0.36,1) both;}
  .l-card-narrow::before{content:'';position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,var(--naranja) 0%,var(--naranja-claro) 100%);border-radius:24px 24px 0 0;}
  @keyframes cardIn{from{opacity:0;transform:translateY(40px) scale(0.96);}to{opacity:1;transform:translateY(0) scale(1);}}
  .form-title{font-size:22px;font-weight:800;color:var(--azul-oscuro);margin-bottom:6px;}
  .form-subtitle{font-size:13px;color:var(--gris-texto);text-align:center;}
  .loading-container{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px 0;}
  .spinner{width:40px;height:40px;border:3px solid var(--azul-palido, #E8EDF5);border-top-color:var(--naranja);border-radius:50%;animation:spin 1s linear infinite;}
  @keyframes spin{to{transform:rotate(360deg);}}
  .success-box{background:#ECFDF5;border:1px solid #A7F3D0;border-radius:16px;padding:24px;display:flex;flex-direction:column;align-items:center;}
  .error-box{background:#FEF2F2;border:1px solid #FCA5A5;border-radius:16px;padding:24px;display:flex;flex-direction:column;align-items:center;}
  .status-icon{width:48px;height:48px;margin-bottom:12px;}
  .status-icon.success{color:#10B981;}
  .status-icon.error{color:#EF4444;}
  .status-text{font-size:14px;color:var(--gris-texto);font-weight:600;line-height:1.5;}
  .btn-action{width:100%;height:52px;background:linear-gradient(135deg,var(--naranja) 0%,var(--naranja-claro) 100%);border:none;border-radius:12px;font-family:'Inter',sans-serif;font-size:15px;font-weight:800;letter-spacing:.5px;color:var(--blanco);cursor:pointer;box-shadow:0 6px 24px rgba(245,168,0,0.35);transition:transform .15s,box-shadow .15s,filter .15s;}
  .btn-action:hover{transform:translateY(-2px);box-shadow:0 10px 32px rgba(245,130,13,0.45);filter:brightness(1.05);}
  .version-tag{text-align:center;font-size:11px;color:var(--gris-suave, #94A3B8);font-weight:600;}
`
