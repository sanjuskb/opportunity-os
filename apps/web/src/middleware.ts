import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';
import { sanitizeNextPath } from '@/lib/auth/redirect';
import { isProtectedPath, shouldFailClosedWithoutConfig } from '@/lib/auth/route-guard';
import { getSupabasePublicConfig } from '@/lib/supabase/env';

export async function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const protectedRoute = isProtectedPath(pathname);
  const config = getSupabasePublicConfig();

  if (!config) {
    if (protectedRoute && shouldFailClosedWithoutConfig()) {
      const loginUrl = request.nextUrl.clone();
      loginUrl.pathname = '/login';
      loginUrl.search = '';
      loginUrl.searchParams.set('error', 'auth_unconfigured');
      loginUrl.searchParams.set('next', `${pathname}${search}`);
      return NextResponse.redirect(loginUrl);
    }
    return NextResponse.next({ request });
  }

  let response = NextResponse.next({ request });

  const supabase = createServerClient(config.url, config.anonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        cookiesToSet.forEach(({ name, value, options }) =>
          response.cookies.set(name, value, options)
        );
      },
    },
  });

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user && protectedRoute) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = '/login';
    loginUrl.search = '';
    loginUrl.searchParams.set('next', `${pathname}${search}`);
    return NextResponse.redirect(loginUrl);
  }

  if (user && pathname === '/login') {
    const safeNext = sanitizeNextPath(request.nextUrl.searchParams.get('next'), '/opportunities');
    const targetUrl = new URL(safeNext, request.nextUrl.origin);
    return NextResponse.redirect(targetUrl);
  }

  return response;
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
