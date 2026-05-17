'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { User, LogOut, CreditCard, Settings, Menu } from 'lucide-react'
import { useAuth } from '@/lib/auth'

export function Navigation() {
  const pathname = usePathname()
  const router = useRouter()
  const { user, isAuthenticated, isLoading, checkAuth, logout } = useAuth()

  useEffect(() => {
    checkAuth().catch(err => console.error('Auth check failed:', err))
  }, [])

  const handleLogout = async () => {
    try {
      await logout()
      router.push('/')
    } catch (err) {
      console.error('Logout failed:', err)
      router.push('/')
    }
  }

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="min-h-[44px] self-stretch inline-flex items-center text-xl font-bold text-primary-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded">
              AI Web Auditor
            </Link>
          </div>

          <div className="flex items-center space-x-4">
            <Link
              href="/"
              className={`min-h-[44px] min-w-[44px] inline-flex items-center px-2 py-2.5 text-gray-600 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded ${pathname === '/' ? 'text-primary-600' : ''}`}
            >
              Audit Nou
            </Link>

            {isAuthenticated && (
              <>
                <Link
                  href="/history"
                  className={`min-h-[44px] inline-flex items-center px-2 py-2.5 text-gray-600 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded ${pathname === '/history' ? 'text-primary-600' : ''}`}
                >
                  Istoric
                </Link>

                <Link
                  href="/pricing"
                  className={`min-h-[44px] inline-flex items-center px-2 py-2.5 text-gray-600 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded ${pathname === '/pricing' ? 'text-primary-600' : ''}`}
                >
                  Preturi
                </Link>
              </>
            )}

            {!isLoading && (
              <>
                {isAuthenticated ? (
                  <div className="flex items-center space-x-3 ml-4 pl-4 border-l">
                    {user != null && user.role === 'admin' && (
                      <Link
                        href="/admin"
                        className={`min-h-[44px] min-w-[44px] inline-flex items-center justify-center text-gray-600 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded ${pathname.startsWith('/admin') ? 'text-primary-600' : ''}`}
                        aria-label="Admin panel"
                      >
                        <Settings className="w-5 h-5" />
                      </Link>
                    )}

                    <div className="flex items-center gap-2 text-sm">
                      <CreditCard className="w-4 h-4 text-gray-400" />
                      <span className="font-medium text-primary-600">{user?.credits}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                        <User className="w-4 h-4 text-primary-600" />
                      </div>
                      <span className="text-sm text-gray-700 hidden sm:block">
                        {user?.name || user?.email?.split('@')[0]}
                      </span>
                    </div>

                    <button
                      onClick={handleLogout}
                      className="min-h-[44px] min-w-[44px] inline-flex items-center justify-center text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
                      title="Deconectare"
                      aria-label="Deconectare"
                    >
                      <LogOut className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center space-x-3 ml-4">
                    <Link
                      href="/login"
                      className="min-h-[44px] min-w-[44px] inline-flex items-center px-2 py-2.5 text-gray-600 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded"
                    >
                      Autentificare
                    </Link>
                    <Link
                      href="/register"
                      className="min-h-[44px] inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"
                    >
                      Inregistrare
                    </Link>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
