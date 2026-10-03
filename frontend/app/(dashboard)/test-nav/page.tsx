'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function TestNavPage() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-text-primary mb-8">
          Navigation Test Page
        </h1>

        <div className="bg-surface border border-border rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-text-primary mb-4">
            Test 1: Next.js Link Components
          </h2>
          <div className="space-y-3">
            <Link 
              href="/dashboard"
              className="block px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors cursor-pointer"
            >
              → Go to Dashboard (Link)
            </Link>
            <Link 
              href="/library"
              className="block px-4 py-3 bg-secondary-600 text-white rounded-lg hover:bg-secondary-700 transition-colors cursor-pointer"
            >
              → Go to Library (Link)
            </Link>
            <Link 
              href="/new"
              className="block px-4 py-3 bg-success-600 text-white rounded-lg hover:bg-success-700 transition-colors cursor-pointer"
            >
              → Go to New Analysis (Link)
            </Link>
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-text-primary mb-4">
            Test 2: useRouter Navigation
          </h2>
          <div className="space-y-3">
            <button
              onClick={() => router.push('/dashboard')}
              className="block w-full text-left px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors cursor-pointer"
            >
              → Go to Dashboard (router.push)
            </button>
            <button
              onClick={() => router.push('/library')}
              className="block w-full text-left px-4 py-3 bg-secondary-600 text-white rounded-lg hover:bg-secondary-700 transition-colors cursor-pointer"
            >
              → Go to Library (router.push)
            </button>
            <button
              onClick={() => router.push('/new')}
              className="block w-full text-left px-4 py-3 bg-success-600 text-white rounded-lg hover:bg-success-700 transition-colors cursor-pointer"
            >
              → Go to New Analysis (router.push)
            </button>
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-6">
          <h2 className="text-xl font-semibold text-text-primary mb-4">
            Test 3: Regular Anchor Tags
          </h2>
          <div className="space-y-3">
            <a 
              href="/dashboard"
              className="block px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors cursor-pointer"
            >
              → Go to Dashboard (anchor)
            </a>
            <a 
              href="/library"
              className="block px-4 py-3 bg-secondary-600 text-white rounded-lg hover:bg-secondary-700 transition-colors cursor-pointer"
            >
              → Go to Library (anchor)
            </a>
            <a 
              href="/new"
              className="block px-4 py-3 bg-success-600 text-white rounded-lg hover:bg-success-700 transition-colors cursor-pointer"
            >
              → Go to New Analysis (anchor)
            </a>
          </div>
        </div>

        <div className="mt-6 p-4 bg-warning-600/10 border border-warning-600/30 rounded-lg">
          <p className="text-sm text-text-secondary">
            <strong>Instructions:</strong> Try clicking each button/link above. 
            All three methods should navigate to the respective pages. 
            If some work and others don't, we'll know which navigation method is problematic.
          </p>
        </div>
      </div>
    </div>
  )
}
