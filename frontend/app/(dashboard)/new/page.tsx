'use client'

import { useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/DashboardLayout'
import { api } from '@/lib/api'
import { getErrorMessage } from '@/lib/apiError'
import type { ValidationResult } from '@/types'
import {
  ChevronRight,
  ChevronLeft,
  Check,
  Upload,
  FileSpreadsheet,
  Play,
  AlertTriangle,
  Info,
  Loader2,
  X,
  Sparkles,
  Tag,
  CheckCircle2
} from 'lucide-react'
import { Button, Card, Badge } from '@/components/ui'

type Step = 1 | 2 | 3 | 4 | 5

const STEPS = [
  { n: 1, label: 'Create' },
  { n: 2, label: 'Performance' },
  { n: 3, label: 'Assets' },
  { n: 4, label: 'Review' },
  { n: 5, label: 'Run' },
]

export default function NewAnalysisPage() {
  const router = useRouter()
  const [step, setStep] = useState<Step>(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Step 1
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [analysisId, setAnalysisId] = useState<number | null>(null)

  // Step 2
  const [perfFile, setPerfFile] = useState<File | null>(null)
  const [validation, setValidation] = useState<ValidationResult | null>(null)
  const [recordsCreated, setRecordsCreated] = useState<number>(0)
  const [uploadedCreativeIds, setUploadedCreativeIds] = useState<string[]>([])
  const perfInputRef = useRef<HTMLInputElement>(null)

  // Step 3
  const [cloudinaryAvailable, setCloudinaryAvailable] = useState<boolean | null>(null)
  const [placeholdersRegistered, setPlaceholdersRegistered] = useState(false)
  const [placeholderResult, setPlaceholderResult] = useState<{
    registered: string[]
    skipped_already_existed: string[]
    rejected_not_in_performance_data: string[]
    registered_count: number
    warning?: string
  } | null>(null)

  // Step 5
  const [runStatus, setRunStatus] = useState<'idle' | 'running' | 'completed' | 'failed'>('idle')
  const [currentStage, setCurrentStage] = useState<string>('')
  const [runError, setRunError] = useState<string | null>(null)
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  // ── Step 1: Create ──────────────────────────────────────────────────────────
  const handleCreate = async () => {
    if (!name.trim()) return
    setError(null)
    setLoading(true)
    try {
      const analysis = await api.createAnalysis({
        name: name.trim(),
        description: description.trim() || undefined,
      })
      setAnalysisId(analysis.id)
      setStep(2)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  // ── Step 2: Upload performance data ─────────────────────────────────────────
  const handleUploadPerformance = async () => {
    if (!perfFile || !analysisId) return
    setError(null)
    setLoading(true)
    try {
      const result = await api.uploadPerformanceData(analysisId, perfFile)
      setValidation(result.validation)
      setRecordsCreated(result.records_created)
      setUploadedCreativeIds(result.creative_ids ?? [])

      if (result.validation.valid || result.records_created > 0) {
        setStep(3)
        api
          .getCloudinaryStatus()
          .then((s) => setCloudinaryAvailable(s.configured))
          .catch(() => setCloudinaryAvailable(false))
      }
    } catch (err) {
      setError(
        getErrorMessage(err) ||
          'Failed to upload performance data. Please check the file format.'
      )
    } finally {
      setLoading(false)
    }
  }

  // ── Step 3: Register placeholder assets for the uploaded creative IDs ───────
  // This registers ONLY the creative IDs that came from the user's uploaded CSV.
  // It never generates new IDs or touches performance records.
  const handleRegisterPlaceholders = async () => {
    if (!analysisId || uploadedCreativeIds.length === 0) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.registerPlaceholderAssets(analysisId, uploadedCreativeIds)
      setPlaceholderResult(result)
      setPlaceholdersRegistered(true)
    } catch (err) {
      setError(
        getErrorMessage(err) ||
          'Failed to register placeholder assets. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  // ── Step 5: Run + poll ───────────────────────────────────────────────────────
  const handleRun = async () => {
    if (!analysisId) return
    setError(null)
    setRunStatus('running')
    setCurrentStage('Starting…')
    try {
      await api.runAnalysis(analysisId)
      startPolling(analysisId)
    } catch (err) {
      setRunError(getErrorMessage(err) || 'Failed to start analysis.')
      setRunStatus('failed')
    }
  }

  const startPolling = useCallback(
    (id: number) => {
      if (pollRef.current) clearInterval(pollRef.current)
      pollRef.current = setInterval(async () => {
        try {
          const s = await api.getAnalysisStatus(id)
          setCurrentStage(s.current_stage || '')
          if (s.status === 'completed') {
            clearInterval(pollRef.current!)
            setRunStatus('completed')
            setTimeout(() => router.push('/dashboard'), 1500)
          } else if (s.status === 'failed') {
            clearInterval(pollRef.current!)
            setRunStatus('failed')
            setRunError(s.error_message || 'Analysis failed. Please try again.')
          }
        } catch {
          // transient poll error — keep trying
        }
      }, 2000)
    },
    [router]
  )

  // ── Step progress indicator ──────────────────────────────────────────────────
  const StepIndicator = () => (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        {STEPS.map((s, idx) => (
          <div key={s.n} className="flex items-center">
            <div
              className={`w-9 h-9 rounded-full flex items-center justify-center font-semibold text-sm transition-all ${
                s.n < step
                  ? 'bg-success-500 text-white'
                  : s.n === step
                  ? 'bg-primary-600 text-white shadow-lg shadow-primary-600/30'
                  : 'bg-surface-elevated text-text-tertiary border border-border'
              }`}
            >
              {s.n < step ? <Check className="w-4 h-4" /> : s.n}
            </div>
            {idx < STEPS.length - 1 && (
              <div
                className={`flex-1 h-0.5 mx-2 transition-colors ${
                  s.n < step ? 'bg-success-500' : 'bg-border'
                }`}
                style={{ minWidth: 24 }}
              />
            )}
          </div>
        ))}
      </div>
      <div className="flex justify-between mt-2 text-xs text-text-tertiary px-0.5">
        {STEPS.map((s) => (
          <span
            key={s.n}
            className={s.n === step ? 'text-primary-400 font-medium' : ''}
          >
            {s.label}
          </span>
        ))}
      </div>
    </div>
  )

  // ── Step content ─────────────────────────────────────────────────────────────
  const renderStep = () => {
    switch (step) {
      // ── 1: Create ────────────────────────────────────────────────────────────
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-text-primary mb-1">
                Name your analysis
              </h2>
              <p className="text-text-secondary text-sm">
                Give this analysis a descriptive name so you can find it later.
              </p>
            </div>

            <div>
              <label
                className="block text-sm font-medium text-text-secondary mb-2"
                htmlFor="analysis-name"
              >
                Analysis name <span className="text-danger-400">*</span>
              </label>
              <input
                id="analysis-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Q4 2026 Campaign Analysis"
                className="w-full px-4 py-2.5 bg-surface border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                required
                autoFocus
              />
            </div>

            <div>
              <label
                className="block text-sm font-medium text-text-secondary mb-2"
                htmlFor="analysis-desc"
              >
                Description{' '}
                <span className="text-text-muted text-xs">(optional)</span>
              </label>
              <textarea
                id="analysis-desc"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the purpose of this analysis…"
                rows={3}
                className="w-full px-4 py-2.5 bg-surface border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all resize-none"
              />
            </div>

            <Button
              onClick={handleCreate}
              disabled={!name.trim() || loading}
              loading={loading}
              fullWidth
              size="lg"
            >
              {loading ? 'Creating…' : 'Create & Continue'}
              <ChevronRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        )

      // ── 2: Performance data ──────────────────────────────────────────────────
      case 2:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-text-primary mb-1">
                Upload performance data
              </h2>
              <p className="text-text-secondary text-sm">
                Upload a CSV or Excel file with your campaign metrics.
              </p>
            </div>

            {/* Required columns */}
            <div className="bg-surface border border-border rounded-lg p-4">
              <p className="text-sm font-medium text-text-secondary mb-2">
                Required columns (or recognised aliases):
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-1 text-xs font-mono">
                {[
                  'creative_id',
                  'platform',
                  'impressions',
                  'clicks',
                  'conversions',
                  'spend',
                  'revenue',
                ].map((c) => (
                  <span
                    key={c}
                    className="bg-surface-elevated text-primary-400 px-2 py-1 rounded"
                  >
                    {c}
                  </span>
                ))}
                <span className="bg-surface-elevated text-text-tertiary px-2 py-1 rounded">
                  date (optional)
                </span>
              </div>
              <p className="text-xs text-text-tertiary mt-2">
                Common column name variants (e.g. <code className="text-primary-400">ad_id</code>{' '}
                for <code className="text-primary-400">creative_id</code>, or{' '}
                <code className="text-primary-400">cost</code> for{' '}
                <code className="text-primary-400">spend</code>) are accepted and
                automatically mapped.
              </p>
            </div>

            {/* File drop zone */}
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
                perfFile
                  ? 'border-success-500 bg-success-500/5'
                  : 'border-border hover:border-primary-500 hover:bg-primary-600/5'
              }`}
              onClick={() => perfInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault()
                const f = e.dataTransfer.files[0]
                if (f) setPerfFile(f)
              }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && perfInputRef.current?.click()}
            >
              <input
                ref={perfInputRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => setPerfFile(e.target.files?.[0] || null)}
                className="hidden"
                aria-label="Upload performance file"
              />
              <FileSpreadsheet
                className={`w-10 h-10 mx-auto mb-3 ${
                  perfFile ? 'text-success-400' : 'text-text-tertiary'
                }`}
              />
              {perfFile ? (
                <div>
                  <p className="text-text-primary font-medium">{perfFile.name}</p>
                  <p className="text-xs text-text-tertiary mt-1">
                    {(perfFile.size / 1024).toFixed(1)} KB
                  </p>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setPerfFile(null)
                      setValidation(null)
                      setRecordsCreated(0)
                      setUploadedCreativeIds([])
                    }}
                    className="mt-2 text-xs text-danger-400 hover:text-danger-300"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div>
                  <p className="text-text-primary font-medium">
                    Click to upload or drag and drop
                  </p>
                  <p className="text-xs text-text-tertiary mt-1">
                    CSV or Excel (.csv, .xlsx, .xls)
                  </p>
                </div>
              )}
            </div>

            {/* Validation result */}
            {validation && (
              <div className="space-y-2">
                <div
                  className={`rounded-lg p-4 border ${
                    validation.valid
                      ? 'bg-success-500/10 border-success-500/30'
                      : 'bg-danger-600/10 border-danger-600/30'
                  }`}
                >
                  <p
                    className={`text-sm font-medium ${
                      validation.valid ? 'text-success-400' : 'text-danger-400'
                    }`}
                  >
                    {validation.valid
                      ? '✓ Validation passed'
                      : '✗ Validation errors found'}
                  </p>
                  <div className="grid grid-cols-3 gap-2 mt-2 text-xs text-text-secondary">
                    <span>
                      Total rows:{' '}
                      <strong className="text-text-primary">
                        {validation.total_rows}
                      </strong>
                    </span>
                    <span>
                      Valid:{' '}
                      <strong className="text-success-400">
                        {validation.valid_rows}
                      </strong>
                    </span>
                    <span>
                      Excluded:{' '}
                      <strong className="text-warning-400">
                        {validation.excluded_rows}
                      </strong>
                    </span>
                  </div>
                </div>
                {validation.errors.map((e, i) => (
                  <div
                    key={i}
                    className="flex items-start space-x-2 text-xs text-danger-400 bg-danger-600/10 rounded-lg px-3 py-2"
                  >
                    <X className="w-3 h-3 mt-0.5 flex-shrink-0" />
                    <span>{e.message}</span>
                  </div>
                ))}
                {validation.warnings.map((w, i) => (
                  <div
                    key={i}
                    className="flex items-start space-x-2 text-xs text-warning-400 bg-warning-600/10 rounded-lg px-3 py-2"
                  >
                    <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                    <span>{w.message}</span>
                  </div>
                ))}
              </div>
            )}

            <div className="flex space-x-3">
              <Button
                variant="ghost"
                onClick={() => setStep(1)}
                className="flex-1"
              >
                <ChevronLeft className="w-5 h-5 mr-1" />
                Back
              </Button>
              <Button
                onClick={handleUploadPerformance}
                disabled={!perfFile || loading}
                loading={loading}
              >
                <Upload className="w-4 h-4 mr-2" />
                {loading ? 'Uploading…' : 'Upload & Continue'}
              </Button>
            </div>
          </div>
        )

      // ── 3: Assets ────────────────────────────────────────────────────────────
      case 3:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-text-primary mb-1">
                Register creative assets
              </h2>
              <p className="text-text-secondary text-sm">
                Upload real creative images for visual feature extraction and Creative DNA
                analysis. Without real images, the analysis will complete with performance
                metrics only.
              </p>
            </div>

            {/* Creative IDs from the upload */}
            {uploadedCreativeIds.length > 0 && (
              <div className="bg-surface border border-border rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Tag className="w-4 h-4 text-primary-400" />
                  <p className="text-sm font-medium text-text-primary">
                    Creative IDs in your dataset ({uploadedCreativeIds.length})
                  </p>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {uploadedCreativeIds.slice(0, 10).map((id) => (
                    <span
                      key={id}
                      className="text-xs font-mono bg-surface-elevated text-primary-400 px-2 py-0.5 rounded"
                    >
                      {id}
                    </span>
                  ))}
                  {uploadedCreativeIds.length > 10 && (
                    <span className="text-xs text-text-tertiary px-2 py-0.5">
                      +{uploadedCreativeIds.length - 10} more
                    </span>
                  )}
                </div>
                <p className="text-xs text-text-tertiary mt-2">
                  These are the exact creative IDs from your uploaded performance
                  data. Upload images for each ID to enable visual analysis.
                </p>
              </div>
            )}

            {/* Cloudinary status */}
            <div
              className={`rounded-lg p-4 border ${
                cloudinaryAvailable
                  ? 'border-success-500/30 bg-success-500/5'
                  : 'border-border bg-surface'
              }`}
            >
              <div className="flex items-center space-x-3 mb-2">
                <Sparkles
                  className={`w-5 h-5 ${
                    cloudinaryAvailable
                      ? 'text-success-400'
                      : 'text-text-tertiary'
                  }`}
                />
                <span className="font-medium text-text-primary">
                  Cloudinary Image Upload
                </span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    cloudinaryAvailable
                      ? 'bg-success-500/20 text-success-400'
                      : 'bg-surface-elevated text-text-tertiary'
                  }`}
                >
                  {cloudinaryAvailable === null
                    ? 'Checking…'
                    : cloudinaryAvailable
                    ? 'Available'
                    : 'Not Configured'}
                </span>
              </div>
              {cloudinaryAvailable ? (
                <div className="space-y-3">
                  <p className="text-sm text-text-secondary">
                    Cloudinary is configured and ready. Upload your creative images
                    to enable visual feature extraction and Creative DNA generation.
                  </p>
                  <Button
                    variant="primary"
                    onClick={() => {
                      if (analysisId) {
                        window.location.href = `/new/assets/${analysisId}`
                      }
                    }}
                    disabled={!analysisId}
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Upload {uploadedCreativeIds.length} Creative Image{uploadedCreativeIds.length !== 1 ? 's' : ''}
                  </Button>
                </div>
              ) : (
                <p className="text-sm text-text-secondary">
                  Cloudinary is not configured. To enable image uploads, set{' '}
                  <code className="text-primary-400">CLOUDINARY_CLOUD_NAME</code>
                  ,{' '}
                  <code className="text-primary-400">CLOUDINARY_API_KEY</code>,
                  and{' '}
                  <code className="text-primary-400">
                    CLOUDINARY_API_SECRET
                  </code>{' '}
                  in the backend environment, then restart the server.
                </p>
              )}
            </div>

            {/* Performance-only option */}
            <div className="bg-surface border border-border rounded-lg p-4">
              <div className="flex items-center space-x-3 mb-2">
                <Info className="w-5 h-5 text-text-tertiary" />
                <span className="font-medium text-text-primary">
                  Performance-Only Analysis
                </span>
              </div>
              <p className="text-sm text-text-secondary mb-3">
                You can run the analysis without uploading creative images. The
                pipeline will compute all performance metrics, but Creative DNA
                visual analysis will be unavailable.
              </p>
            </div>

            {/* Placeholder explanation (deprecated) */}
            <div className="bg-warning-600/10 border border-warning-600/30 rounded-lg p-4">
              <div className="flex items-center space-x-3 mb-2">
                <AlertTriangle className="w-5 h-5 text-warning-400" />
                <span className="font-medium text-warning-400">
                  About Placeholder Assets
                </span>
              </div>
              <p className="text-sm text-text-secondary mb-2">
                Placeholder assets are metadata-only records with NO actual images.
                They do NOT contain visual data and will NOT generate Creative DNA.
              </p>
              <p className="text-sm text-text-secondary">
                To get real Creative DNA insights, upload actual creative images
                through Cloudinary above.
              </p>
            </div>

            <div className="flex space-x-3">
              <Button
                variant="ghost"
                onClick={() => setStep(2)}
                className="flex-1"
              >
                <ChevronLeft className="w-5 h-5 mr-1" />
                Back
              </Button>
              <Button onClick={() => setStep(4)}>
                Continue to Review
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
            </div>
          </div>
        )

      // ── 4: Review ────────────────────────────────────────────────────────────
      case 4:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-text-primary mb-1">
                Review & confirm
              </h2>
              <p className="text-text-secondary text-sm">
                Confirm the details before running your analysis.
              </p>
            </div>

            <div className="space-y-3">
              <div className="bg-surface border border-border rounded-lg p-4">
                <p className="text-xs text-text-tertiary mb-1">Analysis name</p>
                <p className="text-text-primary font-medium">{name}</p>
                {description && (
                  <p className="text-sm text-text-secondary mt-1">{description}</p>
                )}
              </div>

              <div className="bg-surface border border-border rounded-lg p-4">
                <p className="text-xs text-text-tertiary mb-1">Performance data</p>
                {validation ? (
                  <div className="space-y-2">
                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div>
                        <span className="text-text-tertiary text-xs">
                          Total rows
                        </span>
                        <br />
                        <span className="text-text-primary font-medium">
                          {validation.total_rows}
                        </span>
                      </div>
                      <div>
                        <span className="text-text-tertiary text-xs">
                          Persisted records
                        </span>
                        <br />
                        <span className="text-success-400 font-medium">
                          {recordsCreated}
                        </span>
                      </div>
                      <div>
                        <span className="text-text-tertiary text-xs">
                          Excluded
                        </span>
                        <br />
                        <span className="text-warning-400 font-medium">
                          {validation.excluded_rows}
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-text-tertiary">
                      {uploadedCreativeIds.length} unique creative ID
                      {uploadedCreativeIds.length !== 1 ? 's' : ''} in dataset
                    </p>
                  </div>
                ) : (
                  <p className="text-text-secondary text-sm">
                    File: {perfFile?.name}
                  </p>
                )}
              </div>

              <div className="bg-surface border border-border rounded-lg p-4">
                <p className="text-xs text-text-tertiary mb-1">Creative assets</p>
                {placeholdersRegistered && placeholderResult ? (
                  <p className="text-sm text-success-400">
                    {placeholderResult.registered_count} placeholder asset(s)
                    registered for visual analysis
                  </p>
                ) : cloudinaryAvailable ? (
                  <p className="text-sm text-text-secondary">
                    Cloudinary configured — register real assets via the API
                  </p>
                ) : (
                  <p className="text-sm text-text-secondary">
                    No assets registered — analysis will complete with
                    performance data only (Creative DNA unavailable)
                  </p>
                )}
              </div>

              {validation && validation.warnings.length > 0 && (
                <div className="bg-warning-600/10 border border-warning-600/30 rounded-lg p-4">
                  <p className="text-xs text-warning-400 font-medium mb-2">
                    {validation.warnings.length} warning(s) from upload
                  </p>
                  {validation.warnings.map((w, i) => (
                    <p key={i} className="text-xs text-text-secondary">
                      • {w.message}
                    </p>
                  ))}
                </div>
              )}
            </div>

            <div className="flex space-x-3">
              <Button
                variant="ghost"
                onClick={() => setStep(3)}
                className="flex-1"
              >
                <ChevronLeft className="w-5 h-5 mr-1" />
                Back
              </Button>
              <Button onClick={() => setStep(5)}>
                <Play className="w-4 h-4 mr-2" />
                Run Analysis
              </Button>
            </div>
          </div>
        )

      // ── 5: Run + poll ────────────────────────────────────────────────────────
      case 5:
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-text-primary mb-1">
                Running analysis
              </h2>
              <p className="text-text-secondary text-sm">
                Processing your data through the CreativePulse pipeline.
              </p>
            </div>

            {runStatus === 'idle' && (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-primary-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Play className="w-8 h-8 text-primary-400" />
                </div>
                <p className="text-text-secondary mb-2">
                  Ready to analyze{' '}
                  <strong className="text-text-primary">{recordsCreated}</strong>{' '}
                  performance record
                  {recordsCreated !== 1 ? 's' : ''} across{' '}
                  <strong className="text-text-primary">
                    {uploadedCreativeIds.length}
                  </strong>{' '}
                  creative ID{uploadedCreativeIds.length !== 1 ? 's' : ''}.
                </p>
                {!placeholdersRegistered && (
                  <p className="text-xs text-warning-400 mb-6">
                    No assets registered — Creative DNA will be unavailable for
                    this analysis.
                  </p>
                )}
                <Button size="lg" onClick={handleRun} loading={loading}>
                  <Play className="w-5 h-5 mr-2" />
                  Start Analysis
                </Button>
              </div>
            )}

            {runStatus === 'running' && (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-primary-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
                </div>
                <p className="text-text-primary font-medium mb-1">
                  Analyzing…
                </p>
                <p className="text-sm text-text-secondary">
                  {currentStage || 'Processing…'}
                </p>
                <div className="mt-4 w-48 h-1.5 bg-surface-elevated rounded-full mx-auto overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary-600 to-secondary-500 rounded-full animate-pulse"
                    style={{ width: '60%' }}
                  />
                </div>
              </div>
            )}

            {runStatus === 'completed' && (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-success-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Check className="w-8 h-8 text-success-400" />
                </div>
                <p className="text-text-primary font-medium mb-1">
                  Analysis complete!
                </p>
                <p className="text-sm text-text-secondary">
                  Redirecting to your dashboard…
                </p>
              </div>
            )}

            {runStatus === 'failed' && (
              <div className="space-y-4">
                <div className="bg-danger-600/10 border border-danger-600/30 rounded-lg p-4 text-center">
                  <X className="w-8 h-8 text-danger-400 mx-auto mb-2" />
                  <p className="text-danger-400 font-medium mb-1">
                    Analysis failed
                  </p>
                  <p className="text-sm text-text-secondary">{runError}</p>
                </div>
                <div className="flex space-x-3">
                  <Button
                    variant="ghost"
                    onClick={() => setStep(4)}
                    className="flex-1"
                  >
                    <ChevronLeft className="w-5 h-5 mr-1" />
                    Back
                  </Button>
                  <Button
                    onClick={() => {
                      setRunStatus('idle')
                      setRunError(null)
                    }}
                    className="flex-1"
                  >
                    Retry
                  </Button>
                </div>
              </div>
            )}
          </div>
        )
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto">
        <StepIndicator />
        <Card>
          {error && (
            <div className="mb-5 bg-danger-600/10 border border-danger-600/30 text-danger-400 px-4 py-3 rounded-lg text-sm flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {renderStep()}
        </Card>
      </div>
    </DashboardLayout>
  )
}
