import { cn } from '@/lib/utils'
import type { ReactNode, ButtonHTMLAttributes } from 'react'

export function PixelChip({
  children,
  variant = 'cream',
  className,
}: {
  children: ReactNode
  variant?: 'cream' | 'yellow' | 'navy' | 'orange'
  className?: string
}) {
  const styles = {
    cream: 'bg-card text-foreground',
    yellow: 'bg-secondary text-secondary-foreground',
    navy: 'bg-primary text-primary-foreground',
    orange: 'bg-accent text-accent-foreground',
  }
  return (
    <span
      className={cn(
        'inline-block border-2 border-foreground px-3 py-1.5 font-mono text-[9px] uppercase tracking-widest pixel-shadow-sm',
        styles[variant],
        className,
      )}
    >
      {children}
    </span>
  )
}

export function PixelPanel({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <div className={cn('border-4 border-foreground bg-card pixel-shadow', className)}>
      {children}
    </div>
  )
}

type PixelButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'navy' | 'orange' | 'ghost'
}

export function PixelButton({
  children,
  variant = 'navy',
  className,
  ...props
}: PixelButtonProps) {
  const styles = {
    navy: 'bg-primary text-primary-foreground hover:bg-accent hover:text-accent-foreground',
    orange: 'bg-accent text-accent-foreground hover:bg-primary hover:text-primary-foreground',
    ghost: 'bg-card text-foreground hover:bg-muted',
  }
  return (
    <button
      className={cn(
        'border-2 border-foreground px-5 py-3 font-mono text-[10px] uppercase tracking-widest pixel-shadow-sm transition-colors',
        'active:translate-x-[3px] active:translate-y-[3px] active:shadow-none',
        'disabled:cursor-not-allowed disabled:opacity-40',
        styles[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}

export function ProgressSquares({
  total,
  current,
  className,
}: {
  total: number
  current: number
  className?: string
}) {
  return (
    <div
      className={cn('flex items-center gap-1.5', className)}
      role="progressbar"
      aria-valuemin={1}
      aria-valuemax={total}
      aria-valuenow={current + 1}
      aria-label={`Step ${current + 1} of ${total}`}
    >
      {Array.from({ length: total }).map((_, i) => (
        <span
          key={i}
          className={cn(
            'h-3 w-3 border-2 border-foreground',
            i < current ? 'bg-secondary' : i === current ? 'bg-accent' : 'bg-card',
          )}
        />
      ))}
    </div>
  )
}
