import Link from 'next/link'
import { PixelChip } from '@/components/pixel/pixel-ui'
import { AgentsTicker, PixelWorld } from '@/components/pixel/pixel-scene'

export default function WelcomePage() {
  return (
    <main className="relative flex h-svh flex-col overflow-hidden bg-[#bcd8ce]">
      {/* animated pixel supply-chain world */}
      <PixelWorld />

      {/* header chips */}
      <header className="relative z-10 flex items-start justify-between p-4 md:p-6">
        <div className="boot-in">
          <PixelChip variant="yellow">Boot v1.0</PixelChip>
        </div>
        <div className="boot-in boot-delay-1 hidden sm:block">
          <PixelChip variant="cream">Resilient Supply Chain</PixelChip>
        </div>
      </header>

      {/* hero — fills the space above the scene strip */}
      <div className="relative z-10 mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-5 pb-[22svh] text-center">
        <div className="boot-in boot-delay-2">
          <PixelChip variant="cream" className="mb-6 normal-case tracking-wider text-accent">
            {'> GIVE US A PRODUCT. WE BUILD THE SUPPLY CHAIN.'}
            <span className="blink">_</span>
          </PixelChip>
        </div>

        <h1 className="boot-in boot-delay-3 border-4 border-foreground bg-card px-8 py-5 font-mono text-4xl tracking-wider pixel-shadow sm:px-14 sm:py-7 sm:text-6xl md:text-7xl">
          MYCE<span className="text-accent">L</span>
        </h1>

        <p className="boot-in boot-delay-4 mt-6 max-w-xl text-pretty text-sm leading-relaxed text-foreground sm:text-base md:text-lg">
          An AI organization that sources, manufactures, moves and protects your entire supply
          chain — a living network that reroutes around tariff shocks, blocked routes and
          supplier failure.
        </p>

        <div className="boot-in boot-delay-5 mt-8">
          <Link
            href="/setup"
            className="press-pulse inline-block border-2 border-foreground bg-primary px-8 py-4 font-mono text-xs uppercase tracking-widest text-primary-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            Press Start
            <span className="blink">_</span>
          </Link>
        </div>
      </div>

      {/* agents ticker pinned to the bottom edge */}
      <AgentsTicker className="relative z-10" />
    </main>
  )
}
