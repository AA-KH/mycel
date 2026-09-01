import { cn } from '@/lib/utils'

/* Chunky orange pixel sun (plus-shape of squares), gently bobbing */
export function PixelSun({ className }: { className?: string }) {
  const rows = [
    [0, 0, 1, 1, 0, 0],
    [0, 1, 1, 1, 1, 0],
    [1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1],
    [0, 1, 1, 1, 1, 0],
    [0, 0, 1, 1, 0, 0],
  ]
  return (
    <div className={cn('sun-bob', className)} aria-hidden="true">
      <div className="grid grid-cols-6 gap-0">
        {rows.flat().map((on, i) => (
          <span
            key={i}
            className={`h-4 w-4 sm:h-5 sm:w-5 ${on ? 'bg-[#e8983c]' : 'bg-transparent'}`}
          />
        ))}
      </div>
    </div>
  )
}

/* Blocky pixel cloud drifting across the sky */
function PixelCloud({ className, slow }: { className?: string; slow?: boolean }) {
  return (
    <div
      className={cn('absolute', slow ? 'cloud-drift-slow' : 'cloud-drift', className)}
      aria-hidden="true"
    >
      <div className="flex flex-col items-center opacity-70">
        <div className="h-3 w-10 bg-card" />
        <div className="h-3 w-16 bg-card" />
      </div>
    </div>
  )
}

/* Hollow route node square, like the reference slide */
function RouteNode({ className }: { className?: string }) {
  return (
    <span
      className={cn('absolute h-3.5 w-3.5 border-2 border-foreground/50 bg-card', className)}
    />
  )
}

/* A dashed supply route with hollow nodes and a traveling packet */
function Route({
  className,
  packetDelay = '0s',
  packetColor = 'bg-secondary',
  duration = '9s',
}: {
  className?: string
  packetDelay?: string
  packetColor?: string
  duration?: string
}) {
  return (
    <div className={cn('dashed-line-h absolute', className)} aria-hidden="true">
      <span
        className={cn('packet', packetColor)}
        style={{ animationDelay: packetDelay, animationDuration: duration }}
      />
      <RouteNode className="-top-[6px] left-[18%]" />
      <span className="node-blink absolute -top-[5px] left-[72%] h-3 w-3 border-2 border-foreground" />
    </div>
  )
}

/* Stepped L-shaped dashed route (horizontal + vertical + horizontal), like the slide */
function RouteSteps({ className, flip }: { className?: string; flip?: boolean }) {
  return (
    <div className={cn('absolute', className)} aria-hidden="true">
      <div className="dashed-line-h absolute left-0 top-0 w-[55%]" />
      <div
        className={cn('dashed-line-v absolute h-full', flip ? 'left-0' : 'left-[55%]')}
        style={flip ? undefined : undefined}
      />
      <div
        className={cn('dashed-line-h absolute bottom-0 w-[45%]', flip ? 'left-0' : 'left-[55%]')}
      />
      <RouteNode className="-top-[6px] left-[55%] -ml-[6px]" />
      <RouteNode className="-bottom-[6px] right-0" />
    </div>
  )
}

/* ---------- hand-built pixel harbor (no repeating image) ---------- */

/* One shipping container block */
function Box({ color, className }: { color: string; className?: string }) {
  return (
    <div className={cn('relative h-3.5 w-9 border-2 border-foreground sm:h-4 sm:w-11', color, className)}>
      <span className="absolute inset-y-0 left-1/2 w-[2px] -translate-x-1/2 bg-foreground/40" />
    </div>
  )
}

/* Stacked containers on the dock */
function ContainerStack({ className }: { className?: string }) {
  return (
    <div className={cn('flex flex-col items-start', className)} aria-hidden="true">
      <Box color="bg-secondary" className="ml-5" />
      <div className="flex">
        <Box color="bg-accent" />
        <Box color="bg-[#c8502e]" />
      </div>
      <div className="flex">
        <Box color="bg-secondary" />
        <Box color="bg-[#e8983c]" />
        <Box color="bg-accent" />
      </div>
    </div>
  )
}

