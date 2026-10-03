'use client'

import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  Sparkles,
  ArrowRight,
  BarChart3,
  Dna,
  Image,
  Wand2,
  Check,
  TrendingUp,
  Zap,
  Shield
} from 'lucide-react'
import { Button, Card, Badge } from '@/components/ui'

export default function Home() {
  const router = useRouter()
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
    setIsAuthenticated(!!token)
  }, [])

  const handleStartAnalyzing = () => {
    if (isAuthenticated) {
      router.push('/dashboard')
    } else {
      router.push('/login')
    }
  }

  const features = [
    {
      icon: BarChart3,
      title: 'Performance Analytics',
      description: 'Connect creative assets with campaign performance data to understand what drives results.'
    },
    {
      icon: Dna,
      title: 'Creative DNA',
      description: 'Discover statistically-backed visual patterns associated with higher performance.'
    },
    {
      icon: Image,
      title: 'Visual Intelligence',
      description: 'Automated analysis of creative characteristics across your entire asset library.'
    },
    {
      icon: Wand2,
      title: 'Smart Repurposing',
      description: 'Transform high-performing creatives into campaign-ready formats with Cloudinary.'
    },
  ]

  const howItWorks = [
    {
      step: '01',
      title: 'Upload',
      description: 'Connect your creative library and performance data in minutes.'
    },
    {
      step: '02',
      title: 'Analyze',
      description: 'CreativePulse extracts visual features and runs statistical analysis.'
    },
    {
      step: '03',
      title: 'Understand',
      description: 'Discover which creative characteristics are associated with better performance.'
    },
    {
      step: '04',
      title: 'Repurpose',
      description: 'Transform proven creative patterns into production-ready assets.'
    },
  ]

  return (
    <div className="min-h-screen bg-background noise-bg">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center shadow-lg shadow-primary-500/20">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold text-text-primary">
                CreativePulse AI
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/login">
                <Button variant="ghost" size="sm">
                  Sign In
                </Button>
              </Link>
              <Button size="sm" onClick={handleStartAnalyzing}>
                Start Analyzing
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary-600/5 via-transparent to-transparent pointer-events-none" />
        <div className="absolute top-40 left-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-60 right-1/4 w-96 h-96 bg-secondary-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto relative">
          <div className="text-center max-w-4xl mx-auto mb-16">
            <Badge variant="primary" className="mb-6 animate-fade-in">
              <Sparkles className="w-3 h-3 mr-1" />
              AI-Powered Creative Intelligence
            </Badge>

            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-text-primary mb-6 tracking-tight animate-slide-up">
              Turn Creative Performance into{' '}
              <span className="gradient-text">Creative DNA</span>
            </h1>

            <p className="text-xl text-text-secondary mb-8 max-w-3xl mx-auto animate-slide-up delay-100">
              Connect your creative library with campaign performance to discover measurable visual patterns,
              understand what drives results, and transform insights into production-ready assets.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-slide-up delay-200">
              <Button size="lg" className="w-full sm:w-auto" onClick={handleStartAnalyzing}>
                Start Analyzing
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
              <a href="#how-it-works">
                <Button size="lg" variant="outline" className="w-full sm:w-auto">
                  See How It Works
                </Button>
              </a>
            </div>
          </div>

          {/* Hero Visual — illustrative dashboard preview */}
          <div className="relative max-w-6xl mx-auto animate-slide-up delay-300">
            <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent z-10 pointer-events-none" />
            <Card variant="glass" className="overflow-hidden shadow-2xl">
              <div className="aspect-[16/9] bg-gradient-to-br from-surface to-surface-elevated p-8">
                <p className="text-xs text-text-tertiary text-right mb-4 italic">
                  Illustrative example — your results will reflect your own data
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-background/50 backdrop-blur-sm rounded-lg p-4 border border-border">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs text-text-tertiary">ROAS</div>
                      <TrendingUp className="w-4 h-4 text-success-400" />
                    </div>
                    <div className="text-2xl font-bold text-text-primary metric-number">—</div>
                  </div>
                  <div className="bg-background/50 backdrop-blur-sm rounded-lg p-4 border border-border">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs text-text-tertiary">CTR</div>
                      <Zap className="w-4 h-4 text-primary-400" />
                    </div>
                    <div className="text-2xl font-bold text-text-primary metric-number">—</div>
                  </div>
                  <div className="bg-background/50 backdrop-blur-sm rounded-lg p-4 border border-border">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs text-text-tertiary">Creatives</div>
                      <Image className="w-4 h-4 text-secondary-400" />
                    </div>
                    <div className="text-2xl font-bold text-text-primary metric-number">—</div>
                  </div>
                </div>
                <div className="bg-background/50 backdrop-blur-sm rounded-lg p-4 border border-border">
                  <div className="flex items-center space-x-2 mb-3">
                    <Dna className="w-4 h-4 text-primary-400" />
                    <div className="text-sm font-semibold text-text-primary">Creative DNA</div>
                    <span className="text-xs text-text-tertiary italic ml-auto">Computed from your data</span>
                  </div>
                  <div className="text-xs text-text-secondary">
                    Upload your creative assets and performance data to discover visual patterns associated with performance.
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* Capability Strip */}
      <section className="py-12 border-y border-border bg-surface/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-text-primary mb-2 metric-number">9</div>
              <div className="text-sm text-text-tertiary">Visual Features</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-text-primary mb-2 metric-number">Statistical</div>
              <div className="text-sm text-text-tertiary">Evidence-Based</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-text-primary mb-2 metric-number">AI</div>
              <div className="text-sm text-text-tertiary">Visual Intelligence</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-text-primary mb-2 metric-number">Cloudinary</div>
              <div className="text-sm text-text-tertiary">Powered Repurposing</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-text-primary mb-4">
              Creative Intelligence Platform
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mx-auto">
              Turn your creative data into actionable insights with AI-powered analysis and statistical evidence.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, idx) => (
              <Card
                key={idx}
                hover
                className="animate-slide-up"
                style={{ animationDelay: `${idx * 100}ms` }}
              >
                <div className="w-12 h-12 bg-primary-600/20 rounded-xl flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary-400" />
                </div>
                <h3 className="text-lg font-semibold text-text-primary mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-text-secondary">
                  {feature.description}
                </p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 px-4 sm:px-6 lg:px-8 bg-surface/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-text-primary mb-4">
              How It Works
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mx-auto">
              From upload to insight in four simple steps.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {howItWorks.map((step, idx) => (
              <div key={idx} className="relative">
                {idx < howItWorks.length - 1 && (
                  <div className="hidden lg:block absolute top-8 left-full w-full h-0.5 bg-gradient-to-r from-primary-600/50 to-transparent -ml-4" />
                )}
                <div className="text-5xl font-bold text-primary-600/20 mb-4">{step.step}</div>
                <h3 className="text-xl font-semibold text-text-primary mb-2">{step.title}</h3>
                <p className="text-sm text-text-secondary">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <Card variant="glass" padding="lg" className="text-center">
            <Shield className="w-12 h-12 text-primary-400 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-text-primary mb-4">
              Evidence-Based Methodology
            </h3>
            <p className="text-text-secondary mb-6">
              CreativePulse uses Mann–Whitney U tests and rank-biserial effect sizes to identify associations
              between visual characteristics and performance metrics. All insights include statistical evidence
              tiers and clear disclaimers.
            </p>
            <div className="inline-flex items-center space-x-2 text-sm text-text-tertiary bg-surface-elevated px-4 py-2 rounded-lg">
              <Check className="w-4 h-4 text-success-400" />
              <span>Associations, not causation — your data, your insights</span>
            </div>
          </Card>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-text-primary mb-4">
            Find Your Creative DNA
          </h2>
          <p className="text-lg text-text-secondary mb-8">
            Start analyzing your creative performance today.
          </p>
          <Button size="lg" onClick={handleStartAnalyzing}>
            Start Analyzing
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center text-sm text-text-tertiary">
          <p>© 2026 CreativePulse AI. AI-powered creative intelligence for marketing teams.</p>
        </div>
      </footer>
    </div>
  )
}
