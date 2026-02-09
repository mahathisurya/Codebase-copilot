'use client'

import { MainLayout } from '@/components/layout/MainLayout'

// Disable static optimization for this page (uses client-side state)
export const dynamic = 'force-dynamic'

export default function Home() {
  return <MainLayout />
}