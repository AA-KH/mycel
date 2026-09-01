'use client'

import { cn } from '@/lib/utils'
import type { ReactNode } from 'react'

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <p className="mb-3 font-mono text-[10px] uppercase tracking-widest text-accent">{children}</p>
  )
}

export function StepHeading({ kicker, children }: { kicker: string; children: ReactNode }) {
  return (
    <div className="mb-5">
      <p className="mb-2 font-mono text-[9px] uppercase tracking-widest text-muted-foreground">
        {kicker}
      </p>
      <h2 className="text-balance font-mono text-sm uppercase leading-relaxed tracking-wider sm:text-base">
        {children}
      </h2>
    </div>
  )
}

/* Large selectable card (like the reference "I'm technical" cards) */
export function OptionCard({
  title,
  tagline,
  description,
  selected,
  onSelect,
}: {
  title: string
  tagline: string
  description?: string
  selected: boolean
  onSelect: () => void
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={cn(
        'flex h-full flex-col border-2 border-foreground p-3.5 text-left transition-colors',
        selected ? 'bg-teal-mist pixel-shadow-sm' : 'bg-card hover:bg-muted',
      )}
    >
      <span className="mb-1.5 flex items-center gap-2">
        <span
          className={cn(
            'inline-block h-3.5 w-3.5 shrink-0 border-2 border-foreground',
            selected ? 'bg-accent' : 'bg-card',
          )}
        />
        <span className="font-mono text-[9px] uppercase leading-relaxed tracking-wider">
          {title}
        </span>
      </span>
      <span className="text-sm font-semibold leading-snug">{tagline}</span>
      {description ? (
        <span className="mt-1 text-[13px] leading-snug text-muted-foreground">{description}</span>
      ) : null}
    </button>
  )
}

/* Horizontal radio row list (like the engine picker reference) */
export function RadioRow({
  label,
  sublabel,
  badge,
  selected,
  onSelect,
}: {
  label: string
  sublabel?: string
  badge?: string
  selected: boolean
  onSelect: () => void
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={cn(
        'flex w-full items-center gap-3 border-2 border-foreground px-4 py-3 text-left transition-colors',
        selected ? 'bg-teal-mist pixel-shadow-sm' : 'bg-card hover:bg-muted',
      )}
    >
      <span
        className={cn(
          'h-3.5 w-3.5 shrink-0 border-2 border-foreground',
          selected ? 'bg-accent' : 'bg-card',
        )}
      />
      <span className="flex-1">
        <span className="block font-mono text-[10px] uppercase tracking-wider">{label}</span>
        {sublabel ? (
          <span className="mt-0.5 block text-sm text-muted-foreground">{sublabel}</span>
        ) : null}
      </span>
      {badge ? (
        <span className="hidden border-2 border-foreground bg-secondary px-2 py-1 font-mono text-[8px] uppercase tracking-widest sm:inline-block">
          {badge}
        </span>
      ) : null}
    </button>
  )
}

/* Small toggle chip for multi-select */
export function ChipToggle({
  label,
  selected,
  onToggle,
}: {
  label: string
  selected: boolean
  onToggle: () => void
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={selected}
      className={cn(
        'border-2 border-foreground px-3 py-2 font-mono text-[9px] uppercase tracking-wider transition-colors',
        selected
          ? 'bg-secondary text-secondary-foreground pixel-shadow-sm'
          : 'bg-card hover:bg-muted',
      )}
    >
      {label}
    </button>
  )
}

export function TextField({
  label,
  value,
  onChange,
  placeholder,
  optional,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
  optional?: boolean
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block font-mono text-[9px] uppercase tracking-widest">
        {label}
        {optional ? <span className="ml-2 text-muted-foreground">(optional)</span> : null}
      </span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full border-2 border-foreground bg-card px-3 py-2.5 text-sm placeholder:text-muted-foreground/60 focus:bg-background focus:outline-none focus:ring-2 focus:ring-accent"
      />
    </label>
  )
}

export function TextAreaField({
  label,
  value,
  onChange,
  placeholder,
  rows = 4,
  optional,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
  rows?: number
  optional?: boolean
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block font-mono text-[9px] uppercase tracking-widest">
        {label}
        {optional ? <span className="ml-2 text-muted-foreground">(optional)</span> : null}
      </span>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className="w-full resize-y border-2 border-foreground bg-card px-3 py-2.5 text-sm leading-relaxed placeholder:text-muted-foreground/60 focus:bg-background focus:outline-none focus:ring-2 focus:ring-accent"
      />
    </label>
  )
}

/* Callout linking a question to the agent who consumes the answer */
export function AgentNote({
  agent,
  role,
  children,
}: {
  agent: string
  role: string
  children: ReactNode
}) {
  return (
    <div className="flex items-start gap-3 border-2 border-dashed border-accent/60 bg-accent/5 px-3.5 py-3">
      <span
        aria-hidden="true"
        className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center border-2 border-foreground bg-secondary font-mono text-[9px] uppercase tracking-wider pixel-shadow-sm"
      >
        {agent.slice(0, 2)}
      </span>
      <p className="text-[13px] leading-snug text-muted-foreground">
        <span className="font-mono text-[9px] uppercase tracking-widest text-accent">
          {agent} · {role}
        </span>
        <span className="mt-0.5 block">{children}</span>
      </p>
    </div>
  )
}

/* Pixel-square weight picker: 0-5 blocks */
export function WeightPicker({
  label,
  value,
  onChange,
}: {
  label: string
  value: number
  onChange: (v: number) => void
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-2 border-foreground bg-card px-4 py-3">
      <span className="text-sm font-semibold">{label}</span>
      <div className="flex items-center gap-1.5" role="group" aria-label={`${label} weight, ${value} of 5`}>
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            aria-label={`Set ${label} weight to ${n === value ? 0 : n}`}
            onClick={() => onChange(n === value ? 0 : n)}
            className={cn(
              'h-4 w-4 border-2 border-foreground transition-colors',
              n <= value ? 'bg-accent' : 'bg-background hover:bg-muted',
            )}
          />
        ))}
      </div>
    </div>
  )
}
