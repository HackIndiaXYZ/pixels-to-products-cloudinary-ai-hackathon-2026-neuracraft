import clsx from 'clsx'

interface ProgressProps {
  value: number // 0-100
  size?: 'sm' | 'md' | 'lg'
  variant?: 'primary' | 'secondary' | 'success'
  showLabel?: boolean
}

export default function Progress({ 
  value, 
  size = 'md', 
  variant = 'primary',
  showLabel = false
}: ProgressProps) {
  const heights = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  }
  
  const variants = {
    primary: 'bg-primary-600',
    secondary: 'bg-secondary-600',
    success: 'bg-success-600',
  }
  
  const clampedValue = Math.min(Math.max(value, 0), 100)
  
  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-text-secondary">Progress</span>
          <span className="text-sm font-medium text-text-primary">{clampedValue}%</span>
        </div>
      )}
      <div className={clsx('w-full bg-surface-elevated rounded-full overflow-hidden', heights[size])}>
        <div
          className={clsx('h-full rounded-full transition-all duration-300', variants[variant])}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  )
}
