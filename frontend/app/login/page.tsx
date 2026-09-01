import type { Metadata } from 'next'
import { PixelChip } from '@/components/pixel/pixel-ui'
import { AgentsTicker, PixelWorld } from '@/components/pixel/pixel-scene'
import { LoginForm } from '@/components/auth/login-form'

export const metadata: Metadata = {
  title: 'Operator Login — MYCEL',
  description: 'Authenticate to access the MYCEL supply-chain control room.',
}

export default function LoginPage() {
  return (
    <main className="relative flex h-svh flex-col overflow-hidden bg-[#bcd8ce]">
      {/* animated pixel supply-chain world */}
      <PixelWorld />

      {/* header chips */}
      <header className="relative z-10 flex items-start justify-between p-4 md:p-6">
        <div className="boot-in">
          <PixelChip variant="yellow">Auth v1.0</PixelChip>
        </div>
        <div className="boot-in boot-delay-1 hidden sm:block">
          <PixelChip variant="cream">Secure Channel</PixelChip>
        </div>
      </header>

      {/* centered auth terminal */}
      <div className="relative z-10 mx-auto flex w-full max-w-md flex-1 flex-col items-center justify-center px-5 pb-[24svh]">
        <div className="boot-in boot-delay-2 mb-5">
          <PixelChip variant="cream" className="normal-case tracking-wider text-accent">
            {'> OPERATOR AUTHENTICATION REQUIRED'}
            <span className="blink">_</span>
          </PixelChip>
        </div>

        <div className="boot-in boot-delay-3 w-full">
          <LoginForm />
        </div>
      </div>

      {/* agents ticker pinned to the bottom edge */}
      <AgentsTicker className="relative z-10" />
    </main>
  )
}
