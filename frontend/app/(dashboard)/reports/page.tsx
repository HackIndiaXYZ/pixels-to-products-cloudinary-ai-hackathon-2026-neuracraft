'use client'

import { useEffect, useState, useRef } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { api } from '@/lib/api'
import type { Analysis, AnalysisOverview, CreativeDNAInsight } from '@/types'
import { FileText, Printer, ChevronDown, Calendar, Shield, Dna, TrendingUp, BarChart3 } from 'lucide-react'
import { SectionHeader, Card, Button, EmptyState, Skeleton, ErrorState } from '@/components/ui'
import EvidenceBadge from '@/components/EvidenceBadge'

function fmtCur(v: number | null) { return v == null ? '—' : `$${v.toLocaleString('en-US', { maximumFractionDigits: 2 })}` }
function fmtPct(v: number | null) { return v == null ? '—' : `${(v * 100).toFixed(2)}%` }
function fmtMult(v: number | null) { return v == null ? '—' : `${v.toFixed(2)}x` }

export default function ReportsPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [overview, setOverview] = useState<AnalysisOverview | null>(null)
  const [insights, setInsights] = useState<CreativeDNAInsight[]>([])
  const [loadingList, setLoadingList] = useState(true)
  const [loadingReport, setLoadingReport] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const reportRef = useRef<HTMLDivElement>(null)

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
    setLoadingReport(true)
    Promise.all([
      api.getAnalysisOverview(selectedId),
      api.getCreativeDNA(selectedId),
    ])
      .then(([ov, dna]) => {
        setOverview(ov)
        // Only include non-insufficient insights in the report
        setInsights(dna.filter((i) => i.evidence_tier !== 'insufficient_evidence'))
      })
      .catch(() => setError('Failed to load report data.'))
      .finally(() => setLoadingReport(false))
  }, [selectedId])

  const handlePrint = () => {
    window.print()
  }

  const selectedAnalysis = analyses.find((a) => a.id === selectedId)

  if (loadingList) return (
    <DashboardLayout>
      <SectionHeader title="Reports" description="Generate and export analysis reports" />
      <Skeleton height="500px" />
    </DashboardLayout>
  )

  if (error) return <DashboardLayout><ErrorState message={error} onRetry={() => window.location.reload()} /></DashboardLayout>

  return (
    <DashboardLayout>
      <SectionHeader
        title="Reports"
        description="Generate printable analysis reports from your data"
        action={
          overview && (
            <Button onClick={handlePrint} variant="secondary">
              <Printer className="w-4 h-4 mr-2" />
              Print / Save PDF
            </Button>
          )
        }
      />

      {analyses.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No completed analyses"
          description="Complete an analysis to generate a report."
          action={{ label: 'New Analysis', onClick: () => { window.location.href = '/new' } }}
        />
      ) : (
        <>
          {/* Controls */}
          <div className="flex items-center space-x-3 mb-6 no-print">
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

          {loadingReport ? (
            <Skeleton height="500px" />
          ) : overview ? (
            // ── Printable report ───────────────────────────────────────────────
            <div ref={reportRef} className="space-y-6">
              {/* Report header */}
              <Card>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <FileText className="w-5 h-5 text-primary-400" />
                      <h2 className="text-xl font-bold text-text-primary">CreativePulse Analysis Report</h2>
                    </div>
                    <h3 className="text-lg font-semibold text-text-primary">{overview.analysis_name}</h3>
                    <div className="flex items-center space-x-2 mt-1 text-sm text-text-secondary">
                      <Calendar className="w-4 h-4" />
                      <span>Generated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
                    </div>
                    {selectedAnalysis?.description && (
                      <p className="text-sm text-text-secondary mt-2">{selectedAnalysis.description}</p>
                    )}
                  </div>
                </div>
              </Card>

              {/* Summary numbers */}
              <Card>
                <h3 className="text-base font-semibold text-text-primary mb-4 flex items-center space-x-2">
                  <BarChart3 className="w-4 h-4 text-primary-400" />
                  <span>Dataset Summary</span>
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div className="bg-surface rounded-lg px-4 py-3">
                    <p className="text-text-tertiary text-xs mb-1">Total Creatives</p>
                    <p className="text-2xl font-bold text-text-primary metric-number">{overview.total_creatives}</p>
                  </div>
                  <div className="bg-surface rounded-lg px-4 py-3">
                    <p className="text-text-tertiary text-xs mb-1">Performance Records</p>
                    <p className="text-2xl font-bold text-text-primary metric-number">{overview.total_records}</p>
                  </div>
                  <div className="bg-surface rounded-lg px-4 py-3">
                    <p className="text-text-tertiary text-xs mb-1">Total Spend</p>
                    <p className="text-2xl font-bold text-text-primary metric-number">{fmtCur(overview.aggregate_metrics.total_spend)}</p>
                  </div>
                  <div className="bg-surface rounded-lg px-4 py-3">
                    <p className="text-text-tertiary text-xs mb-1">Total Revenue</p>
                    <p className="text-2xl font-bold text-text-primary metric-number">{fmtCur(overview.aggregate_metrics.total_revenue)}</p>
                  </div>
                </div>
              </Card>

              {/* Aggregate performance metrics */}
              <Card>
                <h3 className="text-base font-semibold text-text-primary mb-4 flex items-center space-x-2">
                  <TrendingUp className="w-4 h-4 text-success-400" />
                  <span>Aggregate Performance Metrics</span>
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
                  {[
                    { label: 'ROAS', value: fmtMult(overview.aggregate_metrics.roas) },
                    { label: 'CTR', value: fmtPct(overview.aggregate_metrics.ctr) },
                    { label: 'CVR', value: fmtPct(overview.aggregate_metrics.cvr) },
                    { label: 'CPC', value: fmtCur(overview.aggregate_metrics.cpc) },
                    { label: 'CPM', value: fmtCur(overview.aggregate_metrics.cpm) },
                  ].map(({ label, value }) => (
                    <div key={label} className="bg-surface rounded-lg px-4 py-3">
                      <p className="text-text-tertiary text-xs mb-1">{label}</p>
                      <p className="text-xl font-bold text-text-primary metric-number">{value}</p>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Creative DNA insights */}
              <Card>
                <h3 className="text-base font-semibold text-text-primary mb-4 flex items-center space-x-2">
                  <Dna className="w-4 h-4 text-primary-400" />
                  <span>Creative DNA Findings</span>
                </h3>

                {insights.length === 0 ? (
                  <p className="text-sm text-text-tertiary">No DNA insights with sufficient evidence in this analysis.</p>
                ) : (
                  <div className="space-y-4">
                    {insights.slice(0, 10).map((insight) => (
                      <div key={insight.id} className="bg-surface rounded-lg p-4 border border-border">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <p className="font-medium text-text-primary capitalize">{insight.feature_name.replace(/_/g, ' ')}</p>
                            <p className="text-xs text-text-tertiary">{insight.metric_name.toUpperCase()}</p>
                          </div>
                          <EvidenceBadge tier={insight.evidence_tier} />
                        </div>
                        <p className="text-sm text-text-secondary mb-2">{insight.explanation}</p>
                        <div className="grid grid-cols-4 gap-2 text-xs text-text-tertiary">
                          <span>With: {insight.positive_median.toFixed(4)} (n={insight.sample_size_positive})</span>
                          <span>Without: {insight.negative_median.toFixed(4)} (n={insight.sample_size_negative})</span>
                          <span>p={insight.p_value != null ? insight.p_value.toFixed(4) : '—'}</span>
                          <span>r={insight.effect_size != null ? insight.effect_size.toFixed(3) : '—'}</span>
                        </div>
                      </div>
                    ))}
                    {insights.length > 10 && (
                      <p className="text-xs text-text-tertiary">Showing 10 of {insights.length} insights. View the Creative DNA page for the full list.</p>
                    )}
                  </div>
                )}
              </Card>

              {/* Methodology and disclaimer */}
              <Card>
                <h3 className="text-base font-semibold text-text-primary mb-3 flex items-center space-x-2">
                  <Shield className="w-4 h-4 text-primary-400" />
                  <span>Methodology &amp; Limitations</span>
                </h3>
                <div className="text-sm text-text-secondary space-y-3">
                  <p>
                    <strong className="text-text-primary">Statistical method:</strong> Mann–Whitney U test with rank-biserial correlation effect size. Minimum 5 creatives per group required. Evidence tiers: Strong (p&lt;0.05, |r|≥0.5, |Δ|≥10%), Moderate, Weak, No Clear Evidence.
                  </p>
                  <p>
                    <strong className="text-text-primary">Visual features:</strong> Brightness, contrast, edge density, aspect ratio, orientation, and dominant color are computed from pixel data. Human presence is marked as Unavailable unless an object detector is explicitly configured.
                  </p>
                  <p className="font-medium text-warning-400">
                    ⚠️ Association does not imply causation. Creative DNA identifies correlational patterns in this dataset only. Results may not generalise to other campaigns, time periods, or audiences. Do not use these findings as sole justification for creative decisions.
                  </p>
                </div>
              </Card>
            </div>
          ) : null}
        </>
      )}

      {/* Print styles */}
      <style jsx global>{`
        @media print {
          .no-print { display: none !important; }
          body { background: white !important; color: black !important; }
        }
      `}</style>
    </DashboardLayout>
  )
}
