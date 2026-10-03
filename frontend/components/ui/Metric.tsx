import { LucideIcon } from 'lucide-react'
import clsx from 'clsx'
import Card from './Card'

interface MetricProps {
  label: string
  value: string | number
  change?: {
    value: number
    trend: 'up' | 'down' | 'neutral'
  }
  icon?: LucideIcon
  variant?: 'default' | 'primary' | 'success' | 'warning'
}

export default function Metric({ label, value, change, icon: Icon, variant = 'default' }: MetricProps) {
  const iconVariants = {
    default: 'text-text-tertiary',
    primary: 'text-primary-400',
    success: 'text-success-400',
    warning: 'text-warning-400',
  }
  
  return (
    <Card padding="md" className="h-full">
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
    </Card>
  )
}
