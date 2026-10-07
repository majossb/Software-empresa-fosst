import { useState, useEffect, useRef, FormEvent } from 'react'
import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import { useAuth } from '@/store/auth.context'
import { ROLE_ROUTES } from '@/types'
import { authService } from '@/services/auth.service'

const OTP_LENGTH = 6

export default function OTPPage() {
  const { verifyOTP } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const state = location.state as {
    usuarioId:          string
    expiresAt:          string
    nit:                string
    documento:          string
    password:           string
  } | null

  const [digits, setDigits] = useState<string[]>(Array(OTP_LENGTH).fill(''))
  const [loading, setLoading] = useState(false)
  const [resending, setResending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [expiresAt, setExpiresAt] = useState<Date | null>(
    state?.expiresAt ? new Date(state.expiresAt) : null
  )
  const [secondsLeft, setSecondsLeft] = useState(0)
  const [resendCooldown, setResendCooldown] = useState(0)

  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  useEffect(() => {
    if (!expiresAt) return

    const calcRemaining = () => {
      const diff = Math.max(0, Math.floor((expiresAt.getTime() - Date.now()) / 1000))
      setSecondsLeft(diff)
      return diff
    }

    calcRemaining()
    const timer = setInterval(() => {
      if (calcRemaining() <= 0) clearInterval(timer)
    }, 1000)

    return () => clearInterval(timer)
  }, [expiresAt])

  useEffect(() => {
    if (resendCooldown <= 0) return
    const timer = setInterval(() => {
      setResendCooldown(prev => (prev <= 1 ? 0 : prev - 1))
    }, 1000)
    return () => clearInterval(timer)
  }, [resendCooldown])

  useEffect(() => {
    inputRefs.current[0]?.focus()
  }, [])

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  const handleDigitChange = (index: number, value: string) => {
    const cleaned = value.replace(/\D/g, '')
    if (!cleaned) {
      const newDigits = [...digits]
      newDigits[index] = ''
      setDigits(newDigits)
      return
    }

    if (cleaned.length > 1) {
      const chars = cleaned.slice(0, OTP_LENGTH - index).split('')
      const newDigits = [...digits]
      chars.forEach((char, i) => {
        if (index + i < OTP_LENGTH) {
          newDigits[index + i] = char
        }
      })
      setDigits(newDigits)
      const nextIndex = Math.min(index + chars.length, OTP_LENGTH - 1)
      inputRefs.current[nextIndex]?.focus()
      return
    }

    const newDigits = [...digits]
    newDigits[index] = cleaned
    setDigits(newDigits)

    if (index < OTP_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, OTP_LENGTH)
    if (pasted) {
      const newDigits = Array(OTP_LENGTH).fill('')
      pasted.split('').forEach((char, i) => { newDigits[i] = char })
      setDigits(newDigits)
      const focusIndex = Math.min(pasted.length, OTP_LENGTH - 1)
      inputRefs.current[focusIndex]?.focus()
    }
  }

  const handleSubmit = async (e?: FormEvent) => {
    e?.preventDefault()
    if (!state?.usuarioId) return

    setError(null)
    setSuccessMsg(null)

    const code = digits.join('')
    if (code.length !== OTP_LENGTH) {
      setError('Ingresa los 6 dígitos del código.')
      return
    }

    if (secondsLeft <= 0) {
      setError('El código ha expirado. Reenvía un nuevo código.')
      return
    }

    setLoading(true)
    try {
      const user = await verifyOTP(state.usuarioId, code)
      if (user.rol === 'responsable') {
        navigate('/app/responsable/configuracion', { replace: true })
      } else {
        navigate(ROLE_ROUTES[user.rol], { replace: true })
      }
    } catch (err: any) {
      const message =
        err?.message ?? 'El código ingresado no es válido o ha expirado.'
      setError(message)
      setDigits(Array(OTP_LENGTH).fill(''))
      inputRefs.current[0]?.focus()
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    if (!state || resendCooldown > 0 || resending) return
    setError(null)
    setSuccessMsg(null)
    setResending(true)

    try {
      const response = await authService.resendOTP({
        nit: state.nit,
        documento: state.documento,
        password: state.password,
      })
      if (response.expires_at) {
        setExpiresAt(new Date(response.expires_at))
      }
      setResendCooldown(60)
      setDigits(Array(OTP_LENGTH).fill(''))
      setSuccessMsg('Nuevo código enviado a tu correo.')
      inputRefs.current[0]?.focus()
    } catch (err: any) {
      setError(err?.message ?? 'No se pudo reenviar el código. Intenta más tarde.')
    } finally {
      setResending(false)
    }
  }

  if (!state?.usuarioId) {
    return <Navigate to="/login" replace />
  }

  const isExpired = secondsLeft <= 0

  return (
    <>
      <style>{CSS}</style>
      <div className="lr">
        <div className="bg-wrapper" />
        <main className="l-page">
          <div className="l-card-narrow">
            {/* Logo */}
            <div className="otp-logo">
              <div className="otp-logo-icon">
                <img src="/assets/logo-fosst-icon.png" alt="FOSST Logo" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
              </div>
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: '20px', fontWeight: '700', color: '#1a2f6e' }}>Fosst</div>
                <div style={{ fontSize: '11px', color: '#6b7280', letterSpacing: '0.05em' }}>DIAGNÓSTICO SG-SST</div>
              </div>
            </div>

            {/* Shield icon */}
            <div className="otp-shield">
              <svg width="32" height="32" fill="none" viewBox="0 0 24 24">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="#F5A800" strokeWidth="1.8" fill="rgba(245,168,0,0.08)"/>
                <path d="M9 12l2 2 4-4" stroke="#F5A800" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>

            <h1 className="form-title" style={{ textAlign: 'center' }}>Verificación de seguridad</h1>
            <p className="form-subtitle">
              Hemos enviado un código de 6 dígitos a tu correo electrónico registrado.
            </p>

            {/* Temporizador */}
            <div className={`otp-timer ${isExpired ? 'otp-timer-expired' : ''}`}>
              <svg width="14" height="14" fill="none" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2"/>
                <path d="M12 7v5l3 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
              {isExpired
                ? <span>Código expirado</span>
                : <span>El código expira en <strong>{formatTime(secondsLeft)}</strong></span>
              }
            </div>

            <form onSubmit={handleSubmit} noValidate>
              {/* Inputs de dígitos */}
              <div className="otp-inputs" onPaste={handlePaste}>
                {digits.map((digit, i) => (
                  <input
                    key={i}
                    ref={el => { inputRefs.current[i] = el }}
                    id={`otp-digit-${i}`}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={e => handleDigitChange(i, e.target.value)}
                    onKeyDown={e => handleKeyDown(i, e)}
                    className={`otp-digit ${digit ? 'otp-digit-filled' : ''}`}
                    disabled={loading || isExpired}
                    autoComplete="one-time-code"
                  />
                ))}
              </div>

              {/* Mensajes */}
              {error && <div className="l-error">{error}</div>}
              {successMsg && <div className="l-success">{successMsg}</div>}

              {/* Botón verificar */}
              <button
                id="otp-submit"
                type="submit"
                className="btn-action"
                disabled={loading || isExpired || digits.join('').length !== OTP_LENGTH}
              >
                {loading ? (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 1s linear infinite' }}>
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.416" strokeDashoffset="10" strokeLinecap="round" />
                    </svg>
                    Verificando...
                  </span>
                ) : 'Verificar →'}
              </button>
            </form>

            {/* Reenviar código */}
            <div className="otp-resend">
              <span className="otp-resend-text">¿No recibiste el código?</span>
              <button
                type="button"
                className="otp-resend-btn"
                onClick={handleResend}
                disabled={resendCooldown > 0 || resending}
              >
                {resending ? 'Enviando...' :
                 resendCooldown > 0 ? `Reenviar en ${resendCooldown}s` :
                 'Reenviar código'}
              </button>
            </div>

            {/* Volver */}
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <button
                type="button"
                className="link-small"
                onClick={() => navigate('/login', { replace: true })}
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
              >
                ← Volver al inicio de sesión
              </button>
            </div>

            <p className="version-tag" style={{ marginTop: '24px' }}>DiagnostiSST v1.0 · Res. 0312 de 2019</p>
          </div>
        </main>
      </div>
    </>
  )
}

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  :root{--azul-oscuro:#1A3A6B;--azul-medio:#1A3A6B;--azul-claro:#2C5AA0;--naranja:#F5A800;--naranja-claro:#FFB81C;--blanco:#FFFFFF;--gris-claro:#F4F5F7;--gris-texto:#4A5568;--borde:#D1D5DC;--placeholder:#94A3B8;--sombra:0 20px 60px rgba(26,58,107,0.18);}
  .lr,.lr *{box-sizing:border-box;margin:0;padding:0;}
  .lr{font-family:'Inter',sans-serif;background:var(--azul-oscuro);min-height:100vh;overflow:hidden;}
  .bg-wrapper{position:fixed;inset:0;background:linear-gradient(135deg,#1A3A6B 0%,#2C5AA0 50%,#1A3A6B 100%);z-index:0;}
  .l-page{position:relative;z-index:1;display:flex;align-items:center;justify-content:center;height:100vh;padding:20px;}
  .l-card-narrow{background:var(--blanco);padding:48px 44px;border-radius:24px;box-shadow:var(--sombra);width:100%;max-width:440px;position:relative;animation:cardIn 0.6s cubic-bezier(0.22,1,0.36,1) both;}
  .l-card-narrow::before{content:'';position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,var(--naranja) 0%,var(--naranja-claro) 100%);border-radius:24px 24px 0 0;}
  @keyframes cardIn{from{opacity:0;transform:translateY(40px) scale(0.96);}to{opacity:1;transform:translateY(0) scale(1);}}
  @keyframes spin{to{transform:rotate(360deg);}}

  .otp-logo{display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:24px;}
  .otp-logo-icon{width:48px;height:48px;background:#f0f2f5;border-radius:12px;display:flex;align-items:center;justify-content:center;padding:6px;}

  .otp-shield{width:56px;height:56px;margin:0 auto 16px;background:rgba(245,168,0,0.08);border:1.5px solid rgba(245,168,0,0.25);border-radius:16px;display:flex;align-items:center;justify-content:center;animation:fsd 0.5s 0.2s both;}
  @keyframes fsd{from{opacity:0;transform:translateY(-16px);}to{opacity:1;transform:translateY(0);}}

  .form-title{font-size:22px;font-weight:800;color:var(--azul-oscuro);margin-bottom:8px;animation:fsd 0.5s 0.3s both;}
  .form-subtitle{font-size:13px;color:var(--gris-texto);text-align:center;line-height:1.5;margin-bottom:20px;animation:fsd 0.5s 0.35s both;}

  .otp-timer{display:flex;align-items:center;justify-content:center;gap:6px;padding:8px 16px;background:rgba(44,90,160,0.06);border:1px solid rgba(44,90,160,0.12);border-radius:10px;font-size:13px;color:var(--azul-claro);font-weight:600;margin-bottom:24px;animation:fsd 0.5s 0.4s both;}
  .otp-timer strong{font-weight:800;}
  .otp-timer-expired{background:rgba(239,68,68,0.06);border-color:rgba(239,68,68,0.15);color:#DC2626;}

  .otp-inputs{display:flex;gap:10px;justify-content:center;margin-bottom:20px;animation:fsd 0.5s 0.45s both;}
  .otp-digit{width:50px;height:58px;border:2px solid var(--borde);border-radius:14px;text-align:center;font-family:'Inter',sans-serif;font-size:24px;font-weight:800;color:var(--azul-oscuro);background:var(--blanco);outline:none;transition:border-color 0.2s,box-shadow 0.2s,background 0.2s;caret-color:var(--naranja);}
  .otp-digit:focus{border-color:var(--azul-claro);box-shadow:0 0 0 4px rgba(42,111,173,0.12);background:var(--blanco);}
  .otp-digit-filled{border-color:var(--naranja);background:rgba(245,168,0,0.04);}
  .otp-digit:disabled{opacity:0.6;cursor:not-allowed;}

  .l-error{background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;padding:10px 14px;font-size:12px;color:#DC2626;font-weight:600;margin-bottom:12px;text-align:center;animation:fsd 0.3s both;}
  .l-success{background:#ECFDF5;border:1px solid #A7F3D0;border-radius:10px;padding:10px 14px;font-size:12px;color:#059669;font-weight:600;margin-bottom:12px;text-align:center;animation:fsd 0.3s both;}

  .btn-action{width:100%;height:52px;background:linear-gradient(135deg,var(--naranja) 0%,var(--naranja-claro) 100%);border:none;border-radius:12px;font-family:'Inter',sans-serif;font-size:15px;font-weight:800;letter-spacing:.5px;color:var(--blanco);cursor:pointer;box-shadow:0 6px 24px rgba(245,168,0,0.35);transition:transform .15s,box-shadow .15s,filter .15s;position:relative;overflow:hidden;animation:fsd 0.5s 0.5s both;}
  .btn-action::after{content:'';position:absolute;inset:0;background:linear-gradient(135deg,rgba(255,255,255,0.15) 0%,transparent 60%);pointer-events:none;}
  .btn-action:hover:not(:disabled){transform:translateY(-2px);box-shadow:0 10px 32px rgba(245,130,13,0.45);filter:brightness(1.05);}
  .btn-action:disabled{opacity:.6;cursor:not-allowed;}

  .otp-resend{display:flex;align-items:center;justify-content:center;gap:8px;margin-top:20px;padding-top:16px;border-top:1px solid #EEF2F7;}
  .otp-resend-text{font-size:12px;color:var(--gris-texto);font-weight:600;}
  .otp-resend-btn{font-family:'Inter',sans-serif;font-size:12px;font-weight:800;color:var(--naranja);background:none;border:none;cursor:pointer;transition:color 0.2s;padding:0;}
  .otp-resend-btn:hover:not(:disabled){color:var(--azul-claro);}
  .otp-resend-btn:disabled{color:var(--placeholder);cursor:not-allowed;}

  .link-small{font-size:12px;font-weight:700;color:var(--azul-claro);text-decoration:none;transition:color .2s;}
  .link-small:hover{color:var(--naranja);}

  .version-tag{text-align:center;font-size:11px;color:var(--gris-suave, #94A3B8);font-weight:600;}

  @media(max-width:480px){
    .l-card-narrow{padding:36px 24px;}
    .otp-digit{width:42px;height:50px;font-size:20px;}
    .otp-inputs{gap:6px;}
  }
`
