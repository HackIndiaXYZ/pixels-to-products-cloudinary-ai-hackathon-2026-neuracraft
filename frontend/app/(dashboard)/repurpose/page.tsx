'use client'

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { api } from '@/lib/api'
import { getErrorMessage } from '@/lib/apiError'
import type { Analysis, AssetWithMetrics, GeneratedAsset, RepurposeFormat } from '@/types'
import { Wand2, Image as ImageIcon, ExternalLink, AlertTriangle, ChevronDown, Cloud } from 'lucide-react'
import { SectionHeader, Card, Button, EmptyState, Skeleton, ErrorState } from '@/components/ui'

const FORMATS: { id: RepurposeFormat; label: string; ratio: string; desc: string }[] = [
  { id: '4:5', label: 'Instagram Portrait', ratio: '4:5', desc: '1080 × 1350 px' },
  { id: '9:16', label: 'Story / Reel', ratio: '9:16', desc: '1080 × 1920 px' },
  { id: '16:9', label: 'Landscape / YouTube', ratio: '16:9', desc: '1920 × 1080 px' },
  { id: '1:1', label: 'Square Feed', ratio: '1:1', desc: '1080 × 1080 px' },
]

export default function RepurposePage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([])
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<number | null>(null)
  const [assets, setAssets] = useState<AssetWithMetrics[]>([])
  const [selectedAssetId, setSelectedAssetId] = useState<number | null>(null)
  const [selectedFormats, setSelectedFormats] = useState<RepurposeFormat[]>([])
  const [generatedAssets, setGeneratedAssets] = useState<GeneratedAsset[]>([])
  const [cloudinaryAvailable, setCloudinaryAvailable] = useState<boolean | null>(null)
  const [generating, setGenerating] = useState(false)
  const [loadingList, setLoadingList] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [genError, setGenError] = useState<string | null>(null)

  // Check Cloudinary status on mount
  useEffect(() => {
    api.getCloudinaryStatus()
      .then((s) => setCloudinaryAvailable(s.configured))
      .catch(() => setCloudinaryAvailable(false))
  }, [])

  // Load analyses
  useEffect(() => {
    api.getAnalyses()
      .then((data) => {
        const completed = data.filter((a) => a.status === 'completed')
        setAnalyses(completed)
        if (completed.length > 0) setSelectedAnalysisId(completed[0].id)
      })
      .catch(() => setError('Failed to load analyses.'))
      .finally(() => setLoadingList(false))
  }, [])

  // Load assets when analysis changes
  useEffect(() => {
    if (selectedAnalysisId == null) return
    api.getAnalysisAssets(selectedAnalysisId)
      .then((res) => {
        const cloudinaryAssets = res.assets.filter((a) => a.source === 'cloudinary' && a.cloudinary_url)
        setAssets(cloudinaryAssets)
        setSelectedAssetId(cloudinaryAssets[0]?.id ?? null)
      })
      .catch(() => {})

    // Load existing generated assets
    api.getGeneratedAssets(selectedAnalysisId)
      .then(setGeneratedAssets)
      .catch(() => {})
  }, [selectedAnalysisId])

  const toggleFormat = (fmt: RepurposeFormat) => {
    setSelectedFormats((prev) =>
      prev.includes(fmt) ? prev.filter((f) => f !== fmt) : [...prev, fmt]
    )
  }

  const handleGenerate = async () => {
    if (!selectedAssetId || selectedFormats.length === 0 || !selectedAnalysisId) return
    setGenerating(true)
    setGenError(null)

    const results: GeneratedAsset[] = []
    let lastError = ''

    for (const fmt of selectedFormats) {
      try {
        const result = await api.repurposeAsset(selectedAnalysisId, {
          source_asset_id: selectedAssetId,
          format: fmt,
        })
        results.push(result)
      } catch (err) {
        lastError = getErrorMessage(err) || `Failed to generate ${fmt}`
      }
    }

    if (results.length > 0) {
      // Refresh generated assets list
      const updated = await api.getGeneratedAssets(selectedAnalysisId)
      setGeneratedAssets(updated)
    }
    if (lastError) setGenError(lastError)
    setGenerating(false)
  }

  const selectedAsset = assets.find((a) => a.id === selectedAssetId)

  if (loadingList) return (
    <DashboardLayout>
      <SectionHeader title="Repurpose" description="Transform creatives for different platforms" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6"><Skeleton height="400px" /><Skeleton height="400px" /></div>
    </DashboardLayout>
  )

  if (error) return <DashboardLayout><ErrorState message={error} onRetry={() => window.location.reload()} /></DashboardLayout>

  return (
    <DashboardLayout>
      <SectionHeader
        title="Repurpose"
        description="Transform high-performing creatives into campaign-ready formats using Cloudinary"
      />

      {/* Cloudinary status banner */}
      {cloudinaryAvailable === false && (
        <div className="mb-6 bg-warning-600/10 border border-warning-600/30 rounded-lg px-4 py-3 flex items-start space-x-3">
          <Cloud className="w-5 h-5 text-warning-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-warning-400">Cloudinary not configured</p>
            <p className="text-xs text-text-secondary mt-1">
              Repurposing requires Cloudinary. Set <code className="text-warning-400">CLOUDINARY_CLOUD_NAME</code>, <code className="text-warning-400">CLOUDINARY_API_KEY</code>, and <code className="text-warning-400">CLOUDINARY_API_SECRET</code> in your backend environment.
            </p>
          </div>
        </div>
      )}

      {analyses.length === 0 ? (
        <EmptyState
          icon={Wand2}
          title="No completed analyses"
          description="Complete an analysis with Cloudinary-uploaded assets to enable repurposing."
          action={{ label: 'New Analysis', onClick: () => { window.location.href = '/new' } }}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Configuration */}
          <div className="space-y-5">
            <Card>
              <h2 className="text-base font-semibold text-text-primary mb-4">Source Asset</h2>

              {/* Analysis picker */}
              <div className="mb-4">
                <label className="block text-xs font-medium text-text-tertiary mb-1.5">Analysis</label>
                <div className="relative">
                  <select
                    value={selectedAnalysisId ?? ''}
                    onChange={(e) => setSelectedAnalysisId(Number(e.target.value))}
                    className="w-full appearance-none bg-surface border border-border text-text-primary text-sm rounded-lg px-3 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    {analyses.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                  </select>
                  <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary pointer-events-none" />
                </div>
              </div>

              {/* Asset picker */}
              <div className="mb-4">
                <label className="block text-xs font-medium text-text-tertiary mb-1.5">Creative asset</label>
                {assets.length === 0 ? (
                  <div className="bg-surface border border-border rounded-lg px-3 py-4 text-center">
                    <p className="text-sm text-text-tertiary">No Cloudinary assets in this analysis.</p>
                    <p className="text-xs text-text-muted mt-1">Repurposing requires assets uploaded via Cloudinary.</p>
                  </div>
                ) : (
                  <div className="relative">
                    <select
                      value={selectedAssetId ?? ''}
                      onChange={(e) => setSelectedAssetId(Number(e.target.value))}
                      className="w-full appearance-none bg-surface border border-border text-text-primary text-sm rounded-lg px-3 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      {assets.map((a) => <option key={a.id} value={a.id}>{a.creative_id}</option>)}
                    </select>
                    <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary pointer-events-none" />
                  </div>
                )}
              </div>

              {/* Preview */}
              {selectedAsset?.cloudinary_url && (
                <div className="mb-4 rounded-lg overflow-hidden bg-surface aspect-video">
                  <img
                    src={selectedAsset.cloudinary_url}
                    alt={selectedAsset.creative_id}
                    className="w-full h-full object-contain"
                  />
                </div>
              )}

              {/* Format selection */}
              <div>
                <p className="text-xs font-medium text-text-tertiary mb-2">Target formats</p>
                <div className="space-y-2">
                  {FORMATS.map((fmt) => (
                    <label
                      key={fmt.id}
                      className={`flex items-center p-3 border rounded-lg cursor-pointer transition-all ${
                        selectedFormats.includes(fmt.id)
                          ? 'border-primary-500 bg-primary-600/10'
                          : 'border-border hover:border-border-secondary'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedFormats.includes(fmt.id)}
                        onChange={() => toggleFormat(fmt.id)}
                        className="w-4 h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500 bg-surface border-border"
                      />
                      <div className="ml-3 flex-1">
                        <span className="text-sm font-medium text-text-primary">{fmt.label}</span>
                        <span className="text-xs text-text-tertiary ml-2">{fmt.desc}</span>
                      </div>
                      <span className="text-xs font-mono text-text-tertiary">{fmt.ratio}</span>
                    </label>
                  ))}
                </div>
              </div>

              {genError && (
                <div className="mt-3 flex items-start space-x-2 text-xs text-danger-400 bg-danger-600/10 rounded-lg px-3 py-2">
                  <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  <span>{genError}</span>
                </div>
              )}

              <Button
                className="w-full mt-4"
                onClick={handleGenerate}
                disabled={!selectedAssetId || selectedFormats.length === 0 || generating || !cloudinaryAvailable}
                loading={generating}
              >
                <Wand2 className="w-4 h-4 mr-2" />
                {generating ? 'Generating…' : 'Generate Variants'}
              </Button>
            </Card>
          </div>

          {/* Results */}
          <Card>
            <h2 className="text-base font-semibold text-text-primary mb-4">Generated Variants</h2>
            {generatedAssets.length === 0 ? (
              <div className="text-center py-12">
                <Wand2 className="w-12 h-12 text-text-muted mx-auto mb-3" />
                <p className="text-sm text-text-tertiary">Select an asset and formats, then click Generate.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {generatedAssets.map((ga) => {
                  const fmt = FORMATS.find((f) => f.id === ga.format)
                  return (
                    <div key={ga.id} className="border border-border rounded-lg overflow-hidden">
                      <div className="px-4 py-2.5 bg-surface border-b border-border flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-text-primary">{fmt?.label ?? ga.format}</p>
                          <p className="text-xs text-text-tertiary">{fmt?.ratio} • {fmt?.desc}</p>
                        </div>
                        <a
                          href={ga.generated_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center space-x-1 text-xs text-primary-400 hover:text-primary-300 transition-colors"
                          aria-label="Open generated asset"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span>Open</span>
                        </a>
                      </div>
                      <div className="bg-surface p-3">
                        <img
                          src={ga.generated_url}
                          alt={`${ga.format} variant`}
                          className="w-full rounded max-h-48 object-contain mx-auto"
                          loading="lazy"
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </Card>
        </div>
      )}
    </DashboardLayout>
  )
}
