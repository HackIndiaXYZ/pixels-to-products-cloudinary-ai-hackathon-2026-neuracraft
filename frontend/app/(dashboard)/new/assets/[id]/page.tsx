'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter, useParams } from 'next/navigation'
import DashboardLayout from '@/components/DashboardLayout'
import CloudinaryUploader from '@/components/CloudinaryUploader'
import { api } from '@/lib/api'
import { getErrorMessage } from '@/lib/apiError'
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Image as ImageIcon,
  Sparkles,
  Loader2,
  Info,
} from 'lucide-react'
import { Button, Card } from '@/components/ui'

interface AssetRecord {
  id: number
  creative_id: string
  filename: string
  secure_url?: string | null
  cloudinary_url?: string | null
  source: string
  created_at: string
}

interface Coverage {
  csv_creative_ids: string[]
  registered_real_ids: string[]
  missing_ids: string[]
  total_csv: number
  total_real: number
  total_missing: number
  coverage_complete: boolean
}

export default function AssetUploadPage() {
  const router = useRouter()
  const params = useParams()
  const analysisId = params.id ? parseInt(params.id as string) : null

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [cloudinaryConfigured, setCloudinaryConfigured] = useState(false)

  const [creativeIds, setCreativeIds] = useState<string[]>([])
  const [assets, setAssets] = useState<Record<string, AssetRecord>>({})
  const [uploadErrors, setUploadErrors] = useState<Record<string, string>>({})
  const [coverage, setCoverage] = useState<Coverage | null>(null)

  // Run state
  const [isRunning, setIsRunning] = useState(false)
  const [runError, setRunError] = useState<string | null>(null)
  const [currentStage, setCurrentStage] = useState<string>('')
  const [runComplete, setRunComplete] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!analysisId) return
    loadData()
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [analysisId])

  const loadData = async () => {
    if (!analysisId) return
    setLoading(true)
    setError(null)
    try {
      const [cloudinaryStatus, performanceData, existingAssets, cov] = await Promise.all([
        api.getCloudinaryStatus(),
        api.getAnalysisPerformance(analysisId),
        api.listAssets(analysisId),
        api.getAssetCoverage(analysisId),
      ])

      setCloudinaryConfigured(cloudinaryStatus.configured)

      const uniqueIds = Array.from(
        new Set(performanceData.records.map((r: any) => r.creative_id))
      ).sort() as string[]
      setCreativeIds(uniqueIds)

      const assetMap: Record<string, AssetRecord> = {}
      existingAssets.forEach((asset: any) => {
        assetMap[asset.creative_id] = asset
      })
      setAssets(assetMap)
      setCoverage(cov)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const refreshCoverage = useCallback(async () => {
    if (!analysisId) return
    try {
      const cov = await api.getAssetCoverage(analysisId)
      setCoverage(cov)
    } catch { /* silent refresh failure */ }
  }, [analysisId])

  const handleUploadSuccess = (creativeId: string, assetData: any) => {
    setAssets(prev => ({ ...prev, [creativeId]: assetData }))
    setUploadErrors(prev => {
      const next = { ...prev }
      delete next[creativeId]
      return next
    })
    // Refresh coverage after each successful upload
    refreshCoverage()
  }

  const handleUploadError = (creativeId: string, errorMsg: string) => {
    setUploadErrors(prev => ({ ...prev, [creativeId]: errorMsg }))
  }

  const getUploadStats = () => {
    const total = creativeIds.length
    const uploaded = Object.keys(assets).filter(id => assets[id]?.source === 'cloudinary').length
    const placeholders = Object.keys(assets).filter(id => assets[id]?.source === 'local_demo').length
    return { total, uploaded, placeholders, remaining: total - uploaded - placeholders }
  }

  const startPolling = useCallback((id: number) => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const s = await api.getAnalysisStatus(id)
        setCurrentStage(s.current_stage || 'Processing...')
        if (s.status === 'completed') {
          clearInterval(pollRef.current!)
          setRunComplete(true)
          setCurrentStage('Analysis completed!')
          setTimeout(() => router.push('/dashboard'), 1500)
        } else if (s.status === 'failed') {
          clearInterval(pollRef.current!)
          setIsRunning(false)
          setRunError(s.error_message || 'Analysis failed. Please check the logs.')
        }
      } catch {
        // transient polling error — keep trying
      }
    }, 2000)
  }, [router])

  const handleContinue = async () => {
    if (!analysisId) return
    setRunError(null)
    setIsRunning(true)
    setCurrentStage('Starting analysis...')
    try {
      await api.runAnalysis(analysisId)
      startPolling(analysisId)
    } catch (err) {
      setIsRunning(false)
      setRunError(getErrorMessage(err))
    }
  }

  const stats = getUploadStats()
  const missingIds = coverage?.missing_ids ?? []
  const hasMissingAssets = missingIds.length > 0 && stats.uploaded > 0

  if (!analysisId) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-danger-400">Invalid analysis ID</p>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.back()}
            className="flex items-center space-x-2 text-text-secondary hover:text-text-primary mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
          <h1 className="text-3xl font-bold text-text-primary mb-2">Upload Creative Assets</h1>
          <p className="text-text-secondary">
            Upload real creative images for visual feature extraction and Creative DNA analysis.
          </p>
        </div>

        {error && (
          <Card className="mb-6 bg-danger-600/10 border-danger-600/30">
            <div className="flex items-start space-x-3">
              <XCircle className="w-5 h-5 text-danger-400 flex-shrink-0 mt-0.5" />
              <p className="text-danger-400 text-sm">{error}</p>
            </div>
          </Card>
        )}

        {/* Cloudinary status */}
        <Card className={`mb-6 ${cloudinaryConfigured ? 'border-success-500/30 bg-success-500/5' : 'border-warning-600/30 bg-warning-600/5'}`}>
          <div className="flex items-start space-x-3">
            <Sparkles className={`w-5 h-5 flex-shrink-0 mt-0.5 ${cloudinaryConfigured ? 'text-success-400' : 'text-warning-400'}`} />
            <div>
              <p className={`font-medium ${cloudinaryConfigured ? 'text-success-400' : 'text-warning-400'}`}>
                {cloudinaryConfigured ? 'Cloudinary Ready' : 'Cloudinary Not Configured'}
              </p>
              <p className="text-text-secondary text-sm mt-1">
                {cloudinaryConfigured
                  ? 'Images upload directly to Cloudinary and are registered in the database automatically.'
                  : 'Configure Cloudinary environment variables to enable image uploads.'}
              </p>
            </div>
          </div>
        </Card>

        {/* Coverage summary */}
        {!loading && coverage && (
          <Card className="mb-6">
            <div className="grid grid-cols-4 gap-4 text-center mb-4">
              <div>
                <div className="text-2xl font-bold text-text-primary">{coverage.total_csv}</div>
                <div className="text-xs text-text-tertiary">CSV Creatives</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-success-400">{coverage.total_real}</div>
                <div className="text-xs text-text-tertiary">Real Assets</div>
              </div>
              <div>
                <div className={`text-2xl font-bold ${coverage.total_missing > 0 ? 'text-warning-400' : 'text-text-tertiary'}`}>
                  {coverage.total_missing}
                </div>
                <div className="text-xs text-text-tertiary">Missing</div>
              </div>
              <div>
                <div className={`text-2xl font-bold ${coverage.coverage_complete ? 'text-success-400' : 'text-warning-400'}`}>
                  {coverage.coverage_complete ? '100%' : `${Math.round((coverage.total_real / Math.max(coverage.total_csv, 1)) * 100)}%`}
                </div>
                <div className="text-xs text-text-tertiary">Coverage</div>
              </div>
            </div>

            {/* Missing IDs warning */}
            {hasMissingAssets && (
              <div className="bg-warning-600/10 border border-warning-600/30 rounded-lg p-3">
                <div className="flex items-start space-x-2">
                  <AlertTriangle className="w-4 h-4 text-warning-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-warning-400 text-sm font-medium">
                      {coverage.total_real} of {coverage.total_csv} creatives registered.{' '}
                      {coverage.total_missing} missing:
                    </p>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {missingIds.map(id => (
                        <span key={id} className="text-xs font-mono bg-warning-600/20 text-warning-300 px-2 py-0.5 rounded">
                          {id}
                        </span>
                      ))}
                    </div>
                    <p className="text-xs text-text-secondary mt-2">
                      Visual analysis and Creative DNA will only cover the {coverage.total_real} uploaded creative(s).
                      You can still run a performance-only analysis.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </Card>
        )}

        {/* Per-creative uploaders */}
        {loading ? (
          <div className="text-center py-12">
            <Loader2 className="w-8 h-8 text-primary-500 animate-spin mx-auto" />
            <p className="text-text-tertiary mt-4">Loading creative IDs...</p>
          </div>
        ) : creativeIds.length === 0 ? (
          <Card className="text-center py-12">
            <ImageIcon className="w-12 h-12 text-text-tertiary mx-auto mb-4" />
            <p className="text-text-primary font-medium mb-2">No Creative IDs Found</p>
            <p className="text-text-secondary text-sm">Upload performance data first.</p>
          </Card>
        ) : (
          <div className="space-y-4">
            {creativeIds.map(creativeId => {
              const asset = assets[creativeId]
              const isUploaded = asset?.source === 'cloudinary'
              const isPlaceholder = asset?.source === 'local_demo'
              const uploadError = uploadErrors[creativeId]

              return (
                <Card key={creativeId}>
                  <div className="flex items-start space-x-4">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-3">
                        <h3 className="text-lg font-semibold text-text-primary font-mono">{creativeId}</h3>
                        {isUploaded && (
                          <span className="px-2 py-0.5 bg-success-500/20 text-success-400 text-xs font-medium rounded-full flex items-center space-x-1">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Uploaded</span>
                          </span>
                        )}
                        {isPlaceholder && (
                          <span className="px-2 py-0.5 bg-text-tertiary/20 text-text-tertiary text-xs font-medium rounded-full">
                            Placeholder
                          </span>
                        )}
                      </div>

                      {isUploaded && (asset.secure_url || asset.cloudinary_url) ? (
                        <div className="space-y-2">
                          <div className="aspect-video bg-surface rounded-lg overflow-hidden border border-border">
                            <img
                              src={asset.secure_url || asset.cloudinary_url || ''}
                              alt={creativeId}
                              className="w-full h-full object-contain"
                            />
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-text-tertiary">{asset.filename}</span>
                            {asset.secure_url && (
                              <a href={asset.secure_url} target="_blank" rel="noopener noreferrer"
                                className="text-primary-400 hover:text-primary-300">
                                View Full Size
                              </a>
                            )}
                          </div>
                        </div>
                      ) : isPlaceholder ? (
                        <div className="bg-surface-elevated border border-border rounded-lg p-4 text-center">
                          <p className="text-text-tertiary text-sm">
                            Placeholder only — upload a real image for visual analysis
                          </p>
                        </div>
                      ) : cloudinaryConfigured ? (
                        <CloudinaryUploader
                          analysisId={analysisId}
                          creativeId={creativeId}
                          onSuccess={(data) => handleUploadSuccess(creativeId, data)}
                          onError={(err) => handleUploadError(creativeId, err)}
                          disabled={!cloudinaryConfigured}
                        />
                      ) : (
                        <div className="bg-warning-600/10 border border-warning-600/30 rounded-lg p-4">
                          <div className="flex items-start space-x-2">
                            <AlertTriangle className="w-4 h-4 text-warning-400 flex-shrink-0 mt-0.5" />
                            <p className="text-warning-400 text-sm">Configure Cloudinary to enable uploads</p>
                          </div>
                        </div>
                      )}

                      {uploadError && (
                        <div className="mt-2 bg-danger-600/10 border border-danger-600/30 rounded-lg p-3">
                          <div className="flex items-start space-x-2">
                            <XCircle className="w-4 h-4 text-danger-400 flex-shrink-0 mt-0.5" />
                            <p className="text-danger-400 text-sm">{uploadError}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              )
            })}
          </div>
        )}

        {/* Continue / Run button area */}
        {!loading && creativeIds.length > 0 && (
          <Card className="mt-6">
            {isRunning || runComplete ? (
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  {runComplete
                    ? <CheckCircle2 className="w-5 h-5 text-success-400 flex-shrink-0" />
                    : <Loader2 className="w-5 h-5 text-primary-400 animate-spin flex-shrink-0" />}
                  <div>
                    <p className="text-text-primary font-medium">
                      {runComplete ? 'Analysis complete!' : 'Running Analysis'}
                    </p>
                    <p className="text-text-secondary text-sm">{currentStage}</p>
                  </div>
                </div>
                {!runComplete && (
                  <div className="w-full bg-surface-elevated rounded-full h-2 overflow-hidden">
                    <div className="bg-primary-500 h-full rounded-full animate-pulse" style={{ width: '60%' }} />
                  </div>
                )}
              </div>
            ) : runError ? (
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <XCircle className="w-5 h-5 text-danger-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-danger-400 font-medium">Analysis Failed</p>
                    <p className="text-text-secondary text-sm mt-1">{runError}</p>
                  </div>
                </div>
                <Button onClick={handleContinue} variant="primary">Retry</Button>
              </div>
            ) : (
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <p className="text-text-primary font-medium">
                    {stats.uploaded > 0
                      ? `${stats.uploaded} of ${stats.total} assets uploaded`
                      : 'No assets uploaded yet — performance-only analysis'}
                  </p>

                  {/* Clear coverage message */}
                  {stats.uploaded > 0 && coverage && (
                    <div className="mt-2 space-y-1">
                      {coverage.coverage_complete ? (
                        <p className="text-xs text-success-400 flex items-center space-x-1">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>All {coverage.total_csv} creatives have real assets. Full visual analysis available.</span>
                        </p>
                      ) : (
                        <p className="text-xs text-warning-400 flex items-center space-x-1">
                          <AlertTriangle className="w-3 h-3" />
                          <span>
                            {coverage.total_real} of {coverage.total_csv} creatives registered.
                            Visual analysis covers {coverage.total_real} creative(s) only.
                          </span>
                        </p>
                      )}
                    </div>
                  )}

                  {stats.uploaded === 0 && (
                    <p className="text-xs text-text-tertiary mt-1">
                      Creative DNA and visual features will be unavailable.
                    </p>
                  )}
                </div>

                <Button onClick={handleContinue} disabled={isRunning}>
                  {stats.uploaded > 0 ? 'Run Analysis' : 'Continue Without Images'}
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            )}
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}
