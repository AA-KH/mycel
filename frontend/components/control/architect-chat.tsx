'use client'

import { useEffect, useRef, useState } from 'react'
import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { cn } from '@/lib/utils'

const SUGGESTIONS = [
  'Why dual-sourcing instead of the cheapest supplier?',
  'What happens if Supplier A goes down?',
  'Explain the 30-day safety stock decision',
]

export function ArchitectChat() {
  const { messages, sendMessage, status, error } = useChat({
    transport: new DefaultChatTransport({ api: '/api/architect' }),
  })
  const [input, setInput] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const busy = status === 'submitted' || status === 'streaming'

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages, status])

  const submit = (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || busy) return
    sendMessage({ text: trimmed })
    setInput('')
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 border-2 border-foreground bg-accent px-4 py-2 font-mono text-[10px] uppercase tracking-widest text-accent-foreground pixel-shadow transition-transform hover:-translate-y-0.5"
      >
        <span className="flex h-2 w-2 items-center justify-center bg-accent-foreground" />
        Ask the Architect
      </button>
    )
  }

  return (
    <div className="flex w-[340px] flex-col border-2 border-foreground bg-card pixel-shadow-sm shadow-xl">
      <header className="flex items-center justify-between border-b-2 border-foreground bg-accent px-2.5 py-1.5">
        <h3 className="font-mono text-[9px] uppercase tracking-widest text-accent-foreground">
          Ask the Architect
        </h3>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 font-mono text-[7px] uppercase tracking-widest text-accent-foreground">
            <span className={cn('inline-block h-1.5 w-1.5 bg-accent-foreground', busy && 'blink')} aria-hidden="true" />
            {busy ? 'Thinking' : 'Online'}
          </span>
          <button 
            onClick={() => setIsOpen(false)}
            className="flex h-4 w-4 items-center justify-center bg-accent-foreground font-mono text-[10px] leading-none text-accent transition-transform hover:scale-110"
            aria-label="Close chat"
          >
            ×
          </button>
        </div>
      </header>

      {/* transcript */}
      <div
        ref={scrollRef}
        className="pixel-scroll flex max-h-72 min-h-32 flex-col gap-2.5 overflow-y-auto bg-background p-2.5"
        aria-live="polite"
      >
        {messages.length === 0 ? (
          <div>
            <p className="text-pretty text-[11px] leading-relaxed text-muted-foreground">
              The blueprint is signed off. Ask anything about the architecture — why the council chose this
              topology, what a term means, or how the network survives a disruption.
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {SUGGESTIONS.map((sug) => (
                <button
                  key={sug}
                  type="button"
                  onClick={() => submit(sug)}
                  className="border-2 border-foreground bg-muted px-2 py-1 text-left font-mono text-[8px] uppercase tracking-wider text-foreground transition-colors hover:bg-secondary hover:text-secondary-foreground"
                >
                  {sug}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => {
            const isUser = message.role === 'user'
            return (
              <div key={message.id} className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
                <div
                  className={cn(
                    'max-w-[85%] border-2 border-foreground px-2.5 py-1.5',
                    isUser ? 'bg-primary text-primary-foreground' : 'bg-card text-foreground',
                  )}
                >
                  <span
                    className={cn(
                      'font-mono text-[7px] uppercase tracking-widest',
                      isUser ? 'text-secondary' : 'text-accent',
                    )}
                  >
                    {isUser ? 'You' : 'Architect'}
                  </span>
                  <div className="mt-0.5 whitespace-pre-wrap text-[11px] leading-relaxed">
                    {message.parts.map((part, i) => (part.type === 'text' ? <span key={i}>{part.text}</span> : null))}
                  </div>
                </div>
              </div>
            )
          })
        )}

        {status === 'submitted' ? (
          <p className="font-mono text-[9px] uppercase tracking-widest text-muted-foreground">
            {'> Architect is consulting the blueprint'}
            <span className="blink">_</span>
          </p>
        ) : null}

        {error ? (
          <p className="border-2 border-foreground bg-[#e07a4c]/20 px-2 py-1.5 font-mono text-[9px] uppercase tracking-wider text-foreground">
            Transmission failed. Try asking again.
          </p>
        ) : null}
      </div>

      {/* input */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          submit(input)
        }}
        className="flex border-t-2 border-foreground"
      >
        <label htmlFor="architect-input" className="sr-only">
          Ask the architect a question
        </label>
        <input
          id="architect-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.nativeEvent.isComposing || e.keyCode === 229)) e.preventDefault()
          }}
          placeholder="Ask about the architecture…"
          className="min-w-0 flex-1 bg-card px-2.5 py-2 text-[12px] text-foreground placeholder:font-mono placeholder:text-[9px] placeholder:uppercase placeholder:tracking-widest placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-inset focus:ring-accent"
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className="border-l-2 border-foreground bg-accent px-3 py-2 font-mono text-[9px] uppercase tracking-widest text-accent-foreground transition-colors hover:bg-primary hover:text-primary-foreground disabled:cursor-not-allowed disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </div>
  )
}
