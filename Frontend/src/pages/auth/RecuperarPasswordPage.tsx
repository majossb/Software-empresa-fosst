import { useState, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { authService } from '@/services/auth.service'

export default function RecuperarPasswordPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccessMsg(null)

    const trimmedEmail = email.trim()
    if (!trimmedEmail) {
      setError('Por favor, ingresa tu correo electrónico.')
      return
    }

    // Regex simple para validación
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(trimmedEmail)) {
      setError('Por favor, ingresa un correo electrónico válido.')
      return
    }

    setLoading(true)
    try {
      const response = await authService.solicitarResetPassword(trimmedEmail)
      setSuccessMsg(response.message || 'Si el correo existe, se enviaron las instrucciones de recuperación.')
    } catch (err: any) {
      setError(err?.message || 'Ocurrió un error al procesar tu solicitud. Intenta de nuevo.')
    } finally {
      setLoading(false)
    }
  }

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

            <h1 className="form-title" style={{ textAlign: 'center' }}>¿Olvidaste tu contraseña?</h1>
            <p className="form-subtitle">Ingresa tu correo electrónico registrado y te enviaremos un enlace de recuperación.</p>

            {successMsg ? (
              <div className="success-box" style={{ marginTop: '20px', textAlign: 'center' }}>
                <svg className="status-icon success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 19v-8.93a2 2 0 01.89-1.664l8-5.333a2 2 0 012.22 0l8 5.333A2 2 0 0121 10.07V19M3 19a2 2 0 002 2h14a2 2 0 002-2M3 19l6.75-4.5M21 19l-6.75-4.5M3 10l6.75 4.5M21 10l-6.75 4.5m0 0l-2.25-1.5a2 2 0 00-2.22 0l-2.25 1.5" />
                </svg>
                <p className="status-text">{successMsg}</p>
                <Link to="/login" className="btn-action" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginTop: '24px' }}>
                  Volver al inicio de sesión →
                </Link>
              </div>
            ) : (
              <form onSubmit={handleSubmit} noValidate style={{ marginTop: '20px' }}>
                <div className="field-group">
                  <div>
                    <div className="field-label">Correo Electrónico</div>
                    <div className="field">
                      <span className="field-icon">
                        <svg width="16" height="16" fill="none" viewBox="0 0 24 24">
                          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" strokeWidth="1.8"/>
                          <path d="M22 6l-10 7L2 6" stroke="currentColor" strokeWidth="1.8"/>
                        </svg>
                      </span>
                      <input 
                        type="email" 
                        value={email} 
                        onChange={e=>setEmail(e.target.value)} 
                        placeholder="ejemplo@correo.com" 
                        disabled={loading}
                        required 
                      />
                    </div>
                  </div>
                </div>

                {error && <div className="l-error" style={{ marginTop: '12px' }}>{error}</div>}

                <button type="submit" className="btn-action" disabled={loading} style={{ marginTop: '24px' }}>
                  {loading ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 1s linear infinite' }}>
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.416" strokeDashoffset="10" strokeLinecap="round" />
                      </svg>
                      Enviando...
                    </span>
                  ) : 'Enviar enlace de recuperación →'}
                </button>

                <div style={{ textAlign: 'center', marginTop: '20px' }}>
                  <Link to="/login" className="link-small">← Volver al inicio de sesión</Link>
                </div>
              </form>
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
  :root{--azul-oscuro:#1A3A6B;--azul-medio:#1A3A6B;--azul-claro:#2C5AA0;--naranja:#F5A800;--naranja-claro:#FFB81C;--blanco:#FFFFFF;--gris-claro:#F4F5F7;--gris-texto:#4A5568;--borde:#D1D5DC;--placeholder:#94A3B8;--sombra:0 20px 60px rgba(26,58,107,0.18);}
  .lr{font-family:'Inter',sans-serif;background:var(--azul-oscuro);min-height:100vh;overflow:hidden;}
  .bg-wrapper{position:fixed;inset:0;background:linear-gradient(135deg,#1A3A6B 0%,#2C5AA0 50%,#1A3A6B 100%);z-index:0;}
  .l-page{position:relative;z-index:1;display:flex;align-items:center;justify-content:center;height:100vh;padding:20px;}
  .l-card-narrow{background:var(--blanco);padding:52px 48px;border-radius:24px;box-shadow:var(--sombra);width:100%;max-width:480px;position:relative;animation:cardIn 0.6s cubic-bezier(0.22,1,0.36,1) both;}
  .l-card-narrow::before{content:'';position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,var(--naranja) 0%,var(--naranja-claro) 100%);border-radius:24px 24px 0 0;}
  @keyframes cardIn{from{opacity:0;transform:translateY(40px) scale(0.96);}to{opacity:1;transform:translateY(0) scale(1);}}
  .form-title{font-size:22px;font-weight:800;color:var(--azul-oscuro);margin-bottom:6px;}
  .form-subtitle{font-size:13px;color:var(--gris-texto);text-align:center;line-height:1.5;}
  .field-group{display:flex;flex-direction:column;gap:14px;}
  .field-label{font-size:11px;font-weight:700;letter-spacing:.8px;color:var(--azul-medio);text-transform:uppercase;margin-bottom:5px;}
  .field{position:relative;}
  .field-icon{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--gris-texto);display:flex;align-items:center;pointer-events:none;}
  .field input{width:100%;height:50px;padding:0 14px 0 44px;border:1.5px solid var(--borde);border-radius:12px;font-family:'Inter',sans-serif;font-size:14px;font-weight:600;color:var(--azul-oscuro);background:var(--blanco);outline:none;transition:border-color .2s,box-shadow .2s;}
  .field input::placeholder{color:var(--placeholder);font-weight:500;}
  .field input:focus{border-color:var(--azul-claro);box-shadow:0 0 0 4px rgba(42,111,173,0.12);}
  .l-error{background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;padding:10px 14px;font-size:12px;color:#DC2626;font-weight:600;animation:fsd 0.3s both;}
  .btn-action{width:100%;height:52px;background:linear-gradient(135deg,var(--naranja) 0%,var(--naranja-claro) 100%);border:none;border-radius:12px;font-family:'Inter',sans-serif;font-size:15px;font-weight:800;letter-spacing:.5px;color:var(--blanco);cursor:pointer;box-shadow:0 6px 24px rgba(245,168,0,0.35);transition:transform .15s,box-shadow .15s,filter .15s;}
  .btn-action:hover:not(:disabled){transform:translateY(-2px);box-shadow:0 10px 32px rgba(245,130,13,0.45);filter:brightness(1.05);}
  .btn-action:disabled{opacity:.7;cursor:not-allowed;}
  .link-small{font-size:12px;font-weight:700;color:var(--azul-claro);text-decoration:none;transition:color .2s;}
  .link-small:hover{color:var(--naranja);}
  .success-box{background:#ECFDF5;border:1px solid #A7F3D0;border-radius:16px;padding:24px;display:flex;flex-direction:column;align-items:center;}
  .status-icon{width:48px;height:48px;margin-bottom:12px;}
  .status-icon.success{color:#10B981;}
  .status-text{font-size:14px;color:var(--gris-texto);font-weight:600;line-height:1.5;}
  .version-tag{text-align:center;font-size:11px;color:var(--gris-suave, #94A3B8);font-weight:600;}
  @keyframes spin{to{transform:rotate(360deg);}}
  @keyframes fsd{from{opacity:0;transform:translateY(-16px);}to{opacity:1;transform:translateY(0);}}
`
