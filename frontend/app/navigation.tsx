'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { User, LogOut, CreditCard, Settings, Menu } from 'lucide-react'
import { useAuth } from '@/lib/auth'

export function Navigation() {
  const pathname = usePathname()
  const { user, isAuthenticated, isLoading, checkAuth, logout } = useAuth()

  useEffect(() => {
    checkAuth()
  }, [])

  const handleLogout = async () => {
    await logout()
    window.location.href = '/'
  }

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="text-xl font-bold text-primary-600">
              AI Web Auditor
            </Link>
          </div>

          <div className="flex items-center space-x-4">
            <Link
              href="/"
              className={`text-gray-600 hover:text-gray-900 ${pathname === '/' ? 'text-primary-600' : ''}`}
            >
              Audit Nou
            </Link>

            {isAuthenticated && (
              <>
                <Link
                  href="/history"
                  className={`text-gray-600 hover:text-gray-900 ${pathname === '/history' ? 'text-primary-600' : ''}`}
                >
                  Istoric
                </Link>

                <Link
                  href="/pricing"
                  className={`text-gray-600 hover:text-gray-900 ${pathname === '/pricing' ? 'text-primary-600' : ''}`}
                >
                  Preturi
                </Link>
              </>
            )}

            {!isLoading && (
              <>
                {isAuthenticated ? (
                  <div className="flex items-center space-x-3 ml-4 pl-4 border-l">
                    {user?.role === 'admin' && (
                      <Link
                        href="/admin"
                        className={`text-gray-600 hover:text-gray-900 ${pathname.startsWith('/admin') ? 'text-primary-600' : ''}`}
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
                      className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full"
                      title="Deconectare"
                    >
                      <LogOut className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center space-x-3 ml-4">
                    <Link
                      href="/login"
                      className="text-gray-600 hover:text-gray-900"
                    >
                      Autentificare
                    </Link>
                    <Link
                      href="/register"
                      className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
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
