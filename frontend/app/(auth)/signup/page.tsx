'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import { getErrorMessage } from '@/lib/apiError'
import { Sparkles, CheckCircle2, ArrowRight, Eye, EyeOff } from 'lucide-react'
import { Button, Input } from '@/components/ui'

export default function SignupPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long')
      return
    }

    setLoading(true)

    try {
      await api.signup(email, password)
      router.push('/dashboard')
    } catch (err) {
      setError(getErrorMessage(err) || 'Signup failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const features = [
    'AI-Powered Insights',
    'Creative DNA Analysis',
    'Performance Tracking',
    'Asset Repurposing',
  ]

  return (
    <div className="min-h-screen flex bg-background">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-600/10 via-background to-secondary-600/10 relative overflow-hidden">
        <div className="absolute inset-0 noise-bg" />
        <div className="absolute top-20 left-20 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-secondary-500/20 rounded-full blur-3xl" />
        
        <div className="relative z-10 flex flex-col justify-center px-16 w-full">
          <Link href="/" className="flex items-center space-x-2 mb-16 group">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-text-primary group-hover:text-primary-400 transition-colors">
              CreativePulse AI
            </span>
          </Link>

          <div className="mb-12">
            <h1 className="text-4xl font-bold text-text-primary mb-4 leading-tight">
              Start Your Creative Intelligence Journey
            </h1>
            <p className="text-lg text-text-secondary">
              Join marketing teams using AI-powered insights to optimize their campaigns.
            </p>
          </div>

          <div className="space-y-4">
            {features.map((feature, idx) => (
              <div key={idx} className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-success-600/20 rounded-lg flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 className="w-5 h-5 text-success-400" />
                </div>
                <span className="text-text-secondary">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Side - Signup Form */}
      <div className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-12">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden mb-8 text-center">
            <Link href="/" className="inline-flex items-center space-x-2 group">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold text-text-primary group-hover:text-primary-400 transition-colors">
                CreativePulse AI
              </span>
            </Link>
          </div>

          <div className="mb-8">
            <h2 className="text-3xl font-bold text-text-primary mb-2">Create account</h2>
            <p className="text-text-secondary">
              Start analyzing your creative performance today
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-danger-600/10 border border-danger-600/30 text-danger-400 px-4 py-3 rounded-xl text-sm">
                {error}
              </div>
            )}

            <Input
              label="Email address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />

            <div>
              <Input
                label="Password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Create a strong password"
                required
                autoComplete="new-password"
                helperText="At least 8 characters"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-[38px] text-text-tertiary hover:text-text-secondary transition-colors"
              >
                {showPassword ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
              </button>
            </div>

            <div>
              <Input
                label="Confirm password"
                type={showConfirmPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm your password"
                required
                autoComplete="new-password"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-[38px] text-text-tertiary hover:text-text-secondary transition-colors"
              >
                {showConfirmPassword ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
              </button>
            </div>

            <Button 
              type="submit" 
              fullWidth 
              size="lg"
              loading={loading}
              disabled={loading}
            >
              {loading ? 'Creating account...' : (
                <>
                  Create Account
                  <ArrowRight className="w-5 h-5 ml-2" />
                </>
              )}
            </Button>
          </form>

          <div className="mt-8 pt-6 border-t border-border text-center">
            <p className="text-sm text-text-secondary">
              Already have an account?{' '}
              <Link 
                href="/login" 
                className="text-primary-400 hover:text-primary-300 font-semibold transition-colors"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
