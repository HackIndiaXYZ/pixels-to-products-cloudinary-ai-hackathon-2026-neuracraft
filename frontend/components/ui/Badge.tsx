import { HTMLAttributes, forwardRef } from 'react'
import clsx from 'clsx'

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'outline'
  size?: 'sm' | 'md' | 'lg'
}

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = 'default', size = 'md', className, children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center font-medium rounded-full'
    
    const variants = {
      default: 'bg-surface-elevated text-text-secondary border border-border',
      primary: 'bg-primary-600/20 text-primary-400 border border-primary-600/30',
      secondary: 'bg-secondary-600/20 text-secondary-400 border border-secondary-600/30',
      success: 'bg-success-600/20 text-success-400 border border-success-600/30',
      warning: 'bg-warning-600/20 text-warning-400 border border-warning-600/30',
      danger: 'bg-danger-600/20 text-danger-400 border border-danger-600/30',
      outline: 'border-2 border-border text-text-secondary',
    }
    
    const sizes = {
      sm: 'px-2 py-0.5 text-xs',
      md: 'px-2.5 py-1 text-xs',
      lg: 'px-3 py-1.5 text-sm',
    }
    
    return (
      <span
        ref={ref}
        className={clsx(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {children}
      </span>
    )
  }
)

Badge.displayName = 'Badge'

export default Badge
