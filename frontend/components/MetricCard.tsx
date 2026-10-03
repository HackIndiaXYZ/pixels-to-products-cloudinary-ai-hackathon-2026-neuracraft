import { ReactNode } from 'react'
import { LucideIcon } from 'lucide-react'
import clsx from 'clsx'

interface MetricCardProps {
  label: string
  value: string | number
  icon?: LucideIcon
  small?: boolean
  change?: {
    value: number
    trend: 'up' | 'down' | 'neutral'
  }
  variant?: 'default' | 'primary' | 'success' | 'warning'
}

export default function MetricCard({ 
  label, 
  value, 
  icon: Icon, 
  small = false,
  change,
  variant = 'default'
}: MetricCardProps) {
  if (small) {
    return (
      <div className="text-center">
        <p className="text-xs font-medium text-text-tertiary mb-1">{label}</p>
        <p className="text-sm font-semibold text-text-primary metric-number">{value}</p>
      </div>
    )
  }

  const iconVariants = {
    default: 'text-text-tertiary',
    primary: 'text-primary-400',
    success: 'text-success-400',
    warning: 'text-warning-400',
  }

  return (
    <div className="bg-surface border border-border rounded-xl p-6 transition-all duration-200 hover:shadow-lg">
      <div className="flex items-start justify-between mb-3">
        <span className="text-sm font-medium text-text-secondary">{label}</span>
        {Icon && <Icon className={clsx('w-5 h-5', iconVariants[variant])} />}
      </div>
      <div className="flex items-end justify-between">
        <p className="text-3xl font-bold text-text-primary metric-number">{value}</p>
        {change && (
          <span className={clsx(
            'text-xs font-medium',
            change.trend === 'up' && 'text-success-400',
            change.trend === 'down' && 'text-danger-400',
            change.trend === 'neutral' && 'text-text-tertiary'
          )}>
            {change.trend === 'up' && '+'}
            {change.value}%
          </span>
        )}
      </div>
    </div>
  )
}
