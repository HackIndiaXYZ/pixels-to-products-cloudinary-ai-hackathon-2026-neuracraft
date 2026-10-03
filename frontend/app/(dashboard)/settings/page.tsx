'use client'

import { useState, useEffect } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { api } from '@/lib/api'
import type { User } from '@/types'
import { User as UserIcon, Settings as SettingsIcon, Cloud, Server, Info } from 'lucide-react'
import { SectionHeader, Card, Skeleton, ErrorState } from '@/components/ui'

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null)
  const [cloudinaryStatus, setCloudinaryStatus] = useState<{ configured: boolean; message: string } | null>(null)
  const [aiStatus, setAiStatus] = useState<{ configured: boolean; message: string; endpoint?: string; model?: string } | null>(null)
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [userData, cloudinary, ai, health] = await Promise.allSettled([
          api.getCurrentUser(),
          api.checkCloudinaryHealth(),
          api.checkAIHealth(),
          api.checkHealth(),
        ])
        if (userData.status === 'fulfilled') setUser(userData.value)
        if (cloudinary.status === 'fulfilled') setCloudinaryStatus(cloudinary.value)
        if (ai.status === 'fulfilled') setAiStatus(ai.value)
        setBackendHealthy(health.status === 'fulfilled')
      } catch {
        setError('Failed to load settings.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return (
    <DashboardLayout>
      <SectionHeader title="Settings" description="Account and preferences" />
      <div className="space-y-4 max-w-2xl">
        <Skeleton height="150px" />
        <Skeleton height="120px" />
        <Skeleton height="120px" />
      </div>
    </DashboardLayout>
  )

  if (error) return <DashboardLayout><ErrorState message={error} onRetry={() => window.location.reload()} /></DashboardLayout>

  const StatusDot = ({ ok }: { ok: boolean | null }) => (
    <span className={`inline-block w-2 h-2 rounded-full ${ok == null ? 'bg-text-muted' : ok ? 'bg-success-400' : 'bg-danger-400'}`} aria-hidden="true" />
  )

  return (
    <DashboardLayout>
      <SectionHeader
        title="Settings"
        description="Account information and system status"
      />

      <div className="max-w-2xl space-y-6">
        {/* Account */}
        <Card>
          <div className="flex items-center space-x-3 mb-5">
            <div className="w-9 h-9 bg-primary-600/20 rounded-lg flex items-center justify-center">
              <UserIcon className="w-5 h-5 text-primary-400" />
            </div>
            <h2 className="text-base font-semibold text-text-primary">Account</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-text-tertiary mb-1.5">Email address</label>
              <input
                type="email"
                value={user?.email ?? ''}
                disabled
                className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-secondary text-sm cursor-not-allowed"
                aria-label="Email address (read-only)"
              />
              <p className="mt-1 text-xs text-text-muted">Email address cannot be changed.</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-text-tertiary mb-1.5">User ID</label>
                <input
                  type="text"
                  value={user?.id ?? ''}
                  disabled
                  className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-secondary text-sm font-mono cursor-not-allowed"
                  aria-label="User ID (read-only)"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-tertiary mb-1.5">Member since</label>
                <input
                  type="text"
                  value={user?.created_at ? new Date(user.created_at).toLocaleDateString() : ''}
                  disabled
                  className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-secondary text-sm cursor-not-allowed"
                  aria-label="Member since (read-only)"
                />
              </div>
            </div>
          </div>
        </Card>

        {/* System status */}
        <Card>
          <div className="flex items-center space-x-3 mb-5">
            <div className="w-9 h-9 bg-secondary-600/20 rounded-lg flex items-center justify-center">
              <Server className="w-5 h-5 text-secondary-400" />
            </div>
            <h2 className="text-base font-semibold text-text-primary">System Status</h2>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between py-2.5 border-b border-border">
              <div className="flex items-center space-x-2">
                <StatusDot ok={backendHealthy} />
                <span className="text-sm text-text-secondary">Backend API</span>
              </div>
              <span className={`text-xs font-medium ${backendHealthy ? 'text-success-400' : 'text-danger-400'}`}>
                {backendHealthy == null ? 'Unknown' : backendHealthy ? 'Connected' : 'Unreachable'}
              </span>
            </div>

            <div className="flex items-center justify-between py-2.5 border-b border-border">
              <div className="flex items-center space-x-2">
                <StatusDot ok={cloudinaryStatus?.configured ?? null} />
                <span className="text-sm text-text-secondary">Cloudinary</span>
              </div>
              <span className={`text-xs font-medium ${cloudinaryStatus?.configured ? 'text-success-400' : 'text-text-tertiary'}`}>
                {cloudinaryStatus?.configured ? 'Configured' : 'Not configured'}
              </span>
            </div>

            <div className="flex items-center justify-between py-2.5">
              <div className="flex items-center space-x-2">
                <StatusDot ok={aiStatus?.configured ?? null} />
                <span className="text-sm text-text-secondary">AI Assistant</span>
              </div>
              <span className={`text-xs font-medium ${aiStatus?.configured ? 'text-success-400' : 'text-text-tertiary'}`}>
                {aiStatus?.configured ? 'Configured' : 'Not configured'}
              </span>
            </div>
          </div>
        </Card>

        {/* Application info */}
        <Card>
          <div className="flex items-center space-x-3 mb-5">
            <div className="w-9 h-9 bg-surface-elevated rounded-lg flex items-center justify-center">
              <SettingsIcon className="w-5 h-5 text-text-tertiary" />
            </div>
            <h2 className="text-base font-semibold text-text-primary">Application</h2>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between py-1">
              <span className="text-text-tertiary">Version</span>
              <span className="text-text-primary font-medium">1.0.0</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-text-tertiary">API endpoint</span>
              <span className="text-text-secondary font-mono text-xs">{process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</span>
            </div>
          </div>
        </Card>

        {/* Notification preferences — clearly labelled as not persisted */}
        <Card>
          <div className="flex items-start space-x-3">
            <Info className="w-5 h-5 text-text-tertiary flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-text-primary mb-1">Notification preferences</p>
              <p className="text-xs text-text-secondary">
                Email notification preferences are not yet available in this version. Backend persistence for user preferences is on the roadmap.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  )
}
