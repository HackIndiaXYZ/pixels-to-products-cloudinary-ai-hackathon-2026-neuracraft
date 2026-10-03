import clsx from 'clsx'

interface EvidenceBadgeProps {
  tier: string
}

export default function EvidenceBadge({ tier }: EvidenceBadgeProps) {
  const getColorClass = () => {
    switch (tier.toLowerCase()) {
      case 'strong':
        return 'bg-success-600/20 text-success-400 border-success-600/30'
      case 'moderate':
        return 'bg-primary-600/20 text-primary-400 border-primary-600/30'
      case 'weak':
        return 'bg-warning-600/20 text-warning-400 border-warning-600/30'
      case 'no_clear_evidence':
        return 'bg-surface-elevated text-text-tertiary border-border'
      case 'insufficient_evidence':
        return 'bg-warning-600/20 text-warning-400 border-warning-600/30'
      default:
        return 'bg-surface-elevated text-text-tertiary border-border'
    }
  }

  const getLabel = () => {
    return tier.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }
  
  const getDots = () => {
    switch (tier.toLowerCase()) {
      case 'strong':
        return '●●●●●'
      case 'moderate':
        return '●●●○○'
      case 'weak':
        return '●●○○○'
      default:
        return '○○○○○'
    }
  }

  return (
    <span className={clsx(
      'inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-full border',
      getColorClass()
    )}>
      <span className="mr-2 text-xs opacity-70">{getDots()}</span>
      {getLabel()}
    </span>
  )
}
