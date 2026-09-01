import type { Metadata } from 'next'
import { PixelChip, PixelSunMark } from '@/components/pixel/pixel-ui'
import { LoginForm } from '@/components/auth/login-form'
import { BootConsole } from '@/components/auth/boot-console'

export const metadata: Metadata = {
  title: 'Operator Login — MYCEL',
  description: 'Authenticate to access the MYCEL supply-chain control room.',
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>
}) {
  const { next } = await searchParams

  return (
    <main className="pixel-grid diag-texture relative min-h-svh bg-gradient-to-br from-[#bcd8ce] via-background to-[#eec98f]">
      <div className="mx-auto flex min-h-svh w-full max-w-[1600px] flex-col gap-6 p-4 sm:p-6 lg:h-svh lg:gap-8 lg:p-10 xl:p-14">
        {/* top bar */}
        <header className="flex shrink-0 flex-wrap items-center justify-between gap-3">
          <div className="boot-in flex items-center gap-3">
            <PixelSunMark />
            <span className="border-2 border-foreground bg-card px-3 py-1.5 font-mono text-xs uppercase tracking-[0.3em] pixel-shadow-sm sm:text-sm">
              MYCE<span className="text-accent">L</span>
            </span>
          </div>
          <div className="boot-in boot-delay-1 flex items-center gap-3">
            <PixelChip variant="yellow" className="hidden sm:inline-block">
              Secure Channel
            </PixelChip>
            <PixelChip variant="navy">Auth v1.0</PixelChip>
          </div>
        </header>

        {/* split body */}
        <div className="grid min-h-0 flex-1 grid-cols-1 items-stretch gap-6 lg:grid-cols-[1.15fr_minmax(420px,0.85fr)] lg:gap-10">
          {/* left — statement + live boot log */}
          <section className="boot-in boot-delay-2 flex min-h-0 flex-col gap-5 lg:gap-7">
            <div className="shrink-0">
              <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-accent sm:text-xs">
                {'> Operator authentication required'}
                <span className="blink">_</span>
              </p>
              <h1 className="mt-4 text-balance font-mono text-3xl uppercase leading-tight tracking-wider sm:text-4xl lg:text-[2.75rem] xl:text-5xl 2xl:text-6xl">
                Your supply chain
                <br />
                is <span className="text-accent">already running</span>
              </h1>
              <p className="mt-4 max-w-lg text-pretty leading-relaxed text-muted-foreground">
                Nine agents keep sourcing, pricing and stress-testing your network
                around the clock. Sign in to take the controls.
              </p>
            </div>

            {/* live log fills the rest of the column on desktop */}
            <div className="hidden min-h-0 flex-1 lg:flex">
              <BootConsole />
            </div>
          </section>

          {/* right — auth terminal */}
          <section className="boot-in boot-delay-3 flex min-h-0 items-center">
            <div className="w-full">
              <LoginForm next={next} />
            </div>
          </section>
        </div>

        {/* bottom strip */}
        <footer className="boot-in boot-delay-4 flex shrink-0 flex-wrap items-center justify-between gap-3 border-t-2 border-dashed border-foreground/30 pt-4 font-mono text-[9px] uppercase tracking-widest text-muted-foreground">
          <span>Encrypted operator channel</span>
          <span className="hidden sm:inline">
            Sourcing · Manufacturing · Warehousing · Distribution · Demand
          </span>
          <span className="flex items-center gap-2">
            <span className="h-2 w-2 bg-accent node-blink" aria-hidden="true" />
            Network online
          </span>
        </footer>
      </div>
    </main>
  )
}
