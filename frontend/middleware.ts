import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { jwtVerify } from 'jose'

const JWT_SECRET = new TextEncoder().encode(
  process.env.ADMIN_JWT_SECRET ||
  'ai-web-auditor-super-secret-key-change-in-production-min-32-chars'
)

export async function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value

  if (!token) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('returnUrl', request.nextUrl.pathname)
    return NextResponse.redirect(loginUrl)
  }

  try {
    const { payload } = await jwtVerify(token, JWT_SECRET)
    if (payload.role !== 'admin') {
      return NextResponse.redirect(new URL('/', request.url))
    }
  } catch {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('returnUrl', request.nextUrl.pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/admin/:path*'],
}
