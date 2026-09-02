import { Suspense } from 'react'
import { ControlRoom } from '@/components/control/control-room'

export const metadata = {
  title: 'MYCEL — Mission Control',
}

export default function ControlPage() {
  return (
    <Suspense fallback={<div>Loading control room...</div>}>
      <ControlRoom />
    </Suspense>
  )
}