/* Gantry crane with a hoisting container */
function Crane({ className, delay = '0s' }: { className?: string; delay?: string }) {
  return (
    <div className={cn('relative h-36 w-40 sm:h-44 sm:w-48', className)} aria-hidden="true">
      {/* boom */}
      <div className="absolute left-0 top-6 h-2.5 w-full bg-primary" />
      {/* counterweight block */}
      <div className="absolute left-0 top-2 h-4 w-6 bg-primary" />
      {/* mast + legs */}
      <div className="absolute bottom-0 left-[22%] top-2 w-2.5 bg-primary" />
      <div className="absolute bottom-0 left-[38%] top-8 w-2.5 bg-primary" />
      {/* leg crossbar */}
      <div className="absolute bottom-8 left-[22%] h-2 w-[19%] bg-primary" />
      {/* cable + hanging container */}
      <div className="crane-hoist absolute right-[14%] top-8" style={{ animationDelay: delay }}>
        <div className="mx-auto h-8 w-[2px] bg-foreground" />
        <Box color="bg-accent" />
      </div>
    </div>
  )
}

/* Warehouse with lit windows */
function Warehouse({ className }: { className?: string }) {
  return (
    <div className={cn('relative', className)} aria-hidden="true">
      {/* roof */}
      <div className="mx-auto h-2.5 w-[112%] -translate-x-[5%] bg-primary" />
      <div className="relative h-16 w-36 bg-primary sm:h-20 sm:w-44">
        <div className="absolute left-3 top-3 grid grid-cols-4 gap-1.5">
          {Array.from({ length: 8 }).map((_, i) => (
            <span key={i} className={`h-2.5 w-3.5 ${i === 5 ? 'bg-[#e8983c]' : 'bg-secondary'}`} />
          ))}
        </div>
        {/* door */}
        <div className="absolute bottom-0 left-1/2 h-6 w-8 -translate-x-1/2 bg-secondary sm:h-7" />
      </div>
    </div>
  )
}

/* Cargo ship bobbing on the water */
function Ship({ className }: { className?: string }) {
  return (
    <div className={cn('ship-bob', className)} aria-hidden="true">
      {/* cargo on deck */}
      <div className="flex pl-6">
        <Box color="bg-secondary" />
        <Box color="bg-accent" />
      </div>
      {/* bridge tower */}
      <div className="relative -mt-6 mb-0 ml-1 h-6 w-5 bg-primary">
        <span className="absolute left-1 top-1 h-1.5 w-2 bg-secondary" />
      </div>
      {/* hull */}
      <div className="relative h-6 w-44 border-t-2 border-[#f2ead3] bg-primary sm:w-52">
        <span className="absolute left-4 top-2 h-1.5 w-1.5 bg-secondary" />
        <span className="absolute left-9 top-2 h-1.5 w-1.5 bg-secondary" />
        <span className="absolute left-14 top-2 h-1.5 w-1.5 bg-secondary" />
      </div>
    </div>
  )
}

/* Full-width pixel harbor scene, drawn in CSS — no tiled image */
function PixelHarbor({ className }: { className?: string }) {
  return (
    <div className={cn('absolute inset-x-0 bottom-0', className)} aria-hidden="true">
      {/* dock surface */}
      <div className="absolute inset-x-0 bottom-0 top-[42%] bg-[#e0a463]">
        {/* dashed lane markings on the dock */}
        <div
          className="absolute inset-x-0 top-3 h-1.5 opacity-80"
          style={{
            backgroundImage:
              'repeating-linear-gradient(to right, var(--secondary) 0 18px, transparent 18px 42px)',
          }}
        />
      </div>
      {/* horizon line where structures sit */}
      <div className="absolute inset-x-0 top-[42%] h-1 bg-foreground" />

      {/* water */}
      <div className="absolute inset-x-0 bottom-0 h-[34%] bg-primary">
        <div
          className="water-slide absolute inset-x-0 top-2 h-1 opacity-50"
          style={{
            backgroundImage:
              'repeating-linear-gradient(to right, var(--secondary) 0 10px, transparent 10px 34px)',
          }}
        />
        <div
          className="water-slide absolute inset-x-0 top-6 h-1 opacity-25 [animation-delay:-2s]"
          style={{
            backgroundImage:
              'repeating-linear-gradient(to right, #f2ead3 0 8px, transparent 8px 40px)',
          }}
        />
      </div>

      {/* structures standing on the dock line */}
      <div className="absolute inset-x-0 top-[42%] -translate-y-full">
        <div className="relative mx-auto flex h-0 max-w-[1600px] items-end">
          <ContainerStack className="absolute bottom-0 left-[4%]" />
          <Crane className="absolute bottom-0 left-[16%] hidden sm:block" />
          <ContainerStack className="absolute bottom-0 left-[42%] hidden md:block" />
          <Crane className="absolute bottom-0 right-[26%] hidden lg:block" delay="-3.5s" />
          <Warehouse className="absolute bottom-0 right-[4%]" />
        </div>
      </div>

      {/* ship floating on the water */}
      <Ship className="absolute bottom-[16%] left-[52%] hidden sm:block md:left-[56%]" />
      <Ship className="absolute bottom-[14%] left-[6%] sm:hidden" />
    </div>
  )
}

