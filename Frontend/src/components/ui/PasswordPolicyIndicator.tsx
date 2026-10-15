export interface PasswordRequirements {
  minLength: boolean
  hasUpper: boolean
  hasLower: boolean
  hasNumber: boolean
  hasSpecial: boolean
  isValid: boolean
}

export function checkPasswordPolicy(password: string): PasswordRequirements {
  const minLength = password.length >= 8
  const hasUpper = /[A-Z]/.test(password)
  const hasLower = /[a-z]/.test(password)
  const hasNumber = /[0-9]/.test(password)
  const hasSpecial = /[^A-Za-z0-9]/.test(password)
  const isValid = minLength && hasUpper && hasLower && hasNumber && hasSpecial
  return { minLength, hasUpper, hasLower, hasNumber, hasSpecial, isValid }
}

export function PasswordPolicyIndicator({ password }: { password: string }) {
  if (!password) return null

  const reqs = checkPasswordPolicy(password)

  const items = [
    { key: 'minLength', label: 'Al menos 8 caracteres', pass: reqs.minLength },
    { key: 'hasUpper', label: 'Una letra mayúscula (A-Z)', pass: reqs.hasUpper },
    { key: 'hasLower', label: 'Una letra minúscula (a-z)', pass: reqs.hasLower },
    { key: 'hasNumber', label: 'Un número (0-9)', pass: reqs.hasNumber },
    { key: 'hasSpecial', label: 'Un carácter especial (ej. !@#$%^&*)', pass: reqs.hasSpecial },
  ]

  return (
    <div style={{
      marginTop: '8px',
      padding: '10px 14px',
      backgroundColor: '#F8FAFC',
      border: '1px solid #E2E8F0',
      borderRadius: '10px',
      fontSize: '11px',
      display: 'flex',
      flexDirection: 'column',
      gap: '4px'
    }}>
      {items.map(item => (
        <div key={item.key} style={{ display: 'flex', alignItems: 'center', gap: '6px', color: item.pass ? '#10B981' : '#64748B', fontWeight: item.pass ? 600 : 400 }}>
          <span style={{ fontWeight: '700' }}>{item.pass ? '✓' : '○'}</span>
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  )
}
