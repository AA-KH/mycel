/**
 * Client helpers for the MYCEL FastAPI auth service.
 * Backend routes live at {API_URL}/api/auth/(login|register) and return a JWT.
 * Set NEXT_PUBLIC_API_URL to point at the backend; defaults to localhost:8000.
 */

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const TOKEN_KEY = 'mycel_access_token'
const USER_KEY = 'mycel_user'

export type AuthUser = {
  id: string
  email: string
  name: string | null
  is_admin: boolean
}

export type TokenResponse = {
  access_token: string
  token_type: string
  user: AuthUser
}

async function postAuth(path: string, body: Record<string, string>): Promise<TokenResponse> {
  let res: Response
  try {
    res = await fetch(`${API_URL}/api/auth/${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    throw new Error('LINK OFFLINE — could not reach the MYCEL backend')
  }

  if (!res.ok) {
    let detail = 'Authentication failed'
    try {
      const data = await res.json()
      if (typeof data?.detail === 'string') detail = data.detail
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail)
  }

  return (await res.json()) as TokenResponse
}

export function loginUser(email: string, password: string) {
  return postAuth('login', { email, password })
}

export function registerUser(name: string, email: string, password: string) {
  return postAuth('register', { name, email, password })
}

export function saveSession(session: TokenResponse) {
  sessionStorage.setItem(TOKEN_KEY, session.access_token)
  sessionStorage.setItem(USER_KEY, JSON.stringify(session.user))
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return sessionStorage.getItem(TOKEN_KEY)
}

export function getUser(): AuthUser | null {
  if (typeof window === 'undefined') return null
  const raw = sessionStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthUser
  } catch {
    return null
  }
}

export function clearSession() {
  sessionStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(USER_KEY)
}
