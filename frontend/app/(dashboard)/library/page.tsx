'use client'

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { api } from '@/lib/api'
import type { Analysis, AssetWithMetrics } from '@/types'
import { Image as ImageIcon, Search, ChevronDown, ExternalLink } from 'lucide-react'
import { SectionHeader, Card, EmptyState, Skeleton, StatusBadge, ErrorState, Badge } from '@/components/ui'

function fmtPct(v: number | null) { return v == null ? '—' : `${(v * 100).toFixed(2)}%` }
function fmtMult(v: number | null) { return v == null ? '—' : `${v.toFixed(2)}x` }
function fmtCur(v: number | null) { return v == null ? '—' : `$${v.toFixed(2)}` }

export default function LibraryPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [assets, setAssets] = useState<AssetWithMetrics[]>([])
  const [loadingList, setLoadingList] = useState(true)
  const [loadingAssets, setLoadingAssets] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')

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
    setLoadingAssets(true)
    api.getAnalysisAssets(selectedId)
      .then((res) => setAssets(res.assets))
      .catch(() => setError('Failed to load creative assets.'))
      .finally(() => setLoadingAssets(false))
  }, [selectedId])

  const filtered = assets.filter((a) =>
    a.creative_id.toLowerCase().includes(search.toLowerCase())
  )

  if (loadingList) return (
    <DashboardLayout>
      <SectionHeader title="Creative Library" description="Browse your creative assets" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3, 4, 5, 6].map((i) => <Skeleton key={i} height="280px" />)}
      </div>
    </DashboardLayout>
  )

  if (error) return <DashboardLayout><ErrorState message={error} onRetry={() => window.location.reload()} /></DashboardLayout>

  return (
    <DashboardLayout>
      <SectionHeader
        title="Creative Library"
        description="Browse your creative assets and their performance metrics"
      />

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        {analyses.length > 0 && (
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
        )}
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
          <input
            type="text"
            placeholder="Search creative ID…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-2 text-sm bg-surface border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      {analyses.length === 0 ? (
        <EmptyState
          icon={ImageIcon}
          title="No completed analyses"
          description="Complete an analysis to see creative assets here."
          action={{ label: 'New Analysis', onClick: () => { window.location.href = '/new' } }}
        />
      ) : loadingAssets ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => <Skeleton key={i} height="280px" />)}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={ImageIcon}
          title={search ? 'No results' : 'No assets in this analysis'}
          description={search ? 'Try a different search term.' : 'Register creative assets by running an analysis with performance data.'}
        />
      ) : (
        <>
          <p className="text-sm text-text-tertiary mb-4">
            Showing {filtered.length} of {assets.length} creative{assets.length !== 1 ? 's' : ''}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((asset) => (
              <Card key={asset.id} hover padding="none" className="overflow-hidden">
                {/* Image */}
                <div className="aspect-video bg-gradient-to-br from-surface to-surface-elevated flex items-center justify-center relative">
                  {asset.secure_url || asset.cloudinary_url ? (
                    <img
                      src={asset.secure_url || asset.cloudinary_url}
                      alt={asset.creative_id}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  ) : (
                    <div className="flex flex-col items-center space-y-2">
                      <ImageIcon className="w-12 h-12 text-text-muted" />
                      <span className="text-xs text-text-muted">{asset.source === 'local_demo' ? 'Demo Asset' : 'No Image'}</span>
                    </div>
                  )}
                  {/* Source badge */}
                  <div className="absolute top-2 right-2">
                    <Badge
                      variant={asset.source === 'cloudinary' ? 'primary' : 'default'}
                      size="sm"
                    >
                      {asset.source === 'cloudinary' ? 'Cloudinary' : 'Demo'}
                    </Badge>
                  </div>
                </div>

                {/* Info */}
                <div className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-text-primary font-mono text-sm">{asset.creative_id}</h3>
                      <p className="text-xs text-text-tertiary mt-0.5">{asset.filename}</p>
                    </div>
                    {asset.secure_url && (
                      <a
                        href={asset.secure_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-text-tertiary hover:text-primary-400 transition-colors"
                        aria-label="Open original"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                  </div>

                  {/* Metrics grid */}
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { label: 'ROAS', value: fmtMult(asset.metrics?.roas) },
                      { label: 'CTR', value: fmtPct(asset.metrics?.ctr) },
                      { label: 'CVR', value: fmtPct(asset.metrics?.cvr) },
                      { label: 'CPC', value: fmtCur(asset.metrics?.cpc) },
                    ].map(({ label, value }) => (
                      <div key={label} className="bg-surface rounded-lg px-2 py-1.5">
                        <p className="text-xs text-text-tertiary">{label}</p>
                        <p className="text-sm font-medium text-text-primary">{value}</p>
                      </div>
                    ))}
                  </div>

                  {/* Dimensions */}
                  {asset.width && asset.height && (
                    <p className="text-xs text-text-muted mt-2">{asset.width} × {asset.height}px • {asset.format?.toUpperCase()}</p>
                  )}
                </div>
              </Card>
            ))}
          </div>
        </>
      )}
    </DashboardLayout>
  )
}
