import { Suspense } from 'react'
import { SetupWizard } from '@/components/setup/wizard'

export const metadata = {
  title: 'MYCEL — Build Your Network',
}

export default function SetupPage() {
  return (
    <Suspense fallback={<div className="h-svh w-full bg-[#bcd8ce]" />}>
      <SetupWizard />
    </Suspense>
  )
}
