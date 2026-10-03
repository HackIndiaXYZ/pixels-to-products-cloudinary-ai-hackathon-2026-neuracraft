'use client'

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { api } from '@/lib/api'
import type { Analysis, CreativeDNAInsight, EvidenceTier } from '@/types'
import { Dna, TrendingUp, TrendingDown, Minus, ChevronDown, Info } from 'lucide-react'
import { SectionHeader, Card, EmptyState, Skeleton, ErrorState, Badge } from '@/components/ui'
import EvidenceBadge from '@/components/EvidenceBadge'

const EVIDENCE_TIERS: EvidenceTier[] = ['strong', 'moderate', 'weak', 'no_clear_evidence', 'insufficient_evidence']
const TIER_LABELS: Record<EvidenceTier, string> = {
  strong: 'Strong',
  moderate: 'Moderate',
  weak: 'Weak',
  no_clear_evidence: 'No Clear Evidence',
  insufficient_evidence: 'Insufficient Evidence',
}

function TierCount({ insights, tier }: { insights: CreativeDNAInsight[]; tier: EvidenceTier }) {
  const count = insights.filter((i) => i.evidence_tier === tier).length
  const colors: Record<EvidenceTier, string> = {
    strong: 'text-success-400',
    moderate: 'text-primary-400',
    weak: 'text-warning-400',
    no_clear_evidence: 'text-text-tertiary',
    insufficient_evidence: 'text-text-muted',
  }
  return (
    <Card padding="sm" className="text-center">
      <p className={`text-2xl font-bold metric-number ${colors[tier]}`}>{count}</p>
      <p className="text-xs text-text-tertiary mt-1">{TIER_LABELS[tier]}</p>
    </Card>
  )
}

