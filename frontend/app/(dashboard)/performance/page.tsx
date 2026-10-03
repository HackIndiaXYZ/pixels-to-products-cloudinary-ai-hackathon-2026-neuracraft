'use client'

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { api } from '@/lib/api'
import type { Analysis, AnalysisOverview, CreativePerformance, PlatformMetrics } from '@/types'
import { TrendingUp, BarChart3, ChevronDown, Search, ArrowUpDown } from 'lucide-react'
import { SectionHeader, Card, Metric, EmptyState, Skeleton, ErrorState } from '@/components/ui'

function fmtPct(v: number | null) { return v == null ? '—' : `${(v * 100).toFixed(2)}%` }
function fmtMult(v: number | null) { return v == null ? '—' : `${v.toFixed(2)}x` }
function fmtCur(v: number | null) { return v == null ? '—' : `$${v.toFixed(2)}` }
function fmtInt(v: number) { return v.toLocaleString() }

type SortKey = 'roas' | 'ctr' | 'cvr' | 'cpc' | 'cpm' | 'total_spend' | 'total_revenue'

export default function PerformancePage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [overview, setOverview] = useState<AnalysisOverview | null>(null)
  const [creatives, setCreatives] = useState<CreativePerformance[]>([])
  const [platforms, setPlatforms] = useState<PlatformMetrics[]>([])
  const [loadingList, setLoadingList] = useState(true)
  const [loadingData, setLoadingData] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('roas')
  const [sortAsc, setSortAsc] = useState(false)

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
    setLoadingData(true)
    Promise.all([
      api.getAnalysisOverview(selectedId),
      api.getAnalysisPerformance(selectedId),
      api.getAnalysisPlatforms(selectedId),
    ])
      .then(([ov, perf, plat]) => {
        setOverview(ov)
        setCreatives(perf.creatives)
        setPlatforms(plat.platforms)
      })
      .catch(() => setError('Failed to load performance data.'))
      .finally(() => setLoadingData(false))
  }, [selectedId])

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc((a) => !a)
    else { setSortKey(key); setSortAsc(false) }
  }

  const filtered = creatives
    .filter((c) => c.creative_id.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      const av = a[sortKey] ?? -Infinity
      const bv = b[sortKey] ?? -Infinity
      return sortAsc ? av - bv : bv - av
    })

  const SortBtn = ({ col }: { col: SortKey }) => (
    <button onClick={() => handleSort(col)} className="ml-1 text-text-tertiary hover:text-text-primary transition-colors" aria-label={`Sort by ${col}`}>
      <ArrowUpDown className={`w-3 h-3 ${sortKey === col ? 'text-primary-400' : ''}`} />
    </button>
  )

  if (loadingList) return (
    <DashboardLayout>
      <SectionHeader title="Performance" description="Campaign performance data" />
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6"><Skeleton height="80px" /><Skeleton height="80px" /><Skeleton height="80px" /><Skeleton height="80px" /><Skeleton height="80px" /></div>
      <Skeleton height="300px" />
    </DashboardLayout>
  )
  if (error) return <DashboardLayout><ErrorState message={error} onRetry={() => window.location.reload()} /></DashboardLayout>

  return (
    <DashboardLayout>
      <SectionHeader
        title="Performance Analytics"
        description="Campaign metrics and creative performance from your analysis"
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
        <EmptyState icon={BarChart3} title="No completed analyses" description="Complete an analysis to view performance metrics." action={{ label: 'New Analysis', onClick: () => { window.location.href = '/new' } }} />
      ) : loadingData ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4"><Skeleton height="80px" /><Skeleton height="80px" /><Skeleton height="80px" /><Skeleton height="80px" /><Skeleton height="80px" /></div>
          <Skeleton height="300px" />
        </div>
      ) : overview ? (
        <div className="space-y-8">
          {/* Aggregate metrics */}
          <div>
            <h2 className="text-sm font-semibold text-text-tertiary uppercase tracking-wider mb-4">Aggregate Metrics</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
              <Metric label="CTR" value={fmtPct(overview.aggregate_metrics.ctr)} icon={TrendingUp} variant="primary" />
              <Metric label="CVR" value={fmtPct(overview.aggregate_metrics.cvr)} icon={TrendingUp} variant="primary" />
              <Metric label="CPC" value={fmtCur(overview.aggregate_metrics.cpc)} icon={TrendingUp} variant="default" />
              <Metric label="ROAS" value={fmtMult(overview.aggregate_metrics.roas)} icon={BarChart3} variant="success" />
              <Metric label="CPM" value={fmtCur(overview.aggregate_metrics.cpm)} icon={TrendingUp} variant="default" />
            </div>
          </div>

          {/* Platform breakdown */}
          {platforms.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-text-tertiary uppercase tracking-wider mb-4">Platform Breakdown</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {platforms.map((p) => (
                  <Card key={p.platform} padding="sm">
                    <h3 className="font-semibold text-text-primary mb-3 capitalize">{p.platform}</h3>
                    <div className="space-y-2 text-sm">
                      {[
                        { label: 'Impressions', val: fmtInt(p.total_impressions) },
                        { label: 'Clicks', val: fmtInt(p.total_clicks) },
                        { label: 'CTR', val: fmtPct(p.ctr) },
                        { label: 'ROAS', val: fmtMult(p.roas) },
                        { label: 'Spend', val: fmtCur(p.total_spend) },
                        { label: 'Revenue', val: fmtCur(p.total_revenue) },
                      ].map(({ label, val }) => (
                        <div key={label} className="flex justify-between">
                          <span className="text-text-tertiary">{label}</span>
                          <span className="font-medium text-text-primary">{val}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Creative performance table */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-text-tertiary uppercase tracking-wider">Creative Performance</h2>
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
                <input
                  type="text"
                  placeholder="Search creative ID…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-8 pr-3 py-1.5 text-sm bg-surface border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            <Card padding="none">
              <div className="overflow-x-auto">
                <table className="w-full text-sm" role="table">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left px-4 py-3 text-text-tertiary font-medium">Creative ID</th>
                      <th className="text-right px-4 py-3 text-text-tertiary font-medium">Impressions</th>
                      <th className="text-right px-4 py-3 text-text-tertiary font-medium whitespace-nowrap">
                        CTR <SortBtn col="ctr" />
                      </th>
                      <th className="text-right px-4 py-3 text-text-tertiary font-medium whitespace-nowrap">
                        CVR <SortBtn col="cvr" />
                      </th>
                      <th className="text-right px-4 py-3 text-text-tertiary font-medium whitespace-nowrap">
                        CPC <SortBtn col="cpc" />
                      </th>
                      <th className="text-right px-4 py-3 text-text-tertiary font-medium whitespace-nowrap">
                        ROAS <SortBtn col="roas" />
                      </th>
                      <th className="text-right px-4 py-3 text-text-tertiary font-medium whitespace-nowrap">
                        CPM <SortBtn col="cpm" />
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {filtered.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="text-center py-8 text-text-tertiary">
                          {search ? 'No creatives match your search.' : 'No performance data available.'}
                        </td>
                      </tr>
                    ) : (
                      filtered.map((c) => (
                        <tr key={c.creative_id} className="hover:bg-surface-secondary transition-colors">
                          <td className="px-4 py-3 font-mono text-text-primary text-xs">{c.creative_id}</td>
                          <td className="px-4 py-3 text-right text-text-secondary">{fmtInt(c.total_impressions)}</td>
                          <td className="px-4 py-3 text-right text-text-secondary">{fmtPct(c.ctr)}</td>
                          <td className="px-4 py-3 text-right text-text-secondary">{fmtPct(c.cvr)}</td>
                          <td className="px-4 py-3 text-right text-text-secondary">{fmtCur(c.cpc)}</td>
                          <td className={`px-4 py-3 text-right font-medium ${(c.roas ?? 0) >= 2 ? 'text-success-400' : 'text-text-primary'}`}>
                            {fmtMult(c.roas)}
                          </td>
                          <td className="px-4 py-3 text-right text-text-secondary">{fmtCur(c.cpm)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        </div>
      ) : null}
    </DashboardLayout>
  )
}
