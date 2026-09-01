'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { PixelButton, PixelChip, ProgressSquares } from '@/components/pixel/pixel-ui'
import { PixelWorld } from '@/components/pixel/pixel-scene'
import { fetchSetupStatus, getToken, saveSetup } from '@/lib/auth'
import {
  EMPTY_DATA,
  StepBudget,
  StepBusinessType,
  StepConstraints,
  StepPriorities,
  StepScale,
  StepSupplying,
  StepTimeline,
  StepUpload,
  StepWhere,
  type SetupData,
} from './steps'

const STEPS = [
  { kicker: 'What are you?', component: StepBusinessType },
  { kicker: 'What are you supplying?', component: StepSupplying },
  { kicker: 'Where?', component: StepWhere },
  { kicker: 'How much?', component: StepScale },
  { kicker: 'By when?', component: StepTimeline },
  { kicker: 'At what cost?', component: StepBudget },
  { kicker: 'What matters?', component: StepPriorities },
  { kicker: 'What do we already know?', component: StepConstraints },
  { kicker: 'Upload your data', component: StepUpload },
]

const TOTAL = STEPS.length
const pad = (n: number) => String(n).padStart(2, '0')

/** Gate result: are we allowed to run the wizard for this operator? */
type Gate =
  | { state: 'checking' }
  | { state: 'no-session' }
  | { state: 'has-network' }
  | { state: 'open' }

