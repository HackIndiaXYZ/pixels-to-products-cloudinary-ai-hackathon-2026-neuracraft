import { HTMLAttributes, forwardRef } from 'react'
import clsx from 'clsx'

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'elevated' | 'outline'
  padding?: 'none' | 'sm' | 'md' | 'lg'
  hover?: boolean
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ variant = 'default', padding = 'md', hover = false, className, children, ...props }, ref) => {
    const baseStyles = 'rounded-xl transition-all duration-200'
    
    const variants = {
      default: 'bg-surface border border-border',
      glass: 'bg-surface/80 backdrop-blur-xl border border-border/50',
      elevated: 'bg-surface-elevated border border-border shadow-lg',
      outline: 'border-2 border-border',
    }
    
    const paddings = {
      none: '',
      sm: 'p-3',
      md: 'p-6',
      lg: 'p-8',
    }
    
    const hoverStyles = hover ? 'hover:shadow-xl hover:-translate-y-0.5 cursor-pointer' : ''
    
    return (
      <div
        ref={ref}
        className={clsx(
          baseStyles,
          variants[variant],
          paddings[padding],
          hoverStyles,
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

Card.displayName = 'Card'

export default Card
