'use client'

import { useEffect, useRef, useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { api } from '@/lib/api'
import { getErrorMessage } from '@/lib/apiError'
import type { Analysis, AnalysisOverview, CreativeDNAInsight } from '@/types'
import {
  MessageSquare,
  Send,
  Dna,
  TrendingUp,
  BarChart3,
  Image,
  ArrowRight,
  ChevronDown,
  Loader2,
  Database,
  Info,
} from 'lucide-react'
import { SectionHeader, Card, Button, EmptyState, Skeleton } from '@/components/ui'
import Link from 'next/link'

// ─── Types ───────────────────────────────────────────────────────────────────

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  source?: string
  confidence?: string
  timestamp: Date
}

// ─── Suggested questions (shown before first user message) ───────────────────

const SUGGESTED = [
  'What is the ROAS for this analysis?',
  'Which creative has the highest CTR?',
  'How much was the total spend?',
  'Which platform generated the most revenue?',
  'How many performance records were uploaded?',
  'Are there any Creative DNA insights?',
  'What is the date range of this dataset?',
  'What platforms are in this analysis?',
]

// ─── Confidence badge ────────────────────────────────────────────────────────

function ConfidenceBadge({ confidence }: { confidence?: string }) {
  if (!confidence || confidence === 'unavailable') return null
  const styles: Record<string, string> = {
    high: 'bg-success-500/15 text-success-400',
    medium: 'bg-warning-600/15 text-warning-400',
    low: 'bg-danger-600/15 text-danger-400',
  }
  return (
    <span
      className={`inline-block text-xs px-1.5 py-0.5 rounded font-medium ml-2 ${
        styles[confidence] ?? 'bg-surface-elevated text-text-tertiary'
      }`}
    >
      {confidence}
    </span>
  )
}

// ─── Page component ───────────────────────────────────────────────────────────

