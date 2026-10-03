import clsx from 'clsx'
import { Circle } from 'lucide-react'

interface StatusBadgeProps {
  status: 'draft' | 'uploading' | 'validating' | 'processing' | 'completed' | 'failed'
  showDot?: boolean
}

export default function StatusBadge({ status, showDot = true }: StatusBadgeProps) {
  const variants = {
    draft: {
      bg: 'bg-text-muted/20',
      text: 'text-text-secondary',
      dot: 'text-text-muted',
      label: 'Draft',
    },
    uploading: {
      bg: 'bg-secondary-600/20',
      text: 'text-secondary-400',
      dot: 'text-secondary-400',
      label: 'Uploading',
    },
    validating: {
      bg: 'bg-warning-600/20',
      text: 'text-warning-400',
      dot: 'text-warning-400',
      label: 'Validating',
    },
    processing: {
      bg: 'bg-primary-600/20',
      text: 'text-primary-400',
      dot: 'text-primary-400',
      label: 'Processing',
    },
    completed: {
      bg: 'bg-success-600/20',
      text: 'text-success-400',
      dot: 'text-success-400',
      label: 'Completed',
    },
    failed: {
      bg: 'bg-danger-600/20',
      text: 'text-danger-400',
      dot: 'text-danger-400',
      label: 'Failed',
    },
  }
  
  const variant = variants[status]
  
  return (
    <span className={clsx(
      'inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium',
      variant.bg,
      variant.text
    )}>
      {showDot && (
        <Circle className={clsx('w-2 h-2 mr-1.5 fill-current', variant.dot)} />
      )}
      {variant.label}
    </span>
  )
}