export default function DNAPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [insights, setInsights] = useState<CreativeDNAInsight[]>([])
  const [loadingList, setLoadingList] = useState(true)
  const [loadingInsights, setLoadingInsights] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [filterTier, setFilterTier] = useState<string>('all')
  const [filterMetric, setFilterMetric] = useState<string>('all')

  useEffect(() => {
    api.getAnalyses()
      .then((data) => {
        const completed = data.filter((a) => a.status === 'completed')
        setAnalyses(completed)
        if (completed.length > 0) setSelectedId(completed[0].id)
      })
      .catch(() => setError('Failed to load analyses.'))
      .finally(() => setLoadingList(false))
  }, [])

  useEffect(() => {
    if (selectedId == null) return
    setLoadingInsights(true)
    api.getCreativeDNA(selectedId)
      .then(setInsights)
      .catch(() => setError('Failed to load Creative DNA insights.'))
      .finally(() => setLoadingInsights(false))
  }, [selectedId])

  const metrics = Array.from(new Set(insights.map((i) => i.metric_name))).sort()

  const filtered = insights.filter((i) => {
    const tierOk = filterTier === 'all' || i.evidence_tier === filterTier
    const metricOk = filterMetric === 'all' || i.metric_name === filterMetric
    return tierOk && metricOk
  })

  if (loadingList) return (
    <DashboardLayout>
      <SectionHeader title="Creative DNA" description="Visual pattern intelligence" />
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">{[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} height="70px" />)}</div>
      <Skeleton height="400px" />
    </DashboardLayout>
  )

  if (error) return <DashboardLayout><ErrorState message={error} onRetry={() => window.location.reload()} /></DashboardLayout>

  return (
    <DashboardLayout>
      <SectionHeader
        title="Creative DNA"
        description="Statistical associations between visual characteristics and performance metrics"
      />

      {/* Analysis selector */}
      {analyses.length > 0 && (
        <div className="mb-6 flex items-center space-x-3">
          <span className="text-sm text-text-tertiary">Analysis:</span>
          <div className="relative">
            <select
              value={selectedId ?? ''}
              onChange={(e) => setSelectedId(Number(e.target.value))}
              className="appearance-none bg-surface border border-border text-text-primary text-sm rounded-lg px-3 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-primary-500"
              aria-label="Select analysis"
            >
              {analyses.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary pointer-events-none" />
          </div>
        </div>
      )}

      {analyses.length === 0 ? (
        <EmptyState
          icon={Dna}
          title="No completed analyses"
          description="Complete an analysis to generate Creative DNA insights."
          action={{ label: 'New Analysis', onClick: () => { window.location.href = '/new' } }}
        />
      ) : loadingInsights ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">{[1,2,3,4,5].map(i=><Skeleton key={i} height="70px"/>)}</div>
          <Skeleton height="400px" />
        </div>
      ) : (
        <>
          {/* Evidence tier summary */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            {EVIDENCE_TIERS.map((tier) => (
              <TierCount key={tier} insights={insights} tier={tier} />
            ))}
          </div>

          {/* Disclaimer */}
          <div className="flex items-start space-x-2 bg-surface border border-border rounded-lg px-4 py-3 mb-6">
            <Info className="w-4 h-4 text-text-tertiary flex-shrink-0 mt-0.5" />
            <p className="text-xs text-text-secondary">
              Creative DNA identifies <strong className="text-text-primary">statistical associations</strong> between visual characteristics and performance metrics in this dataset. Association does not imply causation. Results may not generalise beyond this dataset.
            </p>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-3 mb-6">
            <div className="relative">
              <select
                value={filterTier}
                onChange={(e) => setFilterTier(e.target.value)}
                className="appearance-none bg-surface border border-border text-text-primary text-sm rounded-lg px-3 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-primary-500"
                aria-label="Filter by evidence tier"
              >
                <option value="all">All evidence tiers</option>
                {EVIDENCE_TIERS.map((t) => (
                  <option key={t} value={t}>{TIER_LABELS[t]}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary pointer-events-none" />
            </div>
            {metrics.length > 0 && (
              <div className="relative">
                <select
                  value={filterMetric}
                  onChange={(e) => setFilterMetric(e.target.value)}
                  className="appearance-none bg-surface border border-border text-text-primary text-sm rounded-lg px-3 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  aria-label="Filter by metric"
                >
                  <option value="all">All metrics</option>
                  {metrics.map((m) => <option key={m} value={m}>{m.toUpperCase()}</option>)}
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary pointer-events-none" />
              </div>
            )}
            <span className="text-sm text-text-tertiary self-center">
              {filtered.length} insight{filtered.length !== 1 ? 's' : ''}
            </span>
          </div>

          {/* Insights list */}
          {filtered.length === 0 ? (
            insights.length === 0 ? (
              <EmptyState
                icon={Dna}
                title="No Creative DNA insights available"
                description="Creative DNA requires registered creative assets with visual features. Upload your creative images and re-run the analysis to generate insights. Without real visual assets, statistical associations between visual characteristics and performance cannot be computed."
                action={{ label: 'New Analysis', onClick: () => { window.location.href = '/new' } }}
              />
            ) : (
              <EmptyState
                icon={Dna}
                title="No insights match your filters"
                description="Try changing the evidence tier or metric filter."
              />
            )
          ) : (
            <div className="space-y-4">
              {filtered.map((insight) => {
                const isPositive = insight.positive_median >= insight.negative_median
                const pctAbs = Math.abs(insight.percent_difference).toFixed(1)
                const feature = insight.feature_name.replace(/_/g, ' ')

                return (
                  <Card key={insight.id} hover>
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
                          isPositive ? 'bg-success-500/15' : 'bg-danger-600/15'
                        }`}>
                          {isPositive
                            ? <TrendingUp className="w-5 h-5 text-success-400" />
                            : insight.positive_median === insight.negative_median
                            ? <Minus className="w-5 h-5 text-text-tertiary" />
                            : <TrendingDown className="w-5 h-5 text-danger-400" />}
                        </div>
                        <div>
                          <h3 className="font-semibold text-text-primary capitalize">
                            {feature}
                          </h3>
                          <div className="flex items-center space-x-2 mt-0.5">
                            <Badge variant="default" size="sm">{insight.metric_name.toUpperCase()}</Badge>
                            <span className={`text-sm font-medium ${isPositive ? 'text-success-400' : 'text-danger-400'}`}>
                              {isPositive ? '+' : ''}{pctAbs}% observed difference
                            </span>
                          </div>
                        </div>
                      </div>
                      <EvidenceBadge tier={insight.evidence_tier} />
                    </div>

                    <p className="text-sm text-text-secondary mb-3">{insight.explanation}</p>

                    {/* Stats grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                      <div className="bg-surface rounded-lg px-3 py-2">
                        <p className="text-text-tertiary mb-0.5">With feature (n={insight.sample_size_positive})</p>
                        <p className="font-medium text-text-primary">{insight.positive_median.toFixed(4)}</p>
                      </div>
                      <div className="bg-surface rounded-lg px-3 py-2">
                        <p className="text-text-tertiary mb-0.5">Without feature (n={insight.sample_size_negative})</p>
                        <p className="font-medium text-text-primary">{insight.negative_median.toFixed(4)}</p>
                      </div>
                      <div className="bg-surface rounded-lg px-3 py-2">
                        <p className="text-text-tertiary mb-0.5">p-value</p>
                        <p className="font-medium text-text-primary">
                          {insight.p_value != null ? insight.p_value.toFixed(4) : '—'}
                        </p>
                      </div>
                      <div className="bg-surface rounded-lg px-3 py-2">
                        <p className="text-text-tertiary mb-0.5">Effect size</p>
                        <p className="font-medium text-text-primary">
                          {insight.effect_size != null ? insight.effect_size.toFixed(3) : '—'}
                        </p>
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
          )}
        </>
      )}
    </DashboardLayout>
  )
}
