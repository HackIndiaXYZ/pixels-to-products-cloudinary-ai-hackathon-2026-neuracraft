'use client'

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import DashboardLayout from '@/components/DashboardLayout'
import { api } from '@/lib/api'
import type { Analysis, AnalysisOverview, CreativeDNAInsight } from '@/types'
import {
  Plus,
  TrendingUp,
  Image,
  Dna,
  DollarSign,
  MousePointerClick,
  Sparkles,
  ArrowRight,
  BarChart3,
  RefreshCw,
  ChevronDown
} from 'lucide-react'
import {
  SectionHeader,
  Card,
  Button,
  Metric,
  EmptyState,
  Skeleton,
  StatusBadge,
  ErrorState
} from '@/components/ui'
import EvidenceBadge from '@/components/EvidenceBadge'

function fmtCurrency(v: number | null) {
  if (v == null) return '—'
  return `$${v.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
}
function fmtPct(v: number | null) {
  if (v == null) return '—'
  return `${(v * 100).toFixed(2)}%`
}
function fmtMultiple(v: number | null) {
  if (v == null) return '—'
  return `${v.toFixed(2)}x`
}

export default function DashboardPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [overview, setOverview] = useState<AnalysisOverview | null>(null)
  const [insights, setInsights] = useState<CreativeDNAInsight[]>([])
  const [loadingList, setLoadingList] = useState(true)
  const [loadingOverview, setLoadingOverview] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load analyses list
  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.getAnalyses()
        setAnalyses(data)
        // Default to the most recent completed analysis
        const completed = data.filter((a) => a.status === 'completed')
        if (completed.length > 0) setSelectedId(completed[0].id)
      } catch {
        setError('Failed to load analyses. Is the backend running?')
      } finally {
        setLoadingList(false)
      }
    }
    load()
  }, [])

  // Poll for processing analyses
  useEffect(() => {
    const processingAnalyses = analyses.filter(
      (a) => a.status === 'processing' || a.status === 'validating'
    )
    
    if (processingAnalyses.length === 0) return

    const pollInterval = setInterval(async () => {
      try {
        // Check status for each processing analysis
        const updates = await Promise.all(
          processingAnalyses.map((a) => api.getAnalysisStatus(a.id))
        )
        
        let hasChanges = false
        const updatedAnalyses = analyses.map((analysis) => {
          const update = updates.find((u) => u.id === analysis.id)
          if (update && update.status !== analysis.status) {
            hasChanges = true
            return { ...analysis, status: update.status, current_stage: update.current_stage }
          }
          return analysis
        })
        
        if (hasChanges) {
          setAnalyses(updatedAnalyses)
          
          // If a processing analysis completes and no analysis is selected, select it
          const newlyCompleted = updatedAnalyses.find(
            (a) => a.status === 'completed' && 
            processingAnalyses.some((p) => p.id === a.id)
          )
          if (newlyCompleted && !selectedId) {
            setSelectedId(newlyCompleted.id)
          }
        }
      } catch (err) {
        console.error('Error polling analysis status:', err)
      }
    }, 3000)

    return () => clearInterval(pollInterval)
  }, [analyses, selectedId])

  // Load overview + insights when selected analysis changes
  const loadOverview = useCallback(async (id: number) => {
    setLoadingOverview(true)
    setOverview(null)
    setInsights([])
    try {
      const [ov, ins] = await Promise.all([
        api.getAnalysisOverview(id),
        api.getInsights(id, 3),
      ])
      setOverview(ov)
      setInsights(ins)
    } catch {
      setOverview(null)
    } finally {
      setLoadingOverview(false)
    }
  }, [])

  useEffect(() => {
    if (selectedId != null) loadOverview(selectedId)
  }, [selectedId, loadOverview])

  const completedAnalyses = analyses.filter((a) => a.status === 'completed')
  const selectedAnalysis = analyses.find((a) => a.id === selectedId) ?? null

  // ─── Loading skeleton ──────────────────────────────────────────────────────
  if (loadingList) {
    return (
      <DashboardLayout>
        <SectionHeader title="Campaign Overview" description="Performance metrics and creative intelligence" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} height="120px" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <Skeleton height="220px" className="lg:col-span-2" />
          <Skeleton height="220px" />
        </div>
      </DashboardLayout>
    )
  }

  // ─── Error state ───────────────────────────────────────────────────────────
  if (error) {
    return (
      <DashboardLayout>
        <ErrorState message={error} onRetry={() => window.location.reload()} />
      </DashboardLayout>
    )
  }

  const agg = overview?.aggregate_metrics

  return (
    <DashboardLayout>
      {/* Page Header */}
      <SectionHeader
        title="Campaign Overview"
        description="Performance metrics and creative intelligence from your analysis"
        action={
          <Link href="/new">
            <Button>
              <Plus className="w-5 h-5 mr-2" />
              New Analysis
            </Button>
          </Link>
        }
      />

      {/* Analysis selector (only show when there are completed analyses) */}
      {completedAnalyses.length > 1 && (
        <div className="mb-6 flex items-center space-x-3">
          <span className="text-sm text-text-tertiary">Showing:</span>
          <div className="relative">
            <select
              value={selectedId ?? ''}
              onChange={(e) => setSelectedId(Number(e.target.value))}
              className="appearance-none bg-surface border border-border text-text-primary text-sm rounded-lg px-3 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-primary-500"
              aria-label="Select analysis"
            >
              {completedAnalyses.map((a) => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary pointer-events-none" />
          </div>
          {selectedId && (
            <button
              onClick={() => loadOverview(selectedId)}
              className="text-text-tertiary hover:text-text-primary transition-colors"
              aria-label="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
        </div>
      )}

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {loadingOverview ? (
          [1, 2, 3, 4].map((i) => <Skeleton key={i} height="120px" />)
        ) : agg ? (
          <>
            <Metric label="Total Spend" value={fmtCurrency(agg.total_spend)} icon={DollarSign} variant="default" />
            <Metric label="Revenue" value={fmtCurrency(agg.total_revenue)} icon={TrendingUp} variant="success" />
            <Metric label="ROAS" value={fmtMultiple(agg.roas)} icon={BarChart3} variant="primary" />
            <Metric label="CTR" value={fmtPct(agg.ctr)} icon={MousePointerClick} variant="primary" />
          </>
        ) : completedAnalyses.length === 0 ? (
          // No completed analyses — placeholder metrics
          [
            { label: 'Total Spend', icon: DollarSign },
            { label: 'Revenue', icon: TrendingUp },
            { label: 'ROAS', icon: BarChart3 },
            { label: 'CTR', icon: MousePointerClick },
          ].map((m) => (
            <Metric key={m.label} label={m.label} value="—" icon={m.icon} variant="default" />
          ))
        ) : null}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        {/* Creative DNA Highlight */}
        <Card className="lg:col-span-2">
          <div className="flex items-center space-x-2 mb-4">
            <div className="w-10 h-10 bg-primary-600/20 rounded-xl flex items-center justify-center">
              <Dna className="w-5 h-5 text-primary-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Creative DNA</h3>
              <p className="text-sm text-text-tertiary">Top observed pattern</p>
            </div>
          </div>

          {loadingOverview ? (
            <div className="space-y-3">
              <Skeleton variant="text" />
              <Skeleton variant="text" width="60%" />
            </div>
          ) : insights.length > 0 ? (
            <div className="space-y-4">
              {/* Show only the top insight with strongest evidence */}
              {(() => {
                const top = insights[0]
                const direction = top.positive_median >= top.negative_median ? 'higher' : 'lower'
                const pctAbs = Math.abs(top.percent_difference).toFixed(1)
                const feature = top.feature_name.replace(/_/g, ' ')
                return (
                  <>
                    <div>
                      <p className="text-xl font-bold text-text-primary mb-2">
                        {feature.charAt(0).toUpperCase() + feature.slice(1)} associated with{' '}
                        {direction === 'higher' ? '+' : '-'}{pctAbs}% {direction} median{' '}
                        {top.metric_name.toUpperCase()}
                      </p>
                      <p className="text-sm text-text-secondary">
                        Based on comparison of {top.sample_size_positive} vs {top.sample_size_negative} creatives
                      </p>
                    </div>
                    <div className="flex items-center space-x-3">
                      <EvidenceBadge tier={top.evidence_tier} />
                      <span className="text-xs text-text-tertiary">
                        Association does not imply causation
                      </span>
                    </div>
                  </>
                )
              })()}
              <Link href="/dna">
                <Button variant="secondary" className="mt-2">
                  View Creative DNA
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>
          ) : completedAnalyses.length > 0 ? (
            <div className="text-text-tertiary text-sm py-4">
              No DNA insights generated yet for this analysis.{' '}
              <Link href="/dna" className="text-primary-400 hover:text-primary-300">
                View DNA page
              </Link>
            </div>
          ) : (
            <div className="py-4">
              <p className="text-text-secondary text-sm mb-3">
                Run an analysis to discover Creative DNA insights — visual patterns associated with
                performance in your data.
              </p>
              <Link href="/new">
                <Button variant="secondary" size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Analysis
                </Button>
              </Link>
            </div>
          )}
        </Card>

        {/* Quick Actions */}
        <Card>
          <h3 className="text-lg font-semibold text-text-primary mb-4">Quick Actions</h3>
          <div className="space-y-3">
            {[
              { href: '/new', icon: Plus, label: 'New Analysis', sub: 'Start analyzing creative', color: 'primary' },
              { href: '/library', icon: Image, label: 'Creative Library', sub: 'Browse your assets', color: 'secondary' },
              { href: '/dna', icon: Dna, label: 'Creative DNA', sub: 'View visual patterns', color: 'primary' },
              { href: '/repurpose', icon: Sparkles, label: 'Repurpose', sub: 'Transform formats', color: 'warning' },
            ].map(({ href, icon: Icon, label, sub, color }) => (
              <Link key={href} href={href} className="block">
                <button className="w-full text-left px-4 py-3 bg-surface-elevated hover:bg-surface-tertiary rounded-lg transition-all border border-border group">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 bg-${color}-600/20 rounded-lg flex items-center justify-center group-hover:bg-${color}-600/30 transition-colors`}>
                      <Icon className={`w-5 h-5 text-${color}-400`} />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-text-primary">{label}</p>
                      <p className="text-xs text-text-tertiary">{sub}</p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-text-tertiary group-hover:text-text-secondary transition-colors" />
                  </div>
                </button>
              </Link>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent Analyses */}
      <Card padding="none">
        <div className="px-6 py-4 border-b border-border">
          <h2 className="text-lg font-semibold text-text-primary">Recent Analyses</h2>
        </div>
        <div className="divide-y divide-border">
          {analyses.length === 0 ? (
            <div className="py-12">
              <EmptyState
                icon={Dna}
                title="No analyses yet"
                description="Create your first analysis to discover visual patterns associated with performance."
                action={{
                  label: 'Create Analysis',
                  onClick: () => { window.location.href = '/new' },
                }}
              />
            </div>
          ) : (
            analyses.slice(0, 10).map((analysis) => {
              const isProcessing = analysis.status === 'processing' || analysis.status === 'validating'
              const isCompleted = analysis.status === 'completed'
              const isClickable = isCompleted || isProcessing
              
              return (
                <div
                  key={analysis.id}
                  className={`px-6 py-4 flex items-center justify-between transition-colors group ${
                    isClickable ? 'hover:bg-surface-secondary cursor-pointer' : 'cursor-not-allowed opacity-60'
                  } ${analysis.id === selectedId ? 'bg-primary-600/5' : ''}`}
                  onClick={() => {
                    if (isCompleted) setSelectedId(analysis.id)
                  }}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-1">
                      <h3 className="font-medium text-text-primary truncate">
                        {analysis.name}
                      </h3>
                      <StatusBadge status={analysis.status} />
                      {isProcessing && (
                        <div className="inline-block animate-spin rounded-full h-3 w-3 border-b-2 border-primary-500"></div>
                      )}
                      {analysis.id === selectedId && (
                        <span className="text-xs text-primary-400 font-medium">Selected</span>
                      )}
                    </div>
                    {analysis.description && (
                      <p className="text-sm text-text-secondary truncate">{analysis.description}</p>
                    )}
                    <div className="flex items-center space-x-4 mt-1">
                      {analysis.current_stage && (
                        <span className="text-xs text-text-tertiary">{analysis.current_stage}</span>
                      )}
                      <span className="text-xs text-text-tertiary">
                        {new Date(analysis.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  {isCompleted ? (
                    <ArrowRight className="w-5 h-5 text-text-tertiary group-hover:text-text-primary transition-colors flex-shrink-0 ml-4" />
                  ) : isProcessing ? (
                    <RefreshCw className="w-5 h-5 text-primary-400 animate-spin flex-shrink-0 ml-4" />
                  ) : (
                    <div className="w-5 h-5 flex-shrink-0 ml-4" />
                  )}
                </div>
              )
            })
          )}
        </div>
      </Card>
    </DashboardLayout>
  )
}
