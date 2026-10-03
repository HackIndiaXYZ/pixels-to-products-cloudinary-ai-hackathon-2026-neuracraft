/**
 * TypeScript types for the CreativePulse application
 * Single source of truth — all types derived from actual backend schemas
 */

// ─── Auth ────────────────────────────────────────────────────────────────────

export interface User {
  id: number
  email: string
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface SignupRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

// ─── Analysis ────────────────────────────────────────────────────────────────

export type AnalysisStatus =
  | 'draft'
  | 'uploading'
  | 'validating'
  | 'processing'
  | 'completed'
  | 'failed'

export interface Analysis {
  id: number
  user_id: number
  name: string
  description?: string
  status: AnalysisStatus
  current_stage?: string
  error_message?: string
  created_at: string
  updated_at: string
}

export interface CreateAnalysisRequest {
  name: string
  description?: string
}

export interface AnalysisStatusResponse {
  id: number
  status: AnalysisStatus
  current_stage?: string
  error_message?: string
}

// ─── Asset ───────────────────────────────────────────────────────────────────

export interface Asset {
  id: number
  analysis_id: number
  creative_id: string
  filename: string
  cloudinary_public_id?: string
  cloudinary_url?: string
  secure_url?: string
  width?: number
  height?: number
  format?: string
  bytes?: number
  source: 'cloudinary' | 'local_demo'
  created_at: string
}

export interface AssetRegisterRequest {
  creative_id: string
  filename: string
  cloudinary_public_id?: string
  cloudinary_url?: string
  secure_url?: string
  width?: number
  height?: number
  format?: string
  bytes?: number
  source: 'cloudinary' | 'local_demo'
}

export interface AssetWithMetrics extends Asset {
  metrics: PerformanceMetrics
}

// ─── Performance ─────────────────────────────────────────────────────────────

export interface PerformanceMetrics {
  total_impressions: number
  total_clicks: number
  total_conversions: number
  total_spend: number
  total_revenue: number
  ctr: number | null
  cvr: number | null
  cpc: number | null
  roas: number | null
  cpm: number | null
}

export interface CreativePerformance {
  creative_id: string
  total_impressions: number
  total_clicks: number
  total_conversions: number
  total_spend: number
  total_revenue: number
  ctr: number | null
  cvr: number | null
  cpc: number | null
  roas: number | null
  cpm: number | null
}

export interface PlatformMetrics {
  platform: string
  total_impressions: number
  total_clicks: number
  total_conversions: number
  total_spend: number
  total_revenue: number
  ctr: number | null
  cvr: number | null
  cpc: number | null
  roas: number | null
  cpm: number | null
}

// ─── Validation ──────────────────────────────────────────────────────────────

export interface ValidationWarning {
  type: string
  message: string
  count?: number
  details?: Record<string, unknown>
}

export interface ValidationError {
  type: string
  message: string
  details?: Record<string, unknown>
}

export interface ValidationResult {
  valid: boolean
  errors: ValidationError[]
  warnings: ValidationWarning[]
  excluded_rows: number
  total_rows: number
  valid_rows: number
}

export interface PerformanceUploadResponse {
  validation: ValidationResult
  records_created: number
  message: string
  /** Unique creative_id values present in the validated dataset. */
  creative_ids: string[]
}

// ─── Overview ────────────────────────────────────────────────────────────────

export interface AnalysisOverview {
  analysis_id: number
  analysis_name: string
  status: string
  total_creatives: number
  total_records: number
  aggregate_metrics: PerformanceMetrics
  top_by_roas: CreativePerformance[]
  top_by_ctr: CreativePerformance[]
}

export interface PerformanceResponse {
  analysis_id: number
  creatives: CreativePerformance[]
  records: Array<{
    creative_id: string
    platform: string
    impressions: number
    clicks: number
    conversions: number
    spend: number
    revenue: number
    date?: string
  }>
}

export interface AssetsResponse {
  analysis_id: number
  assets: AssetWithMetrics[]
}

export interface PlatformsResponse {
  analysis_id: number
  platforms: PlatformMetrics[]
}

// ─── Creative DNA ────────────────────────────────────────────────────────────

export type EvidenceTier =
  | 'strong'
  | 'moderate'
  | 'weak'
  | 'no_clear_evidence'
  | 'insufficient_evidence'

export interface CreativeDNAInsight {
  id: number
  analysis_id: number
  feature_name: string
  metric_name: string
  positive_group: string
  negative_group: string
  positive_median: number
  negative_median: number
  percent_difference: number
  sample_size_positive: number
  sample_size_negative: number
  p_value: number | null
  effect_size: number | null
  evidence_tier: EvidenceTier
  explanation: string
  created_at: string
}

/** Alias so older imports of DNAInsight still compile */
export type DNAInsight = CreativeDNAInsight

// ─── Creative Features ───────────────────────────────────────────────────────

export interface CreativeFeatures {
  creative_id: string
  aspect_ratio: number | null
  brightness: number | null
  contrast: number | null
  edge_density: number | null
  dominant_color: string | null
  bright_background: boolean | null
  portrait: boolean | null
  landscape: boolean | null
  human_present: boolean | null
  feature_sources: Record<string, string> | null
}

// ─── Cloudinary ──────────────────────────────────────────────────────────────

export interface CloudinarySignature {
  signature: string
  timestamp: string
  api_key: string
  cloud_name: string
  folder: string
  public_id?: string
}

export interface CloudinaryUploadResult {
  public_id: string
  secure_url: string
  url: string
  width: number
  height: number
  format: string
  bytes: number
}

export interface CloudinaryStatus {
  configured: boolean
  message: string
  features_available?: {
    upload: boolean
    transformations: boolean
    repurposing: boolean
  }
}

// ─── Repurpose ───────────────────────────────────────────────────────────────

export type RepurposeFormat = '4:5' | '9:16' | '16:9' | '1:1'

export interface RepurposeRequest {
  source_asset_id: number
  format: RepurposeFormat
}

export interface GeneratedAsset {
  id: number
  analysis_id: number
  source_asset_id: number
  format: string
  transformation?: Record<string, unknown>
  generated_url: string
  created_at: string
}

// ─── API error shape ─────────────────────────────────────────────────────────

export interface ApiError {
  detail: string
}
