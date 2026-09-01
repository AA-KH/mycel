'use client'

import { useState, type FormEvent } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  fetchSetupStatus,
  loginUser,
  registerUser,
  saveSession,
} from '@/lib/auth'

type Mode = 'login' | 'register'

function FieldLabel({ children, htmlFor }: { children: React.ReactNode; htmlFor: string }) {
  return (
    <label
      htmlFor={htmlFor}
      className="mb-2 block font-mono text-[10px] uppercase tracking-widest text-accent"
    >
      {children}
    </label>
  )
}

const inputClasses =
  'w-full border-2 border-foreground bg-background px-4 py-3.5 text-base placeholder:text-muted-foreground/60 focus:bg-card focus:outline-none focus:ring-2 focus:ring-accent lg:py-4'

/**
 * `next` is an optional in-app path to return to after a successful sign-in
 * (e.g. an operator bounced off /setup). Ignored unless it is a relative path,
 * so it can never be used as an open redirect.
 */
export function LoginForm({ next }: { next?: string }) {
  const router = useRouter()
  const safeNext = next && /^\/(?!\/)/.test(next) ? next : null
  const [mode, setMode] = useState<Mode>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [statusLine, setStatusLine] = useState<string | null>(null)

  function switchMode(next: Mode) {
    if (next === mode) return
    setMode(next)
    setError(null)
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (pending) return
    setError(null)

    if (mode === 'register' && name.trim().length < 2) {
      setError('Operator name must be at least 2 characters')
      return
    }
    if (password.length < 8) {
      setError('Passcode must be at least 8 characters')
      return
    }

    setPending(true)
    setStatusLine('Verifying credentials')
    try {
      const session =
        mode === 'login'
          ? await loginUser(email.trim(), password)
          : await registerUser(name.trim(), email.trim(), password)
      saveSession(session)

      // Returning operators already have a network — skip straight to it.
      setStatusLine('Locating your network')
      const status =
        mode === 'login'
          ? await fetchSetupStatus(session.access_token)
          : { has_setup: false, setup: null }

      if (safeNext) {
        setStatusLine('Resuming where you left off')
        router.push(safeNext)
      } else if (status.has_setup) {
        setStatusLine('Network found — entering mission control')
        router.push('/control')
      } else {
        setStatusLine('No network on record — starting setup')
        router.push('/setup')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed')
      setStatusLine(null)
      setPending(false)
    }
  }

  return (
    <div className="w-full border-4 border-foreground bg-card pixel-shadow">
      {/* terminal title bar */}
      <div className="flex items-center justify-between border-b-4 border-foreground bg-primary px-4 py-3 lg:px-5">
        <p className="font-mono text-[10px] uppercase tracking-widest text-primary-foreground">
          MYCE<span className="text-secondary">L</span> // AUTH.SYS
        </p>
        <div className="flex items-center gap-1.5" aria-hidden="true">
          <span className="h-2.5 w-2.5 border-2 border-primary-foreground/70 bg-secondary" />
          <span className="h-2.5 w-2.5 border-2 border-primary-foreground/70 bg-accent" />
          <span className="h-2.5 w-2.5 border-2 border-primary-foreground/70 bg-card" />
        </div>
      </div>

      {/* mode tabs */}
      <div
        className="grid grid-cols-2 border-b-4 border-foreground"
        role="tablist"
        aria-label="Authentication mode"
      >
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'login'}
          onClick={() => switchMode('login')}
          className={cn(
            'border-r-2 border-foreground px-4 py-4 font-mono text-[10px] uppercase tracking-widest transition-colors',
            mode === 'login'
              ? 'bg-secondary text-secondary-foreground'
              : 'bg-card text-muted-foreground hover:bg-muted',
          )}
        >
          Sign In
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'register'}
          onClick={() => switchMode('register')}
          className={cn(
            'border-l-2 border-foreground px-4 py-4 font-mono text-[10px] uppercase tracking-widest transition-colors',
            mode === 'register'
              ? 'bg-secondary text-secondary-foreground'
              : 'bg-card text-muted-foreground hover:bg-muted',
          )}
        >
          New Operator
        </button>
      </div>

      <form
        onSubmit={handleSubmit}
        className="step-enter flex flex-col gap-5 p-6 lg:p-8"
        key={mode}
      >
        <p className="font-mono text-[10px] uppercase leading-relaxed tracking-widest text-accent">
          {mode === 'login'
            ? '> Verify credentials to resume'
            : '> Register a new operator'}
          <span className="blink">_</span>
        </p>

        {mode === 'register' ? (
          <div>
            <FieldLabel htmlFor="auth-name">Operator Name</FieldLabel>
            <input
              id="auth-name"
              type="text"
              autoComplete="name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ada Lovelace"
              className={inputClasses}
            />
          </div>
        ) : null}

        <div>
          <FieldLabel htmlFor="auth-email">Email</FieldLabel>
          <input
            id="auth-email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="operator@mycel.network"
            className={inputClasses}
          />
        </div>

        <div>
          <FieldLabel htmlFor="auth-password">Passcode</FieldLabel>
          <div className="flex">
            <input
              id="auth-password"
              type={showPassword ? 'text' : 'password'}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className={cn(inputClasses, 'border-r-0')}
            />
            <button
              type="button"
              onClick={() => setShowPassword((s) => !s)}
              aria-pressed={showPassword}
              aria-label={showPassword ? 'Hide passcode' : 'Show passcode'}
              className="shrink-0 border-2 border-foreground bg-muted px-4 font-mono text-[9px] uppercase tracking-widest transition-colors hover:bg-secondary"
            >
              {showPassword ? 'Hide' : 'Show'}
            </button>
          </div>
          {mode === 'register' ? (
            <p className="mt-2 text-sm leading-snug text-muted-foreground">
              Minimum 8 characters.
            </p>
          ) : null}
        </div>

        {error ? (
          <p
            role="alert"
            className="border-2 border-destructive bg-accent/10 px-4 py-3 font-mono text-[10px] uppercase leading-relaxed tracking-wider text-destructive"
          >
            [!] {error}
          </p>
        ) : null}

        {pending && statusLine ? (
          <p
            aria-live="polite"
            className="border-2 border-foreground bg-primary px-4 py-3 font-mono text-[10px] uppercase leading-relaxed tracking-wider text-secondary"
          >
            {'> '}
            {statusLine}
            <span className="blink">_</span>
          </p>
        ) : null}

        <button
          type="submit"
          disabled={pending}
          className={cn(
            'mt-1 border-2 border-foreground bg-accent px-6 py-4 font-mono text-[11px] uppercase tracking-widest text-accent-foreground pixel-shadow-sm transition-colors lg:py-5',
            'hover:bg-primary hover:text-primary-foreground',
            'active:translate-x-[3px] active:translate-y-[3px] active:shadow-none',
            'disabled:cursor-not-allowed disabled:opacity-40',
          )}
        >
          {pending ? (
            <>
              Working<span className="blink">_</span>
            </>
          ) : mode === 'login' ? (
            'Resume Network'
          ) : (
            'Create Operator'
          )}
        </button>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t-2 border-dashed border-foreground/30 pt-5">
          <Link
            href="/"
            className="whitespace-nowrap font-mono text-[10px] uppercase tracking-widest text-muted-foreground transition-colors hover:text-accent"
          >
            {'< Back to boot'}
          </Link>
          <button
            type="button"
            onClick={() => switchMode(mode === 'login' ? 'register' : 'login')}
            className="whitespace-nowrap font-mono text-[10px] uppercase tracking-widest text-accent transition-colors hover:text-foreground"
          >
            {mode === 'login' ? 'No account? Register >' : 'Have access? Sign in >'}
          </button>
        </div>
      </form>
    </div>
  )
}
