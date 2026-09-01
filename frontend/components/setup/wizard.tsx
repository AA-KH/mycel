'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
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

export function SetupWizard() {
  const [step, setStep] = useState(0)
  const [done, setDone] = useState(false)
  const [data, setData] = useState<SetupData>(EMPTY_DATA)

  const update = (patch: Partial<SetupData>) => setData((d) => ({ ...d, ...patch }))

  const canContinue =
    step !== 0 || data.businessType !== '' || data.businessDescription.trim().length > 0

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
                <PixelButton variant="orange" onClick={() => setDone(true)}>
                  Build my network
                </PixelButton>
              )}
            </div>
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