/*
 * Full-viewport animated pixel supply-chain backdrop.
 * Banded pastel sky with dithered transitions, pixel grid texture,
 * orange pixel sun, dashed routes, and a hand-drawn CSS harbor.
 */
export function PixelWorld({
  harborHeight = 'h-[27svh] min-h-44',
}: {
  harborHeight?: string
}) {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      {/* banded sky, like the reference slide */}
      <div className="absolute inset-0 flex flex-col">
        <div className="h-[24%] bg-[#bcd8ce]" />
        <div
          className="dither h-[4%]"
          style={{ '--dither-a': '#bcd8ce', '--dither-b': '#d5e2cf' } as React.CSSProperties}
        />
        <div className="h-[14%] bg-[#d5e2cf]" />
        <div
          className="dither h-[4%]"
          style={{ '--dither-a': '#d5e2cf', '--dither-b': '#f2ead3' } as React.CSSProperties}
        />
        <div className="h-[18%] bg-[#f2ead3]" />
        <div
          className="dither h-[4%]"
          style={{ '--dither-a': '#f2ead3', '--dither-b': '#eeda9e' } as React.CSSProperties}
        />
        <div className="h-[12%] bg-[#eeda9e]" />
        <div
          className="dither h-[4%]"
          style={{ '--dither-a': '#eeda9e', '--dither-b': '#e9bd7c' } as React.CSSProperties}
        />
        <div className="flex-1 bg-[#e9bd7c]" />
      </div>

      {/* faint pixel-grid texture over everything */}
      <div className="pixel-grid absolute inset-0" />

      {/* drifting clouds */}
      <PixelCloud className="left-0 top-[8%]" />
      <PixelCloud className="left-0 top-[20%]" slow />

      {/* pixel sun */}
      <PixelSun className="absolute right-8 top-10 hidden md:block lg:right-20" />

      {/* animated supply routes */}
      <Route className="left-0 top-[18%] w-[28%]" packetDelay="0s" />
      <Route
        className="right-0 top-[38%] w-[24%]"
        packetDelay="-4s"
        packetColor="bg-accent"
        duration="11s"
      />
      <Route className="left-0 top-[58%] w-[20%]" packetDelay="-7s" duration="13s" />
      <RouteSteps className="left-[4%] top-[26%] hidden h-24 w-[24%] md:block" />
      <RouteSteps className="right-[2%] top-[52%] hidden h-28 w-[26%] lg:block" />
      <div className="dashed-line-v absolute right-[28%] top-[10%] hidden h-32 md:block" />
      <RouteNode className="right-[28%] top-[10%] -mr-[6px] hidden md:block" />

      {/* pixel harbor at the bottom */}
      <PixelHarbor className={harborHeight} />
    </div>
  )
}

const TICKER_ITEMS = [
  'SUPPLIER INTELLIGENCE',
  'PRICING ANALYST',
  'LOGISTICS PLANNER',
  'GEOGRAPHIC RISK',
  'VERIFICATION AGENT',
  'INVENTORY AGENT',
  'RESILIENCE ARCHITECT',
  'SUPPLY CHAIN ARCHITECT',
  'TARIFF WATCH',
  'ROUTE REROUTER',
]

export function AgentsTicker({ className }: { className?: string }) {
  return (
    <div
      className={cn('overflow-hidden border-t-4 border-foreground bg-primary py-2', className)}
      aria-hidden="true"
    >
      <div className="ticker-track flex w-max gap-10 whitespace-nowrap">
        {[...TICKER_ITEMS, ...TICKER_ITEMS].map((item, i) => (
          <span
            key={i}
            className="flex items-center gap-3 font-mono text-[9px] uppercase tracking-widest text-secondary"
          >
            <span className={`h-2 w-2 ${i % 2 === 0 ? 'bg-secondary' : 'bg-accent'}`} />
            {item}
          </span>
        ))}
      </div>
    </div>
  )
}
