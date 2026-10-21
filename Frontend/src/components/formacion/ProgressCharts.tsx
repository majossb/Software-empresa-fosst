import React from 'react'

interface DonutProgressProps {
  value: number
  total: number
  size?: number
  strokeWidth?: number
  color?: string
  trackColor?: string
  label?: string
  sublabel?: string
  altText?: string
}

export const DonutProgress: React.FC<DonutProgressProps> = ({
  value,
  total,
  size = 120,
  strokeWidth = 10,
  color = '#0284c7', // sky-600
  trackColor = '#e2e8f0', // slate-200
  label,
  sublabel,
  altText,
}) => {
  const percentage = total > 0 ? Math.min(100, Math.max(0, Math.round((value / total) * 100))) : 0
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (percentage / 100) * circumference

  return (
    <div
      className="flex flex-col items-center justify-center"
      role="img"
      aria-label={altText || `${percentage}% de cumplimiento (${value} de ${total})`}
    >
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={trackColor}
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-2">
          <span className="text-xl font-black text-slate-900 tracking-tight font-mono">
            {percentage}%
          </span>
          {sublabel && (
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider leading-none mt-0.5">
              {sublabel}
            </span>
          )}
        </div>
      </div>
      {label && <span className="text-xs font-bold text-slate-700 mt-2 text-center">{label}</span>}
    </div>
  )
}

export interface StackedSegment {
  label: string
  count: number
  color: string
}

interface StackedBarProps {
  segments: StackedSegment[]
  height?: number
  showLegend?: boolean
  altText?: string
}

export const StackedBar: React.FC<StackedBarProps> = ({
  segments,
  height = 12,
  showLegend = true,
  altText,
}) => {
  const total = segments.reduce((sum, s) => sum + s.count, 0)

  return (
    <div
      className="w-full space-y-2"
      role="img"
      aria-label={
        altText ||
        segments
          .map((s) => `${s.label}: ${s.count} (${total > 0 ? Math.round((s.count / total) * 100) : 0}%)`)
          .join(', ')
      }
    >
      {/* Barra apilada */}
      <div
        className="w-full rounded-full overflow-hidden flex bg-slate-100 shadow-inner"
        style={{ height }}
      >
        {total === 0 ? (
          <div className="w-full h-full bg-slate-200" title="Sin datos" />
        ) : (
          segments.map((seg, idx) => {
            const pct = (seg.count / total) * 100
            if (pct <= 0) return null
            return (
              <div
                key={idx}
                style={{ width: `${pct}%`, backgroundColor: seg.color }}
                className="h-full transition-all duration-500 relative group"
                title={`${seg.label}: ${seg.count} (${Math.round(pct)}%)`}
              />
            )
          })
        )}
      </div>

      {/* Leyenda */}
      {showLegend && (
        <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-600 pt-1">
          {segments.map((seg, idx) => (
            <div key={idx} className="flex items-center gap-1.5">
              <span
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: seg.color }}
              />
              <span className="font-medium text-slate-600">{seg.label}:</span>
              <strong className="text-slate-900 font-bold">{seg.count}</strong>
              <span className="text-slate-400 text-[10px]">
                ({total > 0 ? Math.round((seg.count / total) * 100) : 0}%)
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