export default function AssistantPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [overview, setOverview] = useState<AnalysisOverview | null>(null)
  const [insights, setInsights] = useState<CreativeDNAInsight[]>([])
  const [loadingContext, setLoadingContext] = useState(true)

  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)

  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // ── Load analyses list ──────────────────────────────────────────────────────
  useEffect(() => {
    api.getAnalyses()
      .then((data) => {
        const completed = data.filter((a) => a.status === 'completed')
        setAnalyses(completed)
        if (completed.length > 0) setSelectedId(completed[0].id)
      })
      .catch(() => {})
      .finally(() => setLoadingContext(false))
  }, [])

  // ── Load context when analysis changes ─────────────────────────────────────
  useEffect(() => {
    if (selectedId == null) return
    setOverview(null)
    setInsights([])
    Promise.all([
      api.getAnalysisOverview(selectedId),
      api.getInsights(selectedId, 5),
    ])
      .then(([ov, ins]) => { setOverview(ov); setInsights(ins) })
      .catch(() => {})
    // Clear conversation when switching analyses
    setMessages([])
  }, [selectedId])

  // ── Scroll to bottom on new message ────────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // ── Send a question ────────────────────────────────────────────────────────
  const handleSend = async (questionText?: string) => {
    const q = (questionText ?? input).trim()
    if (!q || !selectedId || sending) return

    setInput('')
    setSendError(null)

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: q,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMsg])
    setSending(true)

    try {
      const res = await api.askAssistant(selectedId, q)
      const assistantMsg: Message = {
        id: `a-${Date.now()}`,
        role: 'assistant',
        content: res.answer,
        source: res.source,
        confidence: res.confidence,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err) {
      setSendError(getErrorMessage(err))
      // Remove the user message on hard failure so they can retry
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id))
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const agg = overview?.aggregate_metrics

  // ─── Render ────────────────────────────────────────────────────────────────
  return (
    <DashboardLayout>
      <SectionHeader
        title="Analytics Assistant"
        description="Ask questions about your analysis — answers are computed from your real data"
      />

      {/* Mode banner */}
      <div className="mb-6 bg-primary-600/10 border border-primary-600/30 rounded-lg px-4 py-3 flex items-start space-x-3">
        <Database className="w-5 h-5 text-primary-400 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-primary-400">Analytics mode — no LLM</p>
          <p className="text-xs text-text-secondary mt-0.5">
            All answers are computed directly from your performance data and DNA insights.
            No AI inference, no fabrication. Every response cites its data source.
          </p>
        </div>
      </div>

      {loadingContext ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton height="500px" className="lg:col-span-2" />
          <Skeleton height="500px" />
        </div>
      ) : analyses.length === 0 ? (
        <EmptyState
          icon={MessageSquare}
          title="No completed analyses"
          description="Complete an analysis first to enable the assistant."
          action={{ label: 'New Analysis', onClick: () => { window.location.href = '/new' } }}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* ── Chat panel ────────────────────────────────────────────────── */}
          <div className="lg:col-span-2 flex flex-col" style={{ minHeight: '520px' }}>
            <Card padding="none" className="flex flex-col flex-1">
              {/* Analysis selector header */}
              <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                <span className="text-xs text-text-tertiary">Analysis:</span>
                <div className="relative">
                  <select
                    value={selectedId ?? ''}
                    onChange={(e) => setSelectedId(Number(e.target.value))}
                    className="appearance-none bg-surface border border-border text-text-primary text-xs rounded-lg px-2 py-1.5 pr-6 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    aria-label="Select analysis"
                  >
                    {analyses.map((a) => (
                      <option key={a.id} value={a.id}>{a.name}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-1.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-tertiary pointer-events-none" />
                </div>
              </div>

              {/* Message list */}
              <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4" style={{ maxHeight: '380px' }}>
                {messages.length === 0 && (
                  <div className="text-center py-6">
                    <MessageSquare className="w-10 h-10 text-text-muted mx-auto mb-3" />
                    <p className="text-sm text-text-tertiary mb-4">
                      Ask a question about your analysis data.
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
                      {SUGGESTED.slice(0, 6).map((q) => (
                        <button
                          key={q}
                          onClick={() => handleSend(q)}
                          className="text-xs text-left px-3 py-2 bg-surface hover:bg-surface-elevated border border-border rounded-lg text-text-secondary hover:text-text-primary transition-colors"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-xl px-4 py-3 ${
                        msg.role === 'user'
                          ? 'bg-primary-600/20 text-text-primary border border-primary-600/30'
                          : 'bg-surface border border-border text-text-primary'
                      }`}
                    >
                      {msg.role === 'assistant' && (
                        <div className="flex items-center space-x-2 mb-1">
                          <Database className="w-3 h-3 text-primary-400" />
                          <span className="text-xs font-medium text-primary-400">Analytics</span>
                          <ConfidenceBadge confidence={msg.confidence} />
                        </div>
                      )}
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      {msg.role === 'assistant' && msg.source && msg.source !== 'N/A' && (
                        <p className="text-xs text-text-muted mt-2 flex items-center space-x-1">
                          <Info className="w-3 h-3" />
                          <span>Source: {msg.source}</span>
                        </p>
                      )}
                      <p className="text-xs text-text-muted mt-1">
                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                ))}

                {sending && (
                  <div className="flex justify-start">
                    <div className="bg-surface border border-border rounded-xl px-4 py-3">
                      <div className="flex items-center space-x-2">
                        <Loader2 className="w-4 h-4 text-primary-400 animate-spin" />
                        <span className="text-xs text-text-tertiary">Querying your data…</span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={bottomRef} />
              </div>

              {/* Error */}
              {sendError && (
                <div className="px-4 py-2 bg-danger-600/10 border-t border-danger-600/30 text-xs text-danger-400">
                  {sendError}
                </div>
              )}

              {/* Input */}
              <div className="px-4 py-3 border-t border-border">
                <div className="flex items-end space-x-2">
                  <textarea
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about spend, ROAS, CTR, creatives, platforms, DNA…"
                    rows={2}
                    className="flex-1 px-3 py-2 bg-surface border border-border rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                    aria-label="Ask a question"
                    disabled={sending || !selectedId}
                  />
                  <Button
                    onClick={() => handleSend()}
                    disabled={!input.trim() || sending || !selectedId}
                    loading={sending}
                    size="sm"
                    aria-label="Send question"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
                <p className="text-xs text-text-muted mt-1.5">
                  Enter to send · Shift+Enter for new line
                </p>
              </div>
            </Card>
          </div>

          {/* ── Context sidebar ────────────────────────────────────────────── */}
          <div className="space-y-4">
            {/* Live analysis metrics */}
            {agg && (
              <Card>
                <h3 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider mb-3">
                  Analysis Snapshot
                </h3>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {[
                    { label: 'Creatives', value: String(overview?.total_creatives ?? '—') },
                    { label: 'Records', value: String(overview?.total_records ?? '—') },
                    { label: 'ROAS', value: agg.roas != null ? `${agg.roas.toFixed(2)}x` : '—' },
                    { label: 'CTR', value: agg.ctr != null ? `${(agg.ctr * 100).toFixed(2)}%` : '—' },
                    { label: 'Spend', value: agg.total_spend != null ? `$${agg.total_spend.toLocaleString()}` : '—' },
                    { label: 'Revenue', value: agg.total_revenue != null ? `$${agg.total_revenue.toLocaleString()}` : '—' },
                  ].map(({ label, value }) => (
                    <div key={label} className="bg-surface rounded-lg px-3 py-2">
                      <p className="text-text-muted mb-0.5">{label}</p>
                      <p className="font-medium text-text-primary">{value}</p>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Top DNA findings */}
            {insights.length > 0 && (
              <Card>
                <h3 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider mb-3">
                  Top DNA Findings
                </h3>
                <div className="space-y-2">
                  {insights.slice(0, 3).map((ins) => {
                    const pctAbs = Math.abs(ins.percent_difference).toFixed(1)
                    const dir = ins.positive_median >= ins.negative_median ? '↑' : '↓'
                    return (
                      <button
                        key={ins.id}
                        onClick={() =>
                          handleSend(
                            `Tell me about the Creative DNA finding for ${ins.feature_name.replace(/_/g, ' ')}`
                          )
                        }
                        className="w-full text-left bg-surface hover:bg-surface-elevated rounded-lg px-3 py-2 transition-colors"
                      >
                        <p className="text-xs text-text-primary font-medium capitalize">
                          {ins.feature_name.replace(/_/g, ' ')} {dir}{pctAbs}%{' '}
                          {ins.metric_name.toUpperCase()}
                        </p>
                        <p className="text-xs text-text-muted mt-0.5">
                          {ins.evidence_tier.replace(/_/g, ' ')}
                        </p>
                      </button>
                    )
                  })}
                </div>
                <Link href="/dna">
                  <Button variant="ghost" size="sm" className="w-full mt-3 text-xs">
                    View all Creative DNA
                    <ArrowRight className="w-3 h-3 ml-1" />
                  </Button>
                </Link>
              </Card>
            )}

            {/* Navigation shortcuts */}
            <Card>
              <h3 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider mb-3">
                Explore
              </h3>
              <div className="space-y-2">
                {[
                  { href: '/performance', icon: TrendingUp, label: 'Performance' },
                  { href: '/library', icon: Image, label: 'Creative Library' },
                  { href: '/dna', icon: Dna, label: 'Creative DNA' },
                  { href: '/repurpose', icon: BarChart3, label: 'Repurpose' },
                ].map(({ href, icon: Icon, label }) => (
                  <Link key={href} href={href}>
                    <div className="flex items-center space-x-2 p-2 bg-surface hover:bg-surface-elevated border border-border rounded-lg transition-colors group cursor-pointer">
                      <div className="w-7 h-7 bg-primary-600/20 rounded flex items-center justify-center flex-shrink-0">
                        <Icon className="w-3.5 h-3.5 text-primary-400" />
                      </div>
                      <span className="text-xs text-text-secondary group-hover:text-text-primary">
                        {label}
                      </span>
                      <ArrowRight className="w-3 h-3 text-text-tertiary ml-auto" />
                    </div>
                  </Link>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}
