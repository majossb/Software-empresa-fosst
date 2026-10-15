import { useState, FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '@/store/auth.context'
import { ApiError } from '@/services/api.client'

const PARTICLES = [
  { w:40,  h:40,  left:'5%',  dur:'18s', delay:'0s',  rot:'rotate(20deg)' },
  { w:20,  h:20,  left:'15%', dur:'22s', delay:'3s',  rot:'rotate(45deg)' },
  { w:60,  h:60,  left:'25%', dur:'16s', delay:'1s',  rot:'rotate(10deg)' },
  { w:15,  h:15,  left:'40%', dur:'20s', delay:'5s',  rot:'rotate(60deg)' },
  { w:35,  h:35,  left:'55%', dur:'24s', delay:'2s',  rot:'rotate(30deg)' },
  { w:25,  h:25,  left:'65%', dur:'19s', delay:'7s',  rot:'rotate(75deg)' },
  { w:50,  h:50,  left:'75%', dur:'17s', delay:'4s',  rot:'rotate(15deg)' },
  { w:18,  h:18,  left:'85%', dur:'21s', delay:'6s',  rot:'rotate(50deg)' },
  { w:45,  h:45,  left:'90%', dur:'23s', delay:'1s',  rot:'rotate(35deg)' },
  { w:30,  h:30,  left:'35%', dur:'15s', delay:'9s',  rot:'rotate(80deg)' },
]

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [nit,       setNit]       = useState('')
  const [documento, setDocumento] = useState('')
  const [password,  setPassword]  = useState('')
  const [showPwd,   setShowPwd]   = useState(false)
  const [loading,   setLoading]   = useState(false)
  const [error,     setError]     = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    // ── Validaciones frontend ──────────────────────────
    if (!nit.trim()) {
      setError('Ingresa el NIT de la empresa.')
      return
    }
    if (!documento.trim()) {
      setError('Ingresa tu número de documento.')
      return
    }
    if (!password) {
      setError('Ingresa tu contraseña.')
      return
    }

    setLoading(true)
    try {
      const otpResponse = await login({ nit: nit.trim(), documento: documento.trim(), password })

      // Navegar a la página independiente de OTP
      navigate('/auth/otp', {
        state: {
          usuarioId:           otpResponse.usuario_id,
          expiresAt:           otpResponse.expires_at,
          nit:                 nit.trim(),
          documento:           documento.trim(),
          password,
        },
        replace: true,
      })
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.friendlyMessage)
      } else {
        const message = err?.message ?? 'No pudimos iniciar sesión con los datos ingresados.'
        setError(message)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <style>{CSS}</style>
      <div className="lr">
        <div className="bg-wrapper" />
        <div className="particles" aria-hidden="true">
          {PARTICLES.map((p,i) => (
            <div key={i} className="particle" style={{ width:p.w, height:p.h, left:p.left, animationDuration:p.dur, animationDelay:p.delay, transform:p.rot }} />
          ))}
        </div>
        <main className="l-page">
          <div className="l-card">

            <section className="panel-form">
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                marginBottom: '24px'
              }}>
                <div style={{
                  width: '52px',
                  height: '52px',
                  backgroundColor: '#f0f2f5',
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '6px',
                  flexShrink: 0
                }}>
                  <img
                    src="/assets/logo-fosst-icon.png"
                    alt="FOSST Logo"
                    style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
                  />
                </div>
                <div>
                  <div style={{ fontSize: '20px', fontWeight: '700', color: '#1a2f6e' }}>Fosst</div>
                  <div style={{ fontSize: '11px', color: '#6b7280', letterSpacing: '0.05em' }}>DIAGNÓSTICO SG-SST · RES. 0312/2019</div>
                </div>
              </div>

              <h1 className="form-title">¡Bienvenido de nuevo!</h1>
              <p className="form-subtitle">Ingresa tus datos para acceder al sistema</p>

              <form onSubmit={handleSubmit} noValidate>
                <div className="field-group">
                  <div>
                    <div className="field-label">NIT / Documento empresa</div>
                    <div className="field" style={{animationDelay:'0.5s'}}>
                      <span className="field-icon"><svg width="16" height="16" fill="none" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="3" stroke="currentColor" strokeWidth="1.8"/><path d="M7 8h10M7 12h6M7 16h8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg></span>
                      <input id="login-nit" type="text" value={nit} onChange={e=>setNit(e.target.value.replace(/\D/g, ''))} placeholder="Ej. 900234567" autoComplete="organization" required />
                    </div>
                  </div>
                  <div>
                    <div className="field-label">N° Documento usuario</div>
                    <div className="field" style={{animationDelay:'0.55s'}}>
                      <span className="field-icon"><svg width="16" height="16" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.8"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg></span>
                      <input id="login-documento" type="text" value={documento} onChange={e=>setDocumento(e.target.value.replace(/\D/g, ''))} placeholder="Cédula o identificación" autoComplete="username" required />
                    </div>
                  </div>
                  <div>
                    <div className="field-label">Contraseña</div>
                    <div className="field" style={{animationDelay:'0.6s'}}>
                      <span className="field-icon"><svg width="16" height="16" fill="none" viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.8"/><path d="M8 11V7a4 4 0 1 1 8 0v4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg></span>
                      <input id="login-password" type={showPwd?'text':'password'} value={password} onChange={e=>setPassword(e.target.value)} placeholder="••••••••" autoComplete="current-password" required style={{paddingRight:'44px'}} />
                      <button type="button" className="eye-btn" onClick={()=>setShowPwd(!showPwd)} aria-label={showPwd ? 'Ocultar contraseña' : 'Mostrar contraseña'}>
                        {showPwd
                          ? <svg width="16" height="16" fill="none" viewBox="0 0 24 24"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/><line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
                          : <svg width="16" height="16" fill="none" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" strokeWidth="1.8"/><circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8"/></svg>
                        }
                      </button>
                    </div>
                  </div>
                </div>

                {error && <div className="l-error">{error}</div>}

                <div className="links-row">
                  <Link to="/recuperar-password" className="link-small">¿Olvidaste tu contraseña?</Link>
                </div>

                <button id="login-submit" type="submit" className="btn-login" disabled={loading}>
                  {loading ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 1s linear infinite' }}>
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.416" strokeDashoffset="10" strokeLinecap="round" />
                      </svg>
                      Verificando...
                    </span>
                  ) : 'Iniciar sesión →'}
                </button>

                <div className="register-row">
                  <span className="register-text">¿Tu empresa aún no está registrada?</span>
                  <Link to="/registro-empresa" className="register-link">Registrar empresa →</Link>
                </div>
              </form>

              <p className="version-tag">DiagnostiSST v1.0 · Res. 0312 de 2019 · Ministerio del Trabajo</p>
            </section>

            <aside className="panel-banner">
              <div className="banner-circle bc1" /><div className="banner-circle bc2" /><div className="banner-circle bc3" /><div className="banner-line" />
              <div className="banner-top">
                <div className="badge"><div className="badge-dot" /><span className="badge-text">Sistema activo</span></div>
                <div className="banner-headline">Gestión<br/><span>SG-SST</span><br/>Inteligente</div>
                <p className="banner-desc">Diagnóstica el Sistema de Gestión de Seguridad y Salud en el Trabajo de tu empresa basado en la Resolución 0312 de 2019.</p>
                <div className="features">
                  {[
                    { icon:<svg fill="none" viewBox="0 0 24 24" width="16" height="16"><path d="M9 11l3 3L22 4M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>, name:'Clasificación automática', sub:'Cap. I, II o III según tu empresa' },
                    { icon:<svg fill="none" viewBox="0 0 24 24" width="16" height="16"><circle cx="12" cy="12" r="9" stroke="white" strokeWidth="2"/><path d="M12 7v5l3 3" stroke="white" strokeWidth="2" strokeLinecap="round"/></svg>, name:'Diagnóstico en tiempo real', sub:'Puntaje PHVA automático' },
                    { icon:<svg fill="none" viewBox="0 0 24 24" width="16" height="16"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" stroke="white" strokeWidth="2"/><path d="M14 2v6h6M8 13h8M8 17h5" stroke="white" strokeWidth="2" strokeLinecap="round"/></svg>, name:'Plan de mejora automático', sub:'Acciones correctivas priorizadas' },
                  ].map(f => (
                    <div key={f.name} className="feature-item">
                      <div className="feature-icon">{f.icon}</div>
                      <div className="feature-text"><span className="feature-name">{f.name}</span><span className="feature-sub">{f.sub}</span></div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="banner-bottom">
                <div className="norm-badge">
                  <div className="norm-badge-icon"><svg fill="none" viewBox="0 0 24 24" width="15" height="15"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" stroke="#F5820D" strokeWidth="2"/></svg></div>
                  <div className="norm-text"><span className="norm-title">Resolución 0312 de 2019</span><span className="norm-sub">Ministerio del Trabajo · Colombia</span></div>
                </div>
              </div>
            </aside>

          </div>
        </main>
      </div>
    </>
  )
}

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  :root{--azul-oscuro:#1A3A6B;--azul-medio:#1A3A6B;--azul-claro:#2C5AA0;--naranja:#F5A800;--naranja-claro:#FFB81C;--blanco:#FFFFFF;--gris-claro:#F4F5F7;--gris-texto:#4A5568;--borde:#D1D5DC;--placeholder:#94A3B8;--gris-suave:#94A3B8;--azul-palido:#E8EDF5;--gris-bg:#F4F5F7;--sombra:0 20px 60px rgba(26,58,107,0.18);}
  .lr,.lr *{box-sizing:border-box;margin:0;padding:0;}
  .lr{font-family:'Inter',sans-serif;background:var(--azul-oscuro);min-height:100vh;overflow:hidden;}
  .bg-wrapper{position:fixed;inset:0;background:linear-gradient(135deg,#1A3A6B 0%,#2C5AA0 50%,#1A3A6B 100%);z-index:0;}
  .bg-wrapper::before{content:'';position:absolute;inset:0;background:radial-gradient(ellipse 600px 400px at 80% 20%,rgba(245,168,0,0.1) 0%,transparent 70%),radial-gradient(ellipse 400px 600px at 10% 80%,rgba(44,90,160,0.15) 0%,transparent 70%);animation:bgPulse 8s ease-in-out infinite alternate;}
  @keyframes bgPulse{from{opacity:.7;}to{opacity:1;}}
  .particles{position:fixed;inset:0;z-index:0;overflow:hidden;pointer-events:none;}
  .particle{position:absolute;border:1.5px solid rgba(255,255,255,0.06);border-radius:4px;animation:floatUp linear infinite;}
  @keyframes floatUp{0%{bottom:-80px;opacity:0;}10%{opacity:1;}90%{opacity:.4;}100%{bottom:110%;opacity:0;}}
  .l-page{position:relative;z-index:1;display:flex;align-items:center;justify-content:center;height:100vh;padding:20px;}
  .l-card{display:flex;width:100%;max-width:920px;min-height:540px;border-radius:24px;overflow:hidden;box-shadow:var(--sombra),0 0 0 1px rgba(255,255,255,0.06);animation:cardIn 0.8s cubic-bezier(0.22,1,0.36,1) both;}
  @keyframes cardIn{from{opacity:0;transform:translateY(40px) scale(0.96);}to{opacity:1;transform:translateY(0) scale(1);}}
  .panel-form{flex:1;background:var(--blanco);padding:52px 48px;display:flex;flex-direction:column;justify-content:center;position:relative;}
  .panel-form::before{content:'';position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,var(--naranja) 0%,var(--naranja-claro) 100%);}
  .form-title{font-size:22px;font-weight:800;color:var(--azul-oscuro);margin-bottom:6px;animation:fsd 0.6s 0.4s both;}
  .form-subtitle{font-size:13px;color:var(--gris-texto);margin-bottom:28px;animation:fsd 0.6s 0.45s both;}
  .field-group{display:flex;flex-direction:column;gap:14px;margin-bottom:10px;}
  .field-label{font-size:11px;font-weight:700;letter-spacing:.8px;color:var(--azul-medio);text-transform:uppercase;margin-bottom:5px;}
  .field{position:relative;animation:fsd 0.6s both;}
  .field-icon{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--gris-texto);display:flex;align-items:center;pointer-events:none;transition:color 0.2s;}
  .field:focus-within .field-icon{color:var(--azul-claro);}
  .field input{width:100%;height:50px;padding:0 14px 0 44px;border:1.5px solid var(--borde);border-radius:12px;font-family:'Inter',sans-serif;font-size:14px;font-weight:600;color:var(--azul-oscuro);background:var(--blanco);outline:none;transition:border-color .2s,box-shadow .2s,background .2s;}
  .field input::placeholder{color:var(--placeholder);font-weight:500;}
  .field input:focus{border-color:var(--azul-claro);background:var(--blanco);box-shadow:0 0 0 4px rgba(42,111,173,0.12);}
  .eye-btn{position:absolute;right:14px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:var(--gris-texto);display:flex;align-items:center;transition:color .2s;}
  .eye-btn:hover{color:var(--azul-claro);}
  .l-error{background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;padding:10px 14px;font-size:12px;color:#DC2626;font-weight:600;margin-bottom:8px;animation:fsd 0.3s both;}
  .links-row{display:flex;justify-content:space-between;align-items:center;margin:6px 0 22px;animation:fsd 0.6s 0.65s both;}
  .link-small{font-size:12px;font-weight:700;color:var(--azul-claro);text-decoration:none;transition:color .2s;}
  .link-small:hover{color:var(--naranja);}
  .btn-login{width:100%;height:52px;background:linear-gradient(135deg,var(--naranja) 0%,var(--naranja-claro) 100%);border:none;border-radius:12px;font-family:'Inter',sans-serif;font-size:15px;font-weight:800;letter-spacing:.5px;color:var(--blanco);cursor:pointer;box-shadow:0 6px 24px rgba(245,168,0,0.35);transition:transform .15s,box-shadow .15s,filter .15s;animation:fsd 0.6s 0.7s both;position:relative;overflow:hidden;}
  .btn-login::after{content:'';position:absolute;inset:0;background:linear-gradient(135deg,rgba(255,255,255,0.15) 0%,transparent 60%);pointer-events:none;}
  .btn-login:hover:not(:disabled){transform:translateY(-2px);box-shadow:0 10px 32px rgba(245,130,13,0.45);filter:brightness(1.05);}
  .btn-login:active:not(:disabled){transform:translateY(0);box-shadow:0 4px 16px rgba(245,130,13,0.30);}
  .btn-login:disabled{opacity:.7;cursor:not-allowed;}
  .version-tag{text-align:center;margin-top:20px;font-size:11px;color:var(--gris-suave);font-weight:600;animation:fsd 0.6s 0.8s both;}
  @keyframes fsd{from{opacity:0;transform:translateY(-16px);}to{opacity:1;transform:translateY(0);}}
  @keyframes spin{to{transform:rotate(360deg);}}
  .panel-banner{width:340px;flex-shrink:0;background:linear-gradient(160deg,#2C5AA0 0%,#1A3A6B 100%);padding:44px 36px;display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden;}
  .banner-circle{position:absolute;border-radius:50%;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);}
  .bc1{width:280px;height:280px;top:-80px;right:-80px;}.bc2{width:180px;height:180px;bottom:-60px;left:-60px;}.bc3{width:100px;height:100px;top:50%;left:50%;transform:translate(-50%,-50%);}
  .banner-line{position:absolute;top:0;right:60px;width:3px;height:100%;background:linear-gradient(180deg,transparent 0%,rgba(245,130,13,0.5) 40%,rgba(245,130,13,0.2) 80%,transparent 100%);}
  .banner-top{position:relative;z-index:1;}
  .badge{display:inline-flex;align-items:center;gap:6px;background:rgba(245,130,13,0.18);border:1px solid rgba(245,130,13,0.4);border-radius:20px;padding:5px 12px;margin-bottom:20px;}
  .badge-dot{width:6px;height:6px;border-radius:50%;background:var(--naranja);animation:pulse 2s ease-in-out infinite;}
  @keyframes pulse{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.5;transform:scale(1.4);}}
  .badge-text{font-size:10px;font-weight:800;letter-spacing:1.5px;color:var(--naranja-claro);text-transform:uppercase;}
  .banner-headline{font-family:'Inter',sans-serif;font-size:36px;font-weight:800;line-height:1.05;letter-spacing:1px;color:var(--blanco);margin-bottom:14px;}
  .banner-headline span{color:var(--naranja-claro);}
  .banner-desc{font-size:13px;line-height:1.6;color:rgba(255,255,255,0.65);font-weight:500;margin-bottom:24px;}
  .features{display:flex;flex-direction:column;gap:10px;}
  .feature-item{display:flex;align-items:center;gap:10px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:10px 14px;transition:background .2s;}
  .feature-item:hover{background:rgba(255,255,255,0.09);}
  .feature-icon{width:32px;height:32px;flex-shrink:0;background:linear-gradient(135deg,var(--naranja) 0%,var(--naranja-claro) 100%);border-radius:8px;display:flex;align-items:center;justify-content:center;}
  .feature-text{display:flex;flex-direction:column;}
  .feature-name{font-size:12px;font-weight:800;color:var(--blanco);line-height:1.2;}
  .feature-sub{font-size:10px;color:rgba(255,255,255,0.5);font-weight:500;}
  .banner-bottom{position:relative;z-index:1;}
  .norm-badge{display:flex;align-items:center;gap:8px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:10px 14px;}
  .norm-badge-icon{width:28px;height:28px;flex-shrink:0;background:rgba(245,130,13,0.2);border-radius:7px;display:flex;align-items:center;justify-content:center;}
  .norm-text{display:flex;flex-direction:column;}
  .norm-title{font-size:11px;font-weight:800;color:var(--blanco);}
  .norm-sub{font-size:10px;color:rgba(255,255,255,0.5);font-weight:500;}
  @media(max-width:680px){.panel-banner{display:none;}.panel-form{padding:40px 28px;}}
  .register-row{display:flex;align-items:center;justify-content:center;gap:8px;margin-top:16px;padding-top:16px;border-top:1px solid #EEF2F7;animation:fsd 0.6s 0.75s both;}
  .register-text{font-size:12px;color:var(--gris-texto);font-weight:600;}
  .register-link{font-size:12px;font-weight:800;color:var(--naranja);text-decoration:none;transition:color .2s;}
  .register-link:hover{color:var(--azul-claro);}
`