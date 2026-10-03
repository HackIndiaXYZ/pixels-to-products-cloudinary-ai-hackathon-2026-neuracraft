'use client'

import { ReactNode, useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  LayoutDashboard,
  Image,
  Dna,
  TrendingUp,
  Wand2,
  MessageSquare,
  FileText,
  Settings,
  LogOut,
  Menu,
  X,
  Sparkles,
  Plus,
  User
} from 'lucide-react'
import { api } from '@/lib/api'

interface DashboardLayoutProps {
  children: ReactNode
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname()
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [user, setUser] = useState<{ email: string; id: number } | null>(null)
  const [authChecked, setAuthChecked] = useState(false)

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userData = await api.getCurrentUser()
        setUser(userData)
      } catch {
        // Token invalid or missing — redirect to login
        router.replace('/login')
      } finally {
        setAuthChecked(true)
      }
    }
    fetchUser()
  }, [router])

  const handleLogout = () => {
    api.logout()
  }

  const navigation = [
    {
      name: 'Overview',
      href: '/dashboard',
      icon: LayoutDashboard,
      description: 'Campaign metrics and insights'
    },
    {
      name: 'New Analysis',
      href: '/new',
      icon: Plus,
      description: 'Create a new analysis',
      highlight: true
    },
    {
      name: 'Creative Library',
      href: '/library',
      icon: Image,
      description: 'Browse your creative assets'
    },
    {
      name: 'Creative DNA',
      href: '/dna',
      icon: Dna,
      description: 'Visual pattern intelligence'
    },
    {
      name: 'Performance',
      href: '/performance',
      icon: TrendingUp,
      description: 'Campaign performance data'
    },
    {
      name: 'Repurpose',
      href: '/repurpose',
      icon: Wand2,
      description: 'Transform creative formats'
    },
    {
      name: 'AI Assistant',
      href: '/assistant',
      icon: MessageSquare,
      description: 'Ask CreativePulse AI'
    },
    {
      name: 'Reports',
      href: '/reports',
      icon: FileText,
      description: 'Export and share insights'
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Settings,
      description: 'Account and preferences'
    },
  ]

  const Sidebar = ({ mobile = false }) => (
    <div className={`flex flex-col h-full ${mobile ? 'bg-background' : 'bg-background-secondary'} border-r border-border relative z-10`} style={{ position: 'relative', zIndex: 100 }}>
      {/* Logo */}
      <div className="flex items-center h-16 px-6 border-b border-border">
        <Link href="/dashboard" className="flex items-center space-x-2 group">
          <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center shadow-lg shadow-primary-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-bold text-text-primary group-hover:text-primary-400 transition-colors">
            CreativePulse
          </span>
        </Link>
        {mobile && (
          <button
            onClick={() => setSidebarOpen(false)}
            className="ml-auto text-text-tertiary hover:text-text-primary"
            aria-label="Close sidebar"
          >
            <X className="w-6 h-6" />
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-custom relative z-10" aria-label="Main navigation">
        {navigation.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href

          return (
            <Link
              key={item.name}
              href={item.href}
              prefetch={true}
              onClick={(e) => {
                console.log('Navigation clicked:', item.name, item.href)
                if (mobile) setSidebarOpen(false)
              }}
              aria-current={isActive ? 'page' : undefined}
              aria-label={`Navigate to ${item.name}`}
              tabIndex={0}
              className={`
                group flex items-center px-3 py-2.5 rounded-lg transition-all duration-200 cursor-pointer relative z-10
                ${isActive
                  ? 'bg-primary-600/10 text-primary-400 shadow-sm'
                  : 'text-text-secondary hover:bg-surface-secondary hover:text-text-primary'
                }
                ${item.highlight && !isActive ? 'border border-primary-600/30' : ''}
              `}
              style={{ cursor: 'pointer', userSelect: 'none', WebkitTapHighlightColor: 'transparent', position: 'relative' }}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 transition-colors ${
                isActive ? 'text-primary-400' : 'text-text-tertiary group-hover:text-text-primary'
              }`} />
              <span className="ml-3 font-medium text-sm">{item.name}</span>
            </Link>
          )
        })}
      </nav>

      {/* User Section */}
      <div className="p-4 border-t border-border">
        {user && (
          <div className="mb-3 px-3 py-2.5 bg-surface-secondary rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-full flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-text-tertiary">Signed in as</p>
                <p className="text-sm font-medium text-text-primary truncate">{user.email}</p>
              </div>
            </div>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="w-full flex items-center space-x-3 px-3 py-2.5 text-text-secondary hover:bg-surface-secondary hover:text-text-primary rounded-lg transition-all"
          aria-label="Log out"
        >
          <LogOut className="w-5 h-5" />
          <span className="font-medium text-sm">Logout</span>
        </button>
      </div>
    </div>
  )

  // While auth is being checked, show a minimal loading screen
  if (!authChecked) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center animate-pulse">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <p className="text-text-tertiary text-sm">Loading…</p>
        </div>
      </div>
    )
  }

  // If auth failed, render nothing (router.replace('/login') is already called)
  if (!user) return null

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
          <div className="fixed inset-y-0 left-0 z-50 w-72 lg:hidden">
            <Sidebar mobile />
          </div>
        </>
      )}

      {/* Desktop sidebar */}
      <aside className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col z-50">
        <Sidebar />
      </aside>

      {/* Main content */}
      <div className="lg:pl-64 noise-bg">
        {/* Top header */}
        <header className="sticky top-0 z-20 bg-background-secondary/80 backdrop-blur-xl border-b border-border">
          <div className="flex items-center h-16 px-4 lg:px-8">
            {/* Mobile menu button */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="mr-4 text-text-tertiary hover:text-text-primary lg:hidden"
              aria-label="Open sidebar"
            >
              <Menu className="w-6 h-6" />
            </button>

            <div className="flex-1">
              <h1 className="text-lg font-semibold text-text-primary lg:hidden">
                CreativePulse
              </h1>
            </div>

            {/* Header actions */}
            <div className="flex items-center space-x-3">
              <div className="hidden lg:flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="min-h-[calc(100vh-4rem)] p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
