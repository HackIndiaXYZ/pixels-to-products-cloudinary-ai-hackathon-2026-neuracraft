import { HTMLAttributes } from 'react'
import clsx from 'clsx'

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'circle' | 'text'
  width?: string
  height?: string
}

export default function Skeleton({ 
  variant = 'default', 
  width, 
  height,
  className, 
  ...props 
}: SkeletonProps) {
  const baseStyles = 'animate-pulse bg-surface-elevated'
  
  const variants = {
    default: 'rounded-lg',
    circle: 'rounded-full',
    text: 'rounded h-4',
  }
  
  const style = {
    width: width || (variant === 'circle' ? '40px' : '100%'),
    height: height || (variant === 'circle' ? '40px' : variant === 'text' ? '16px' : '100px'),
  }
  
  return (
    <div
      className={clsx(baseStyles, variants[variant], className)}
      style={style}
      {...props}
    />
  )
}