export function SetupWizard() {
  const [step, setStep] = useState(0)
  const [done, setDone] = useState(false)
  const [data, setData] = useState<SetupData>(EMPTY_DATA)
  const [gate, setGate] = useState<Gate>({ state: 'checking' })
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  // Require a session, and skip the wizard if a network already exists.
  useEffect(() => {
    let active = true
    const token = getToken()

    if (!token) {
      setGate({ state: 'no-session' })
      return
    }

    fetchSetupStatus(token).then((status) => {
      if (!active) return
      setGate({ state: status.has_setup ? 'has-network' : 'open' })
    })

    return () => {
      active = false
    }
  }, [])

  const update = (patch: Partial<SetupData>) => setData((d) => ({ ...d, ...patch }))

  const canContinue =
    step !== 0 || data.businessType !== '' || data.businessDescription.trim().length > 0

  /** Persist the answers, then reveal the compiling screen. */
  async function handleBuild() {
    if (saving) return
    setSaveError(null)
    setSaving(true)

    const token = getToken()
    if (!token) {
      setGate({ state: 'no-session' })
      return
    }

    try {
      await saveSetup(token, data)
      setDone(true)
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Could not save your setup')
    } finally {
      setSaving(false)
    }
  }

  if (gate.state === 'checking') {
    return <GateScreen variant="checking" />
  }

  if (gate.state === 'no-session') {
    return <GateScreen variant="no-session" />
  }

  if (gate.state === 'has-network') {
    return <GateScreen variant="has-network" onRebuild={() => setGate({ state: 'open' })} />
  }

  if (done) {
    return <DoneScreen data={data} />
  }

  const Current = STEPS[step].component

  return (
    <main className="relative flex h-svh flex-col overflow-hidden bg-gradient-to-b from-[#bcd8ce] via-background to-[#eec98f]">
      {/* animated pixel world behind everything */}
      <PixelWorld harborHeight="h-[14svh] min-h-28" />

      {/* header */}
      <header className="relative z-10 flex shrink-0 items-start justify-between px-4 pb-2 pt-4 md:px-8 md:pt-5">
        <PixelChip variant="yellow">{`Step ${pad(step + 1)} of ${pad(TOTAL)}`}</PixelChip>
        <div className="flex items-center gap-3">
          <PixelChip variant="cream" className="hidden sm:inline-block">
            Building your network
          </PixelChip>
          <Link
            href="/"
            className="border-2 border-foreground bg-card px-3 py-1.5 font-mono text-[9px] uppercase tracking-widest pixel-shadow-sm hover:bg-muted"
          >
            Exit
          </Link>
        </div>
      </header>

      {/* panel region — fills remaining height, never overflows the page */}
      <div className="relative z-10 mx-auto flex w-full max-w-3xl min-h-0 flex-1 flex-col px-4 pb-[10svh] pt-1 sm:px-6">
        <h1 className="mb-3 shrink-0 font-mono text-xs uppercase tracking-widest text-foreground sm:text-sm">
          {`Step ${step + 1} of ${TOTAL} · `}
          <span className="text-accent">{STEPS[step].kicker}</span>
        </h1>

        <div className="flex min-h-0 flex-1 flex-col border-4 border-foreground bg-card/95 pixel-shadow backdrop-blur-[1px]">
          {/* only this area scrolls, with a pixel scrollbar */}
          <div key={step} className="step-enter pixel-scroll min-h-0 flex-1 overflow-y-auto p-5 sm:p-7">
            <Current data={data} update={update} />
          </div>

          {saveError ? (
            <p
              role="alert"
              className="shrink-0 border-t-2 border-destructive bg-accent/10 px-5 py-3 font-mono text-[10px] uppercase leading-relaxed tracking-wider text-destructive sm:px-7"
            >
              [!] {saveError}
            </p>
          ) : null}

          {/* nav pinned inside the panel, always visible */}
          <div className="flex shrink-0 items-center justify-between gap-4 border-t-2 border-dashed border-foreground/30 bg-card px-5 py-3.5 sm:px-7">
            <ProgressSquares total={TOTAL} current={step} />
            <div className="flex gap-3">
              {step > 0 ? (
                <PixelButton variant="ghost" onClick={() => setStep((s) => s - 1)}>
                  Back
                </PixelButton>
              ) : null}
              {step < STEPS.length - 1 ? (
                <PixelButton onClick={() => setStep((s) => s + 1)} disabled={!canContinue}>
                  Next
                </PixelButton>
              ) : (
                <PixelButton variant="orange" onClick={handleBuild} disabled={saving}>
                  {saving ? (
                    <>
                      Saving<span className="blink">_</span>
                    </>
                  ) : (
                    'Build my network'
                  )}
                </PixelButton>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}

/**
 * Pre-wizard states: verifying the session, no session at all, or an
 * operator who already has a network and shouldn't be re-onboarded.
 */
function GateScreen({
  variant,
  onRebuild,
}: {
  variant: 'checking' | 'no-session' | 'has-network'
  onRebuild?: () => void
}) {
  const copy = {
    checking: {
      chip: 'Verifying operator',
      kicker: '> Reading your credentials_',
      title: 'Checking for an existing network',
      body: 'Hold while MYCEL looks up whether your blueprints are already on record.',
    },
    'no-session': {
      chip: 'Session required',
      kicker: '> No operator session found_',
      title: 'Sign in to build your network',
      body: 'The setup wizard writes to your operator record, so we need to know who you are first.',
    },
    'has-network': {
      chip: 'Network on record',
      kicker: '> Blueprints already exist_',
      title: 'Your network is already built',
      body: 'You have completed setup before. Head straight to mission control, or rebuild from scratch to start over.',
    },
  }[variant]

  return (
    <main className="relative flex h-svh flex-col overflow-hidden bg-gradient-to-b from-[#bcd8ce] via-background to-[#eec98f]">
      <PixelWorld harborHeight="h-[18svh] min-h-32" />

      <header className="relative z-10 flex shrink-0 items-start justify-between p-4 md:p-6">
        <div className="boot-in">
          <PixelChip variant={variant === 'has-network' ? 'orange' : 'yellow'}>
            {copy.chip}
          </PixelChip>
        </div>
        <Link
          href="/"
          className="boot-in boot-delay-1 border-2 border-foreground bg-card px-3 py-1.5 font-mono text-[9px] uppercase tracking-widest pixel-shadow-sm hover:bg-muted"
        >
          Exit
        </Link>
      </header>

      <div className="relative z-10 mx-auto flex w-full max-w-xl min-h-0 flex-1 flex-col items-center justify-center px-4 pb-[14svh]">
        <div className="boot-in boot-delay-2 w-full border-4 border-foreground bg-card/95 pixel-shadow">
          <div className="flex items-center justify-between border-b-4 border-foreground bg-primary px-4 py-2.5">
            <p className="font-mono text-[9px] uppercase tracking-widest text-primary-foreground">
              MYCE<span className="text-secondary">L</span> // SETUP.SYS
            </p>
            <span className="h-2 w-2 bg-secondary node-blink" aria-hidden="true" />
          </div>

          <div className="p-6 sm:p-8">
            <p
              aria-live="polite"
              className="font-mono text-[10px] uppercase tracking-widest text-accent"
            >
              {copy.kicker}
              <span className="blink">|</span>
            </p>
            <h1 className="mt-3 text-balance font-mono text-base uppercase leading-relaxed tracking-wider sm:text-xl">
              {copy.title}
            </h1>
            <p className="mt-3 text-pretty text-sm leading-relaxed text-muted-foreground">
              {copy.body}
            </p>

            {variant === 'checking' ? (
              <div
                className="mt-6 flex items-center gap-1.5"
                role="status"
                aria-label="Checking your operator record"
              >
                {[0, 1, 2, 3, 4, 5].map((i) => (
                  <span
                    key={i}
                    className="h-3 w-3 border-2 border-foreground bg-secondary node-blink"
                    style={{ animationDelay: `${i * 0.12}s` }}
                  />
                ))}
              </div>
            ) : null}

            {variant === 'no-session' ? (
              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href="/login?next=/setup"
                  className="press-pulse border-2 border-foreground bg-accent px-6 py-3 font-mono text-[10px] uppercase tracking-widest text-accent-foreground hover:bg-primary hover:text-primary-foreground"
                >
                  Operator login
                </Link>
                <Link
                  href="/"
                  className="border-2 border-foreground bg-card px-6 py-3 font-mono text-[10px] uppercase tracking-widest text-foreground pixel-shadow-sm hover:bg-muted"
                >
                  Back to start
                </Link>
              </div>
            ) : null}

            {variant === 'has-network' ? (
              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href="/control"
                  className="press-pulse border-2 border-foreground bg-accent px-6 py-3 font-mono text-[10px] uppercase tracking-widest text-accent-foreground hover:bg-primary hover:text-primary-foreground"
                >
                  Enter mission control
                </Link>
                <PixelButton variant="ghost" onClick={onRebuild}>
                  Rebuild from scratch
                </PixelButton>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </main>
  )
}

function DoneScreen({ data }: { data: SetupData }) {
  const topPriorities = data.priorities.slice(0, 3)

  return (
    <main className="relative flex h-svh flex-col overflow-hidden bg-gradient-to-b from-[#bcd8ce] via-background to-[#eec98f]">
      <PixelWorld harborHeight="h-[20svh] min-h-36" />

      <header className="relative z-10 flex shrink-0 items-start justify-between p-4 md:p-6">
        <div className="boot-in">
          <PixelChip variant="orange">Network compiling</PixelChip>
        </div>
        <div className="boot-in boot-delay-1 hidden sm:block">
          <PixelChip variant="cream">Resilient Supply Chain</PixelChip>
        </div>
      </header>

      <div className="relative z-10 mx-auto flex w-full max-w-2xl min-h-0 flex-1 flex-col items-center justify-center px-4 pb-[16svh] text-center">
        <div className="boot-in boot-delay-2 flex min-h-0 w-full flex-col border-4 border-foreground bg-card/95 pixel-shadow">
          <div className="pixel-scroll min-h-0 overflow-y-auto p-6 sm:p-8">
            <p className="font-mono text-[10px] uppercase tracking-widest text-accent">
              {'> Inputs received_'}
              <span className="blink">|</span>
            </p>
            <h1 className="mt-3 text-balance font-mono text-base uppercase leading-relaxed tracking-wider sm:text-xl">
              MYCEL is growing your network
            </h1>
            <p className="mt-3 text-pretty text-sm leading-relaxed text-muted-foreground">
              Our agents are mapping suppliers, pricing routes, scoring geographic risk and
              stress-testing your network against tariff spikes and blocked routes.
            </p>

            <div className="mt-5 flex flex-col gap-2 text-left">
              <SummaryRow label="Business" value={data.businessType || 'Described in your own words'} />
              <SummaryRow
                label="Reach"
                value={[data.supplySource, data.customerAreas].filter(Boolean).join(' -> ') || 'To be mapped'}
              />
              <SummaryRow
                label="Scale"
                value={
                  [data.volume, data.peakSurge ? `peaks at ${data.peakSurge}` : '']
                    .filter(Boolean)
                    .join(' · ') || 'To be estimated'
                }
              />
              <SummaryRow
                label="Timeline"
                value={
                  data.timeline === 'Fixed launch date' && data.targetDate
                    ? data.targetDate
                    : data.timeline || 'Flexible'
                }
              />
              <SummaryRow label="Budget stance" value={data.budgetTolerance || 'Balanced'} />
              <SummaryRow
                label="Optimizing for"
                value={topPriorities.length > 0 ? topPriorities.join(', ') : 'Balanced network'}
              />
              <SummaryRow
                label="Known constraints"
                value={`${data.constraints.length} recorded · ${data.files.length} files uploaded`}
              />
            </div>

            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <Link
                href="/control"
                className="press-pulse border-2 border-foreground bg-accent px-6 py-3 font-mono text-[10px] uppercase tracking-widest text-accent-foreground hover:bg-primary hover:text-primary-foreground"
              >
                Enter mission control
              </Link>
              <Link
                href="/"
                className="border-2 border-foreground bg-card px-6 py-3 font-mono text-[10px] uppercase tracking-widest text-foreground pixel-shadow-sm hover:bg-muted"
              >
                Back to start
              </Link>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-2 border-foreground bg-background px-3 py-2.5">
      <span className="font-mono text-[8px] uppercase tracking-widest text-accent">{label}</span>
      <span className="text-right text-sm capitalize">{value}</span>
    </div>
  )
}
